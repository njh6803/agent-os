# 2026-10-23 (31) 병합 기록에서 다시 풀 과제의 후보를 찾아 표로 내고 층과 씨앗으로 고른다 (model-rerun 05)

## 사용자 프롬프트

티켓 02의 세션(일지 2026-10-23-18)이 PR #363을 병합한 뒤 `next-session`의 지시문으로 이 세션을 열었다. 첫 메시지는 아래다. 이 세션에 사용자의 다른 메시지는 없었다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/model-rerun/issues/05-task-selection.md
>
> 다음 작업: .scratch/model-rerun/issues/05-task-selection.md. 병합 기록에서 후보 티켓을 찾아 까닭과 함께 표로 내고, 층과 씨앗으로 파일럿 셋과 본 측정 여덟을 고른다
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/model-rerun/issues/05-task-selection.md
> 브랜치: feature/05-task-selection
> 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-18-hidden-test-filter.md의 "다음", .scratch/plan.md
> 이어받을 상태: 티켓 05 메모에 02가 넘긴 판단 항목이 있다. 그 밖에 PR #363의 claude-review 셋째 회차(30c33ed2)가 Minor로 짚고 PR 코멘트에만 적은 둘이 있다: tools/rerun_hidden.py 의 _cut_links 가 끊기(명령)와 남은 링크 돌려주기(질의)를 함께 한다(CQS, tools/canary.py 와 같은 모양), _checkout 의 finally 안에 분기가 쌓였고 _sort 가 커밋 해석부터 판정 조립까지 한 함수에서 한다(_run_merge·_run_base 로 나누기). 05가 rerun_hidden.py 를 다시 열 때 메모의 항목과 함께 본다. 형제 03(PR #364)·04는 아직 병합 전이다
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지. 사용자는 측정 도구 짓기까지 이어 가라고 했다(2026-10-22)

## 체크아웃 정리

주 체크아웃에서 `tidy-checkouts`를 먼저 돌았다. 루트는 main이고 깨끗했다. `empty-trash`는 종료 1이었다(휴지통의 항목을 python.exe pid 41176이 쥐었다). 보고만 하고 기다리지 않았다. 그 뒤 `EnterWorktree`(이름 `05-task-selection`)로 들어가 `feature/05-task-selection`을 땄고, 세션 제목을 브랜치 이름으로 바꿨다. 티켓 `Status:`를 `in-progress`로 바꿨다(아직 커밋하지 않았다).

## 구현

`tools/rerun_select.py`를 새로 썼다(값만 받는 층과 git을 부르는 바깥 층, 명령 줄 `table`·`pilot`·`main`). 정한 것.

- 바깥 검증 낱말은 B의 티켓 글에서 대소문자를 가리지 않고 찾는다. 독스트링과 후보 표 머리에 적었다.
- 날짜 바닥은 B의 커밋 시각 기준 KST 2026-10-12 0시다(`DATE_FLOOR`).
- 되살릴 목록에 날짜만으로 빠진 후보가 들어도 오류로 보지 않는다. 낱말에 걸리지 않았거나, 날짜 밖의 싼 조건으로도 빠졌거나, id가 후보 하나에 맞지 않으면 `SelectError`다.
- 02가 넘긴 이름 충돌(`Hidden`·`Outcome`이 `rerun_files`와 `rerun_hidden`에 함께 있다)은 `rerun_hidden`을 모듈로 import해 피했다(`rerun_hidden.Hidden`).
- 시험이 숨은 시험 가르기를 갈아 끼우도록 `main(argv, *, make_sorter=None)`과 `select_rows`를 두었다.
- 하위 프로세스(git)마다 시간 제한(`GIT_TIMEOUT`)을 두고 자식 환경에서 `REPO_LOCATION_VARS`를 벗긴다.
- `rerun_hidden.py`는 아직 다시 열지 않았다. 메모의 Minor 항목과 PR #363의 Minor 둘은 실제 후보 표를 돌려 그 모듈의 결함이 나오면 함께 고칠 생각이었다.

고친 것: Write 도구가 `\u2028`·`\u2029`·`\ufeff` 이스케이프를 날것 문자로 저장해 `_BREAKS` 정규식을 `chr()`로 짓고 BOM 벗기기도 `chr(0xFEFF)`로 바꿨다. `sys.path` 해킹은 지우고 `uv run python -m tools.rerun_select`로 부르게 했다(선례 `morning_collect`).

## 브랜치 표와 실제 기록 훑기

