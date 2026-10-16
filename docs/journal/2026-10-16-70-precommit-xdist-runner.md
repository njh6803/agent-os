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
- 다시 친 커밋 `fd61175b`의 pre-commit은 `Skipped` 없이 모두 통과했다. 러너는 check-instructions 0.8초, zizmor 1.1초,
  lint-imports 2.1초, check-type-escapes 5.2초, pyright 28.0초, run-hooks 72.6초, pytest 174.4초, web-verify 227.2초였고,
  표·줄 구분 문자·변이 표·인용 대조·커밋 메시지도 통과했다. 인용 대조의 경고 둘은 헌법 판 문단의 옛 판 서술에 있던 인용이다
  (그 문단이 한 줄이라 판을 올리며 줄 전체가 더한 줄로 잡혔다).

## 인계 (커밋 뒤)

`fd61175b`를 커밋한 뒤 인계 계기(세션 컨텍스트 약 42.7만 토큰, 경계 `커밋 뒤`)가 다시 왔고, 이번에는 커밋이 성공해
`next-session` "인계할 때"의 인계하지 않는 때 넷 가운데 어느 것에도 들지 않았다(요청 범위는 PR과 병합까지, 지시문의
이어받을 상태는 `인계:`로 시작하지 않고, 이 일지에 `인계 못함` 줄이 없다). 이 세션의 지금 제목은
`chore/precommit-xdist-runner`이고 넘기며 `chore/precommit-xdist-runner (인계함)`으로 바꾼다. 이 절은 커밋하지 않았다.
새 세션이 이 파일을 이어 쓰고 커밋한다.

이 세션이 번복하거나 고친 것: `confirm.py`의 표지 조건(문구만 바꿨다가 경계 입력으로 조건을 고쳤다), 저장한 출력의 겹친
CR(첫 커밋 시도가 막혀 고쳤다). 결정은 모두 ADR 0035 안이고 사용자에게 물은 것은 없다.

남은 단계: origin/main을 합친 뒤 PR 직전 리뷰의 대체 둘(`/security-review`, `bug-perf-review`. CodeRabbit CLI는
`coderabbit auth status`가 `Seat: not assigned`였다), 그 반영, 이 일지의 PR 직전 리뷰·회고·다음 절, 푸시, PR, 봇 회차,
병합. `bug-perf-review`에 밀 주장 여섯은 위 셀프 리뷰 절에 있다.

지시문:

