# 2026-11-06 (02) 설치형 문서 질의응답 방향(제안서 반영)

## 사용자 프롬프트

> 사용자: @"C:\Users\User\Downloads\agent-os-rag-baseline-plan.md"
> 첨부한 agent-os-rag-baseline-plan.md는 다음 기능 계획의 제안서다. 그대로 붙여 넣지 말고 저장소 절차대로 반영해 줘.
>
> 1. 기준 커밋 403c9e9 이후 main이 바뀌었으면 1절의 사실부터 다시 확인한다.
> 2. 6절의 PRD 개정안을 보여 주고 승인을 받는다.
> 3. 7~9절의 ADR 0044, 0045, 0046 초안을 셀프 리뷰한 뒤 하나씩 승인을 받는다. 번호는 저장소의 다음 번호에 맞춘다.
> 4. 승인이 끝나면 3절과 4절대로 .scratch/plan.md를 고친다.
> 5. 10~13절은 각 행의 설계 인터뷰 입력으로 쓴다. 저장소 어디에 둘지는 문서 위치 규약대로 정한다.
>
> 계획과 저장소의 현재 상태가 맞지 않는 곳이 있으면 고치기 전에 먼저 알려 줘.

(같은 글이 메시지에 두 번 들어 있었다. 제안서는 저장소 밖의 파일이라 커밋하지 않는다. 제안서의 절 번호는 이 일지에서 "제안서 N절"로 가리킨다.)

## 대조(고치기 전)

기준 커밋 `403c9e9` 뒤로 main에 #469(approval-rules 설계, ADR 0044), #470(harness 044, `tests/test_plan_status.py`), #471(approval-rules 명세)이 들어왔다. 주 체크아웃에서 `git fetch` 뒤 `git log 403c9e9..origin/main`으로 봤다.

- 큰 어긋남 하나. 제안서는 approval-rules가 시작 전이라는 전제로 그 행을 슬라이스 10으로 미뤘다. 지금은 ADR 0044(accepted)와 `.scratch/approval-rules/spec.md`(ready-for-agent)가 섰고, plan.md 프론티어 문단은 "다음은 명세 검토와 티켓"이며, 워크트리 `approval-rules-tickets`가 잠겨 있다(잠금 파일 "claude session approval-rules-tickets"를 손으로 봤다. 그 세션이 지금 도는지는 어림).
- 제안서 1절의 나머지 열둘은 코드를 읽어 대 봤다(main 83a66cd). 다른 것은 둘이다. `[server]`에는 `command`·`args` 말고 도구별 `secret_args`도 있다(`sdk/manifest.py`). mcp 2.3.0의 `streamable_http_client`는 헤더 인자가 없어 토큰 헤더를 실으려면 `httpx2.AsyncClient`를 넘겨야 하고, httpx2 2.13.0은 잠금 파일에 이미 있지만 직접 import하면 선언하는 관행이 있다(`pyproject.toml` 35~38줄 주석, ADR 0023의 pyjwt).
- 작은 어긋남. ADR 0044는 이미 쓰였으므로 제안서의 0044·0045·0046은 0045·0046·0047로 옮긴다. PRD의 미룬 것은 한 줄 나열이라 제안서 6절의 `~` 줄 모양이 맞지 않는다. 멀티테넌시가 미룬 것에 남는 것과 제품 1.0의 "여러 부서가 한 설치를 나눠 쓴다"가 헷갈릴 수 있다. ADR 초안의 stdio·HTTP 비율과 제안서 11절의 요금은 웹 글의 수다. RAG 서버 저장소는 아직 없고 `rag-server-plan.md`는 받지 않았다. ADR 0043의 dev 브랜치는 아직 없어(`git branch -r`) PR은 main으로 간다.
- 제안서 10~13절의 자리. 10절은 행마다의 위험이라 각 행에 넣는다(`docs/agents/issue-tracker.md` 전체 계획 절의 "행에는 다른 기능이 넘긴 것을 적는다"). 11~13절은 세 행 이상이 함께 쓰는 자료라 `.scratch/doc-qa-direction/inputs.md` 하나에 두고 행에서 가리킨다. 기능 이름의 폴더(`.scratch/local-model/` 등)를 만들면 `grill-with-docs`의 트리거("`.scratch/<slug>/`가 없는 단계")가 꺼지고, `docs/`는 다시 확인할 작업 자료의 자리가 아니라서다. 선례는 ADR 0042 때의 `.scratch/agent-os-direction/`이다.

## 사용자가 정한 것

> 사용자: (approval-rules(운영자가 규칙 파일로 도구 호출을 막거나 묻거나 허락하는 기능)는 설계와 명세가 끝났고 지금 다른 세션이 티켓을 쓰는 중입니다. 이 기능을 어디에 둘까요?) "지금 자리에서 계속 (Recommended)" — 설명: approval-rules는 지금처럼 바로 진행하고, 그 뒤의 mcp-trust부터는 제안서대로 pilot-release 뒤로 갑니다. 프론티어는 approval-rules, local-model, mcp-http, pilot-portal 넷이 되고, 제품 0.1의 알려진 한계에서 '운영자 승인 규칙 없음'이 빠집니다. 대신 규칙 파일에 없는 도구는 기본으로 승인을 묻게 되므로(명세가 정한 동작), doc-qa와 참조 배포가 검색 도구를 허락하는 규칙 파일을 함께 내야 합니다. 두 기능이 같은 파일(adapters/mcp.py)을 고치므로, 나중에 병합하는 쪽이 충돌을 풀어야 합니다.

화면에 올리기 전에 대 본 것: 두 기능이 `src/agent_os/adapters/mcp.py`를 고친다(stdio 연결 158줄, 명세의 도구 모음 자리), 규칙이 없으면 묻는다(명세의 넘겨받은 것 (3)·(11)). 다른 세션이 티켓을 쓰는 중이라는 것은 잠금 파일로 본 어림이다.

## PRD 개정(승인)

제안서 6절을 지금 PRD 모양과 위 결정에 맞춰 고쳐 일곱 블록으로 보였다. 보인 문장은 이 절을 쓴 뒤의 `docs/PRD.md` diff에서 아래 "용어" 절의 낱말 교체를 되돌린 것과 같다(셀프 리뷰 뒤 대화 기록에서 승인 질문 직전의 글을 뽑아 대 봤다). 제안서와 달라진 곳 가운데 화면에 까닭을 적은 것은 다섯이다(보인 글에는 1.0 줄의 "오래된 근거의 경고"와 "(어림)"도 있었으나 까닭을 따로 적지 않았다). "이미 보장하는"을 뺐다(강제는 지금 `requires_approval`과 꺼짐 파일까지다). 미룬 것은 한 줄 나열 모양에 맞추고 멀티테넌시와 부서 나눠 쓰기를 가르는 문장을 더했다. 전제를 셋으로 세고 "묶음 ②(trace-postgres부터)"로 넓혔다(ADR 0042에서 PostgreSQL·Redis는 18, worker는 12와 함께 든다. ADR 0042 표를 읽었다). 기준선 줄에 승인 규칙이 나란히 간다는 문장을 더하고 1.0 줄을 "묶음 ①의 나머지"로 고쳤다. 1.0의 "트레이스 조회까지 이어진다"는 제안서의 audit-export 행("문서별 열람 권한을 걸지 않는다")과 어긋나 "운영자가 조회하고 내보낸다"로 고쳤다.

> 사용자: (위 PRD 개정안을 이대로 승인하시겠습니까? 승인하시면 ADR 초안 셋의 셀프 리뷰로 넘어가고, PRD 파일은 ADR 승인까지 끝난 뒤 같은 PR에 함께 싣습니다.) "이대로 승인" — 설명: 위의 일곱 블록(상태 줄, 누구의 문제, 왜 지금, 무엇을 만드나, 미룬 것, 전제, 성공의 정의)을 적힌 문장 그대로 docs/PRD.md에 반영합니다. ADR 번호(0045·0046·0047)는 다른 세션이 먼저 가져가면 같이 옮깁니다.