수집 도구(`.scratch/harness/probes/session_cost/collect.py`)를 `--refresh --out .scratch/model-rerun/probes/branches.json`으로 돌렸다(아직 커밋하지 않았다). 그 파일에서 이메일·토큰·사용자 경로 꼴을 grep으로 찾아 0건이었다.

숨은 시험 가르기 없이 싼 조건까지만 세션 스크래치 스크립트로 훑었다(기준 origin/main c3c2cfcf, 손으로 봤다. 스크립트는 커밋하지 않았다). 후보는 77개, 푼 티켓 파일이 둘 이상인 병합 커밋은 #23이었다. 날짜 안에서 싼 조건을 지난 후보는 17개이고, 이 기능의 자기 티켓(model-rerun 01·02)도 규칙상 든다. token-usage-07은 chore 브랜치라, admin-api-03은 docs 브랜치라 빠진다. 날짜 앞 후보는 대개 `-m llm`·`사진 비교` 낱말에 걸리고, 걸리지 않는 9월 후보는 B에 준비·게이트 파일(`web/package.json`, `tools/run_checks.py`)이 0~1개였다. 숨은 시험 가르기를 지나는 수는 아직 모른다.

## 시험과 변이

`tests/tools/test_rerun_select.py`(58개)를 썼고 모두 초록이었다. ruff·pyright도 초록이다. 처음 판에서 고친 것: `_후보`의 `pr - 100`이 `int | None`이라 타입이 맞지 않아 모든 후보에 맞는 브랜치 표 `_ROWS`를 두었다. 거슬러 채우기 표 시험의 후보 차례와 끝 줄 수를 모듈과 대조해 고쳤다. 비공개 함수(`_cell`, `_terms_cell`)를 부르던 두 시험은 `render_table` 출력으로 보게 바꿨다(pyright `reportPrivateUsage`).

구현을 시험보다 먼저 써서 시험은 빨강을 본 적이 없다. 그래서 변이 표 `.scratch/model-rerun/probes/rerun_select_mutations.toml`(27개)을 썼다(아직 커밋하지 않았다). `--check`는 27 모두 원문이 한 번씩 있었다. 첫 실행은 표지를 일부러 비워(`표지-미정`) 실패 출력을 받았다. 26개는 빨갰고, 23번(중간 층을 작은 층의 씨앗으로 섞는다)은 초록이었다. 시험의 층이 셋이라 고를 것이 다 들고 차례만 바뀌는데, 씨앗 2와 3이 그 셋을 같은 차례로 섞은 것으로 본다. 21번(본 측정이 파일럿이 아닌 목록을 받는다)은 빨갰지만 종류 검사가 아니라 층 부족(`작은 층이 1개라`)으로 빨개, 그 갈림을 재지 못했다. 그래서 본 측정 시험을 후보 21개(파일럿을 빼면 층마다 여섯)로, 종류 시험을 `replace(pilot, kind=LIST_MAIN)`으로 고쳤다. 21~24번만 다시 돌려 넷 모두 빨갰고(21은 `DID NOT RAISE`), 출력의 `E` 줄에서 27개의 표지를 골랐다. 표지를 단 27개를 다시 모두 돌려 `변이 27 모두 기대대로`(종료 0)였다(커밋하지 않은 작업 트리, 기준 c3c2cfcf). 그 뒤 `--check`가 27 모두 원문이 한 번씩 있다고 해 소스가 되돌아온 것을 봤다. 인계 계기가 온 뒤에 끝난 실행이라, 모듈은 추적하지 않는 파일이어서 도중에 끊으면 변이를 git으로 되돌릴 수 없어 멈추지 않고 기다렸다.

## 인계: 셀프 리뷰 직전

셀프 리뷰(`/code-review`)를 부른 직후 `hook_handoff`가 컨텍스트 29.7만 토큰으로 계기를 냈다. 인계하지 않는 다섯에 들지 않아(요청 범위는 병합까지, 지시문의 "이어받을 상태"가 `인계:`로 시작하지 않는다, `인계 못함` 줄이 없다, `get_session`에 `parentSessionId`가 없다) 넘긴다. 셀프 리뷰의 단계는 밟지 않았다.

이 세션의 제목은 `feature/05-task-selection`이었고, 넘기기 전에 `feature/05-task-selection (인계함)`으로 바꿨다.

남은 순서(티켓의 "씨앗은 후보 표를 내기 전에 커밋한다" 때문에 커밋이 둘이다).

