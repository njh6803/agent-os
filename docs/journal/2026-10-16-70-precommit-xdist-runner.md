# 2026-10-16 (70) pre-commit 러너의 pytest를 xdist로 나눠 돌린다

ADR 0035의 구현이다. 대기열 309를 닫는다. 브랜치는 `chore/precommit-xdist-runner`(워크트리
`precommit-xdist-runner`)이고, 앞 세션(일지 2026-10-16-68)이 연 새 세션에서 시작했다.

> 사용자: "대기열 309(pre-commit이 문서만 바꾼 커밋도 약 11.5분 걸리는 것)를 ADR 0035대로 구현하는 하네스 chore를 chore/precommit-xdist-runner 한 PR로 반영한다"

## 시작: 주 체크아웃 정리

지시문의 선행 조건(주 체크아웃 미갱신)대로 워크트리에 들어가기 전에 `tidy-checkouts`를 돌았다. 루트는 main이고 깨끗해
`feb64be1`에서 `17e80b32`(origin/main)로 앞당겼다. 병합된 로컬 브랜치 넷(`chore/retro-self-approve`,
`chore/token-usage-07-status`, `feature/06-large-result-hook`, `worktree-03-remaining-metrics-and-weekly-reports`)을 지웠다.
사람에게 넘긴 것은 둘이다. `confident-wright-2d3ebf`는 분리 HEAD인데 그 커밋이 origin/main에 없고,
`skill-check-and-retro-section`은 병합된 PR의 머리와 브랜치 끝이 다르다. 나머지 워크트리는 살아 있는 잠금 pid나 작업
디렉터리로 쥔 프로세스, 병합된 PR 없음 때문에 남겼다.

## 구현

- **`test_mutate`의 20초 미만 단언(가장 먼저).** `test_못_보는_것_뒤의_시험이_걸려도_첫_실패에서_멈춰_빨강이다`는 기준선과
  변이로 pytest를 두 번 띄우는 시간까지 20초 안에 들어야 했다. 시험이 재려는 것은 `-x`가 뒤의 시험을 돌리지 않는다는
  것이라, 걸린 시간 대신 뒤의 시험이 자기 전에 남기는 파일(`b-ran`)이 없는지를 본다. 변이의 시간 제한은 20초에서 40초로
  늘렸다(뒤의 시험은 60초를 자므로 `-x`가 빠지면 여전히 시간 제한에 걸려 `code == 0`도 빨개진다). 변이 둘로 고친 시험이
  `-x`를 잡는지 봤다(`.scratch/harness/probes/mutate_first_failure_mutations.toml`, 아래 검사 절).
- **의존성.** `uv add --dev pytest-xdist`가 3.8.0(execnet 2.1.2)을 `uv.lock`에 고정했다. ADR이 적은 3.8.0과 같아 major도
  같다. 다시 재지 않았다.
- **러너.** `tools/run_checks.py`에 `pytest_workers(cpu_count)`(논리 CPU의 절반, `None`이면 1, 1 아래로 내려가지 않는다)를
  두고 `CHECKS`의 pytest 명령을 `uv run pytest -q -n <수>`로 바꿨다. 시험이 먼저 빨갰다(`pytest_workers`가 없어 가져오기
  오류). 시험은 다섯 사례(16→8, 15→7, 2→1, 1→1, None→1)와 러너의 pytest 명령이 `-n`과 계산한 수를 갖는지를 본다.
- **문서.** `tech.md`의 테스트 행과 `operations.md` 가드레일의 러너 문장에 나누는 자리와 한 프로세스인 자리를 적고, 헌법을
  3.0.40으로 올렸다(patch, 형제의 가장 높은 판은 3.0.39). 대기열 309를 닫았다.
- **확인 도구.** ADR이 구현에 넘긴 두 벌 동시의 한 바퀴 도구로 `.scratch/harness/probes/precommit_xdist/confirm.py`를 지었다.
  러너의 `CHECKS`를 그대로 돌리고 pytest만 같은 명령을 감싸 출력을 남기며, 부를 때마다 `results/confirm_<시각>/`에 회차별
  파일을 남겨 둘을 동시에 띄워도 덮지 않는다. 표지는 검사마다의 결과 줄, 러너 명령의 `-n`, 통과 집계 줄, xdist가 뜬 줄이고
  두 벌 동시는 두 pytest가 겹쳤는지까지 본다.