## 용어(domain-modeling)

`.claude/rules/adr.md`대로 ADR을 쓰기 전에 `domain-modeling`을 불러 `CONTEXT.md`와 대 봤다. 부딪친 것은 둘이다.

- 제안서의 "주소 모양 MCP 서버(상주 서버)"는 용어집의 **원격 MCP 서버**와 같은 것이라 그 이름을 쓴다. ADR 0042 묶음 ③의 "원격 MCP" 줄이 `[server]`의 http 모양을 이미 "url·헤더의 환경 변수 이름"으로 정했으므로(ADR 0042 63줄을 읽었다), 제안서 mcp-http 행이 연 "매니페스트인가 서버 파일인가"는 그 모양에서 출발하는 것으로 고친다. 묻지 않고 정했다(용어집과 ADR이 이미 정한 것을 따르는 것이다).
- 용어집의 **설치(Install)**는 마켓플레이스의 플러그인 폴더를 복사하는 일이고 코드가 가는 길은 배포다. 승인받은 PRD가 "설치"를 제품을 서버에 띄우는 뜻으로 네 곳(24·43·43·44줄, `grep`으로 셌다)에 썼다.

> 사용자: (제품을 고객 서버에 띄우는 일을 문서에서 무엇이라고 부를까요?) "'배포'로 부른다 (Recommended)" — 설명: 용어집에 '배포 환경'(참조 배포를 띄우는 조직의 서버와 망) 항목을 더하고, 승인받은 PRD의 네 곳(24·43·44줄)을 '1시간 안에 배포되고', '배포 환경의 모델', '한 배포 환경을 나눠 쓴다'로 바꿉니다. '설치형 문서 질의응답'은 제품의 분류 이름으로만 남기고, 행 이름 install-package는 deploy-package로 바꿉니다. ADR과 plan.md도 같은 말로 씁니다.

반영: PRD 네 곳을 고쳤다. 같은 줄의 "다른 저장소의 RAG 서버가 맡는다"는 PRD의 다른 줄이 쓰는 "문서 검색 서버"에 맞춰 고쳤다(뜻은 같고 낱말만 맞춘 것이라 따로 묻지 않았다). `CONTEXT.md`에 **배포 환경**, **참조 배포**(구조 절, 설치 뒤)와 **문서 검색 서버**(원격 MCP 서버 뒤)를 더했다.

## ADR 초안(셀프 리뷰 전)

ADR 셋을 `proposed`로 썼다. 0045(기준선과 제품 1.0이 ADR 0042의 나머지 열셋 앞에 선다), 0046(Agent OS는 위젯을 모른다), 0047(문서 검색 서버는 다른 저장소다). 제안서 7~9절과 달라진 곳은 위 두 결정과 용어(원격 MCP 서버, 배포, 문서 검색 서버, install-package → deploy-package), 그리고 근거 표시다. 제안서 0044 초안의 stdio·HTTP 비율 수치는 빼고 "공개 MCP 서버의 다수가 stdio(어림, 세지 않았다)"로 적었다. 0047의 CI 분담은 dev 브랜치가 아직 없어 "ADR 0043의 CI 분담대로, 빠른 검사는 가짜 서버, 실제 이미지 compose e2e는 실제 이미지"로 적었다.

함께 고친 것: ADR 0042에 `## 이력`의 2026-11-06 항목과 포인터 넷(표의 15·3 행, "원격 MCP(3의 한 가지)", Consequences의 plan.md 줄), ADR 0044 62줄("다음 기능 mcp-trust")에 `(바뀜: ADR 0046)`, ADR 0024에 2026-11-06 이력, 색인 행 셋. `uv run python tools/check_adr_pointers.py`가 0으로 끝났다(손으로 쳤다).

이 세션이 고친 것: ADR 0047의 "관리 화면에서 위젯을 이르는 것은 주석 둘"이 틀려(`git grep -i 'widget\|위젯' -- web/apps/admin`으로 일곱 파일의 주석을 봤다) "같은 모양을 따른다고 적은 주석뿐"으로 고쳤다. 색인에 새 행을 0044 앞에 넣었다가 뒤로 옮겼다.

## 인계 전 상태(셀프 리뷰 직전)

세션 컨텍스트가 인계 문턱을 넘어 `셀프 리뷰 직전` 경계에서 넘긴다. 이 세션의 제목은 `docs/doc-qa-direction`이었다. 커밋하지 않은 변경이 워크트리 `C:/project/agent/.claude/worktrees/doc-qa-direction`에 있다.

남은 일(사용자 요청 2~5의 나머지):

1. `/code-review` 셀프 리뷰. 기준점 origin/main(83a66cd). 명세 축의 원천은 이 일지의 사용자 프롬프트와 "사용자가 정한 것", 제안서 6~9절이다.
2. 반영한 뒤 ADR 0046 → 0047 → 0048을 하나씩 보이고 승인받는다. 승인되면 `status: accepted`와 색인의 상태를 바꾼다.
3. 승인 뒤 `.scratch/plan.md`를 제안서 3·4절대로 고친다. 이 세션에서 정해진 차이: approval-rules는 슬라이스 7·Blocked by skill-plugin 그대로이고, mcp-trust의 Blocked by가 approval-rules와 pilot-release다(나머지 Blocked by 표는 제안서 4절). 번호는 0045~0047, install-package는 deploy-package, "주소 모양 MCP 서버"는 원격 MCP 서버, mcp-http 행은 ADR 0042 "원격 MCP" 모양에서 출발하며 토큰 헤더를 실으려면 httpx2를 직접 의존으로 선언할 수 있다는 것을 적는다. doc-qa-agent와 deploy-package 행에 검색 도구를 허락하는 규칙 파일을, pilot-release의 알려진 한계에서 "운영자 승인 규칙 없음"을 뺀다. 프론티어 문단 끝 문장은 프론티어 넷(approval-rules, local-model, mcp-http, pilot-portal)으로 쓴다. 제안서 10절의 위험은 각 행 내용 칸에 "설계 인터뷰가 먼저 볼 것"으로 넣되 행에 이미 있는 것은 다시 적지 않는다.
4. 제안서 11~13절을 `.scratch/doc-qa-direction/inputs.md`에 두고 행에서 가리킨다. 요금과 출처는 웹 글의 수라 "웹 요약, 원문을 대 보지 않았다"로 표시한다.
5. 검증 명령, 커밋(`docs/doc-qa-direction`, 면제 PR), PR, 병합, 일지 "다음", retro. ADR 0047이 넘긴 harness 티켓(openapi.json에 위젯 전용 이름이 없는지 보는 저장소 상태 시험)은 후속이다.

주의: 워크트리 `approval-rules-tickets`가 잠겨 있어 그 세션이 plan.md의 approval-rules 행과 프론티어 문단을 고칠 수 있다. 커밋 전에 origin/main과 대 본다.

## 인계 지시문

```
다음 작업: 기능 doc-qa-direction. 설치형 문서 질의응답 제안서를 저장소 절차대로 반영한다(ADR 0046~0048 셀프 리뷰와 하나씩 승인, plan.md, 인터뷰 입력)
다음 단계: 설계 인터뷰
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: docs/journal/2026-11-06-02-doc-qa-direction.md의 "사용자 프롬프트" 절의 요청을 "인계 전 상태"의 남은 일 1부터 잇는다. 제안서는 C:\Users\User\Downloads\agent-os-rag-baseline-plan.md
브랜치: docs/doc-qa-direction
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-06-02-doc-qa-direction.md 전체, 제안서 3·4·10~13절
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. PRD 개정과 용어 '배포'는 승인받아 반영했고 ADR 셋은 proposed 초안이다. docs/journal/2026-11-06-02-doc-qa-direction.md
확인할 선행 조건: approval-rules-tickets 워크트리를 잠근 세션이 지금 도는지는 잠금 파일만 보고 어림했다
이번 요청 범위: PR과 병합까지(ADR 셋은 하나씩 사용자 승인)
```

