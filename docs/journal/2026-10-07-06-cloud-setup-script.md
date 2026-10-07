# 2026-10-07 (06) 클라우드 환경의 설정 스크립트를 실제로 도는 모양으로 고친다

일지 2026-10-07-05의 세션이 이어서 했다. 같은 클라우드 세션, 같은 브랜치 `claude/funny-planck-itf28j`다.

## 계기

일지 05의 답이 대기열 135(그때 번호 132)의 처방을 문장으로 적었다. "`pwsh` 설치, `uv sync`, `pnpm -C web install
--frozen-lockfile`, `pnpm -C web exec playwright install --only-shell chromium`". 사용자가 그것을 클라우드 환경의 Setup
script 칸에 그대로 넣은 화면을 보냈다.

> 사용자: "이렇게 넣었어"

## 무엇이 틀렸나

- **스크립트가 아니라 문장이었다.** 칸은 Bash 스크립트이고, 한 줄 전체가 `pwsh`라는 명령 하나로 읽힌다. `pwsh`가 없는
  환경에서 같은 줄을 `bash`로 돌리자 `pwsh: command not found`, 종료 코드 127이었다(손). 공식 문서
  (code.claude.com의 cloud-environments, Script requirements)는 0이 아닌 종료 코드면 세션이 시작되지 않는다고 적는다.
- **문장 속 명령도 그대로는 못 쓴다.** 이 환경에서 `cdn.playwright.dev`는 막혀 있어(`curl -I`가 000) `playwright install`이
  브라우저를 받지 못한다. 같은 문서에 따르면 설정 스크립트는 저장소 설정(`uv sync`, `pnpm install`)보다 VM을 갖추는 데
  쓰는 자리이고, 프로젝트 설치는 SessionStart 훅의 몫이다.

## 어떻게 했나

`.scratch/harness/cloud-setup.sh`를 원본으로 두었다. 이 컨테이너에서 root로 돌린 결과는 다음과 같다(손).

- **PowerShell.** `packages.microsoft.com`(허용 목록에 있고 `curl -I`가 200)의 apt 저장소로 설치했다. 7.6.6이 깔렸다.
- **브라우저.** Playwright 1.63.0이 찾는 `chromium_headless_shell-1243`은 Chrome 153.0.8010.12의 headless shell이다
  (`playwright-core@1.63.0`의 `browsers.json`을 읽었다). 같은 빌드를 Chrome for Testing 저장소
  (`storage.googleapis.com`, 허용 목록에 있고 200)에서 받아 `/opt/pw-browsers/chromium_headless_shell-1243/`에 풀고
  `INSTALLATION_COMPLETE` 표지를 둔다. 기존 `chromium_headless_shell-1194` 폴더의 모양을 따랐다.
- **시간과 종료 코드.** 처음 실행은 10초에 0, 이미 깔린 뒤의 실행은 0초에 0이었다. 캐시 기준(약 5분) 안이다.
- **넣지 않은 것.** `uv sync`는 `uv run`이 처음 돌 때 스스로 한다(이 세션의 첫 `uv run`이 패키지 80개를 깔았다).
  `pnpm -C web install`은 저장소 설정이라 세션에서 친다.
- **확인.** 스크립트를 돌린 뒤 `tests/tools/test_open_session.py` 9건이 통과했고, `pnpm -C web verify`가 Vitest 21파일
  309건을 통과했으며, `uv run python tools/run_checks.py`가 일곱을 모두 통과시켰다(74초).

Playwright 판을 올리면 스크립트의 두 값(`PW_REVISION`, `CHROME_VERSION`)도 바꿔야 한다. 그것을 보는 자동 검사는 없다.
`playwright-core`의 `browsers.json`은 `web/node_modules`에만 있어, `web` 의존성을 깔지 않는 CI의 `python` 잡에서 대조할
수 없다.

## 번호를 옮겼다

PR #157이 이 브랜치보다 먼저 병합되며 일지 `2026-10-07-02`, 대기열 132~134, 헌법 3.0.16을 썼다. main을 병합하고 이
브랜치의 일지를 03·04·05로, 대기열 행을 135·136으로, 헌법 판을 3.0.17로 옮겼다. 고친 인용은 이 브랜치가 들인 줄에 있는
것뿐이다. `git diff origin/main -U0`의 더한 줄과 글자 그대로 같은 줄만 스크립트로 고쳤고, 일지 안의 짧은 표기("일지
02", 제목의 번호)는 손으로 고쳤다. main이 쓴 줄의 `2026-10-07-02`는 카나리아 일지를 가리켜 그대로 두었다.

## 바꾼 것

- `.scratch/harness/cloud-setup.sh`(새 원본).
- `.scratch/retro-queue.md`: 135를 닫고 137을 올렸다.
- 병합 커밋: 위 번호 이동과 헌법 README의 3.0.17.

## 검사

- `bash -n`과 실제 실행(위). `uv run pytest -q tests/tools` 820 통과(병합 뒤). 마크다운 표 검사와 인용 대조는 바뀐 문서에
  돌렸다.

## 회고

일지의 "다음"을 쓰기 전에 retro를 돌렸다. 후보 하나를 냈고 승인돼 대기열 137로 갔다.

> 사용자(질문에 답): "대기열에 올린다 (Recommended)"

1. **사람이 붙여 넣을 값을 문장으로 줬다(대기열 137).** 위 "무엇이 틀렸나"의 사건이다. 붙여 넣을 자리가 있는 값은 그대로
   붙여 넣을 수 있는 코드 블록으로 주고, 실제로 돌려 본 뒤에 준다. 1회차.

## 다음

- 사용자가 Setup script 칸의 내용을 `.scratch/harness/cloud-setup.sh`로 바꾼다. 바꾸기 전까지는 새 세션이 시작되지 않을
  수 있다.
- 대기열 136(변이 도구의 시간 제한)은 그대로다.
