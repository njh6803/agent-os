# 2026-10-16 (41) 셀프 리뷰 표준 축을 sonnet·high로, 쓰지 않는 플러그인 넷 끄기

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/token-usage/issues/07-review-axis-and-plugins.md
> (지시문: 나란히 여는 4 중 4, 브랜치 feature/07-review-axis-and-plugins, 모델 Opus 5.5 / medium, 범위는 PR과 병합까지)

## 정리

티켓 `.scratch/token-usage/issues/07-review-axis-and-plugins.md`를 구현했다. 결정은 ADR 0033 본문이다.

- `code-review` 4단계 첫 문장을 바꿨다. 표준 축은 변경 종류와 상관없이 `model: sonnet`과 `effort: high`로 띄우고, 명세 축에는 둘 다 주지 않는다. 센티널 주석의 "4단계의 sonnet 규칙"도 고쳤다.
- `docs/model-selection.md` 표준 축 행의 손잡이를 "모델과 노력"으로, `KICKOFF.md` 305행의 덧댄 것 목록을 바뀐 규칙으로 고쳤다.
- `.claude/settings.json`의 `enabledPlugins`에 `document-skills@anthropic-agent-skills`, `example-skills@anthropic-agent-skills`, `skill-creator@claude-plugins-official`, `code-review@claude-plugins-official`을 `false`로 더했다.
- 레벨 스윕 README에 `### 조건 변경(ADR 0033)` 절을 만들고 두 줄을 적었다. `sweep.py prereg`는 0으로 끝났다.

## 확인

- **잔존 grep.** "touches no source file", "소스 파일이 없는", "소스 없는 변경은 sonnet"을 저장소 전체에서 grep했다. 남은 것은 ADR 0006 24행(포인터 `(바뀜: ADR 0033)`이 붙은 문장), 명세와 이 티켓, 새 카나리아 명세의 머리 주석(옛 판을 설명하는 대조군 문장), 레벨 스윕 README 새 절의 "전에는" 줄(조건 변경의 기록)이고, 살아 있는 문서에서 옛 규칙을 지시하는 자리는 0이다.
- **플러그인 넷을 부르는 자리.** 네 이름과 `code-review:code-review`를 grep했다. 지침과 스킬이 그 넷의 스킬을 부르는 자리는 없었다. ADR 0006 49행은 그 플러그인을 쓰지 않는다는 기록이고, `tests/tools/test_hook_stop_korean.py`는 문자열 재료다.
- **플러그인 끄기(손으로 봤다, claude 2.1.300).** 사용자 설정을 싣는 맨 `claude -p --model sonnet`에 같은 질문(파일로 `<` 넘김)을 던졌다. 질문은 세션의 스킬 목록에서 `coderabbit:` 스킬(표지)과 넷의 접두를 가진 스킬을 옮기게 했다.
  - 양성 대조: origin/main(`30b9f37`)을 임시 워크트리로 꺼내 띄운 세션은 표지 셋과 넷의 스킬 열여덟(`document-skills:` 넷, `example-skills:` 열둘, `skill-creator:skill-creator`, `code-review:code-review`)을 옮겼다.
  - 실험군: 이 워크트리에서 띄운 세션은 표지 셋을 옮기고 넷의 스킬에는 없다는 표지 "없음2"로 답했다.
  - 그래서 프로젝트 설정의 `false`가 사용자 설정의 `true`를 이긴다는 것을 이 PC에서 한 번 봤다. 보고서 9절로 0자를 보는 확인은 티켓 09가 한다.
- **카나리아.** 새 명세 `.scratch/harness/probes/canary/code_review_standards_axis_effort.toml`을 `--control-commit 30b9f37`로 돌려 통과 4였다. 실험군 셋은 바뀐 문장을 옮겼고, 대조군은 노력 값이 없다며 "없음"이라 답했다.

## 셀프 리뷰

`/code-review` 두 축(base `30b9f37b`, 수정 6, 미추적 2, 커밋 0). 표준 축은 바뀐 규칙대로 `sonnet`·`high`로 띄웠다. 두 축 모두 Critical은 없었다.