## 확인

ADR 0035의 완료 조건을 `confirm.py`로 쟀다. 이 워크트리(커밋 전 작업 트리, 3396개)에서 프로세스 8개, 다른 세션이 도는 부하
아래였다. 두 벌 동시는 같은 체크아웃에서 돌았다.

- **한 바퀴 연속 5번.** 다섯 모두 통과(pytest 종료 코드 0, skip·error 0, 다른 검사의 빨강 없음). 한 바퀴 213.5~284.4초,
  pytest 146.7~228.9초(`results/confirm_20261016-185135/`).
- **두 벌 동시 3번.** 여섯 회차 모두 통과하고 세 번 모두 두 pytest가 겹쳤다. 한 바퀴 294.6~332.8초, pytest 243.2~287.2초
  (`results/confirm_20261016-191232/`).
- 대기열 309의 기록(약 11.5분)에 견주면 한 바퀴가 홀로 약 3.5~4.7분, 두 벌 동시 약 4.9~5.5분이다. 테스트 수가 3156개와
  3396개로 달라 어림이다.
- 시간에 민감한 사례 셋 가운데 고친 `test_mutate` 밖의 둘(`test_filesystem`의 재시도 사례, 대기열 306의 Ctrl_C 사례)은
  열한 회차에서 걸리지 않았다. ADR대로 걸리면 그 사례만 고친다. 운영 코드를 건드릴 일은 없어 사용자에게 묻지 않았다.

## 셀프 리뷰

`/code-review`의 두 축(base `17e80b32`, 커밋 0, 바뀐 파일 11개, 미추적 3개). 표준 축은 sonnet·high로 돌렸다. 확인 회차가
같은 워크트리에서 도는 동안이라 두 축에는 pytest 전체와 러너를 돌리지 말라고 했다. 반영은 확인 회차가 끝난 뒤에 했다.
`confirm.py`는 회차마다 새로 불려 도중에 고치면 측정이 섞인다.

**표준 축.** Critical·Major 없음, Minor 넷, Nit 넷.

- [Minor·유효] `test_mutate` 독스트링의 "홀로는 4.56초"는 ADR의 "홀로"(8개 홀로 10.60초)와 어긋난다. 4.56초는 한
  프로세스 값이다. 원인을 단정한 문장에는 ADR대로 어림이라고 붙인다.
- [Minor·유효] `confirm.py`가 skip·error를 측정의 결과로 센다고 적었는데, error만 있는 집계 줄(`1 error in 2.0s`, 수집
  오류의 모양)은 `passed`가 없어 "통과 집계 줄"이 빠진 회차, 곧 측정 아님이 된다. 표지를 "집계 줄"로 고쳐 error만 있는
  회차도 측정으로 센다.
- [Minor·유효] README가 가리키는 이 일지의 "확인 절"과 "검사 절"이 있어야 한다. 커밋 전에 대 본다.
- [Minor·유효] 대기열 309의 닫힘 문구에 완료 조건의 결과가 없고, ADR이 든 시간에 민감한 사례 셋 가운데 이 diff는
  `test_mutate` 하나만 고친다. 결과를 닫힘 문구와 이 일지에 적고, 남은 둘(`test_filesystem`의 재시도 사례, 대기열 306)이
  확인 회차에서 걸렸는지를 적는다(ADR은 걸리면 고친다고 했다).
- [Nit·판단] `CLAUDE.md`의 "pre-commit도 그 다섯의 명령을 돌린다"는 pytest에 `-n`이 붙어 글자 그대로는 아니다. 명세 축의
  판정과 함께 정한다.
- [Nit·남김] 러너 명령 시험이 `str(pytest_workers(os.cpu_count()))`로 구현을 되풀이한다. ADR이 시험에 요구한 것이 "명령이
  `-n`과 계산한 수를 갖는지"라 그대로 둔다. 독스트링의 "`-n`은 러너에만 있다"는 단언하지 않는 사실이라 문장을 결정의
  서술로 고친다.
- [Nit·남김] `confirm.py`의 `capture`가 `run_checks.run_one`과 닮았고(Duplicated Code), 행을 사전으로 다룬다(Primitive
  Obsession). 프로브이고 러너의 함수는 출력을 남기지 않아 그대로 둔다.
