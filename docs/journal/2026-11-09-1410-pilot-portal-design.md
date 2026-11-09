# 2026-11-09 (14:10) pilot-portal 설계 인터뷰

세션 제목: `docs/pilot-portal-design`. 브랜치 `docs/pilot-portal-design`, 워크트리 `.claude/worktrees/pilot-portal-design`. 모델 Fable 5.1 / xhigh. 주 체크아웃에서 시작해 `EnterWorktree`로 들어온 뒤 브랜치 이름을 지시문대로 바꿨다. 나란히 도는 mcp-http 설계 인터뷰(브랜치 `docs/mcp-http-design`, 워크트리 `.claude/worktrees/mcp-http-design`)가 이미 ADR 0049를 썼으므로 이 기능의 ADR은 0050으로 간다.

## 사용자 프롬프트

> 사용자: .claude/skills/grill-with-docs/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: pilot-portal
>
> 다음 작업: 기능 pilot-portal. 위젯을 담는 질문 페이지가 로그인 없이 온 사람에게 사이트 토큰을 내, 포털이 없는 공개 데모와 배포 환경을 돕는다
> 다음 단계: 설계 인터뷰
> 어디서: 새 세션. 사용자가 mcp-http 설계 인터뷰와 나란히 열라고 했다. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /grill-with-docs pilot-portal
> 브랜치: docs/pilot-portal-design
> 모델: Fable 5.1 / xhigh
> 읽을 것: .scratch/pilot-portal/plan.md(설계 인터뷰가 먼저 볼 것과 수락). 함께 도는 mcp-http 설계 인터뷰(브랜치 docs/mcp-http-design)와 새 ADR 번호, CONTEXT.md 용어, ADR 0046 이력이 겹칠 수 있다
> 이어받을 상태: 없음
> 확인할 선행 조건: 없음
> 이번 요청 범위: PR과 병합까지

## 인터뷰 전에 대 본 사실

- 서명 토큰은 RS256 하나, 필수 클레임 다섯, 수명 600초까지, 시계 여유 30초다(`src/agent_os/http/sites.py`). 주체 이름은 `<발급자>|<sub>`이고 관리 화면은 `|`만으로 최종 사용자의 실행을 가른다(`web/apps/admin/components/organisms/RunDecision.tsx` 58줄).
- 위젯은 요청마다 사이트의 `tokenProvider`를 불러 새 토큰을 받고 10초 안에 답이 없으면 알림을 보인다(`web/apps/widget/EMBED.md`). 대화는 탭의 sessionStorage에 발급자와 `sub`로 묶어 두고 둘 중 하나가 바뀌면 지운다(`web/apps/widget/lib/storage.ts`, ADR 0024).
- web 워크스페이스의 ESLint는 Next 서버 파일(route, middleware, proxy, instrumentation)과 Server Actions를 모든 앱에서 막는다(`web/eslint.config.mjs`. 서버 파일은 92~95줄과 314~316줄, Server Actions는 74~90줄의 `RESTRICTED_SYNTAX`. 근거는 ADR 0019. 줄 번호는 셀프 리뷰가 고쳤다). 그래서 Next 앱 안에 개인 키로 서명하는 코드를 둘 수 없다.
- `node:http`로 작은 서버를 세운 선례는 위젯 e2e의 중계(`web/apps/widget/e2e/relay.ts`), `node:crypto`만으로 키 쌍과 토큰을 짓는 선례는 같은 폴더의 `token.ts`(수명 300초)다.
- `tech.md`의 웹 줄은 앱마다 스택을 적고 지금 두 앱(관리 화면, 위젯)은 Next다. ADR 0021은 "관리 화면은 Next 16과 React 19"라고 적는다. ADR 0024는 위젯에서 "정적 파일을 nginx가 서빙한다(Next 없음)"를 고르지 않았지만 거부하지도 않았다.
- `.scratch/plan.md`의 프론티어는 `local-model`, `mcp-http`, `pilot-portal`이다. 이웃 행은 public-demo(익명 모드의 질문 페이지를 쓴다. 고지의 내용, 사이트 하나만 두기, 프록시의 빈도 제한을 적는다), portal-login(모드 전환 뒤 남는 익명 토큰과 서명 키를 정한다), release-image(포털의 컨테이너 이미지를 짓는다)다.

## 설계 인터뷰 라운드 1

> 사용자: (질문 페이지(포털) 앱을 어떤 구성으로 만들까요?) "Node 서버 하나 (Recommended)" — 설명: 표준 라이브러리 node:http로 선 서버 하나가 페이지(HTML)와 토큰 끝점(/portal/token)을 함께 냅니다. 페이지는 서버가 설정값(제목, 고지 글, 에이전트 이름)으로 요청 때 그리고, 모양은 디자인 시스템의 CSS(@agent-os/ui가 내는 theme.css)를 씁니다. Next와 새 프레임워크 의존성이 없고 프로세스가 하나라 컨테이너 이미지도 하나입니다. 선례: 위젯 e2e의 중계가 node:http로 섰습니다. 대가: 지금 두 앱(관리 화면, 위젯)은 Next로 서 있어(ADR 0021·0024, tech.md 웹 줄) 모양이 다른 셋째 앱이 되고, 그 줄과 ADR에 적습니다. ADR 0024는 위젯에서 'Next 없음'을 고르지 않았지만 거부하지도 않았습니다.

