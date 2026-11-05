# 01: 계약 — 트레이스의 도구 호출과 멈춤에 적용 규칙·서버 칸이 는다

**What to build:** 운영자가 관리 API로 트레이스를 읽으면 `tool_called`에 선택 칸 `rule`이, `run_paused`에 선택 칸 `rule`과 `server`가 실려 있다. `rule`의 값은 sdk가 내보내는 닫힌 목록 `AppliedRule` 다섯(`deny`, `requires_approval`, `ask`, `allow`, `default`)이다. 옛 트레이스(형식 1·2·3)는 그대로 읽히고 형식은 3 그대로다. 관리 화면의 실행 하나 화면은 두 칸을 다른 칸처럼 "적용 규칙"과 "서버"라는 이름과 값으로 그린다. 최종 사용자 면의 항목은 두 칸을 싣지 않는다. 에이전트가 이 칸을 채운 `tool_called`나 `run_paused`를 내면 그 이벤트를 쓰지 않고 실행이 `run_failed`(원인 `agent_code`)로 끝난다.

이 기능의 계약 티켓이고 02와 03을 막는다(04·05·06은 그 둘을 거쳐 막힌다). 계약은 sdk 이벤트의 세 칸과 `AppliedRule`, `openapi.json`, 생성 타입이다. 끌고 오는 것은 생성 타입을 단 리터럴, 관리 화면 필드 이름 표의 두 줄과 그 사진 정답, 런타임 전용 판정, `.claude/rules/sdk.md`의 선택 필드 항목이다. 리뷰의 질문은 "동작하나"가 아니라 이 칸 이름과 값으로 오래 살 수 있느냐다.

**병합 뒤에 틈이 있다(to-tickets에서 사용자가 분할을 골랐다).** 런타임은 아직 두 칸을 채우지 않아 새로 쓰는 트레이스에서도 늘 `null`이다. 런타임이 채우는 것은 04다. 런타임 전용 판정은 이 티켓에서 바로 듣는다. 그 판정을 04에 두면 01과 04 사이에 에이전트가 채운 칸이 트레이스에 남고, 04 뒤 그 트레이스를 재개하면 재생 구간에서 `agent_code`로 끝나기 때문이다(명세 검토가 `_reject_runtime_only`를 읽었다). 이 티켓이 쓰는 문장(독스트링, 주석, rules)은 틈 동안에도 참이어야 한다. 런타임이 무엇을 채우는지가 아니라 계약이 무엇을 약속하는지를 말한다(skill-plugin 01과 같은 규칙).

근거는 `.scratch/approval-rules/spec.md`의 "적용 규칙 칸의 이름과 값", "두 칸은 런타임만 쓴다"와 그 2026-11-06 명세 검토 주석, "서버 칸과 재개의 대조"의 첫·셋째 불릿, "계약과 관리 화면", "고칠 자리의 묶음"의 A 줄과 그 주석, Testing Decisions의 "sdk 이벤트"·"HTTP 두 면"이다. 앞선 결정은 ADR 0044의 "기록"·Consequences "계약"과 2026-11-05 이력 "승인 결정은 서버에도 묶인다", ADR 0031(런타임 전용 판정), ADR 0010의 2026-09-24 이력 "트레이스 상세는 객체이고 이벤트는 `sdk`의 것 그대로다"(늘 실리는 이벤트의 칸을 required로 내보낸다)이다.

**Blocked by:** None (can start immediately)

**Status:** done

### sdk — 두 이벤트의 세 칸과 `AppliedRule`