- [Nit·남김] CPU가 1~3개면 `-n 1`이라 프로세스 하나짜리 xdist의 시작 비용이 얹힌다. ADR이 정한 "1 아래로 내려가지
  않는다"의 결과이고 이 PC에서는 나지 않는다.

**명세 축.** Critical·Major 없음, 빠진 것 셋, 범위 넘침 0, 틀려 보이는 것 셋(표준 축과 겹친 하나 포함).

- [Minor·유효] `CLAUDE.md`의 "pre-commit도 그 다섯의 명령을 돌린다"가 글자 그대로는 거짓이다(표준 축의 Nit과 같은 자리).
  ADR이 갈음 규약을 이 문장에 기댄다. 두 축이 함께 짚었고 매 세션 실리는 문서라, 갈음은 그대로이고 pytest만 나눠 돌며
  한 프로세스에서만 나는 실패는 CI가 본다는 괄호를 붙인다.
- [Minor·유효] `tools/hook_bash_commit_msg.py`가 에이전트에게 보이는 문구에 pre-commit 단계의 검사가 약 8분이라는 시간이 남았다. 이
  PR이 그 시간을 바꾸므로 잔존이다. 썩는 수 대신 "몇 분"으로 고친다. 같은 파일 독스트링의 "약 7~8분의 게이트를 한 번 더
  돌았다"는 지난 사건의 기록이라 둔다.
- [Minor·근거 확인] 변이 표의 결과가 지금 표로 나온 것인지 수정 시각으로는 불확실하다는 지적. 표를 스크래치패드에서 돌린
  뒤 저장소로 복사해(18:43:19) 되돌린 파일들의 시각(18:42:49)보다 늦은 것이고 내용은 같다. 다만 시험 독스트링을 고치므로
  확인 회차가 끝난 뒤 다시 돌린다.
- [Nit·유효] `run_checks.py` 머리 문단의 "병목인 pytest"는 지금은 사실이 아니다(6개 이상에서는 web verify가 막대).
  지난 때로 고친다.
- [Nit·유효] `confirm.py` 독스트링은 다른 검사의 빨강도 마지막 줄의 통과 수에 적는다고 읽히는데, 통과 수는 pytest
  기준이다. 다른 검사의 빨강은 회차 줄의 `other_failed`에만 있다고 고친다.
- [Nit·유효] 시험의 변이 시간 제한을 20초에서 40초로 올린 이유가 시험에 없다. 독스트링에 적는다(60초 잠보다 짧아야
  `-x`가 빠졌을 때 걸린다).

잰 것 중 이상 없던 것: `pytest_workers`(None·0·1·2·3·-1→1, 16→8), 헌법 3.0.40 문단과 `tech.md`·`operations.md`의 새
문장, `mutate_first_failure_mutations.toml`의 `--check`와 표지, `uv.lock`의 3.8.0, ADR 0005·0021의 거부 문장(거부한 안의
근거라 포인터가 필요 없다). 명세 축은 ADR "바뀌는 곳"의 파일이 모두 diff에 있고, `ci.yml`과 `addopts`에 `-n`이 없으며,
`confirm.py`의 판정(failed·skipped·error·xfailed·deselected·집계 줄 없음을 넣어 봤다)이 통과 기준대로이고 두 벌의 겹침을
본다는 것을 확인했다.

**고친 것.** 위에서 유효로 판정한 것을 모두 고쳤다(러너 명령 시험의 독스트링을 결정의 서술로, `test_mutate` 독스트링의 한
프로세스·홀로·어림과 시간 제한의 이유,
`confirm.py`의 집계 줄 표지와 `other_failed` 문장, `CLAUDE.md`의 괄호, `hook_bash_commit_msg`의 "몇 분", `run_checks.py`의
"그때 병목이던", 대기열 309 닫힘 문구의 결과와 남은 사례). `confirm.py`의 표지는 처음에 문구만 바꾸고 조건(`"passed" not
in counts`)을 그대로 두어, 경계 입력(`1 error in 2.0s`)을 넣어 보고서야 조건을 `not counts`로 고쳤다. 고친 뒤 그 입력은
측정이고 통과가 아니며, 집계 줄이 없는 출력만 측정 아님이다(손으로 불러 봤다).

