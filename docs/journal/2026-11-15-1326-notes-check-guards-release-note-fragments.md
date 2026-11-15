# 노트 검사가 노트 조각의 빠뜨림과 모양을 병합 전에 막는다 (release-image 티켓 05)

브랜치 `feature/05-notes-check-guards-release-note-fragments`.

## 사용자 프롬프트 원문

이 세션의 첫 메시지는 앞 묶음이 낸 지시문이었고, 사용자의 다른 말은 없었다.

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/release-image/issues/05-notes-check-guards-release-note-fragments.md
>
> 다음 작업: 노트 검사가 노트 조각의 빠뜨림과 모양을 병합 전에 막는다
> 다음 단계: 구현
> 모델: Sonnet 5.5 / high
> 이번 요청 범위: PR과 병합까지

## 한 것

- `tools/check_notes.py`를 지었다. 인자 없음(커밋 검사. 스테이지한 변경을 HEAD에 견준다)과 `--ci`(PR의 변경 전체), `--title-only`(PR 제목만) 세 모드이고, 판정은 (가) PR 제목의 꼴과 느낌표·`upgrade/` 조각의 짝, (나) 기능 계획의 `**끝:**` 줄이나 `features/<slug>.md`를 더할 때 그 기능이 제품 변경을 담았는지에 따른 기능 단락의 있고 없음, (다) 조각의 모양(비어 있지 않음, `#` 줄 없음, 기능 단락은 빈 줄 없는 400자 이하, 소개 글 이름 `X.Y.Z.md`)이다. 독스트링에 "못 보는 것"을 적었고 시험이 고정한다.
- `tests/tools/test_check_notes.py`는 임시 git 저장소에서 도는 시험이다. 순수 함수 시험과 프로세스 시험이 섞여 있고, 구현과 함께 써서 빨강을 본 적이 없는 단언은 `tools/mutate.py`로 변이를 넣어 빨강을 봤다(아래 "확인").
- 등록: `tools/run_checks.py`의 `CHECKS`에 `check-notes`를 더했다(pre-commit). `.github/workflows/ci.yml`의 `ticket` 잡에 `--ci` 스텝을 더했고(앞 스텝이 빨강이어도 돈다), `.github/workflows/pr-title.yml`을 새로 두었다(`pull_request`의 `edited`에만, 머리가 main·dev면 건너뜀, 필수 검사 아님). 제목은 모두 환경 변수로 넘긴다. zizmor는 지적 없이 지났다.
- 문서: `docs/constitution/operations.md`에 "릴리스 노트 조각" 절(조각 셋, 느낌표 기준, 보는 자리)과 가드레일 문단의 한 문장, 문서 위치 절의 기록 목록에 "판으로 나간 노트 조각"을 더했다. `.github/PULL_REQUEST_TEMPLATE.md`에 "올릴 때 운영자가 손댈 것" 칸, `docs/agents/issue-tracker.md`의 "끝 줄을 적는 때"에 기능 단락, `.claude/skills/implement/SKILL.md`의 티켓 맞추기 문단에 기능 단락과 느낌표·`upgrade/` 지시, `CLAUDE.md`에 게이트 수(열일곱에서 열여덟)와 노트 검사 문장을 더했다. `**끝:**`을 하네스에서 grep했고 `grill-with-docs`와 `next-session merge.md`는 그 줄을 계기로 말할 뿐이라 고치지 않았다.
- 헌법 판을 3.0.99에서 3.0.100으로 올렸다. 까닭: `operations.md`에 절 하나와 규약 문장이 더해졌다(앞선 판들이 같은 종류의 규약 문장 추가를 patch로 올렸고 그 관례를 따랐다). `tools/sibling_overlap.py`가 번호 겹침 없음을 확인했다(형제가 쓴 가장 높은 판은 3.0.99).

## 결정

- 커밋 검사는 "스테이지한 변경 대 HEAD"를 본다(명세의 "스테이지된 변경"). 한 PR 안에서 제품 변경과 끝 줄이 다른 커밋에 나뉘면 커밋 검사는 놓치고 CI가 잡는다(시험이 둘 다 고정한다).
- 병합을 마무리하는 커밋은 커밋 검사가 판정하지 않고 알린다. 그 안에 든 것은 CI가 PR 전체로 본다.
- (나)의 "담았다"는 티켓 파일과 제품 경로를 함께 고친 비병합 커밋(`--no-merges --full-history`로 읽는다)이 하나라도 있는지로 센다. 병합 커밋의 합친 변경은 한 커밋으로 세지 않는다.

## 확인

