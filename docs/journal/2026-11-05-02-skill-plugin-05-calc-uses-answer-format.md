# 2026-11-05 (02) skill-plugin 05: calc가 예시 스킬 answer-format을 쓰고 실제 모델 시험이 스킬 경로를 지난다 (구현 세션)

세션 제목은 `feature/05-calc-uses-answer-format-skill`이다. 티켓은 `.scratch/skill-plugin/issues/05-calc-uses-answer-format-skill.md`이다.

## 사용자 프롬프트

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 인자: .scratch/skill-plugin/issues/05-calc-uses-answer-format-skill.md (다음 단계: 구현 / 어디서: 새 세션, 나란히 여는 2 중 2 / 브랜치: feature/05-calc-uses-answer-format-skill / 이번 요청 범위: PR과 병합까지. 원문은 줄바꿈이 있는 지시문이었다. 위는 그 값을 옮긴 것이다.)

## 한 것

- 워크트리 `.claude/worktrees/05-calc-uses-answer-format-skill`에 들어가 브랜치를 `feature/05-calc-uses-answer-format-skill`로 바꿨다. 기준은 origin/main `5b255a18`(03 병합 뒤)이다. `uv sync`와 `pnpm -C web install --frozen-lockfile`은 끝 코드 0이었다.
- 티켓 `Status:`를 `in-progress`로 바꿨다가 구현을 마치고 `done`으로, 체크박스 열일곱을 모두 채웠다(`sed`로 바꾸고 `grep -c "\[x\]"`가 17을 냈다).
- 예시 스킬 `plugins/skills/answer-format/`을 두었다. `plugin.toml`은 공통 넷뿐이고 `SKILL.md`의 머리말은 `name: answer-format`과 한 줄 `description`, 본문은 프로브가 잰 세 문장 그대로다. `plugins/skills/.gitkeep`은 지우지 않았다.
- `plugins/agents/calc/plugin.toml`에 `skills = ["answer-format"]`을 적었다. `plugins/agents/calc/agent.py`는 `PROMPT`에 `{skills}`를 더하고 `ctx.skills`마다 `지침 <이름>: <본문>\n\n` 블록을 머리 문장 뒤, 앞 대화 블록 앞에 엮는다. 본문은 `.strip()`으로 다듬는다. 독스트링의 "그 전과 글자 그대로 같다"를 고쳤다.
- 시험(`tests/test_calc_plugin.py`): `FRESH_PROMPT`를 블록이 든 글로 바꾸고 `HEAD`·`ANSWER_FORMAT_BODY`·`BARE_PROMPT`를 뽑았다. 더한 시험은 넷이다(여기에 이름을 바꾼 시험 하나가 있다). 저장소 폴더를 실제 어댑터로 읽어 `Skill`이 되는 것, 이어 간 실행에서 스킬 블록이 앞 대화 블록 앞에 서는 것, 스킬이 둘일 때 매니페스트 순서로 블록 둘이고 둘째 본문이 시험 파일에서 읽히는 것(앞뒤 공백 다듬기 포함), `skills`를 지운 사본이 옛 글인 것. `_run_calc`가 `plugins_root`를 받는다. 이름을 바꾼 시험은 `…_저장소_스킬_블록이_든_글과_글자_그대로_같다`라서 변이 표의 선택자 `-k 글자_그대로_같다`가 그대로 맞는다.
- `tests/test_main.py`: `-m llm`의 calc 시험에 단언을 더했다(첫 `llm_called.prompt`에 `SKILL.md`를 `parse_skill`로 읽어 다듬은 본문이 든다). `_copy_repo_plugins`가 `skills/answer-format`도 복사한다. 새 시험은 더하지 않았다.
- 옛 표현 grep: README·CONTEXT·PRD·헌법·rules·`src/`·`plugins/`에서 "calc의 프롬프트가 그 전과 같다"류의 살아 있는 문장은 없었다(`Grep`으로 봤다). README의 트리 줄은 이미 스킬의 `SKILL.md`를 적는다.

## 빨강을 본 것

- 구현 전 `uv run pytest -q tests/test_calc_plugin.py`: 5 failed, 2 passed(출력을 이 세션이 읽었다). 실패는 저장소 폴더 읽기, `FRESH_PROMPT`, 이어 간 실행의 블록 자리, 스킬 둘, `skills` 지운 사본이다. `skills` 지운 사본이 빨간 것은 시험의 `assert text.count(old) == 1`이 매니페스트에 `skills` 줄이 없어서 낸 것이라, 옛 글 단언 자체를 본 빨강이 아니다. 구현 뒤 `tests/test_calc_plugin.py`와 `tests/test_plugins_boundary.py`는 끝 코드 0이다.
- 변이를 새로 넣은 빨강은 보지 않았다. 스킬 둘 시험이 "본문을 코드에 베낀 calc는 지나지 못한다"는 논리는 이 세션이 변이로 재지 않았다.

