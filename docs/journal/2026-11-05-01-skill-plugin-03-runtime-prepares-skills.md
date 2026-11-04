# 2026-11-05 (01) skill-plugin 03: 런타임이 실행마다 고른 스킬을 준비해 컨텍스트로 넘긴다 (구현 세션)

세션 제목은 `feature/03-runtime-prepares-skills-per-run`이다. 티켓은 `.scratch/skill-plugin/issues/03-runtime-prepares-skills-per-run.md`이다.

## 사용자 프롬프트

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다.
> 인자: .scratch/skill-plugin/issues/03-runtime-prepares-skills-per-run.md
> 다음 단계: 구현 / 어디서: 새 세션 / 브랜치: feature/03-runtime-prepares-skills-per-run / 모델: Sonnet 5.5 / high / 읽을 것: 일지 2026-11-04-04의 "PR 봇 회차"와 "PR 직전 리뷰" / 이번 요청 범위: PR과 병합까지 (원문은 줄바꿈이 있는 지시문이었다. 위는 그 값을 옮긴 것이다.)

## 한 것

- 준비 단계(`core/run.py`)가 에이전트 매니페스트의 `skills`를 적힌 순서대로 읽는다. 이름마다 스킬 매니페스트(`read_manifest(PluginKind.SKILL, …)`)가 먼저, 스킬 문서(`read_skill`)가 그다음이고, 한 이름을 끝낸 뒤 다음 이름으로 간다. 결과는 `_Prepared.skills`를 거쳐 `_Context.skills`로 간다(02가 둔 빈 열 자리).
- 순서: 부재 → 깨짐(mcp, 마스킹·승인 충돌, 모델, **스킬**, 운영자 파일의 손상) → 꺼짐(에이전트, mcp, 모델, **스킬**) → 진입점 import → 모델 만들기. 스킬의 깨짐은 모델 뒤, 운영자 파일의 손상 앞이다.
- 문구: `에이전트 <이름> 이 지정한 skill 플러그인이 없다: <스킬>`, `… skill 플러그인에 SKILL.md 가 없다: <스킬>`. 읽히지 않음은 어댑터의 `PluginError`를 그대로 올린다. 꺼진 스킬은 `Disabled`이고 문구가 스킬 이름과 에이전트를 든다.
- 런타임은 본문을 프롬프트에 붙이지 않는다. `llm_called.prompt`, 이벤트 필드, 트레이스 열쇠 어디에도 스킬 이름과 본문이 실리지 않는다(시험이 잰다).
- 시험: `tests/core/test_run.py`에 "스킬" 절과 준비 순서 표의 일곱 사례를 더했다. 순서, 이름마다 한 번 읽기, 없음·읽히지 않음, 꺼짐(하나·여럿), 고르지 않은 에이전트는 읽지 않음, 고르지 않은 스킬의 꺼짐은 무관함, 실행 사이 본문 편집이 듣는 것, 프롬프트 불변, 재개의 대조와 일시정지 중 꺼짐, 이어 가기. `tests/channel/http/test_end_user.py`에 실제 라우트를 지나는 셋(꺼짐 409 고정 문구, 없음 500, 본문이 최종 사용자 경로의 에이전트에 닿음)을 더했고 `FakePlugins`를 종류별로 넓혔다.
- 옛 셈("mcp와 모델")을 적은 자리를 고쳤다: `core/run.py`(모듈 독스트링, `_prepare`, `_reject_disabled`), `core/ports.py`(`Disabled`, `read_disabled`), `channel/cli/main.py`, `channel/http/router.py`(둘), `channel/http/end_user.py`(둘), `tests/core/test_run.py`의 절 머리, `.claude/rules/core.md`·`http.md`·`sdk.md`, `README.md`의 `disabled.toml` 줄.
- `.scratch/plan.md`의 skill-plugin 행을 `in-progress`로 올렸다(01·02가 병합된 시점의 상태 변경).
- 변이 표 점검: `uv run python tools/mutate.py --check`로 `prepare_mutations.toml`(변이 3)과 `continuation_mutations.toml`(변이 30)의 원문이 모두 한 번씩 있음을 봤다.

## 결정