```
다음 작업: 대기열 309, pre-commit의 pytest를 러너에서만 xdist로 나눠 돌린다(ADR 0035의 구현)
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 309(pre-commit이 문서만 바꾼 커밋도 약 11.5분 걸리는 것)를 ADR 0035대로 구현하는 하네스 chore를 chore/precommit-xdist-runner 한 PR로 반영한다
브랜치: chore/precommit-xdist-runner
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-16-70-precommit-xdist-runner.md(끝의 인계 절은 아직 커밋하지 않았다), docs/adr/0035-precommit-pytest-is-split-by-xdist-in-the-runner.md
이어받을 상태: 인계: 커밋 뒤. 커밋 fd61175b까지 구현, 셀프 리뷰 반영, ADR 0035 완료 조건 확인(한 바퀴 연속 5번과 두 벌 동시 3번이 모두 통과)을 마쳤다. 아직 푸시하지 않았고 PR도 없다. 남은 단계는 origin/main을 합친 뒤 PR 직전 리뷰 대체 둘(/security-review와 bug-perf-review. CodeRabbit CLI는 Seat: not assigned였다), 반영, 일지의 PR 직전 리뷰·회고·다음 절, 푸시, PR, 봇 회차, 병합이다. bug-perf-review 브리프에 밀 주장 여섯은 일지의 셀프 리뷰 절에 있다. 일지 파일은 docs/journal/2026-10-16-70-precommit-xdist-runner.md이고 끝의 인계 절이 커밋되지 않은 채 워크트리에 있다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-16T10:45:44Z

## 이어받기 (새 세션)

새 세션은 첫 턴 훅대로 제목을 `chore/precommit-xdist-runner`로 바꾼 뒤 `EnterWorktree(path)`로 이 워크트리에 들어가려
했다. 도구가 `belongs to another running Claude Code session (locked: claude session precommit-xdist-runner (pid
41220))`로 거부했다. pid 41220은 인계한 앞 세션(제목 `chore/precommit-xdist-runner (인계함)`)의 `claude.exe`였고, 그
세션은 인계를 마친 뒤에도 `list_sessions`에서 `isRunning`이었다(20초 뒤에 다시 봐도 같았다). 앱이 연 세션은 턴을
끝내도 프로세스가 남아 잠금의 pid가 살아 있다.

ADR 0032는 `locked` 줄을 막는 이유로 쓰지 않고 세션이 쓰는지를 제목으로 보기로 했고, 앞 세션의 제목은 `(인계함)`이라
그 확인을 지난다. 그래서 `git worktree unlock`으로 잠금만 풀고 `EnterWorktree(path)`로 들어왔다. 앞 세션은 `next-session`
"인계할 때" 6대로 다시 깨어나도 일하지 않는다. 이 틈은 회고 후보로 올린다(아래 회고).

origin/main은 `17e80b32`에서 움직이지 않아 합칠 것이 없었고, `sibling_overlap.py`는 번호 겹침 없음이었다.

## PR 직전 리뷰

CodeRabbit CLI는 여전히 `Seat: not assigned`라 대체 둘을 나란히 돌렸다.

- **`/security-review`**: 발견 없음. 식별 서브태스크가 후보를 내지 않아 거르는 서브태스크는 띄우지 않았다. 측정 출력도
  비밀 모양의 낱말로 찾았지만 나오지 않았다.
- **`bug-perf-review`**(기준 `17e80b32`, 62개 파일, 호출 40): 유효 2, 보류 1, 오탐 0. 밀 주장 여섯 가운데 다섯은 근거와
  맞았다.
  - [Minor·유효] 밀 주장 5(README 변이 표 행의 "첫째가 시간 제한 40초보다 긴 것은 `taskkill`과 출력 배출을 기다리는
    시간이 붙어서"). 리뷰가 `tools/mutate.py`의 `run_command`로 60초 자는 프로세스를 5초에 끊어 보니 끊은 뒤 붙는
    시간이 0.6~0.7초였다(리뷰의 스크래치 스크립트, 잴 때의 부하는 모른다). 첫째는 기준선에 40초를 더한 값보다도 15.5초와
    19.2초 길어 그 서술로 설명되지 않는다. 원인 문장을 "그 까닭은 재지 않았다"로 바꿨고 수는 그대로 뒀다.
  - [Minor·유효] `confirm.py`의 `run_round`가 러너의 출력을 `\r\n`을 둔 채 텍스트 모드로 써, 첫 커밋 시도를 막은 것과
    같은 홀로 선 CR이 생긴다. 러너는 실패한 검사의 출력 바이트를 그대로 옮긴다(`tools/run_checks.py`의 `run`). 앞
    세션은 `capture`만 고쳤다. 가짜 실패 검사 하나만 둔 `run_round`를 불러 고치기 전에 `\r\r\n` 둘을 재현했고,
    `.replace("\r\n", "\n")`을 더한 뒤 0이 됐다(스크래치 스크립트로 손으로 봤다). 저장한 11회차는 `other_failed`가 비어
    영향이 없다.
  - [Minor·보류] `os.cpu_count()`가 컨테이너의 CPU 한도를 반영하지 않으면 클라우드 세션의 러너가 `-n`을 과하게 붙인다.
    ADR 0035와 러너 독스트링의 못 보는 것에 이미 있고, 클라우드 컨테이너에서 `os.cpu_count()`와
    `len(os.sched_getaffinity(0))`를 함께 찍어야 닫힌다. 고치지 않고 PR 체크리스트에 판정과 값을 적는다.
- 리뷰가 시나리오로 따라가 문제없다고 본 것: `pytest_workers`의 경계(`None`·0·1·2·3·-1→1, 15→7, 16→8), xdist가 없는
  체크아웃(러너의 `uv run`이 개발 그룹을 동기화해 깔고, 동기화를 끈 환경이면 `unrecognized arguments: -n`과 종료 4로
  뚜렷하게 빨갛다. 손으로 돌리지는 않았다), skip 판정(ADR 0035의 `skip_under_xdist.py` 결과), 두 벌 동시의 출력 경로.

## 회고

후보 셋, 승인 하나, 기각 둘, 넘김 0이다. 사람에게 넘긴 것이 없어 답을 기다리지 않았다.

1. **승인 → 대기열 326.** 인계로 연 새 세션의 `EnterWorktree(path)`가 앞 세션의 살아 있는 pid 잠금에 거부됐다(위
   "이어받기"). 사건은 이 세션에서 났고, 층은 행동이 일어나는 자리(`next-session` "인계할 때" 4의 열기 직전, 넘기는
   세션이 자기 잠금을 푼다)의 단계 문장이며, PR 하나로 되돌릴 수 있다. 판정할 검사가 없는 것은 잠금을 풀어야 하는
   때가 인계라는 절차 안에서만 정해지기 때문이다. 받는 쪽이 남의 잠금을 푸는 상시 규칙은 후보로 내지 않았다. 넘기는
   쪽이 풀면 원인이 사라지고, 받는 쪽 규칙은 도구의 잠금 거부를 느슨하게 하는 것이라 넘김 몫이다. 이번에는 ADR
   0032의 제목 판정에 기대 한 번 풀었다. 이 PR의 범위(대기열 309) 밖이고 바꾼 스킬은 새 세션에서 불러 봐야 해서 이
   세션에서는 반영하지 않는다.
2. **기각.** `confirm.py`의 `run_round`가 `capture`와 같은 줄 끝 결함을 남겼다(PR 직전 리뷰). 그 결과인 홀로 선 CR이
   든 파일은 커밋 때 줄 구분 문자 검사(pre-commit의 훅과 pytest의 저장소 상태 테스트)가 이미 막는다. 첫 커밋 시도에서
   실제로 막았다.
3. **기각.** 셀프 리뷰를 반영하며 쓴 원인 문장(밀 주장 5)이 근거와 어긋났다. 대기열 260을 닫은 장치(`code-review` 6단계
   1 끝, 새로 쓴 사실 문장을 PR 직전 리뷰에 밀 주장으로 나열한다)가 의도대로 다음 층에서 잡았다. 이미 있는 지침이
   잡은 것이다.

## 인계 (PR 연 뒤)

이 세션(위 "이어받기"부터)은 앞 세션의 지시문으로 열렸다. 사용자 프롬프트는 그 지시문이고 첫 줄은 아래다. 나머지 열 줄은
위 "인계 (커밋 뒤)"의 지시문과 같다.

> 사용자: "대기열 309(pre-commit이 문서만 바꾼 커밋도 약 11.5분 걸리는 것)를 ADR 0035대로 구현하는 하네스 chore를 chore/precommit-xdist-runner 한 PR로 반영한다"

반영 커밋 `3cabd586`을 커밋한 뒤 인계 계기(약 28.4만 토큰, 경계 `커밋 뒤`)가 왔지만, 지시문의 이어받을 상태가 같은 경계
(`인계: 커밋 뒤`)로 시작해 `next-session` "인계할 때" 1의 인계하지 않는 때로 보고 이었다. 푸시하고 PR #281을 연 뒤 계기
(약 31.2만 토큰, 경계 `PR 연 뒤`)가 다시 왔고, 이번에는 넷 가운데 어느 것에도 들지 않는다(요청 범위는 병합까지, 이어받을
상태의 경계가 다르다, 이 일지에 `인계 못함` 줄이 없다). 그래서 넘긴다. 이 세션의 지금 제목은
`chore/precommit-xdist-runner`이고 넘기며 `chore/precommit-xdist-runner (인계함)`으로 바꾼다. 이 절은 커밋하지 않았다.
새 세션이 이 파일을 이어 쓰고 커밋한다.

이 세션의 결정: 앞 세션의 살아 있는 pid 잠금을 ADR 0032의 제목 판정에 기대 풀었다(위 "이어받기"). PR 직전 리뷰의 유효
둘을 고치고 보류 하나를 PR 체크리스트에 적었다. 회고는 승인 하나(대기열 326)와 기각 둘이다. 이 세션이 고친 것은 앞 세션이
쓴 README 변이 표 행의 원인 문장과 `confirm.py`의 `run_round` 줄 끝이다. 사용자에게 물은 것은 없다.

이 워크트리는 `path`로 들어온 뒤 다시 잠기지 않아(`git worktree list --porcelain`에 `locked` 줄이 없다) 새 세션의
`EnterWorktree(path)`는 잠금에 막히지 않을 것으로 본다. "이어받기"에서 본 앞 세션의 `isRunning`은 그 세션이 열기의 끝을
기다리던 턴 안이었다. 그 세션이 턴을 끝내 `isRunning: false`가 된 뒤(11:12Z 무렵)에도 pid 41220은 살아 있어, 턴을 끝내도
프로세스와 잠금이 남는다는 대기열 326의 서술을 손으로 봤다. 남은 단계: PR #281의 봇 회차(첫 `@coderabbitai review` 코멘트와
`tools/wait_ci.py` 대기부터), 반영, 병합(`next-session` "워크트리에서 병합할 때"), 병합 뒤의 다음 지시문.

지시문:

```
다음 작업: 대기열 309, pre-commit의 pytest를 러너에서만 xdist로 나눠 돌린다(ADR 0035의 구현)
다음 단계: PR 반영·병합
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 309(pre-commit이 문서만 바꾼 커밋도 약 11.5분 걸리는 것)를 ADR 0035대로 구현하는 하네스 chore를 chore/precommit-xdist-runner 한 PR로 반영한다
브랜치: chore/precommit-xdist-runner
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-16-70-precommit-xdist-runner.md(끝의 "인계 (PR 연 뒤)" 절은 아직 커밋하지 않았다), docs/adr/0035-precommit-pytest-is-split-by-xdist-in-the-runner.md
이어받을 상태: 인계: PR 연 뒤. PR #281을 열었고 머리는 3cabd586이다(구현 fd61175b, PR 직전 리뷰 반영·일지의 PR 직전 리뷰·회고·다음 절 3cabd586). next-session 순서 1의 2(봇 회차)부터 한다. 첫 @coderabbitai review 코멘트도 아직 남기지 않았다. PR 직전 리뷰의 보류 하나(os.cpu_count()와 컨테이너 CPU 한도)는 PR 체크리스트에 적었다. 일지 끝의 "인계 (PR 연 뒤)" 절은 커밋되지 않은 채 워크트리에 있고, 새 세션이 이 파일을 이어 쓰고 커밋한다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-16T11:11:58Z