> 사용자: (익명 최종 사용자의 주체 이름(트레이스에 남는 이름)을 어떤 꼴로 할까요?) "sub에 익명 표지 (Recommended)" — 설명: 토큰의 sub를 anon-<UUID>로 내어 주체가 <발급자>|anon-3f2a…처럼 됩니다. 트레이스와 관리 화면에서 사람이 익명 주체를 바로 알아봅니다(관리 화면은 지금 | 만으로 최종 사용자의 실행을 가릅니다, RunDecision.tsx). 뒤의 portal-login이 같은 발급자로 사내 계정 id를 sub로 낼 때 anon- 접두를 금지하면 두 모드의 주체가 글자로 겹치지 않습니다. 발급자는 페이지의 공개 출처(예: https://demo.example) 하나입니다.

> 사용자: (브라우저에 주는 식별자를 어디에 두고 얼마나 오래 쓸까요?) "서버 쿠키, 질문마다 30일 연장 (Recommended)" — 설명: 포털 서버가 UUID를 만들어 HttpOnly·Secure·SameSite=Strict 쿠키(경로 /portal)로 두고, 토큰을 낼 때마다 만료를 30일 뒤로 다시 적습니다. 마지막 질문 뒤 30일이 지나야 새 식별자가 되어, 대화 도중 식별자가 바뀌어 위젯이 대화를 지우는 일(위젯은 발급자나 sub가 바뀌면 저장을 지웁니다, lib/storage.ts)이 없습니다. 서버는 쿠키 값이 UUID 꼴이 아니면 새로 냅니다. 고지에 '식별자 쿠키를 둔다'를 적습니다.

> 사용자: (포털이 내는 토큰의 수명(exp - iat)을 얼마로 할까요?) "120초 (Recommended)" — 설명: 위젯이 요청마다 새 토큰을 받으므로(EMBED.md) 토큰은 요청 직후에만 쓰입니다. 2분이면 느린 망에서도 넉넉하고(서버가 30초 여유를 더 봐줍니다, http/sites.py), 밖으로 샌 토큰이나 모드를 바꾼 뒤 남는 옛 토큰(portal-login의 물음)이 살아 있는 시간이 짧습니다.

같은 라운드의 둘째 화면(frontier가 넷을 넘어 호출을 둘로 나눴다).

> 사용자: (고지(질문이 기록되고 모델 API에 보내진다, 개인정보를 넣지 말라 등)를 페이지의 어디에 둘까요?) "늘 보이는 고지 + 첫 질문 전 확인 한 번 (Recommended)" — 설명: 위젯 곁에 짧은 고지가 늘 보입니다. 식별자 쿠키가 없는 브라우저에는 서버가 안내문 전문과 '확인하고 질문하기' 버튼이 위젯을 덮은 모양으로 페이지를 그리고, 버튼을 누르면 식별자 쿠키를 받는 요청이 가고 덮개가 걷힙니다. 확인 전에는 쿠키도 토큰도 내지 않습니다. 쿠키가 있으면(앞 라운드의 30일 안에 확인한 브라우저) 덮개 없이 그립니다. 고지의 글은 배포 설정이 주고 포털은 기본 글을 듭니다(ADR 0047: 문구는 사이트가 가진다). 대가: 처음 온 사람에게 클릭 하나가 늘고, 서버가 쿠키 유무로 페이지를 두 모양으로 그립니다.

> 사용자: (포털 페이지가 위젯을 어떤 방식으로 담을까요?) "페이지 안 방식 (Recommended)" — 설명: 페이지에 <agent-os-widget agent=…> 요소와 같은 출처의 /widget/element.js 스크립트를 두고, tokenProvider가 같은 출처의 /portal/token을 fetch합니다. 같은 출처라 식별자 쿠키가 저절로 실리고 postMessage 규약이 필요 없습니다. 위젯은 shadow root에 그려 페이지의 CSS와 서로 닿지 않습니다(EMBED.md). 사이트 파일의 허용 출처는 공개 출처 하나입니다. 대가: 페이지의 스크립트가 토큰과 대화를 읽을 수 있는데, 페이지가 이 저장소의 것이라 새로 잃는 것이 없습니다.

> 사용자: (포털이 서명에 쓸 키 쌍은 어떻게 준비할까요?) "포털의 키 만들기 명령 (Recommended)" — 설명: 포털 앱에 키 만들기 명령 하나(이름은 명세가 짓습니다)를 두어, node:crypto로 RSA 2048 키 쌍을 만들고 개인 키를 준 경로에 PEM으로 쓰며, 사이트 파일에 붙일 [[sites.public_keys]] 조각(kid와 pem)을 출력합니다. 포털은 시작할 때 설정의 개인 키 경로와 kid를 읽고, 파일이 없거나 RSA 개인 키가 아니면 구성 오류로 끝납니다(fail-closed). 키 파일은 커밋하지 않습니다. 선례: 위젯 e2e의 token.ts가 같은 호출(generateKeyPairSync rsa 2048, spki pem)로 키를 만듭니다.

> 사용자: (포털의 설정(발급자, 대상, 개인 키 경로, 에이전트 이름, 제목, 고지 글 등)을 어떤 모양으로 받을까요?) "TOML 파일 하나를 시작 인자로 (Recommended)" — 설명: serve가 사이트 파일을 --site-file로 받듯, 포털도 설정 TOML 파일 하나를 시작 인자로 받습니다. 발급자, 대상, 개인 키 경로와 kid, 에이전트 이름, 제목·소개, 고지 글, 보고서 링크, 듣는 호스트·포트가 듭니다(정확한 칸은 명세가 짓습니다). 읽는 데는 위젯이 이미 쓰는 smol-toml을 씁니다. 모르는 키와 빠진 필수 키는 시작에서 구성 오류입니다. 고지 같은 여러 줄 글도 한 파일에 들어가고 배포 묶음에서 사이트 파일 곁에 나란히 놓입니다.

## 설계 인터뷰 라운드 2

라운드 1의 답이 연 가지들이다. 올리기 전에 대 본 사실: 위젯 e2e의 중계는 `/end-user/` 아래를 serve로, `/widget`과 `/widget/` 아래를 Next로 넘기고 나머지는 404로 답한다(`web/apps/widget/e2e/relay.ts` 머리). 쿠키는 `Path`가 요청 경로의 앞부분일 때만 실리므로(HTTP 쿠키 규격) 라운드 1의 쿠키 경로 `/portal`과 페이지가 `/`에 있는 배치는 함께 설 수 없다. 루프백만 받는 호스트 목록은 serve의 `LOOPBACK_HOSTS`(`main.py` 73줄), 관리 화면의 `tools/loopback.ts`, 위젯의 `tools/start.ts`(39줄) 세 곳이 따로 든다(ADR 0047 37줄). 상한 칸은 `limits.py`의 `concurrent_runs_per_principal`·`concurrent_runs_per_site`·`hourly_runs_per_principal`·`hourly_runs_per_site`·`request_chars`·`subscriptions_per_principal`이다. e2e 준비 코드는 관리 화면 `e2e/stack.ts` 354줄, 위젯 `e2e/stack.ts` 329줄로 앱마다 제 사본이고(`wc -l`), 위젯 e2e에는 중계 85줄, 픽스처 플러그인 138줄, 토큰 45줄이 더 있다. 워크스페이스 패키지는 `api-client`와 `ui` 둘이고, ESLint 경계 규칙은 앱 사이의 import를 막되(ADR 0047 10줄) 워크스페이스 패키지는 external로 보아 허용한다(`web/eslint.config.mjs` 229줄 주석). 첫 화면은 `hook_choice_facts`가 한 번 막아 위 사실을 대 본 뒤 같은 문장으로 다시 올렸다.

> 사용자: (포털이 내는 경로(페이지, 확인, 토큰)를 어디에 둘까요?) "모두 /portal/ 아래 (Recommended)" — 설명: 페이지는 /portal/, 확인과 토큰 끝점은 /portal/confirm·/portal/token처럼 /portal/ 아래에 모읍니다(끝점 이름은 명세가 짓습니다). 포털은 /를 받으면 /portal/로 302로 보냅니다. 라운드 1의 쿠키 경로 /portal과 맞아, 쿠키는 포털의 요청에만 실리고 같은 출처의 /widget/과 /end-user/ 요청에는 실리지 않습니다. 프록시 규칙은 = /와 /portal/ 둘이고, 위젯 e2e 중계처럼 그 밖은 404입니다. 대가: 공개 주소의 페이지 주소가 https://demo.example/portal/이 됩니다(루트로 들어오면 넘어갑니다).

> 사용자: (포털 서버는 어느 주소에서 들을까요?) "루프백만, 넷째 목록 (Recommended)" — 설명: serve와 두 Next 앱처럼 127.0.0.1과 ::1만 받고, 설정의 호스트가 그 밖이면 시작에서 구성 오류로 끝납니다(fail-closed, 위젯 start.ts와 같은 문구). 포털은 TLS를 끝내는 프록시 뒤에만 섭니다. 루프백 목록이 서로 다른 네 파일에 들게 되어 ADR 0047의 '바꾸면 함께 고친다' 줄에 포털을 더합니다. compose에서 프록시가 다른 컨테이너에 있을 때의 이음은 release-image 설계 인터뷰가 네 프로세스에 한꺼번에 정합니다.

> 사용자: (토큰 끝점에 포털 자체의 빈도 제한을 둘까요?) "두지 않는다, 무상태 (Recommended)" — 설명: 포털은 식별자를 저장하지 않고 쿠키 값의 꼴만 검사하는 무상태 서버입니다. 토큰은 서명 한 번이고 그 자체로는 비용이 들지 않으며, 실행의 비용은 serve의 주체별·사이트별 상한(limits.py)이, 요청 폭주는 프록시의 접속 주소별 빈도 제한(public-demo 계획)이 막습니다. 대가: 포털만 따로 두면 토큰 끝점을 두드리는 요청을 아무도 막지 않습니다(프록시 없이 두는 배치는 이 기능의 범위 밖입니다).

> 사용자: (포털 e2e의 준비 코드(serve·위젯 Next·중계 띄우기, 픽스처 플러그인)를 어디에 둘까요?) "워크스페이스 패키지로 빼서 함께 쓴다 (Recommended)" — 설명: 위젯 e2e의 중계·픽스처 플러그인·serve 띄우기를 새 워크스페이스 패키지(이름은 명세가 짓습니다. 테스트 전용 devDependency)로 옮기고, 위젯 e2e와 포털 e2e가 함께 import합니다. 앱 사이 import는 ESLint 경계가 막지만 워크스페이스 패키지는 허용됩니다. 중계는 상류를 셋(serve, 위젯 Next, 포털)으로 받게 넓힙니다. 대가: 위젯 e2e를 함께 고치는 티켓이 하나 들고, 관리 화면 e2e의 사본은 그대로 둡니다(이 기능의 범위 밖).

## 사용자가 앞서 말한 요구를 다시 꺼냄

라운드 2의 둘째 화면을 올리기 전에 사용자가 앞선 대화의 말을 붙여 넣고 반영됐는지 물었다.

> 사용자: 내가 agnet os 관리자 화면, rag engine 관리자 화면, 위젯 관리자 화면이 각각 있다고 하지 않았나? 위젯은 채널이 아니라 사이트라 위제 설정 같은 관리 화면이 필요하다고 했던거 같은데... 그리고 그리고 사이트마다 위젯을 설정할 수 있어야 하며 설정에는 어떤 에이전트를 쓸건지, 레이아웃 모양 아이콘 등등 적용할 수 있어야 해. 그리고 그 적용된 설정들을 실제 확인할 수 있는 페이지도 필요하고 예를들어 사이트를 선택할 수 있는 셀렉트 박스가 있고 선택된 사이트에 따라 설정된 위젯을 보여주고 테스트 해볼 수 있게. 익명 사용자는 사이트 설정에 따라 로그인이 필요한 위젯인지 익명으로 사용하는 위젯인지 아니면 둘다 지원하는지... — 이 내용 이제 반영 된거지?

찾아본 것: `docs/journal/*.md`, `.scratch/*/plan.md`·`spec.md`, `CONTEXT.md`, `docs/PRD.md`, 다른 워크트리(`.claude/worktrees/*/docs/journal`, 같은 자리의 `.scratch/*/plan.md`)를 "셀렉트", "위젯 관리", "레이아웃 모양", "둘다 지원", "로그인이 필요한 위젯"으로 Grep했다. 일치가 없다. 2026-10-03-03 일지의 "둘 다 지원하는 건 어때?"는 임베드 방식(script와 iframe)에 대한 답이고, 2026-11-03-04 일지는 "서비스"(에이전트 하나에 접근 정책·위젯 설정·보존 기간을 묶은 Notion 개념)가 우리에게는 없다고 적었다. 지금 계획과 어긋나는 자리: ADR 0047과 PRD 21줄(관리 화면은 위젯을 모른다, 위젯 관리 기능이 없다), `EMBED.md` 176줄(위젯의 모양은 속성 다섯뿐), portal-login 계획("한 배포에서는 하나만 쓴다"), 이 인터뷰의 라운드 1(TOML 파일 하나, 에이전트 하나). 반영되어 있지 않다고 답하고 어디까지 지금 반영할지 물었다.

> 사용자: (사이트마다 위젯을 설정하고 골라 보는 요구를 어디까지 지금 pilot-portal에 넣을까요?) "설정은 사이트 여럿, 미리보기까지 지금 (Recommended)" — 설명: pilot-portal의 설정 파일을 사이트 여럿의 목록으로 바꿉니다. 사이트마다 에이전트, 위젯이 지금 받는 모양 값(제목, 소개, 테마, 밝음), 모드(익명 / 로그인 / 둘 다)를 적습니다. 포털에 사이트를 고르는 셀렉트 박스가 있는 미리보기 페이지가 생겨, 고른 사이트의 설정으로 그린 위젯에 질문해 볼 수 있습니다. 이번에 실제로 도는 모드는 익명뿐이고, 로그인과 둘 다는 칸만 받아 두고 portal-login이 채웁니다(portal-login 계획의 '한 배포에는 하나만' 문장을 고칩니다). 설정을 화면에서 고치는 위젯 관리 화면과, 레이아웃·아이콘 같은 새 모양 칸은 새 기능 행으로 세웁니다. 대가: 이 인터뷰의 라운드 1 답 둘(TOML 파일 하나, 에이전트 하나)을 다시 묻고 티켓이 늘어 release-image와 public-demo가 그만큼 늦어집니다.

이 답으로 라운드 1의 "TOML 파일 하나를 시작 인자로"는 파일 하나는 그대로이되 안이 사이트 여럿의 목록이 되고, "페이지 안 방식"의 `<agent-os-widget agent=…>`는 고른 사이트의 설정으로 그려진다. 라운드 1의 "발급자는 페이지의 공개 출처 하나"와 "사이트 파일의 허용 출처는 공개 출처 하나"도 라운드 3에서 사이트마다의 발급자와 "공개 출처가 그 사이트의 허용 출처에 든다"는 시작 검사로 바뀐다(이 두 교체는 셀프 리뷰가 빠진 기록을 짚어 더했다). 설계 나무를 다시 세어 라운드 3을 올린다.

## 설계 인터뷰 라운드 3

사이트가 여럿이 되면서 열린 가지 넷. 올리기 전에 대 본 사실: serve의 CORS 허용 출처는 모든 사이트의 것을 합친 하나이고 사이트별로 가르지 않으며(`src/agent_os/http/sites.py` 114~123줄), 최종 사용자 경로는 `Origin`을 따로 검사하지 않는다(`channel/http/end_user.py`에 그 낱말이 없다). 열 에이전트 밖의 요청은 404 고정 문구다(같은 파일 165줄). 사이트 파일을 읽는 TypeScript 코드는 위젯 빌드가 쓰는 `tools/site-file.ts` 하나다(`next.config.ts`가 부른다). 위젯은 `tokenProvider`가 던지거나 거부하면 "로그인 정보를 받지 못했습니다." 알림을 보인다(`EMBED.md` 48줄). 첫 화면은 `hook_choice_facts`가 한 번 막았고, 그때 "위젯 e2e의 사이트 파일 읽기"를 "위젯 빌드의"로, "403"을 "404"로 고쳐 다시 올렸다.

> 사용자: (포털이 아는 사이트 목록의 원천을 어디에 둘까요?) "serve의 사이트 파일을 함께 읽고 시작 때 대 본다 (Recommended)" — 설명: 포털은 시작 인자로 설정 파일과 serve의 사이트 파일 둘을 받습니다. 사이트 파일에서 발급자·열 에이전트 목록·허용 출처·공개 키를 읽고, 포털 설정 파일은 사이트마다 발급자를 열쇠로 고를 이름(slug)·에이전트 하나·모양 값·모드·고지 글을 더합니다. 시작 때 네 가지를 대 보고 하나라도 어긋나면 뜨지 않습니다. 발급자가 사이트 파일에 있다, 고른 에이전트가 그 사이트의 열 에이전트에 든다, 포털의 공개 출처가 그 사이트의 허용 출처에 든다, 포털의 kid로 든 공개 키가 포털 개인 키에서 난 공개 키와 같다. 사이트 파일을 읽는 TypeScript 코드는 지금 위젯 앱의 빌드가 쓰는 tools/site-file.ts 하나라, e2e 준비처럼 워크스페이스 패키지로 옮겨 위젯 빌드와 포털이 함께 씁니다. 대가: 포털이 사이트 파일 형식(schema_version 1)에 묶이고, 위젯 빌드의 사이트 파일 읽기를 함께 옮기는 티켓이 듭니다.

> 사용자: (모드가 '로그인'이나 '둘 다'인 사이트를 이번 판에서는 어떻게 다룰까요?) "시작은 받고 페이지가 '아직 없음'을 보인다 (Recommended)" — 설명: 설정의 모드 값 셋(익명, 로그인, 둘 다)을 모두 받고 포털이 뜹니다. 로그인 사이트의 페이지는 위젯 없이 '이 사이트는 로그인이 필요하고 로그인은 아직 제공하지 않는다'는 알림을 그리고, '둘 다' 사이트의 페이지는 익명 흐름 옆에 같은 알림이 붙은 비활성 로그인 단추를 둡니다. 로그인 사이트의 토큰 끝점은 늘 거절합니다. 그래서 미리보기에서 사이트의 모드가 보이고, portal-login은 로그인 갈래만 채웁니다. 대가: '아직 없음' 화면 둘을 이번에 그리고 e2e로 고정합니다.

> 사용자: (사이트를 고르는 셀렉트 박스와 위젯 페이지를 어떤 모양으로 둘까요?) "페이지 하나에서 클라이언트가 위젯을 바꿔 끼운다" — 설명: /portal/ 페이지 하나에 셀렉트 박스가 있고, 고르면 페이지의 스크립트가 <agent-os-widget>의 속성과 tokenProvider가 부를 토큰 끝점을 바꿔 끼웁니다. 이동 없이 바뀝니다. 대신 고지 덮개와 확인 여부를 서버가 아니라 클라이언트 스크립트가 사이트마다 물어 그려야 하고, 위젯이 속성 변경을 다시 그리는지는 확인하지 않았습니다(어림).

추천(사이트마다 제 페이지, 셀렉트는 이동)과 다른 답이다. 라운드 1의 "서버가 쿠키 유무로 페이지를 두 모양으로 그린다"는 이것으로 바뀐다. 서버는 페이지 하나를 그리고, 사이트마다의 확인 여부와 덮개는 페이지의 스크립트가 그 사이트의 끝점에 물어 그린다.

> 사용자: (식별자 쿠키와 고지 확인을 포털 전체에 하나로 둘까요, 사이트마다 따로 둘까요?) "사이트마다 따로 (Recommended)" — 설명: 쿠키 경로를 /portal/sites/<이름> 으로 두어 사이트마다 식별자와 확인이 따로입니다. 같은 브라우저도 사이트에 따라 다른 익명 주체가 되고, 고지 글이 사이트마다 다를 때 그 글을 확인한 뒤에만 그 사이트의 쿠키를 받습니다. 라운드 1의 쿠키 경로 /portal을 이것으로 고칩니다. 대가: 사이트를 옮길 때마다 확인을 한 번씩 더 합니다.

라운드 3 뒤에 대 본 사실: 위젯 요소는 `observedAttributes`가 속성 다섯이고 `attributeChangedCallback`이 다시 그리며, 머리 주석이 "`agent`가 바뀌면 위젯 한 벌을 새로 띄운다"고 적는다(`web/apps/widget/element/WidgetElement.tsx` 5~9줄, 48줄, 90줄). 그래서 "클라이언트가 바꿔 끼운다"의 어림은 풀렸다. 디자인 시스템 패키지는 `THEMES`·`MODES`·`DEFAULT_THEME`을 내보낸다(`web/packages/ui/src/index.ts` 27줄). 위젯 e2e는 `default-src 'none'`에 `script-src`·`connect-src`·`font-src`와 `style-src 'self'`만 연 페이지에서 CSP 위반 없이 위젯이 칠해지는 것을 본다(`EMBED.md` CSP 절). `pnpm -C web verify`의 `typecheck`는 `tsc --noEmit`을 워크스페이스 전체에 돌린다(`web/package.json` 10·13줄).

## 설계 인터뷰 라운드 4

남은 가지 둘과 합의 요약. 올리기 전에 대 본 사실: 두 Next 앱의 `dev`·`start`가 `node tools/start.ts`로 `.ts`를 빌드 없이 돌리고(두 앱의 `package.json` 6~8줄), 그 파일은 확장자를 붙여 import하며(`start.ts` 33~35줄), 기준 tsconfig가 `erasableSyntaxOnly`를 켠다(`web/tsconfig.base.json` 9줄). 이 PC의 Node는 v24.19.0, `engines`는 `>=24 <25`. 반대 선례는 디자인 시스템 패키지의 내보내는 빌드(`tsconfig.build.json`, `themes.ts` 30줄 주석)다. 위젯 e2e의 출처는 `http://*.localhost`이고 브라우저가 보안 맥락으로 본다(`e2e/stack.ts` 13~14줄). 평문 출처에서 `Secure` 쿠키를 받는지는 재지 않았다(어림으로 적었다). 첫 화면은 `hook_choice_facts`가 한 번 막았고 사실을 대 본 뒤 같은 문장으로 다시 올렸다.

> 사용자: (포털 서버를 어떻게 띄울까요?) "빌드 없이 node가 .ts를 바로 돈다 (Recommended)" — 설명: 두 Next 앱의 시작 래퍼(node tools/start.ts)처럼 포털도 node가 타입만 벗겨 .ts 파일을 바로 돌립니다. 앱의 start 스크립트가 node <입구>.ts --config … --site-file … 꼴이고 빌드 단계와 dist 폴더가 없습니다. import는 확장자를 붙이고 문법은 erasableSyntaxOnly가 이미 묶어 둡니다. 타입 검사는 pnpm verify의 tsc가 따로 돕니다. 컨테이너 이미지는 소스와 node_modules를 그대로 담습니다(release-image 몫). 대가: 워크스페이스 패키지(사이트 파일 읽기, @agent-os/ui의 THEMES)도 node가 바로 읽을 수 있는 꼴(빌드된 .js나 .ts 진입점)이어야 하고, 이 조합이 서는지는 명세 전에 프로브로 재서 ADR에 적습니다.

> 사용자: (식별자 쿠키의 Secure 표시를 어떻게 둘까요?) "포털의 공개 출처가 https일 때만 Secure (Recommended)" — 설명: 설정의 공개 출처가 https면 쿠키에 Secure를 붙이고 http면 붙이지 않습니다. 운영(TLS를 끝내는 프록시 뒤, https 출처)에서는 늘 Secure이고, e2e의 http://*.localhost에서는 붙지 않아 브라우저가 평문 출처의 Secure 쿠키를 받는지에 기대지 않습니다. 대가: 공개 출처를 http로 적은 배치는 Secure 없는 쿠키를 냅니다(그 배치는 어차피 평문이라 새로 잃는 것이 없습니다).

> 사용자: (본문의 합의 요약 ①~⑪대로 가도 될까요?) "그대로 간다 (Recommended)" — 설명: 라운드 1~3의 답과 본문 ①~⑪의 가정이 모두 결정으로 굳고, 이어서 domain-modeling으로 용어와 ADR 0050 초안을 씁니다. 끝점 이름, 패키지 이름과 수, 설정 칸 이름, 마커 이름은 명세가 짓습니다.

확인받은 요약(호출 곁 본문에 올린 글 그대로):

① 앱은 `web/apps/` 아래의 포털 앱(폴더 이름은 명세) 하나이고 `node:http` 서버 하나, 무상태, 루프백만 듣습니다. 시작 인자는 포털 설정 TOML과 serve의 사이트 파일 둘입니다. 시작 검사는 라운드 3의 넷에 더해 설정의 모양(모르는 키, 빠진 필수 키, 테마 키는 `THEMES`, 밝음은 `MODES`, 모드는 익명·로그인·둘 다, 사이트 이름은 경로에 쓸 수 있는 글자)을 봅니다.
② 경로는 `/`가 `/portal/`로 302, `/portal/`이 페이지 하나, 사이트마다 `/portal/sites/<이름>/` 아래에 확인 여부(상태), 확인(POST, 쿠키 발급), 토큰(쿠키가 없거나 꼴이 아니면 401, 로그인 모드면 늘 거절) 끝점, `/portal/health`, 페이지 스크립트와 디자인 토큰 CSS·글꼴 CSS 같은 정적 파일, 그 밖은 404입니다. 끝점 이름은 명세가 짓습니다. 페이지는 고른 사이트를 질의 `?site=<이름>`에 남겨 새로 고침과 링크가 같은 사이트를 열고, 사이트가 하나면 셀렉트 박스를 숨깁니다.
③ 쿠키는 HttpOnly, SameSite=Strict, Path=`/portal/sites/<이름>`, 30일, 토큰을 낼 때마다 다시 적고, 값은 UUID v4, 꼴이 아니면 없는 것으로 봅니다. `Secure`는 둘째 질문입니다.
④ 토큰은 RS256에 `kid`, `iss`는 그 사이트의 발급자, `sub`는 `anon-<UUID>`, `aud`는 사이트 파일의 그 사이트 `audience`, `exp`는 `iat`+120초입니다. 포털 키 하나로 모든 사이트에 서명하고, 운영자는 그 공개 키와 `kid`를 사이트마다 `[[sites.public_keys]]`에 붙입니다(키 만들기 명령이 그 조각을 출력).
⑤ 서버는 HTML 하나를 그리며 사이트 목록과 사이트마다의 공개 설정(이름, 제목, 소개, 테마, 밝음, 모드, 고지 글, 보고서 링크)을 JSON 데이터 블록으로 싣습니다. 페이지 스크립트는 인라인이 아니라 같은 출처의 파일이고, 고른 사이트의 상태 끝점에 물어 확인 전이면 고지 전문과 "확인하고 질문하기" 단추가 위젯을 덮은 모양을, 확인하면 확인 끝점을 불러 쿠키를 받고 덮개를 걷습니다. 위젯 요소의 속성 다섯을 사이트 설정으로 두고 `tokenProvider`는 그 사이트의 토큰 끝점을 부릅니다. 짧은 고지는 늘 보입니다. 로그인 모드는 위젯 없이 알림, 둘 다는 익명 흐름에 비활성 로그인 단추입니다. 페이지의 CSP는 `default-src 'none'`에 `script-src`·`connect-src`·`style-src`·`font-src`·`img-src`를 `'self'`로 엽니다.
⑥ 포털 페이지의 모양은 디자인 시스템 CSS를 포털이 같은 출처에서 내어 씁니다. 화면(셀렉트 박스, 짧은 고지, 덮개, 아직 없음 둘)은 명세 전에 `/ui-design pilot-portal`로 그립니다(web-widget 선례).
⑦ 포털의 기록(로그)에 쿠키 값과 토큰을 싣지 않습니다.
⑧ 사이트 파일 읽기(위젯 빌드의 `tools/site-file.ts`)와 e2e 준비(위젯 e2e의 중계·픽스처 플러그인·serve 띄우기)를 워크스페이스 패키지로 옮기고 위젯이 그것을 쓰게 고칩니다. 패키지의 이름과 수는 명세가 짓습니다.
⑨ 테스트는 Vitest(설정 읽기와 사이트 파일 대조, 토큰 서명과 클레임, 쿠키 판정, 페이지 데이터), Playwright e2e(serve, 위젯 Next, 포털, 중계. 익명·로그인·둘 다 사이트를 두고 확인→질문→답, 확인 전 401과 위젯의 알림, 사이트 바꾸기, 로그인 모드의 알림, 사이트별 시간당 상한을 1로 둔 둘째 질문의 거부), 실제 모델 e2e 하나(calc에 질문. 마커는 명세가 정하고 새 마커면 `pyproject.toml`과 `tests.md`를 고칩니다)입니다. 기능 계획의 수락 셋을 덮습니다.
⑩ 다른 행: portal-login 계획의 "한 배포에서는 하나만 쓴다"를 "사이트마다 고르고 둘 다도 된다"로 고칩니다. 설정을 화면에서 고치는 위젯 관리 화면과 레이아웃·아이콘 같은 새 모양 칸은 새 기능 행으로 세우고, 그 행의 이름과 자리는 승인 화면에서 함께 보입니다. public-demo는 사이트 하나라 셀렉트 박스가 숨습니다.
⑪ 문서: ADR 0050 하나에 결정 전부, `CONTEXT.md`에 질문 페이지(포털)·익명 주체 용어, `tech.md` 웹 줄에 포털 앱, ADR 0024·0047에 포인터를 둡니다.

이것으로 frontier가 비었다. 절차(스킬, 훅, 브랜치와 병합 규약)를 바꾸는 결정이 없어 grilling의 갈래 밟기는 해당하지 않는다.

## 용어와 ADR 초안

domain-modeling으로 쓴 것. 컨텍스트 압축 뒤라 일지를 다시 읽어 라운드의 답과 요약 ①~⑪을 옮겼다.

- `CONTEXT.md`: 질문 페이지(Portal), 질문 페이지 설정, 보증 모드, 로그인 모드, 익명 식별자, 익명 주체, 고지, 고지 확인을 더했다. 사이트 항목에 "질문 페이지가 담는 항목 하나하나도 사이트다"를, 모드 항목에 "익명인지 로그인인지는 보증 모드다"를 더했고, 사이트 파일의 _Avoid_ "위젯 설정"의 괄호를 질문 페이지도 읽는 것으로 고쳤다. "보증 모드"를 새로 세운 까닭: 용어집의 모드는 라이트·다크(디자인 시스템)라서, 인터뷰에서 "모드(익명/로그인/둘 다)"라고 부른 것과 글자가 겹쳤다(인터뷰 화면에서는 라이트·다크를 "밝음"으로 불러 피했다). 나란히 도는 mcp-http 워크트리의 `CONTEXT.md` 변경은 MCP 서버와 전송 항목(176~181줄)이라 자리가 겹치지 않는다(두 워크트리의 파일을 `diff`로 손으로 봤다).
- `docs/adr/0050-portal-is-one-node-server-hosting-many-sites-and-signing-anonymous-site-tokens.md`: 결정 열셋, Considered Options 열셋, Consequences 열(셀프 리뷰가 `- **` 항목을 센 수로 고쳤다. 리뷰 반영으로 Considered Options가 열넷이 됐다). 라운드 3에서 추천과 다른 답(페이지 하나에서 클라이언트가 바꿔 끼운다)은 Considered Options에 추천이었던 안과 함께 적었다. node가 워크스페이스 패키지를 바로 읽는 조합은 요약 ①대로 명세 전 프로브로 재서 이력에 적기로 하고, 지금 코드를 읽어 아는 걸림돌 셋(`@agent-os/ui` 진입점이 `.tsx`를 다시 내보냄, `theme.css`가 Tailwind 지시문을 품은 원본, node가 `node_modules` 아래의 타입을 벗기지 않음)을 어림으로 적었다. 전역 `fetch` 금지(`web/eslint.config.mjs`의 `no-restricted-globals`, `files` 없는 블록)가 질문 페이지의 스크립트에도 걸리는 것을 Consequences에 적고 푸는 길은 명세에 넘겼다.
- `docs/adr/README.md` 0050 행. mcp-http 워크트리가 같은 자리에 0049 행을 더했으므로 병합 때 두 행이 이웃으로 선다.
- 포인터: ADR 0047 "떼어 낼 때 끊을 연결"의 두 문장(사이트 파일 읽기의 자리, 루프백 목록 셋)과 ADR 0024의 nginx가 넘기는 경로 문장 둘에 `(바뀜: ADR 0050)`.
- `docs/constitution/tech.md`: 웹 행에 질문 페이지의 스택, 원격·CI 행의 프록시가 넘기는 것에 질문 페이지의 경로.
- 기능 계획: portal-login의 "한 배포에서는 하나만 쓴다"를 보증 모드 문장으로, pilot-portal의 "이 페이지를 사이트 하나로 등록한다"를 "담는 사이트마다"로 고쳤다. 새 행 둘(portal-admin, widget-appearance)은 승인 화면에서 슬라이스를 고른 뒤 만든다.
- 쓴 뒤 돌린 검사: `uv run python tools/check_adr_pointers.py`, `tools/check_md_tables.py`, `tools/check_line_separators.py`, `tools/plan_table.py --check` 모두 종료 0.

## 인계

셀프 리뷰 직전 경계에서 `hook_handoff`의 계기를 받았다(세션 컨텍스트 295,098 토큰, 문턱 200,000). `handoff.md`의 인계하지 않는 다섯 경우에 들지 않는다. 계기를 낸 명령이 실패한 것이 아니고, 이번 요청 범위는 PR과 병합까지이며, 이 세션의 지시문 "이어받을 상태"는 없음이고, 이 일지에 `인계 못함` 줄이 없고, `get_session self`에 `parentSessionId`가 없다. 그래서 넘긴다. 이 세션의 지금 제목은 `docs/pilot-portal-design`이고, 넘기며 `docs/pilot-portal-design (인계함)`으로 바꾼다. 이 세션이 번복하거나 고친 것은 위 절들에 있다(라운드 3의 추천과 다른 답으로 라운드 1의 "서버가 쿠키 유무로 두 모양" 결정이 바뀜, 사용자가 다시 꺼낸 요구의 반영, ADR 번호 0049 선점으로 0050).

### 새 세션이 할 일

1. 워크트리 변형의 `/code-review`로 셀프 리뷰. 기준은 `origin/main`과의 merge-base이고, 범위는 미커밋 변경 일곱 파일과 미추적 둘(ADR 0050, 이 일지)이다. Critical·Major를 반영하고 보고를 이 일지에 옮긴다.
2. 승인 화면 하나(AskUserQuestion). 질문 ① ADR 0050 초안 승인(ADR 승인만 사용자 판정이다). 질문 ② 새 행 둘의 슬라이스. 행 이름과 한 줄은 다음을 제안한다. `portal-admin`: 질문 페이지 설정을 화면에서 고치는 관리 화면. ADR 0047대로 사이트 쪽(질문 페이지)의 것이고 Agent OS 관리 화면이 아니다. Blocked by pilot-portal. `widget-appearance`: 레이아웃·아이콘 같은 새 모양 칸을 위젯의 임베드 속성과 질문 페이지 설정에 더한다. Blocked by pilot-portal(위젯과 질문 페이지 둘 다 고친다). 자리의 추천은 슬라이스 10(제품 1.0 열의 편의 행)이고 선택지는 10 / 9(기준선 끝) / 12(1.0 뒤)다. `hook_choice_facts`가 처음 보는 화면을 한 번 막으므로 설명의 사실을 대 본 뒤 같은 질문·라벨로 다시 올린다. 답은 라벨과 설명을 글자 그대로 이 일지에 `> 사용자:` 인용으로 옮긴다.
3. 승인 뒤. `.scratch/pilot-portal/plan.md`의 `**Blocked by:**` 줄 뒤에 `**설계:** ADR 0050` 줄. 새 행 둘의 `.scratch/<slug>/plan.md`(첫 줄 `# <slug>: <한 줄>`, `**슬라이스:** N`, `**Blocked by:** pilot-portal`, 본문에 근거(ADR 0047·0050, 이 일지의 "사용자가 앞서 말한 요구를 다시 꺼냄")와 수락). ADR 0050 Consequences "다른 행"의 "둘의 슬라이스는 승인 화면에서 사용자가 골랐다"를 고른 값으로 고친다. `uv run python tools/plan_table.py`를 같은 커밋에 싣는다. 승인이 거부되면 ADR을 고쳐 다시 올린다(status는 승인 전제로 accepted로 적어 두었다).
4. 검증(린트 둘, `uv run pyright`, `uv run lint-imports`, `uv run python tools/run_checks.py`는 timeout 600000이나 백그라운드), `git branch --show-current`, `uv run python tools/sibling_overlap.py`(나란히 도는 mcp-http가 ADR 0049와 README 행을 더했고 README에서 이 브랜치의 0050 행과 이웃이라 병합 때 충돌할 수 있다), 커밋(heredoc이나 `-F`, 끝에 `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`), PR(끝에 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`), 병합(묻지 않는다), next-session.
5. 이 일지에 셀프 리뷰 보고, 승인 답, `## 다음` 절.

### 지시문

```
다음 작업: 기능 pilot-portal. 위젯을 담는 질문 페이지가 로그인 없이 온 사람에게 사이트 토큰을 내, 포털이 없는 공개 데모와 배포 환경을 돕는다
다음 단계: 설계 인터뷰
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /grill-with-docs pilot-portal
브랜치: docs/pilot-portal-design
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-09-1410-pilot-portal-design.md의 "인계" 절(남은 단계와 승인 화면의 내용). 나란히 도는 mcp-http 설계 인터뷰(브랜치 docs/mcp-http-design)가 ADR 0049와 docs/adr/README.md 행을 더했다
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. docs/journal/2026-11-09-1410-pilot-portal-design.md. 설계 인터뷰는 끝났고(frontier가 비었고 요약 ①~⑪을 확인받았다) domain-modeling으로 CONTEXT.md 용어, ADR 0050 초안, ADR 0024·0047 포인터, tech.md, 기능 계획 두 문장까지 썼다. 셀프 리뷰 뒤 승인 화면(ADR 0050과 새 행 둘의 슬라이스), 승인 뒤 설계 줄과 새 행의 기능 계획과 plan_table.py, 검증, 커밋, PR, 병합, next-session이 남았다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `docs/pilot-portal-design (인계함)`으로 바꿨고, `git worktree unlock C:/project/agent/.claude/worktrees/pilot-portal-design`이 오류 없이 끝났다. 멈출 백그라운드 작업은 없었다.

open-session을 부른다 2026-11-09T06:49:04Z

## 셀프 리뷰(인계받은 세션)

인계받은 세션이 `code-review`를 base `24fdbe9a`(origin/main과의 merge-base, HEAD와 같다)로 돌렸다. 범위는 바뀐 추적 파일 일곱, 커밋 0, 미추적 둘(ADR 0050, 이 일지)이다. 표준 축은 sonnet·high, 명세 축은 본 세션의 모델이다. 명세는 이 일지의 라운드 1~4의 `> 사용자:` 답과 확인받은 요약 ①~⑪, 기능 계획의 "설계 인터뷰가 먼저 볼 것"과 "수락"으로 주고, "용어와 ADR 초안"·"인계" 절은 리뷰어 참고(요구가 아니다)로 갈랐다. 외부 근거(Node 문서의 `node_modules` 타입 벗기기 거부, RFC 6265 5.1.4 경로 일치)는 WebFetch 웹 요약으로 발췌해 두 브리프에 실었다.

### Spec

(a) 누락·부분

1. **Major** — 고지의 기본 글과 식별자 고지가 ADR에 없다. 라운드 1 답 "고지의 글은 배포 설정이 주고 포털은 기본 글을 듭니다(ADR 0047: 문구는 사이트가 가진다)"와 "고지에 '식별자 쿠키를 둔다'를 적습니다". ADR 0050 "시작 인자와 시작 검사"·"페이지" 항목에 "기본 글"이 0건이고, 고지 글이 필수 칸인지 빠졌을 때 기본 글을 드는지가 비어 "빠진 필수 키는 구성 오류"와 어느 쪽인지 알 수 없다. 식별자 고지는 CONTEXT.md 고지 항목에만 있고 용어집은 결정이 아니다.
2. **Minor** — 라운드 2 답 "compose에서 프록시가 다른 컨테이너에 있을 때의 이음은 release-image 설계 인터뷰가 네 프로세스에 한꺼번에 정합니다"가 어디에도 적히지 않았다. ADR 0050은 "프록시 뒤에만 선다"와 "컨테이너 이미지도 하나다(release-image 몫)"뿐이고, `.scratch/release-image/plan.md`는 아직 루프백 목록이 세 곳이라던 문장 그대로다(잔존. 반영 전의 글). 그 계획의 "포털"도 CONTEXT.md가 이번에 _Avoid_로 둔 말이다.
3. **Minor** — 라운드 3 답 "'아직 없음' 화면 둘을 이번에 그리고 e2e로 고정합니다". ADR 테스트 결정은 "로그인 사이트의 알림"만 들고 '둘 다' 사이트의 비활성 로그인 단추는 없다.
4. **Minor** — 라운드 1 "발급자는 페이지의 공개 출처 하나"와 "사이트 파일의 허용 출처는 공개 출처 하나"가 라운드 3에서 사이트별 발급자·"허용 출처에 든다"로 바뀌었는데, 일지의 "다시 꺼냄" 절 끝은 바뀐 라운드 1 답을 둘(TOML 하나, 에이전트 하나)만 들고 ADR Considered Options도 쿠키 경로·두 모양만 적는다. 교체 기록이 없다.

(b) 요구 밖

5. **Minor** — ADR Consequences "다른 행": "둘의 슬라이스는 승인 화면에서 사용자가 골랐다". 요약 ⑩은 "승인 화면에서 함께 보입니다"(미래)이고 화면은 아직 열리지 않았다. 초안 글자로는 거짓인 과거형이다.
6. **Nit** — Consequences "사이트를 바꾸면 새 대화다 … 받아들인다". 라운드 3 답 설명에 없는 대가를 에이전트가 받아들인 것으로 적었다. 승인 화면에 한 줄로 보인다.
- 요구 안으로 판정: tech.md 원격·CI 행(라운드 2 "프록시 규칙은 = /와 /portal/ 둘"이 "최종 사용자 접두사와 위젯만"을 거짓으로 만듦), pilot-portal 계획 문장, CONTEXT.md 네 용어(domain-modeling "Update CONTEXT.md inline", 보증 모드는 모드와의 글자 겹침 해소).

(c) 잘못 구현

7. **Minor** — CONTEXT.md _Avoid_ "포털(앱 폴더와 경로 이름에서만)"이 ADR 결정 "폴더 이름은 명세가 짓는다"와 어긋난다. 결정된 것은 경로 `/portal/`뿐이다.
8. **Nit** — `.scratch/portal-login/plan.md` "(수명은 600초까지, `http/sites.py`)": ADR 0050이 질문 페이지 토큰을 120초로 정해 이 행의 전제 수치가 바뀌었다.

(d) 주장 검증

대 본 주장 35개(인용 9, 닫힌 주장 7, 코드 동작·선례 12, 다른 ADR 참조 7), 어긋남 0. 루프백 목록은 비테스트 코드에서 정확히 셋, smol-toml import는 `tools/site-file.ts` 하나(`testing/site-file.ts`는 JSON 픽스처만 읽음), 패키지 둘, 걸림돌 셋(`index.ts`의 `.tsx` 재내보내기, `theme.css`의 `@theme`, `build`→`dist/theme.css`), `wc -l` 354/329/85/138/45, eslint `no-restricted-globals` 블록에 `files` 없음 확인. relay `upstreamOf`를 node로 불러 `/portal/`·`/portal/sites/a/token`·`/`·`/widgetx`·`/health`→null(404), `/widget?x=1`·`/widget/element.js`→Next, `/end-user/x`→serve 확인(스크래치패드 스크립트, 측정 아님). 쿠키 `Path=/portal/sites/<이름>`은 RFC 6265 5.1.4 셋째 조건으로 `/portal/sites/<이름>/…`에 맞고 `<이름>x`에는 새지 않는다. ADR status `accepted`는 0047 첫 커밋과 같은 관행. `check_adr_pointers`·`plan_table --check`·`check_md_tables` 모두 0.
- **Nit** — "토큰은 서명 한 번이고 그 자체로는 비용이 들지 않으며"와 "120초면 느린 망에서도 넉넉하며"는 어림 표시 없는 보편 주장이다(RSA-2048 서명은 CPU 비용이 있다. 재지 않았다).

지적 9개. 가장 심각한 것은 1(Major): 고지의 기본 글과 식별자 고지 조건이 ADR 0050에 없다.

### Standards

Critical와 Major는 없다. 지적은 Minor 5개와 Nit 6개이고, 가장 센 것은 아래 (a)의 3번과 5번이다.

(a) 표준 위반

1. **Minor** — "사이트 토큰"은 용어집에 없는 말이다(`docs/agents/domain.md`, `CODING_STANDARDS.md` 관점 2). 새 `CONTEXT.md` 항목(질문 페이지, 고지 확인)과 ADR 0050 제목이 이 말을 쓴다. 용어집에는 "서명 토큰"만 있고, origin/main에서 "사이트 토큰"은 ADR 0046에만 두 번 나온다. 정의를 달거나 "서명 토큰"으로 맞춘다.
2. **Minor** — `CONTEXT.md`에서 사이트와 질문 페이지의 정의가 서로를 가리킨다. 질문 페이지 항목은 이 저장소가 함께 내는 사이트라 하고, 사이트 항목은 질문 페이지가 담는 항목 하나하나도 사이트라 한다(반영 전의 글). 질문 페이지는 사이트이면서 사이트를 담는 그릇이다. 발급자를 가진 단위가 사이트라는 말을 한 곳에 박는다.
3. **Minor** — pilot-portal 계획의 옛 문장이 남았다. `.scratch/pilot-portal/plan.md`에 상한이 배포 전체를 묶는 것은 사이트가 이 페이지 하나인 배치에서뿐이라는 문장이 그대로 있다(반영 전의 글). 페이지 하나가 사이트 여럿을 담게 됐으므로 뜻이 어긋난다. ADR 0050 Consequences "상한"은 "기능 계획이 이미 적었다"고 하고, "다른 행" 절의 고친 문장 목록에도 이 문장이 없다. "사이트가 하나인 배치"로 고친다.
4. **Minor** — ADR 0050이 길고 명세 수준의 세부를 못 박는다(Speculative Generality 가능성). 23.7KB로 ADR 0047(7.9KB)의 세 배다. 쿠키 플래그, CSP 목록, 테스트 시나리오, 키 만들기 명령까지 정한다. "끝점 이름은 명세가 짓는다"고 하면서 `/portal/sites/<이름>/`과 `/portal/health`는 확정한다. 서두의 굵은 문단 하나가 3천 자 가까워 처음 보는 사람이 판단하기 어렵다.
5. **Minor** — ADR 0023 이력 2026-11-04와 어긋나는데 말이 없다. 그 이력(ADR 0042 묶음 ⑤ 21)은 `serve`가 사이트 파일을 바뀌었을 때 다시 읽는다고 정했다. ADR 0050은 두 파일을 시작 때 한 번만 대 보므로, 운영 중 키를 바꾸거나 열 에이전트를 고치면 질문 페이지의 검사가 낡는다. 다시 시작해야 한다는 한 줄이 필요하다.

(b) 스멜(모두 판단 항목)

- **Nit, Shotgun Surgery 가능성.** `web/eslint.config.mjs`의 `files` 글롭 `**/{route,middleware,proxy,instrumentation}.*`는 질문 페이지 앱의 `route.ts`나 `proxy.ts`도 Next 서버 파일로 보고 막는다. `node:http` 서버의 라우터에 붙이기 쉬운 이름이라, 명세가 이 이름을 피하라고 적어야 한다.
- **Nit.** 계획 문장은 "멀티테넌시는 PRD의 미룬 것"이라 하는데, 발급자별 설정을 가진 사이트 여럿을 담는 이 설계가 왜 그게 아닌지는 어디에도 없다.
- **Nit.** `.scratch/portal-login/plan.md`에 단독 "모드"가 남았다("모드를 바꿀 때 서명 키를…"). 보증 모드로 쓰는 편이 낫다.

(c) 주장 검증

대 본 주장은 약 30개이고, 틀린 것은 둘이다. 하나는 일지의 세는 말과 줄 번호 인용(아래 첫째와 둘째 Nit)이고, 다른 하나는 위 (a)의 3번이다.

- **Nit.** 일지는 결정 열넷, Consequences 아홉이라 했지만(반영 전의 글) 실제 `- **` 항목은 결정 13개, Consequences 10개다(Considered Options 13은 맞다).
- **Nit.** 일지의 eslint 92~95줄, 314~316줄이라는 인용은(반영 전의 글) `SERVER_FILE`과 파일 글롭만 가리킨다. Server Actions 규칙은 `RESTRICTED_SYNTAX`(74~90줄)에 있다. 인용은 맞지만 "Server Actions"는 그 줄에 없다.
- **웹 요약.** ADR의 "Node 문서로 아는 것"은 이 세션의 WebFetch 웹 요약에 기댄 말이고, 원문을 내려받아 대 보지 않았다. ADR이 "이 워크스페이스에서 대 보지 않았다"고 밝혀 두었으므로 문구는 허용 범위다.
- 맞은 것(대표): `http/sites.py`의 RS256·클레임 다섯·600초·30초·CORS 합집합, `RunDecision.tsx` 58줄의 `|`, `EMBED.md`의 `tokenProvider`·10초·"로그인 정보를 받지 못했습니다."·속성 다섯·CSP 절, `lib/storage.ts`의 발급자와 `sub`, 루프백 목록이 정확히 세 파일이라 "넷" 셈이 맞음, `tools/start.ts`를 쓰는 두 Next 앱·`erasableSyntaxOnly`·`typecheck`, 위젯 e2e `relay.ts`의 라우팅·`token.ts`의 RSA 2048과 spki pem·`wc -l`의 354/329/85/138/45, `limits.py`의 시간당 상한 칸은 주체별과 사이트별 둘, `end_user.py` 165줄, `ui` 패키지의 export와 `build`의 `dist/theme.css`, `WidgetElement`의 `observedAttributes`, `tests/fixtures/site_file`의 칸 이름, ADR 0019·0023·0024·0046 이력·0047의 인용. `plan_table.py --check`, `check_adr_pointers.py`, `check_md_tables.py`, `check_instructions.py` 모두 종료 0.
- 포인터 `(바뀜: ADR 0050)` 넷(ADR 0024 둘, ADR 0047 둘)은 `.claude/rules/adr.md` 규칙에 맞는다. 포인터가 빠진 본문 문장은 찾지 못했다. ADR 0011 87줄과 ADR 0024 123·131줄은 이력이라 기록이다.
- 금지어 "동의", "모드"(단독), "포털"(질문 페이지 뜻)은 ADR 0050에서 쓰지 않았다. "포털"이 한 번 나오지만 사이트 쪽 포털이라는 다른 뜻이다.
- `**설계:**` 줄과 새 행 둘이 없는 것은 일지가 승인 뒤로 미룬 절차라 위반이 아니다.

지적은 11개(Minor 5, Nit 6)이고, 병합 전에 고칠 것은 (a)의 3번과 5번이다.

### 요약

범위: base `24fdbe9a`, 추적 파일 일곱, 커밋 0, 미추적 둘. 표준 축 11개(Minor 5, Nit 6. 가장 센 것은 pilot-portal 계획의 옛 문장과 ADR 0023 이력과의 어긋남), 명세 축 9개(Major 1, Minor 5, Nit 3. 가장 센 것은 고지의 기본 글과 식별자 고지가 ADR에 없음).

### 반영

고친 것(근거를 끝까지 열고 쓴 새 문장은 PR 직전 리뷰의 밀 주장으로 아래에 원문으로 둔다).

- 명세 1(Major): ADR 0050 "시작 인자와 시작 검사"에 더했다. "고지 글은 비울 수 있는 칸이다. 비우면 질문 페이지의 기본 글을 쓰고, 사이트가 적은 글이 있으면 그 글이 이긴다(ADR 0047대로 문구는 사이트가 가진다). 기본 글은 질문이 기록되고 모델 API에 보내진다는 것, 익명 식별자 쿠키를 둔다는 것, 개인정보를 넣지 말라는 것을 적는다. 익명 식별자 쿠키를 둔다는 문장은 사이트가 글을 적어도 질문 페이지가 고지 전문에 늘 넣는다. 그 쿠키는 사이트의 글이 아니라 질문 페이지의 동작이기 때문이다." 근거는 라운드 1의 답 둘("고지의 글은 배포 설정이 주고 포털은 기본 글을 듭니다", "고지에 '식별자 쿠키를 둔다'를 적습니다")이다.
- 표준 a5(Minor): 같은 항목에 더했다. "두 파일은 시작 때 한 번 읽는다. `serve`는 바뀐 사이트 파일을 요청마다 변경 시각으로 보고 다시 읽지만(ADR 0023 이력 2026-11-04), 질문 페이지는 그러지 않아 운영 중에 사이트 파일이나 질문 페이지 설정이나 키를 바꾸면 다시 띄워야 하고, 그 전까지는 옛 판으로 검사하고 서명한다." ADR 0023의 이력 제목 "2026-11-04 사이트 파일은 바뀌었을 때 다시 읽고, …"를 grep으로 열어 봤다.
- 명세 3(Minor): "테스트" 결정에 "로그인 사이트의 알림과 둘 다 사이트의 비활성 로그인 단추(아직 없음 화면 둘)"를 더했다.
- 명세 4(Minor): Considered Options에 "**발급자는 질문 페이지의 공개 출처 하나이고 사이트 파일의 허용 출처도 그 하나다.**" 항목을 더해 라운드 1의 답이 라운드 3에서 어떻게 바뀌었는지 적었고(Considered Options가 열넷이 됐다), 이 일지의 "다시 꺼냄" 절 끝에도 그 두 교체를 더했다.
- 명세 5(Minor): "다른 행"의 과거형(사용자가 골랐다)을 승인 화면에서 고른다는 현재형으로 고쳤고, 승인 뒤 고른 값으로 다시 고친다("승인 뒤" 절).
- 명세 2(Minor): "다른 행"에 "compose에서 TLS를 끝내는 프록시가 다른 컨테이너에 있을 때 루프백만 듣는 네 프로세스(`serve`, 관리 화면, 위젯, 질문 페이지)와 프록시를 잇는 방법은 그 행의 설계 인터뷰가 한꺼번에 정한다"를 더하고, 받는 쪽인 `.scratch/release-image/plan.md`(Blocked by pilot-portal이라 받는 쪽이 먼저 돌지 않는다)에 세 가지를 적었다. 첫 줄의 "포털"을 "질문 페이지"로, 루프백 목록이 세 곳이라던 문장을 "`serve`와 두 Next 앱과 질문 페이지는 루프백에만 서는데(ADR 0011, ADR 0019, ADR 0050. 루프백 목록은 네 곳이 따로 든다, ADR 0047과 그 포인터)"로, 그리고 "질문 페이지 이미지는 빌드 산출이 아니라 소스와 `node_modules`를 그대로 담는다. node가 `.ts`를 빌드 없이 바로 돌린다(ADR 0050)"를 더했다. 첫 줄이 바뀌어 `uv run python tools/plan_table.py`를 돌렸다(종료 0, `.scratch/plan.md` 한 줄 바뀜).
- 명세 7(Minor): `CONTEXT.md` 질문 페이지의 _Avoid_ "포털(앱 폴더와 경로 이름에서만)"을 "포털(경로 `/portal/`과 코드 이름에서만)"으로 고쳤다. 폴더 이름은 명세가 짓는다.
- 명세 8(Nit): `.scratch/portal-login/plan.md`의 "(수명은 600초까지, `http/sites.py`)"를 "(질문 페이지의 토큰 수명은 120초다, ADR 0050. `serve`가 받는 상한은 600초, `http/sites.py`)"로 고쳤다.
- 명세 9(Nit): "120초면 느린 망에서도 넉넉하다고 어림하며", "토큰은 서명 한 번이고 그 CPU 비용은 작다고 어림하며(재지 않았다)"로 어림 표시를 달았다.
- 표준 a1(Minor): `CONTEXT.md`에 **사이트 토큰(Site Token)** 항목을 더했다. "사이트가 최종 사용자의 신원을 보증해 RS256으로 서명하고, 위젯이 최종 사용자 경로의 요청마다 싣는 토큰. 발급자가 그 사이트이고 `serve`는 사이트 파일의 공개 키로 검증한다(ADR 0023)." _Avoid_에 "서명 토큰(ADR 0023과 `http/sites.py`가 토큰의 꼴을 말할 때 쓴 이름. 누가 냈는지가 빠진다)"을 두었다. 용어집에는 두 말 모두 정의가 없었고(`grep -n '^\*\*.*토큰' CONTEXT.md`로 봤다), 사용자의 지시문과 기능 계획 첫 줄이 "사이트 토큰"을 쓴다.
- 표준 a2(Minor): `CONTEXT.md` 사이트 항목에 "발급자 하나가 사이트 하나이고"를, 질문 페이지 항목을 "이 저장소가 함께 내는, 사이트 여럿을 담는 웹 페이지와 그 서버. … 사이트 쪽의 것이라 위젯처럼 Agent OS의 일부가 아니다"로 고쳐 서로를 가리키는 정의를 풀었다. ADR 0050에서 페이지가 사이트라던 두 자리도 "사이트 쪽"으로 맞췄다.
- 표준 a3(Minor): `.scratch/pilot-portal/plan.md`에서 사이트가 이 페이지 하나인 배치에서뿐이라던 문장을 "사이트가 하나인 배치에서뿐이다(질문 페이지는 사이트 여럿을 담을 수 있다, ADR 0050)"로 고쳤다.
- 표준 b Nit 1: ADR 0050 Consequences "전역 `fetch` 금지" 항목에 "같은 설정의 Next 서버 파일 금지도 파일 이름 글롭(`**/{route,middleware,proxy,instrumentation}.{ts,tsx,mts,cts,js,jsx,mjs,cjs}`)으로 모든 앱에 걸리므로, 질문 페이지의 파일 이름은 그 넷을 피한다"를 더했다. 글롭은 `web/eslint.config.mjs` 314줄을 열어 글자 그대로 옮겼다.
- 표준 b Nit 2: Consequences "상한"에 "사이트 여럿은 `serve`의 사이트 파일이 처음부터 받던 것이고(ADR 0023), 사이트는 테넌트가 아니라(`CONTEXT.md`의 사이트 _Avoid_) PRD가 미룬 멀티테넌시는 이 설계가 건드리지 않는다"를 더했다.
- 표준 b Nit 3: `.scratch/portal-login/plan.md`의 "모드를 바꿀 때"를 "보증 모드를 바꿀 때"로 고쳤다.
- 표준 c Nit 1·2: 이 일지의 셈(결정 열셋, Considered Options 열넷, Consequences 열)과 ESLint 줄 번호(Server Actions는 74~90줄의 `RESTRICTED_SYNTAX`)를 고쳤다.

남긴 것과 이유.

- 표준 a4(Minor, ADR이 길고 세부를 못 박는다): 사용자가 확인한 요약 ⑪이 "ADR 0050 하나에 결정 전부"이고, 결정으로 적은 세부(쿠키 표시, CSP, 테스트 시나리오, 키 만들기 명령, `/portal/sites/<이름>/`과 `/portal/health`)는 모두 라운드의 답과 요약 ①~⑨에 사용자가 고른 것이다. 크기는 ADR 0024(29.2KB, `wc -c`)보다 작다. 명세가 짓는 것의 목록은 Consequences에 따로 있다.
- 명세 6(Nit, "사이트를 바꾸면 새 대화다 … 받아들인다"): 라운드 3 답의 설명에 없던 대가를 에이전트가 적은 것이 맞다. 결정이 아니라 Consequences의 서술이고 승인 화면의 설명에 한 줄로 보여 사용자가 ADR 승인으로 함께 판정한다.
- 표준 (c)의 웹 요약 메모: ADR의 "Node 문서로 아는 것이고 이 워크스페이스에서 대 보지 않았다"는 그대로 둔다. 명세 전 프로브가 잰다.

다시 돌린 명령. `uv run python tools/plan_table.py`, `tools/check_adr_pointers.py`, `tools/check_md_tables.py`, `tools/check_line_separators.py` 모두 종료 0(이 세션에서 쳤다). 린트·타입·경계·run_checks는 커밋 직전에 돌리고 결과를 아래 적는다.

## 승인 화면

셀프 리뷰 반영 뒤 AskUserQuestion 하나에 질문 둘을 올렸다. `hook_choice_facts`가 처음 보는 화면을 한 번 막아 설명의 사실(슬라이스 9·10·12의 행 이름은 `.scratch/plan.md` 표, 120초·30일·위젯 속성 다섯은 ADR 0050과 두 리뷰 축이 EMBED.md로 대 본 것, `serve`의 사이트 파일 다시 읽기는 ADR 0023 이력 2026-11-04)을 확인한 뒤 같은 질문·라벨로 다시 올렸다. 화면 앞의 글에서 ADR, 슬라이스, ADR 0050의 요지, 새 행 둘을 쉬운 말로 풀었다.

> 사용자: (ADR 0050 초안(질문 페이지는 node:http 서버 하나로 사이트 여럿을 담고, 고지를 확인한 브라우저의 익명 식별자로 사이트 토큰을 낸다)을 승인할까요?) "승인한다 (Recommended)" — 설명: 초안 그대로 결정으로 굳습니다. 기능 계획에 '설계: ADR 0050' 줄이 적히고 다음은 화면 그리기(/ui-design)와 node 실행 프로브, 그다음 명세입니다. 셀프 리뷰가 더한 문장 셋도 함께 승인됩니다. 첫째, 사이트가 고지 글을 비우면 질문 페이지의 기본 글을 쓰고 '익명 식별자 쿠키를 둔다'는 문장은 사이트가 글을 적어도 늘 들어갑니다. 둘째, 설정 파일과 사이트 파일은 시작할 때 한 번만 읽어 운영 중에 바꾸면 다시 띄워야 합니다(serve는 바뀐 사이트 파일을 요청마다 다시 읽습니다). 셋째, '둘 다' 사이트의 비활성 로그인 단추도 e2e로 고정합니다. 대가로 적은 것: 사이트를 바꾸면 대화가 새로 시작되고, 사이트를 옮길 때마다 고지 확인을 한 번씩 더 합니다.

> 사용자: (새 기능 행 둘(portal-admin: 질문 페이지 설정을 화면에서 고치는 관리 화면, widget-appearance: 레이아웃·아이콘 같은 새 모양 칸)을 전체 계획의 어느 자리에 둘까요?) "제품 1.0 묶음에 둔다 (Recommended)" — 설명: 슬라이스 10입니다. 감사 내보내기(audit-export), 입출력 가드레일(io-guardrail), 이용 보고(usage-report)와 같은 줄에 서고, 0.1 판(pilot-release, 슬라이스 9)에는 들지 않습니다. 0.1 판까지는 질문 페이지 설정을 파일로 고치고 모양은 지금 위젯이 받는 다섯 값(에이전트, 제목, 소개, 테마, 밝음)뿐입니다. 두 행 모두 Blocked by는 pilot-portal입니다.

## 승인 뒤

- `.scratch/pilot-portal/plan.md`의 `**Blocked by:** 없음` 뒤에 `**설계:** ADR 0050` 줄을 적었다.
- 새 기능 계획 둘을 만들었다. `.scratch/portal-admin/plan.md`(슬라이스 10, Blocked by pilot-portal. 본문에 근거(ADR 0047·0050, 이 일지의 "다시 꺼냄"), 설계 인터뷰가 먼저 볼 것 셋, 수락)과 `.scratch/widget-appearance/plan.md`(같은 슬라이스와 Blocked by. 지금 속성 다섯, 먼저 볼 것, 수락).
- ADR 0050 Consequences "다른 행"의 슬라이스 문장을 "둘의 슬라이스는 10(제품 1.0 묶음. 0.1 판에는 들지 않는다)이고 Blocked by는 pilot-portal이다. 이 ADR의 승인 화면에서 사용자가 골랐고(일지 2026-11-09-1410), 두 행의 기능 계획이 원천이다"로 고쳤다.
- `uv run python tools/plan_table.py`를 돌려 `.scratch/plan.md`에 새 행 둘이 슬라이스 10에 섰는지 봤다(아래 검증 절).

## 검증(커밋 전)

`uv run ruff check .`(All checks passed), `uv run ruff format --check .`(1957 files already formatted), `uv run python tools/run_checks.py`(종료 0. check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, pytest 419초, web-verify 570초 모두 Passed. 백그라운드로 돌려 끝 알림을 받았다). `git branch --show-current`는 `docs/pilot-portal-design`. `uv run python tools/sibling_overlap.py`는 1로 끝났다. 번호 겹침은 없고(이 브랜치의 새 번호 ADR 0050), origin/main이 1d5d0ed(mcp-http의 ADR 0049, 헌법 3.0.73)로 움직였으며, `docs/constitution/tech.md`를 고치고 판을 올리지 않았다고 알렸다. 그래서 이 커밋 뒤 origin/main을 합치고 그 커밋에서 헌법 판을 3.0.74로 올린다. 함께 고친 파일 후보는 `.scratch/plan.md`, `CONTEXT.md`, `docs/adr/README.md`, `docs/constitution/tech.md`다.

## 커밋 1차와 헌법 판

첫 커밋은 pre-commit의 `check-constitution-version`에 막혔다(종료 1. `docs/constitution/tech.md`를 고쳤는데 `docs/constitution/README.md`의 판이 3.0.72 그대로). 계기를 낸 명령이 실패한 것이라 `handoff.md` 1에 따라 인계하지 않고 잇는다. 판을 3.0.74로 올렸다(`tech.md` 웹 행과 원격·CI 행의 문구 수정이라 patch. origin/main이 3.0.73을 썼으므로 그 위, `sibling_overlap`의 안내대로). 같은 pre-commit의 `check-quotes`가 막지 않는 경고로 낸 인용 열두 건(일지의 리뷰 보고가 반영 전 글을 따옴표로 든 것 아홉, ADR 0050 "다른 행"의 고친 문장 인용 둘, "이미지도 하나" 축약 하나)은 원문 그대로 옮기거나 따옴표를 뗐다. 나머지 검사(parallel-checks 562초 포함)는 모두 Passed였다.

## 인계(둘째, 커밋 뒤)

커밋 뒤 경계에서 `hook_handoff`의 계기를 받았다(세션 컨텍스트 364,981 토큰, 문턱 200,000). `handoff.md`의 인계하지 않는 다섯 경우에 들지 않는다. 계기를 낸 커밋 50214b60은 pre-commit을 지나 성공했고, 이번 요청 범위는 PR과 병합까지이며, 이 세션의 지시문 "이어받을 상태"는 `인계: 셀프 리뷰 직전`이라 같은 경계가 아니고, 이 일지에 `인계 못함` 줄이 없고, `get_session self`에 `parentSessionId`가 없다. 그래서 넘긴다. 이 세션의 지금 제목은 `docs/pilot-portal-design`이고, 넘기며 `docs/pilot-portal-design (인계함)`으로 바꾼다.

이 세션이 한 것과 고친 것은 위 "셀프 리뷰(인계받은 세션)"·"반영"·"승인 화면"·"승인 뒤"·"검증(커밋 전)"·"커밋 1차와 헌법 판" 절에 있다. 번복한 결정은 없다. 앞 세션의 ADR 초안에 셀프 리뷰로 문장을 더하고(고지 기본 글과 식별자 문장, 시작 때 한 번 읽음, 둘 다 사이트의 e2e, 라운드 1 답의 교체 기록, 서버 파일 이름 글롭, 멀티테넌시 아님), `CONTEXT.md`에 사이트 토큰을 더했으며, release-image 계획에 넘기는 문장을 적었다. 사용자는 ADR 0050을 승인하고 새 행 둘을 슬라이스 10에 두기로 골랐다. 헌법 판은 이 커밋에서 3.0.74로 올렸다(앞 절).

커밋 50214b60의 pre-commit은 parallel-checks(517초) 아래 열 검사와 마크다운 표·줄 구분 문자·변이 표·헌법 판·커밋 메시지 검사가 모두 Passed였다. ruff 둘은 스테이지된 `.py`가 없어 Skipped라 손으로 쳤다(`uv run ruff check .` All checks passed, `uv run ruff format --check .` 1957 files already formatted). `check-quotes`가 막지 않는 경고 둘을 남겼는데(이 일지의 셀프 리뷰 보고가 반영 전의 글을 따옴표로 든 두 자리), 이 절을 쓰며 따옴표를 떼고 반영 전의 글이라고 적었다. 이 절과 그 수정은 커밋하지 않았다. 새 세션이 origin/main을 합친 커밋에 함께 싣는다.

### 새 세션이 할 일

1. `git fetch origin main` 뒤 `git merge origin/main`. origin/main에 mcp-http의 ADR 0049가 들어와 `docs/adr/README.md`의 같은 자리에 0049 행을 더했으므로 이 브랜치의 0050 행과 글자 충돌이 예상된다. 둘 다 남긴다(0049 위, 0050 아래). `docs/constitution/README.md`의 판 줄은 origin/main이 3.0.73, 이 브랜치가 3.0.74라 충돌하면 3.0.74와 이 브랜치의 Last Amended(2026-11-09)를 남긴다. `CONTEXT.md`(MCP 서버·전송 항목)와 `docs/constitution/tech.md`(런타임 의존성 행)는 자리가 달라 자동 병합을 확인한다. `.scratch/plan.md`는 손으로 풀지 않고 `uv run python tools/plan_table.py`를 다시 돌린다.
2. 검증을 다시 돌리고(`uv run ruff check .`, `uv run ruff format --check .`, `uv run python tools/run_checks.py`는 백그라운드로, `uv run python tools/sibling_overlap.py`), `git branch --show-current`를 본 뒤 커밋한다(heredoc이나 `-F`, 끝에 `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`). 이 일지의 이 절도 그 커밋에 든다.
3. 푸시, PR(제목은 첫 커밋 제목, 본문 끝에 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`), next-session `merge.md` 2(봇 회차: PR 직전 리뷰 `coderabbit-review`, 봇 코멘트 반영)부터 병합(묻지 않는다)까지, next-session.
4. 이 일지에 병합 전 리뷰와 봇 회차, `## 다음` 절. 회고(`retro`)는 단계를 닫는 세션이 돈다.

### 지시문

```
다음 작업: 기능 pilot-portal. 위젯을 담는 질문 페이지가 로그인 없이 온 사람에게 사이트 토큰을 내, 포털이 없는 공개 데모와 배포 환경을 돕는다
다음 단계: 설계 인터뷰
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /grill-with-docs pilot-portal
브랜치: docs/pilot-portal-design
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-09-1410-pilot-portal-design.md의 "인계(둘째, 커밋 뒤)" 절(남은 단계 넷과 예상 충돌)
이어받을 상태: 인계: 커밋 뒤. docs/journal/2026-11-09-1410-pilot-portal-design.md. 설계 인터뷰와 셀프 리뷰 반영, 승인(ADR 0050 승인, 새 행 portal-admin·widget-appearance는 슬라이스 10), 설계 줄, 새 기능 계획 둘, plan_table, 헌법 판 3.0.74까지 커밋 50214b60에 있다. 푸시하지 않았고 PR은 없다. 일지의 인계 절은 커밋하지 않은 채 워크트리에 있다. 남은 것은 origin/main 합치기, 검증 다시, 커밋, 푸시, PR, 봇 회차, 병합, next-session이다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

워크트리 잠금 풀기는 `git worktree unlock`이 `is not locked`로 끝났다(이미 풀려 있었다). open-session을 부른다 2026-11-09T07:51:13Z

`open_session.ps1`은 `page=16:52:08` 뒤 새 세션 화면의 폴더가 `C:\project\rag-engine`이라(앱의 마지막 폴더. `C:\project\agent`가 아니다) 보내지 않고 멈췄다(`stale=1`은 앞서 열린 화면의 글자를 거른 것). 지시문은 그 화면에 남아 있고 모델은 아직 고르지 않았다. open-session 3의 폴더 오류 갈래대로 같은 파일로 다시 돌리지 않고, 사람에게 환경 버튼에서 `C:\project\agent`를 고르고 모델을 `Fable 5.1 / xhigh`로 맞춰 보내 달라고 부탁하고 턴을 끝냈다. 제목은 `(인계함)` 그대로 둔다. 사람이 보내면 그 세션이 이 브랜치를 잇는다(대기열 378의 다섯 번째 회차).

## origin/main 합치기(셋째 세션)

둘째 인계를 받은 세션이다. 주 체크아웃 `C:\project\agent`에서 시작해 제목을 `docs/pilot-portal-design`으로 바꾸고, `git worktree list`에서 이 브랜치가 체크아웃된 `.claude/worktrees/pilot-portal-design`을 찾아 `EnterWorktree(path)`로 들어왔다. 워크트리에는 커밋 50214b60 위에 이 일지의 수정만 커밋하지 않은 채 있었다.

`git fetch origin main` 뒤 `git merge origin/main`(1d5d0ed8, mcp-http의 ADR 0049). 앞 절이 예상한 대로 셋이 충돌했다. `docs/adr/README.md`는 0049 행 아래에 0050 행을 두어 둘 다 남겼고, `docs/constitution/README.md`의 판 줄은 3.0.74와 Last Amended 2026-11-09를 남겼으며, `.scratch/plan.md`는 손으로 풀지 않고 `uv run python tools/plan_table.py`를 돌려 다시 만들었다(종료 0. origin/main 대비 release-image 행의 "질문 페이지"와 새 행 둘만 다르다). `CONTEXT.md`와 `docs/constitution/tech.md`는 자동 병합됐고 `git diff origin/main`에 이 브랜치의 변경만 남은 것을 봤다. 충돌 표지는 `docs/**/*.md`와 `.scratch/plan.md`에서 0건이다.

검증: `uv run ruff check .`(All checks passed), `uv run ruff format --check .`(1960 files already formatted), `uv run python tools/sibling_overlap.py`(종료 0. 번호 겹침 없음, 형제가 쓴 가장 높은 헌법 판은 origin/main의 3.0.73이라 3.0.74 그대로. mcp-shutdown-spec 워크트리가 `.scratch/plan.md`를 함께 고쳤다고 알렸는데 그 파일은 도구가 만드므로 나중에 병합하는 쪽이 다시 돌린다), `git branch --show-current`는 `docs/pilot-portal-design`. `run_checks.py`는 이 병합 커밋의 pre-commit 결과로 갈음한다(`CLAUDE.md` 검증 명령). 그 결과와 PR 직전 리뷰, 봇 회차는 아래 절에 적는다.