- 시험: `tests/tools/test_check_notes.py`는 첫 실행에서 97건이 통과했다(pytest 출력). 변이 7번의 틈을 막으려 둘을 더했고, 더한 둘은 `-k 병합`으로 돌려 통과했다(3 passed). 셀프 리뷰 반영 뒤 파일 전체를 다시 돌려 106건이 통과했다(pytest 출력 `106 passed`).
- 변이(`tools/mutate.py`, 변이 열 열 개): 기능 단락 상한 401, 경계 이상, 느낌표 읽기 삭제, 고친 upgrade 파일을 새 파일로 세기, (나)의 빠뜨림 알림 삭제, (나)의 제품 변경 없는 기능 단락 막기 삭제, 병합 커밋 이력 세기, 머리가 main·dev인 PR 건너뛰기 삭제, 병합 마무리 커밋 건너뛰기 삭제, 조각 머리줄 검사 삭제. 아홉은 처음부터 기대대로 빨강이었다. 7번(`--no-merges`를 `--first-parent`로)만 초록으로 어긋났다. 병합 커밋이 합친 변경으로 이력에 잡혀서였다. 병합 커밋의 합친 변경을 한 커밋으로 세지 않는 시험과, base를 병합해 들여온 제품 변경도 세는 시험을 더하자 7번이 빨강이 됐다. 변이 표는 세션 스크래치패드에서만 돌렸고 저장소에 커밋하지 않았다. 커밋한 표에는 빨강 변이마다 `expect_output` 표지가 있어야 하는데 이번에는 달지 않았다. 변이 결과는 이 절이 원천이고 도구의 출력을 옮긴 것이다.
- 고친 `implement` 스킬을 새 세션(`claude -p`, 카나리아)에서 불렀다. `implement_ticket_status.toml`에 6번(기능 단락)과 7번(느낌표와 `upgrade/` 조각) 물음을 더해 통과 4, "없음" 섞임 0이었다(claude 2.1.322, 대조군 `--control-commit caaa062b`은 일곱 물음 모두 "없음"). 같은 원천을 든 나머지 셋(`implement_full_checks_runner`, `implement_uv_sync_timeout`, `dev_base_implement`)은 건드린 문단 밖의 문구를 묻는 명세라 `--preflight`로 갈음했고 모두 통과했다(대조군 커밋은 각 명세 머리 주석의 `9220d4a6`, `5f72cdbb`, 주 체크아웃 순서다).
- `pyright`(새 파일 셋), `ruff check`, `ruff format --check`, `check_instructions`, `check_type_escapes`, `zizmor`는 지적 없이 끝났다.

## 셀프 리뷰 (`/code-review`, 기준 `origin/dev`, 표준 축 sonnet·high와 명세 축)

- 고친 것: (가)가 `upgrade/` 아래의 모든 더한 경로(하위 폴더와 `.md`가 아닌 파일 포함)를 새 할 일 조각으로 센다(`tools/release.py`의 `_upgrade_entry`와 같은 기준). 기능 단락의 앞쪽 빈 줄도 빈 줄 규칙에 걸린다. `implement` 스킬과 `operations.md`, `CLAUDE.md` 지도 줄, `tools/release.py` 독스트링의 문구를 서로 맞췄다(근거 없던 "저장소 상태 시험" 언급은 grep으로 확인하고 뺐다). 이 반영을 고정하는 시험 일곱을 더했다(하위 폴더·비 `.md` 두 갈래, 이름 바꾸기가 새로 더한 것으로 세어져 막힘, 도구·시험 경로만 고친 `feat!`, 단락 내용은 보지 않음, 앞쪽 빈 줄, 얕은 체크아웃의 종료 2).
- 남긴 것: git 보조 함수가 도구마다 복사된 것(도구는 서로 import하지 않는 단독 스크립트라는 결정의 비용), `Scene.after`의 표지값과 `Wording` 중간 전달자(Minor), `pr-title.yml`의 `edited` 필터(명세 문구대로), 두 워크플로 스텝의 `GITHUB_EVENT_NAME` 중복(도구가 읽으므로 그대로), 슬라이스 줄에 대한 스킬과 도구의 표현 차이(무해).
- 다시 돌린 것: 두 파일 `pyright` 0건, `ruff check`·`ruff format`, `check_instructions`, `check_type_escapes`, 카나리아 `--preflight`(대조군 `caaa062b`)와 `--shape`. 스킬 문구는 카나리아 실행 뒤 다시 고쳤으나 카나리아 문구가 묻는 두 줄은 그대로라 사전 점검으로 갈음했다. 전체 러너는 커밋의 pre-commit 결과로 갈음한다.

## PR 직전 리뷰 (`coderabbit-review`, CodeRabbit CLI 0.7.5, 기준 `origin/dev`)

Critical·Major 없음. 겨냥한 주장 넷(`upgrade/` 아래 경로 세기가 `_upgrade_entry`와 같은 기준, 앞쪽 빈 줄 규칙, 이름 바꾸기를 삭제와 추가로 세기, 워크플로의 제목 전달과 `pr-title.yml`의 트리거·권한)은 코드를 읽고 임시 입력으로 재 보아 맞았다. 지적은 Minor 여섯이다.