## 이어받기 (PR 반영 세션)

이 세션은 위 "인계 (PR 연 뒤)"의 지시문으로 열렸고, 사용자 프롬프트는 그 지시문 그대로다. 첫 턴 훅대로 제목을
`chore/precommit-xdist-runner`로 바꿨다(앱이 지은 제목이라 묻지 않고 바뀌었다). `EnterWorktree(path)`는 앞 절이 본 대로
잠금에 막히지 않았다. origin/main은 `17e80b32`에서 움직이지 않았고 `sibling_overlap.py`는 번호 겹침 없음이었다.

넘겨받은 "인계 (PR 연 뒤)" 절은 그 앞의 "다음" 절 뒤에 붙어 있었다. 다음 세션은 최신 일지 끝의 "다음"을 읽으므로, 이
세션의 절을 이어 쓰며 "다음"을 파일 끝으로 옮겼다(아래 회고 2).

## PR 봇 회차

PR #281, 머리 `3cabd586`.

- CI의 python·web·e2e·visual·verify가 모두 통과했다.
- claude-review는 계정의 주간 사용량 한도로 빨갰다. 실행 38892015837에서 Claude의 말이 "You've hit your weekly limit ·
  resets Oct 18, 9pm (UTC)"이고 결과 블록이 `"is_error": true`와 `"terminal_reason": "api_error"`다. 리뷰 없음이고,
  `operations.md` 리뷰 파이프라인 3대로 풀리기를 기다리지 않는다.
