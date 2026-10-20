"""Re-publish mutable release assets using the repository Actions token.

All assets are downloaded and verified before any release is changed.
Existing tags and download filenames are preserved. Use --apply to mutate.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile


BOT = "github-actions[bot]"
REQUIRED = {
    "release-manifest.json",
    "StockAuto-windows-x64.zip",
    "StockAuto-macos-arm64.zip",
}
TAG_PATTERN = r"v[0-9]+(?:\.[0-9]+){2,3}(?:-(?:alpha|beta|rc)[0-9]+)?"


def api(route: str, method: str = "GET", data: dict | None = None):
    command = ["gh", "api", "--method", method, route]
    if data is not None:
        command += ["--input", "-"]
    result = subprocess.run(
        command,
        input=json.dumps(data) if data is not None else None,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout) if result.stdout.strip() else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.tag != "all" and not re.fullmatch(TAG_PATTERN, args.tag):
        raise ValueError("Use 'all' or a numeric version tag with an optional prerelease suffix")

    repo = os.environ["GITHUB_REPOSITORY"]
    base = f"repos/{repo}"
    releases = json.loads(subprocess.check_output([
        "gh", "api", "--paginate", "--slurp", f"{base}/releases?per_page=100"
    ], text=True))
    releases = [release for page in releases for release in page]
    selected = [r for r in releases if args.tag == "all" or r["tag_name"] == args.tag]
    if not selected:
        raise ValueError("No matching releases")
    latest = api(f"{base}/releases/latest")["tag_name"]
    version_key = lambda tag: tuple(map(int, tag.removeprefix("v").split("-", 1)[0].split(".")))
    if any(not re.fullmatch(TAG_PATTERN, r["tag_name"]) for r in selected):
        raise ValueError("Unexpected release tag")
    selected.sort(key=lambda r: version_key(r["tag_name"]))
    # Explicitly selected drafts are the normal private CI handoff. The 'all'
    # maintenance option must never publish somebody else's unfinished draft.
    for release in selected:
        if release["draft"] and args.tag == "all":
            raise ValueError("Select a draft tag explicitly to publish it")
        if release["draft"] and not release["prerelease"] and version_key(release["tag_name"]) > version_key(latest):
            latest = release["tag_name"]
    cache = Path(tempfile.mkdtemp(prefix="release-republish-"))

    # Verify the complete original set before deleting or changing anything.
    for release in selected:
        tag = release["tag_name"]
        if release.get("immutable"):
            raise ValueError(f"Refusing immutable release: {tag}")
        assets = release["assets"]
        if {a["name"] for a in assets} != REQUIRED or len(assets) != len(REQUIRED):
            raise ValueError(f"Unexpected asset set: {tag}")
        folder = cache / tag
        folder.mkdir()
        subprocess.run([
            "gh", "release", "download", tag, "--repo", repo, "--dir", str(folder)
        ], check=True)
        for asset in assets:
            digest = asset.get("digest", "")
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                raise ValueError(f"Missing SHA-256: {tag}/{asset['name']}")
            path = folder / asset["name"]
            with path.open("rb") as stream:
                actual = hashlib.file_digest(stream, "sha256").hexdigest()
            if path.stat().st_size != asset["size"] or "sha256:" + actual != digest:
                raise ValueError(f"Original asset verification failed: {tag}/{path.name}")
        (folder / "original-release.json").write_text(json.dumps(release))
        print(f"Verified all original assets: {tag}", flush=True)

    if not args.apply:
        print("Verification complete; no releases changed.")
        return

    # Confirm the actual authenticated creator is the Actions bot first.
    probe = api(f"{base}/releases", "POST", {
        "tag_name": "bot-auth-check-" + os.environ["GITHUB_RUN_ID"],
        "name": "Bot authentication check",
        "draft": True,
    })
    try:
        if probe["author"]["login"] != BOT:
            raise ValueError("Publishing requires the repository Actions bot token")
    finally:
        api(f"{base}/releases/{probe['id']}", "DELETE")

    for original in selected:
        tag = original["tag_name"]
        current = api(f"{base}/releases/{original['id']}")
        if current["id"] != original["id"] or current.get("immutable"):
            raise ValueError(f"Release changed during verification: {tag}")
        if any(current[key] != original[key] for key in ("name", "body", "draft", "prerelease")):
            raise ValueError(f"Release details changed during verification: {tag}")
        original_assets = {a["name"]: (a["id"], a["digest"]) for a in original["assets"]}
        current_assets = {a["name"]: (a["id"], a["digest"]) for a in current["assets"]}
        if original_assets != current_assets:
            raise ValueError(f"Assets changed during verification: {tag}")
        api(f"{base}/releases/{original['id']}", "DELETE")
        replacement = api(f"{base}/releases", "POST", {
            "tag_name": tag,
            "name": original["name"],
            "body": original.get("body") or "",
            "draft": True,
            "prerelease": original["prerelease"],
        })
        if replacement["author"]["login"] != BOT:
            raise ValueError("Unexpected replacement author; leaving draft unpublished")
        for asset in original["assets"]:
            subprocess.run([
                "gh", "release", "upload", tag,
                str(cache / tag / asset["name"]), "--repo", repo,
            ], check=True)
        uploaded = api(f"{base}/releases/{replacement['id']}")
        expected = {a["name"]: (a["size"], a["digest"]) for a in original["assets"]}
        actual = {a["name"]: (a["size"], a["digest"]) for a in uploaded["assets"]}
        if actual != expected or any(a["uploader"]["login"] != BOT for a in uploaded["assets"]):
            raise ValueError(f"Uploaded assets failed verification; draft unpublished: {tag}")
        api(f"{base}/releases/{replacement['id']}", "PATCH", {
            "draft": False,
            "make_latest": "true" if tag == latest else "false",
        })
        print(f"Re-published {tag}: bot author, bot uploaders, identical asset bytes", flush=True)

    if api(f"{base}/releases/latest")["tag_name"] != latest:
        raise ValueError("Latest release changed unexpectedly")
    print("All selected releases verified. Latest version preserved.")


if __name__ == "__main__":
    main()
