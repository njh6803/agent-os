# 2026-10-19 (08) pre-commit 검사 셋(대기열 31·287·312)

next-session 지시문으로 연 새 세션의 하네스 chore다. 대상 파일이 `.pre-commit-config.yaml`인 열린 대기열 행 가운데 ADR이
필요 없는 셋(31 헌법 판, 287 카나리아 명세 모양, 312 변이 표 원문)을 한 PR로 닫는다.

> 사용자: "다음 작업: 대기열 31·287·312(대상 파일이 `.pre-commit-config.yaml`인 열린 행 가운데 ADR이 필요 없는 셋)을 chore 한 PR로 반영한다 / 다음 단계: 구현 / 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 브랜치: chore/pre-commit-batch / 모델: Opus 5.5 / xhigh / 읽을 것: 대기열 31·287·312 행과 그 행이 드는 일지들의 회고 절 / 이어받을 상태: 없음 / 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다. 토큰 최적화 세션의 재개 안내가 왔는지 본다 / 이번 요청 범위: PR과 병합까지" (지시문 열 줄을 `/`로 이어 옮겼다)

## 시작

- **정리.** 주 체크아웃 세션에서 `tidy-checkouts`를 먼저 돌았다. 루트는 main이고 이미 `origin/main`(`655b19a8`)과 같아
  당길 것이 없었다. 지운 워크트리와 브랜치는 없었다.
- **워크트리.** 루트에서 브랜치를 따지 않고 `EnterWorktree(name=pre-commit-batch)`로 들어가 브랜치 이름을
  `chore/pre-commit-batch`로 바꿨다. 기점은 `655b19a8`이다.
- **토큰 최적화 세션의 재개 안내.** 이 세션에 온 안내는 없었다.

## ADR이 필요한가

- **31.** 행은 "게이트가 느는 것이라 `operations.md` 가드레일 문장과 ADR이 먼저다"라고 적었다. 그 전제는 CI에도 넣는 길(자리
  후보 (2))이다. 자리 후보 (1)을 골라 pre-commit에만 두면 `CLAUDE.md`가 세는 게이트(CI가 판정하는 것)가 늘지 않는다. 인용 대조,
  커밋 메시지 검사, 변이 표 원문 확인처럼 pre-commit에만 있는 검사의 선례가 셋이고, 셋 모두 ADR 없이 들어왔다. 그래서 ADR 없이
  했다. 가드레일 문장(`operations.md`의 "pre-commit에만 있고" 목록)과 헌법 판은 고쳤다.
- **287.** pre-commit 훅과 CI의 pytest 저장소 상태 시험이 함께 있는 꼴이라 게이트가 하나 는다. 마크다운 표·줄 구분 문자 검사가
  같은 꼴로 ADR 없이 헌법 patch(2.5.4)로 들어온 선례대로 했다. 게이트는 열셋에서 열넷이다.
- **312.** 이미 있는 pre-commit 훅의 판정을 넓히는 것이라 게이트 수도 결정도 바뀌지 않는다. 다만 대기열 73·92가 세운 "커밋에
  든 표만 본다, 옛 원문은 썩어도 된다"를 좁힌다. 아래처럼 "부모 판에서도 맞지 않던 옛 원문은 썩어도 된다"로 남겼다.

## 312: 커밋에 들 판에서 변이 표의 원문을 본다

`tools/mutate.py --staged`를 더하고 `check-mutations` 훅을 `--check`(넘어온 표 파일)에서 이것(`pass_filenames: false`,
`always_run: true`)으로 바꿨다.

- **보는 것.** 커밋에 들 판(색인)이다. 작업 트리를 읽으면 스테이지하지 않은 변경이 판정에 섞인다. pre-commit이 그 변경을
  치워 두고 돌지만, 부분 커밋(`git commit <경로>`)은 임시 색인을 `GIT_INDEX_FILE`로 넘기고 작업 트리는 그대로라 색인을
  읽어야 맞다. 이것은 실제 `git commit`이 띄우는 훅으로 시험했다.
- **커밋에 든 표**(이 커밋이 더하거나 고친 `*_mutations.toml`)는 원문 전부를 본다. 옛 `--check`와 같다(대기열 92).
- **커밋에 들지 않은 표**는 이 커밋이 고친 파일(지우거나 옮긴 것 포함, `--no-renames`)을 가리키는 변이만 보고, 부모 판에서
  맞던 원문이 색인에서 깨졌을 때만 알린다. 부모 판에서도 맞지 않던 원문은 이 커밋이 깬 것이 아니라 그대로 썩어도 된다(대기열
  73). 이것이 312가 처방한 "file =이 스테이지된 파일을 가리키는 표도 본다"를 좁힌 판이다. 처방 그대로면 코드를 고친 커밋마다 그
  파일을 가리키는 옛 표의 썩은 원문이 모두 걸린다. 2026-10-17-13이 적은 썩은 표 넷(편집 18건)이 그 예다.
- **합치는 커밋.** `MERGE_HEAD`가 있으면 표가 색인과 같은 부모 모두에서 맞던 원문만 본다. main을 합치는 커밋을 HEAD 하나와만
  견주면 main의 변경이 모두 이 커밋의 것으로 들어, main이 이미 깬 원문을 그 커밋의 탓으로 읽는다.
- **못 보는 것.** 색인의 블롭을 그대로 읽어 작업 트리의 줄 끝 변환(`eol=crlf`)을 거치지 않는다. 디스크의 `--check`는 지나는데
  색인 확인은 막는 갈래를 시험으로 고정했다.
- **추적하지 않는 파일.** 첫 판은 색인에 없는 파일을 모두 "색인에 없다"로 막았다. 프로브 README의 원문 확인 행을 고치려고 읽다가,
  `.scratch/design-refresh/probes/checker_mutations.toml`의 머리 주석이 그 표의 원문 확인을 생성물(`ds-bundle/`,
  `.design-sync/sb-reference/index.json`)이 있는 체크아웃에서 한다고 적은 것을 보았다. 생성물은 추적하지 않아 색인에 없으니, 첫
  판이면 그 표를 고친 커밋은 생성물이 있는 체크아웃에서도 늘 막혔다. 지금은 색인에도 어느 부모에도 없는 파일(어느 판도 추적하지
  않는 파일)은 옛 `--check`처럼 작업 트리에서 읽는다. 이 커밋이 그 파일을 깰 수 없기 때문이다. 이 커밋이 추적을 끊은 파일(어느
  부모 기준으로 `D`, `git rm --cached` 포함)은 작업 트리에 남아도 막는다. 두 갈래와 생성물이 없을 때의 막힘을 시험으로 고정했다.
