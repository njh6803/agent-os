# 2026-10-07 (03) pre-commit의 always_run 검사 일곱을 러너 하나가 함께 띄운다

일지 2026-10-07-02의 세션이 이어서 했다. 같은 클라우드 세션, 같은 브랜치 `claude/funny-planck-itf28j`이고 기준은
`162ae54`(PR #156 병합 뒤)다.

## 계기

일지 02의 끝에서 러너 훅의 ADR 초안(ADR 0005 이력)을 보였다.

> 사용자: "초안 승인"

## 어떻게 했나

- **테스트 먼저.** `tests/tools/test_run_checks.py`를 먼저 쓰고 모듈이 없어 수집 오류(빨강)인 것을 본 뒤 러너를 썼다.
  설정을 바꾸기 전에는 저장소 상태 테스트 하나가 빨갰고, 설정을 바꾼 뒤 모두 초록이다. 셀프 리뷰가 더하게 한 둘(띄우지
  못한 명령, CLI의 알려진 빨강)도 앞의 것은 빨강을 본 뒤 고쳤다.
- **함께 띄우는지는 시간으로 재지 않는다.** 두 검사가 서로의 표지 파일을 기다리게 했다. 하나씩 돌면 앞의 것이 20초를
  기다리다 실패한다. 러너 안에서 pyright·web verify와 함께 돌아 붐벼도 거짓 빨강이 나지 않을 여유다.
- **CLI 테스트가 진짜 검사에 닿지 않게 했다.** 첫 판의 CLI 테스트는 SKIP으로 일곱을 모두 건너뛰는 것에만 기댔다. 변이
  표의 "SKIP 을 읽지 않는다"를 돌리자 러너가 진짜 pytest를 띄우고, 그 pytest의 CLI 테스트가 러너를 또 띄워 10분이 넘도록
  돌고 돌았다(프로세스 37개를 손으로 죽였다. 변이가 70행에 남아 있어 손으로 되돌렸다). 그래서 CLI 테스트는 `PATH`를 빈
  임시 디렉터리로 바꿔, SKIP이 깨져도 `uv`·`pnpm`을 찾지 못해 곧바로 끝나게 했다.
- **명령은 `shutil.which`로 찾는다.** pre-commit은 명령을 띄우기 전에 `PATHEXT`로 실행 파일을 찾아(4.6.2
  `parse_shebang.py`의 `normalize_cmd`와 `find_executable`을 읽었다) Windows에서 `pnpm`을 `pnpm.cmd`로 찾아 주지만,
  러너의 `subprocess`는 경로 없이 `.cmd`를 띄우지 못한다. Windows에서의 실행은 이 Linux 컨테이너에서 재지 못했다.
- **출력.** 통과한 검사는 이름·결과·시간 한 줄, 실패한 검사는 그 뒤에 모은 출력까지 찍는다. 훅에 `verbose: true`를 두어
  통과한 커밋에서도 줄들이 보인다. 승인된 초안은 검사마다 출력을 한 덩어리로 찍는다고 적었는데, pre-commit은 통과한 훅의
  출력을 보이지 않으므로 이 모양으로 바꿔 ADR에 적었다. 같은 ADR에 겹침 테스트 문장도 더했다. 승인 뒤에 바뀐 이 두 곳은
  이 단계의 답에서 사용자에게 알린다(셀프 리뷰 명세 축).
- **`default_stages: [pre-commit]`.** 일지 02의 셀프 리뷰가 남긴 제안이다. 다섯 훅에 적었던 `stages`와 파일 검사 셋의
  `stages`를 걷고, 커밋 메시지 훅만 `stages: [commit-msg]`로 남겼다.
- **커밋이 둘이다.** 셀프 리뷰가 도는 동안 세션의 Stop 훅이 미커밋 변경을 커밋·푸시하라고 해, 리뷰 전의 판을 `cf4ba21`로
  먼저 올리고 리뷰 반영을 다음 커밋에 담았다.

## 바꾼 것

- `tools/run_checks.py`(새 러너)와 `tests/tools/test_run_checks.py`(아홉).
- `.pre-commit-config.yaml`: 검사 일곱을 `parallel-checks` 훅 하나로 묶고 `default_stages`를 두었다. 옛 훅의 설명
  주석(web verify가 늘 도는 이유, e2e를 넣지 않는 이유)은 러너 훅 위로 옮겼다. 검사 목록은 러너의 `CHECKS` 하나에만 있다.
- `tools/hook_bash_gate_pipe.py`와 그 테스트: 러너도 판정 명령으로 본다. 파이프 뒤에 묻히면 경고한다.
- `docs/adr/0005-remote-ci-pr-from-day-one.md`: 승인된 이력. 본문에 포인터를 달 문장은 없었다(본문은 pre-commit의 훅
  구성을 말하지 않는다). ADR 0021·0026의 pre-commit 문장은 web verify가 러너 안에서 여전히 pre-commit으로 돌아 참이다.
  ADR 0004의 "검사 넷"과 0013의 "pre-commit 훅과 CI 스텝이 하나씩 는다"는 결정 때의 셈이라 포인터를 달지 않는다
  (`.claude/rules/adr.md`의 "달지 않는 것").
- `docs/constitution/operations.md` 가드레일과 `docs/constitution/README.md`(3.0.16).
- `KICKOFF.md`: 커밋 메시지 훅 줄에 `default_stages`, 지침 검사는 러너의 `CHECKS`로, 파일 검사 둘의 `stages`를 걷고
  러너 항목을 더했다. `README.md`: 원천 표의 실행 자리와 `tools/` 줄. `.claude/rules/tools.md`: GIT 환경을 벗기는 쪽의
  "러너"를 "훅 러너"로(러너가 둘이 됐다).
- `.scratch/harness/probes/`: `run_checks_mutations.toml`과 README 행, `precommit_parallel.py` 독스트링 한 줄,
  `midturn_korean_mutations.toml`의 게이트 목록 변이 원문(정규식이 바뀌어 옛 원문이 없어졌다).
- `.scratch/retro-queue.md`: 133을 올렸다(아래 회고).

## 잔존 grep

`SKIP=`, `pyright 훅`·`pytest 훅`·`web verify 훅`·`web-verify 훅`, `pre-commit run <옛 id>`, `stages: [pre-commit]`을
저장소 전체에서 찾았다. 살아 있는 문서에 남은 것은 이 변경이 새로 쓴 문장과 기록(대기열 80·118의 닫힌 행)이다.
`CLAUDE.md`의 "다섯은 pre-commit이 돌린다"는 러너가 그 다섯을 pre-commit 안에서 돌리므로 그대로 참이다.

## 검사

- **러너 테스트.** `tests/tools/test_run_checks.py` 아홉이 초록이다. 변이 표 `run_checks_mutations.toml`의 열둘이 모두
  빨강이다(하나씩 돌기, SKIP 무시와 공백, 실패에도 0, 실패 출력 빼기, 통과 출력 찍기, 띄우지 못한 명령을 잡지 않기, main의
  종료 코드 버리기, 건너뜀 알림, 설정에 같은 검사를 같은 명령이나 같은 id로 다시 등록, 게이트 목록에서 러너 빼기).
  `midturn_korean_mutations.toml`의 고친 변이도 빨강이고 `--check`로 두 표의 원문이 모두 한 번씩 있다.
- **commit-msg 단계(손).** `uv run pre-commit run --hook-stage commit-msg --commit-msg-filename <파일>`이 0.3초이고 커밋
  메시지 검사 하나만 돈다. `default_stages`로 ruff 둘과 인용 대조의 Skipped 줄도 없어졌다.
- **커밋과 같은 조건(손).** 리뷰 반영 뒤 스테이지하고 `uv run pre-commit run`을 쳐 74초였다. ruff 둘, 마크다운
  표, 줄 구분 문자, 변이 표, 인용 대조는 통과했다. 러너 안에서는 지침 검사, import-linter, 타입 우회 검사, 훅
  러너(7.1초), pyright(16.8초)가 통과했고, pytest(71.6초)와 web verify(72.8초)가 실패했다. pytest는 9 failed,
  1644 passed이고 실패는 모두 `test_open_session.py`의 `pwsh` 부재다. web verify는 Vitest 21파일 중 15파일이
  통과했고 브라우저 스토리 테스트가 `chromium_headless_shell-1243`을 찾지 못했다. 둘 다 일지 02의 대기열 132와 같은
  환경 탓이다. 실패한 검사의 출력은 상태 줄 뒤에 그대로 찍혔다. 리뷰 전의 판(`cf4ba21`)에서도 79초에 같은 결과였다.
- **손으로 치는 검증 명령.** ruff check와 ruff format 통과, pyright 0 errors, 타입 우회 검사·지침 검사 종료 0.
  import-linter·pytest·web verify·훅 러너는 위 러너 실행의 결과다.

## 셀프 리뷰

`/code-review`, base `ca8a191`, 스테이지 14파일, 미추적 1(이 일지), 커밋 0. `tools/`와 `tests/`가 바뀌어 두 축 모두 기본
모델로 돌렸다. 명세는 승인된 ADR 초안이다. 두 축 모두 Critical은 없었다.

- **고쳤다, 표준 하드.** CLI 테스트가 종료 코드 0만 봐 `sys.exit(main())`을 `main()`으로 바꾸는 변이가 살았다. 검사 하나만
  남기고 `PATH`를 비워 알려진 빨강(1과 Failed 줄)을 내는 CLI 테스트를 더하고 그 변이를 표에 넣었다. 측정 수(145.5초,
  73.7초)를 적은 ADR, 러너 독스트링, `KICKOFF.md`에 잰 트리(`cbb6a6c`, 스토리 테스트 전)를 밝혔다. 일지 02가 미래형으로
  남긴 "프로브를 다시 돌린다"는 아래 "다음"으로 넘겼다.
- **고쳤다, 두 축의 Minor.** 찾은 뒤 띄우지 못한 명령(실행 형식 오류 등)이 traceback으로 터지던 것을 실패 한 줄로 바꾸고
  테스트와 변이를 더했다. 겹침 테스트가 같은 id로 다시 등록한 훅도 보게 하고 그 변이를 더했으며, ADR 문장은 테스트가
  보는 만큼(글자 그대로의 명령과 같은 id)으로 적었다. 검사 수를 7로 묶던 단언은 비어 있지 않은지로 바꿨다.
- **고쳤다, 판단.** 검사 목록을 훅 `name`, 설정 주석, `operations.md`, 게이트 테스트 독스트링에서 다시 나열하던 것을
  `CHECKS`를 가리키게 줄였다. `operations.md`의 "나머지 `always_run` 검사"는 ruff가 `always_run`이 아니라 "파일을 고치지
  않는 `always_run` 검사"로 고쳤다. 파이프 경고 훅의 "게이트다"는 러너가 게이트 여럿을 띄우는 명령이라 게이트 수는 늘지 않는다는 문장으로 고쳐
  헌법 README의 "게이트 수는 그대로다"와 맞췄다. `run`의 독스트링에 `environ`은 SKIP에만 쓰고 자식은 이 프로세스의
  환경을 물려받는다고 적었다. 이 일지가 ADR 0013의 문장을 두고 든 근거를 `adr.md`의 "달지 않는 것"으로 바로잡았다.
- **남겼다.** Windows에서 상태 줄(UTF-8)과 `PYTHONUTF8` 없는 자식의 출력(cp949)이 한 스트림에 섞일 수 있다. 예전에도
  pre-commit이 훅마다 바이트를 그대로 넘겨 회귀가 아니다. `Passed`·`Failed`·`Skipped`는 `tools.md`의 "문자열은 한국어"와
  어긋나지만, pre-commit 출력과 같은 말이라 한 화면에서 읽히고 훅 러너의 `ok`·`FAIL`이 선례다.

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
- 일지 02의 "다음"에 적은, 러너를 구현할 때 프로브를 다시 돌린다는 일은 닫지 못하고 넘긴다. PR #156 뒤 이 컨테이너에서는 스토리 테스트가
  브라우저를 찾지 못해 web verify가 실패하는 채로 끝나, 가장 긴 검사를 잴 수 없었다(위 검사). ADR의 "가장 긴 pytest
  만큼"이 지금도 맞는지는 브라우저가 있는 기계에서 `precommit_parallel.py all`로 다시 잰다.
- 대기열 132(클라우드 환경 설정)는 그대로 사용자에게 있다.
