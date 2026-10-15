# StockAuto 공식 다운로드 (Windows / macOS)

StockAuto 최신 버전 설치 파일 다운로드 저장소입니다.
최초 1회 다운로드 후 실행하면, 이후 업데이트는 앱 실행 시 자동으로 감지 및 설치됩니다.

---

## 📥 최신 버전 바로 다운로드 (항상 최신 버전 유지)

- **Windows (64-bit 무설치 포터블)**:
  👉 [StockAuto-windows-x64.zip 다운로드](https://github.com/heymuni-releases/stock/releases/latest/download/StockAuto-windows-x64.zip)

- **macOS (Apple Silicon / M1·M2·M3·M4)**:
  👉 [StockAuto-macos-arm64.zip 다운로드](https://github.com/heymuni-releases/stock/releases/latest/download/StockAuto-macos-arm64.zip)

---

## 🚀 실행 방법 안내

### Windows
> ⚠️ **중요 (반드시 압축 풀기 후 실행)**
> 다운로드한 `.zip` 압축 파일 안에서 바로 `StockAuto.exe`를 더블클릭하면 안 됩니다. (임시 실행 모드로 인해 파이썬 라이브러리를 찾을 수 없다는 오류가 발생합니다.)
> 반드시 **마우스 우클릭 → [압축 풀기] (또는 '모두 압축 풀기')**를 완료한 후, 풀린 새 폴더 안에 있는 `StockAuto.exe`를 실행해 주세요.

1. 다운로드한 `StockAuto-windows-x64.zip` 파일에서 마우스 우클릭 후 **[압축 풀기]** (또는 '모두 압축 풀기')를 선택합니다.
2. 압축이 해제된 새 폴더 안으로 들어갑니다.
3. 폴더 안의 `StockAuto.exe`를 실행합니다.

### macOS (최초 1회 실행 시 주의사항)
1. 다운로드한 `StockAuto-macos-arm64.zip`을 더블클릭하여 압축을 해제하고 `StockAuto.app`을 **응용 프로그램(/Applications)** 폴더로 이동합니다.
2. 브라우저에서 최초 다운로드 시 macOS Gatekeeper 보안 확인이 뜰 수 있습니다.
   - `StockAuto.app` 아이콘을 **Control-클릭(우클릭) → 열기(Open)**를 누르거나,
   - 터미널에서 아래 명령어를 1회 실행한 뒤 앱을 열면 정상 실행됩니다:
     ```bash
     xattr -cr /Applications/StockAuto.app
     ```
3. 최초 실행 이후에는 자동 업데이트 시 격리 속성이 자동으로 처리되므로 추가 경고 없이 바로 업데이트됩니다.