- **시간.** 첫 판은 이 저장소에서 한 번에 약 7초였다. 표 82개의 변이마다 편집 경로를 `resolve`한 것이 거의 전부였고, 같은 글자는
  한 번만 풀게 한 뒤 약 2초가 됐다(프로세스 안에서 손으로 쟀다). git 호출 여섯 번이 약 1.1초이고 그대로 두었다(셀프 리뷰
  명세 축은 `cat-file`을 두 번 부르는 색인에서 일곱 번을 셌다). `uv run`을 거친 훅 한 번은 약 4초였다(손으로 봤다. 명세 축은
  다른 세션이 함께 돌 때 6.8~8.1초를 봤다). 커밋마다 수 분이 드는 러너에 견주면 작다고 보았다.
- **러너 밖에 둔다.** 설정 주석은 파일을 고치지 않는 `always_run` 검사를 러너가 함께 띄운다고 적었고, ADR 0005의 2026-10-07
  이력은 받은 파일만 보는 빠른 검사(변이 표 포함)를 따로 둔다고 적었다. `--staged`는 `always_run`이 되었지만 따로 두었다.
  러너의 `CHECKS` 여덟은 모두 CI도 도는 검사이고(`ci.yml`과 대 봤다. pytest만 러너가 프로세스를 나눠 돌고 CI는 한
  프로세스로 돈다, ADR 0035. 셀프 리뷰 두 축이 "같은 명령"이라 적은 첫 판을 짚었다), 이 확인은 색인을 보아 pre-commit에만 있다.
  그 경계를 설정 주석에 적었다("CI 도 도는 검사 가운데"). 값은 커밋마다 차례로 더 드는 수 초다. ADR 0005의 2026-10-07 이력의
  "받은 파일만 보는 빠른 검사(…, 변이 표, …)도 따로 둔다"는 따로 둔다는 결정이 그대로라 포인터를 달지 않았다(첫 판은 이 문장을
  "본문"이라 적었다). 변이 표 확인이 그때 받은
  파일만 봤다는 것은 그 결정 시점의 사실로 보았다(`.claude/rules/adr.md`의 달지 않는 것).
- **이 변경이 잡은 것.** 구현하는 동안 새 확인이 이 브랜치가 깬 원문 셋을 잡았다. `_parse`의 모르는 선택 문구를 바꿔
  `mutate_runners_mutations.toml`의 하나가, 저장소 밖 판정을 두 줄로 늘려 `mutate_timeout_select_mutations.toml`의 하나가 깨졌고,
  훅을 실제로 돌린 첫 회에는 `tools/canary.py`의 새 `_shape_only`가 `_preflight_only`와 같은 `return 2 if failed else 0`을 가져
  `canary_mutations.toml`의 "사전 확인이 실패에도 0"이 원문 두 번이 됐다. 셋 모두 원문을 넓히거나 새 문구로 고쳤다. 옛 판이면
  셋째는 표가 커밋에 들지 않아 지나갔다.
- 행이 함께 고치라고 한 `run_checks_mutations.toml`의 "게이트 목록에서 검사 러너를 뺀다"는 PR #290이 먼저 고쳤다(지금
  `--check`가 열둘 모두 맞다).

## 31: 헌법 판 검사

`tools/check_constitution_version.py`를 더하고 `check-constitution-version` 훅(`files: ^docs/constitution/[^/]+\.md$`,
`pass_filenames: false`)으로 걸었다.

- **판정.** 색인의 헌법 파일(`principles.md`·`tech.md`·`operations.md`) 가운데 이 가지가 고친 것(merge-base와도 `origin/main`과도
  다른 것)이 있으면, 색인의 헌법 README 판이 `origin/main`의 판과도 merge-base의 판과도 달라야 한다. `origin/main`과 같은 파일을
  빼는 것은 main을 합치는 커밋이 main의 변경을 이 가지의 것으로 세지 않게 하려는 것이고, 거르는 규칙은 `tools/sibling_overlap.py`의
  `_own_changes`와 같다(그 도구는 작업 트리와 추적하지 않는 파일을, 이 검사는 색인을 견준다. 첫 판은 "같은 판정"이라 적었다). main이 이 가지 몫으로 비워 둔 판(대기열 279)은 그 도구의 `reserved_version`으로 센다. 그
  도구에서 상수와 함수를 import해 판정을 둘로 나누지 않았다.
- **커밋 단위.** 판은 가지마다 한 번 올리면 되어, 앞 커밋에서 올렸으면 다른 헌법 파일만 고친 뒤 커밋도 지나간다. 반대로 고친
  커밋과 판을 올린 커밋을 나누면 가지 전체로는 맞아도 앞 커밋이 막힌다. 행이 자리 후보 (1)의 값으로 적은 그대로이고, 독스트링의
  못 보는 것에 적고 시험으로 고정했다. 판의 크기(patch·minor·major)와 이력 문단은 보지 않는 것도 같다.
- **판정하지 못하면**(git 저장소 밖, `origin/main`이 없다, merge-base가 없는 얕은 클론) 2로 막는다. 건너뛰려면
  `SKIP=check-constitution-version`이다.
- 이 브랜치가 `operations.md`를 고친 뒤 실제 커밋에서 이 훅이 판을 올리기 전의 색인을 막는지는 아래 검사 절에 적는다.

## 287: 카나리아 명세 모양

