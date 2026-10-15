# 2026-10-15 (10) grill-with-docs를 모델이 부를 수 있는 스킬로 바꾼다

## 계기

다른 세션에서 사용자가 토큰 최적화 설계 인터뷰를 요청했다. `grill-with-docs`가 사용자 전용(`disable-model-invocation: true`)이라
그 세션은 `grilling`만 불러 진행했고, `domain-modeling`이 하는 `CONTEXT.md` 용어 기록과 ADR 초안 작성이 빠졌다. 사용자가 물었다.

> 사용자(시작 세션이 전한 말): domain-modeling, grill-with-docs를 disable-model-invocation: false로 못 바꾸냐

확인해 보니 `domain-modeling`은 이미 모델이 부를 수 있고 `grill-with-docs`만 사용자 전용이었다. `retro`도 원본은 사용자 전용이었는데
이 저장소에서 모델이 부르게 바꾼 선례가 있다(그 스킬 머리 주석, 일지 2026-09-20). 시작 세션이 `to-spec`·`to-tickets`·`implement`는
바꾸지 않기로 제안했고, 이 세션은 `grill-with-docs` 하나를 바꾸는 `chore/` PR을 맡았다.

PR #247을 연 뒤 사용자가 이어서 말했다.

> 사용자: grill-with-docs 불렸을 때 훅을 두는건? 실제 설계를 하는 내용인지 확인하도록, ADR 개정 승인, 병합 진행

세 가지로 읽었다. 모델이 이 스킬을 부를 때 설계 인터뷰가 맞는지 확인하게 하는 훅을 더하고, ADR 0028의 어긋난 목록을 고치는
개정을 승인하며(CLAUDE.md 작업 규약 5의 승인), CI가 끝나면 병합까지 진행한다.

## 한 일

- `.claude/skills/grill-with-docs/SKILL.md`: `disable-model-invocation: true`를 뺐다. 설명을 한국어 한 문장으로 다시 썼다.
  앞에 선두어 "설계 인터뷰"를 두고 트리거를 둘로 좁혔다(사용자가 이를 요청할 때, 즉 "grill"이나 "인터뷰 진행하자"일 때, 새 기능에
  `.scratch/<slug>/`가 없는 단계일 때). 구현과 리뷰 중에는 하던 일을 이어 간다는 한 구절을 붙였다(셀프 리뷰 표준 축이 가지마다
  트리거 하나, 선두어 되풀이 금지, 부정보다 긍정을 짚어 첫 판의 동의어 셋과 부정문을 고쳤다).
  머리 주석에 "프로젝트 사본, model-invoked"와 근거를 남겼다(`retro`와 같은 모양).
- `tools/check_instructions.py`: `PATCHED_SKILLS`에 `grill-with-docs`를 더했다. 머리 주석이 센티널이라 목록에 없으면 역방향 검사
  (`skills_with_sentinel_not_listed`)가 빨강이 된다.
- 참조를 고쳤다. `next-session` 54행(사용자 전용 목록에서 `/grill-with-docs`를 빼고 모델도 부른다고 적음), `kickoff/pitfalls.md`
  27행, `KICKOFF.md`의 덧댄 사본 수 두 곳(여섯에서 일곱, 다섯에서 여섯).
- 확인만 하고 안 고친 것: `next-session` 48행의 시작 프롬프트 `/grill-with-docs`는 그대로 맞다. `open-session`은 첫 줄의
  `/<이름>`이 이 저장소의 스킬이면 `SKILL.md`를 읽으라는 한 줄로 옮기는 처리라 플래그와 상관이 없다. `docs/agents/domain.md` 10행의
  "`/grill-with-docs`가 호출"은 지금도 참이다.
- `to-spec`·`to-tickets`·`implement`는 단계를 넘어갈지 사람이 정하는 관문이라 사용자 전용으로 둔다.
- 사용자 요청 뒤에 더한 것:
  - `tools/hook_grill_design_check.py`: PreToolUse 훅(매처 `Skill`). 모델이 `grill-with-docs`를 부르려 하면 설계 인터뷰가 맞는지
    확인하라는 계기를 넣는다. 막지 않는다. 등록(`.claude/settings.json`), 테스트(`tests/tools/test_hook_grill_design_check.py`),
    페이로드 표(`tools/hook_payloads.toml`의 발동과 침묵 각 하나), `.claude/rules/tools.md`의 훅 시간 문단에 한 문장.
  - ADR 0028: 이력 항목 "grill-with-docs는 모델이 부르되 부르기 전에 설계 인터뷰인지 확인한다"와 "범위" 문장 뒤의 포인터. 사용자가
    승인했다. `.scratch/kickoff-auto-flow/spec.md` 324행의 같은 목록도 고쳤다(진행 중인 명세라 살아 있는 문서다).