- **`is_file()`의 `OSError`는 core에서 감싸지 않는다.** 02의 PR 봇(CodeRabbit)이 짚은 것이고 포트 전체의 결정으로 미뤄 둔 일이었다. 03의 호출 자리를 읽으니 `read_manifest`가 매 실행에 이미 같은 노출을 갖고 있어 03이 새 종류의 문제를 더하지 않는다. core가 `OSError`를 잡으면 어댑터의 오류 변환 규칙이 core로 새므로 어댑터 쪽에서 포트 전체로 정하는 것이 맞다. 대기열 572로 올렸다.
- **스킬 이름의 패턴은 core에서 다시 거르지 않는다.** `manifest.skills`의 원소는 매니페스트를 읽는 단계에서 `Field(pattern=PLUGIN_NAME_PATTERN)`를 이미 지난다(`tests/sdk/test_manifest.py`가 `skills`의 패턴 위반 거부를 잰다). 코드 주석이 그렇게 적는다.
- **`str(error)`를 쓰지 않는다.** 스킬 문서의 `ValidationError` 문구는 틀린 값을 싣는다는 02의 교훈이라, 03은 어댑터가 만든 `PluginError`를 그대로 올리고 core가 문구를 다시 만들지 않는다.

## 빨강을 본 것

- `_prepare`의 프롬프트 불변 시험: `llm()`에 스킬 본문을 프롬프트 앞에 붙이는 줄을 임시로 넣어 `model.received`와 `llm_called.prompt` 단언이 빨개짐을 본 뒤 되돌렸다. 되돌린 뒤 저장소 전체에서 표지 문자열이 0임을 grep했다.

## 관찰

- ruff는 한글을 폭 2로 센다. 긴 주석은 `tools/rewrap_comments.py`가 어절 단위로 감는다. 이 도구의 출력을 저장소 밖 상대 경로(`../../../`)로 돌렸다가 주 체크아웃 루트에 임시 파일을 만들었다. 읽고 지웠다(`ls`로 없음을 확인했다).

## 검증 (인계 시점까지)

모두 이 세션이 쳐서 출력을 읽은 것이다.

- `uv run ruff check .`와 `uv run ruff format --check .`: 둘 다 종료 0.
- `uv run python tools/run_checks.py` 첫 바퀴: check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, run-hooks, pytest(363.4초), web-verify(481.1초)는 Passed이고 pyright와 pyright-linux는 Failed였다. 원인은 `tests/core/test_run.py`의 `parametrize` 람다 다섯이 `FakePlugins`의 멤버 타입을 모른다는 `reportUnknown*` 23건이다. 람다를 이름 있는 함수(`_drop_ghost_manifest` 따위 다섯)로 바꿨다. 그 뒤 `uv run pyright`는 0 errors이고 `uv run pytest -q -n 4 tests/core/test_run.py tests/channel/http/test_end_user.py`는 459 passed다. 고친 뒤 `run_checks.py` 전체는 다시 치지 않았다. 커밋의 pre-commit이 갈음한다.
- `uv run --env-file ../../../.env pytest -m llm`: 7 passed(255.45초). `LLM 토큰 합계 49,451(입력 48,410, 출력 1,041). 트레이스 10개, 모델 호출 20건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.`
- `uv run --env-file ../../../.env pytest -m llm_widget`: 1 passed(46.09초). `LLM 토큰 합계 6,777(입력 6,705, 출력 72). 트레이스 1개, 모델 호출 2건.`
- 위젯 e2e(`pnpm -C web/apps/widget exec playwright test`): `15 passed (31.6s)`, 종료 코드 0. 규칙·README·주석·테스트의 람다만 바뀐 뒤 코드는 이 e2e 뒤에 바뀌지 않았다.

## 아직 하지 않은 것 (커밋하지 않은 작업이 워크트리에 있다)

- 셀프 리뷰(`/code-review`)는 스킬을 불렀을 뿐 두 축을 돌리지 않았다. 인계 계기가 그 경계에서 왔다. 새 세션이 `origin/main` 기준으로 처음부터 한다.
- 티켓 `Status:`는 `in-progress`다. 커밋 전에 `done`으로 바꾼다.
- 커밋 전: `git branch --show-current`와 `uv run python tools/sibling_overlap.py`. 바뀐 규칙 파일(`core.md`, `http.md`, `sdk.md`)의 카나리아 알림이 나오면 02의 선례(일지 2026-11-04-04)대로 `--preflight`만 돌릴지 본다.
- PR 직전 리뷰는 `coderabbit-review`(CodeRabbit 좌석이 없어 대기열 570의 대체 둘로 갈 수 있다)나 `bug-perf-review`로 한다. 밀 주장(이 세션이 새로 쓴 사실 문장): `core.md` 새 불릿의 "읽히지 않음은 어댑터의 `PluginError`를 그대로 올린다", "`llm_called`에도 이벤트에도 스킬 이름과 본문을 싣지 않는다", 준비 순서에서 스킬의 깨짐이 모델 뒤 운영자 파일의 손상 앞이라는 문장, `sdk.md`의 "고르지 않은 에이전트의 `skills`는 빈 열이다", `README.md`의 "skill은 에이전트가 고르면 런타임이 실행을 준비할 때 켜짐을 본다".
- 일지의 `is_file()` 결정(대기열 572)은 위 "결정" 절에 있다. 병합 뒤 retro가 이어받는다.

