# 2026-10-07 (04) 검사 러너를 GitHub Actions의 Windows·Linux 러너에서 잰다

일지 2026-10-07-03의 세션이 이어서 했다. 같은 클라우드 세션, 같은 브랜치 `claude/funny-planck-itf28j`다.

## 계기

일지 03의 답 끝에 "아직 확인하지 못한 것" 넷을 적었다. Windows에서 러너가 `pnpm.cmd`를 찾는지, PR #156 뒤 가장 긴
검사가 무엇인지, 변이 도구의 되풀이 사건(대기열 133), 클라우드 환경 설정(대기열 132)이다.

> 사용자: "아직 확인하지 못한 것 확인해봐"

뒤의 둘은 확인할 것이 아니라 할 일이다. 133은 따로 반영할 chore이고, 132는 저장소 밖의 설정이라 사용자가 바꾼다. 이
단계는 앞의 둘을 쟀다.

## 어떻게 쟀나

이 컨테이너는 Linux이고 Playwright가 찾는 브라우저 판도 없다. `ci.yml`은 main 푸시와 PR에서만 돌고 이 브랜치에는 PR이
없다. 그래서 이 브랜치의 푸시에만 도는 임시 워크플로를 올려 ubuntu-latest·windows-latest에서 돌리고, 결과를 읽은 뒤
되돌렸다(`ab7c50e`를 `006e807`이 되돌렸다). PR #117이 실험 커밋을 올렸다 되돌린 것(ADR 0021 이력)과 같은 모양이다.
워크플로의 사본은 `.scratch/harness/probes/run_checks_ci_probe.yml`이다.

- `npm install -g pnpm@11.24.0`으로 `pnpm.cmd`를 두었다. 사용자 PC의 설치 방식은 확인하지 않았다. 저장소의
  기록은 Windows에 `pnpm.CMD`가 있다는 것뿐이다(일지 2026-10-01-01).
- `PYTHONUTF8`을 두지 않았다. 사람의 터미널에서 도는 pre-commit은 그것 없이 돈다.
- 먼저 측정 프로브 `precommit_parallel.py`를 고쳤다. 명령을 경로 없이 띄우고 있어서 Windows에서는 web verify를 띄우지
  못했을 것이다. 러너처럼 `shutil.which`로 찾게 하고, 실패한 명령은 출력의 끝을 찍게 했다(`dc9079b`).

## 잰 것

실행 37561588972, 두 러너 모두 CPU 4, 트리는 `ab7c50e`(PR #156 뒤)다. 판은 uv 0.12.23, Node 24.21.0, pnpm 11.24.0,
Playwright 1.63.0(chromium-headless-shell 1243)이다.

- **Windows에서 명령 찾기.** `shutil.which('pnpm')`은 `C:\npm\prefix\pnpm.CMD`였다. 경로 없이
  `subprocess.run(['pnpm', '--version'])`을 치면 `FileNotFoundError: [WinError 2]`였다. 러너가 `shutil.which`로 찾는
  까닭이 실제로 섰다.
- **pre-commit을 거친 러너.** `uv run pre-commit run parallel-checks --all-files`가 두 러너 모두 일곱을 통과시켰다.
  Linux는 70.6초(pytest 70.5초, web verify 62.1초), Windows는 153.4초(web verify 153.2초, pytest 142.9초)였다.
  `pwsh`와 브라우저가 있는 러너라 이 컨테이너의 실패 둘은 나오지 않았다.
- **차례와 동시(프로브).**

| 러너 | 차례로(`serial`) | 한꺼번에(`all`) | 한꺼번에 띄울 때 가장 긴 것 |
|---|---|---|---|
| ubuntu-latest | 115.0초 | 66.5초 | pytest 66.5초(web verify 61.9초) |
| windows-latest | 240.0초 | 142.5초 | web verify 142.5초(pytest 135.1초) |

- 함께 띄우면 검사마다는 느려진다. Windows의 pytest는 차례로 98.0초, 함께 135.1초였고, web verify는 120.4초와 142.5초였다.
  그래도 전체는 Linux에서 42%, Windows에서 41% 줄었다.

## 바꾼 것

- `.scratch/harness/probes/precommit_parallel.py`(`shutil.which`, 실패 출력의 끝)와 `run_checks_ci_probe.yml`(새 사본),
  프로브 README의 두 행.
- `docs/adr/0005-remote-ci-pr-from-day-one.md`: 이력에서 가장 긴 검사를 다시 재야 한다고 적었던 문장을 위 표의 값으로
  바꿨다. ADR 이력의 문구를 승인 뒤에 또 바꾼 것이라 답에서 사용자에게 알린다.
- `tools/run_checks.py` 독스트링: CI 시간을 더하고, "못 보는 것"의 Windows 문장을 위 실행에서 본 것으로 바꿨다.
- `KICKOFF.md`: 러너 항목에 Windows 러너의 시간과 `shutil.which`의 까닭.

## 검사

- **커밋과 같은 조건(손).** 스테이지하고 `uv run pre-commit run`을 쳐 89초였다. ruff 둘, 마크다운 표, 줄 구분
  문자, 인용 대조는 통과했고 변이 표는 받은 표가 없어 Skipped였다. 러너 안에서는 지침 검사, import-linter, 타입 우회
  검사, 훅 러너, pyright가 통과했다. pytest(9 failed, 1644 passed, 실패는 모두 `pwsh` 부재)와 web verify(스토리
  테스트가 `chromium_headless_shell-1243`을 찾지 못함)는 이 컨테이너의 환경 탓으로 실패했다(대기열 132). 같은 두
  검사가 위 GitHub Actions 러너에서는 통과했다.

## 회고

일지의 "다음"을 쓴 계기 훅으로 retro를 돌렸다. 이 단계에서 사람이 고치거나 되돌린 것이 없고, 도구 호출의 낭비도 없어
낸 후보가 없다.

## 다음

- 대기열 133(변이 도구의 시간 제한)과 132(클라우드 환경 설정)는 그대로다.
- CPU가 넷보다 적은 기계에서 함께 띄운 것이 차례로 돈 것보다 느린지는 여전히 재지 않았다. 사용자 PC의 CPU 수를 알게
  되면 `precommit_parallel.py serial`과 `all`을 그 PC에서 한 번 돌린다.