`tools/canary.py --shape <명세…>`를 더하고 `check-canary-specs` 훅(`files: ^\.scratch/(.+/)?probes/canary/[^/]+\.toml$`,
`require_serial: true`)으로 걸었다. 명세마다 TOML 파싱과 명세 검증(`read_spec`)만 하고 체크아웃과 claude는 보지 않는다. 하나가
깨져도 나머지를 마저 보고, 오류의 이어진 줄(pydantic이 칸 이름과 까닭을 두 줄로 찍는다)을 모두 들여 찍는다. 갈래의 체크아웃까지
보는 `--preflight`는 병합 뒤 주 체크아웃이 새 사본이 되면 막혀 걸지 않았다(행의 처방). CI에서는 `tests/tools/test_canary.py`의
저장소 상태 시험(`test_이_저장소의_카나리아_명세는_모두_모양을_지난다`)이 커밋된 명세 전부에 돈다.

## 문서

- `CLAUDE.md` 검증 명령 절: 게이트 열넷, pre-commit이 돌리는 일곱에 카나리아 명세 모양 검사.
- `docs/constitution/operations.md` 가드레일: pre-commit에만 있는 목록의 변이 표 원문 확인을 `--staged`(대기열 92·312)로, 헌법
  판 검사(대기열 31)를 더했다. 스테이지된 파일에 돌고 CI에서는 저장소 상태 시험으로 도는 목록에 카나리아 명세 모양 검사를
  더했다.
