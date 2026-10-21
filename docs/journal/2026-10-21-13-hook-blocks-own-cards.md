# 2026-10-21 (13) 모델이 스스로 내는 세션 카드를 훅이 막는다

브랜치 `feature/06-hook-blocks-own-cards`, 티켓 `.scratch/ticket-for-every-pr/issues/06-hook-blocks-own-cards.md`. 기능
`ticket-for-every-pr`의 티켓 일곱 가운데 나란히 여는 셋의 둘째다(일지 2026-10-21-07의 "다음").

## 요청

> 사용자: /implement .scratch/ticket-for-every-pr/issues/06-hook-blocks-own-cards.md

범위는 지시문의 "PR과 병합까지"다. 지시문대로 주 체크아웃에서 브랜치를 따지 않고 `EnterWorktree`(이름
`06-hook-blocks-own-cards`)로 들어가 브랜치 이름을 바꿨다. 묶음의 첫 세션이 아니라 `tidy-checkouts`는 돌지 않았다.

훅을 `.claude/settings.json`에 등록하기 전에 티켓대로 선택 화면으로 허락을 물었다. 사용자는 선택지가 아닌 "Something
else"로 답한 뒤 요청을 끊고 말로 답했다.

> 사용자: 등록해

## 한 것

- 첫 편집으로 티켓의 `Status:`를 `in-progress`로 바꿨다.
- 시험 먼저. `tests/tools/test_hook_session_card.py`를 쓰고, 아무것도 내지 않는 첫 판의 훅으로 `own_initiative` 사례만 빨간 것을
  봤다(일곱 가운데 하나 실패). 나머지 여섯(`user_asked`, `offer`, `proposal_id`만 든 시작, JSON이 아닌 입력, `tool_input`이 객체가
  아닌 입력, 최상위가 객체가 아닌 입력)은 침묵을 단언해 첫 판에서도 초록이다.
- 훅 `tools/hook_session_card.py`. 매처는 `mcp__ccd_session__start_session` 하나이고 `tool_input.initiation`이
  `own_initiative`이면 deny와 까닭의 글(일지의 "다음"이나 대기열 행으로 적는다, `user_asked`·`offer`로 바꿔 다시 부르지 않는다,
  ADR 0037)을 낸다. pyright strict가 `dict`로 좁힌 값의 Unknown을 잡아, 다른 훅처럼 TypedDict와 JSON 값의 합 타입으로 받았다.
- 등록. 사용자의 허락 뒤 `.claude/settings.json`의 PreToolUse에 래퍼 모양으로 더했다.
- 실제 입력 표. 발동과 `proposal_id` 침묵은 카드 탐침의 훅 기록 둘째·셋째 줄 그대로이고, `user_asked` 침묵은 탐침이 부르지 않아
  발동 입력의 `initiation`만 바꿔 재구성했다(표의 note에 적었다).
- 러너가 잡은 결함. `tools/run_hooks.py`가 발동 사례를 `exit 1`로 냈다. 훅 환경에 `PYTHONUTF8`이 없어 표준 출력이 cp949인데
  `ensure_ascii=False`로 낸 까닭 글의 `—`를 쓰지 못해 예외로 끝났다. PreToolUse의 예외는 막지 않고 지나가므로(fail-open), 그대로
  병합했으면 훅이 조용히 아무것도 막지 않았다. 출력을 ASCII 이스케이프로 바꾸고, 출력이 ASCII인지 단언하는 시험을 더했다.
  그 시험이 `ensure_ascii=False`인 판에서 빨간 것은 아래 검사의 변이로 봤다.
- 문서. `KICKOFF.md` 훅 목록에 이 훅과 그 이유, 막는 훅의 무리(ADR 0037이 막기로 정한 것), 바꿀 곳(앱의 세션 카드 도구를 쓰는
  프로젝트에만)을 더했다. `.claude/rules/tools.md` 훅 시간 문단에 이 훅이 붙는 도구와 어림한 시간(약 0.2초)을 적었다.
- 카나리아. `.scratch/harness/probes/canary/tools_rule_session_card_hook.toml`을 새로 뒀다.

## 검사

