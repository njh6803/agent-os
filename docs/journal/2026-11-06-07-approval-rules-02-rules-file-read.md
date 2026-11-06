# 2026-11-06 (07) approval-rules 02 규칙 파일 읽기: 도구 이름의 별표는 패턴이다

## 시작

> 사용자: 다음 작업: .scratch/approval-rules/issues/02-rules-file-read.md. 운영자의 rules.toml을 플러그인 포트의 read_rules()로 읽어 core의 불변 값 Rules로 만든다 / 다음 단계: 구현 / 어디서: 새 세션 … 시작 프롬프트: /implement .scratch/approval-rules/issues/02-rules-file-read.md / 브랜치: feature/02-rules-file-read / 모델: Sonnet 5.5 / high / 읽을 것: docs/journal/2026-11-06-05-approval-rules-contract-trace-fields.md의 "다음" 절 … 이어받을 상태: 없음. 01은 PR 475로 병합됐다. 그 PR에서 보류한 지적 둘 … 은 04의 몫이라 이 티켓은 건드리지 않는다 / 확인할 선행 조건: 주 체크아웃 미갱신 … 이번 요청 범위: 구현·리뷰·커밋까지

(`…`는 이 세션의 대화 기록에서 이미 그렇게 보인 생략이다.) 이 세션은 `/implement` 흐름으로 티켓 02를 구현·리뷰·커밋까지 했고, 이어 사용자가 PR 열기와 병합을 요청했다.

## 사용자 결정

규칙 줄의 도구 이름에 든 `*`를 어떻게 받을지가 이 세션의 유일한 설계 결정이었다. 구현 중에 맨 `*`나 `send_*`가 와일드카드가 아니라 글자 그대로의 이름으로 읽혀 `deny = ["send_*"]`가 조용히 아무 도구도 막지 않는 모양이 드러났다. 세션이 낸 선택지는 둘뿐이었고(조용히 두기, 읽을 때 거부하기), 패턴으로 받는 셋째 안이 빠져 있었다. 사용자의 답은 순서대로 다음과 같다.

> 사용자: 거부한다
> 사용자: "*" 는 패턴으로 안되는거야?
> 사용자: 클로드코드는 어떤식으로 해?
> 사용자: 같게 해줘
> 사용자: 승인
> 사용자: 이어서 진행

- 첫 답으로 읽을 때 거부하는 커밋 `97f99a58`이 섰다. 뒤의 두 질문은 거부가 맞는지 되묻는 것이었다.
- Claude Code의 방식은 공식 문서 `https://code.claude.com/docs/en/permissions`를 WebFetch로 받아 읽었다(문서에서 읽은 것). deny와 ask는 도구 이름 전체에 맞는 글롭(`"*"`, `"mcp__*"`)을 받고, allow는 글자 그대로의 `mcp__<서버>__` 접두 뒤에서만 글롭을 받으며 앞이 열린 allow 글롭은 건너뛰어 승인하지 않는다. 도구 이름에 `_`나 `*`가 든 deny·ask는 "맞는 도구 없음" 시작 경고에서 빠진다(저장된 문서 사본 207행).
- "같게 해줘"로 거부 방식이 뒤집혀 커밋 `a1bccadb`이 섰다. ADR 0044의 규칙 줄 모양이 걸려 있어 이력 "도구 이름의 별표는 패턴이다"를 초안으로 쓰고 셀프 리뷰를 반영한 뒤 보여 주었다. "승인"이 그 승인이다.
- 사용자가 따로 정하지 않은 것을 세션이 정했다. 하나, Claude Code는 allow의 앞이 열린 글롭을 건너뛰지만 이 파일은 조용히 효력 없는 줄이 남지 않게 읽을 때 깨진 파일로 거부한다. 둘, 서버 칸은 플러그인 이름이라 `*`를 받지 않는다(`*:add`는 깨진 파일). 둘 다 ADR 0044 이력에 적혀 승인과 함께 갔다.

## 한 것

커밋은 셋이다(`git log`의 출력). 앞의 둘은 구현이고 마지막이 별표 패턴 전환이다.

- `ebc01446` 운영자의 규칙 파일을 읽어 core의 불변 규칙 값(`Rule`, `RuleSet`, `Rules`)으로 만든다. 읽기는 기존 `PluginSource` 포트의 `read_rules()`이고 포트는 다섯 그대로다. 파일 모양과 문자열을 `Rule`로 바꾸는 일은 파일시스템 어댑터가, 값과 `applied_rule`·`matches`는 core가 가진다.
- `97f99a58` 도구 이름에 `*`가 들면 깨진 파일로 거부한다(뒤집힌 안).
- `a1bccadb` 도구 이름의 `*`를 패턴으로 받는다.
  - core `Rule.matches`가 `_name_matches`로 조각을 `re.escape`한 정규식에 `fullmatch`한다(코드를 읽었다).
  - 어댑터는 줄의 글자 모양만 정규식으로 본다. deny·ask는 맨 도구 이름(패턴 포함), `서버:*`, `서버:도구(패턴 포함)`를 받고 allow는 서버를 붙인 꼴만 받는다.
  - 명세, 티켓 02·05, `.claude/rules/adapters.md`, ADR 0044(본문 두 곳의 포인터와 새 이력)를 같은 결정으로 고쳤다.

