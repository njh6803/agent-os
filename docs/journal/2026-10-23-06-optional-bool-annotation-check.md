# 2026-10-23 (06) 매개변수와 반환의 `bool | None` 주석을 잡는 검사 (harness 004)

## 구현

> 사용자: (next-session 지시문을 첫 메시지로 받았다) "대기열 423을 티켓 .scratch/harness/issues/004-optional-bool-annotation-check.md로 쓰고 한다 / 다음 작업: 받는 세션이 쓸 .scratch/harness/issues/004-optional-bool-annotation-check.md. 매개변수와 반환의 주석이 `bool | None`인 자리(세 값으로 출력을 고르는 꼴)를 AST로 잡는 검사를 더한다 / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 6 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 브랜치: chore/004-optional-bool-annotation-check / 모델: Opus 5.5 / medium. 레벨 스윕의 갈래 / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다. 묶음의 첫 세션이 아니라 `tidy-checkouts`는 돌지 않았다.
- `EnterWorktree(004-optional-bool-annotation-check)` 뒤 브랜치 이름을 `chore/004-optional-bool-annotation-check`로 바꿨다. 기준은 origin/main `975bf04c`(#355).
- 일지를 2026-10-23-05로 만들었다가 계기 훅이 형제와 겹친다고 알려 `sibling_overlap.py --move`로 06으로 옮겼다. 티켓 004는 겹치지 않았다.

### 한 것

- 티켓 `.scratch/harness/issues/004-optional-bool-annotation-check.md`(in-progress로 시작).
- 시험 먼저: `tests/tools/test_check_instructions.py`에 열 개(매개변수화로 사례 열여섯)를 더해 `ImportError`로 빨간 것을 본 뒤 구현했다.
- `tools/check_instructions.py`: `optional_bool_annotations`(와 `optional_bool_lines`, `optional_bool_sources`, `OPTIONAL_BOOL_ROOTS`)를 더하고 `main`이 부른다. 합을 펴서 갈래가 `bool`과 None 둘뿐인지 본다(`|`, `Optional[...]`, `Union[...]`, 문자열 주해). 자리는 함수의 매개변수 다섯 갈래와 반환이다. 독스트링에 잡는 것, 잘못 막는 것, 못 보는 것을 적고 못 보는 것은 지나간다는 시험 하나로 고정했다. 모듈 독스트링 목록에 한 줄을 더했다.
- 들이자 저장소 상태 시험이 `tools/canary.py`의 `_registered`(목록을 읽지 못하면 None을 내는 `bool | None` 반환)를 잡았다. 대기열 행은 범위 안에 0곳이라 적었는데, 그 수는 매개변수만 센 것으로 어림한다. 열거 `_Registration`(`LISTED`·`GONE`·`UNKNOWN`)으로 고치고 부르는 곳(`is False`)을 `is _Registration.GONE`으로 바꿨다. 그 줄을 원문으로 든 `.scratch/harness/probes/canary_mutations.toml`의 변이를 새 원문으로 고쳤다.
- probes에서는 셋이 잡혔다(`worktree_skill_listing.py`의 `drive` 반환, `handoff_cost.py`의 `_same` 반환, `jwt_verify/cases.py`의 `mark`의 `accepted`). 판정 함수를 커밋하지 않은 스크래치 스크립트로 돌려 손으로 셌다. 행의 넷과 다르고 어느 하나가 빠졌는지는 보지 않았다.
- 변이: `.scratch/harness/probes/instruction_check_mutations.toml`에 아홉(Optional·Union을 펴지 않음, 문자열 주해를 읽지 않음, 키워드 전용·반환을 보지 않음, 갈래 수를 보지 않음, 범위에서 tests를 뺌, probes까지 훑음, main에서 뺌)을 더했다. 표지는 그 시험의 FAILED 줄이다. `PYTHONUTF8=1 uv run python tools/mutate.py … --since origin/main`이 두 표 모두 기대대로(지침 검사 9, canary 1).
- `CODING_STANDARDS.md`의 불리언 플래그 줄에 이 검사가 막는 범위를 적었다. 대기열 423을 닫았다.

### 결정

- 새 `tools/check_*.py`를 두지 않고 지침 검사에 더했다. 같은 파일에 코드 모양을 AST로 보는 선례(`calls_without_timeout`)가 있고, 새 도구면 pre-commit·CI·러너 등록과 `CLAUDE.md`의 게이트 수가 함께 바뀐다.
- 훑는 범위는 pyright의 `include`와 같게 두고 시험이 `check_type_escapes.scanned_roots()`와 맞댄다. 지침 검사는 스크립트로 돌아 다른 도구를 import하지 않으므로 상수로 적었다.
- 뺄 표지는 두지 않았다. "모른다"를 None으로 내는 반환도 세 갈래이고, 들인 때 잡힌 하나가 바로 그 꼴이라 열거로 고쳤다.

### 인계 (셀프 리뷰 직전)

`code-review`를 부른 직후 인계 계기가 왔다(세션 컨텍스트 201,858 토큰, 경계 `셀프 리뷰 직전`). 인계하지 않는 때 다섯에 들지 않았다(곁 세션 아님: `get_session`의 `self`에 `parentSessionId`가 없다). 셀프 리뷰는 밟지 않았다. 이 세션의 지금 제목은 `chore/004-optional-bool-annotation-check`이고 넘기기 전에 `(인계함)`을 붙인다. 커밋은 아직 없다. 전체 검사 러너(`tools/run_checks.py`)는 아직 돌리지 않았다. 돌린 것은 `test_check_instructions.py`·`test_canary.py`, 변이 두 표, ruff 둘이다. 티켓의 수용 기준 체크박스는 아직 채우지 않았다.

지시문:

```
다음 작업: .scratch/harness/issues/004-optional-bool-annotation-check.md. 매개변수와 반환의 주석이 `bool | None`인 자리를 AST로 잡는 검사를 더한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 423을 티켓 .scratch/harness/issues/004-optional-bool-annotation-check.md로 쓰고 한다
브랜치: chore/004-optional-bool-annotation-check
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-23-06-optional-bool-annotation-check.md의 "구현" 절
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review origin/main)부터 한다. 그 뒤 전체 검사 러너, 티켓 체크박스와 done, 커밋, PR. 일지 docs/journal/2026-10-23-06-optional-bool-annotation-check.md
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

- 제목을 `chore/004-optional-bool-annotation-check (인계함)`으로 바꿨다. 멈출 백그라운드 작업은 없었다. `git worktree unlock`을 쳤다.
- open-session을 부른다 2026-10-22T17:43:48Z

### 이어받음

- 새 세션이 제목을 브랜치 이름으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. origin/main은 그대로 `975bf04c`였다.
- 셀프 리뷰 `/code-review origin/main`(base `975bf04c`, 파일 일곱, 커밋 0, 미추적 둘)을 두 축으로 돌렸다.
- 명세 축(Minor 넷, 범위 밖 없음): 못 보는 것 가운데 이름이 typing·내장의 것인지와 데이터클래스 칸에 시험이 없다(이름을 가린 `Optional`은 지나가지 않고 잡히니 잘못 막는 쪽이다). 맨 위인데 지나가는 반례 넷(`Optional[Optional[bool]]`, `Optional[bool | None]`, `Union[bool, Optional[bool]]`, `Optional['bool']`)이 목록에 없다. "앞의 둘"이 가리키는 것이 어긋난다. 일지의 시험 수가 틀렸다(더한 시험 함수 아홉, 사례 열다섯). 행의 "넷"과 probes 셋의 차이는 기준 커밋의 데이터클래스 칸 `enter_worktree_loading.py`의 `worktree_error`일 것이라 어림했다.
- 표준 축(문서화된 표준 위반 셋, 판단 항목 다섯): 프로브 README의 `instruction_check_mutations.toml` 행이 새 아홉과 그 결과를 적지 않았다(`docs/agents/issue-tracker.md` 프로브와 근거). "앞의 둘"이 어긋난다. 못 보는 것이 불완전하고 시험이 없는 항목이 있다(`.claude/rules/tools.md` 못 보는 것): 갈래 안의 문자열, 합 안의 합, `builtins.bool`, `NoneType`, 앞 공백의 문자열 주해. 판단 항목은 자리 문자열을 `endswith("반환")`으로 다시 읽는 결합, `_member_kind`와 `_registered`의 이름, 어댑터의 `X | None` 표준과의 긴장, 범위를 네 곳에 적은 것, `>= 200`이다.
- 고친 것: 합을 끝까지 펴고 갈래 안의 문자열과 앞뒤 공백까지 읽게 했다(`_parsed`, 재귀 `_union_members`). 시험 먼저: 펴서 잡는 사례 여섯이 빨강인 것을 본 뒤 고쳤다. 잘못 막는 것(typing이 아닌 `Optional`)과 못 보는 것 일곱(모듈 변수, 클래스 칸, 별칭, 감싼 주석, `Annotated`, `builtins.bool`, `NoneType`)을 시험으로 고정하고 독스트링을 그대로 고쳤다("앞의 둘"도). `_registered`를 `_registration`으로 바꾸고 독스트링·대기열 닫힘·canary 변이 원문을 따라 고쳤다. 변이 표의 문자열 주해 원문을 새 코드로 고치고 새 갈래 셋의 변이를 더했으며(표는 마흔), 프로브 README 행에 열둘과 결과를 적었다. 일지 위 "한 것"의 시험 수는 그때의 기록으로 두되 실제로는 시험 함수 아홉, 사례 열다섯이었다.
- 남긴 것: `endswith("반환")` 결합은 한 파일 안의 메시지 조사 하나라 판단 항목으로 둔다. `_member_kind`의 `"None"` 문자열도 같다. 어댑터의 `X | None` 표준과의 긴장은 `bool | None` 반환이 "없다"가 아니라 세 번째 답이라는 독스트링의 잘못 막는 것 항목이 답한다. 범위를 네 곳에 적은 것은 원천이 상수 하나이고 나머지는 설명이다. `>= 200`은 같은 파일의 `tool_sources() >= 50` 선례를 따른다.
- 다시 돌린 것: 변이 `instruction_check_mutations.toml --since origin/main` 열둘 모두 기대대로(표는 마흔), `canary_mutations.toml --since origin/main` 하나 기대대로. ruff 둘 초록. 전체 검사 러너는 pytest만 빨강이었다(`test_이_저장소의_표는_전부_GFM_에서_깨지지_않는다`, 프로브 README 행에 이스케이프하지 않은 `bool | None`의 `|`가 칸을 하나 더 냈다). `\|`로 고치고 그 시험을 다시 돌려 초록이었다. 나머지 아홉 게이트(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright 둘, run-hooks, web-verify)는 초록이었다. 커밋의 pre-commit이 다섯을 다시 돈다.
- PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장): `optional_bool_annotations` 독스트링의 "합 안의 합(`Optional[bool | None]`, `Union[bool, Optional[bool]]`), 그리고 주석 전체나 갈래 하나를 문자열로 쓴 주해(`'bool | None'`, `Optional['bool']`. 앞뒤 공백은 벗긴다)", "이름 `Optional`·`Union` 이 typing 의 것인지 보지 않아, 같은 이름의 다른 것으로 쓴 주석도 잡는다", "갈래는 이름 `bool` 과 상수 None 으로만 알아봐서 `builtins.bool | None` 과 `bool | NoneType` 도 지나간다".
