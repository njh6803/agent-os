# 2026-10-22 (01) 모델이 스스로 내는 세션 카드를 훅이 막는다

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
    정한 요소 그대로이고, 괄호의 "그 값은 사용자가 말로 새 세션을 시켰거나 사용자에게 물을 때만 쓴다"가 그 갈래를 연다. 명세 축도 같은 갈래를
    어긋남으로 보지 않았다.
  - Nit: `JsonValue` 이름(다른 훅의 TypedDict 합 관례), `ensure_ascii` 주석 없음(시험 독스트링이 지킨다), `KICKOFF.md` 매처 나열
    (이미 여럿 빠졌고 settings.json이 원천이라 적었다), 변이 2의 문자열 사례, 카나리아의 "약 0.2초" 기대와 머리 주석의 "(위
    둘째 줄)", 변이 5의 `-k`가 `offer`도 고른다는 것(그 회차에 빨개진 것은 `user_asked` 하나였다), 스토리 38의 `offer` 우회.
- 다시 돌린 명령: `tests/tools/test_hook_session_card.py` 9 통과, 변이 여섯 기대대로. 나머지 손으로 치는 다섯은 커밋의
  pre-commit으로 갈음했다. 커밋 `949fcbba`의 pre-commit은 모두 Passed(pytest 545.3초, 헌법 판은 고친 파일이 없어 Skipped).
  인용 대조 경고 1건(이 절의 줄임표 인용)은 커밋 뒤 원문 그대로 고쳤다.
- PR 직전 리뷰에 밀 주장(셀프 리뷰 반영으로 새로 쓴 문장): 위 "고친 것"의 새 문장 다섯(`KICKOFF.md`의 `hook_session_card`
  괄호, 독스트링의 판과 "카드는 만들어지지 않는다", `hook_payloads.toml`의 note와 머리 주석, 프로브 README의 변이 행).

## 인계 (커밋 뒤)

커밋 `949fcbba` 직후 세션 컨텍스트가 약 21.8만 토큰으로 문턱을 넘은 채 `커밋 뒤` 경계에 와서 인계 계기가 왔다. 인계하지 않는 때
다섯에 들지 않았다(넘겨받은 경계는 `셀프 리뷰 직전`이라 같지 않고, 요청 범위는 PR과 병합까지다). 이 세션의 제목은
`feature/06-hook-blocks-own-cards`였고 `feature/06-hook-blocks-own-cards (인계함)`으로 바꾼다.

- 커밋 뒤에 고친 것(커밋하지 않음): 이 일지의 셀프 리뷰 절 끝과 이 절. 새 세션이 다음 커밋에 싣는다.
- 남은 일: 티켓의 "실제 세션의 확인"(사람이 이 워크트리 폴더에서 새 앱 세션을 열어 `own_initiative`가 막히고 `user_asked`나
  없는 `proposal_id`가 막히지 않는지 본다. 결과는 `probes/README.md`와 이 일지에), 티켓 `Status:`를 `done`으로, PR 직전 리뷰
  (위 밀 주장 포함), 푸시, PR, 봇 회차, 워크트리에서 병합하는 길.
- 확인하지 못한 것: 래퍼와 `settings.json` 등록으로 실제 앱 세션에서 막히는지.
- 지시문:

