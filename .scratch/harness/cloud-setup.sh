#!/bin/bash
# agent-os 클라우드 환경 설정 스크립트(claude.ai 의 클라우드 환경 → Edit → Setup script 에 붙여 넣는 원본). 세션이 뜨기 전에 root 로 돈다.
# 어느 단계가 실패해도 세션은 뜨도록 단계마다 실패를 stderr 에 알리기만 하고 넘어가며, 끝에서 0 으로 나간다.

# 1) PowerShell 7. pytest 의 tests/tools/test_open_session.py 가 pwsh 로 스크립트 함수를 부른다.
if ! command -v pwsh >/dev/null 2>&1; then
  (
    . /etc/os-release
    curl -fsSL -o /tmp/packages-microsoft-prod.deb \
      "https://packages.microsoft.com/config/ubuntu/${VERSION_ID}/packages-microsoft-prod.deb" &&
      dpkg -i /tmp/packages-microsoft-prod.deb &&
      apt-get update -o Dir::Etc::sourcelist=sources.list.d/microsoft-prod.list \
        -o Dir::Etc::sourceparts=- -o APT::Get::List-Cleanup=0 &&
      apt-get install -y --no-install-recommends powershell
  ) || echo "setup: PowerShell 설치 실패" >&2
fi

# 2) web 스토리 테스트의 브라우저. web/pnpm-lock.yaml 의 Playwright 1.63.0 은
#    chromium_headless_shell-1243(Chrome 153.0.8010.12)을 찾는다. cdn.playwright.dev 는 막혀 있어
#    같은 빌드를 Chrome for Testing 저장소에서 받는다. Playwright 판을 올리면 아래 두 값도 바꾼다
#    (web/node_modules/playwright-core/browsers.json 의 chromium-headless-shell 항목).
PW_REVISION=1243
CHROME_VERSION=153.0.8010.12
PW_DIR="${PLAYWRIGHT_BROWSERS_PATH:-/opt/pw-browsers}/chromium_headless_shell-${PW_REVISION}"
if [ ! -f "${PW_DIR}/INSTALLATION_COMPLETE" ]; then
  (
    mkdir -p "${PW_DIR}" &&
      curl -fsSL -o /tmp/chrome-headless-shell.zip \
        "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-headless-shell-linux64.zip" &&
      unzip -q -o /tmp/chrome-headless-shell.zip -d "${PW_DIR}" &&
      touch "${PW_DIR}/INSTALLATION_COMPLETE" &&
      rm -f /tmp/chrome-headless-shell.zip
  ) || echo "setup: chrome-headless-shell 설치 실패" >&2
fi

exit 0