- 고친 것
  - 두 축이 함께 짚은 것(노력 상속): 명세 축이 노력까지 물려받는다는 문장을 단정했다. ADR 0033은 노력의 상속을 어림으로 적었다. 스킬 4단계와 `docs/model-selection.md` 행에 어림이라고 붙였다.
  - 두 축이 함께 짚은 것(README 근거): 레벨 스윕 README 새 절 머리가 "새 세션의 설정과 훅은 주 체크아웃의 사본으로 돈다"며 훅 디렉터리를 말하는 `tools.md` 항목을 근거로 들었다. 워크트리의 `claude -p`에는 워크트리의 설정이 실렸으므로 반례가 있었다. 스킬은 시작한 체크아웃의 사본(`operations.md` 환경 규약 상세), 설정은 띄운 자리의 것(이 일지의 확인)으로 고쳤다.
  - 표준 축: README의 "전에는 소스 파일이 없는 변경에서만" 줄이 옛 규칙의 범위(`src/`·`tests/`·`tools/` 아래 `*.py`)보다 좁았다. 옛 범위대로 고쳤다. 일지 정리의 따옴표 인용이 원문에 없는 문장이라 따옴표를 뺐다. 잔존 목록에 README의 "전에는" 줄을 더했다.
  - 명세 축: 카나리아가 명세 축 문장을 고정하지 않았다. 질문에 명세 축 문장을 더하고 `expect`에 `Give the Spec sub-agent neither`를 더해 다시 돌렸다. 통과 4였다.
  - Nit: 일지의 "없음2"는 오타가 아니라 질문이 정한 표지라서, 표지라고 밝혔다.
- 남긴 것과 이유
  - README의 `PR #PRNUM`: PR을 연 뒤 268로 바꿨다.
  - `docs/model-selection.md` 새 칸 "모델과 노력"과 같은 표의 "모델과 레벨"의 낱말 차이: 티켓이 "모델과 노력"으로 정했다.
  - `KICKOFF.md` 38행·334행이 `enabledPlugins`의 `false`로 플러그인을 끄는 길을 아직 적지 않은 것: 티켓은 305행만 고치라고 했다. 런북은 사람이 직접 겪은 것으로 만들어 간다는 방침이라, retro 후보로 넘긴다.
  - Agent 도구가 `effort`를 받지 못하는 환경의 갈래: 이 세션의 도구는 받는다. 실제로 `sonnet`·`high`로 돌았는지는 티켓 09가 보고서 4절로 본다.
  - 같은 규칙이 다섯 자리에 적힌 것(Shotgun Surgery 판단 항목): 티켓이 정한 자리다.
- 다시 돌린 명령: `sweep.py prereg` 0, 카나리아 통과 4. 나머지 검증 명령은 커밋의 pre-commit으로 갈음한다.

## PR 직전 리뷰

CodeRabbit CLI는 좌석 미배정(`Seat: not assigned`, CLI 0.7.5)으로 돌지 못해 대체 둘을 나란히 돌렸다.

- `bug-perf-review`: 유효 1, 오탐 5. 유효는 README의 `PR #PRNUM` 자리표시자다(Minor). PR을 연 직후 268로 바꿨다. 오탐으로 판정한 것은 다섯이다. 이름이 같은 프로젝트 `code-review` 스킬이 꺼질 위험, 카나리아 거짓 통과, 옛 규칙 잔존, `effort`를 받지 못하는 환경, 주 체크아웃의 옛 사본 갈래다.
- `/security-review`: 지적 없음. 설정 변경은 `enabledPlugins`에 `false`를 더한 것뿐이고 `permissions`·`hooks`는 그대로다.

## 다음

- 표준 축이 실제로 `sonnet`·`high`로 돌았는지(보고서 4절)와 넷의 스킬 목록이 0자인지(보고서 9절)는 티켓 09가 본다.
- `KICKOFF.md` 38행·334행에 프로젝트 `enabledPlugins`의 `false`로 플러그인을 끄는 길을 적을지는 retro 후보다(셀프 리뷰 절의 남긴 것).