- 카나리아: 첫 번은 카나리아에 훅 이름을 두어, 도구가 그 이름이 git 상태의 새 파일 경로에 있다며 돌리기 전에 멈췄다. 규칙
  문장에만 있는 구절로 바꾼 둘째 번이 통과 4였다(실험군 3/3, 대조군 "없음" 셋, `303e8fb5` 위의 커밋 전 작업 트리).
- `uv run python tools/run_hooks.py`: 훅 페이로드 140건, 어긋남 0건.
- 변이(`.scratch/ticket-for-every-pr/probes/session_card_hook_mutations.toml`): 다섯 모두 기대대로 빨갰다. 구현 뒤에 쓴 ASCII
  시험과, 첫 판부터 초록이던 침묵 시험 넷(JSON이 아닌 입력, 최상위와 `tool_input`이 객체가 아닌 입력, `user_asked`)의 빨강이다.
- `ruff check .`·`ruff format --check .` 깨끗. `uv run python tools/run_checks.py` 여덟 검사 모두 Passed(pytest 309.8초,
  web-verify 398.5초).

## 인계 (셀프 리뷰 직전)

`/code-review`를 부른 직후 세션 컨텍스트가 약 25.5만 토큰으로 문턱을 넘은 채 `셀프 리뷰 직전` 경계에 와서 인계 계기가 왔다.
인계하지 않는 때 다섯에 들지 않았다(곁 세션 아님: `get_session`의 `self`에 `parentSessionId`가 없다). 이 세션의 제목은
`feature/06-hook-blocks-own-cards`였고 `feature/06-hook-blocks-own-cards (인계함)`으로 바꾼다.

- 결정: 등록은 사용자의 "등록해"로 했다. 실제 입력 표의 `user_asked` 침묵은 탐침이 그 호출을 부르지 않아 재구성했다(note에 적었다).
  카나리아 낱말은 git 상태의 새 파일 이름과 겹치지 않는 규칙 문장의 구절로 골랐다.
- 번복한 것: 출력의 `ensure_ascii=False`를 러너가 cp949 예외로 잡아 되돌렸다(위 "한 것"). 일지에 처음 "손으로 봤다"고 적은
  ASCII 시험의 빨강을 변이로 다시 봐 고쳐 적었다.
- 커밋은 없다. 셀프 리뷰는 돌지 않았다(두 축의 서브에이전트를 띄우기 전에 넘긴다).
- 남은 일: `/code-review` 셀프 리뷰(base `303e8fb5`, 추적 변경 여섯, 미추적 다섯, 명세 축의 기준은 티켓 06과 명세 "카드 막는 훅"),
  반영, 커밋 직전의 `sibling_overlap.py`(이 일지 순번 13이 아직 다음 빈 번호와 맞는지), 커밋, 티켓의 "실제 세션의 확인"(사람이 이
  워크트리 폴더에서 새 앱 세션을 열어 `own_initiative`가 막히고 `user_asked`나 없는 `proposal_id`가 막히지 않는지 본다. 결과는
  `probes/README.md`와 이 일지에), PR 직전 리뷰, 푸시, PR, 봇 회차, 워크트리에서 병합하는 길. PR 전에 티켓 `Status:`를 `done`으로.
- 확인하지 못한 것: 래퍼와 `settings.json` 등록으로 실제 앱 세션에서 막히는지(위 실제 세션의 확인).
- open-session을 부른다 2026-10-21T12:39:14Z

## 셀프 리뷰 (이어받은 세션)

> 사용자: (지시문) 다음 작업: .scratch/ticket-for-every-pr/issues/06-hook-blocks-own-cards.md. 모델이 스스로 내는 세션 카드를 훅이 막는다. 구현은 끝났고 셀프 리뷰부터 잇는다