- `docs/constitution/README.md`: 3.0.43(patch). 3.0.42는 함께 돌던 형제 `chore/next-session-handoff-batch`(PR #293)가 먼저
  매겨 비워 두었다.
- `KICKOFF.md`: 변이 도구 항목의 pre-commit 설정을 `--staged`로, 헌법 판 검사 항목을 더했다. 카나리아 러너는 런북에 항목이 없어
  두었다.
- `tests/tools/test_mutate.py`의 옛 주석 둘("옛 프로브의 원문은 썩어도 된다")을 새 판정에 맞게 고쳤다.
- 대기열 31·287·312를 닫았다.
- 옛 표현의 잔존: "커밋에 든 표만 본다"와 "썩어도 된다"를 저장소 전체에서 grep했다. 살아 있는 문서에 남은 것은 설정 주석과 독스트링의
  새 문장(옛 판을 과거로 적은 것)뿐이고, 나머지는 일지와 닫힌 대기열 행(기록)이다. 이 판정은 틀렸다. 셀프 리뷰 두 축이 시험
  주석 셋, 변이 표 머리 주석 둘, 훅 독스트링 하나를 더 찾았다(셀프 리뷰 절의 반영). "pre-commit"과 "--check"를 함께 grep하지
  않고 옛 문장의 말만 찾은 탓이다.
- 프로브 README: 새 표 둘의 행을 더하고, 카나리아·runners·timeout_select 행에 이번 결과를, 원문 확인(`mutation_check_mutations.toml`)
  행에 pre-commit 훅이 이제 `--staged`를 띄운다는 것을 적었다.

## 변이

표를 하나씩 차례로 돌렸다. 변이가 `tools/mutate.py` 자신을 고치므로 표를 동시에 돌리지 않고, 도는 동안 `tools/`와 `tests/`를
고치지 않는다. 고르는 기점은 `origin/main`이다(이 브랜치가 더하거나 고친 변이). 이 브랜치가 고친 기존 시험은 독스트링과 주석뿐이라
(`git diff origin/main`의 지운 줄로 봤다) 고른 것만 돌렸다. 이 PC에 다른 세션이 여럿 돌아 pytest 기준선이 평소보다 길었다
(`test_mutate.py` 170~320초, `test_check_constitution_version.py` 77~202초).

- **헌법 판(`check_constitution_version_mutations.toml`, 열둘).** 새 시험은 없는 모듈의 import(수집 오류)로만 빨갰어서 행동의
  빨강을 여기서 봤다. 첫 회차에서 1~9는 저마다 겨눈 시험 하나만 빨갰다(실패한 시험 이름으로 봤다). 10은 겨눈 시험이 아니라 다른
  시험(`test_앞_커밋에서_…`)의 error로 빨갰고, 11·12는 종료 코드 3221225794(0xC0000142, 프로세스를 띄우지 못했다)로 출력 없이 끝나
  셋 다 측정이 아니다. 셋에 겨눈 시험의 `FAILED` 줄을 표지(`expect_output`)로 달아 그 셋만 다시 돌렸고, 셋 모두 표지까지 맞는
  빨강이었다.
- **카나리아(`canary_mutations.toml`).** 원문을 넓힌 "사전 확인이 실패에도 0"과 새 여섯(139~144)을 `--since origin/main`으로 골라
  일곱 모두 기대대로 빨강.
- **runners(`mutate_runners_mutations.toml`).** 원문을 고친 27(모르는 선택을 변이 이름으로 넘긴다)을 `--since origin/main`으로 골라
  기대대로 빨강. 그 뒤 `tools/mutate.py`에서 고친 자리는 `_reader`·`_changes`·`staged`라 27이 고치는 `_parse`와 겹치지 않아 다시
  돌리지 않았다.
- **TaskStop 뒤에 남은 묶음.** 헌법 표 첫 회차의 10~12를 보고 차례로 돌던 묶음을 `TaskStop`으로 멈췄다. 곧바로 남은 프로세스를
  찾았지만 거르는 조건이 `python.exe`이면서 명령줄에 워크트리 경로나 `check_constitution`이 든 것이라, `uv run`이 띄운 python(명령줄의
  경로가 상대 경로다)도 묶음을 돌리던 `bash.exe`도 걸리지 않았다. 묶음은 카나리아·색인 확인·runners 표를 이어 돌았고, 그 약 17분
  동안 나는 `tools/mutate.py`와 `tests/tools/test_mutate.py`를 고쳤다. runners 27이 `tools/mutate.py`에 변이를 넣은 동안 친 `ruff
  check`는 변이가 든 판을 읽어 `flags`가 쓰이지 않는다고 했다(ruff format은 바꾼 것이 없었다). 둘째 찾기에서 `bash.exe`·`uv.exe`까지
  넓혀 묶음 스크립트를 찾았고, 명령줄을 확인한 뒤 `taskkill /T /F`로 끝냈다. 되돌림이 내 고침을 덮지 않았는지 `git diff -- tools/`로
  봤고 의도한 고침뿐이었다. 카나리아 회차는 `tools/canary.py`만 고치는 표라 그대로 셌고, 고치는 도중의 판으로 돈 색인 확인 표의
  회차(종료 2)는 버렸다. `tools/mutate.py` 독스트링이 이미 적은 "멈춘 뒤 명령줄로 남은 프로세스를 찾아 `taskkill /T`로 끝낸다"를
  찾기의 조건이 틀린 채 따른 것이다(회고 1).
- **리뷰 전에 띄운 묶음을 멈췄다.** 헌법 10~12를 다시 돌린 묶음이 색인 확인 표(열넷)로 이어졌는데, 기준선이 320초, 변이 1이
  392초(기대대로 빨강)였다. 다른 세션(`mutate-ctrl-c-under-load`)이 pytest를 스물네 프로세스로 돌던 때다. 남은 열셋에 한 시간이 넘게
  드는데, `tools/mutate.py` 독스트링은 표 전체를 셀프 리뷰와 PR 직전 리뷰를 반영해 커밋한 뒤에 한 번 돌리게 한다(리뷰가 시험을
  고치면 그 전의 실행은 옛 시험을 잰 것이다, 대기열 265). 그래서 멈추고 리뷰 뒤로 미뤘다. 이번에는 끄기 전에 `tools/mutate.py`를
  스크래치에 떠 두고, 프로세스를 `bash.exe`·`uv.exe`까지 넓혀 찾아 명령줄(`run_mutations2.sh`)을 확인한 뒤 그 나무를 `taskkill /T
  /F`로 껐다. pytest가 먼저 꺼진 틈에 mutate.py가 변이 2를 "빨강"으로 찍고(측정이 아니다) 변이 3을 넣은 채 다음 pytest를 띄웠다.
  고아가 된 그 pytest도 명령줄을 확인하고 껐고, 원문이 0번인 변이를 찾는 스크래치 스크립트로 남은 변이 3을 찾아 손으로 되돌렸다.
  끄기 전 사본과의 차이가 그때 든 변이 2의 한 줄뿐이고 `--check`가 여섯 표 모두 맞아, 변이가 남지 않은 것을 봤다.

## 인계(셀프 리뷰 직전)

셀프 리뷰를 부르자 세션 컨텍스트가 인계 문턱을 넘은 채 `셀프 리뷰 직전`에 왔다는 계기가 왔다. 인계하지 않는 때 넷에 들지 않아
next-session의 인계 줄대로 새 세션에 넘긴다. 이 세션의 제목은 `chore/pre-commit-batch`이고 넘기기 전에
`chore/pre-commit-batch (인계함)`으로 바꾼다.

- **번복하거나 고친 것.** `--staged`의 첫 판이 추적하지 않는 생성물을 막던 것을 고쳤다(312 절의 추적하지 않는 파일). 헌법 표 10~12에
  표지를 달아 다시 돌렸다. 리뷰 전에 띄운 색인 확인 표의 실행을 멈췄다(둘 다 변이 절).
- **남은 단계(차례대로).**
  1. 셀프 리뷰(`/code-review`). 기점은 `655b19a8`, 명세는 그 판의 대기열 31·287·312 행이다. 아래 밀 주장을 두 축 브리프에 나열한다.
  2. 반영한 뒤 커밋한다. 스테이지하지 않은 고침이 여럿이고, 이 일지와 새 변이 표 둘(`check_constitution_version_mutations.toml`,
     `mutate_staged_mutations.toml`)은 추적하지 않는 파일이다.
  3. `origin/main`을 합친다. 그사이 #293·#294가 병합되었다. `docs/constitution/README.md`의 판 줄이 겹친다. main이 3.0.42를
     매겼으니 이 브랜치는 3.0.43을 두고, 이력 문단의 "3.0.42는 함께 돌던 형제 브랜치(…)가 먼저 매겨 비워 두었다" 문장을 main의
     3.0.42 문단으로 바꾼다. #294가 "변경을 마치고 전체를 볼 때는 손 pytest 대신 `tools/run_checks.py`를 친다"를 세웠다(`CLAUDE.md`
     검증 명령, ADR 0035 이력 2026-10-19). main이 더한 카나리아 명세 둘을 `--shape`의 저장소 상태 시험이 읽는다.
  4. 헌법 판 훅이 판을 올리기 전의 색인을 실제 커밋에서 막는지 본다(31 절의 마지막 줄이 검사 절에 적겠다고 했다).
  5. PR 직전 리뷰 둘(`/security-review`, `bug-perf-review`)과 반영.
  6. 반영해 커밋한 뒤 변이 표를 돌린다. 헌법 표 전체(열둘)와 색인 확인 표 전체(열넷, 이 세션에서는 1만 측정됐다)는 새 표라
     전체이고, 카나리아·runners·timeout_select 표는 `--since origin/main`이다(timeout_select의 19는 아직 한 번도 돌지 않았다). 리뷰가
     시험을 고치면 그 표는 전체다. 표를 동시에 돌리지 않고, 도는 동안 `tools/`·`tests/`를 고치지 않는다. 이 PC는 다른 세션의 부하로
     `test_mutate.py` 변이 하나가 6분 남짓 걸렸다. 결과는 위 변이 절과 프로브 README에 적는다. 새 표 둘의 README 행은 아직 없다.
  7. 일지의 셀프 리뷰·검사·회고·다음 절. 회고 후보는 위 변이 절의 `TaskStop` 뒤에 남은 묶음이다(`tools/mutate.py` 독스트링이 2회차
     뒤에 처방을 적었고 이번이 3회차다. 남은 프로세스를 찾는 조건이 틀렸다).
  8. `/git-pr`, 봇 회차, 워크트리에서 병합하는 길, next-session.