open-session을 부른다 2026-11-05T15:51:30Z

open-session 1에서 list_sessions(limit 50)를 손으로 봤다. 같은 제목으로 도는 다른 세션은 없고, docs/approval-rules-tickets 세션이 isRunning이다(지시문의 '확인할 선행 조건'은 그 뒤에 확인되었다. 지시문은 고치지 않았다).

인계 못함 셀프 리뷰 직전. open-session 3의 `tools/open_session.ps1 -Action send`가 자동 모드의 권한 판정에 거부되었다(설명 없음). 제목을 docs/doc-qa-direction으로 되돌리고 이 세션에서 셀프 리뷰를 잇는다. 워크트리 잠금은 풀린 채 두었다(handoff.md 4).

## 셀프 리뷰(`/code-review`)

범위: base `83a66cd`(origin/main과 같다), 바뀐 파일 여섯, 미추적 넷, 커밋 0. 표준 축은 sonnet·high, 명세 축은 지정 없음. 명세 축은 제안서 원문 6~9절을 직접 읽었다.

표준 축이 낸 것(요지):

- Major. ADR 0046 8줄 "나머지 열여섯은 모두 운영자가 바깥에서 거는 정책과 그 기록"은 닫힌 주장이고 반례가 있다(declarative-agent, claude-code-compat, run-handoff, delegation, replay-evaluation, admin-crud, multi-instance).
- Major. ADR 0047 10줄 "위젯을 이르는 것은 같은 모양을 따른다고 적은 주석뿐"과 "끊을 연결" 셋이 코드와 어긋난다. 루프백 목록을 세 곳이 따로 들고 함께 고친다(`web/apps/admin/tools/loopback.ts` 9~10줄, `main.py` 71~72줄), 사이트 파일 규칙의 원천은 두 언어가 함께 읽는 픽스처다(`main.py` 520~521줄), `RunPage.test.tsx` 359줄은 "문구는 위젯의 몫"이라 적는다, `src/`도 주석으로 위젯을 이른다.
- Major. 포인터 없는 옛 문장 둘. ADR 0042 "전제"의 "배포는 프로세스 넷"(PRD 전제 셋이 기준선과 1.0을 한 프로세스로 바꿨다), ADR 0042 54줄 "PII 처리는 미룬 것"(PRD는 PII를 1.0으로 당겼다). 또 value-masking은 아는 비밀 값을 가리는 것이지 PII 탐지가 아니라서 PRD의 "입출력 가드레일과 value-masking으로 당기고"가 부정확하다.
- Minor. PRD 33줄 "주소 모양 MCP 서버(상주 서버)". PRD 33줄 "묶음 ②(trace-postgres부터) 프로세스 넷"은 worker가 retention-worker에서 서므로 정확하지 않다. ADR 0046 71줄의 `inputs.md`와 ADR 0048이 드는 행이 아직 없다. "참조 에이전트"·"참조 클라이언트"가 용어집에 없다. ADR 0042 제목과 색인 행의 "다음 기능은 다섯 묶음 열일곱".
- Nit. ADR 0046 16줄 "value-masking을 그 뒤로 당기며"의 앞뒤. 냄새(판단): ADR 0046 표와 PRD 1.0 줄이 같은 목록을 되풀이한다.

명세 축이 낸 것(요지):

- Major. ADR 0046 65줄 "그러지 않으면 질문마다 운영자의 결정을 기다린다"는 ADR 0044 63줄(최종 사용자가 주체인 실행에서 ask는 그 최종 사용자 자신의 확인)과 어긋난다.
- Major. ADR 0042 8줄의 굵은 결정 "다음 기능은 다섯 묶음 열일곱이고 순서는 …"에 포인터가 없다.
- Minor. PRD 33줄 "주소 모양 MCP 서버". ADR 0047 10줄의 반례(`RunPage.test.tsx` 359줄, `web/apps/admin/e2e/stack.ts` 3~4줄). 일지에 승인한 PRD 문장이 없어 "달라진 곳은 다섯"을 판정할 수 없고, 다섯 밖의 차이(1.0 줄의 "오래된 근거의 경고"와 "(어림)")가 있다. PRD의 "RAG 서버 → 문서 검색 서버"는 승인 뒤에 묻지 않고 바꿨다.
- Nit. ADR 0046 19줄이 "approval-rules가 도구마다 싣는 서버 이름"의 출처를 ADR 0042 "원격 MCP"로 든다(그 줄은 신뢰 수준·해시·주체 전파만 든다). ADR 0046 67줄 "프로세스 넷은 묶음 ②부터"는 1.0에 드는 value-masking도 묶음 ②라 정확하지 않다.
- 맞는 것: 번호 0045~0047은 다음 빈 번호다. 답 1의 요소가 ADR 0046에 모두 들었다. 답 3(배포, deploy-package)이 지켜졌다.

고친 것(근거를 열고 판정했다):

- ADR 0046 8줄과 Considered Options 첫 줄: "ADR 0042의 다섯 묶음(신뢰·강제, 비용·기록, 바깥 연결, 여러 에이전트, 확장·채널)에 걸친 런타임 기능이고", "런타임 기능만 쌓이고, 그 기능이 어떤 요구에 답하는지 시험할 자리가 없다"(ADR 0042 표의 묶음 이름을 읽었다).
- ADR 0046 16줄: "묶음 ②에서는 value-masking 하나만 앞으로 당겨 그 둘 바로 뒤에 두며".
- ADR 0046 19줄: "approval-rules가 도구마다 싣는 서버 이름(`.scratch/approval-rules/spec.md`의 `ToolSpec.server`)과, mcp-trust의 신뢰 수준·해시·주체 전파(ADR 0042 "원격 MCP")"(명세 89줄과 ADR 0042 63줄을 읽었다).
- ADR 0046 65줄: "최종 사용자가 주체인 실행에서 그 물음은 운영자의 검토가 아니라 최종 사용자 자신의 확인이다(ADR 0044). … 그러지 않으면 질문마다 검색 도구를 부르기 전에 실행이 멈추고, 위젯에서 질문한 사람이 그 호출을 직접 승인해야 답이 나온다"(ADR 0044 29·63줄을 읽었다).
- ADR 0046 67줄: "1.0에 드는 value-masking은 프로세스를 늘리지 않는다. PRD의 프로세스 넷은 trace-postgres가 PostgreSQL과 Redis를 더하고 retention-worker가 worker를 더해 선다(ADR 0042 묶음 ②의 표)"(ADR 0042 25·29줄을 읽었다).
- ADR 0047 10줄: "관리 화면과 `src/`가 위젯을 이르는 곳은 모두 주석과 독스트링이다. 예를 들어 …"로 닫힌 목록을 예시로 바꾸고, 루프백 목록과 사이트 파일 규칙은 함께 고쳐야 하는 결합이라 적었다(`git grep -i -E 'widget|위젯' -- web/apps/admin src`로 스물여덟 줄을 손으로 봤다). 14줄에 "모른다는 것은 위젯의 코드를 import하지 않고 위젯 전용 경로와 기능을 두지 않는다는 뜻이다"를 더했다. 끊을 연결에 공유 픽스처(`tests/fixtures/site_file/`, 위젯 `tools/site-file.ts` 17줄과 `testing/site-file.ts` 1줄)와 루프백 목록(위젯 `tools/start.ts` 22·39줄)을 더했다.
- ADR 0042: 8줄 굵은 결정, 15줄 전제, 54줄 PII 문장 뒤에 포인터를 달고, 2026-11-06 이력을 "바뀐 것은 여섯"으로 고쳐 전제의 프로세스 넷과 PII를 더했다. `tools/check_adr_pointers.py`가 0으로 끝났다.
- `CONTEXT.md`에 **참조 에이전트**(참조 배포 뒤)와 **참조 클라이언트**(위젯 뒤)를 더했다.
- 이 일지의 PRD 개정 절: 승인한 문장이 지금 PRD diff와 같다는 것과 "다섯"의 뜻을 바로잡았다.

