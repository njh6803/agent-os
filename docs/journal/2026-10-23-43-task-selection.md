# 2026-10-23 (43) 병합 기록에서 다시 풀 과제의 후보를 찾아 표로 내고 층과 씨앗으로 고른다 (model-rerun 05)

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

## 씨앗 커밋과 main 합치기

씨앗을 든 코드를 705f8f16으로 커밋했다. pre-commit은 모두 통과했다(ruff 둘, `checks` 304초: check-ticket·lint-imports·zizmor·check-instructions·check-type-escapes·pyright 둘·run-hooks·web-verify·pytest, 마크다운 표, 줄 구분 문자, 변이 표 원문, 인용 대조 14건 경고 없음, 커밋 메시지). 카나리아 명세와 헌법 판은 바뀐 파일이 없어 `Skipped`였다. 손으로 치는 다섯은 이 결과로 갈음한다.

origin/main(8575f57d. #364 model-rerun 03, #365 harness 005, #367 admin-style)을 합쳤다. 03이 11 티켓 끝에 더한 "03에서 넘어온 메모"가 이 브랜치의 "05에서 넘어온 메모"와 같은 자리에서 겹쳐, 둘 다 남기고 03의 것을 앞에 뒀다. main이 바꾼 파일을 이 브랜치가 이름으로 든 파일과 대조했다. `tools/mutate.py`는 임시 워크트리를 `core.longpaths`를 켜고 지우라는 독스트링 변경이고, `tools/rerun_hidden.py`는 꺼내기와 지우기에 이미 켜 두어 고칠 것이 없다. 프로브 README는 03이 판정 변이 표의 행과 사전 등록 표지 약속을 더했다. 병합 커밋 de5423bd의 pre-commit도 모두 통과했다(`checks` 350초). 그 뒤 sibling_overlap이 origin/main 934f8dfa(#368 web-widget 문서)를 더 봤다. 이 브랜치와 겹치는 파일이 없어 PR 직전에 합친다.

## 실제 후보 표

`PYTHONUTF8=1 uv run python -m tools.rerun_select table --branches .scratch/model-rerun/probes/branches.json --table .scratch/model-rerun/probes/candidates.md --rev c3c2cfcf`를 백그라운드로 띄웠다(de5423bd 위, 2026-10-23 12:25). 끝은 브랜치 표를 모은 때의 main으로 고정했다(명세 축 8).

> 사용자: 2시간 넘게 진행중인거야?

2시간 32분째였다. 싼 조건을 지난 후보가 38개이고(후보 77, 날짜 안 37, 싼 조건을 지난 것 가운데 날짜 안 17. 세션 스크래치 스크립트로 `list_candidates`·`checked_of`만 불러 셌다), 후보마다 작업 트리 둘에 `uv sync`와 pytest를 돌려 하나에 평균 4분 남짓이었다. 날짜 안만으로는 숨은 시험이 셋 이상인 후보가 열둘에 한참 못 미쳐, 거슬러 채우기가 9월의 후보까지 끝까지 내려갔다.

결함: 첫 후보(model-rerun 02, B d0e696c9 M c3c2cfcf)가 `git grep -q 를 띄우지 못했다: embedded null character`로 실패 갈래였다. 02의 시험 가운데 그 한계를 고정하던 `test_못_보는_것_NUL_이_든_문자열은_…`이 본문에 `"a\x00b"`를 들어, 조건 3의 찾을 문자열로 모여 `git grep`의 인자로 넘어갔다. `rerun_hidden.py` 독스트링의 못 보는 것에 적힌 한계였지만, 후보가 모자란 때에 도구의 한계로 후보 하나를 통째로 잃는 것이라 고친다. 돌던 실행은 다른 결함이 더 나오는지 보려고 끝까지 두었다(돌던 프로세스는 모듈을 이미 불러 디스크의 고침이 닿지 않는다).

고친 것: `_body_terms`가 줄바꿈으로 나눈 줄을 NUL에서도 나눠 두 글자 이상인 조각을 센다. 시험 셋. 값 층의 NUL 나누기, 실제 사고와 같은 길(`sort_candidate`)에서 NUL이 든 문자열이 있어도 실패하지 않고 조각으로 조건 3을 보는 것(고치기 전에 같은 문구로 빨갰다), `term_in`에 NUL을 넘기던 못 보는 것 시험을 남는 한계(명령 줄에 넘기지 못할 만큼 긴 문자열, 30만 자)로 바꾼 것. 시험 파일 58 passed(129초). 변이 표는 원문이 바뀐 23번을 맞추고 NUL 나누기 변이(9번)를 더했다. `--check` 25 모두 원문이 한 번씩 있고, 8·9·23번이 표지까지 기대대로 빨갰다(9번은 표지를 비운 첫 실행의 출력에서 `At index 0 diff: 'ab-old\x00c' != 'ab-old'`를 골랐다).

표는 15:17에 썼다(2시간 52분, 가른 후보 38개). 끝 줄: 날짜 안의 남은 후보 1개(ticket-for-every-pr-03, 숨은 시험 3), 거슬러 채워 남은 후보 7개(http-channel-04·03, admin-api-06·04, interrupts-05·04·03), 그 7개 모두 B에 준비·게이트 파일 둘이 다 없다, 푼 티켓 파일이 둘 이상인 병합 커밋 #23. 모두 8개라 문턱 12개에 못 미친다. 가장 흔한 빠진 까닭은 조건 2의 "결과 없음(모음 실패)"이다. 새 모듈을 짓고 그 시험을 새로 쓰는 티켓이 많아, B에 덮은 시험 파일이 import부터 실패해 노드가 모두 빠진다. 숨은 시험 0개·빠진 노드 0개인 행(web-admin-03·04·06·07·08, ticket-for-every-pr-02, kickoff-auto-flow-03)은 M이 바꾼 파이썬 시험 함수가 없는 후보로 본다(코드를 읽어 짐작했다, 재지 않았다). 다른 결함은 나오지 않았다(가르지 못한 후보는 02 하나).

고친 도구로 02 하나만 다시 갈랐다(세션 스크래치 스크립트로 `sort_candidate(".", "d0e696c9", "c3c2cfcf")`를 불러 손으로 봤다). 숨은 시험 0개, 빠진 노드 99개(조건 2 결과 없음(모음 실패) 98, 조건 3 문자열 1)였다. 고쳐도 02는 "숨은 시험이 0개라 3개보다 적다"로 빠지고, 표 끝의 수는 그대로다.

표를 다시 지을지 물었다.

> 질문: 후보 표를 고친 도구로 다시 지을까요? 다시 지어도 결론(8개, 문턱 12개 미달)은 같고, 바뀌는 것은 02 행 하나입니다. 그 행의 세 칸(빠진 까닭, 숨은 시험, 빠진 노드)이 도구 결함 문구에서 '숨은 시험이 0개라 3개보다 적다'와 그 요약으로 바뀝니다. 다른 행은 같은 입력이면 같게 나올 것으로 어림합니다. 참고로 11 티켓의 파일럿 명령은 표를 처음부터 다시 짓기 때문에, 실제 과제 고르기에는 어느 쪽이든 고친 도구가 쓰입니다.
>
> 사용자: 지금 표를 커밋 (Recommended). 설명: 방금 지은 표를 그대로 커밋합니다. 02 행이 고치기 전 도구의 결함 문구로 남는다는 점과, 고친 도구로 02만 다시 가른 결과(숨은 시험 0개, 빠진 노드 99개)를 README 행·일지·PR 설명에 적습니다. 추가로 기다리는 시간이 없습니다.

고르지 않은 선택지는 "고친 도구로 다시 짓기"(약 3시간)였다. 첫 화면은 `hook_choice_facts`가 막아, 바뀌는 칸이 셋인 것과 다른 행이 같다는 것이 어림인 것을 고쳐 다시 물었다.

## 셀프 리뷰: NUL 고침과 후보 표

`/code-review`를 부른 직후 `hook_handoff`가 컨텍스트 339,341 토큰으로 `셀프 리뷰 직전` 경계에 왔다고 알렸다. 이 세션 지시문의 "이어받을 상태"가 `인계: 셀프 리뷰 직전`으로 시작해(위 인계 지시문 인용) next-session "인계할 때" 1의 인계하지 않는 때라 넘기지 않았고, 자동 압축 뒤에 리뷰를 이었다. 기준 de5423bd, 커밋 0, 바뀐 추적 파일 7, 미추적 1(`candidates.md`)로 두 축을 띄웠다. 두 축 모두 Critical·Major는 없었다.

### 표준 축

맞다고 본 것: `_body_terms`가 NUL 하나·둘·앞뒤·연속, 줄바꿈과 섞인 것, 한 글자 조각을 서술대로 나눈다(스크래치 탐침), `term_in`에 NUL을 바로 주면 여전히 `CandidateError`, 이 PC에서 명령 줄 2만 자는 띄워지고 4만 자는 `WinError 206`이며 `sort_candidate`에 긴 문자열을 주면 노드가 아니라 후보 전체가 `Failure`다, 변이 `--check` 25 모두 한 번씩이고 8·9·23번이 표지까지 빨갰으며 9번의 표지는 고른 단언에서만 나온다, 후보 표의 수(77행, 날짜 안 37, 거슬러 채움 40, 남음 1+7, 가른 38, 모음 실패 23행, 0/0 7행, 끝 줄 넷, 해시 261a4650719e), 02 다시 가르기(0, 99), 인용 "실제 후보 수를 본 뒤 정한다".

1. [Minor] "가장 흔한 빠진 까닭은 모음 실패"는 빠진 노드 칸에서만 맞다. 빠진 까닭 칸에서는 바깥 검증 낱말 34행, 숨은 시험 0개 26행이 더 많다. → 고친다.
2. [Minor] README의 `rerun_select_mutations.toml` 문단이 "원문이 바뀐 다섯(5·6·7·12·13)"과 "원문이 바뀐 일곱(5·6·7·9·12·13·27)"을 함께 쓴다. → 고친다. 9·27번은 원문이 아니라 겨누는 시험에 셀프 리뷰가 사례를 더한 변이다(9번 시험의 파일 이름 사례, 27번 시험의 꼬리·제목 중간 PR 번호·티켓 없는 PR·BOM·곁가지 커밋 사례를 시험 파일에서 봤다). 다시 돌린 까닭은 이 세션의 기록에 남지 않아, README에는 두 변이가 무엇이었는지만 적는다.
3. [Minor] NUL 나누기가 조건 3의 정의를 바꾸는데 명세와 11 메모에 없다. → 고친다(명세 축 1과 같다).
4. [Minor] README의 02 다시 가르기 문장에 호출 인자가 없고, "2시간 52분"의 출처가 없으며, 시험 주석의 128KiB는 재지 않은 상수다. → 고친다.
5. [Minor] 긴 문자열 시험의 `match="띄우지 못했다"`는 다른 원인의 띄우기 실패도 지난다. → 고친다. 같은 호출이 짧은 문자열이면 띄워져 답하는 대조를 더했다.
6. [Minor] 05 티켓의 "PR 설명과 일지에 적는다"가 PR 전에 [x]다. → 남긴다(명세 축 2와 함께 아래).
7. [정보] origin/main에 #369(model-rerun 04)가 들어와 프로브 README가 겹친다. 위 "씨앗 커밋과 main 합치기"의 "겹치는 파일이 없다"는 934f8dfa 때의 말이다. → 받는다. PR 직전에 합치며 푼다.
8. [Nit] 표 머리의 "되살릴 목록은 없음다"(→ 고친다. 시험을 먼저 빨갛게 봤다), 변이 표 머리 주석 한 줄이 길다(→ 고친다), 변이 9의 `-k`가 느린 `sort_candidate` 시험까지 고른다(→ 고친다. `NUL_이_든_문자열은_그_자리에서도`로 좁혔다), 시험의 저장소 설정이 여섯째로 복제됐다(→ 남긴다. 같은 파일의 앞 다섯과 같은 꼴이고, 묶으면 변이 표가 고르는 시험 여럿을 함께 고쳐야 한다), `_body_terms`는 `re.split` 하나로 줄어든다(→ 남긴다. 뜻이 같고, 변이 9·23이 지금 두 단계의 원문을 겨눈다), 11 메모의 미룬 까닭이 흐리다(→ 고친다, 명세 축 6과 함께), 05 메모의 미래형이 갱신되지 않았다(→ 고친다).

### 명세 축

맞다고 본 것: 77행 모두 두 파일 칸이 `git cat-file`과, 브랜치·비용 칸이 `branches.json`과, 크기 칸이 `BACKTICK_PATH`로 다시 센 값과 맞는다, M은 늦은 차례이고 B는 늘 M의 부모다, `branches.json`과 씨앗이 705f8f16에 들어 후보 표보다 앞선다, 변이 원문 확인 25와 38, NUL 경계 입력, 02 다시 가르기(0, 99), 11의 Blocked by에 05가 든다, 사용자 답이 요구한 두 사실이 README와 일지에 있다.

1. [Minor] NUL 나누기가 명세에도 11의 사전 등록 메모에도 없다. → 고친다. 명세 조건 3의 주석 뒤에 "(2026-10-23 티켓 05의 실제 후보 표: …)"를 덧붙이고(티켓 01이 구현 PR #361에서 같은 꼴의 주석을 단 선례), 11 메모에 사전 등록으로 옮길 정의로 더했다.
2. [Minor] 체크박스 둘(PR 설명과 일지, 검증 명령이 모두 초록)이 이르게 [x]다. → 남긴다. 티켓은 PR을 열기 전에 done으로 바꾸고(`docs/constitution/operations.md` 가드레일, CI의 `ticket` 잡), 두 항목은 이 커밋의 pre-commit과 PR 직전의 `tools/run_checks.py`, PR을 여는 순간에 채워진다. 어느 하나가 빨가면 PR을 열지 않고 되돌린다.
3. [Minor] "가장 흔한 빠진 까닭"이 범위 없이 쓰였다(빠진 69행 가운데 34행이 바깥 검증 낱말, 모음 실패 23행 가운데 4행은 남은 후보). → 고친다(표준 1과 같다).
4. [Minor] README의 "끝 줄의 수는 그대로다"와 11 메모의 "결론은 같다"는 어림인데 사실처럼 적혔다. → 고친다.
5. [Minor] 세 자리 하네스 티켓은 `TICKET_PATH`의 `[0-9]{2}`에 맞지 않아 표에 행 없이 빠진다(#335). → 남긴다. 명세의 `<NN>`을 글자 그대로 따른 것이고 결과는 같다(chore 브랜치). 위 셀프 리뷰 명세 축 7과 같은 것이라 PR 설명에 적는다.
6. [Minor] 11 메모의 바깥 층 Minor를 미룬 까닭이 사용자의 선택을 넓혀 읽었고, "셋째 회차의 둘:" 뒤 목록이 셋 이상으로 읽힌다. → 고친다. 사용자 결정을 까닭에서 빼고, 05 메모의 PR 봇 항목과 셋째 회차의 둘을 나눠 적고, 그 메모의 조건(다시 열면 함께 고친다)에 닿았다는 것과 넣지 않은 까닭 둘을 적었다.
7. [Minor] 11 메모가 표 한 벌에 드는 시간을 넘기지 않는다. → 고친다. `pilot`과 `main`이 저마다 표를 처음부터 짓고(모듈의 `--help` 설명), 한 벌이 2시간 52분이었다고 적었다.
8. [Nit] "없음다", README의 끝 줄이 셋이라 했지만 넷이다, "2시간 52분"의 출처, 30만 자 시험 주석의 상수. → 모두 고친다(앞의 것과 끝의 둘은 표준 4·8과 같다).

PR 설명에 넣을 것(명세 축): 후보 표는 NUL 고침 전 도구로 지었고, 문턱 12개에 8개, 거슬러 채운 7개의 B 상태, 02 행이 도구 결함 문구이고 고친 도구로 02만 다시 가르면 0개라는 것, 다른 행이 같다는 것은 어림, 표는 사용자 결정으로 다시 짓지 않았다.

### 반영

고친 것.
- README: 결과 절의 "가장 흔한 까닭"을 두 칸으로 나눴다(빠진 까닭 칸은 바깥 검증 낱말 34/69, 노드 칸은 모음 실패 23/30행·705노드, 다음은 조건 2 통과 10행, 모음 실패 23행 가운데 4행이 남은 후보. 세션 스크래치 스크립트 `row_reasons.py`·`node_reasons.py`로 셌다). 02 다시 가르기 문장에 호출 인자를 적고 끝 줄이 그대로라는 것을 어림으로 고쳤다. 표 행에 끝 줄 넷째와 "2시간 52분"의 출처를 적고, 결과 절 머리에 "없음다"가 그 판 도구의 문구라고 적었다. 변이 문단의 다섯·일곱을 바로잡았다.
- 일지(이 파일): 앞 절 "실제 후보 표"의 "가장 흔한 빠진 까닭은 조건 2의 "결과 없음(모음 실패)"이다"는 빠진 노드 칸에서만 맞다. 기록 문장은 그대로 두고 여기 바로잡는다. "씨앗 커밋과 main 합치기"의 "겹치는 파일이 없어"도 934f8dfa 때의 말이고, 그 뒤 #369가 프로브 README를 바꿨다.
- 명세 조건 3에 티켓 05 주석을, 11 메모에 NUL 정의 항목을 더했다. 11 메모의 후보 표 항목을 어림과 시간까지 적게, 바깥 층 항목을 까닭 둘로 고쳤다. 05 메모의 미래형 뒤에 실제로 넘긴 곳을 적었다.
- 도구: 표 머리의 "없음다"를 "없다"로 고쳤다(`_header`). 시험에 "되살릴 목록은 없다." 단언을 더해 고치기 전에 빨간 것을 봤다.
- 시험: 긴 문자열 시험에 짧은 문자열 대조를 더하고 주석의 상수를 재지 않은 문서 상수로 밝혔다.
- 변이 표: 9번의 `-k`를 값 층 시험 하나로 좁히고 머리 주석의 긴 줄을 나눴다.

남긴 것: 표준 6·명세 2(체크박스, 까닭은 위), 명세 5(PR 설명으로), 표준 8의 둘(시험 설정 복제, `re.split`).

다시 돌린 명령: 두 시험 파일 127 passed(314초). 변이 원문 확인은 숨은 시험 25·고르기 38 모두 한 번씩이고, 좁힌 9번은 표지까지 기대대로 빨갰다(`변이 1 모두 기대대로`). 나머지 검증 명령은 커밋의 pre-commit으로 갈음한다.

커밋 전의 `tools/sibling_overlap.py`가 이 일지(31)가 origin/main의 최신 일지(2026-10-23-33)보다 이름순으로 앞이라고 해 `--move`로 38로 옮겼다(README, 시험 주석, `rerun_hidden.py` 독스트링의 인용도 함께 옮겨졌다). 같은 출력에서 형제 07(워크트리 `07-gates-and-official-cost`)이 `tools/rerun_hidden.py`와 그 시험, 변이 표, 05 티켓, 명세를 함께 고치고 있었다. 나중에 병합하는 쪽에서 글자 충돌이 날 수 있어 PR 설명에 적는다.

PR 직전 리뷰에 밀 주장으로 넘길 새 문장(원문).
- README: "후보가 빠진 까닭은 바깥 검증 낱말이, 노드가 빠진 까닭은 조건 2의 "결과 없음(모음 실패)"이 가장 흔하다." 와 그 뒤의 수(34, 29, 30, 23, 705, 10, 4)
- README: "다른 행이 같은 입력이면 같게 나온다는 것은 다시 짓지 않은 어림이라, 끝 줄의 수가 그대로라는 것도 어림이다."
- README: "그 다섯과 겨누는 시험에 사례가 더해진 둘(9번의 되살리기 오류 시험에 파일 이름 사례가, 27번의 병합 기록 시험에 꼬리·제목 중간의 PR 번호·티켓 없는 PR·BOM·곁가지 커밋 사례가 더해졌다)"
- 명세: "NUL이 든 인자는 하위 프로세스를 띄울 때 `embedded null character`로 거부되어, 나누지 않으면 그 후보 전체가 실패 갈래였다."
- 11 메모: "`pilot`과 `main` 명령은 저마다 표를 처음부터 다시 지으므로" 와 "한 벌을 짓는 데 이 PC에서 2시간 52분(가른 후보 38개)이 들었으니"
- 11 메모: "05가 고친 것은 값 층의 문자열 나누기 한 줄이라 바깥 층과 겹치지 않고, 그 항목들은 PR 봇이 Minor로 매긴 구조 정리라 05의 수용 기준(후보 표와 고르기)에 닿지 않는다."
- 시험 주석: "윈도는 명령 줄 전체가 32767자(CreateProcess 의 한도), 리눅스는 인자 하나가 128KiB (MAX_ARG_STRLEN)를 넘으면 띄우지 못한다."

## 인계: 커밋 뒤

반영을 06af4aab로 커밋했다(후보 표, NUL 고침, 셀프 리뷰 반영, 일지 옮기기). pre-commit은 모두 통과했다(ruff 둘, `checks` 440초: check-ticket·zizmor·lint-imports·check-instructions·check-type-escapes·pyright 둘·run-hooks·web-verify·pytest, 마크다운 표, 줄 구분 문자, 변이 표 원문, 인용 대조 11건 경고 없음, 커밋 메시지). 카나리아 명세와 헌법 판은 바뀐 파일이 없어 `Skipped`였다. 손으로 치는 다섯은 이 결과로 갈음한다.

커밋 직후 `hook_handoff`가 컨텍스트 278,529 토큰으로 `커밋 뒤` 경계에 왔다고 알렸다. 이 세션이 넘겨받은 경계(`셀프 리뷰 직전`)와 다르고, 요청 범위는 병합까지이며, `get_session`의 `self`에 `parentSessionId`가 없어 곁 세션도 아니다. 그래서 인계한다. 이 세션의 지금 제목은 `feature/05-task-selection`이다. 이 브랜치에 열린 PR은 없다(`gh pr view`가 "no pull requests found").

남은 순서.
1. origin/main을 합친다. 겹치는 파일은 `.scratch/model-rerun/probes/README.md`다(#369 model-rerun 04가 행을 더했다). 합친 뒤 `tools/sibling_overlap.py`를 다시 친다.
2. ruff 둘을 치고 `uv run python tools/run_checks.py`를 백그라운드로 돌린다.
3. PR 직전 리뷰(`docs/constitution/operations.md` 리뷰 파이프라인 2). `coderabbit auth status`를 보고, 돌지 못하면 `/security-review`와 `bug-perf-review`로 한다. 밀 주장은 이 일지 두 절의 "PR 직전 리뷰에 밀 주장으로 넘길 새 문장" 목록이다("이어받은 세션: 셀프 리뷰"의 일곱과 "셀프 리뷰: NUL 고침과 후보 표"의 일곱). 앞 절의 NUL 독스트링 문장, 프로브 README의 결과 절, 11 메모의 05 항목도 겨눈다.
4. `/git-pr`로 PR을 연다. PR 설명에 넣을 것.
   - 후보 표는 NUL 고침 전 도구(de5423bd)로 main c3c2cfcf를 끝으로 지었다. 그 뒤의 병합(03 #364 이후)은 표 밖이다.
   - 문턱 12개에 남은 후보 8개다. 날짜 안 1개(ticket-for-every-pr-03), 거슬러 채운 7개(http-channel-04·03, admin-api-06·04, interrupts-05·04·03). 거슬러 채운 7개는 모두 B가 2026-09-21~26이고 B에 `web/package.json`과 `tools/run_checks.py`가 둘 다 없다. 길은 티켓 11이 사람에게 묻는다.
   - model-rerun-02 행은 도구 결함 문구다. 고친 도구로 02만 다시 가르면 숨은 시험 0개, 빠진 노드 99개라 그 행은 여전히 빠진다. 다른 행이 같다는 것은 어림이다. 표는 사용자 결정으로 다시 짓지 않았다.
   - 이 기능의 티켓(01·02)도 후보로 든다.
   - 명세가 "B에 티켓 파일 없음"의 예로 든 #335는 세 자리 하네스 티켓이라 `<NN>`에 맞지 않아 표에 행이 없다. 결과는 같다(chore 브랜치).
   - 형제 07(워크트리 `07-gates-and-official-cost`)이 `tools/rerun_hidden.py`와 그 시험, 변이 표, 05 티켓, 명세를 함께 고친다. 나중에 병합하는 쪽에서 글자 충돌이 날 수 있다.
5. ccd_pr로 PR을 묶고 CI와 봇 회차를 본 뒤, 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 병합하고 next-session을 부른다.

인계 지시문.

> 다음 작업: .scratch/model-rerun/issues/05-task-selection.md. 병합 기록에서 후보 티켓을 찾아 까닭과 함께 표로 내고, 층과 씨앗으로 파일럿 셋과 본 측정 여덟을 고른다
> 다음 단계: 구현
> 어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
> 시작 프롬프트: /implement .scratch/model-rerun/issues/05-task-selection.md
> 브랜치: feature/05-task-selection
> 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-38-task-selection.md의 "인계: 커밋 뒤"(남은 순서와 PR 설명에 넣을 것), 같은 일지 두 절의 "PR 직전 리뷰에 밀 주장으로 넘길 새 문장"
> 이어받을 상태: 인계: 커밋 뒤. 실제 후보 표, NUL 고침, 셀프 리뷰 반영을 커밋했고 pre-commit이 모두 통과했다. PR은 아직 없고, origin/main 합치기, 전체 검사, PR 직전 리뷰, PR, 봇 회차, 병합이 남았다(일지 docs/journal/2026-10-23-38-task-selection.md)
> 확인할 선행 조건: origin/main에 #369(model-rerun 04)가 들어와 .scratch/model-rerun/probes/README.md가 겹친다. 형제 07(워크트리 07-gates-and-official-cost)이 tools/rerun_hidden.py와 그 시험·변이 표·05 티켓·명세를 함께 고친다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지. 사용자는 측정 도구 짓기까지 이어 가라고 했다(2026-10-22)

제목을 `feature/05-task-selection (인계함)`으로 바꿨다. 멈출 백그라운드 작업은 없었다. 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-23T07:45Z

## 이어받은 세션: main 합치기

지시문으로 연 새 세션이 `EnterWorktree(path)`로 이 워크트리에 들어와 이었다. 세션 제목을 `feature/05-task-selection`으로 바꿨다.

origin/main(893e0fe8. #368 web-widget 문서, #369 model-rerun 04, #366 harness 007, #370 model-rerun 06)을 합쳤다. 글자 충돌은 프로브 README 표 끝 하나였다. 이 브랜치의 세 행(`branches.json`, `candidates.md`, `rerun_select_mutations.toml`)과 main의 두 행(04의 `rerun_round_mutations.toml`, 06의 `rerun_session_mutations.toml`)을 모두 남겨 티켓 번호 차례(04 → 05 → 06)로 놓았다. 명세는 자동으로 합쳐졌다(같은 문단에 이 브랜치가 덧붙인 NUL 주석만 남는다). main이 바꾼 파일을 이 브랜치가 이름으로 든 파일과 대조했다. `tools/rerun_files.py`는 비공개 상수 셋을 공개 이름(`MODEL_FORM`·`IDENT_FORM`·`VERSION_FORM`)으로 바꿨고, `tools/rerun_select.py`는 그 상수를 가져오지 않아 고칠 것이 없다. 게이트 쪽은 harness 007이 pre-commit과 CI에 `rg`를 요구하는 줄(ADR 0038)을 더한 것이 전부다.

병합 커밋 5b1efeca의 pre-commit은 충돌 파일만 보아 ruff 둘이 `Skipped`였고 `checks`는 통과했다(656초: check-ticket·zizmor·lint-imports·check-instructions·check-type-escapes·pyright 둘·run-hooks·web-verify·pytest). ruff 둘은 손으로 쳐 통과했다.

## PR 직전 리뷰

`coderabbit auth status`가 `Seat: not assigned`라 CLI가 돌지 못해 대체 둘을 돌렸다. 버그·성능은 `bug-perf-review`를 두 갈래(코드와 시험, 문서와 측정 기록)로 나눠 띄웠다. 한 갈래에 밀 주장 열넷과 파일 열셋을 다 주면 도구 호출 40번 안에 닿지 못할 것으로 봤다. 보안은 내장 `/security-review`다. 기준은 5b1efeca(merge-base 893e0fe8)다.

- 보안: 지적 없음. 하위 프로세스는 셸 없이 인자 목록으로 띄우고, 쓰기 경로는 사람이 주는 CLI 인자이며, `branches.json`에 이메일·토큰·사용자 경로 꼴이 없다. 보고 문턱 아래로 `--rev`가 `-`로 시작해도 막지 않는 것을 적었다(신뢰하는 CLI 인자라 뺐다).
- 문서·수치 갈래: 유효 0, 보류 2. 밀 주장 아홉(README 결과 절의 수, 어림 문장, 변이 문단, 명세의 NUL 주석, 11 메모 셋, 끝 줄, 2시간 52분)은 모두 근거와 맞았다. 보류 둘은 이 세션이 닫았다. `rerun_hidden_mutations.toml`의 `[[mutation]]`은 25개라 "25 모두"가 맞다. 11 티켓 본문(15·35행)이 파일럿 전과 본 측정 전에 `branches.json`을 다시 모으라고 이미 적어, `--rev` 기본값(`origin/main`)이 05 뒤의 병합까지 드는 것이 의도대로다. 둘 다 오탐이다.
- 코드 갈래: 유효 Minor 셋, 오탐 다섯. 밀 주장 여덟(파일 이름 되살리기, 날짜, 출력 자리, `_blobs`, 첫 부모 줄, `_shown`, 명령 줄 한도, NUL 나누기)은 모두 사실이었다. 명령 줄 한도는 이 PC에서 3만2천5백 자까지 답하고 3만2천7백 자부터 `WinError 206`이었다(리뷰어가 `term_in`을 불러 봤다).

고친 것(셋 모두 고치는 값이 작아 PR 전에 고쳤다).
1. 브랜치 표의 한 행이 `cost_post_pr > cost`이거나 NaN이면 PR 앞 비용이 음수나 NaN이 되어, 가르기가 끝난 뒤 과제 목록을 쓸 때 `rerun_files`의 `ShapeError`가 잡히지 않고 트레이스백과 종료 1로 끝났다(리뷰어가 실제 `branches.json`에 그 값을 넣어 재현했다). `_branch_row`가 두 칸이 0 이상의 유한한 수이고 `cost_post_pr`이 `cost`보다 크지 않은지 보고 `SelectError`(2)로 거부한다. 실제 표 366행은 모두 지난다(세션에서 `uv run python -c`로 셌다).
2. 출력 자리의 앞선 검사가 부모 폴더만 봐, 그 자리가 폴더이거나 읽기 전용 파일이면 가르기를 다 돈 뒤에야 2로 끝나 결과를 잃었다. 그 자리가 폴더인지와, 이미 있는 파일이면 `os.access`로 쓸 수 있는지를 함께 본다. 원래의 쓰기 실패 시험은 넓힌 검사에 먼저 걸리지 않게, 검사 뒤 가르기를 지을 때 그 자리에 폴더를 만들도록 바꿨다. 독스트링의 못 보는 것에 그 뒤에 쓸 수 없게 된 자리를 적었고, 그 시험이 고정한다.
3. `-c core.quotepath=false log`의 알림이 `git -c core.quotepath=false`로 찍혔다. `rerun_hidden`의 `_git_name`과 같은 규칙의 `git_name`을 두었다.

시험 아홉(비용 넷, 출력 자리 둘, git 이름 셋)은 고치기 전에 빨간 것을 봤다. 읽기 전용 갈래는 가르기를 부른 뒤 `Permission denied`로 끝나 리뷰의 시나리오가 그대로 났다. 시험 파일 78 passed, 두 파일 pyright 0 errors, ruff 통과다. 변이 원문 확인 38 모두 한 번씩, 35·36번이 표지까지 기대대로 빨갰다.

남긴 것(오탐·Nit): 11 메모의 "한 줄"(한 문장이 세 줄이 됐다), 변이 문단의 "그 다섯과 … 둘" 문장의 모호함, 변이 표 행에 걸리는 시간이 없는 것, 커밋하지 않은 스크래치 스크립트, `_shown`이 `repo/..`를 `..`으로 적는 것. 모두 뜻을 바꾸지 않아 두었다.

## 인계: PR 연 뒤

반영을 a5726119로 커밋했다. pre-commit은 모두 통과했다(ruff 둘, `checks` 378초: check-ticket·zizmor·lint-imports·check-instructions·check-type-escapes·pyright 둘·run-hooks·web-verify·pytest, 마크다운 표, 줄 구분 문자, 변이 표 원문, 인용 대조 경고 없음, 커밋 메시지). 커밋 직후 `hook_handoff`가 `커밋 뒤` 경계를 알렸지만, 이 세션 지시문의 "이어받을 상태"가 `인계: 커밋 뒤`로 시작해 넘기지 않고 이었다.

푸시하고 PR #371을 열었다(`gh pr create`, 본문은 템플릿대로 채웠다. 실제 후보 표의 결과, 형제 07과의 충돌 가능성, PR 직전 리뷰 셋의 결과를 적었다). 직후 `hook_handoff`가 컨텍스트 346,803 토큰으로 `PR 연 뒤` 경계를 알렸다. 넘겨받은 경계와 다르고, 요청 범위는 병합까지이며, `get_session`의 `self`에 `parentSessionId`가 없고, `인계 못함` 줄도 없어 인계한다. `@coderabbitai review` 코멘트는 남기지 않았고 ccd_pr로 묶지도 않았다(앱의 `get_session`은 이 세션에 PR #371을 이미 보인다). 이 절은 커밋하지 않았다. 새 세션이 첫 반영 커밋에 싣는다. 이 세션의 지금 제목은 `feature/05-task-selection`이다.

인계 지시문.

> 다음 작업: .scratch/model-rerun/issues/05-task-selection.md. 병합 기록에서 후보 티켓을 찾아 까닭과 함께 표로 내고, 층과 씨앗으로 파일럿 셋과 본 측정 여덟을 고른다
> 다음 단계: PR 반영·병합
> 어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
> 시작 프롬프트: /implement .scratch/model-rerun/issues/05-task-selection.md
> 브랜치: feature/05-task-selection
> 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-38-task-selection.md의 "PR 직전 리뷰"와 "인계: PR 연 뒤"
> 이어받을 상태: 인계: PR 연 뒤. PR #371을 a5726119로 열었고 next-session 순서 1의 2(봇 회차)부터 한다. ccd_pr로 PR을 묶고, 첫 @coderabbitai review 코멘트도 새 세션이 남긴다. 일지의 "인계: PR 연 뒤" 절은 커밋하지 않았으니 첫 반영 커밋에 싣는다(일지 docs/journal/2026-10-23-38-task-selection.md)
> 확인할 선행 조건: 형제 07(워크트리 07-gates-and-official-cost)이 tools/rerun_hidden.py와 그 시험·변이 표·05 티켓·명세·프로브 README를 함께 고친다. 07이 먼저 병합되면 이 PR에 글자 충돌이 날 수 있다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지. 사용자는 측정 도구 짓기까지 이어 가라고 했다(2026-10-22)

제목을 `feature/05-task-selection (인계함)`으로 바꿨다. 멈출 백그라운드 작업은 없었다(커밋과 서브에이전트 셋이 모두 끝났다). 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-23T08:31Z

## 이어받은 세션: 봇 회차

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. (… 위 "인계: PR 연 뒤"의 지시문과 같다 …) 인자: .scratch/model-rerun/issues/05-task-selection.md

`git worktree list`에서 브랜치가 `.claude/worktrees/05-task-selection`(a5726119)에 있어 `EnterWorktree(path)`로 들어갔다. 세션 제목을 `feature/05-task-selection`으로 바꿨다. 커밋하지 않은 변경은 넘겨받은 대로 이 일지 하나였다. origin/main은 893e0fe8 그대로라 합칠 것이 없었고, 형제 07은 아직 PR이 없다.

PR #371을 `bind_pr`로 이 세션에 묶었다. `@coderabbitai review`를 남기고 `tools/wait_ci.py 371`을 백그라운드로 띄웠다(그때 `python` 잡만 pending이었다).

claude-review 첫 회차(a5726119의 실행): 경계 지적 없음, 유지보수성 Minor 하나. `tools/rerun_select.py` 한 모듈이 값 층, git 읽기 층, 명령 줄 층을 다 담아 1033행이니 git 읽기 층을 다른 모듈로 빼라는 것이다. 고치지 않고 까닭을 PR 코멘트로 남겼다. 같은 계열 도구(`rerun_hidden.py`의 `# --- 바깥 층 ---`, `rerun_round.py`)가 한 파일 안에서 구분선으로 층을 나누는 꼴이고, 값 층 시험이 git 없이 도는 것은 이미 함수 경계가 지킨다(시험 파일의 앞 마흔여 개는 값만 넘기고, git을 띄우는 시험은 700행 뒤에 모였다). 리뷰가 근거로 든 형제 07과의 충돌 범위에도 이 파일은 없다(`git diff --name-only origin/main...refs/heads/feature/07-gates-and-official-cost`의 `tools/` 파일은 `rerun_cost`·`rerun_files`·`rerun_gates`·`rerun_hidden`·`rerun_round`·`tidy_checkouts`). 뒤로 넘기는 일이 아니라 일지 "다음"에는 적지 않는다.

`wait_ci`가 끝났다. 검사 여덟 모두 통과, CodeRabbit `Review completed`. CodeRabbit 첫 회차(a5726119): Minor 하나. `_write`가 `OSError`만 `SelectError`로 바꿔, 과제 목록을 쓸 때 `rerun_files`의 `ShapeError`가 나면 가르기를 다 돈 뒤 트레이스백과 종료 1로 끝난다는 것이다. 근거를 보니 맞았다. 앞 세션이 비용 칸을 막은 뒤에도 그 길이 둘 남았다.
- 브랜치 표의 `top_model_effort`가 빈 글(`""`)이면 `_branch_row`는 글인지만 보아 지나가고, 과제 목록은 `opt_text`가 빈 글을 받지 않아 쓸 때 터진다. 실제 표 366행에 빈 글은 없다(`uv run python -c`로 값을 셌다. null 19, 나머지는 모두 `claude-…/<레벨>`).
- 병합 기록에서 온 slug가 과제 id의 꼴(`_TASK_ID`, 영소문자·숫자·`-`)이 아니면(대문자 slug의 `A-01`) 쓸 때 터진다. 이 저장소의 `.scratch` 폴더 이름은 모두 그 꼴이다(`ls .scratch`를 정규식으로 걸렀다).

고친 것(커밋하지 않음).
1. `_branch_row`가 빈 `top_model_effort`를 `SelectError`("top_model_effort 가 빈 글이다")로 가르기 전에 거부한다. 꼴 검사 매개변수 표에 한 줄을 더했다.
2. `_write`가 `(OSError, ShapeError)`를 받아 `SelectError`(2)로 바꾼다. 새 시험 `test_고른_과제가_과제_목록의_꼴에_맞지_않으면_목록을_쓰지_않고_2로_끝난다`가 대문자 slug 저장소로 `pilot`을 돌려 2, "과제 목록 … 를 쓰지 못했다", 후보 표는 있고 목록은 없음을 본다. 그 저장소를 지으려고 `_여러_후보_저장소`에 `slug` 인자를 두고, 브랜치 표 행을 `_여러_후보_브랜치_표`로 뺐다(앞의 파일럿·본 측정 시험도 그것을 쓴다).
3. 독스트링: 종료 코드 문단에 "`top_model_effort`는 null이거나 빈 글이 아니어야 한다", 못 보는 것에 "병합 기록과 가르기에서 온 값이 과제 목록의 꼴(`tools/rerun_files.py`)에 맞는지는 미리 보지 않는다. 맞지 않으면(대문자가 든 slug의 과제 id) 목록을 쓰는 때에야 2로 끝나 가른 결과를 잃는다."
4. 변이 36번("쓰기의 OSError 를 고르기의 오류로 바꾸지 않는다")의 원문을 새 `except` 줄로, 바꿀 글을 `except ShapeError`(`OSError`를 뺀다)로 맞췄다. 프로브 README의 그 행 끝에 이 반영을 한 문장 더했다.

시험 둘은 고치기 전에 빨간 것을 봤다(빈 글은 거부되지 않았고, 대문자 slug는 `ShapeError: 과제 목록.tasks[0].task_id: 정해진 꼴의 문자열가 아니다: 'A-04'` 트레이스백). 고친 뒤 시험 파일 80 passed, 두 파일 ruff check·format·pyright 0 errors. 변이 원문 확인 38 모두 한 번씩, 36번을 골라 돌려 표지(`PermissionError: [Errno 13] Permission denied`)까지 기대대로 빨갰다.

셀프 리뷰에 밀 주장으로 넘길 새 문장: 위 3의 독스트링 두 문장, 시험 주석 둘("과제 목록은 빈 글을 받지 않아 과제 목록을 쓸 때에야 ShapeError 로 터진다", "대문자 slug 의 과제 id(`A-01`)는 과제 목록이 받지 않아 목록을 쓸 때에야 ShapeError 가 난다"), `_branch_row`의 주석 "과제 목록이 빈 글을 받지 않는다(위 비용과 같은 까닭)", `_write`의 주석 "ShapeError: 고른 값이 과제 목록의 꼴이 아니다", 프로브 README 행 끝의 새 문장, 그리고 claude-review 보류 코멘트(issuecomment-6360926177)의 사실 셋(같은 계열 도구의 구분선, 값 층 시험이 git 없이 돈다, 07의 `tools/` 파일 목록).

CodeRabbit의 인라인 코멘트(id 4357714959)에는 아직 답하지 않았다. 반영을 푸시한 뒤 답한다. CodeRabbit 리뷰 본문이 "Your plan provides up to 1 included review per hour; 0 remain after this review"라고 적어, 다음 `@coderabbitai review`는 한도에 걸릴 수 있다(걸린 푸시는 회차로 세지 않는다).

## 인계: 셀프 리뷰 직전

위 반영을 마치고 `/code-review a5726119`를 부른 직후 `hook_handoff`가 컨텍스트 237,111 토큰으로 `셀프 리뷰 직전` 경계를 알렸다. 넘겨받은 경계(`PR 연 뒤`)와 다르고, 요청 범위는 병합까지이며, `get_session`의 `self`에 `parentSessionId`가 없고, `인계 못함` 줄도 없어 인계한다. 셀프 리뷰는 밟지 않았다. 이 세션의 지금 제목은 `feature/05-task-selection`이다.

남은 순서. 셀프 리뷰(`/code-review a5726119`)와 그 반영 → 회고(`retro`)와 `## 다음` → 커밋(이 일지 포함) → 푸시 → CodeRabbit 인라인 코멘트에 답 → `@coderabbitai review`와 `tools/wait_ci.py 371` → 봇 둘째 회차(Critical·Major만) → 병합(이 워크트리 사본의 next-session "워크트리에서 병합할 때").

인계 지시문.

> 다음 작업: .scratch/model-rerun/issues/05-task-selection.md. 병합 기록에서 후보 티켓을 찾아 까닭과 함께 표로 내고, 층과 씨앗으로 파일럿 셋과 본 측정 여덟을 고른다
> 다음 단계: PR 반영·병합
> 어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
> 시작 프롬프트: /implement .scratch/model-rerun/issues/05-task-selection.md
> 브랜치: feature/05-task-selection
> 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-38-task-selection.md의 "이어받은 세션: 봇 회차"와 "인계: 셀프 리뷰 직전"
> 이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 a5726119)부터 한다. 변경은 PR #371 CodeRabbit 첫 회차 반영(_write 가 ShapeError 도 2로, 빈 top_model_effort 거부, 시험 둘, 변이 36번 원문, 프로브 README 한 문장)과 일지 두 절이다. 밀 주장은 일지 "이어받은 세션: 봇 회차"의 목록이다. claude-review 첫 회차의 Minor 는 보류 코멘트를 이미 남겼고, CodeRabbit 인라인 코멘트에는 푸시 뒤 답한다. 그 뒤 회고와 "다음", 커밋, 푸시, 봇 둘째 회차(Critical·Major만), 병합. docs/journal/2026-10-23-38-task-selection.md
> 확인할 선행 조건: 형제 07(워크트리 07-gates-and-official-cost)이 tools/rerun_hidden.py와 그 시험·변이 표·05 티켓·명세·프로브 README를 함께 고친다. 07이 먼저 병합되면 이 PR에 글자 충돌이 날 수 있다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지. 사용자는 측정 도구 짓기까지 이어 가라고 했다(2026-10-22)

제목을 `feature/05-task-selection (인계함)`으로 바꿨다. 멈출 백그라운드 작업은 없었다(`wait_ci`는 끝났다). 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-23T08:52Z

## 이어받은 세션: 셀프 리뷰와 봇 둘째 회차

`git worktree list`에서 브랜치가 `.claude/worktrees/05-task-selection`(a5726119)에 있어 `EnterWorktree(path)`로 들어갔다. 세션 제목을 `feature/05-task-selection`으로 바꿨다. 커밋하지 않은 변경은 넘겨받은 대로 다섯 파일(모듈, 시험, 변이 표, 프로브 README, 이 일지)이었다. origin/main은 893e0fe8 그대로였고, 형제 07은 PR #372를 열었다(08:53Z). 07과 이 브랜치가 함께 바꾸는 파일은 05 티켓, 명세, 프로브 README, `rerun_hidden.py`와 그 시험·변이 표다. 07이 바꾸는 `tools/rerun_files.py`는 회차 결과의 `SetupFailure`·`Gate` 쪽이라 이 모듈이 쓰는 과제 목록의 꼴과 겹치지 않는다(`git diff origin/main...refs/remotes/origin/feature/07-gates-and-official-cost -- tools/rerun_files.py`).

`/code-review a5726119`를 기준 a5726119, 커밋 0, 바뀐 추적 파일 5, 미추적 0으로 돌렸다. 명세 출처는 05 티켓, 기능 명세, PR #371의 CodeRabbit 인라인 지적(이 반영의 요구)이다.

### 표준 축

문서화된 표준의 하드 위반은 없었다. 맞다고 본 것: `rerun_files`가 빈 `original_model_effort`를 `정해진 꼴의 문자열가 아니다: ''`로 거부한다(함수를 불러 봤다), 변이 표 38개의 원문이 모두 한 번씩이고 36번의 새 바꿀 글(`except ShapeError`)에서 `PermissionError`가 새어 이름·표지와 맞는다, `branches.json` 366행에 null 19·빈 글 0, `.scratch` 폴더 이름이 모두 과제 id의 slug 꼴이다, 보류 코멘트의 사실 셋(07 브랜치에 d5db123e가 더해졌지만 `tools/` 목록은 같다).

1. [Minor] 독스트링의 못 보는 것 "병합 기록과 가르기에서 온 값이 과제 목록의 꼴에 맞는지는 미리 보지 않는다"는 시험으로 고정된 것이 대문자 slug뿐이다. 가르기에서 온 값(숨은 시험, 준비 파일)은 `rerun_hidden.py`가 `is_test_file`·`is_support_file`로 이미 거른다. slug는 대문자 말고도 `my_slug`·`a.b`·`한글`이 `_TASK_ID`에 맞지 않는다(리뷰어가 `fullmatch`로 봤다). → 고친다. 과제 목록의 칸을 `_task`에서 하나씩 보니 이 모듈이 미리 보지 않는 것은 slug로 지은 `task_id` 하나라(비용·`branch`·`top_model_effort`는 `_branch_row`가 본다), 그 항목을 slug의 과제 id로 좁히고 괄호를 예시로 밝혔다.
2. [Nit] 새 시험이 `과제 목록 … 를 쓰지 못했다`만 보아 `OSError` 갈래로 빨개져도 지난다. `CODING_STANDARDS.md`의 "실패를 기대하는 테스트는 실패의 까닭까지 단언한다"에 걸린다. → 고친다. `task_id: 정해진 꼴의 문자열가 아니다: 'A-`를 함께 단언한다.
3. [판단] Shotgun Surgery 기미: `_branch_row`가 `rerun_files`의 꼴 규칙을 조각조각 되풀이한다(비용, 빈 글). → 남긴다. 리뷰어도 지금 크기에서는 이 방식이 낫다고 봤고, 과제를 일찍 지어 꼴을 보는 쪽은 가르기 전에 후보마다 숨은 시험을 알아야 해 지금 순서로는 할 수 없다.

### 명세 축

맞다고 본 것: 새 시험 둘을 a5726119의 옛 모듈에 대 보니 둘 다 빨갰다, 시험 파일 80 passed, 변이 원문 38, 일지의 수(366행, null 19, 빈 글 0, `.scratch` 폴더 22개와 origin/main 첫 부모 기록의 slug 17개가 모두 `_TASK_ID` 꼴, 1033행, 07의 `tools/` 여섯, PR #372 08:53Z, CodeRabbit 한도 문구), 브랜치 표에서 오는 칸은 모두 미리 보고 병합 기록과 가르기에서 오는 칸은 보지 않는 가름. `original_model_effort`는 패턴 없이 `opt_text`라 `"foo"`·`" "`·`"a\nb"`도 목록에 쓰인다(빈 글만 막힌다).

1. [Minor] 지적의 "과제 목록 쓰기 실패가 main의 기존 오류 처리와 종료 코드 2를 따르도록"이 다 닫히지 않았다. 브랜치 표의 `top_model_effort`가 홀로 선 서로게이트(`"\ud800"`)면 `_branch_row`와 `dumps_task_list`를 지나 `write_text`의 `UnicodeEncodeError`가 `_write`를 벗어나, 트레이스백과 종료 1로 끝나고 0바이트 목록 파일이 남는다(리뷰어가 `_write`를 불러 봤다). → 고친다. `(OSError, ShapeError)`는 닫힌 목록이고 이것은 그 반례라, 반례만 덧붙이지 않고 일반 조항으로 고쳤다(`code-review` 6단계 1). `_write`가 글을 다 짓고 UTF-8 바이트로 바꾼 뒤에야 열고(`write_bytes`), 값 오류 전체(`ValueError`. `ShapeError`와 `UnicodeEncodeError`가 그 하위 형식이다)를 2로 바꾼다. 과제 목록은 `write_task_list` 대신 `dumps_task_list`의 글을 받는다.
2. [Minor] 독스트링 "`top_model_effort`는 null이거나 빈 글이 아니어야 한다"가 같은 모듈의 "글이나 null 이 아니다"와 같은 짜임으로 읽혀 null도 막는 말로 읽힌다(명세: "`top_model_effort` 글 그대로이며 없으면 빈 값이다"). → 고친다. "null이거나 비지 않은 글이어야 한다".
3. [Nit] 과제 id가 꼴에 맞지 않으면 가르기의 낭비가 그대로 남는다. → 남긴다. 못 보는 것에 적었고, 실제 slug가 모두 맞는 꼴이다.
4. [Nit] 빈 글이 든 행은 후보가 아니어도 표 전체를 2로 막는다. 빈 글을 null로 읽는 길도 있었다. → 남긴다. 비용 칸의 선례처럼 브랜치 표는 수집 도구의 산출물이고, 수집 도구가 내지 않는 값은 입력이 틀린 것으로 본다.
5. [Nit] 못 보는 것의 "가른 결과를 잃는다"는 넓다. 후보 표는 남고 잃는 것은 숨은 시험 ID다. → 고친다. 표에는 숨은 시험의 수만 든다(`_hidden_cells`가 `len`만 적는다)고 적었다.
6. [Nit] 일지 "시험 파일의 앞 마흔여 개는 값만 넘기고"는 a5726119에서 git 절(698행) 앞의 시험 함수 39개, 수집된 사례 61개다. PR 코멘트에는 이 수가 없다. → 기록 문장은 그대로 두고 여기 바로잡는다.
7. [Nit] 종료 코드 문단이 2의 까닭에 "고른 값이 과제 목록의 꼴에 맞지 않음"을 들지 않는다. → 고친다.

### 반영

고친 것.
- 모듈: `_write`(바이트로 바꾼 뒤 열기, `ValueError` 받기), 과제 목록은 `dumps_task_list`로, import에서 `write_task_list`를 빼고 `dumps_task_list`를 넣었다. 독스트링의 종료 코드 문단(2의 까닭, 꼴 거부나 인코딩 실패면 그 자리를 건드리지 않는다, "null이거나 비지 않은 글"), 못 보는 것(slug로 지은 과제 id로 좁히고 괄호를 예시로, 후보 표는 남고 숨은 시험은 수만 든다).
- 시험(80 → 81): 대문자 slug 시험에 꼴 거부의 까닭(`task_id: 정해진 꼴의 문자열가 아니다: 'A-`)을 더했다. 새 시험 `test_과제_목록의_글을_UTF_8로_바꾸지_못하면_빈_목록_파일을_남기지_않고_2로_끝난다`는 고치기 전에 `UnicodeEncodeError: … surrogates not allowed`로 빨간 것을 봤다. 변이 36번의 `-k "쓰지_못하면"`에 걸리지 않게 이름에 그 조각을 넣지 않았다.
- 변이 표(38 → 40): 36번의 원문을 새 `except` 줄로, 바꿀 글을 `except ValueError`(`OSError`를 뺀다)로 맞췄다. 39번(바이트로 바꾸기 전에 연다), 40번(인코딩 실패를 2로 바꾸지 않는다)을 더하고 머리 주석의 범위에 넣었다. TOML 리터럴 문자열은 이스케이프를 풀지 않아 처음 적은 `"\\n"`을 `"\n"`으로 고쳤다.
- 프로브 README: 변이 문단 끝에 이 반영의 문장을 더했다.

남긴 것: 표준 3(판단), 명세 3·4(까닭은 위).

다시 돌린 명령: 시험 파일 81 passed(50초), 두 파일 ruff check·format·pyright 0 errors. 변이 원문 확인 40 모두 한 번씩. 36·39·40번을 골라 돌려 36번은 표지까지 기대대로였고, 39·40번은 표지를 비운 첫 실행의 출력에서 `AssertionError: 글을 바이트로 바꾸기 전에 파일을 열었다`와 `UnicodeEncodeError: 'utf-8' codec can't encode character`를 골라 다시 돌려 `변이 2 모두 기대대로`였다. 그 뒤 원문 확인 40 모두 한 번씩. 나머지 검증 명령은 커밋의 pre-commit으로 갈음한다.

곁일: `_write`를 고친 직후 `hook_edit_during_mutate`가 이 체크아웃에서 변이 도구(pid 23936)가 돈다고 알렸다. 이 세션은 변이 도구를 띄우지 않았고, 그때 도는 변이 도구는 `08-continue-and-caps` 워크트리의 `rerun_session_mutations.toml` 하나뿐이었으며(`Get-CimInstance Win32_Process`의 명령 줄), pid 23936·27160은 살아 있지 않았다. 이 워크트리의 git 디렉터리에 오늘 11:50(KST)의 표지 둘(`mutate-running-23936.json`, `mutate-running-27160.json`)이 남아 있었다. 앞 세션이 같은 변이 실행을 겹쳐 띄웠다가 끈 때의 것으로 본다("이어받은 세션: 셀프 리뷰"의 다시 돌린 명령). 훅은 그 pid를 잠깐 다른 프로세스가 받아 산 것으로 읽었다고 본다(그 훅 독스트링의 못 보는 것 "pid 의 재사용"). `git diff`에 변이가 없는 것을 본 뒤 두 표지를 지웠다.

PR 봇 둘째 회차에 밀 주장으로 넘길 새 문장(원문).
- 모듈 독스트링: "출력 자리에 쓰지 못했거나(고른 값이 과제 목록의 꼴에 맞지 않거나 글이 UTF-8로 바뀌지 않을 때도 든다)", "출력은 글을 다 짓고 바이트로 바꾼 뒤에야 열어, 꼴 거부나 인코딩 실패로 끝나면 그 자리를 건드리지 않는다.", "`top_model_effort`는 null이거나 비지 않은 글이어야 한다"
- 모듈 독스트링 못 보는 것: "병합 기록에서 온 slug로 지은 과제 id가 과제 목록의 꼴(`tools/rerun_files.py`의 `_TASK_ID`)에 맞는지는 미리 보지 않는다." 와 "후보 표는 남지만 표에는 숨은 시험의 수만 들어, 목록을 지으려면 가르기를 다시 돈다."
- `_write` 독스트링과 주석: "꼴 거부나 인코딩 실패면 그 자리를 건드리지 않는다", "ValueError: 꼴 거부(`ShapeError`)와 인코딩 실패"
- 시험 주석: "홀로 선 서로게이트는 JSON 으로 읽히고 과제 목록의 꼴도 지나지만 UTF-8 로 바뀌지 않는다"

## 인계: 커밋 뒤

셀프 리뷰 반영, 아래 회고와 "다음"을 990f79d9로 커밋했다. pre-commit은 모두 통과했다(ruff 둘, `checks`: check-instructions·check-type-escapes·pyright 둘·run-hooks·web-verify 288.9초·pytest 424.7초 등, 마크다운 표, 줄 구분 문자, 변이 표 원문, 커밋 메시지). 카나리아 명세와 헌법 판은 바뀐 파일이 없어 `Skipped`였다. 인용 대조 경고 여섯은 옛 독스트링·주석의 원문(지금은 고쳐져 저장소에 없다), CodeRabbit 원문, 리뷰어가 제안한 문구를 기록으로 옮긴 것이라 두었다. 손으로 치는 다섯은 이 결과로 갈음한다.

커밋 직후 `hook_handoff`가 컨텍스트 336,699 토큰으로 `커밋 뒤` 경계를 알렸다. 넘겨받은 경계(`셀프 리뷰 직전`)와 다르고, 요청 범위는 병합까지이며, `get_session`의 `self`에 `parentSessionId`가 없고, `인계 못함` 줄도 없어 인계한다. 아직 푸시하지 않았다. 이 세션의 지금 제목은 `feature/05-task-selection`이다.

남은 순서.
1. 이 절을 커밋한다(일지만).
2. 푸시하기 전에 `gh pr edit 371`로 PR 본문을 넓힌다(`next-session` 순서 1의 1). 이 커밋이 PR 본문에 없던 결정(`_write`가 글을 바이트로 바꾼 뒤에 열고 `ValueError`를 받는다, 빈 `top_model_effort` 거부)과 대기열 행(381의 2회차, 새 449·450)을 더했다.
3. 푸시하고 CodeRabbit 인라인 코멘트(id 4357714959)에 반영을 답한다. 반영 커밋은 990f79d9이고, 지적한 `ShapeError`에 더해 셀프 리뷰가 찾은 인코딩 실패까지 `ValueError`로 받게 넓혔다는 것을 적는다.
4. `@coderabbitai review`와 `tools/wait_ci.py 371`. 두 봇 모두 이번이 둘째 회차라 Critical·Major만 고치고 나머지는 지적마다 보류 이유를 PR 코멘트에 남긴다. CodeRabbit 첫 회차는 a5726119였고 시간당 한 번의 한도가 있다.
5. 병합(이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다)과 next-session.

인계 지시문.

> 다음 작업: .scratch/model-rerun/issues/05-task-selection.md. 병합 기록에서 후보 티켓을 찾아 까닭과 함께 표로 내고, 층과 씨앗으로 파일럿 셋과 본 측정 여덟을 고른다
> 다음 단계: PR 반영·병합
> 어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
> 시작 프롬프트: /implement .scratch/model-rerun/issues/05-task-selection.md
> 브랜치: feature/05-task-selection
> 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-38-task-selection.md의 "인계: 커밋 뒤"(남은 순서)
> 이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰 반영·회고·"다음"을 990f79d9로 커밋했고 아직 푸시하지 않았다. 커밋하지 않은 일지 절 "인계: 커밋 뒤"를 먼저 커밋한 뒤, PR #371 본문을 넓히고(새 결정과 대기열 381·449·450) 푸시, CodeRabbit 인라인 코멘트 4357714959에 답, 봇 둘째 회차(Critical·Major만), 병합을 한다. 회고는 마쳤다. docs/journal/2026-10-23-38-task-selection.md
> 확인할 선행 조건: 형제 07(PR #372, 워크트리 07-gates-and-official-cost)이 05 티켓·명세·프로브 README·tools/rerun_hidden.py와 그 시험·변이 표를 함께 고친다. 07이 먼저 병합되면 이 PR에 글자 충돌이 날 수 있다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지. 사용자는 측정 도구 짓기까지 이어 가라고 했다(2026-10-22)

제목을 `feature/05-task-selection (인계함)`으로 바꿨다. 멈출 백그라운드 작업은 없었다(커밋과 서브에이전트 둘이 모두 끝났다). 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-23T09:33Z

## 이어받은 세션: 푸시와 봇 둘째 회차

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. (… 위 "인계: 커밋 뒤"의 지시문과 같다 …) 인자: .scratch/model-rerun/issues/05-task-selection.md

`git worktree list`에서 브랜치가 `.claude/worktrees/05-task-selection`(990f79d9)에 있어 `EnterWorktree(path)`로 들어갔다. 세션 제목을 `feature/05-task-selection`으로 바꿨다. 커밋하지 않은 변경은 넘겨받은 대로 이 일지 하나였다. origin/main은 893e0fe8 그대로였고, 형제 07(PR #372)은 d5db123e로 아직 열려 있다. `tools/sibling_overlap.py`는 번호 겹침 없음(0)이었다.

- 넘겨받은 일지 절을 82fefb70로 커밋했다(pre-commit 모두 통과, ruff 둘은 `.py`가 없어 `Skipped`).
- 푸시 전에 `gh pr edit 371`로 PR 본문을 넓혔다. 변경사항 문단, "왜 이렇게 했나"의 두 결정(`_write`가 글을 바이트로 바꾼 뒤에 연다, 빈 `top_model_effort` 거부), "남긴 위험"의 slug 과제 id, "변경된 영역"의 대기열 381·449·450, 체크리스트와 확인 방법의 수(셀프 리뷰 세 번, 시험 81, 변이 40).
- 푸시하고 CodeRabbit 인라인 코멘트 4357714959에 반영을 답했다(discussion_r4358232460). `@coderabbitai review`를 남기고 `tools/wait_ci.py 371`을 백그라운드로 띄웠다.

### 봇 둘째 회차

- CodeRabbit(82fefb70): 고칠 지적 없음. 인라인 답에 반영을 확인했다(discussion_r4358237887).
- claude-review(82fefb70): Critical·Major 없음, Minor 둘과 Nit 하나. 둘째 회차라 셋 모두 보류하고 이유를 PR 코멘트에 남겼다(issuecomment-6362462104). 셋 모두 동작을 바꾸지 않는 구조 정리다. `_run`의 출력 자리 검사를 함수로 빼기(순서는 시험 둘이 고정한다), 모듈 나누기(첫 회차 보류와 같은 판단. 11은 이 모듈을 돌릴 뿐 코드를 더하지 않아 뒤로 넘기는 일도 아니다), `Pick`이 `BranchRow`를 직접 들기(`Checked`의 형식과 `picks_of`를 함께 바꾸는 정리).
- 검사: `e2e`가 취소되고 그 결과를 모으는 `verify`가 빨갰다. 코드와 무관하다. e2e 잡의 `playwright install-deps chromium`(apt)이 Ubuntu 미러에서 24.7 MB를 14분 24초(28.6 kB/s)에 받아 잡의 15분 제한에 걸렸다. 같은 스텝의 지연은 세 번째 기록이고(2026-10-01 4분 32초, 일지 2026-10-23-03의 web 잡 9.4분), 잡을 실패시킨 것은 처음이다. 이 티켓의 회고를 마친 뒤의 사건이라 대기열에 올리지 않고 "다음"에 다음 회고가 판정할 일로 적었다. `gh run rerun 39934299752 --failed`로 실패한 잡만 다시 돌렸다. 다시 돈 e2e와 verify는 통과했다.

### 봇 셋째 회차와 main 합치기

- 위 기록을 ec4cdc40로 커밋해 푸시했다. pre-commit은 600초를 넘겨 백그라운드로 넘어간 뒤 종료 0으로 끝났다. 그 커밋 직후 `hook_handoff`가 컨텍스트 204,520 토큰으로 `커밋 뒤` 경계를 알렸다. 이 세션의 지시문이 `인계: 커밋 뒤`로 시작해(같은 경계) 넘기지 않았다.
- 검사 여덟 모두 통과. CodeRabbit은 `Review rate limited`라 이 푸시는 CodeRabbit의 회차로 세지 않는다.
- claude-review 셋째 회차(ec4cdc40): Critical·Major 없음, Minor 셋과 Nit 하나. 넷 모두 보류하고 이유를 PR 코멘트에 남겼다(issuecomment-6362933285). 새 지적은 `--table`과 `--out`에 같은 경로를 주면 후보 표가 덮어써진다는 Minor 하나다. 두 인자는 필수이고 형식이 달라(마크다운, JSON) 사람이 잘못 준 경우로 보고, 뒤로 넘기는 일로도 적지 않는다. 나머지는 앞 회차와 같은 지적(모듈 나누기, `_run`의 검사 빼기)과 ruff `I`가 지나간 import 자리다.
- 병합 확인에서 PR이 `BEHIND`였다. origin/main에 #373(web-widget 명세)이 들어왔다. 함께 고친 파일은 `.scratch/retro-queue.md`이고, main은 행 319만 고쳐 이 브랜치의 381·449·450과 겹치지 않았다. 충돌 없이 54a4e9fe로 합쳤다. 합치기 커밋에서는 커밋 메시지 검사만 돌았다. main이 고친 319는 "origin/main을 합친 뒤 저장소 전체 린트를 돌리지 않고 푸시해 main의 새 ruff 규칙을 CI에서야 잡았다"는 행이라, 푸시 전에 `uv run ruff check .`와 `uv run ruff format --check .`를 쳤다.
- 합친 뒤 `tools/sibling_overlap.py`가 종료 1이었다. 이 일지(옛 번호 38)가 main의 최신 일지 2026-10-23-40보다 이름순으로 앞서 다음 세션이 이 일지의 "다음"을 지나친다는 것이다. `--move`로 옮겼고, 그사이 42도 형제가 가져가 43이 됐다. 도구가 파일 이름과 머리 줄, 인용 넷(프로브 README, 대기열, `tools/rerun_hidden.py`와 그 시험의 주석)을 고쳤다. 인용 블록(`>`)의 옛 경로는 지시문 원문이라 도구가 일부러 두었다(그 독스트링). PR 본문의 옛 번호도 도구가 지은 본문으로 고쳤다.

## 회고

티켓 05를 닫는 세션이라 이 일지 전체(이 티켓의 세션 다섯)를 원천으로 돌렸다. 후보 여덟, 승인 셋(새 행 둘, 회차 하나), 기각 다섯, 넘김 0이다. 이 세션에서 반영한 것은 없다. 만료할 행은 없었다(`tools/queue_open_rows.py`를 작업 트리와 `--ref origin/main`으로 돌려 둘 다 "(없음)").

1. **승인, 회차.** 같은 체크아웃에서 같은 변이 표의 실행을 두 번 띄워 두 프로세스가 같은 모듈에 변이를 넣었다("이어받은 세션: 셀프 리뷰"의 다시 돌린 명령). 둘 다 끄고 원문 확인 뒤 다시 돌려 손상은 없었고, 겹친 실행의 결과를 버렸다. 열린 381이 같은 처방(같은 git 디렉터리에 산 표지가 있으면 시작하지 않는다)을 들어 그 행의 2회차로 더했다. 구현 때 실리는 지침이 아니라 열린 행이 처방한 사건이라 회차로 센다.
2. **승인, 새 행 449(1회차).** 1에서 끈 실행이 남긴 표지 둘을, 그 pid를 잠깐 받은 다른 프로세스 때문에 `hook_edit_during_mutate`가 산 것으로 읽어 이 세션에 거짓 경고를 냈다("곁일"). 사건: 프로세스 목록, `git diff`, 표지를 보느라 도구 호출 아홉 번. 층: 도구와 훅(표지에 프로세스 시작 시각을 적고 pid와 함께 본다). 되돌림: PR 하나. 더하는 것이라 문턱 전이어서 대기열에 두었고, 381과 서로 가리킨다(381의 처방이 들면 같은 표지가 측정의 시작도 막는다).
3. **승인, 새 행 450(1회차).** 후보 표를 짓는 2시간 52분 동안 진행 줄이 몇 번째 후보인지 적지 않아 사용자가 물었고("실제 후보 표"의 인용), 세션은 가를 후보의 수를 스크래치 스크립트로 셌다. 층: 도구 출력(`_sorter`가 `k/N`과 지난 시간을 적는다). 티켓 11의 `pilot`·`main`이 같은 가르기를 저마다 다시 돌아 곧 다시 겪는다. 더하는 것이라 대기열에 두었다.
4. **기각.** Write 도구가 `U+2028`·`U+2029`·`U+FEFF` 이스케이프를 날것 문자로 저장했다("구현"의 고친 것). 닫힌 22·52·160이 들인 검사(`tools/check_line_separators.py`와 그 훅)가 맡는 꼴이고 그 자리에서 고쳤다. 이 회고 절을 쓴 Edit에서도 세 이스케이프가 날것으로 저장됐고, `hook_line_separators`가 그 편집 직후에 알려 `chr()`로 문자를 지은 스크래치 스크립트로 `U+2028` 꼴로 바꿨다.
5. **기각.** NUL이 든 문자열이 `git grep`의 인자로 넘어가 후보 하나를 통째로 잃던 결함("실제 후보 표"). 환경이 아니라 이 티켓의 도구 결함이고 이 PR이 고쳤다.
6. **기각.** 봇 첫 회차 반영이 예외를 닫힌 목록(`OSError, ShapeError`)으로 좁게 고쳐, 인코딩 실패가 남은 것을 이 세션의 셀프 리뷰 명세 축이 잡았다. 리뷰가 제 몫을 한 사건이라 셈에서 뺀다.
7. **기각.** 이 세션이 변이 표의 TOML 리터럴 문자열에 `"\\n"`을 적었다. 돌리기 전에 스스로 보고 고쳐 비용이 없었다.
8. **기각.** 앞 세션이 일지에 "시험 파일의 앞 마흔여 개"로 적은 수가 39개였다. 260의 처방대로 다음 층(이 세션의 셀프 리뷰)이 잡았다.

## 다음

- 05가 병합돼도 새로 풀리는 티켓은 없다. 11(파일럿과 사전 등록)은 10을 기다리고, 10은 07·09를 기다린다. 07(PR #372)과 08은 형제 세션이 돈다.
- 실제 후보 표의 결론(남은 후보 8개로 문턱 12개에 못 미친다)과 사람에게 물을 길은 11 티켓의 "05에서 넘어온 메모"에 있다. 11이 `pilot`을 돌기 전에 대기열 450을 보면 그 가르기의 진행을 알 수 있다.
- 형제 07이 05 티켓, 명세, 프로브 README, `tools/rerun_hidden.py`와 그 시험·변이 표를 함께 고친다. 05가 먼저 병합되면 07이 main을 합칠 때 그 파일들에서 글자 충돌이 날 수 있다.
- CI의 `playwright install-deps chromium` 지연이 세 번째로 기록되었고 처음으로 잡을 시간 초과로 실패시켰다(위 "봇 둘째 회차"의 검사 줄). 이 티켓의 회고 뒤에 났으므로, 다음 회고가 대기열 후보로 판정한다.