- **셀프 리뷰에 밀 주장(나열 밖도 잰다).**
  - `tools/mutate.py` 모듈 독스트링 `--staged` 문단: 추적하지 않는 생성물을 작업 트리에서 읽는다, 추적을 끊은 파일은 알린다,
    합치는 중이면 표가 색인과 같은 부모 모두에서 맞던 원문만 본다, `git commit <경로>`의 임시 색인을 본다, 못 보는 것(`eol=crlf`).
  - `.pre-commit-config.yaml` 주석: "CI 도 도는 검사 가운데 파일을 고치지 않는 always_run 검사를 러너가 함께 띄운다",
    check-mutations 주석의 "커밋마다 약 4초가 차례로 더 든다".
  - `CLAUDE.md` 검증 명령 절의 게이트 열넷과 pre-commit이 돌리는 일곱, `docs/constitution/operations.md` 가드레일의 두 목록,
    `docs/constitution/README.md` 3.0.43 이력 문단.
  - `KICKOFF.md`의 헌법 판 검사 항목의 근거("PR 열하나가 판을 올리지 않았다").
  - `tools/check_constitution_version.py` 독스트링의 판정과 못 보는 것, `tools/sibling_overlap.py`의 `_own_changes`와 같은 판정이라는
    주장, `tools/canary.py --shape`의 독스트링과 사용법.
  - 이 일지의 "pre-commit에만 있는 검사의 선례가 셋이고 셋 모두 ADR 없이 들어왔다", "2.5.4 선례", "러너의 `CHECKS` 여덟은 모두 CI도
    같은 명령으로 도는 검사"(`ci.yml`과 대 봤다), 시간(약 7초 → 약 2초, git 호출 여섯 번 약 1.1초, 훅 한 번 약 4초), 프로브 README의
    새 수(카나리아 백마흔넷, 모양 확인 여섯).
- **지시문.**

  ```
  다음 작업: 대기열 31·287·312(대상 파일이 `.pre-commit-config.yaml`인 열린 행 가운데 ADR이 필요 없는 셋)을 chore 한 PR로 반영한다
  다음 단계: 구현
  어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
  시작 프롬프트: 대기열 31·287·312(대상 파일이 `.pre-commit-config.yaml`인 열린 행 가운데 ADR이 필요 없는 셋)을 chore 한 PR로 반영한다
  브랜치: chore/pre-commit-batch
  모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
  읽을 것: docs/journal/2026-10-19-08-pre-commit-batch.md(그 워크트리의 추적하지 않는 파일. 끝의 "인계" 절이 남은 단계와 셀프 리뷰에 밀 주장이다)
  이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리(C:/project/agent/.claude/worktrees/pre-commit-batch)에 있고 셀프 리뷰(/code-review, 기점 655b19a8)부터 한다. 일지 파일은 docs/journal/2026-10-19-08-pre-commit-batch.md이다
  확인할 선행 조건: 없음
  이번 요청 범위: PR과 병합까지
  ```

open-session을 부른다 2026-10-19T00:00:19Z

## 새 세션(인계받음)

> 사용자: "대기열 31·287·312(대상 파일이 `.pre-commit-config.yaml`인 열린 행 가운데 ADR이 필요 없는 셋)을 chore 한 PR로 반영한다" (위 지시문 그대로)

- **들어가기.** 제목을 `chore/pre-commit-batch`로 바꿨다. `EnterWorktree(path)`가 `belongs to another running Claude Code
  session (locked: claude session pre-commit-batch (pid 18656))`으로 거부했다. pid 18656은 살아 있었고, `list_sessions`에서 넘긴
  세션의 제목은 `chore/pre-commit-batch (인계함)`이었다. 넘긴 세션이 시작할 때 주 체크아웃은 `655b19a8`이었고, 그 판의
  next-session에는 잠금 풀기 단계가 없다(`git show 655b19a8:.claude/skills/next-session/SKILL.md`에 0건). 그 단계는 #293이
  더했다. 그래서 main의 next-session 잠금 풀기 단락대로 `git worktree unlock C:/project/agent/.claude/worktrees/pre-commit-batch`로
  풀고 들어갔다. 단계를 더한 뒤의 실패가 아니라 단계가 없던 판의 회차다.

## 셀프 리뷰

기점 `655b19a8`, 커밋 0, 바뀐 파일 16, 미추적 3(새 변이 표 둘과 이 일지). 명세는 그 판의 대기열 31·287·312 행이고, 이
세션이 내린 판단(31의 자리와 ADR, 312를 좁힌 판정)은 브리프의 참고 절에 따로 적었다.

### 표준 축(sonnet·high)

Critical·Major 0. 받은 지적과 판정:

- **Minor(하드).** `tools/check_constitution_version.py`의 얕은 클론 안내 `git fetch --deepen`은 값이 없어 그대로 치면
  `option 'deepen' requires a value`로 실패한다(임시 얕은 클론에서 재현). merge-base 없음 갈래에 시험이 없다.
- **Minor(하드).** 같은 도구의 못 보는 것에 두 갈래가 없다. 헌법 파일을 지우기만 한 커밋은 pre-commit이 지운 파일을
  `files`에서 빼(`--diff-filter=ACMRTUXB`) 훅이 돌지 않는다. 로컬 `origin/main`이 낡은 경우.
- **Minor.** 잔존: 옛 `--check` 배선이 `.scratch/harness/probes/mutation_check_mutations.toml:1`과
  `.scratch/design-refresh/probes/checker_mutations.toml:7`에 남았다.