남긴 것과 이유:

- PRD 수정 넷은 승인이 필요해 ADR 0046과 함께 보인다. 33줄 "주소 모양 MCP 서버(상주 서버)" → 원격 MCP 서버, 33줄 프로세스 넷의 정확한 시점, 미룬 것의 "과 value-masking" 빼기, 승인 뒤에 묻지 않고 바꾼 "RAG 서버 → 문서 검색 서버".
- ADR 0042 제목과 색인 행의 "다음 기능은 다섯 묶음 열일곱": 제목에 포인터를 단 선례가 없고 본문의 다른 글자는 고치지 않는다(`.claude/rules/adr.md`). 같은 결정을 이르는 8줄 굵은 문장에 포인터를 달았다.
- `inputs.md`와 ADR 0048이 드는 행: ADR 승인 뒤 같은 PR에서 쓴다(남은 일 3·4).
- ADR 0046 표와 PRD 1.0 줄의 되풀이: PRD는 무엇을 왜, ADR은 결정의 자리라 같은 목록이 두 층에 있는 것이 이 저장소의 모양이다(ADR 0042와 PRD 2026-11-04 개정의 선례). 판단 항목.

PR 직전 리뷰에 밀 주장으로 넘길 새 문장: ADR 0046의 "다섯 묶음에 걸친 런타임 기능", "위젯에서 질문한 사람이 그 호출을 직접 승인해야 답이 나온다", "trace-postgres가 PostgreSQL과 Redis를 더하고 retention-worker가 worker를 더해 선다". ADR 0047의 "모두 주석과 독스트링이다", 끊을 연결의 공유 픽스처와 루프백 목록. ADR 0042 이력의 "바뀐 것은 여섯".

다시 돌린 명령: `uv run python tools/check_adr_pointers.py`(0). 나머지 검증 명령은 커밋의 pre-commit으로 갈음한다.

## PRD 수정 셋과 ADR 0046 승인

화면에 PRD 수정 셋을 diff로 보였다. 전제 줄의 프로세스 넷 시점(trace-postgres가 PostgreSQL과 Redis를, retention-worker가 worker를 더한다)과 "주소 모양 MCP 서버(상주 서버)" → "원격 MCP 서버(상주 서버)", 미룬 것의 "입출력 가드레일(패턴으로 막거나 가린다)과 value-masking으로 당기고" → "입출력 가드레일(패턴으로 막거나 가린다)로 당기고"(value-masking은 아는 비밀 값을 가리는 것이라 개인정보를 찾지 않는다), 그리고 승인 뒤에 묻지 않고 바꾼 "RAG 서버 → 문서 검색 서버"를 함께 확인받았다. ADR 0046은 결정 여섯과 치르는 값 넷으로 요약해 보였다.

> 사용자: (PRD를 위의 세 군데대로 더 고치고, 승인 뒤에 바꾼 '문서 검색 서버' 낱말도 그대로 두어도 될까요?) "모두 고친다 (Recommended)" — 설명: 전제 줄에서 프로세스가 넷이 되는 시점을 trace-postgres(PostgreSQL과 Redis)와 retention-worker(worker)로 나눠 적고, '주소 모양 MCP 서버'를 '원격 MCP 서버'로 바꿉니다. 미룬 것에서는 'value-masking'을 빼서 개인정보 패턴은 입출력 가드레일이 맡는다고 적습니다. 기준선 줄의 '문서 검색 서버'는 지금처럼 둡니다.

> 사용자: (ADR 0045(기준선과 제품 1.0을 ADR 0042의 나머지보다 먼저 만들고, 원격 MCP 서버를 앞당긴다)를 이대로 승인하시겠습니까?) "이대로 승인" — 설명: ADR 0045의 상태를 proposed에서 accepted로 바꾸고 색인의 상태도 함께 바꿉니다. 그다음 ADR 0046(Agent OS는 위젯을 모른다)을 보여 드립니다.

반영: PRD 두 줄(전제, 미룬 것)을 고쳤다. ADR 0046의 `status`와 색인 행을 accepted로 바꿨다.

## ADR 0047 승인

리뷰로 끊을 연결이 넷이 되어 ADR 0024 이력의 "끊을 연결 셋"을 "넷"으로 고친 뒤, 결정(의존은 위젯에서 Agent OS로 한쪽, 모른다는 것은 import와 위젯 전용 경로·기능을 두지 않는 것), 화면의 장면(관리 화면에 위젯 외형 메뉴가 없다), 사이트 파일, 떼어 낼 신호 넷, 지키는 장치, 끊을 연결 넷, 치르는 값 둘로 요약해 보였다.

> 사용자: (ADR 0046(Agent OS는 위젯을 모른다: 관리 화면과 serve에 위젯 전용 기능을 두지 않는다)을 이대로 승인하시겠습니까?) "이대로 승인" — 설명: ADR 0046의 상태를 proposed에서 accepted로 바꾸고 색인의 상태도 함께 바꿉니다. 그다음 ADR 0047(문서 검색 서버는 다른 저장소다)을 보여 드립니다.

반영: ADR 0047의 `status`와 색인 행을 accepted로 바꿨다.

## ADR 0048 승인

보이기 전에 "런타임(`src/`)은 calc를 모르듯"을 `git grep -n -w calc -- src`로 대 봤다(경로 예시를 든 주석 한 줄뿐, `admin/http.py` 177줄). 저장소 둘의 표, 한 방향 의존, 검색 도구 형식의 계약과 판, 읽기 도구만, 배포와 운영, 서비스마다의 데이터베이스, 포트 하나와 제품의 판, 치르는 값 셋으로 요약해 보였다.

> 사용자: (ADR 0047(문서 검색 서버는 agent-os 밖의 저장소이고, 런타임은 그 서버를 모른다)을 이대로 승인하시겠습니까?) "이대로 승인" — 설명: ADR 0047의 상태를 proposed에서 accepted로 바꾸고 색인의 상태도 함께 바꿉니다. 그다음 제안서 3·4절대로 .scratch/plan.md를 고치고, 11~13절을 .scratch/doc-qa-direction/inputs.md에 둡니다.

반영: ADR 0048의 `status`와 색인 행을 accepted로 바꿨다.

## 인터뷰 입력의 자리를 다시 정했다

`plan.md`를 고치기 전에 `tools/check_ticket.py`의 면제 모양을 읽고 그 `exempt`를 후보 경로로 불러 봤다. `.scratch/doc-qa-direction/inputs.md`는 `False`이고, `plan.md`·일지·ADR·기능 폴더의 `spec.md`·`probes/`·`design/` 아래는 `True`였다. 그 파일을 만들면 이 `docs/` 브랜치의 커밋이 판정 7로 막힌다. 대조 절에서 자리를 정할 때 면제 목록을 대 보지 않았고, 셀프 리뷰 두 축도 "파일이 아직 없다"까지만 봤다. 승인받은 ADR 0046의 자리 문장이 바뀌므로 고치기 전에 물었다.

