# 2026-10-11 (01) 명세 쪽 하네스와 pytest id

next-session 지시문으로 연 새 세션의 하네스 chore다. 대기열 56·103·105·106·114·121·125·126을 한 PR로 닫는다. 세션은 주
체크아웃에서 열렸고, 지시문대로 `tidy-checkouts`를 먼저 돈 뒤 `EnterWorktree(name=spec-pipeline-and-pytest-ids)`로 들어가
`origin/main`(`58969f7`, #166)에서 `chore/spec-pipeline-and-pytest-ids`를 땄다.

> 사용자: "대기열 106·121·125(.claude/agents/spec-reviewer.md), 103·105·126(.claude/skills/to-spec/SKILL.md), 114(.claude/skills/grilling/SKILL.md), 56(pyproject.toml의 pytest id)을 chore/spec-pipeline-and-pytest-ids 한 PR로 반영한다"

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했다. `f71e577`에서 `58969f7`로 당겼다. 스킬 파일은 바뀌지 않아 실린 사본 그대로 3을 돌았다.
- **지운 것.** 워크트리 열과 그 브랜치(`01-tokens-story-seam-and-buttons`, `02-visual-comparison-gate`,
  `03-status-badge-progress-card`, `04-text-field-switch-alert`, `canary-procedure-and-runner`,
  `llm-tokens-and-bot-review-rounds`, `review-axis-and-failure-reason`, `tidy-before-worktree`, `tidy-checkouts-tool`,
  `zizmor-workflow-audit`), 로컬 브랜치 둘(`chore/review-checkout-credentials`, `chore/review-owner-fallback`).
- **남긴 것.** 병합된 PR이 없는 워크트리 둘(`review-workflow-guards`, `rewrap-and-separator-hook`)과 `claude/*`·`worktree-*` 브랜치
  열넷.
- **사람에게 넘긴 것.** prunable `05-admin-hides-decision-for-end-user`, 분리 HEAD 셋(`confident-wright-2d3ebf`,
  `elegant-dijkstra-aaddb9`, `unruffled-lalande-9017fa`), PR 머리가 다른 `skill-check-and-retro-section`, 등록 없는 폴더
  여섯(대기열 148). 지시문대로 답을 기다리지 않았다.

## 어떻게 했나

- **56은 실패하는 테스트부터.** `tests/test_pytest_ids.py`가 한국어 매개변수 id가 node id에 그대로 있는지 단언한다. 설정 전에
  PowerShell에서 돌리자 id가 `\uXXXX` 꼴로 찍히며 빨갰고, 설정을 넣자 한글 그대로 찍히며 초록이었다. 함수 이름에
  없는 `-k 다른_자리`가 그 사례 하나를 골랐고, `-o`로 설정을 끄면 같은 선택이 비어 종료 코드 5였다(PowerShell과 Git Bash에서
  손으로 봤다). 처음에는 `request.node.name`을 읽었는데 pyright strict가 Unknown으로 보아(pytest의 `FixtureRequest.node`에
  반환 주석이 없다. 일지 2026-10-07-19와 같은 함정) pytest가 도는 테스트마다 채우는 `PYTEST_CURRENT_TEST`로 옮겼다. 옮긴 판도
  설정을 끄면 빨갛다. 변이 표들의 `-k`는 함수 이름만 고르므로(`.scratch/*/probes/*_mutations.toml`) 이 설정에 깨지지 않는다.
  셀프 리뷰의 두 축이 변이 표의 `-k` 200개를 설정을 켜고 끈 두 판으로 모아 견줬고, 고른 수가 바뀐 것은 없었다.
- **옵션이 제어 문자도 그대로 둔다.** 셀프 리뷰의 명세 축이 `run-1\n` id가 줄바꿈 그대로 찍히는 것을 찾았다. 전체를 수집해
  보니 그런 id가 여섯이었고(`test_run.py` 하나, `test_canary.py` 하나, `test_hook_env_read.py` 넷) 출력에서 모두 두 줄 이상으로
  갈렸다. 테스트마다 `ids`를 주지 않고 `tests/conftest.py`의 `pytest_make_parametrize_id`가 문자열 값의 인쇄되지 않는 문자만
  `\n` 꼴로 되돌린다. pytest는 훅이 돌려준 id를 이스케이프하지 않고 쓴다. 이것도 시험(`test_인쇄되지_않는_문자만_이스케이프한다`)을
  먼저 빨갛게 보고 넣었고, 넣은 뒤 다시 수집하니 `tests/`로 시작하는 줄이 수집 수 1874와 같았다.
- **106은 행의 "어디로" 두 자리.** `spec-reviewer` 체크리스트 6(제안하는 쪽)과 `to-tickets` 5단계(옮기는 쪽)다. 예시는
  과거형으로 적었다. 지금의 인증 미들웨어는 `Clock` 포트를 받는다(`src/agent_os/http/auth.py`). PyJWT가 벽시계를 읽는 것은
  설치본 `jwt/api_jwt.py`의 `datetime.now(tz=timezone.utc)`를 읽었다.
- **121은 체크리스트 7(자리표시자).** 문구가 서는 조건을 적지 않은 문장은 구현자에게 결정을 떠넘기는 것과 같은 모양이다.
- **125는 체크리스트가 아니라 질문 1의 측정 문장.** 넘긴 측정은 이미 질문 1이 다루고 있어, 같은 주제를 두 자리에 나누지
  않았다. 그래서 `spec-reviewer`의 "체크리스트 일곱과 질문 둘"은 그대로다.
- **103·105·126은 `to-spec`.** 103은 첫머리에, 105와 126은 3단계의 "명세를 쓴 뒤의 차례" 한 문장(셀프 리뷰 반영, 서두의 수
  세기, ADR 초안·이력의 승인, 커밋)으로 묶었다. 126의 2회차(일지 2026-10-07-17)는 `to-spec` 밖의 chore 세션이 쓴 ADR이었으므로
  행의 "어디로"가 든 `CLAUDE.md` 작업 규약 5도 고쳤다. 줄은 늘리지 않고 그 줄의 문구만 바꿨다. `domain-modeling`은 ADR을 권하는
  기준만 두고 초안을 보여 주는 단계가 없어 두었다.
- **114는 `CLAUDE.md` 원칙으로 넓혔다.** 행이 넓힐지를 반영하는 브랜치에 맡겼다. 처음에는 grilling 밖의 회차가 한 번(일지
  2026-10-06-09, next-session을 돌던 세션의 즉석 질문)이라 보고 grilling 라운드 문단만 고쳤는데, 셀프 리뷰의 표준 축이 둘을 더
  찾았다. 일지 2026-10-06-10의 anyio 길 셋과 2026-10-07-17의 zizmor 정책에서도 사용자가 "쉽게 설명해줘"로 되물었다. 셋 다 스킬의
  단계가 아닌 즉석 `AskUserQuestion`이라 둘 자리는 매 세션 실리는 `CLAUDE.md`뿐이고, 교정 루프의 세 번에 닿는다. 길 셋(`CLAUDE.md`
  한 줄, grilling만 두고 회고 후보, `AskUserQuestion` 계기 훅)을 보였다.

  > 사용자: (고른 것) "CLAUDE.md 한 줄 (Recommended)"

  세 토막(무엇인가·잡아 주는 것·치르는 값)의 원천은 원칙 절의 그 줄 하나이고, grilling은 호출 곁 본문에 풀이를 둔다는 자리만
  적고 그 줄을 가리킨다.

## 바꾼 것

- `pyproject.toml`(`disable_test_id_escaping_and_forfeit_all_rights_to_community_support`), `tests/conftest.py`의
  `pytest_make_parametrize_id`, 새 시험 `tests/test_pytest_ids.py`.
- `.claude/agents/spec-reviewer.md` 체크리스트 6·7과 질문 1, `.claude/skills/to-tickets/SKILL.md` 5단계와 머리 주석.
- `.claude/skills/to-spec/SKILL.md` 첫머리·3단계와 머리 주석, `CLAUDE.md` 작업 규약 5와 원칙 절(한 줄 늘었다).
- `.claude/skills/grilling/SKILL.md` 라운드 문단과 머리 주석.
- 프로브: 카나리아 명세 넷(`.scratch/harness/probes/canary/`의 `to_spec_new_session_and_order.toml`, `to_tickets_test_seam.toml`,
  `grilling_concept_gloss.toml`, `claude_md_adr_order_and_gloss.toml`), spec-reviewer 확인 스크립트
  `spec_reviewer_agent.py`, 그 README의 `canary/` 행.
- `.scratch/retro-queue.md`: 여덟 행 닫힘. 56의 옛 "무엇" 칸이 이스케이프된 출력을 한글로 적어 둔 것(`[다른 자리]`)을 `\uXXXX`
  꼴로 바로잡았다. 이 세션의 일지 초안도 도구 호출에 쓴 `\u` 열이 한글로 풀려 같은 모양이 됐고, 셀프 리뷰가 잡았다.

## 잔존 grep

`초안을 보여주고 승인`, `작업 규약 5`, 사본 머리 주석의 `…을 더했다`를 살아 있는 문서에서 찾았다(일지 제외). `CLAUDE.md` 지도 표의
`docs/adr/` 쓰는 때 칸("아키텍처 결정 뒤 초안을 보여주고 승인")은 차례를 말하지 않아 두었다. `code-review` 6단계 3의 "먼저
묻는다"는 고치기 전에 결정을 묻는 것이라 다른 차례다. `kickoff/claude-md-template.md`의 작업 규약 5는 다른 프로젝트가 복사하는
원본이고 그 3도 이 저장소의 세부를 줄여 두었다. 런북에 무엇을 옮길지는 이 PR의 범위 밖이라 고치지 않았다.

## 셀프 리뷰

`/code-review`(base `58969f7`, 바뀐 파일 8·미추적 6·커밋 0). 두 축 모두 기본 모델이다(`tests/`의 파이썬이 있다). 표준 축은 하드
위반 4·판단 항목 8, 명세 축은 빠짐 3·범위 추가 1·틀림 3이었다. 두 축이 따로 같은 셋을 짚었다.

- **고친 것.**
  - 114의 근거 "grilling 밖은 한 번"이 거짓이었다(위 "어떻게 했나"). 사용자에게 물어 `CLAUDE.md`로 넓혔다.
  - 56의 닫힘 표지가 아직 돌지 않은 CI를 과거형으로 적었다. 자리표시로 두고 PR의 CI를 본 뒤 채운다.
  - 일지 초안의 이스케이프 표기가 한글로 풀려 있었다(위 "바꾼 것").
  - spec-reviewer를 재는 확인이 저장소에 없었다. 스크래치의 스크립트를 `spec_reviewer_agent.py`로 옮겨 커밋하고 README에 적었다.
  - 옵션이 제어 문자도 그대로 둔다(명세 축, 위 "어떻게 했나"). `conftest.py`의 훅과 시험을 더했다.
  - `to-spec` 첫머리의 "무엇이 맥락을 대신했는지 명세 서두에 적는다"는 103 행에 없는 지시라 뺐다. 병합하면 낡는 "지금까지는
    지시문이 실어 왔다"도 뺐고, 영어 원문을 우리말로 바꿔 따옴표에 넣은 둘은 원문(`Do NOT interview the user`, `current
    conversation context`)으로 고쳤다. 126 문장은 `CLAUDE.md` 작업 규약 5를 가리키는 데서 그쳤다.
  - `pyproject.toml` 주석의 "-k 선택이 빈다"를 매개변수 id로 고른 선택으로 좁혔다. 시험은 `PYTEST_CURRENT_TEST`의 끝 모양
    `(call)`에 기대지 않게 바꿨다.
  - `CLAUDE.md` 카나리아는 상위 폴더의 옛 `CLAUDE.md`가 함께 실릴 수 있어, 통과와 실패를 읽는 법을 명세 머리에 적었다.
- **남긴 것.**
  - spec-reviewer 체크리스트 6과 `to-tickets` 5단계가 같은 규칙과 일화를 되풀이한다(표준 축 7). 행이 제안하는 쪽과 옮기는 쪽
    둘을 요구했고, 서브에이전트와 스킬은 한 컨텍스트에 함께 실리지 않아 서로를 대신하지 못한다.
  - `code-review` 6단계 3이 새 작업 규약 5를 가리킨다(표준 축 8). 그 단계는 고치기 전에 결정을 묻는 것이고, 초안은 반영 단계에서
    쓰므로 "리뷰를 반영한 뒤에 보여 준다"와 어긋나지 않는다.
  - spec-reviewer 6의 "이 검토가 제안한"(표준 축 9). 일지 2026-10-05-04가 그 문구를 명세 검토 주석으로 적었고, 명세 검토는
    `to-tickets` 1단계가 이름 붙인 `spec-reviewer`다. "세 번째"는 행대로 검토의 문구를 옮긴 실수의 회차다.
  - 125를 체크리스트가 아니라 질문 1에 둔 것(명세 축 a3). 행의 "무엇"은 충족하고, PR 본문에 적어 사용자 확인을 받는다.
  - 이스케이프를 전제한 변이 표의 주석 둘(`pause_index_mutations.toml`, `limits_mutations.toml`)은 끝난 기능의 프로브라 기록으로
    두었다(명세 축).

## PR 직전 보안·버그·성능 축

CodeRabbit CLI는 이번에도 `Seat: not assigned`라 대체 둘을 나란히 돌렸다(커밋 `706f1e0` 기준).

- **보안(`/security-review`).** 지적 없음. 프로브 스크립트의 `subprocess.run`은 고정 인자에 `shell=True`가 없고, 테스트 설정과
  문서는 제외 범주다. spec-reviewer의 도구 목록은 바뀌지 않았다.
- **버그·성능(`bug-perf-review`).** 턴 한도에서 보고 없이 멈춰 보고만 내 달라고 이어 붙였다. 유효 셋·보류 하나였고 셋을 고쳤다.
  - 옵션이 켜지면 pytest가 바이트 값을 문자열로 바꾸지 않아 `"-".join`에서 `TypeError`로 수집이 죽는다. 지금 스위트에는 바이트
    매개변수가 없어 드러나지 않았다. 시험(`test_바이트_값도_이스케이프해_id_로_쓴다`)으로 그 수집 오류를 먼저 보고, 훅이 바이트
    값을 언제나 `\xff` 꼴의 문자열로 바꾸게 했다. 인쇄 가능한 바이트도 기본 길로 보내면 같은 자리에서 죽으므로 훅이 맡는다.
  - 훅은 손으로 준 id(`ids=`의 목록과 함수, `pytest.param(id=...)`)를 보지 못한다. 지금은 그런 id가 모두 한 줄이라 막지 않고
    `conftest.py` 독스트링에 적었다.
  - 확인 스크립트가 `tools/canary.py`가 막은 자리를 다시 열어 두었다. 잘린 줄에서 죽고, 제한 시간에 남은 회차를 버리고, init의
    도구와 서버를 보지 않아 본 세션이 정의를 읽어 옮긴 답이 통과할 수 있었고, 서브에이전트 이벤트가 없어도 도구 판정이 비어
    통과했다. 모두 판정에 넣고, 돌리기 전에 두 사본의 카나리아를 보아 대조군이 새 사본이면 종료 2로 막고, stderr도 남긴다.
    `claude` 없이 판정만 돌려 보니 앞서 429로 끝난 원본에서 실패 이유 다섯을, 잘린 줄에서 JSON 오류를 냈다.
  - 보류: 대기열의 자리표시(`CI_자리표시`, `카나리아는_자리표시`). 원래 CI와 카나리아를 본 뒤 채울 자리다.

## PR

[njh6803/agent-os#172](https://github.com/njh6803/agent-os/pull/172). 첫 푸시(`92f48f2`)의 CI는 python·web·e2e·visual·verify가
초록이었다. python 잡(Ubuntu 24.04)은 1875 passed로 id 시험 셋이 리눅스에서도 통과했고, 대기열 56의 CI 자리를 이것으로 채웠다.
claude-review는 23초 만에 빨갰고, 로그의 `rate_limit_event`가 `seven_day`, 결과가 "You've hit your weekly limit · resets 9pm
(UTC)"였다. 카나리아와 같은 계정 한도다(대기열 165의 길). CodeRabbit은 `92f48f2`까지 보고 고칠 지적 없이 끝났고, 보안 구조
검토는 Low였다. 그 하드닝 제안(서브에이전트의 도구 금지를 실행 전에 강제하고 실제 권한을 확인한다)은 따르지 않았다. 확인
스크립트는 보안 경계가 아니라 실린 정의를 보는 탐침이고, 서브에이전트가 도구를 부르면 판정이 실패로 잡는다.

처음에는 한도가 풀린 뒤(2026-10-12 06:00 KST) 카나리아를 돌려 통과하면 병합하기로 했다(위 114와 같은 질문 묶음에서 사용자가 골랐다).
CI 결과를 보고한 뒤 사용자가 병합을 먼저 골랐다. 15:47에 다시 보니 자식 `claude -p`는 여전히 429였다.

> 사용자: "병합해줘"

그래서 카나리아 넷과 spec-reviewer 확인 스크립트는 병합 뒤 한도가 풀리면 돌리는 후속으로 남기고, 대기열 일곱 행의 닫힘 표지에
그렇게 적었다. 작업 규약 3의 실행 확인이 없는 채로 병합하는 하네스는 그 결과가 나올 때까지 확인되지 않은 것이다. claude-review도
같은 한도로 빨간 채 병합한다.

## 검사

- 검증 명령: `uv run pytest -q` 1873 passed(7 deselected. 경고 5건은 `tests/test_conftest.py`가 pytester로 띄운 안쪽 세션의
  pytest-asyncio 폐기 예고다), `ruff check`·`ruff format --check`, `pyright` 0 errors(첫 판에서 이 시험 파일에 오류를 냈으니 그
  파일을 분석한다), `lint-imports` 5 kept. web은 건드리지 않았다. 셀프 리뷰를 반영한 뒤 모두 다시 돌렸고 pytest만 1874 passed(제어
  문자 시험 하나를 더했다)로 바뀌었다. PR 직전 리뷰를 반영한 뒤에도 다시 돌려 1875 passed(바이트 시험 하나를 더했다)였다. 지침
  검사와 타입 우회 검사도 초록이고, 표·줄 구분 문자·인용 검사는 바뀐 파일을 인자로 넘겨 돌렸다(인용 경고 둘은 106 행의 옛 후보
  문장이라 두었다).
- 카나리아 명세 넷은 `tools/canary.py`의 돌리기 전 확인(`_preflight`)을 통과했고, spec-reviewer 스크립트의 카나리아 셋은 새
  사본에만 있다(옛 사본은 `origin/main`에서 꺼내 셌다).
- 카나리아: 처음 돌린 넷이 모두 실패했다. 본문 탓이 아니라 자식 `claude -p`가 첫 요청에서 429였다. 원본의
  `rate_limit_event`는 `rateLimitType: seven_day`, 사용률 1, 초과 사용 거절(`out_of_credits`)이었고, haiku로도 같은
  `usage_limit_reached`였다. 풀리는 시각은 2026-10-12 06:00 KST(21:00 UTC)다. 15:31과 15:47에 다시 쳐도 429였다.

## 회고

후보 넷을 냈고 넷 모두 승인됐다. 이 PR에서는 반영하지 않았다.

> 사용자(질문에 답): "1 한도 때의 길 (165 넓힘), 2 에이전트 갈래 (153 회차), 3 \u 열이 한글로 풀림 (새 행), 4 리뷰 에이전트 턴 한도 (새 행)"

1. **계정 한도가 `claude -p`를 막을 때의 길이 없다 → 대기열 165(2회차, 범위를 넓혔다).** 165는 claude-review만 다뤘는데, 이번에는
   같은 `seven_day` 한도가 카나리아도 막아 작업 규약 3의 실행 확인을 언제 할지 두 번 물었다(114와 묶은 질문, 그리고 병합).
2. **에이전트 갈래가 없어 확인 스크립트를 또 손으로 지었다 → 대기열 153(2회차).** 이번 스크립트는 `tools/canary.py`가 막아 둔
   거짓 통과 자리 셋(잘린 줄, 제한 시간, init의 도구·서버)을 다시 열어 두었고, 그 도구에도 없는 넷째(서브에이전트 이벤트가 없으면
   도구 판정이 빈다)까지 PR 직전 리뷰가 찾았다.
3. **도구 호출에 쓴 역슬래시 u와 16진 네 자리가 파일에서 그 글자로 풀린다 → 대기열 168(새 행, 2회차).** 일지 초안의 이스케이프된
   id가 한글 id로 들어갔다. 앞 세션의 대기열 56 행도 같은 모양이었다.
4. **`bug-perf-review`가 턴 한도에서 보고 없이 멈췄다 → 대기열 169(새 행, 1회차).**

번호는 `tools/sibling_overlap.py`로 대조한다(커밋 직전).

일지에만 남기는 것:

- 114의 근거 "grilling 밖은 한 번"을 대기열이 적어 둔 회차로 닫았다. 일지를 낱말("쉽게 설명해줘")로 찾지 않았다. 셀프 리뷰 브리프의
  주장 검증 1(닫힌 주장)이 시킨 대로 표준 축이 반례 둘을 찾았다.
- 스크래치 스크립트의 `Path.write_text`가 Windows에서 `\n`을 CRLF로 바꿔 대기열 파일의 줄 끝을 바꿨다. `git diff`의 경고로 알았고
  바이트로 되돌렸다.
- 도구 호출 사이의 문장을 영어로 쓴 것을 훅이 네 번 짚었다. 반복문 속 `git show`를 워크트리 가드가 거부했고, Git Bash가
  `origin/main:<경로>`를 Windows 경로로 바꿔 PowerShell로 옮겼다(둘 다 알려진 함정이다).

## 다음

- **카나리아 후속(이 PR의 남은 확인).** 2026-10-12 06:00 KST 뒤에 2026-10-11에 더한 명세 넷과 `spec_reviewer_agent.py`를 돌린다.
  병합 뒤의 대조군은 README `canary/` 행이 적는다. 결과를 그 행과 대기열 103·105·106·114·121·125·126의 닫힘 표지에 적고, 실패한
  것은 그 하네스를 고친다.
- 그 뒤는 일지 2026-10-07-12의 "다음"이 남긴 묶음을 다시 센다.
- 병합은 워크트리에서 해 주 체크아웃은 당기지 않는다. 주 체크아웃 미갱신: 루트는 main.