## 검증 (인계 시점까지)

모두 이 세션이 쳐서 출력을 읽은 것이다.

- `uv run ruff check .`와 `uv run ruff format --check .`: 둘 다 통과(`1254 files already formatted`).
- `uv run python tools/run_checks.py`(백그라운드, 끝 코드 0): check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, pytest(373.8초), web-verify(477.6초) 모두 Passed. 이 러너는 티켓을 `in-progress`로 둔 채 돌았다. 티켓을 `done`으로 바꾼 뒤에는 다시 돌리지 않았다.
- `uv run python tools/mutate.py --check .scratch/conversation/probes/continuation_mutations.toml`: `변이 30 모두 원문이 한 번씩 있다`, 끝 코드 0.
- `uv run --env-file ../../../.env pytest -m llm`: `7 passed`(142.52초). `LLM 토큰 합계 61,603(입력 60,548, 출력 1,055). 트레이스 10개, 모델 호출 23건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.`
- `uv run --env-file ../../../.env pytest -m llm_widget`: `1 passed`(51.62초). `LLM 토큰 합계 6,937(입력 6,865, 출력 72). 트레이스 1개, 모델 호출 2건.`
- 위젯 e2e(`pnpm -C web/apps/widget exec playwright test`): 끝 코드 0. 요약 줄은 읽지 않았다.
- 관리 화면 e2e와 사진 비교는 치지 않았다. 이 티켓은 `web/`을 건드리지 않았고 관리 e2e의 스택은 자기 가짜 플러그인을 쓴다(`web/apps/admin/e2e/stack.ts`를 grep으로 봤다).

## 아직 하지 않은 것 (커밋하지 않은 작업이 워크트리에 있다)

- 셀프 리뷰(`/code-review`)는 스킬을 불렀을 뿐 두 축을 돌리지 않았다. 인계 계기가 그 경계에서 왔다. 새 세션이 처음부터 한다(base는 `origin/main`).
- 변경 파일: 새 `plugins/skills/answer-format/{plugin.toml,SKILL.md}`, 고친 `plugins/agents/calc/{plugin.toml,agent.py}`, `tests/test_calc_plugin.py`, `tests/test_main.py`, 티켓 파일, 이 일지.
- 커밋 전: `git branch --show-current`와 `uv run python tools/sibling_overlap.py`(이 세션의 마지막 결과는 번호 겹침 없음, 함께 고친 파일 없음, 일지 번호는 02). 카나리아 알림이 나오면 03 일지(2026-11-05-01)의 선례대로 `--preflight`만 돌릴지 본다. 이번에 바뀐 `.claude/rules/*.md`는 없다.
- `.scratch/plan.md`의 skill-plugin 행은 이 티켓이 병합되면 04와 함께 상태를 맞춘다(03 일지의 선례). 이 세션은 건드리지 않았다.
- PR 직전 리뷰에 밀 주장(이 세션이 새로 쓴 사실 문장): `agent.py` 독스트링의 "스킬을 고르지 않고 이어 가지도 않은 실행의 프롬프트는 블록이 없어 머리 문장과 요청뿐이다", 시험 독스트링의 "본문을 코드에 베낀 calc 는 여기서 빨갛다", `test_main.py` `_copy_repo_plugins` 독스트링의 "calc 의 매니페스트가 고른 스킬이 없으면 실행이 준비에서 멈춘다".
- 대기열 572(`is_file()`의 `OSError`)는 이 티켓의 몫이 아니고 병합 뒤 retro가 이어받는다.
- 병합은 이 워크트리 사본의 next-session `merge.md`("워크트리에서 병합할 때")를 Read로 열어 따른다.

## 인계

이 세션이 컨텍스트 문턱을 넘은 채 `셀프 리뷰 직전`에 와서 인계한다(커밋하지 않은 변경이 워크트리에 있다). 새 세션이 할 일: 셀프 리뷰, 커밋, PR, 봇 회차와 병합까지. 일지 파일은 `docs/journal/2026-11-05-02-skill-plugin-05-calc-uses-answer-format.md`다.

제목을 `feature/05-calc-uses-answer-format-skill (인계함)`으로 바꾸고 워크트리 잠금을 푼 뒤 `open-session`을 부른다.