> 사용자: (제안서 11~13절(GPU 환경과 요금, 모델 배치 구성, 남은 확인)을 어디에 둘까요?) "이 일지에 둔다 (Recommended)" — 설명: 이 세션의 일지(docs/journal/2026-11-06-02)에 '설계 인터뷰 입력' 절을 두고, local-model·answer-eval·deploy-package 같은 행의 내용 칸이 그 절을 가리킵니다. 요금은 조사 시점의 기록이라 일지와 성격이 맞고, 커밋 검사도 지납니다. 일지는 나중에 고치지 않으므로, 요금이나 모델 선택은 그 행의 설계 인터뷰가 다시 확인해 명세에 적습니다. ADR 0045의 자리 문장 하나를 일지를 가리키도록 고칩니다.

반영: ADR 0046 Consequences의 `.scratch/plan.md` 줄을 "그 행의 내용 칸"과 "일지 2026-11-06-02의 '설계 인터뷰 입력' 절"로 고쳤다. 고르지 않은 선택지(라벨만): "면제 목록을 넓힌다".

## 설계 인터뷰 입력(제안서 11~13절)

ADR 0046 Consequences와 `plan.md`의 행(local-model, answer-eval, deploy-package 등)이 이 절을 가리킨다. 제안서 11~13절을 옮기며 낱말을 이 저장소의 말로 바꾸고(설치 환경 → 배포 환경, install-package → deploy-package, RAG 서버 → 문서 검색 서버), 근거의 종류 표시(제안서의 기록, 어림, 웹 요약)를 더했으며, 요금을 다시 확인하라는 문장은 이 머리로 옮겼다. 요금, 기동 시간, 할당량, vLLM의 요구 사양은 제안서가 웹 글에서 옮긴 것이고, 이 세션은 그 원문을 열어 대 보지 않았다(웹 요약). 로컬 PC의 GPU 사양도 제안서에 적힌 것이고 이 세션이 장치를 보지는 않았다. 일지는 나중에 고치지 않으므로, 그 행의 설계 인터뷰가 쓰기 전에 다시 확인해 명세에 적는다. 제안서 10절의 위험은 이 절이 아니라 각 행의 내용 칸에 "설계 인터뷰가 먼저 볼 것"으로 넣었다.

### GPU 환경(제안서 11절)

local-model의 시험 엔드포인트, answer-eval의 평가, deploy-package의 대상 사양 측정이 같은 환경을 쓴다. 문서 검색 서버의 검색 지연 측정도 이 환경을 쓴다.

로컬 PC로 되는 것. 로컬 PC의 GPU는 GTX 1660 Ti(VRAM 6GB, compute capability 7.5)다(제안서의 기록).

- LLM은 로컬에서 돌리지 않는다. 평소 기능 개발은 지금처럼 Anthropic API로 하고, 로컬 모델과의 호환과 측정은 클라우드 GPU의 vLLM으로 한다. 그래서 GPU를 빌리는 시간은 호환 시험과 측정에 쓰는 시간으로 줄어든다.
- 임베딩과 리랭커는 문서 검색 서버를 개발하는 동안 로컬 PC(CPU나 GPU)에서 돌린다. 수억 파라미터급 모델이라 개발용 문서 양에는 충분하다(어림).
- vLLM의 최소 요구(compute capability 7.5)는 맞지만, 6GB로는 쓸 만한 모델을 올리기 어렵고 리눅스 전용이다(Windows는 WSL을 거친다). 그래서 로컬에서는 쓰지 않는다.

24GB GPU에 드는 모델(어림). 가중치 크기는 "파라미터 수 × 파라미터당 바이트"로 어림하고, 그 위에 KV 캐시를 위한 여유가 필요하다. 24GB GPU에는 16비트 7~8B 모델(가중치 약 15~16GB)이나 4비트로 양자화한 14B 안팎 모델(가중치 약 7~8GB)이 든다. 정확한 값은 고른 모델과 문맥 길이로 잰다.

클라우드 GPU 선택지. 괄호의 달은 제안서가 적은 조사 시점이다(웹 요약).

| 선택지 | 요금(조사 시점) | 맞는 용도 | 주의 |
|---|---|---|---|
| RunPod Pod, 24GB급(RTX A5000, RTX 3090, RTX 4090) | 시간당 $0.16, $0.22, $0.34 (2026-11) | 작업하는 동안만 켜 두는 개발용 vLLM 서버 | 끝나면 반드시 멈춘다. 같은 RTX 4090도 Secure Cloud는 시간당 $0.89다(2026-10) |
| RunPod Pod, L4(24GB), L40S(48GB) | 시간당 $0.44, $0.79 (2026-11) | 대상 사양 측정(데이터센터 GPU) | 측정할 때만 몇 시간 빌린다 |
| RunPod Serverless, 24GB급 | 시간 환산 $0.69, 초 단위 과금, 쉬면 0으로 줄어든다 (2026-08) | 가끔 도는 자동 평가 | 새 작업자가 뜰 때 모델 로딩 지연이 있다 |
| Modal | 매월 $30 무료 크레딧(A10G 기준 약 27시간), 초 단위 과금, 쉬면 0으로 줄어든다 (2026-10) | 가끔 쓰는 평가와 데모 | vLLM 첫 기동이 45~120초다(스냅숏 없이, Modal이 낸 수치) |
| Vast.ai 마켓플레이스 | RTX 4090 시간당 $0.29~0.50 관측 (2026-03~07) | 가장 싼 일회성 작업 | 호스트마다 안정성이 달라 호스트를 직접 확인해야 한다 |
| AWS EC2 서울 리전, g6.xlarge(L4 24GB), g6e.xlarge(L40S 48GB) | 온디맨드 시간당 약 $0.99, $2.29. 스팟 시간당 약 $0.46, $1.25 (2026-11 조회) | 데이터가 국내 리전에 있어야 하는 측정, 클라우드 배치 구성의 시험 | 같은 GPU가 RunPod의 2~3배다. 새 계정은 GPU 인스턴스의 vCPU 할당량 기본값이 0이라 증설을 먼저 요청한다. 디스크(EBS)와 외부 전송 요금이 따로 붙는다 |

권하는 조합.

1. 평소 기능 개발은 GPU를 켜지 않고 Anthropic API로 한다. 에이전트와 문서 검색의 동작을 고치는 반복은 대부분 여기서 일어난다.
2. 로컬 모델 호환 시험과 vLLM 위의 개발은 그 작업을 하는 시간에만 RunPod의 24GB급 Pod를 켜서 vLLM을 띄운다. 하루 4시간, 한 달 22일(88시간)이면 RTX A5000 기준 약 $14, RTX 4090 기준 약 $30이다. 같은 시간을 AWS 서울 리전의 g6.xlarge 온디맨드로 쓰면 약 $87이다(위 표의 시간당 요금을 곱한 어림). 모델 파일은 네트워크 볼륨(GB당 월 $0.07, 2026-08)에 두어 매번 받지 않는다. Pod의 주소는 밖에서 접속할 수 있으므로 vLLM을 `--api-key`로 막는다.
3. 자동 평가(answer-eval)는 Modal 무료 크레딧이나 RunPod Serverless로 돌려, 쉬는 동안에는 요금이 나가지 않게 한다.
4. 대상 사양 측정(deploy-package)은 L4나 L40S를 몇 시간 빌려 지연과 동시 처리량을 잰다. 데이터가 국내에 있어야 하면 AWS 서울 리전의 스팟을 쓴다.

데이터 규칙.

- 커뮤니티 클라우드와 마켓플레이스 호스트(RunPod Community Cloud, Vast.ai)는 제3자의 장비이므로 공개 문서만 올린다.
- 공개되지 않은 문서는 그런 장비에 올리지 않는다. 그 문서를 가진 쪽이 허용한 보안 수준의 환경에서만 처리한다.