**남긴 것.** Nit 셋(러너 명령 시험의 구현 되풀이, `confirm.py`의 Duplicated Code·Primitive Obsession, CPU 1~3개의 `-n 1`).
이유는 위 지적마다 적었다.

**다시 돌린 것.** 변이 표를 다시 돌렸다(아래 검사 절). 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 사실 문장):

1. `test_mutate` 독스트링: "pytest 두 벌을 동시에 돌린 부하 아래에서 20.3초와 21.6초로 빨갰다(… 한 프로세스로는 4.56초,
   xdist 8개 홀로는 10.60초였다. 원인이 부하의 지연이라는 것은 어림이다)."
2. 같은 독스트링: "시간 제한은 기동이 늘어도 남게 40초로 두되, test_b 의 60초 잠보다 짧아야 `-x` 가 빠진 변이가 시간 제한에
   걸려 빨개진다."
3. `confirm.py`: "2026-10-16 의 두 실행은 표지가 '통과 집계 줄'이던 앞 판으로 돌았다. 모든 회차에 `passed` 가 있어 판정은
   지금 판과 같다."
4. `CLAUDE.md`: "pytest만 프로세스를 나눠 돌고, 한 프로세스에서만 나는 실패는 CI가 본다."
5. README의 변이 표 행: "첫째가 시간 제한 40초보다 긴 것은 끊은 뒤 `taskkill`과 출력 배출(`_DRAIN_SECONDS`)을 기다리는
   시간이 붙어서로 본다(코드를 읽었다)."
6. 대기열 309 닫힘: "`test_filesystem`의 재시도 사례와 대기열 306은 그 회차에서 걸리지 않아 열린 채다."

## 검사

- 변이 `.scratch/harness/probes/mutate_first_failure_mutations.toml`: 두 번 돌려 두 번 모두 변이 둘이 기대대로 빨갰다. 처음
  고친 뒤 기준선 6.88초, 첫째(`-x`를 붙이지 않는다) 62.42초, 둘째(거기에 뒤의 시험이 자지 않는다) 6.05초. 셀프 리뷰를
  반영한 뒤 기준선 26.85초, 첫째 86.03초, 둘째 25.82초(다른 세션이 도는 부하 아래).
- 러너 시험: `pytest_workers`가 없을 때 가져오기 오류로 빨갰고(종료 2), 구현 뒤 15개 통과.
- `ruff check .`, `ruff format --check .`, 바뀐 파이썬 파일의 `pyright`, `check_md_tables.py`, `check_line_separators.py`,
  `check_type_escapes.py`, `check_instructions.py`: 모두 통과.
- `confirm.py`의 판정을 경계 입력 넷(`1 error`, `1 skipped`, 통과, 집계 줄 없음)과 다른 검사의 빨강 하나로 불러 봤다.
- 첫 커밋 시도는 pre-commit에 막혔다(종료 1). 새 러너(xdist 8개)로 돈 첫 실제 커밋이었고 러너의 검사 여덟 가운데 pytest만
  빨갰다. pytest 160.8초(3395개 통과, 1개 실패), web-verify 211.7초, run-hooks 67.7초, pyright 27.0초였다. 실패는 하나의
  까닭이다. `confirm.py`의 `capture`가 pytest 출력을 바이트로 받아 `\r\n`을 둔 채 텍스트 모드로 써서 윈도에서 줄 끝이
  `\r\r\n`이 됐고, 그 홀로 선 CR을 줄 구분 문자 훅과 같은 판정을 하는 pytest의 저장소 상태 테스트
  (`test_이_저장소의_추적_파일에_날것_줄_구분_문자가_없다`)가 함께 잡았다. `capture`가 `\r\n`을 `\n`으로 바꾸게 고치고,
  저장한 출력 11개의 줄 끝을 스크래치 스크립트로 `\n`으로 바로잡았다(파일마다 64줄, 내용은 그대로).
- 이 실패로 커밋 뒤 경계에 온 것이 아니어서, 함께 온 인계 계기(세션 컨텍스트 약 40만 토큰)는 `next-session` "인계할 때" 1의
  인계하지 않는 때(계기를 낸 명령이 실패했다)로 보고 이 세션에서 이었다.