## 갈린 곳

- **훅이 막을지, 사용자에게 물을지, 알리기만 할지.** 알리기만 하는 계기로 정했다. 훅은 대화를 읽지 못해 설계 인터뷰인지 가를 수
  없다. 막거나 `permissionDecision: ask`로 물으면 사용자가 요청한 인터뷰까지 한 번 더 막히거나 묻는다. 모델이 알림을 보고 스스로
  가른다. 알림 뒤에도 틀리는 일은 못 막고, 그런 사례가 나오면 막는 훅이나 트리거 좁히기로 간다(`.claude/rules/tools.md`의 계기 훅과
  막는 훅 가름).
- **ADR 0028 76행과 명세 324행의 목록.** 처음에는 범위 문장이 참이라 고치지 않고 PR 본문에 적었다. 사용자가 ADR 개정을 승인해
  이력 항목과 포인터로 고쳤다.
- **둘째 트리거(`.scratch/<slug>/`가 없는 단계)가 사람의 관문을 건너뛰는지.** 셀프 리뷰 표준 축이 짚었다(Major, 판단 항목). 설계
  인터뷰는 기능의 첫 단계라 건너는 관문이 앞에 없고, 시작 프롬프트(`/grill-with-docs`)가 이미 모델이 부르지 못해 사람이 쳐야
  했던 자리인데 이 PR은 그 사람의 몫을 덜어 내는 것이 요청이다. 인터뷰의 질문마다 사람이 답하므로(`AskUserQuestion`) 모델이 혼자
  결정을 확정하지는 못한다. 둘째 가지는 시작 요청에 명시된 트리거라 남겼고, `kickoff/pitfalls.md`의 기준 문장에 이 이유를 적었다.
- **`grill`이 `grilling`의 설명과 겹치는지.** 겹침이 이 PR이 고치려던 실패(`domain-modeling` 누락)를 되살릴 수 있다고 짚었다.
  "이 설계를 grill해줘" 요청으로 재 보니 `grill-with-docs`가 먼저 불리고 셋이 차례로 불렸다(아래 검증).

## 검증

- `uv run pytest -q tests/tools/test_check_instructions.py`: 107 passed. `uv run python tools/check_instructions.py`: 출력 없음(통과).
- 새 `claude -p` 세션을 이 워크트리에서 시작해 손으로 봤다(커밋한 프로브가 아니라 "쟀다"가 아니다). 명령은
  `echo "<요청>" | claude -p --model sonnet --tools Skill --max-turns 6 --output-format stream-json --verbose`이고,
  stream-json의 `tool_use` 중 `Skill` 호출을 뽑았다(`--max-turns` 도달로 종료 코드 1이 난 회차가 있다. 호출 순서를 본 것이라 무관하다).
  init의 스킬 목록에 `grill-with-docs`가 있었다.
  - 설명을 다듬기 전의 첫 판으로 한 번, 다듬은 최종 판으로 한 번 돌렸다. 아래는 최종 판의 결과이고 첫 판의 긍정·부정 결과도 같았다
    (구현 요청에서만 첫 판은 `tdd`가 불렸고 최종 판은 스킬 호출이 없었다).
  - 불린 경우 "인터뷰 진행하자. 주제는 토큰 최적화." → `grill-with-docs`, `grilling`, `domain-modeling` 차례로 불렸다.
    "이 설계를 grill해줘. 새 기능 admin-foo의 범위를 같이 따져 보자." → 같은 차례로 불렸다(`grilling`만 불리지 않았다).
  - 불리지 않은 경우 "tools/check_instructions.py에 PATCHED_SKILLS의 항목 수를 돌려주는 함수를 구현해줘." → `grill-with-docs`가
    불리지 않았다. "지금 브랜치의 변경을 리뷰해줘." → `code-review`만 불렸다.
  - 한계: 시험은 네 번(긍정 둘, 부정 둘)이고 한 모델이다. 한글 요청을 파이프로 넘겨 출력의 인자 글자가 깨져 보이지만 호출 순서에는 영향이 없다.
    설계와 닮았지만 요청하지 않은 말("새 기능을 어디부터 할까")에서의 경계는 재지 않았다.