제안서가 든 출처(이 세션은 열지 않았다).

- vLLM GPU 설치 문서: https://docs.vllm.ai/en/latest/getting_started/installation/gpu/
- RunPod 요금(gpuperhour, 2026-11): https://gpuperhour.com/providers/runpod
- RunPod Serverless와 저장소 요금(Hivenet, 2026-08-20 기준): https://www.hivenet.com/post/runpod-pricing-complete-guide-to-gpu-cloud-costs
- RunPod와 Vast.ai의 RTX 4090 요금(SynpixCloud, 2026-10-27 검토): https://www.synpixcloud.com/blog/vast-ai-vs-runpod-rtx-4090-pricing
- Modal 요금과 vLLM 배포(DEV Community, 2026-10-28 갱신): https://dev.to/jangwook_kim_e31e7291ad98/modal-labs-serverless-gpu-for-vllm-with-no-yaml-le5
- AWS g6.xlarge 서울 리전 요금(DoiT, 2026-11-05 조회): https://www.doit.com/compute/compute/aws/ap-northeast-2/g6.xlarge
- AWS g6e.xlarge 서울 리전 요금(DoiT, 2026-11-05 조회): https://www.doit.com/compute/compute/aws/ap-northeast-2/g6e.xlarge
- EC2 인스턴스 유형별 할당량 기본값(AWS 문서): https://docs.aws.amazon.com/ec2/latest/instancetypes/ec2-instance-quotas.html

### 모델 배치 구성(제안서 12절)

배포 환경에 GPU 서버가 없다고 해서 곧바로 클라우드 API로 가는 것은 아니다. 구성은 "그 환경이 문서를 밖으로 보낼 수 있는가"로 갈린다. 어느 구성이든 색인과 원본 문서와 검색(문서 검색 서버)은 배포 환경의 서버에 남고, 바뀌는 것은 답을 만드는 LLM이 어디서 도는가뿐이다.

| 배포 환경의 조건 | LLM 구성 | 밖으로 나가는 것 | agent-os에서 맡는 기능 |
|---|---|---|---|
| 문서를 밖으로 보낼 수 없다(폐쇄망, 민감 문서) | 배포 환경의 GPU 서버에서 vLLM으로 서빙 | 없음 | local-model |
| 보낼 수 있지만 국내 보관이나 보안 인증이 필요하다 | 국내 리전이나 국내 클라우드의 LLM 엔드포인트 | 질문과 검색된 조각 | local-model(OpenAI 호환일 때) 또는 공급자 어댑터 추가 |
| 제한이 없다 | 상용 클라우드 API | 질문과 검색된 조각 | 지금의 Anthropic 공급자, 또는 local-model의 OpenAI 호환 어댑터 |

API를 쓰는 구성에서도 문서 조각은 밖으로 나간다. 문서 전체는 배포 환경의 서버에 남지만, 답을 만들려면 검색된 조각을 질문과 함께 LLM에 보내야 하기 때문이다. deploy-package의 안내 문서에 이 사실을 적는다.

### 남은 확인(제안서 13절)

- 24GB GPU에 들어가면서 상용 이용이 가능한 한국어 오픈 모델을 고른다. local-model 수락의 모델 둘과 answer-eval의 모델 비교에 쓴다. 제안서는 K-EXAONE 2.0의 Apache 2.0 전환을 블로그 한 곳에서만 확인했고, 그 모델은 FP8로도 약 750GB라 24GB GPU에 들어가지 않는다고 적었다(웹 요약).
- NPU 서빙 소프트웨어(퓨리오사AI, 리벨리온)가 OpenAI 호환 API를 내는지, 도구 호출을 지원하는지, 어떤 모델을 지원하는지 확인한다. local-model의 경계가 GPU 밖에서도 성립하는지가 여기에 달려 있다.

## plan.md 반영

고치기 전에 `git fetch` 뒤 `git log 83a66cdc..origin/main`이 비었고(main은 그대로), 열린 PR이 없었다(`gh pr list --state open`). 표의 approval-rules 행 아래 열여섯 행을 새 차례의 서른하나로 바꾸고(스크래치패드의 스크립트로 행을 갈아 끼웠다), 프론티어 문단 끝에 2026-11-06 문장을 더했다. 제안서 3·4절과 달라진 곳은 위 결정(approval-rules는 슬라이스 7 그대로, mcp-trust는 approval-rules와 pilot-release에 막힌다)과 용어, ADR 번호(제안서의 0044·0045·0046 → 0046·0047·0048, 아래 "번호를 옮겼다" 절) 말고 다음과 같다.

- doc-qa-agent의 Blocked by에 approval-rules를 더했다. 사용자의 답("doc-qa와 참조 배포가 검색 도구를 허락하는 규칙 파일을 함께 내야 합니다")에서 따라 나온다고 판단했고 따로 묻지 않았다. 규칙 파일의 꼴은 approval-rules가 정하고, pilot-release가 approval-rules를 기다리게 하는 길(그래야 0.1의 알려진 한계에서 "운영자 승인 규칙 없음"이 빠진다)이 표에서 이것 하나다.
- 제안서 문장을 저장소의 사실에 맞춰 고쳤다. local-model의 "(ADR 0040 이력)"은 엔드포인트 자리를 정하면 ADR 0040의 이력에 적는다는 뜻으로 옮기고, 둘째 제공사가 가산 변경이라는 근거는 ADR 0040 Consequences의 "이번 범위 밖"으로 댔다. pilot-portal의 "계정 관리와 멀티테넌시는 … PRD의 미룬 것"은 PRD의 미룬 것에 멀티테넌시만 있어 둘을 갈랐다. diag-bundle의 "최종 사용자의 글과 문서 조각(PRD의 알아 둘 사실)"은 PRD가 글만 적어 문서 조각을 괄호 밖으로 뺐다. release-image의 Dockerfile은 ADR 0043 26줄("실제 이미지의 compose e2e(Dockerfile과 compose를 새로 짓는다)", 잡 이름과 모양은 harness 티켓)에 맞췄다. pilot-release의 알려진 한계는 ADR 0046 Consequences "기준선 판의 강제"대로 "MCP 서버의 신뢰 수준과 값 기반 마스킹 없음"으로 바꿨다.
- 받는 쪽에 넘긴 것을 적었다(`docs/agents/issue-tracker.md`의 "행에는 다른 기능이 넘긴 것을 적되"). approval-rules와 mcp-http에 ADR 0046의 "같은 파일을 고치는 두 행", mcp-trust에 ADR 0046의 "문서 속 지시", principal-propagation에 ADR 0048의 주체 형식, trace-postgres에 audit-export의 포트 읽기와 ADR 0048의 데이터베이스, replay-evaluation에 answer-eval의 평가 표다. approval-rules 행은 approval-rules-tickets 세션이 고칠 수 있는 줄이라 나중에 병합하는 쪽이 그 줄의 충돌을 푼다.
- `CONTEXT.md`의 값 기반 마스킹 `_Avoid_`의 "PII 마스킹(미룬 것)"이 승인한 PRD의 미룬 것과 어긋나 "패턴으로 잡히는 개인정보는 제품 1.0의 입출력 가드레일이 맡고, 나머지 탐지는 미룬 것"으로 고쳤다(잔존 grep으로 찾았다).

## 셀프 리뷰 둘째(plan.md와 설계 인터뷰 입력 절)

앞선 셀프 리뷰 뒤에 쓴 세 곳(plan.md, 이 일지의 "설계 인터뷰 입력" 절, `CONTEXT.md` 한 줄)만 두 축으로 봤다. base `83a66cd`, 커밋 0. 표준 축은 sonnet·high, 명세 축은 지정 없음. 두 축 모두 Critical·Major는 없었다.