- [ ] **`AppliedRule`은 sdk가 소유해 내보내는 닫힌 목록 다섯이다.** `deny`(운영자의 deny), `requires_approval`(저자의 승인 요구), `ask`(운영자의 ask), `allow`(운영자의 allow), `default`(적힌 규칙 없음, 그래서 묻는다)이고 용어집 **적용 규칙**의 다섯과 하나씩 맞는다. 계약의 컴포넌트 이름은 별칭 이름 `AppliedRule`이다(`FailureCause`의 선례)
- [ ] **칸은 셋이다.** `tool_called.rule`, `run_paused.rule`, `run_paused.server`이고 모두 선택이며 기본값은 없음(`null`)이다. `tool_called`에는 `server`가 없다(mcp-trust가 정한다, 명세 Out of Scope). `server`에는 이벤트의 다른 식별자 필드처럼 sdk의 패턴을 걸지 않는다(`.claude/rules/sdk.md`)
- [ ] **옛 줄이 그대로 읽히고, 새 칸이 왕복하며, 헤더의 형식은 3 그대로인 것을 단언한다.** `AppliedRule` 밖의 값은 거부된다. 실패를 기대하는 시험은 pydantic 오류의 `type`으로 까닭을 단언한다(`CODING_STANDARDS.md`). 선례는 `tests/adapters/test_jsonl.py`의 `test_실패_원인과_바로가기가_왕복하고_헤더는_3_그대로다`와 `test_새_필드_둘의_키가_없는_옛_줄은_원인과_바로가기가_없음으로_읽힌다`다
- [ ] **계약에 실리는 모델의 독스트링은 한 줄이고 논증은 `#` 주석에 둔다**(`.claude/rules/sdk.md`, `.claude/rules/http.md`의 "계약에 박히는 것 둘")

### 런타임 전용 판정

- [ ] **에이전트가 `yield`한 `tool_called`나 `run_paused`에 세 칸 가운데 하나라도 채워져 있으면 그 이벤트를 쓰지 않고 `run_failed`(원인 `agent_code`)로 끝낸다. 재생 구간에서도 같다.** 대화 요약과 실패 이벤트를 막는 판정(`_reject_runtime_only`, ADR 0031)과 같은 길이다. 칸을 채운 `run_paused`는 지어낸 일시정지를 멈춘 것으로 치지 않는 지금의 길보다 먼저 끝난다(선례 `tests/core/test_run.py`의 `test_에이전트가_지어낸_일시정지_이벤트는_실행을_멈춘_것으로_치지_않는다`)
- [ ] **칸마다(셋) 실시간과 재생 구간 모두에서 원인 `agent_code`와 메시지의 까닭을 단언하고, 양성 대조로 세 칸이 빈 `tool_called`는 지금처럼 통과하는 것을 본다**
- [ ] **`.claude/rules/core.md`의 런타임 전용 항목("`conversation_summarized`와 `run_failed`는 런타임만 낼 수 있다")과 `core/run.py`의 모듈 독스트링·`_reject_runtime_only` 독스트링에 세 칸을 더한다**

### 계약 파일과 생성 타입