- **Minor.** 프로브 README가 새 표 둘의 행을 가리키는데 행이 없다(남은 단계 6에서 채울 예정).
- **Minor.** 새 표의 `expect_output`이 헌법 표 열둘 가운데 셋, `mutate_staged` 표 열넷 가운데 0이다(`probes.md` 표지 규칙).
- **Minor.** `tests/tools/test_canary.py`의 `사전_코드 == 2`가 까닭 없이 코드만 본다(`CODING_STANDARDS.md` 실패 까닭 단언).
- **Minor.** `KICKOFF.md`의 헌법 판 검사 항목에 시험 파일과 `sibling_overlap` 의존이 없다.
- **주장 검증.** 맞음: 표 82, 카나리아 변이 144, 새 표 12·14, 게이트 열넷(5+7+2), `CHECKS` 여덟, 열하나(#19~#50), 2.5.4 선례,
  `--staged` 약 3.6초. 틀림: 일지의 "`CHECKS` 여덟은 모두 CI도 같은 명령"은 pytest에서 틀린다(러너는 `-n N`, CI는
  `pytest -q`, ADR 0035). 일지가 ADR 0005의 그 문장을 "본문"이라 했는데 2026-10-07 이력이다. README 3.0.43의 3.0.42 문장은
  합칠 때 고친다(남은 단계 3). `--amend`는 `mutate.py` 독스트링에 갈래가 없다(HEAD가 `--no-verify`로 넣은 깨진 표는
  amend에서 지나간다).
- **판단 항목.** `staged()`가 git 배관·TOML 읽기·보고를 섞는다. `_reader`의 `deleted=None` 동작 인자와 `_INDEX=""`
  센티널. `_shape_only`가 `_preflight_only`의 루프를 되풀이한다. `Judged.bumped`가 고친 파일이 없을 때도 참이다(이름).
  "`_own_changes`와 같은 판정"은 거르는 규칙만 같다(이 도구는 색인, 그 도구는 작업 트리와 미추적 파일).

### 명세 축(본 세션 모델)

임시 저장소에서 실제 pre-commit으로 커밋해 보며 쟀다. Critical·Major 0. 받은 지적:

- **Minor.** 헌법 파일을 지우기만 한 커밋은 훅이 `(no files to check)Skipped`로 지나간다(31). 같은 색인에 도구를 직접 부르면
  1로 막는다. pre-commit이 지운 파일을 넘기지 않는 것은 `tests/tools/test_mutate.py`에 이미 적힌 사실이다. 옮긴 파일은 막혔다.
- **Minor.** `KICKOFF.md`대로 새 프로젝트를 만들면 원격이 생기기 전의 첫 커밋(8단계)이 헌법 판 훅에 2로 막힌다("origin/main 이
  없다"). 런북의 그 항목에도 8단계에도 그 사실과 `SKIP` 안내가 없다.
- **Minor.** 잔존: "pre-commit이 표를 `--check`로 넘긴다"는 옛 문장이 `tests/tools/test_mutate.py` 2043·2071·2146줄과
  `.scratch/harness/probes/mutation_check_mutations.toml` 1줄에 남았다. `tools/hook_session_web_deps.py:6`의 "(셋 다 CI 에
  없다)"는 이제 넷이다. 그래서 이 일지의 "살아 있는 문서에 남은 것은 … 뿐"도 틀린다.
- **Nit.** 분리 HEAD에서 비워 둔 판을 쓴 커밋이 막힌다(가지 위 0, 분리 HEAD 1). `git rebase --continue`는 훅을 돌리지 않아
  분리 HEAD에서 손으로 `git commit`을 칠 때만 난다. 못 보는 것에 없다.
- **Nit.** 일지의 수: git 호출은 이 색인에서 일곱 번(`cat-file` 두 번), "`CHECKS` 여덟은 CI도 같은 명령"은 pytest만 다르다,
  "훅 한 번 약 4초"는 부하가 있을 때 6.8~8.1초였다(프로세스 안의 2.2~2.5초는 "약 2초"와 맞다).
- **Nit.** git 저장소 밖에서 헌법 판 도구를 돌리면 문구가 "origin/main 이 없다"로 나온다(종료 2는 맞다).
- **맞은 것.** 31: 판을 안 올린 커밋, 같은 색인에서 올린 커밋, 앞 커밋에서 올린 뒤의 커밋, main을 합치는 커밋, README만 바꾼
  커밋, 옮긴 커밋, 부분 커밋, `--amend`, `origin/main` 없음, 얕은 클론. 287: 깨진 TOML·칸 누락·`kind`가 주석에 붙은 명세는
  막고 정상은 지난다, 정규식 깊이 0·1·3을 잡고 `canary/sub/`는 거른다, 부분 커밋 두 방향. 312: 코드만 고쳐 깬 커밋은 막고 이미
  썩은 원문은 지난다, 임시 색인 두 방향, 합치기 두 방향, 옮긴 파일과 `rm --cached`, 생성물 있음·없음, `--amend`, 첫 커밋. 수와
  인용(카나리아 144, 모양 확인 여섯, 열하나, 2.5.4, 2026-10-17-13의 18건)이 맞다. 범위 넘침 없음.

### 반영

- **고친 것.**
  - `tools/check_constitution_version.py`: 얕은 클론 안내를 `git fetch --unshallow origin`으로 바꾸고, 저장소 밖이면 그렇게
    알린다(`rev-parse --git-dir`를 먼저 본다). 못 보는 것에 셋을 더했다(헌법 파일을 지우기만 한 커밋은 pre-commit이 훅을
    띄우지 않는다, 로컬 `origin/main`이 낡으면 받지 않은 main의 판을 모른다, 분리 HEAD에서는 비워 둔 판을 찾지 못해 막는다).
    지우기만 한 커밋을 잡으려고 `always_run`으로 두는 길은 도구 한 번이 이 PC에서 4.5~5.5초(PowerShell `Measure-Command` 세
    번, 다른 세션이 함께 돌 때)라 두지 않았다. `Judged.bumped`를 `passes`로 바꿨다. "`_own_changes`와 같은 판정"을 "거르는
    규칙이 같다"로 좁혔다.
  - `tests/tools/test_check_constitution_version.py`: 저장소 밖, 얕은 클론(안내한 명령을 그대로 쳐서 판정이 1로 풀리는 것까지),
    지우기만 한 커밋(이 저장소의 훅 항목을 떼어 실제 `pre-commit run`으로 `(no files to check)Skipped`, 고친 커밋에서는 같은 훅이
    돈다), 받지 않은 main, 분리 HEAD. 새 열둘과 매개변수 표가 모두 통과했다(191초, 이 PC의 부하).
  - `tools/mutate.py` 못 보는 것에 `--amend`(HEAD를 부모로 읽어, HEAD가 훅을 건너뛰고 넣은 깨진 원문을 지나간다)와 그 시험.
  - `tests/tools/test_canary.py`: 모양 확인의 대조로 부른 사전 확인에 실패 까닭(`새: 체크아웃 … 이 없다`)을 단언했다.
  - 잔존: `tests/tools/test_mutate.py`의 주석·독스트링 셋, `mutation_check_mutations.toml`의 머리 주석, 프로브 README의 원문
    확인 행, `tools/hook_session_web_deps.py`의 "셋 다 CI 에 없다"(넷이 되었다). `checker_mutations.toml`의 머리 주석도
    고쳤다가 되돌렸다(아래 검사 절).
  - `KICKOFF.md`: 헌법 판 검사 항목에 시험 파일, 형제 번호 대조에 기대는 import, `origin/main`이 없을 때의 2를 적고, 8단계
    첫 커밋 명령에 `SKIP=check-constitution-version`을 붙였다.
  - 새 변이 표 둘의 변이마다 겨눈 시험의 `FAILED` 줄을 표지로 달았다(헌법 열둘 가운데 남은 아홉, 색인 확인 열넷). 표지는 코드와
    시험을 읽고 고른 것이고, 변이 실행이 표지까지 맞는지 잰다. 헌법 표에 새 코드를 겨누는 변이 둘(저장소 밖을 따로 알리지
    않는다, 값 없는 `--deepen`을 안내한다)을 더해 열넷이다.
  - `.pre-commit-config.yaml` 주석: 시간은 "수 초(손으로 본 값이 약 4초, 다른 세션이 함께 돌 때 7~8초)", 헌법 판 훅에 지우기만
    한 커밋을 적었다.
  - 이 일지의 틀린 주장 넷(같은 명령, ADR 0005 "본문", `_own_changes`와 같은 판정, 잔존 판정)을 고쳤다.
- **남긴 것과 이유.** `staged()`의 길이와 `_reader`의 `deleted` 동작 인자, `_INDEX` 센티널: 판단 항목이고, 쪼개면 방금 표지를
  단 `mutate_staged` 표의 원문 열넷이 함께 움직인다. `_shape_only`와 `_preflight_only`의 비슷한 돌기: 출력 모양이 다르고(모양
  확인은 여러 줄 오류를 줄마다 찍는다) 판단 항목이다. git 저장소 밖 문구(명세 축 Nit)는 고쳤다. 프로브 README의 새 표 두 행은
  변이를 돌린 뒤 채운다(남은 단계 6).
- **PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장).**
  - `tools/check_constitution_version.py` 못 보는 것의 새 세 문장과 "모든 커밋에 띄우면 커밋마다 수 초가 더 들어 두지 않았다",
    "`git rebase --continue` 가 커밋을 옮길 때는 pre-commit 이 돌지 않아".
  - `tools/mutate.py`의 `--amend` 문장.
  - `KICKOFF.md` 8단계의 "아직 원격이 없어 헌법 판 검사(7단계)가 `origin/main`이 없다고 막으므로".
  - `tools/hook_session_web_deps.py`의 "넷 다 CI 에 없다".
  - `.pre-commit-config.yaml`의 "다른 세션이 함께 돌 때 7~8초"와 "같은 판정을 tools/sibling_overlap.py 가 작업 트리로 알린다".
