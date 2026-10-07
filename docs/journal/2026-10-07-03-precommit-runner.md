# 2026-10-07 (03) pre-commit의 always_run 검사 일곱을 러너 하나가 함께 띄운다

일지 2026-10-07-02의 세션이 이어서 했다. 같은 클라우드 세션, 같은 브랜치 `claude/funny-planck-itf28j`이고 기준은
`162ae54`(PR #156 병합 뒤)다.

## 계기

일지 02의 끝에서 러너 훅의 ADR 초안(ADR 0005 이력)을 보였다.

> 사용자: "초안 승인"

## 어떻게 했나

- **테스트 먼저.** `tests/tools/test_run_checks.py`를 먼저 쓰고 모듈이 없어 수집 오류(빨강)인 것을 본 뒤 러너를 썼다.
  설정을 바꾸기 전에는 저장소 상태 테스트 하나가 빨갰고, 설정을 바꾼 뒤 일곱이 모두 초록이다.
- **함께 띄우는지는 시간으로 재지 않는다.** 두 검사가 서로의 표지 파일을 기다리게 했다. 하나씩 돌면 앞의 것이 20초를
  기다리다 실패한다.
- **CLI 테스트가 진짜 검사에 닿지 않게 했다.** 첫 판의 CLI 테스트는 SKIP으로 일곱을 모두 건너뛰는 것에만 기댔다. 변이
  표의 "SKIP 을 읽지 않는다"를 돌리자 러너가 진짜 pytest를 띄우고, 그 pytest의 CLI 테스트가 러너를 또 띄워 10분이 넘도록
  돌고 돌았다(프로세스 37개를 손으로 죽였다. 변이가 70행에 남아 있어 손으로 되돌렸다). 그래서 CLI 테스트는 `PATH`를 빈
  임시 디렉터리로 바꿔, SKIP이 깨져도 `uv`·`pnpm`을 찾지 못해 곧바로 빨갛게 했다.
- **명령은 `shutil.which`로 찾는다.** pre-commit은 명령을 띄우기 전에 `PATHEXT`로 실행 파일을 찾아(4.6.2
  `parse_shebang.py`의 `normalize_cmd`와 `find_executable`을 읽었다) Windows에서 `pnpm`을 `pnpm.cmd`로 찾아 주지만,
  러너의 `subprocess`는 경로 없이 `.cmd`를 띄우지 못한다. Windows에서의 실행은 이 Linux 컨테이너에서 재지 못했다.
- **출력.** 통과한 검사는 이름·결과·시간 한 줄, 실패한 검사는 그 뒤에 모은 출력까지 찍는다. 훅에 `verbose: true`를 두어
  통과한 커밋에서도 줄들이 보인다. ADR 초안의 "덩어리마다 이름·결과·시간 줄"을 이 모양으로 적어 넣었다.
- **`default_stages: [pre-commit]`.** 일지 02의 셀프 리뷰가 남긴 제안이다. 다섯 훅에 적었던 `stages`와 파일 검사 셋의
  `stages`를 걷고, 커밋 메시지 훅만 `stages: [commit-msg]`로 남겼다.

## 바꾼 것

- `tools/run_checks.py`(새 러너)와 `tests/tools/test_run_checks.py`(일곱).
- `.pre-commit-config.yaml`: 검사 일곱을 `parallel-checks` 훅 하나로 묶고 `default_stages`를 두었다. 옛 훅의 설명
  주석(web verify가 늘 도는 이유, e2e를 넣지 않는 이유)은 러너 훅 위로 옮겼다.
- `tools/hook_bash_gate_pipe.py`와 그 테스트: 러너도 게이트 명령이다. 파이프 뒤에 묻히면 경고한다.
- `docs/adr/0005-remote-ci-pr-from-day-one.md`: 승인된 이력. 본문에 포인터를 달 문장은 없었다(본문은 pre-commit의 훅
  구성을 말하지 않는다). ADR 0004·0013·0021·0026의 pre-commit 문장도 거짓이 되지 않는다(web verify는 러너 안에서 여전히
  pre-commit이 돈다).
- `docs/constitution/operations.md` 가드레일과 `docs/constitution/README.md`(3.0.16).
- `KICKOFF.md`: 커밋 메시지 훅 줄에 `default_stages`, 지침 검사는 러너의 `CHECKS`로, 파일 검사 둘의 `stages`를 걷고
  러너 항목을 더했다. `README.md`: 원천 표의 실행 자리와 `tools/` 줄.
- `.scratch/harness/probes/`: `run_checks_mutations.toml`과 README 행, `precommit_parallel.py` 독스트링 한 줄,
  `midturn_korean_mutations.toml`의 게이트 목록 변이 원문(정규식이 바뀌어 옛 원문이 없어졌다).
- `.scratch/retro-queue.md`: 133을 올렸다(아래 회고).

## 잔존 grep

`SKIP=`, `pyright 훅`·`pytest 훅`·`web verify 훅`·`web-verify 훅`, `pre-commit run <옛 id>`, `stages: [pre-commit]`을
저장소 전체에서 찾았다. 살아 있는 문서에 남은 것은 이 변경이 새로 쓴 문장과 기록(대기열 80·118의 닫힌 행)이다.
`CLAUDE.md`의 "다섯은 pre-commit이 돌린다"는 러너가 그 다섯을 pre-commit 안에서 돌리므로 그대로 참이다.

## 검사

- **러너 테스트.** `tests/tools/test_run_checks.py` 일곱이 초록이다. 변이 표 `run_checks_mutations.toml`의 열 변이가 모두
  빨강이다(하나씩 돌기, SKIP 무시와 공백, 실패에도 0, 실패 출력 빼기, 통과 출력 찍기, 명령을 못 찾을 때의 예외, 건너뜀
  알림, 설정에 같은 검사를 다시 등록, 게이트 목록에서 러너 빼기). `midturn_korean_mutations.toml`의 고친 변이도 빨강이고
  `--check`로 두 표의 원문이 모두 한 번씩 있다.
- **commit-msg 단계(손).** `uv run pre-commit run --hook-stage commit-msg --commit-msg-filename <파일>`이 0.3초이고 커밋
  메시지 검사 하나만 돈다. `default_stages`로 ruff 둘과 인용 대조의 Skipped 줄도 없어졌다.
- **커밋과 같은 조건(손).** 스테이지한 뒤 `uv run pre-commit run`이 79초였다. ruff 둘, 마크다운 표, 줄 구분 문자, 변이 표,
  인용 대조는 통과했다. 러너 안에서는 지침 검사, import-linter, 타입 우회 검사, 훅 러너(7.7초), pyright(18.4초)가
  통과했고, pytest(75.1초)와 web verify(77.5초)가 실패했다. pytest는 9 failed, 1642 passed이고 실패는 모두
  `test_open_session.py`의 `pwsh` 부재다. web verify는 Vitest 21파일 중 15파일 275건이 통과했고 브라우저 스토리 테스트가
  `chromium_headless_shell-1243`을 찾지 못했다. 둘 다 일지 02의 대기열 132와 같은 환경 탓이다. 실패한 검사의 출력은
  상태 줄 뒤에 그대로 찍혔다.
- **손으로 치는 검증 명령.** ruff check 통과, ruff format 통과, pyright 0 errors, 타입 우회 검사·지침 검사 종료 0.
  import-linter·pytest·web verify·훅 러너는 위 러너 실행의 결과다.

## 셀프 리뷰

## 회고

일지의 "다음"을 쓴 계기 훅으로 retro를 돌렸다. 후보 하나를 냈고 승인돼 대기열 133으로 갔다.

> 사용자(질문에 답): "대기열에 올린다 (Recommended)"

1. **[도구 경제] 변이 도구에 시간 제한이 없다(대기열 133).** 위 "어떻게 했나"의 되풀이 사건이다. `tools/mutate.py`는
   변이마다 명령이 끝날 때까지 기다리고, 끝나지 않으면 사람이 죽일 때까지 돈다. 죽이면 되돌리기도 돌지 않아 변이된 한 줄이
   파일에 남았다. 처방은 변이마다 시간 제한을 두고, 넘기면 자식 프로세스를 모두 끝낸 뒤 파일을 되돌리는 것이다. 1회차.

후보로 내지 않은 것: 도구 호출 사이의 영어 문장은 이 단계에서도 기존 훅(`hook_midturn_korean`)이 그 자리에서 잡았다.

## 다음

- 사용자 PC(Windows)에서 첫 커밋 때 러너가 `pnpm.cmd`를 찾아 web verify를 띄우는지, 일곱의 시간이 얼마인지 본다. 이
  컨테이너에서는 재지 못했다.
- 대기열 132(클라우드 환경 설정)는 그대로 사용자에게 있다.