- [ ] **`openapi.json`을 `uv run python tools/export_openapi.py`로 다시 뽑는다.** `ToolCalled.rule`, `RunPaused.rule`, `RunPaused.server`가 직렬화 스키마에서 `required`이고 `null`을 허락하며 컴포넌트 `AppliedRule`이 든다. 선례는 `tests/sdk/test_events.py`의 `test_직렬화_스키마에서_새_필드와_새_이벤트의_필드가_required_다`다. 최신성 시험이 파일을 판정한다
- [ ] **생성 타입을 다시 만든다.** 칸이 필수로 들어 옛 리터럴이 타입 검사에서 깨지는 것이 첫 빨강이다
- [ ] **두 이벤트의 리터럴에 새 칸을 적는다.** to-tickets 시점(main `83a66cdc`)에 `web/`에서 `type: "tool_called"`·`type: "run_paused"`를 Grep하면 생성 타입 파일 밖에서 다섯 파일의 열 곳이 나오고, 그 가운데 아홉 곳이 이벤트 리터럴이다(나머지 하나는 타입 가드 `isEvent`에 넘기는 `type`만 든 객체다. 셀프 리뷰가 Grep으로 셌다). 어느 것이 생성 타입을 다는지는 타입 검사가 가르고, 타입을 달지 않은 픽스처는 vitest나 e2e에서 드러나니 함께 본다
- [ ] **관리 화면 필드 이름 표(`web/apps/admin/components/organisms/EventItem.tsx`의 `FIELD_NAMES`)에 `rule: "적용 규칙"`과 `server: "서버"`를 더한다.** 도구 이벤트 카드에 "적용 규칙", 멈춤 이벤트 카드에 "적용 규칙"과 "서버" 줄이 서는 것을 페이지 시험으로 단언한다. 선례는 `RunPage.test.tsx`의 실패 원인 줄 단언이다. 명세 검토는 관리 화면 시험이 이벤트 카드의 필드 줄 수나 글자를 단언하는지 보지 않았다. 그런 단언이 깨지면 새 줄을 넣어 고친다
- [ ] **관리 화면의 사진 정답을 다시 만든다.** 이벤트 카드가 모든 칸을 이름과 값으로 그리고 `null`도 글자로 그리므로, 리터럴에 칸이 들면 멈춤·도구 이벤트가 든 실행 상세 사진이 바뀐다(코드를 읽었다. `organisms-rundetail--*` 마흔여덟 장 가운데 몇 장인지는 세지 않은 어림이다). `pnpm -C web visual:admin`으로 빨강을 보고 `pnpm -C web visual:admin:update`로 정답을 컨테이너 안에서 다시 만든 뒤 바뀐 사진을 PR 본문에 적는다(`.claude/rules/web-design.md`)
- [ ] **관리 API의 경로와 관리 화면의 다른 자리는 바뀌지 않는다**(ADR 0044 "범위 밖")

### 최종 사용자 면

- [ ] **최종 사용자 항목의 투영(`channel/http/items.py`)은 두 칸을 싣지 않는다.** 투영은 칸을 골라 항목을 만들어 새 칸이 저절로 실리지 않으므로(명세 검토가 코드를 읽었다) 투영 코드는 고치지 않는다. 칸을 채운 `tool_called`·`run_paused`를 투영해도 항목에 적용 규칙과 서버가 없는 것을 단언해 회귀를 막는다. 선례는 `tests/channel/http/test_end_user.py`의 `test_항목은_프롬프트도_도구_결과도_주체도_싣지_않는다`다

### 문서

- [ ] **`.claude/rules/sdk.md`의 선택 필드 항목(`shortcuts`·`cause`의 불릿)에 두 이벤트의 세 칸을 더한다.** 선택이고 기본값이 없음이라 형식 3 그대로인 것, 직렬화 스키마에서 required이고 `null`을 허락하는 것, 관리 화면 필드 이름 표의 두 줄, 그리고 이 기능 전의 코드가 새 칸이 든 줄을 손상으로 거부하는 비대칭(두 이벤트가 재개의 입력이라 옛 판은 새 판이 멈춘 실행을 재개하지 못한다. ADR 0044가 받아들였다)이다. 런타임이 언제 무엇을 채우는지는 04가 쓴다. 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다(`.claude/rules/agent-docs.md`)
- [ ] **옛 표현을 저장소 전체에서 grep해 살아 있는 문서에 잔존이 0인지 본다**(`CLAUDE.md` 작업 규약 4). 런타임만 내는 것이 두 종류뿐이라고 읽히는 문장이다. 기록(일지, 대기열, ADR 이력)은 고치지 않는다

### 검증

- [ ] **빨강을 먼저 본다**(헌법 원칙 II). 첫 빨강은 리터럴이 타입 검사에서 깨지는 것, `openapi.json` 최신성 시험, sdk의 왕복·거부 시험, 런타임 전용 판정의 시험이다
- [ ] **검증 명령이 모두 초록이다.** 손으로 치는 다섯에 더해 관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`. api-client가 바뀐다)와 사진 비교 `pnpm -C web visual:admin`을 친다. `-m llm`은 이 티켓이 닿지 않는다. 위젯 e2e와 `-m llm_widget`은 투영 코드를 바꾸지 않아 닿지 않지만, 생성 타입이 위젯이 쓰는 api-client의 몫까지 바뀌면 위젯 e2e를 친다