표준 축이 낸 것(요지): pilot-portal의 "제안서의 일정 어림은 이 행에 3주"는 저장소에서 대 볼 수 없는 근거다. pilot-release의 "스캔본과 HWP 바이너리 미지원"은 저장소 어디에도 근거가 없다. mcp-http의 "`[dependency-groups]` 위 주석"은 자리가 틀렸다(주석은 그 머리 줄 아래). deploy-package의 "운영 담당자"는 용어집의 운영자이고 "위젯 번들"의 "번들"은 `_Avoid_`다("관리자 페이지"는 ADR 0048이 이미 쓴다). mcp-http가 ADR 0042 "원격 MCP"의 모양을 다시 적어 "계약의 모양은 ADR 번호로만 가리킨다"(`docs/agents/issue-tracker.md`)와 어긋난다. 판단 항목으로 trace-postgres의 "배포의 프로세스가 넷"이 참조 배포의 컨테이너 수와 헷갈린다, release-image의 Dockerfile 몫이 조건부다, 일지의 vLLM 요구 사양에 웹 요약 표시가 없다. 맞는 것으로 확인한 것: 프론티어 넷, approval-rules에 `issues/`가 없음, ADR 0040 "이번 범위 밖", `streamable_http_client`의 인자, `uv.lock`의 httpx2 2.13.0, 요금 셈.

명세 축이 낸 것(요지): deploy-package에서 GPU 환경을 가리키는 괄호가 빠졌다. ADR 0046의 "같은 파일을 고치는 두 행"이 approval-rules 행에 없다. local-model에서 "(ADR 0040 이력)"이 빠졌다. doc-qa-agent의 Blocked by에 approval-rules를 더한 것은 범위 안이지만 일지에 결정으로 적을 것. mcp-trust의 "ADR 0046이 넘긴 것" 가운데 "그 서버를 어느 신뢰 수준으로 둘지"는 ADR 0046에 없는 추론이다. "3주"는 제안서 원문이 "2~3주"다. 이 절 머리의 "낱말만 … 바꿨다"는 닫힌 주장이고 반례(근거 종류 표시, 옮긴 문장)가 있다. 맞는 것으로 확인한 것: 10절 위험 일곱이 모두 행에 들었다, 11~13절이 빠짐없이 옮겨졌다, 4절의 바꿀 것 여섯이 반영됐다, 인용 여섯이 원문과 같다.

고친 것(근거를 열고 판정했다):

- pilot-portal: "로그인 방식을 하나로 좁힌다(넓히면 기준선의 일정이 늘어난다, 어림)."
- pilot-release: "알려진 한계: MCP 서버의 신뢰 수준과 값 기반 마스킹 없음(ADR 0046), 단일 인스턴스, 문서별 권한과 입출력 가드레일과 감사 조회 없음. 지원 문서 형식은 문서 검색 서버가 정하고, 제안서는 스캔본과 HWP 바이너리를 지원하지 않는 형식으로 들었다"
- mcp-http: "첫 티켓은 계약이다: 모양은 ADR 0042 "원격 MCP" 줄에서 출발한다."와 "(`pyproject.toml`의 `[dependency-groups]` 첫 주석, ADR 0023의 pyjwt)"(`pyproject.toml` 34~38줄을 `grep -n`으로 봤다).
- deploy-package: "운영 담당자" → "운영자" 두 곳, "위젯 번들처럼" → "위젯처럼", "GPU 등급은 … 잰 값을 근거로 한다(일지 2026-11-06-02의 "설계 인터뷰 입력" 절, GPU 환경의 권하는 조합 4)".
- local-model: "설계 인터뷰가 정해 ADR 0040의 이력에 적는다".
- approval-rules: "ADR 0046이 넘긴 것: mcp-http와 둘 다 `adapters/mcp.py`를 고치므로, 나중에 병합하는 쪽이 충돌을 풀고 도구마다 싣는 서버 이름이 원격 MCP 서버의 도구에도 실리는지를 시험으로 본다."
- mcp-trust: ADR 0046에 없는 신뢰 수준 문장을 뺐다.
- trace-postgres: "agent-os 배포의 프로세스가 넷".
- 이 일지의 "설계 인터뷰 입력" 절 머리: "낱말을 … 바꾸고, 근거의 종류 표시(제안서의 기록, 어림, 웹 요약)를 더했으며, 요금을 다시 확인하라는 문장은 이 머리로 옮겼다. 요금, 기동 시간, 할당량, vLLM의 요구 사양은 …(웹 요약)."
- doc-qa-agent의 Blocked by는 위 "plan.md 반영" 절에 결정으로 적었다.

남긴 것과 이유:

- "관리자 페이지"(deploy-package, run-feedback): 문서 검색 서버의 화면을 이르는 말이고 승인된 ADR 0048이 같은 낱말을 쓴다. 용어집의 운영자 `_Avoid_`는 Agent OS의 운영자를 부르는 말에 걸린다.
- release-image의 조건부 Dockerfile 몫: ADR 0043 26줄이 Dockerfile을 새로 짓는다고만 하고 누가 짓는지 정하지 않았고, 그 harness 티켓은 아직 없다. 먼저 오는 쪽이 짓는다는 문장이 그 빈자리를 메운다. 판단 항목.
- 살아 있는 `plan.md`가 기록인 일지를 가리키는 것: 사용자가 고른 자리다.

PR 직전 리뷰에 밀 주장으로 넘길 새 문장: pilot-release의 "지원 문서 형식은 문서 검색 서버가 정하고", approval-rules 행의 "ADR 0046이 넘긴 것", "(`pyproject.toml`의 `[dependency-groups]` 첫 주석, ADR 0023의 pyjwt)", "GPU 환경의 권하는 조합 4", 이 일지 "설계 인터뷰 입력" 절 머리의 표시 목록, "plan.md 반영" 절의 "표에서 이것 하나다".

다시 돌린 명령: `uv run python tools/check_adr_pointers.py`(0), `uv run python tools/check_md_tables.py`(바뀐 마크다운, 0), `uv run pytest -q tests/test_plan_status.py`(고치기 전에 12 passed). 나머지 검증 명령은 커밋의 pre-commit으로 갈음한다.

## 번호를 옮겼다

커밋 직전의 `uv run python tools/sibling_overlap.py`가 1로 끝났다. 워크트리 `retro-queue-per-item`의 커밋하지 않은 변경이 `docs/adr/0045-coordination-state-is-one-file-per-item-named-by-slug.md`를 들고 있어 이 브랜치의 ADR 0045와 번호가 겹쳤고, 출력의 "옮길 번호"는 ADR 0045 → 0046, 0046 → 0047, 0047 → 0048이었다. 사용자가 PRD를 승인하며 고른 설명("ADR 번호(0045·0046·0047)는 다른 세션이 먼저 가져가면 같이 옮깁니다")이 이 경우라 묻지 않고 `--move`로 옮겼다. 같은 출력에서 PR #472(approval-rules-tickets)와 두 워크트리가 `.scratch/plan.md`를, `retro-queue-per-item`이 `CONTEXT.md`·ADR 0042·색인을 함께 고친다고 나와, 나중에 병합하는 쪽이 그 충돌을 푼다.

도구가 옮긴 것은 파일 이름 셋과 `ADR NNNN` 꼴의 인용이다(plan.md, PRD, ADR 0024·0042·0044·0046·0048, 색인, 이 일지). `>` 인용 줄은 옮기지 않았다. 손으로 고친 것: 0045가 0046이 되며 받침이 생긴 조사 열 곳(`0046가` → `0046이` 등, plan.md·ADR 0042 이력·이 일지), 이 일지 "인계 전 상태"의 "ADR 0046 → 0046 → 0047"(낱말 없는 번호가 옮겨지지 않았다)과 인계 지시문의 "ADR 0046~0047". 이 절 위의 글에서 낱말 없이 든 번호(대조 절의 "0044·0045·0046은 0045·0046·0047로", ADR 초안 절의 "0045(…), 0046(…), 0047(…)", 인계 전 상태의 "번호는 0045~0047", 명세 축의 "번호 0045~0047은 다음 빈 번호다")와 사용자 인용은 그때의 번호 그대로다. 지금 번호로는 기준선과 제품 1.0이 ADR 0046, 위젯 경계가 ADR 0047, 문서 검색 서버가 ADR 0048이다.