1. 셀프 리뷰(`/code-review`)와 반영. 반영으로 시험이나 모듈을 고치면 변이 표를 `--check`로 보고, 바뀐 갈림의 변이만 번호로 다시 돈다(전체는 10분 넘게 걸린다).
2. 씨앗을 든 코드를 커밋한다(티켓 `in-progress`, 모듈, 시험, 변이 표, `branches.json`). 커밋 전에 브랜치와 `tools/sibling_overlap.py`를 본다.
3. 실제 후보 표를 백그라운드로 짓는다: `uv run python -m tools.rerun_select table --branches .scratch/model-rerun/probes/branches.json --table .scratch/model-rerun/probes/candidates.md --rev origin/main`. 후보마다 작업 트리 둘에 `uv sync`를 돌려 오래 걸린다. `rerun_hidden.py`의 결함이 나오면 고치고, 그때 티켓 메모의 Minor 항목과 PR #363의 Minor 둘도 함께 보고 `rerun_hidden_mutations.toml`을 `--check`로 본다.
4. 후보 표를 커밋하고, `probes/README.md` 표에 `branches.json`·후보 표·변이 표의 행과 변이 절의 문단을 더한다(형제 03과 그 표에서 겹칠 수 있다).
5. 이 일지와 PR 설명에 2026-10-12 뒤의 남은 후보 수와 거슬러 채운 후보의 B 상태를 적는다. 티켓을 `done`으로 바꾸고(기능은 닫지 않는다) 검증 명령을 돈 뒤 PR과 병합.

인계 지시문.