- 훅(손으로 봤다): `uv run python tools/run_hooks.py`가 페이로드 96건 어긋남 0건. 등록 모양의 새 `claude -p` 세션에서 "Skill
  도구로 grill-with-docs를 부르고 훅이 알린 첫 문장을 옮겨라"에는 모델이 "grill-with-docs를 부르기 전에 설계 인터뷰가 맞는지
  확인한다"를 옮겼고, 같은 요청을 `grilling`으로 하면 "알림 없음"이라고 답했다. 훅 문장이 모델에게 닿는 증거는 모델의 답이다
  (스트림에는 additionalContext가 실리지 않는다). 변이는 손으로 한 번 봤다: 훅의 `!= SKILL`을 `==`로 뒤집으면 테스트 8건 중 3건이
  빨갛고 되돌렸다(`tools/mutate.py`의 변이 표는 만들지 않았다).
- 전체 `pytest`, `ruff`, `pyright`, `lint-imports`, `web verify`는 PR 본문의 검사 절을 따른다.

## 셀프 리뷰 (훅과 ADR 추가분)

범위는 기준 `95c2420`(PR #247에 이미 푸시), 수정 8개와 미추적 2개. 두 축 모두 Critical은 없었다.

- 고친 것(Major): 독스트링의 못 보는 것 중 "플러그인 이름이 붙은 호출"에 고정 테스트가 없었다(`test_플러그인_이름이_붙은_호출은_보지_않는다`).
  `KICKOFF.md` 훅 복사 목록(284행)에 새 훅이 빠져 새 프로젝트가 훅 없이 스킬만 받을 수 있었다(284행에 훅을 적고 306행에 짝을 적었다).
- 고친 것(Minor): ADR의 "바뀌는 것은 하나다"를 둘로, "거부한 안은 둘이다"를 막기(`deny`)를 더해 셋으로 고쳤다. 슬래시 명령이 훅을
  거치지 않는다는 주장을 "재지 않았다(어림)"로 낮췄다. 독스트링의 출처 불명 귀속(`bug-perf-review`)을 지웠다. ADR의 "손으로 봤다"에
  명령이 있는 일지의 절을 가리켰다. 새 파일의 엠대시를 없앴다. 테스트 6·7이 둘 다 `None`이어도 통과하던 것을 `is not None` 단언으로 막았다.
- 남긴 것: ADR 개정문이 쓰이기 전에 승인을 받았다는 점(규약 5는 초안을 보인 뒤 승인). 사용자가 개정 자체를 승인했고 문안은 PR에서 본다.

## 회고

후보 넷. 승인 0, 기각 4, 넘김 0.

1. 스킬 트리거를 재는 도구가 없다(`tools/canary.py`의 skill 갈래는 본문 카나리아가 실리는지만 본다). 이 세션이 Skill 호출을 뽑는
   스크립트를 스크래치패드에 짓고 손으로 돌렸다: 기각. 모델이 부르는 스킬의 설명을 바꾼 것은 `retro` 이후 이번이 처음이라 반복이
   아니고, 사건은 한 번의 수고뿐이다. 설명을 또 바꾸는 세션이 같은 수고를 하면 그때 도구로 올린다.
2. "사용자 전용 스킬" 목록이 `next-session`, `kickoff/pitfalls.md`, `KICKOFF.md`, ADR 0028, 명세에 산문으로 흩어져 있다: 기각.
   바꿀 곳을 놓친 실수는 나지 않았다. `CLAUDE.md` 작업 규약 4의 grep이 다섯 곳을 모두 찾았다.
3. 이 세션의 Grep 호출 두 번이 `.env`에 닿는 glob(`!…`)으로 훅에 막혔다: 기각. 이미 막는 훅이 있고 거부 메시지가 고칠 길을
   알려 줬다.
4. `KICKOFF.md`가 덧댄 사본 수("여섯", "다섯")를 글자로 적어 사본을 더할 때마다 손으로 고쳐야 한다: 기각. 런북의 "바꿀 곳"
   문장이 이미 그 상수를 가리키고, 수를 지우는 것은 런북 구조를 건드리는 범위 밖의 일이며 틀린 수가 낸 실수는 없었다.

## 다음

- PR 병합 뒤 주 체크아웃의 `tidy-checkouts`가 이 워크트리를 지운다.
- 설명이 모든 세션 컨텍스트에 실리는 값을 치르므로, 설계 인터뷰가 아닌 말에 `grill-with-docs`가 불린 사례가 생기면 트리거를 더 좁힌다.
- 설계가 아닌 요청에서 `grill-with-docs` 알림 뒤에도 인터뷰가 돌아간 사례가 생기면 훅을 막는 쪽(`permissionDecision: ask` 등)으로
  올릴지 정한다. ADR 0028 이력에 같은 말을 적었다.