```
다음 작업: .scratch/ticket-for-every-pr/issues/06-hook-blocks-own-cards.md. 모델이 스스로 내는 세션 카드를 훅이 막는다. 커밋은 됐고 실제 세션의 확인과 PR부터 잇는다
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리다. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/ticket-for-every-pr/issues/06-hook-blocks-own-cards.md
브랜치: feature/06-hook-blocks-own-cards
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-22-01-hook-blocks-own-cards.md 의 "인계 (커밋 뒤)" 절
이어받을 상태: 인계: 커밋 뒤. 커밋 949fcbba까지 구현과 셀프 리뷰 반영을 마쳤고 열린 PR은 없다. 일지의 커밋 뒤 수정은 커밋하지 않았다. 남은 단계는 실제 세션의 확인(사람이 이 워크트리 폴더에서 새 앱 세션을 연다), 티켓 Status done, PR 직전 리뷰(일지의 밀 주장), 푸시, PR, 봇 회차, 워크트리에서 병합. docs/journal/2026-10-22-01-hook-blocks-own-cards.md
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

- 잠금 풀기: `is not locked`라 넘어갔다.
- open-session을 부른다 2026-10-21T13:15:09Z

## PR 직전 리뷰 (이어받은 둘째 세션)

> 사용자: (지시문) 다음 작업: .scratch/ticket-for-every-pr/issues/06-hook-blocks-own-cards.md. 모델이 스스로 내는 세션 카드를 훅이 막는다. 커밋은 됐고 실제 세션의 확인과 PR부터 잇는다

지시문대로 주 체크아웃에서 `tidy-checkouts`를 먼저 돌았다. 루트는 이미 `origin/main`(`14efe41d`)과 같아 당기지 않았다. 쉬는
세션만 쥔 병합된 워크트리 둘(`02-boundary-exceptions`, `ticket-for-every-pr-to-tickets`)은 `end-holders`로 그 세션을 끄고
브랜치와 함께 지웠다. 휴지통의 `node_modules` 셋(`01-mcp-2-and-cli-interrupt`, `ticket-for-every-pr-to-spec`,
`ticket-for-every-pr-to-tickets`)은 그것을 올린 프로세스(node.exe, esbuild.exe) 때문에 남았다. 나머지 워크트리는 병합된 PR이
없거나, 다른 세션의 프로세스가 쥐었거나, 앱의 표지가 있어 남겼다.

- `origin/main`을 합쳤다(병합 커밋 `00e4df47`, 충돌 없음). `sibling_overlap.py`는 0으로 끝났고, 이 일지 순번 13은 겹치지 않는다.
- CodeRabbit CLI는 `Seat: not assigned`라 대체 둘을 돌렸다.
  - `/security-review`: 취약점 없음. 훅 명령은 다른 등록과 같은 모양이고 입력이 명령줄에 닿지 않으며, 출력은 상수 글뿐이다.
  - `bug-perf-review`: Critical·Major 0. 보류 Minor 2(`initiation` 값을 대소문자·공백 정규화 없이 견준다, `tool_input`이 JSON
    문자열로 오면 지나간다. 둘 다 실제 입력은 enum 문자열과 객체였다), 유효 Nit 1(다른 세션 도구를 보지 않는다는 것을 매처
    값으로만 지키고 `output_for`가 `tool_name`을 보지 않는다는 단언이 없다). 고치지 않았다. PR 체크리스트의 그 줄에 판정과 값을
    적는다(고치는 값: Minor 둘은 각각 시험 하나와 한 줄, Nit은 시험 하나).
- 실제 세션의 확인은 하지 못했다. 사람에게 이 워크트리 폴더에서 새 앱 세션을 열고 붙여 넣을 글(아래 지시문의 "확인할 선행
  조건")을 건넸는데, 그 결과가 오기 전에 주간 한도 95% 초과로 인계 요청이 왔다(세션 "주간한도 95% 초과 시 세션 전환"의 메시지).

## 인계 (한도 전환)

주간 한도가 95%를 넘어 다른 계정으로 넘기라는 메시지를 받았다. 새 단계를 시작하지 않고 이 일지를 커밋해 푸시하고 멈춘다. PR은
열지 않았다. 이 세션의 제목은 `feature/06-hook-blocks-own-cards`이고 `feature/06-hook-blocks-own-cards (인계함)`으로 바꾼다.

- 남은 일: 실제 세션의 확인(결과를 `probes/README.md`와 이 일지에), 티켓 `Status:`를 `done`으로, 위 리뷰의 Nit·보류 Minor를
  고칠지 정하기(고치면 셀프 리뷰를 짧게 다시), PR(체크리스트에 위 리뷰 결과), `@coderabbitai review`, 봇 회차, 워크트리에서 병합.
- 남은 위험: 래퍼와 `settings.json` 등록이 실제 앱 세션에서 막는지 아직 보지 않았다. 막지 않으면 훅은 조용히 아무것도 막지 않는다.
  `.claude/rules/tools.md`·`.claude/settings.json`·`tools/hook_payloads.toml`을 함께 고친 형제 PR(#296, #297)과 워크트리
  (`bug-perf-review-batch`, `measure-word-hook`)가 있어, 뒤에 병합하는 쪽에서 글자 충돌이 날 수 있다.

## 실제 세션의 확인 (이어받은 셋째 세션)

> 사용자: (지시문) 다음 작업: .scratch/ticket-for-every-pr/issues/06-hook-blocks-own-cards.md. 모델이 스스로 내는 세션 카드를 훅이 막는다. 푸시는 됐고 실제 세션의 확인과 PR부터 잇는다

지시문대로 `EnterWorktree(path)`로 이 워크트리에 들어왔다. 이 세션은 주 체크아웃에서 시작해 그 `settings.json`(이 등록이 없다)으로
떴으므로 여기서는 훅을 볼 수 없었다. 확인할 세션을 누가 열지 선택 화면으로 물었고, 사용자는 아래를 골랐다.

> 사용자: 제가 대신 엽니다 (Recommended) — 제가 그 폴더를 작업 위치로 지정해 새 세션을 바로 시작하고 확인 절차를 보냅니다. 사이드바에 세션 한 줄이 생기고, 그 세션이 끝나면 결과가 이 세션으로 돌아옵니다.

`start_session`(`user_asked`, `cwd`는 이 워크트리 폴더)으로 확인 세션을 열어 정해 둔 호출 둘을 시켰다(아래 양성 대조의
하나는 결과를 보고 더 시켰다).

- `own_initiative`: 결과가 `PreToolUse:mcp__ccd_session__start_session hook error: ` 뒤에 이 훅의 까닭 글 그대로였고 카드 id가
  없었다. 래퍼와 `settings.json` 등록이 실제 앱 세션에서 막는다.
- 양성 대조: `proposal_id`만 든 호출 둘에 훅 머리말이 없었다. 첫 값 `task_doesnotexist0`은 앱의 형식 검사에서 거절되어, 형식에
  맞춘 `task_00000000`으로 한 번 더 시켰고 앱이 `No pending proposal …`으로 거절했다.
- 결과는 `.scratch/ticket-for-every-pr/probes/README.md`의 "2026-10-22 결과: 실제 카드 훅의 새 세션 확인"에 적었다. 티켓
  `Status:`를 `done`으로 바꿨다.
- PR 직전 리뷰의 보류 Minor 2와 유효 Nit 1은 고치지 않고 PR 체크리스트에 판정과 고치는 값을 적는다(둘째 세션의 판정 그대로).

- 셀프 리뷰: `/code-review` base `39d4731d`, 미커밋 파일 셋, 미추적 0, 커밋 0. 두 축 모두 Critical·Major 0이다.
  - 고친 것: 두 축이 함께 짚은 Minor(README의 "정해진 호출 셋"은 결과를 보고 하나를 더 시킨 것과 어긋난다)를 "정해 둔 호출 둘을 한 번씩
    부르고, 둘째가 형식 검사에 걸려 형식에 맞춘 호출 하나를 더 시켰다"로 고쳤다. 표준 축의 판단 거리 넷도 고쳤다. 인용이 확인 세션의
    보고를 거친 이차 근거라는 것과 그 세션 id, 양성 대조가 "훅이 돌지 않았다"와 갈리지 않는다는 것과 그래도 앞의 해석을 고르는 까닭,
    주 체크아웃 등록이 없다는 문장의 시점(2026-10-22), 선택 화면의 답을 `> 사용자:` 인용으로. 명세 축 Nit으로 티켓의 체크 줄에
    사용자가 대신 열기를 골랐다는 괄호를 더했다.
  - 남긴 것: 앞 절 "못 본 것"에서 새 절로 가는 되돌림 표시(Nit). 그 절은 2026-10-21 결과의 기록이라 고치지 않는다.
  - 다시 돌린 명령: 문서만 고쳐 커밋의 pre-commit으로 갈음한다.
  - PR 직전 리뷰에 밀 주장: README 새 절의 고친 문장 셋("정해 둔 호출 둘을 … 하나를 더 시켰다", "아래 인용은 그 보고에서 옮긴 이차
    근거다", "매처는 도구 이름만 보므로 앞의 해석을 고른다"). PR 직전 리뷰는 둘째 세션이 끝냈고 이 변경은 문서뿐이라 다시 돌지 않고 PR 봇
    회차에 맡긴다.