- 고친 것: 조각이 아닌 파일까지 `git show`로 읽던 것을 읽기 전에 거른다(`_fragment_folder`). `upgrade/` 아래에 하위 폴더나 `.md`가 아닌 파일을 새로 더하면 (가)는 세지만 (다)가 모양을 보지 않아 빈 항목이 노트에 실릴 수 있었으므로, 그런 파일을 "할 일 조각이 아니다"로 막는다(`_stray_upgrade`). 이 구멍은 셀프 리뷰에서 (가)를 판 내기와 맞춘 뒤에 생긴 것이고, 시험(`test_할_일_폴더_아래의_…`)이 두 갈래로 고정한다.
- 남긴 것: `ci.yml`의 `ticket` 잡이 제목을 고쳐도 다시 돌지 않는 한계(`operations.md`에 적었고 푸시 한 번으로 풀린다), `_delivered`가 slug마다 이력을 다시 읽는 비용(지금 크기에서 문제가 아니다), `#` 머리 검사가 앞 공백과 BOM을 못 보는 것(독스트링과 맞는다), 머리 브랜치 이름이 `main`·`dev`면 포크 PR도 건너뛰는 것(이 저장소는 외부 기여를 받지 않고 `check_ticket`의 기존 판정과 같다).
- 다시 돌린 것: 고친 파일 `pyright`·`ruff`, 시험 파일 전체. 전체 러너는 두 번째 커밋의 pre-commit 결과로 갈음한다.

## PR 봇 첫 회차 (PR #576, 머리 `de1b8ea`)

CodeRabbit은 무료 리뷰 한도에 걸려 리뷰가 없었다(`Review rate limited`, 요청 코멘트에도 같은 답). 검사 줄(`e2e`·`e2e-portal`·`e2e-widget`·`python`·`ticket`·`verify`·`visual`·`web`)은 모두 SUCCESS, `llm`은 SKIPPED였다. claude-review는 코멘트 하나에 Minor 둘과 Nit 하나를 냈다.

- 고친 것(Minor): `judge_pr`의 키워드 전용 불리언 `title_only`는 `CODING_STANDARDS.md`의 불리언 플래그 항목이 함수가 두 가지 일을 한다는 신호로 보아 쪼개라고 정한 대상이었다. `judge_title`과 `judge_pr`로 쪼개고 공통부를 `_pr_input`으로 모았으며, 입구는 `Mode` 문자열 유니온으로 가른다.
- 남긴 것: `Wording`이 필드 하나뿐인 데이터클래스라는 Minor(셀프 리뷰에서 이미 판단해 둔 것과 같다. 두 상수의 이름과 필드가 커밋 검사와 PR 검사의 막는 말을 한곳에서 읽히게 하고, 문자열 두 개를 바로 넘기면 `blocked_text`의 인자가 의미 없는 문자열이 된다. 쪼개는 이득이 작아 보류), `title_problems`를 작은 함수로 나누자는 Nit(읽는 순서가 어렵다는 취향 지적이라 보류).
- 뒤로 넘긴 일: 없음. 위 둘은 다른 작업으로 넘기는 일이 아니라 이 도구 안의 취향 판단이다.

## 인계 (셀프 리뷰 직전)

컨텍스트가 인계 문턱을 넘은 채 `셀프 리뷰 직전` 경계에 와서 새 세션에 넘긴다(`next-session handoff.md`). 이 세션의 제목은 `feature/05-notes-check-guards-release-note-fragments`였고 인계하며 `feature/05-notes-check-guards-release-note-fragments (인계함)`으로 바꾼다. 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없었다).

남은 일: 셀프 리뷰(`/code-review`)와 반영, 커밋(pre-commit이 전체 러너를 돌린다. 이 세션은 아직 `uv run python tools/run_checks.py`를 돌리지 않았다), `origin/dev`를 합치기, PR(`dev`로), 봇 회차, 병합(`merge.md`의 "워크트리에서 병합할 때"). 티켓 체크박스는 모두 채웠고 `Status`는 `done`이다(마지막 "검증 명령이 모두 초록이다"는 커밋의 pre-commit이 확인하기 전까지 닫힌 것이 아니다. 초록이 아니면 되돌린다). `.scratch/plan.md`는 `tools/plan_table.py`를 돌렸고 바뀌지 않았다.
open-session을 부른다 2026-11-15T04:52Z
인계 못함 셀프 리뷰 직전: open_session.ps1 의 실행을 자동 모드 판정기가 거부했다(PowerShell 도구, 사유 없음). 제목은 되돌렸고 이 세션이 셀프 리뷰부터 잇는다.