## 검증

초록은 아래 명령의 출력에서 읽었다.

- `uv run pytest tests/core/test_rules.py tests/adapters/test_filesystem.py`: 166 통과(마지막 변경 뒤).
- `uv run ruff check . && uv run ruff format --check .`: 통과. `uv run pyright`: 오류 0, 경고 0. `uv run lint-imports`: 계약 6 지킴 0 깨짐. `uv run python tools/check_adr_pointers.py`: 출력 없이 종료.
- 변이 표 `tools/mutate.py`: 13개 모두 기대대로 빨강(마지막 실행). `--check`는 원문이 한 번씩 있다고 했다.
- 카나리아 `.scratch/approval-rules/probes/canary/adapters_rule_rules_file_read.toml`: 통과 4(새 `claude -p` 세션, 규칙 파일 `adapters.md`를 바꾼 뒤 한 번. 그 파일은 이후 바뀌지 않았다).
- 커밋 `a1bccadb`의 pre-commit: 검사가 모두 `Passed`였고 `constitution version`만 헌법 파일을 건드리지 않아 `Skipped`였다. 위 손으로 친 명령 가운데 pytest 전체·pyright·lint-imports·ruff는 이 pre-commit 결과로 갈음한다(`CLAUDE.md` 검증 명령 절). 위젯 e2e와 `-m llm`은 치지 않았다. 이 변경은 어댑터와 core의 규칙 값이고 위젯과 최종 사용자 경로의 코드를 바꾸지 않았다(코드를 읽은 어림).

## 셀프 리뷰(`/code-review`)

범위는 기준 `97f99a58`, 작업 트리 변경 10개였다. 표준 축은 sonnet·high, 명세 축은 본 세션 모델이다.

- **명세 축.** 확정 둘을 고쳤다. 하나, 에이전트 표의 검사(명세 "에이전트 표의 검사", 티켓 05)가 글자 그대로의 이름만 알아 `[agents.calc] deny = ["*"]`가 `tool_connection`으로 실행을 실패시킬 길이 있었다. `*`가 든 줄은 도구 실재 검사에서 빼고 `서버:패턴`의 서버만 `mcp`에 있는지 보게 명세·티켓 05·ADR 이력에 적었다(구현은 05의 몫). 둘, ADR 본문 21행의 "서버 칸은 `<서버>:*`에만 대 본다"에 포인터를 이어 달았다.
- **표준 축.** 같은 에이전트 표 지적과, 변이 표지 넷(1·7·8·9)이 pytest의 풀이 줄(`where … = …`)에서 나온다는 지적이 확정이었다. 표지를 고른 사례가 실패할 때만 찍히는 인자 줄(`rule = Rule(...), server = ..., tool = ...`)로 바꿨다. 변이 1의 인자 줄은 한 줄이 길어 `tool = ...`이 다음 줄로 넘어가 있었고, 손으로 변이를 넣어 출력을 보고서야 표지를 줄였다(명령 출력).
- **판단 항목.** `re.DOTALL`이 어느 시험에도 지켜지지 않는다는 지적은 개행이 든 이름 사례와 변이를 더해 지켰다(없으면 `deny = ["*"]`가 개행이 든 이름 앞에서 샌다). `Rule(server, "*")`와 `Rule(server, None)`의 표현 중복, `Rule.tool: str`이 이름과 패턴을 겸하는 점은 동작에 문제가 없어 남겼다(값이 같은 뜻을 두 가지로 가질 수 있다. 필요해지면 한쪽으로 정규화한다).
- 서브에이전트 두 보고의 사실 문장은 판정에 쓰기 전에 코드와 실행으로 대 봤다.

## PR 직전 리뷰