- **헌법 판 훅의 실제 커밋(31 절이 적겠다고 한 것).** 변경을 모두 스테이지한 뒤 헌법 README만 스테이지에서 빼고, 다른 훅을
  `SKIP`으로 뺀 `git commit -F`를 쳤다. `constitution version … Failed`, 종료 1, `!! 헌법 파일을 고쳤는데 판을 올리지 않았다:
  docs/constitution/operations.md`, `판 3.0.41 — origin/main 의 판 3.0.42, merge-base 의 판 3.0.41`이 찍히고 커밋이 되지 않았다.
- **첫 커밋 시도(모든 훅).** 러너의 검사 여덟은 모두 통과했다(lint-imports 8.8초, check-instructions 9.8초, zizmor 10.4초,
  check-type-escapes 21.5초, pyright 48.3초, run-hooks 349.2초, pytest 509.3초, web-verify 570.6초). ruff 둘, 마크다운 표, 줄
  구분 문자, 헌법 판, 인용 대조도 통과했다. 변이 표 원문 확인(`--staged`)이 2로 막았다. 반영으로 머리 주석을 고친
  `.scratch/design-refresh/probes/checker_mutations.toml`이 커밋에 든 표가 되어 원문을 모두 보는데, 그 표가 가리키는 생성물
  (`.design-sync/sb-reference/index.json`, `ds-bundle/…`)이 이 워크트리에 없어 넷을 읽지 못했다. 독스트링이 적은 그대로의
  동작이다(생성물이 있는 체크아웃에서 커밋한다). 그 주석의 "원문 확인(`--check`, pre-commit 의 check-mutations)"은 괄호를 두
  항목으로 읽으면 지금도 참이라, 생성물을 짓지 않고 고침을 되돌렸다. 되돌린 뒤 `uv run python tools/mutate.py --staged`는 0(커밋에
  든 표 6, 고친 파일을 가리키는 다른 표의 변이 74, 문제 0)이었다. 다시 친 커밋은 바로 앞 시도에서 통과한 러너를
  `SKIP=parallel-checks`로 뺐다. 두 시도의 색인 차이는 그 표의 주석 되돌림과 이 일지뿐이고, 러너는 main을 합치는 커밋에서 다시
  돈다.
- **다시 돌린 명령.** 새 시험만 골라 돌렸다(헌법 판 열둘 191초, 카나리아 하나, `--amend` 하나 모두 통과). 원문 확인
  `--check`가 두 표 모두 맞다. 나머지 검증 명령은 커밋의 pre-commit으로 갈음한다(결과는 아래 검사 절).
- **커밋 `000c8512`의 pre-commit.** 러너(`parallel-checks`)는 `SKIP`으로 `Skipped`였다(까닭은 위 첫 커밋 시도). ruff 둘, 마크다운
  표, 줄 구분 문자, 변이 표 원문(`--staged`), 헌법 판, 커밋 메시지가 `Passed`였다. 카나리아 명세 모양은 커밋에 든 명세가 없어
  `(no files to check)Skipped`였다. 인용 대조는 두 묶음으로 경고 1건과 12건(막지 않는다)이다. 프로브 README 74줄 하나, 이
  일지의 열(38·138·163·184·235·251·256·287·295·296줄), 헌법 README 11줄의 둘이다. 검사 절을 쓸 때 원문과 하나씩 대 본다. 커밋
  요약의 `rewrite docs/constitution/README.md (96%)`는 긴 판 줄 하나를 바꾼 것이다(`git diff --stat 655b19a8 HEAD`가 한 줄 더하고
  한 줄 지움, 줄 끝을 빼도 같다).