> 다음 작업: .scratch/model-rerun/issues/05-task-selection.md. 병합 기록에서 후보 티켓을 찾아 까닭과 함께 표로 내고, 층과 씨앗으로 파일럿 셋과 본 측정 여덟을 고른다
> 다음 단계: 구현
> 어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
> 시작 프롬프트: /implement .scratch/model-rerun/issues/05-task-selection.md
> 브랜치: feature/05-task-selection
> 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-24-task-selection.md의 "인계: 셀프 리뷰 직전"(남은 순서), .scratch/model-rerun/issues/05-task-selection.md의 메모
> 이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경(tools/rerun_select.py, tests/tools/test_rerun_select.py, .scratch/model-rerun/probes/rerun_select_mutations.toml, .scratch/model-rerun/probes/branches.json, 티켓의 in-progress, 일지)이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다(일지 docs/journal/2026-10-23-24-task-selection.md). 변이 27은 표지까지 모두 기대대로 빨갰다. 티켓이 씨앗을 든 코드의 커밋을 후보 표의 커밋보다 앞에 두라고 해서, 리뷰를 반영한 뒤 코드를 먼저 커밋하고 실제 후보 표를 돌린다. tools/rerun_hidden.py는 아직 다시 열지 않아, 티켓 메모의 02 판단 항목과 PR #363 claude-review 셋째 회차(30c33ed2)의 Minor 둘(_cut_links가 끊기와 남은 링크 돌려주기를 함께 한다, _checkout의 finally 분기와 _sort를 _run_merge·_run_base로 나누기)이 그대로 남았다
> 확인할 선행 조건: 형제 03(PR #364)·04가 그사이 병합됐으면 .scratch/model-rerun/probes/README.md 표의 행이 겹칠 수 있다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지. 사용자는 측정 도구 짓기까지 이어 가라고 했다(2026-10-22)

워크트리 잠금을 풀었다(`git worktree unlock`, 출력 없이 끝났다).

open-session을 부른다 2026-10-23T01:54Z

## 이어받은 세션: 셀프 리뷰

지시문으로 연 새 세션이 `EnterWorktree(path)`로 이 워크트리에 들어와 이었다. 커밋 전의 `tools/sibling_overlap.py`가 이 일지(24)가 main의 최신 일지(2026-10-23-27)보다 이름순으로 앞이라고 해 `--move`로 31로 옮겼다. 위 인계 지시문 인용의 옛 경로는 그때의 글 그대로 둔다. origin/main은 harness 005(#365) 하나만 전진했고(750761b9), 형제 03(PR #364)·04는 아직 병합 전이다. 두 형제 브랜치 모두 `.scratch/model-rerun/probes/README.md` 표에 행을 더한다.

`/code-review`를 기준 c3c2cfcf, 커밋 0, 바뀐 추적 파일 1(티켓), 미추적 5(모듈, 시험, 변이 표, `branches.json`, 일지)로 돌렸다.

### 명세 축

맞다고 본 것: 층 자르기, 씨앗과 `random.Random(seed).shuffle`, 파일럿 갈래 A·A·E, 엇갈린 차례, 상한, 후보 표의 칸과 끝 세 줄, 독스트링이 드는 명세 절 이름, 거슬러 채우기의 "병합 시각"(M의 `%cI`), 티켓의 시험 사례 목록.

1. [Major] 파일 이름 `human-verification`으로 빠진 후보가 되살아난다. 명세는 "되살리기는 이 낱말로만 빠진 후보에 쓰고, 다른 조건으로 빠진 후보를 든 입력은 오류다"이고 파일 이름은 낱말과 따로 든 조건인데, `external_terms`가 파일 이름 맞음을 `terms`에 넣었다. 날짜 안의 token-usage-09와 kickoff-auto-flow-04가 이 꼴이다. → 고친다. 파일 이름은 낱말 밖의 까닭(`others`)으로 옮긴다.
2. [Minor] 날짜 앞 후보를 되살리기로 받는다. 끝내 닿지 않으면 "닿지 않음·빠짐" 행에 "(되살림: …)"이 붙는다. → 남긴다. 채우기가 닿을지는 숨은 시험을 가른 뒤에야 알고, 되살려도 날짜 조건을 넘지 못해 우회가 생기지 않는다. 그 판단은 11이 사전 등록에 옮길 규칙으로 11의 티켓 메모에 적는다.
3. [Minor] "닿지 않음" 행의 빠진 까닭이 날짜 하나뿐이라 독스트링의 "후보 표에는 걸린 까닭을 모두 적는다"가 거짓이다(admin-api-03 행에 `docs/` 브랜치라는 까닭이 없다). → 고친다. 닿지 않은 행에도 싼 조건의 까닭을 함께 적는다.
4. [Minor] 큰 층이 나머지를 받는 것을 재는 시험이 없다(성공 사례의 m이 모두 3의 배수). → 고친다. 3의 배수가 아닌 m의 시험과 변이를 더한다.
5. [Nit] 명세에 없는 판단 셋(낱말을 대소문자 없이 찾는다, 굵지 않은 `Status:` 머리도 받는다, 날짜 바닥을 KST로 잡았다). → 11의 티켓 메모에 사전 등록으로 옮길 목록으로 적는다.
6. [Nit] 독스트링의 "브랜치 표에 행이 없다"가 실제 문구 "브랜치 표에 PR #N 의 행이 없다"와 다르다. → 고친다.
7. [Nit] 명세가 "B에 티켓 파일 없음"의 예로 든 #335는 harness 001(세 자리)이라 `<NN>` 패턴에 맞지 않아 표에 행이 없다. 결과는 같다(chore 브랜치). → PR 설명에 한 줄 적는다.
8. [Nit] 일지 둘. "admin-api-03은 docs 브랜치라 빠진다"가 날짜 안을 말하는 문장에 들었는데 그 B는 2026-09-23이다. 남은 순서 3의 `--rev origin/main`은 형제가 병합되면 티켓의 "이 티켓의 기준 main"과 달라진다. → 둘 다 받는다. 앞의 것은 아래 "고친 것"에 적고 기록 문장은 두며, 실제 후보 표는 `--rev c3c2cfcf`로 짓는다.

### 표준 축

맞다고 본 것: 시험 58 초록, ruff·`check_instructions`·`check_type_escapes` 통과, `branches.json`에 이메일·토큰·사용자 경로·긴 비밀 꼴 0건, `BACKTICK_PATH`가 `collect.py`와 글자까지 같다, 값만 받는 함수는 git·pytest를 부르지 않는다, `sort`를 부르는 차례, `_blobs`가 `cat-file --batch`를 한 번 부르고 missing·tree·공백 경로를 다룬다, 되살리기 오류 세 갈래, 명세 절 이름.

1. [Minor] `--table`·`--out`의 상위 폴더가 없으면 쓰기의 `OSError`가 트레이스백(종료 1)으로 끝나 독스트링의 종료 코드와 어긋나고, 오래 걸린 가르기를 버린다. → 고친다. 시작할 때 출력 자리의 폴더를 보고, 쓰기의 `OSError`도 `SelectError`(2)로 바꾼다.
2. [Minor] 못 보는 것의 시험이 빠졌다(꼬리 `(<slug> <NN>)`가 티켓과 어긋나는 입력, 티켓 없는 PR, 낱말 밖의 말, 같은 티켓을 푼 M 둘의 `main` 길). → 앞의 셋은 시험을 더한다. 넷째는 남긴다. 겹친 id는 `picks_of`의 시험이 던지는 것을 보고, 고르기의 `SelectError`가 목록 없이 1로 끝나는 길은 `test_고르기_명령은_후보가_모두_싼_조건에서_빠지면_…`이 밟는다.
3. [Minor] `pilot`·`main` 명령의 성공 길(종료 0, 목록 쓰기), `GIT_TIMEOUT` 넘김, `REPO_LOCATION_VARS` 벗기기에 시험이 없다(두 변이가 살았다). → 고친다. 셋 모두 시험을 더한다.
4. [Minor] 변이 표 머리가 "병합 기록 읽기를 포함해"라고 하지만 그 변이는 하나뿐이고, `--first-parent` 빼기·`PR_SUFFIX`의 `$` 빼기·BOM 벗기기 빼기·시간 제한·환경 벗기기 변이가 살았다. → 고친다. 시험을 더하고 그 변이를 표에 더하며 머리를 실제 범위로 고친다.
5. [Minor] `CONTEXT.md` 동사 표의 `check`는 "어긋나면 던진다. 값을 돌려주지 않는다(명령)"인데 `check()`는 `Checked`를 돌려준다. → 고친다. `checked_of`(`<명사>_of`)로 바꾼다.
6. [Minor] 프로브 `README.md`에 행이 없다. → 남은 순서 4에서 더한다.
7. 주장: "표 끝에 PR 번호만 적는다"(번호가 없으면 해시 앞 여덟 자리), `--help` 설명이 독스트링 첫 줄이라 문장 중간에서 끊긴다, `_header`가 `--branches`·`--revive` 경로를 그대로 적어 절대 경로면 커밋할 표에 사용자 경로가 든다. → 셋 다 고친다. 경로는 저장소 안이면 저장소 기준 상대 경로, 밖이면 파일 이름만 적는다.
8. 닿지 않는 코드: `_blobs`의 `ambiguous` 갈래(전체 SHA만 넘긴다), `base not in when`(첫 부모 줄은 각 커밋의 첫 부모를 다음 줄에 든다). → 둘 다 지운다.
9. smell(판단 사항).
   - Duplicated Code: `_GIT`·`_env`·`_git`이 `rerun_hidden.py`와 닮았다 → 남긴다. 두 모듈의 오류 형식이 다르고 `rerun_hidden`은 `VIRTUAL_ENV`도 벗긴다. 02 메모가 모을지 보라고 한 것은 작업 트리 꺼내기·걷기인데 이 모듈은 작업 트리를 꺼내지 않는다. `(merged_at, merge)` 정렬 키 두 자리와 `f"{base}:{path}"` 네 자리 → 고친다(함수 하나씩). `Json` 별칭 → 내지 않는다(`tools/`의 열다섯 도구가 저마다 두는 관례).
   - Mysterious Name: `Checked.row`(브랜치 표의 행)와 `Row`(후보 표의 행)가 헷갈린다 → `Checked.origin`으로 바꾼다. `sort`의 두 뜻 → 남긴다(02의 `sort_candidate`와 같은 말). `pick_*`·`select_*` → 남긴다.
   - Message Chains·Feature Envy·Divergent Change → 남긴다(판단 사항. 한 모듈에 바뀌는 이유가 여럿인 것은 02 메모의 `rerun_hidden` 지적과 같은 모양이고, 나누기는 그 메모의 몫과 함께 본다).
   - Speculative Generality: `build_rows(floor=)`는 부르는 자리가 없다 → 지운다. 같은 꼴인 `check`의 `revived` 인자도 지운다. BOM 벗기기에 시험이 없다 → 시험을 더한다(첫 줄이 `Status:`이고 BOM이 있으면 `status_of`가 값을 못 읽는다).
   - 시험의 Nit 둘(`_섞은`이 `shuffle`을 되풀이한다, 상수를 되풀이하는 시험) → 남긴다. 앞의 것은 명세가 정한 섞기의 정의로 기대값을 짓는 것이고, 뒤의 것은 사전 등록할 값을 고정한다.

### 반영

고친 것.
- 모듈: 파일 이름의 `human-verification`을 낱말 밖의 까닭(`others`)으로 옮겼다(`external_terms`는 글만 받는다). 닿지 않은 행의 까닭에 싼 조건의 까닭을 더했다. `check`를 `checked_of`로, `Checked.row`를 `Checked.origin`으로 바꾸고 쓰이지 않던 `revived`·`floor` 인자를 지웠다. 정렬 키(`_merge_order`)와 블롭 키(`_at`)를 함수 하나씩으로 모았다. 닿지 않는 갈래 둘(`ambiguous`, `base not in when`)을 지웠다. 출력 자리의 폴더를 가르기 전에 보고 쓰기의 `OSError`를 `SelectError`(2)로 바꿨다. 표 머리의 입력 경로를 저장소 기준 상대 경로나 이름만으로 적는다(`_shown`). `--help` 설명을 따로 적었다. 독스트링의 종료 코드, 되살리기, 닿지 않음, PR 표기, 인용 문구를 코드에 맞췄다.
- 시험(58 → 69): 파일 이름은 낱말이 아니고 되살리면 오류다, 낱말 밖의 말("브라우저로 본다")은 걸리지 않는다, 닿지 않은 행의 까닭, 큰 층이 나머지를 받는다(m = 11), 병합 기록 시험에 꼬리 `(zzz 09)`와 제목 중간의 `(#77)`·티켓 없는 PR·BOM 뒤 첫 줄의 `Status:`·곁가지 커밋을 더했다, 자식 환경의 저장소 변수, git 시간 제한, 출력 자리의 폴더 없음(두 명령), 후보 표 쓰기 실패, `pilot`·`main` 명령의 성공 길, 표 머리의 입력 경로.
- 변이 표(27 → 38): 머리말을 실제 범위로 고치고, 원문이 바뀐 다섯(5·6·7·12·13)을 맞췄으며, 새 갈림 열하나(28~38)를 더했다. 28~38은 처음에 표지를 비워(`표지-미정`) 실패 출력을 받은 뒤 고른 단언의 문구로 채웠다. 36의 표지(`PermissionError: [Errno 13] Permission denied`)는 이 PC(윈도)의 문구다.
- 11 티켓에 "05에서 넘어온 메모"를 더했다(명세가 정하지 않아 05가 정한 판단 셋, 되살리기의 규칙 둘. 사전 등록 절에 옮길 정의다).
- 일지(명세 축 8): 앞 절 "브랜치 표와 실제 기록 훑기"의 "admin-api-03은 docs 브랜치라 빠진다"는 날짜 안의 후보가 아니다(그 B는 2026-09-23). 기록 문장은 그대로 두고 여기 바로잡는다.

남긴 것: 위 두 축 절에 "남긴다"로 적은 것(명세 2·5는 11의 메모로, 명세 7은 PR 설명으로 넘긴다, 표준 2의 넷째, smell 일부).

다시 돌린 명령: 시험 파일 69 passed(56초), ruff check·format, pyright 0 errors, `check_type_escapes` 종료 0. 변이는 원문이 바뀐 일곱(5·6·7·9·12·13·27)과 새 열하나를 돌려 모두 표지까지 기대대로 빨갰다(앞의 것은 한 실행, 뒤의 것은 표지를 채운 둘째 실행이 `변이 11 모두 기대대로`). 그 사이에 같은 변이 실행(28~38)을 두 번 띄워 두 프로세스가 같은 모듈에 변이를 넣었다. 명령 줄을 확인하고 둘 다 끈 뒤 `--check`로 38 모두 원문이 제자리인 것을 보고 한 번만 다시 돌렸다. 겹친 두 실행의 결과는 쓰지 않는다. 나머지 검증 명령은 커밋의 pre-commit으로 갈음한다.

PR 직전 리뷰에 밀 주장으로 넘길 새 문장(원문).
- 모듈 독스트링: "파일 이름은 낱말이 아니라 되살리지 않는다(명세 "바깥 검증"의 주석)."
- 모듈 독스트링: "날짜는 보지 않는다. 거슬러 채우기가 그 후보에 닿을지는 숨은 시험을 가른 뒤에야 알고, 닿지 않으면 되살린 후보도 "닿지 않음"으로 빠진다."
- 모듈 독스트링: "출력 자리의 폴더는 숨은 시험을 가르기 전에 본다."
- `_blobs`: "커밋은 전체 해시만 넘겨 이름이 모호할 일이 없다."
- `list_candidates`의 주석: "첫 부모 줄은 커밋마다 그 첫 부모를 다음 줄에 든다"
- `_shown`: "저장소 안이면 저장소 기준 상대 경로이고, 밖이면 이름만이라 사용자 경로가 표에 들지 않는다."
- 11 티켓 메모: "명세는 시간대를 정하지 않았고, Further Notes의 후보 수는 시간대가 +0900인 이 PC에서 `git log --since=2026-10-12`로 센 것이라 KST로 잡았다"