지시문대로 주 체크아웃에서 `tidy-checkouts`를 먼저 돌았다. 루트를 `303e8fb5`에서 `f1e6516b`(#340)로 당겼고, 브랜치
`worktree-01-harness-ticket-numbers`를 지웠다. 휴지통의 `01-mcp-2-and-cli-interrupt~~web%2Fnode_modules`는 그것을 올린 프로세스
(node.exe, esbuild.exe 둘) 때문에 남았다. 워크트리는 모두 남겼다(병합된 PR이 없거나 쥔 프로세스가 있거나 앱의 표지).

`/code-review` base `303e8fb5`, 추적 변경 여섯, 미추적 다섯, 커밋 0. 두 축 모두 Critical·Major 0이다. 표준 축 Minor 3·Nit 6,
명세 축 Minor 3·Nit 4.

- 고친 것.
  - 두 축: 못 보는 것 셋째(다른 세션 도구)를 고정한 시험이 없다(`.claude/rules/tools.md` 못 보는 것 항목). 시험
    `test_다른_세션_도구와_이름이_바뀐_도구는_보지_않는다`를 `tools.run_hooks.registered_matchers`로 더했다(선례
    `test_hook_bash_msys_pathconv.py`). 처음부터 초록이라 변이 파일에 매처를 `.*__start_session`으로 넓히는 여섯째 변이를
    더해 빨강을 봤다(변이 여섯 모두 기대대로).
  - 명세 축: `KICKOFF.md`의 새 분류 "ADR(0037)이 막기로 정한 것"이 `.claude/rules/tools.md`의 "예외는 둘이다"와 갈린다. 둘째
    예외로 합쳤다. 새 문장: "`hook_session_card`(PreToolUse 계기는 그 호출의 결과와 함께 닿으니 카드가 뜬 뒤라고 어림한다.
    결과와 함께 닿는 것을 잰 도구는 AskUserQuestion이다. 사용자가 막기를 고른 것은 ADR 0037)".
  - 명세 축: 독스트링 측정 절의 판 "Claude Code 2.1.299"가 측정처럼 적혔다. 새 문장: "판은 Claude Code 2.1.299 로, 출력이
    아니라 탐침 세션 기록에서 손으로 봤다". 같은 축 Nit의 "화면에 카드가 생기지 않는다"를 "카드는 만들어지지 않는다(아래
    측정에서 카드 id 가 없었다)"로 좁혔다.
  - 표준 축: `hook_payloads.toml`의 `user_asked` note가 `tool_use_id`를 지은 것을 빠뜨렸다. 새 note: "위 발동 입력의 initiation
    을 바꾸고 background 를 빼고 tool_use_id 를 지었다(재구성)". 머리 주석에 "그 기록은 tool_name·tool_use_id·tool_input 만
    남겨, session_id 같은 나머지 필드는 없다"를 더했다.
  - 표준 축 Nit: 프로브 README 변이 행의 "몇 초"를 "시간은 재지 않았다"로, 결과를 "변이 여섯 모두 기대대로(다섯은 셀프 리뷰
    전에, 매처 변이를 더한 여섯은 셀프 리뷰 반영 뒤에 돌렸다)"로 고쳤다.
- 남긴 것.
  - 표준 축 Minor 3(까닭의 글이 사용자가 시켰는데 `own_initiative`로 잘못 적은 갈래를 말하지 않는다): 글은 명세 "까닭의 글"이
    정한 요소 그대로이고, 괄호의 "그 값은 사용자가 말로 새 세션을 시켰거나 … 때만 쓴다"가 그 갈래를 연다. 명세 축도 같은 갈래를
    어긋남으로 보지 않았다.
  - Nit: `JsonValue` 이름(다른 훅의 TypedDict 합 관례), `ensure_ascii` 주석 없음(시험 독스트링이 지킨다), `KICKOFF.md` 매처 나열
    (이미 여럿 빠졌고 settings.json이 원천이라 적었다), 변이 2의 문자열 사례, 카나리아의 "약 0.2초" 기대와 머리 주석의 "(위
    둘째 줄)", 변이 5의 `-k`가 `offer`도 고른다는 것(그 회차에 빨개진 것은 `user_asked` 하나였다), 스토리 38의 `offer` 우회.
- 다시 돌린 명령: `tests/tools/test_hook_session_card.py` 9 통과, 변이 여섯 기대대로. 나머지 손으로 치는 다섯은 커밋의
  pre-commit으로 갈음한다(결과는 커밋 뒤에 적는다).