## 셀프 리뷰 (이 세션, base 3012f78d, 파일 14개·커밋 0개·미추적 1개)

표준 축과 명세 축을 서브에이전트 둘로 병렬로 돌렸다.

- 고친 것:
  - README 트리 줄에 "스킬에는 SKILL.md도 있다"를 더했다(명세 축과 표준 축이 함께 냈다).
  - 옛 셈 잔존 넷을 고쳤다: `channel/http/end_user.py` 주석에 모델, `channel/http/router.py` 주석에 모델과 스킬, `tests/core/test_run.py` "꺼진 플러그인" 절 머리에 모델과 스킬, `core/ports.py`의 `PluginError` 독스트링에 스킬.
  - ADR 인용을 맞췄다: `core/ports.py`의 `Disabled`와 `router.py` 주석에 ADR 0041을 더했다.
  - `.claude/rules/core.md` 새 불릿의 "`llm_called`에도 이벤트에도 스킬 이름과 본문을 싣지 않는다"를 "이벤트에 스킬 이름과 본문을 따로 싣지도 않는다 … 에이전트가 프롬프트에 엮은 본문은 그 프롬프트의 일부로 `llm_called.prompt`에 실린다"로 좁혔다. 시험(`called.prompt`가 고친 본문을 든다)과 맞춘다.
  - 같은 불릿의 "읽히지 않음은 어댑터의 `PluginError`를 그대로 올린다"에 `is_file()`의 `OSError`는 감싸지 않는다는 예외를 괄호로 더했다(대기열 572).
  - 준비 순서 표에 "mcp 없음이 스킬 없음보다 먼저"와 "마스킹 충돌이 스킬 없음보다 먼저" 두 행을 더했다. 표의 시험은 17개이고 모두 통과한다.
  - 티켓을 `done`으로 바꾸고 체크박스를 채웠다.
- 남긴 것:
  - smell 셋(`_reject_disabled`의 세 갈래 중복, 종류를 더할 때 열거 문장 열 곳을 고치는 산탄 수정, `FakePlugins`의 스킬용 속성 여덟)은 판단 항목이라 고치지 않았다. 종류가 더 늘지 않는 한 되풀이되지 않는다.
  - 트레이스 시험이 "형식 3"을 단언하지 않는다는 지적은 형식 번호가 `jsonl` 어댑터 헤더의 몫이라 core 가짜로는 볼 수 없다. 시험은 시작 이벤트의 키 집합과 스킬 이름·본문의 부재를 잰다.
  - 티켓의 첫 빨강(가짜의 스킬 문서 읽기가 한 번도 불리지 않는 것)을 본 기록은 이 일지에 없다. 시험 독스트링의 그 문장은 불리지 않으면 이 시험이 먼저 빨갛다는 논리이고 측정이 아니다. 본 빨강은 위 "빨강을 본 것"의 프롬프트 불변 시험 하나뿐이다.
  - 일지 위 "람다 다섯"의 셈은 이름 있는 함수가 여섯이라는 지적이 있다. 여섯째(`_turn_off_skill` 따위)가 바뀐 람다였는지 이 세션은 확인하지 않았다.