- 본 세션이 `coderabbit auth status`를 보니 `Plan: Free`, `Seat: not assigned`였다(명령 출력). `coderabbit-review` 서브에이전트는 그 줄에서 `리뷰를 돌리지 않고` 종료했다(에이전트 정의 1단계: 좌석 `not assigned`면 CLI 축이 비었다고 보고 종료).
- 규정(`docs/constitution/operations.md` 리뷰 파이프라인 2)은 CLI 축이 비었는지를 PR마다 실제 실행으로 판정하라고 한다. 그래서 `coderabbit review --agent --committed --base origin/main`을 직접 쳤더니 종료 코드 0, 출력의 `complete` 줄이 `review_completed`, `findings: 0`, 검토한 파일 19개였다(명령 출력). 좌석이 `not assigned`인데도 리뷰가 돌았다.
- 그래서 CLI 축은 비지 않았고 대체 둘(`/security-review`, `bug-perf-review`)은 돌리지 않았다. 지적이 0건이라 트리아지할 것도 없다.
- 에이전트 정의의 `not assigned`면 종료한다는 문장이 규정, 그리고 같은 정의의 `Seat:` 줄이 없을 때의 처리와 어긋난다. 이 세션의 사건으로 한 번 났다. 고치는 것은 이 변경의 몫이 아니어서 회고가 대기열 578로 받았다.

## 회고

후보 일곱을 냈고 판정은 승인 3, 기각 4, 넘김 0이다. 판정과 근거는 모두 에이전트가 정했다. 근거의 종류는 대화 기록과 저장소를 읽은 것, `tools/queue_open_rows.py`의 출력, `tools/mutate.py`의 코드를 읽은 것이다.

- **승인(고침): `coderabbit-review` 정의 1단계가 `Seat: not assigned`만 보고 리뷰를 돌리지 않고 종료했다.** 사건은 이 세션의 PR 직전이다. 같은 좌석 상태에서 본 세션이 `coderabbit review`를 직접 쳐 `review_completed`, 지적 0건을 받았다. 층은 에이전트 정의의 고침이고 PR 하나로 되돌릴 수 있다. 가드레일을 느슨하게 하는 것이 아니라 리뷰를 더 돌리게 하는 쪽이다. 대기열 578(557의 3회차, 557은 2회차로 닫혔다)로 갔다. 이 세션에서 반영하지 않은 까닭은 하네스 변경을 이 기능의 PR에 섞지 않기 위해서다.
- **승인(회차를 센다): 변이 표지가 pytest 풀이 줄의 부분 문자열이었는데 `--check`가 알리지 못했다.** 사건은 표준 축 리뷰가 잡은 표지 넷이다. `.claude/rules/probes.md`는 구현 때 실리는 지침이라 리뷰가 잡아도 회차로 센다. 행 찾기에서 닫힌 350·367·517이 걸렸고 가장 큰 회차는 5라 대기열 579(517의 6회차)로 갔다. 열린 행의 회차가 3 이상이라 chore 계기다.
- **승인(회차를 센다): 사용자에게 낸 선택 질문이 둘뿐이라 가장 가까운 선례의 방식을 빠뜨렸다.** 사건은 사용자의 되물음 두 번과 뒤집힌 커밋 `97f99a58`이다. 층은 질문을 쓰는 스킬의 지침 문장이고 검사로 옮길 수 없다. 더하는 것이라 문턱 전이므로 대기열 580(1회차)이다.
- **기각: 티켓 05의 미래형 문장을 같이 고치지 않았다(`CLAUDE.md` 작업 규약 4).** 명세 축과 표준 축이 모두 잡았다. `code-review`의 두 브리프가 그 자리를 보는 주장 검증 항목(미래형)이라 리뷰가 제 몫을 한 것이고 회차로 세지 않는다.
- **기각: 파이프가 든 pytest 명령과, 변이를 돌리는 동안 같은 체크아웃의 문서를 고친 일.** 이미 있는 훅이 그 자리에서 알렸고 따랐다.
- **기각: Grep이 긴 줄을 `[Omitted long matching line]`으로만 내어 줄을 Read로 다시 열었다.** `hook_grep_omitted`가 그때마다 알렸고 알린 대로 했다.
- **기각: `Skill`에 워크트리 접두를 붙인 이름을 불러 Unknown skill이 났다.** 한 번이고 오류가 바로 이름을 알려 줬다. 사건 없이 떠올린 것에 가깝다.

만료할 행은 없었다(`tools/queue_open_rows.py --ref origin/main`이 "만료할 행 (없음)"을 냈다).

## 다음

- 이 브랜치의 PR을 열고 병합한다. 병합 뒤 02는 `done`이다(티켓 `Status`는 이미 `done`, plan.md의 approval-rules 행은 `in-progress` 그대로).
- 03(도구의 서버 이름·같은 이름 검사)은 다른 워크트리에서 나란히 돌고 있다. `src/agent_os/core/ports.py`, `.claude/rules/adapters.md`, `.claude/rules/core.md`를 함께 고치므로, 나중에 병합하는 쪽이 글자 충돌을 합친다(`tools/sibling_overlap.py` 출력).
- 04(런타임이 도구 호출마다 규칙을 집행한다)는 02와 03이 모두 병합된 뒤다. 05는 04 바로 뒤이고, 05의 에이전트 표 검사는 `*`가 든 줄을 도구 실재 검사에서 빼도록 티켓이 이미 고쳐져 있다.