open-session을 부른다 2026-11-04T17:14:34Z


## 셀프 리뷰 (인계받은 세션, base 5b255a18, 파일 5개 변경과 미추적 3개, 커밋 0)

두 축을 서브에이전트로 돌렸다(표준은 sonnet·high, 명세는 세션 모델). 보고는 이 세션이 읽었다.

- 표준 축: 확정 위반 없음. 판단 둘. (1) Minor: 프로브 `.scratch/skill-plugin/probes/answer_format_llm.py`의 `_prepare`가 `"{previous}요청: {request}"` 한 번을 단언해, 새 `PROMPT`(`"{skills}{previous}요청: {request}"`)에서 모델을 부르기 전에 멈춘다. 이 세션이 Grep으로 `PROMPT_TAIL`이 옛 모양인 것을 확인했다. (2) Nit: `지침 answer-format: {ANSWER_FORMAT_BODY}\n\n` 꼴이 시험 파일에 세 번. 글자 그대로 박는 것이 의도라 남긴다.
- 표준 축의 주장 검증: 독스트링 인용(ADR 0022·0041, 명세 "예시 스킬", conversation 명세 "calc"·스토리 40)이 글자 그대로이고, 본문을 코드에 베낀 calc 사본(임시 복사)이 스킬 둘 시험과 `skills` 지운 시험에서 빨갛고 `FRESH_PROMPT`·순서 시험은 초록인 것을 서브에이전트가 돌려 봤다. `_copy_repo_plugins` 독스트링의 "준비에서 멈춘다"는 `core/run.py`의 `_prepare`가 `PluginError`를 내는 것과 맞는다.
- 명세 축: Critical·Major 없음, 범위 넘침 없음. 요구 열일곱 모두 구현. 약한 지점 둘. (a) `plugin.toml`이 공통 넷뿐이라는 요구를 직접 재는 시험이 없다(내용은 맞고 어댑터 읽기 시험이 지난다). (b) 일지의 `run_checks`는 티켓이 `in-progress`일 때 돌았다.

고친 것. 프로브 `_prepare`: 모든 갈래(셋이다)에서 복사한 calc 매니페스트에서 `skills = ["answer-format"]` 줄을 지우고(그래야 대조 갈래에 본문이 없고 블록 갈래에는 글로 넣은 블록 하나만 있다), `PROMPT_TAIL`을 새 모양으로 바꿨다. 독스트링에 한 문장을 더했다. 모델을 부르지 않고 `_prepare`를 두 갈래로 불러, 대조는 `머리\n\n요청: …`이고 블록은 `머리\n\n지침 answer-format: <본문>\n\n요청: …` 한 블록인 것을 봤다. LLM 프로브는 다시 돌리지 않았다(재던 것이 그대로이고, 본문은 바뀌지 않았다).
남긴 것. 위 Nit과 `plugin.toml` 시험 부재(Minor, 파일 내용이 공통 넷뿐인 것은 명세 축이 읽어 확인했고, 어댑터가 그 폴더를 `Skill`로 읽는 시험이 지난다). 일지의 "더한 시험은 다섯"은 넷이 맞아 고쳤다.
다시 돌릴 것. 커밋의 pre-commit(티켓이 `done`인 채 도는 첫 판)이 손으로 치는 다섯을 갈음한다. 결과는 커밋 뒤 이 일지와 PR 본문에 적는다.

PR 직전 리뷰에 밀 주장(이 세션이 새로 쓴 사실 문장): 프로브 `_prepare` 주석 "모든 갈래에서 그 줄을 지워 대조 갈래에 본문이 없고 블록 갈래에는 글로 넣은 블록 하나만 있게 한다(재던 것 그대로)", 프로브 독스트링 "티켓 05 뒤에도 같다".

## PR 직전 리뷰 (CLI 좌석 없음, 대체 둘)