- 다시 돌린 명령: `uv run ruff check .`와 `uv run ruff format --check .` 초록, 준비 순서 시험 17개 통과. 나머지는 커밋의 pre-commit이 갈음한다.
- 카나리아: `uv run python tools/sibling_overlap.py`가 바뀐 규칙 파일(`core.md`, `http.md`, `sdk.md`)을 원천으로 든 명세 아홉을 새 `claude -p`로 돌리라고 알렸다(종료 코드 1은 이 알림이고 번호 겹침은 없다). 02의 선례대로 사전 확인(`--preflight`)만 돌렸고 아홉 모두 통과했다(`end-user-continuation`의 여덟은 한 번에 치고, 경로가 `web-widget` 아래인 `http_rule_llm_widget.toml`은 따로 쳤다). 본 회차는 돌리지 않았다. 바꾼 줄은 그 명세들이 묻는 줄이 아니다(`core.md` 새 불릿은 스킬 준비 한 줄, `http.md`는 최종 사용자 500 목록, `sdk.md`는 스킬 한 줄 — 손으로 읽은 판단이다). 그 알림이 남은 채 커밋한다.
- PR 직전 리뷰에 밀 주장(이 세션이 새로 쓴 사실 문장): `core.md`의 "에이전트가 프롬프트에 엮은 본문은 그 프롬프트의 일부로 `llm_called.prompt`에 실린다", "경로 존재 확인의 `OSError`는 `read_manifest`와 같이 감싸지 않고 올라온다".

## 커밋 (이 세션)

셀프 리뷰 반영까지 `45bf702a`(`feat: 런타임이 실행마다 고른 스킬을 준비해 ctx.skills로 넘긴다 (skill-plugin 03)`)로 커밋했다. 커밋의 pre-commit 출력은 이 세션이 읽었다: ruff 둘, 러너(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest, web-verify), 표·줄 구분 문자·변이 표 모두 Passed이고 카나리아 명세와 헌법 판 검사는 파일이 없어 Skipped다. 인용 대조는 경고 하나였고(일지 69행의 따옴표 인용이 저장소에 글자 그대로 없다) 그 줄을 따옴표 없이 고쳐 커밋하지 않은 채 워크트리에 있다.

## PR 직전 리뷰 (인계받은 세션)

CodeRabbit 좌석이 없어 `bug-perf-review`로 돌렸다(기준 3012f78d, 범위 15파일). Critical·Major·Minor는 없고 Nit 둘이다. 밀 주장 셋(프롬프트에 엮은 본문이 `llm_called.prompt`에 실림, `is_file()`의 `OSError`가 감싸지 않고 올라옴, 스킬의 깨짐이 모델 뒤·운영자 파일 손상 앞)은 서브에이전트가 코드(`core/run.py`의 `ctx.llm`·`_prepare`, `filesystem.py`)와 시험(`tests/core/test_run.py`의 스킬·준비 순서 38개를 `-k`로 쳐서 통과)을 읽고 맞는다고 보고했다. 이 세션이 코드를 다시 읽거나 시험을 다시 치지는 않았다. `is_file()`이 `PermissionError`와 `OSError(EIO)`를 그대로 올리고 ENOTDIR는 `None`으로 삼킨다는 것도 서브에이전트가 `uv run python -c`로 `Path.stat`을 바꿔 쳐서 본 것이라고 보고한 값이고, 이 세션은 다시 치지 않았다.

- 고친 것: `_resolve_skills` 독스트링의 "받는 것은 `PluginError` 뿐"에 `OSError` 예외 구절을 더했다.
- 남긴 것: `is_file()`의 `OSError`가 `PluginError`가 아닌 채로 올라오고 트레이스가 비는 것을 고정하는 시험은 두지 않았다. 대기열 572가 포트 전체의 결정을 내리면 그 결정에 맞춰 둔다(감싸기로 정하면 이 시험은 뒤집힌다).
- 한계: 카나리아 명세는 사전 확인(`--preflight`)만 돌렸고 본 회차는 돌리지 않았다.

## 인계

이 세션이 컨텍스트 문턱을 넘은 채 `커밋 뒤`에 와서 인계한다(인계 경계 `커밋 뒤`). 새 세션이 할 일: 위 일지 수정을 커밋에 포함해 푸시하고, PR(`git-pr`)을 열고, `merge.md`의 봇 회차와 병합까지 한다. PR 직전 리뷰는 위 "셀프 리뷰"의 밀 주장 둘을 `bug-perf-review`나 `coderabbit-review`에 넘긴다. 유의: PR 본문에 카나리아는 사전 확인만 돌렸다는 것, `core.md`의 `OSError` 예외(대기열 572)를 적는다.

제목을 `feature/03-runtime-prepares-skills-per-run (인계함)`으로 바꾸고 워크트리 잠금을 푼 뒤 `open-session`을 부른다.

open-session을 부른다 2026-11-04T16:03:13Z