## PR 직전 리뷰

커밋 81f9ea41 뒤 `git fetch`에서 `git log 83a66cdc..origin/main`이 비어 합칠 것이 없었다. `coderabbit-review` 서브에이전트가 `coderabbit auth status`를 보니 CLI 0.7.5에 `Plan: Free`, `Seat: not assigned`였고, `coderabbit review`는 돌리지 않았다(서브에이전트의 보고). 그래서 대체 둘(`bug-perf-review`, `/security-review`)을 돌린다.

`/security-review`: 합칠 것이 없어 커밋 뒤 바로 돌렸다. 그 명령이 모은 범위는 커밋 81f9ea41 하나와 바뀐 파일 열하나(모두 마크다운)였다. 취약점 식별 서브태스크는 찾은 것이 없다고 보고했다. 바뀐 파일에 코드·설정·워크플로·스크립트가 없어 새 공격 면이 없고, diff에서 비밀 값 모양(API 키·토큰 접두사, 대입 꼴, 주소 안의 인증 정보, 긴 영숫자 덩어리)과 개인정보 모양(이메일, 주민등록번호·전화번호)을 grep해 실제 값이 0건이었다(`secret_args`·`--api-key`는 이름뿐, io-guardrail 행의 "주민등록번호, 계좌번호, 전화번호"는 막을 종류의 이름이다). 찾은 것이 없어 거짓 양성 거르기 서브태스크는 돌리지 않았다.

`bug-perf-review`: 범위는 base `83a66cd`, 문서 열한 파일, 미추적 0이었다. 유효 셋(모두 Minor, 고치는 값 작음), 보류 0, 오탐 열여섯 줄이 나왔고 성능 축은 해당이 없었다. 유효 셋은 다음과 같다.

- ADR 0042 2026-11-06 이력의 "바뀐 것은 여섯이다"는 열거로 재현되지 않는다(센 사람은 일곱이나 여덟을 얻는다).
- ADR 0046 Consequences "같은 PR에 드는 것"이 `CONTEXT.md`를 "배포 환경·참조 배포·문서 검색 서버"로 닫아 적었는데, diff에는 참조 에이전트, 참조 클라이언트, 값 기반 마스킹 `_Avoid_`도 들었다(첫 셀프 리뷰에서 더한 것을 ADR이 따라가지 못했다).
- plan.md deploy-package 수락의 "밖으로 열린 포트가 443과 SSH뿐"이 PRD와 ADR 0046 14줄의 "밖으로 여는 포트는 하나다"와 어긋난다.

오탐으로 대 본 밀 주장: ADR 0046의 다섯 묶음 이름, 위젯 질문자의 직접 승인(ADR 0044 29·63줄), PostgreSQL·Redis와 worker의 시점, ADR 0047의 "모두 주석과 독스트링"(`git grep` 스물여덟 줄에 코드 줄 0), 끊을 연결의 줄 근거, approval-rules 행의 넘긴 것(ADR 0046 66줄, `adapters/mcp.py` 있음), mcp-http의 근거(`uv.lock`, `streamable_http_client`를 `inspect.signature`로 불렀다, `pyproject.toml` 35~38줄), "권하는 조합 4", 설계 인터뷰 입력 머리의 표시, "표에서 이것 하나다"(Blocked by에 approval-rules가 든 행은 doc-qa-agent와 mcp-trust 둘이고 mcp-trust는 pilot-release 뒤), 번호 옮기기 뒤 조사와 옛 번호(0건). 서브에이전트가 따라가지 못했다고 적은 것: 제안서 원문은 발췌로만 대 봤다, `tools/check_ticket.py`는 돌리지 않았다, ADR 0046 8줄의 base 표 Blocked by 문장은 대 보지 않았다.

고친 것(근거를 열고 판정했다):

- ADR 0042 이력: "바뀐 것은 여섯이다."를 뺐다. 셀 기준이 본문에 없어 수로 닫지 않는다. 같은 말을 인용한 곳은 이 일지(기록)뿐이다(grep).
- ADR 0046 Consequences: "`CONTEXT.md`의 용어(배포 환경, 참조 배포, 참조 에이전트, 참조 클라이언트, 문서 검색 서버)와 값 기반 마스킹의 `_Avoid_`"(`git diff -U0 83a66cdc -- CONTEXT.md`로 굵은 용어 다섯과 `_Avoid_` 한 줄을 봤다). 승인받은 ADR의 글이지만, 결정이 아니라 같은 PR에 든 파일의 목록을 사실에 맞춘 것이다.
- plan.md deploy-package 수락: "그 VM에서 밖으로 열린 포트가 배포가 여는 443과 VM을 관리하는 SSH뿐임을 확인한다". 제안서 141줄도 443과 SSH를 함께 들고, 같은 행 앞 문장이 "밖으로 여는 포트는 … 443 하나"라 배포의 포트와 VM의 포트를 갈랐다. 승인받은 PRD는 고치지 않았다.

PR 봇에 밀 주장으로 넘길 새 문장: ADR 0046의 `CONTEXT.md` 목록, plan.md의 "배포가 여는 443과 VM을 관리하는 SSH".

다시 돌린 명령: `uv run python tools/check_adr_pointers.py`(0), `uv run python tools/check_md_tables.py`(바뀐 마크다운 넷, 0), `uv run pytest -q tests/test_plan_status.py`(12 passed). 나머지 검증 명령은 반영 커밋의 pre-commit으로 갈음한다. 반영 커밋 06ca5929의 pre-commit은 모두 Passed였다(pytest 517.5s, web-verify 535.2s. ruff 둘과 카나리아·헌법 판 검사는 대상 파일이 없어 Skipped).

## main을 합쳤다

push를 훅이 막았다. 그 사이 PR #472(approval-rules 티켓 여섯)가 main에 병합되어(15f11711) 이 브랜치가 한 커밋 뒤처졌다. `git merge origin/main`이 `.scratch/plan.md`에서 충돌했다. main이 기준 `83a66cd`에서 바꾼 줄은 approval-rules 행과 프론티어 문단 둘뿐이었고(스크래치패드의 스크립트가 줄마다 견줘 확인했다), 이렇게 풀었다.

- approval-rules 행: main의 행(티켓 여섯과 그 차례, "다음은 막힌 것이 없는 01 이다")에 이 브랜치의 "ADR 0046이 넘긴 것" 문장을 같은 자리(관리 API·관리 화면 문장 뒤)에 넣었다.
- 프론티어 문단: 날짜 차례대로 main의 2026-11-06 문장(티켓 분할, 다음은 01) 뒤에 이 브랜치의 2026-11-06 문장(ADR 0046)을 이었다. 이 브랜치 문장의 "approval-rules 는 그대로 명세 검토와 티켓(to-tickets)이 다음이고"를 "approval-rules 는 위대로 막힌 것이 없는 티켓 01(계약)이 다음이고"로 고쳤다.

ADR 0046~0048, ADR 0042, PRD, `CONTEXT.md`에는 approval-rules의 다음 단계를 적은 문장이 없었다(`to-tickets`·`명세 검토` grep 0건). 합친 뒤 `uv run pytest -q tests/test_plan_status.py`(12 passed), `uv run python tools/check_md_tables.py .scratch/plan.md`(0).