- `coderabbit auth status`가 `Seat: not assigned`를 냈다(이 세션이 쳤다). CLI는 돌지 못해 `bug-perf-review` 서브에이전트와 내장 `/security-review`를 대신 돌렸다. 둘 다 커밋 `ac14e4d7` 뒤에 돌았고 origin/main은 base 5b255a18 그대로였다(`git log HEAD..origin/main`이 비었다).
- `/security-review`: 지적 없음. 코드를 읽어 본 판정이다. 스킬 본문은 `SKILL.format(name=…, body=…)`과 `PROMPT.format(skills=…)`의 인자로만 들어가 재해석되지 않고, 본문은 운영자가 둔 파일이라 지시로 쓰는 것이 ADR 0041의 결정이다. 이 변경은 새 입력 경로(네트워크, 경로, 명령)를 더하지 않는다.
- `bug-perf-review`(서브에이전트): Critical·Major·Minor 없음, Nit 둘. 서브에이전트가 `uv run python`으로 `_skill_blocks`에 빈 목록, 중괄호(`{previous} {request} {0} {}`)와 줄바꿈이 든 본문을 넣어 재해석되지 않는 것을 봤고, 임시 폴더에서 프로브 `_prepare`를 세 갈래로 불러 매니페스트의 `skills`가 빠지는 것과 블록이 글로 넣은 하나뿐인 것을 봤고, 안 만든 스킬 폴더로 `_resolve_skills`를 불러 `PluginError`가 나는 것을 봤다(보고에 적힌 대로이고 이 세션은 되돌려 재지 않았다).
  - Nit 1(고쳤다): 프로브 주석·독스트링의 "두 갈래 모두"가 틀리다. 갈래는 셋이다(`ARMS`). "모든 갈래"로 고쳤다.
  - Nit 2(남겼다): 공백뿐인 본문은 `지침 a: \n\n`이라는 내용 없는 줄이 된다. `parse_skill`이 빈 본문을 거르지 않는다. 티켓은 본문의 앞뒤 공백을 다듬는 것까지만 요구하고 빈 본문 처리는 요구하지 않으며, 머리말만 있는 스킬 문서를 두는 운영자 실수의 몫이라 이 티켓에 넣지 않는다.
- 일지 인용 두 곳의 띄어쓰기(`calc 는`, `calc 의`)를 코드의 독스트링과 같게 고쳤다(pre-commit의 인용 대조 경고 둘, 대기열 42).

## 인계 2 (PR 연 뒤)

- 커밋 둘(`ac14e4d7` 구현과 시험, `a76270a0` 리뷰 반영)을 푸시하고 PR [#464](https://github.com/njh6803/agent-os/pull/464)를 열었다. 두 커밋 모두 pre-commit의 손으로 치는 다섯(ruff 둘, pyright, lint-imports, pytest, web verify)이 `Passed`였다. 캐나리아 명세·헌법 판 검사는 `Skipped`(해당 파일 없음)였다. 두 번째 커밋에서 인용 경고는 없었다.
- PR 본문은 `.github/PULL_REQUEST_TEMPLATE.md`를 채웠다. 사용자 프롬프트는 위 "사용자 프롬프트" 그대로(범위: PR과 병합까지)다.
- 이 세션이 번복한 것: 없음. 표준 축이 낸 프로브 단절(Minor)을 고쳤고, 공백뿐인 본문의 빈 지침 줄(Nit)은 이 티켓의 요구 밖이라 남겼다.
- 남은 일: `merge.md` 2의 봇 회차(첫 `@coderabbitai review` 코멘트 포함), 병합(`merge.md`의 "워크트리에서 병합할 때"), 병합 뒤 `.scratch/plan.md`의 skill-plugin 행을 04와 함께 맞추기. 대기열 572는 이 티켓의 몫이 아니고 병합 뒤 retro가 이어받는다.
- 이 세션의 제목은 `feature/05-calc-uses-answer-format-skill`이었다.
open-session을 부른다 2026-11-04T17:44:01Z

## 봇 회차 (첫 회차)

- 근거는 `gh pr view 464 --json comments`로 읽은 PR 코멘트다. CodeRabbit은 "No actionable comments"를 남겼고 `wait_ci.py 464`가 모든 검사를 통과로 찍었다. claude-review는 병합을 막는 지적이 없고 Minor 하나, Nit 둘이었다.
  - Minor(고쳤다): `plugins/skills/answer-format/plugin.toml`이 공통 넷뿐이라는 티켓 요구를 재는 시험이 없었다. `test_저장소의_answer_format_매니페스트는_공통_넷뿐이다`를 `tests/test_calc_plugin.py`에 더했다. `uv run pytest -q tests/test_calc_plugin.py`가 8개 통과, 해당 파일의 ruff 검사와 서식 검사가 통과했다(손으로 쳤다).
  - Nit(남겼다): `지침 answer-format: …` 꼴이 시험에 세 번 나온다. 프롬프트 모양을 글자 그대로 박는 것이 의도다.
  - Nit(남겼다): 공백뿐인 본문의 빈 지침 줄은 위 리뷰 반영에서 이미 이 티켓 밖으로 적었다.