- CodeRabbit은 PR을 열 때 `Review skipped: manual review required for this OSS repository`였다. 11:15Z에 남긴
  `@coderabbitai review`는 OSS 한도에 걸렸다(`Review rate limited`, 다음 리뷰는 17분 뒤).
- 요청 직후 띄운 `tools/wait_ci.py 281`은 CodeRabbit을 기다리지 않고 `끝: 실패 claude-review`(종료 1)로 끝났다. 그 도구는
  나머지 검사가 끝났는데 실패가 있으면 리뷰 요청을 기다리지 않고, claude-review의 한도 빨강도 실패로 센다(독스트링의 못
  보는 것 "claude-review가 계정 한도로 빨간 것과 진짜 실패의 차이"). 그래서 한도가 풀릴 때까지 백그라운드 `sleep`으로
  기다렸다(아래 회고 1).
- 한도가 풀린 뒤(11:35Z) 이 일지 절을 커밋한 머리 `59607dad`에 CodeRabbit을 다시 요청했다. 선례(일지
  2026-10-07-11·2026-10-13-33)가 그렇게 했고, 2026-10-13-33에서는 그 리뷰가 Major 하나를 냈다.
- 문서만 바꾼 그 커밋의 pre-commit은 3분 38초였다(러너 214.2초, 그 안에서 pytest 156.5초, web-verify 213.9초. ruff 둘과
  변이 표 검사는 `.py`와 변이 표가 없어 `Skipped`). 대기열 309가 적은 문서 커밋의 약 11.5분에 견주는 첫 실제 커밋의 값이다.