## 인계(커밋 뒤)

커밋 `000c8512`가 된 직후 세션 컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤`에 왔다는 계기가 왔다. 인계하지 않는 때 다섯에 들지
않는다. 커밋은 성공했고, 요청 범위는 PR과 병합까지이고, 넘겨받은 경계는 `셀프 리뷰 직전`으로 다르고, 이 세션이 쓴 `인계 못함`
줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 그래서 main의 next-session(잠금 풀기 단계가 든 판)의 인계 줄대로
새 세션에 넘긴다. 이 세션의 제목은 `chore/pre-commit-batch`이고 넘기기 전에 `chore/pre-commit-batch (인계함)`으로 바꾼다. 실행 중
세션 확인에서 대기열 31·287·312나 대상 파일 `.pre-commit-config.yaml`을 쥔 다른 세션은 없었다(열린 PR #296의 227은 `tools/`의
계기 훅이다).

- **번복하거나 고친 것.** 반영 절의 `checker_mutations.toml` 머리 주석 고침을 되돌렸다. 그 밖에 커밋 뒤에 바꾼 것은 이 절과 위
  pre-commit 줄뿐이고 커밋하지 않았다.
- **남은 단계(차례대로).**
  1. `origin/main`을 합친다. 인계(셀프 리뷰 직전) 절의 남은 단계 3이 적은 그대로다(`docs/constitution/README.md` 판 줄은
     3.0.43을 두고 3.0.42 문장을 main의 3.0.42 문단으로 바꾼다, `CLAUDE.md`·`operations.md`·`retro-queue.md`의 겹침). 그 사이
     #295도 병합되었다. `000c8512`가 러너를 `SKIP`으로 뺐으므로 합치는 커밋에서는 러너를 빼지 않는다.
  2. PR 직전 리뷰 둘(`/security-review`, `bug-perf-review`)과 반영. 브리프에는 반영 절의 "PR 직전 리뷰에 밀 주장"을 나열한다.
  3. 반영해 커밋한 뒤 변이 표를 돌린다. 헌법 표 전체(열넷)와 색인 확인 표 전체(열넷), 카나리아·runners·timeout_select 표는
     `--since origin/main`이다. 차례와 제약은 인계(셀프 리뷰 직전) 절의 남은 단계 6이다. 결과는 변이 절과 프로브 README에
     적고 새 표 두 행을 더한다.
  4. 일지의 검사·회고·다음 절. 검사 절에는 첫 커밋 시도와 위 pre-commit 줄, 인용 대조 경고를 옮긴다. 회고 후보는 인계(셀프
     리뷰 직전) 절의 남은 단계 7이다.
  5. `/git-pr`, 봇 회차, 워크트리에서 병합하는 길, next-session.
- **지시문.**

  ```
  다음 작업: 대기열 31·287·312(대상 파일이 `.pre-commit-config.yaml`인 열린 행 가운데 ADR이 필요 없는 셋)을 chore 한 PR로 반영한다
  다음 단계: 구현
  어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
  시작 프롬프트: 대기열 31·287·312(대상 파일이 `.pre-commit-config.yaml`인 열린 행 가운데 ADR이 필요 없는 셋)을 chore 한 PR로 반영한다
  브랜치: chore/pre-commit-batch
  모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
  읽을 것: docs/journal/2026-10-19-08-pre-commit-batch.md(끝의 "인계(커밋 뒤)" 절이 남은 단계다. 그 절은 워크트리에서 커밋하지 않은 고침이다)
  이어받을 상태: 인계: 커밋 뒤. 커밋 000c8512까지 셀프 리뷰 반영과 커밋을 마쳤고(러너는 SKIP으로 뺐다), 푸시하지 않았고 PR도 없다. origin/main 합치기부터 하고 남은 단계는 일지의 "인계(커밋 뒤)" 절이다. 일지 파일은 docs/journal/2026-10-19-08-pre-commit-batch.md이다
  확인할 선행 조건: 없음
  이번 요청 범위: PR과 병합까지
  ```

- **넘기기 전에.** 제목을 `chore/pre-commit-batch (인계함)`으로 바꿨다(앱이 묻지 않았다). 이 세션이 띄운 백그라운드 작업은
  없었다. `git worktree unlock C:/project/agent/.claude/worktrees/pre-commit-batch`는 `is not locked`로 끝났다. 이 세션이 들어갈 때
  잠금을 손으로 풀었고, 그 뒤의 `EnterWorktree(path)`는 다시 잠그지 않은 것으로 보인다(잠금 사유를 따로 보지 않았다).

open-session을 부른다 2026-10-19T02:48:11Z

인계 못함 커밋 뒤

- **열기가 막혔다.** `tools/open_session.ps1 -Action send`가 `idle=208s`, `fired=11:50:25.635`, `page=11:50:28.316`까지 내고 `6초
  안에 지시문('대기열 31·287·312(대상 파일이 …')이 든 입력창 을(를) 찾지 못했다`로 1에 끝났다. `sent=`가 없어 보내지 않았다.
  직후 `list_sessions`에 `chore/pre-commit-batch` 제목의 새 세션은 없었고, 같은 분에 `feature/09-human-verification-close`라는
  새 세션이 생겨 돌고 있었다(그 브랜치의 `(인계함)` 세션이 같은 때에 인계했다). 두 세션의 딥링크가 같은 새 세션 화면에 겹쳐
  이 지시문이 그 화면에 실리지 않았다고 보지만, 앱 로그(`deeplink_timeline.ps1`)로 가르지 않았다. 같은 파일로 다시 돌리지
  않는다(open-session 막히면). 제목을 `chore/pre-commit-batch`로 되돌렸고, 이 세션에서 위 남은 단계 1부터 잇는다.