- claude-review는 `59607dad`에서도 같은 주간 한도로 빨갰다(실행 38893766712).
- **CodeRabbit 첫 회차(`59607dad`).** 지적 하나(Minor). 첫 회차라 지적마다 판단했고 근거가 맞아 고쳤다.
  - [Minor] `confirm.py`의 `new_folder`가 초 단위 시각만으로 폴더를 `exist_ok` 없이 만들어, 같은 초에 따로 부른 둘째
    호출이 `FileExistsError`로 측정을 시작하지 못했다. 독스트링이 약속한 "부를 때마다 새 폴더"와 어긋난다. 봇이 제안한
    `tempfile.mkdtemp`는 이름 끝에 무작위 글자를 붙여 일지와 README가 가리키는 `confirm_<시각>` 꼴을 흐리므로, 그 이름을
    먼저 잡은 호출이 있을 때만 `-2`, `-3`을 붙인다. 스크래치 스크립트로 `RESULTS`를 임시 폴더로 바꿔 끼워, 옛 판이 같은 초의
    둘째 호출에서 `FileExistsError`를 내는 것을 재현하고, 새 판이 순차 세 번과 같은 초에 동시에 띄운 네 프로세스에서 모두
    다른 폴더를 만드는 것을 봤다. 고친 파일의 ruff·ruff format·pyright는 손으로 쳐 통과했다. 같은 약속을 적은 probes
    README의 `precommit_xdist/` 행에도 독스트링과 같은 괄호를 붙였다.

## 회고 (PR 반영 세션)

후보 셋, 승인 하나, 기각 둘, 넘김 0이다. 사람에게 넘긴 것이 없어 답을 기다리지 않았다.

1. **승인 → 대기열 327.** 사건: claude-review가 계정의 주간 한도로 빨간 PR에서 `tools/wait_ci.py`가 CodeRabbit 요청 직후
   그 빨강을 실패로 세고 끝나, CodeRabbit의 결과를 기다리는 자리가 비었다(위 "PR 봇 회차"). 한도는 이틀 넘게 가므로 그동안
   이 계정의 모든 PR에서 같은 일이 난다. 층: 도구의 고침이다. 리뷰 파이프라인 3이 이미 그 빨강을 리뷰 없음으로 읽으라고
   정했는데 도구가 그것을 따르지 못한다. 병합의 판정을 느슨하게 하는 것이 아니라 문서의 규칙을 대기 도구에 옮기는 것이라
   넘김에 들지 않는다. 되돌림: PR 하나. 이 PR의 범위(대기열 309) 밖이고 도구의 시험과 변이가 함께 가야 해서 이
   세션에서는 반영하지 않는다.
2. **기각.** 넘겨받은 인계 절이 "다음" 뒤에 있어, 그대로 커밋하면 최신 일지의 끝이 "다음"이 아니게 될 뻔했다. 앞 세션이
   PR 직전 단계를 닫으며 "다음"을 먼저 쓴 뒤 넘긴 경우이고, 받는 세션이 이어 쓰며 옮기면 된다(Edit 하나). 실수는 나지
   않았다.
3. **기각.** 셀프 리뷰와 PR 직전 리뷰가 지난 `confirm.py`의 같은 초 폴더 충돌을 CodeRabbit 첫 회차가 잡았다(위 "PR 봇
   회차"). 리뷰 파이프라인의 다음 층이 제 일을 했고, 프로브 하나의 이름 짓기라 같은 꼴의 반복이 보이지 않는다.

## 다음

대기열 309는 이 PR로 닫힌다. 남긴 것은 넷이다. 컨테이너의 CPU 한도와 `os.cpu_count()`는 ADR 0035와 러너 독스트링의
못 보는 것이고 PR 체크리스트에 보류로 적었다. 시간에 민감한 사례 가운데 `test_filesystem`의 재시도 사례와 대기열
306은 열린 채다. 인계 잠금은 대기열 326, `wait_ci`가 claude-review의 한도 빨강을 실패로 세는 것은 대기열 327이다.
