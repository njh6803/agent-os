# 06: nginx 틀과 위젯 e2e — 실제 serve·Next·nginx(TLS) 뒤에서 iframe 위젯이 요청 하나를 끝까지 보낸다

**What to build:** 운영자가 `deploy/nginx/`의 틀을 `envsubst`로 채우면, nginx가 TLS를 끝내고 최종 사용자 접두사(`/end-user/`)와 위젯 경로(`/widget`)만 바깥에 내보낸다. 나머지는 404다. 이 티켓이 그 틀과 위젯 e2e를 함께 세운다. e2e는 사이트 파일과 RS256 키를 준 실제 `serve`, 그 사이트 파일로 빌드한 실제 Next, 틀을 채운 실제 nginx(TLS)를 띄우고, 다른 출처의 사이트 페이지에 iframe 위젯을 넣어 요청 하나를 결말까지 보낸다. 실행 도중 도구 줄이 결말 전에 서는 것도 본다. CI에는 잡 `e2e-widget`이 생기고 필수 검사 `verify`에 든다.

이 티켓이 위젯 e2e의 준비(키, 인증서, 임시 플러그인 루트, nginx를 찾는 길)를 세우고, 뒤의 티켓(09, 10, 11)이 그 위에 사례를 더한다. 페이지 안 방식(커스텀 요소)의 사례는 10, 새로 고친 뒤 다시 붙는 사례는 09, 실제 모델은 11이다. 07과 08은 사례를 더하지 않고 이 e2e로 회귀를 본다.

근거는 `.scratch/web-widget/spec.md`의 "nginx와 배포" 절과 Testing Decisions 4다. ADR 0024(nginx 뒤의 한 출처, 접두사만 내보냄, fail-closed)가 앞선 결정이다. 설계 인터뷰가 nginx 중계를 잰 것이 `.scratch/web-widget/probes/nginx_relay/`이고, 우회 사례의 요청 줄을 글자 그대로 보내 누가 답하는지 본 결과는 `measure.py` 독스트링 끝에 있다.

**Blocked by:** 02 (core — 실시간 중계. 실제 서버에서 도구 줄이 결말 전에 서려면 있어야 한다), 05 (대화)

**Status:** ready-for-agent

### nginx 틀(`deploy/nginx/`)

- [ ] **틀 하나.** 서버 이름, 인증서와 키의 경로, 파이썬과 Next의 상류 주소, 듣는 포트는 `${…}` 자리로 두어 운영자가 `envsubst`로 채우고, e2e는 같은 자리를 테스트의 값으로 채운다
- [ ] **`location`은 셋이다.** `/end-user/` 아래는 파이썬에, `= /widget`과 `/widget/` 아래는 Next에 넘기고, 나머지는 `return 404`다. `proxy_pass`에 URI를 붙여 정규화한 경로를 넘기고, `proxy_http_version 1.1`을 명시하며, `X-Forwarded-For`·`X-Forwarded-Proto`는 덮어쓴다
- [ ] **443은 TLS와 HSTS, 80은 ACME 확인 경로와 HTTPS로 넘기기만 한다**
- [ ] **`client_max_body_size`는 `256k`다.** 틀의 주석에 까닭(BMP 밖 글자 20,000자를 모두 `\u` 이스케이프한 시작 본문이 240,091바이트)과, 사이트 파일에서 `request_chars`를 올리면 이 값도 그 수 × 12에 1KB를 더한 값 이상으로 올려야 한다는 것을 적는다. 결정 본문의 거부 사유는 서버가 길이를 묶지 않아, 위젯 밖의 클라이언트가 이보다 큰 사유를 보내면 nginx의 413이 답한다는 것도 적는다(위젯은 08이 사유에 상한을 둔다)
- [ ] 운영의 인증서는 운영자가 마련한다(ADR 0011 이력 2026-10-03). 틀은 경로만 받는다

### e2e의 준비(선례 `web/apps/admin/e2e/stack.ts`)

- [ ] **실제 `serve`**를 사이트 파일과 RS256 공개 키로 띄우고, **실제 Next**를 같은 사이트 파일(`AGENT_OS_SITE_FILE`)로 빌드해 띄우며, **실제 nginx**를 틀에 테스트의 값을 채워 띄운다. serve의 환경에는 부모의 환경을 펼친다(관리 화면 e2e의 준비가 그렇다. 11이 `.env`의 키를 serve까지 넘기는 길이다)
- [ ] **키와 토큰은 `node:crypto`가 짓고, 자체 서명 인증서는 파이썬 `cryptography`가 짓는다**(`pyjwt[crypto]`로 이미 든다)
- [ ] **에이전트는 임시 플러그인 루트에 짓는, 모델 없이 도는 것들이다.** 이 티켓의 사례가 쓰는 것은 도구를 직접 부르는 것과 출력에 HTML 조각을 내는 것이다. 승인 대상에서 멈추는 것과 새로 고치는 동안 끝나지 않는 것은 그것을 쓰는 티켓이 더한다
- [ ] **사이트 페이지는 위젯과 다른 출처**에서 서빙한다. 허용 출처의 페이지 하나와 허용 밖 출처의 페이지 하나다
- [ ] **사이트 페이지의 출처는 호스트 이름으로 둔다**(`localhost`나 `*.localhost`). 표기 규칙(04)은 IP 호스트의 출처와 CSP의 문법 밖인 호스트(밑줄, `$`, 빈 라벨이 든 것)의 출처도 지나보낸다. 그런데 CSP3(2026-09-16 Working Draft)의 문법은 호스트 글자를 영문자·숫자·하이픈으로 두고, host-part 대조는 host가 domain이 아니면 맞지 않는다고 적는다. 그래서 그런 출처는 `frame-ancestors`에서 맞지 않을 수 있다(04가 원문을 내려받아 읽었다. 브라우저에서는 재지 않았다, `tests/fixtures/site_file/README.md`). 위젯 빌드의 `AGENT_OS_SITE_FILE`이 상대 경로면 시작 래퍼를 부른 자리에서 푼다(04)
- [ ] **로컬의 nginx는 환경 변수 `AGENT_OS_NGINX`가 주는 실행 파일을 쓰고, 없으면 PATH의 `nginx`를 쓴다.** 둘 다 없으면 건너뛰지 않고, 그 변수와 nginx를 받을 곳을 말하는 문구로 실패한다. 이 PC의 PATH에는 nginx가 없다. 설계의 측정은 nginx.org의 윈도우 zip을 받아 경로로 줬다(`.scratch/web-widget/probes/` README의 `nginx_relay` 행)
- [ ] **nginx는 master와 worker를 함께 거둔다.** 선례인 관리 화면 준비의 거두기(`stack.ts`의 `stop()`)는 자식 하나를 `kill()`할 뿐이다. Windows의 nginx는 master와 worker가 따로 뜨므로 master만 끊으면 worker가 포트를 쥔 채 남을 수 있다. 설계의 측정(`nginx_relay/measure.py`)은 `nginx -s stop`과 프로세스 트리째 끊기(`taskkill /T /F`)로 내렸다. 이 PC에서 e2e를 한 번 돌린 뒤 nginx 프로세스와 그 포트가 남지 않았는지 보고 일지에 적는다(PR 직전 리뷰가 짚었고, 이 PC에 nginx가 없어 재지 못했다)

### e2e의 사례

- [ ] **iframe 위젯이 요청 하나를 결말까지 보낸다.** 허용 출처의 사이트 페이지가 postMessage로 토큰을 넘기고, 위젯이 도구를 직접 부르는 에이전트를 돌려 도구 줄과 출력을 그린다. 위젯의 요청은 위젯 출처 아래 `/end-user`로 가고, 같은 출처라 CORS 사전 요청이 없다
- [ ] **도구 줄이 결말 전에 선다.** 도구를 직접 부르는 에이전트가 첫 도구를 부른 뒤 다음 도구에서 기다리는 동안, 첫 도구 줄이 이미 화면에 서 있다. 아래 nginx 사례의 "SSE가 결말 전에 흐르는 것"을 위젯 화면에서 보는 것이고, nginx가 SSE를 모으지 않는 것과 02의 실시간 중계가 함께 있어야 초록이다
- [ ] **iframe 산출물의 CSS가 선다.** iframe 페이지의 위젯 요소에 디자인 토큰의 값이 계산된 스타일로 든다(명세 "테스트 프로젝트"의 "두 산출물의 빌드에서 서는지는 e2e가 본다"의 iframe 몫. 페이지 안 방식의 몫은 10이 본다)
- [ ] **postMessage 거르기.** 부모가 아니거나 허용 밖 출처에서 온 토큰 메시지는 버려진다
- [ ] **`frame-ancestors`.** 허용 출처의 페이지는 iframe을 품고, 허용 밖 출처의 페이지는 품지 못한다
- [ ] **출력의 HTML 조각이 실행되지 않는다**
- [ ] **글자 수 상한.** 입력창의 상한이 서버의 기본값과 같다. 서버에 직접 보낸 20,000자는 받고 20,001자는 422다
- [ ] **nginx.** 80과 443의 동작과 HSTS. 우회 사례(`..`, 퍼센트 인코딩, `/end-userx`, 밖에서 안으로 들어오는 `/runs/../end-user/…`), 파이썬이 접두사 밖 경로를 받지 않는 것, 대소문자(Linux에서만). 본문 크기의 경계는 BMP 밖 글자 20,000자를 모두 `\u` 이스케이프한 본문을 위젯을 거치지 않고 보내, 413이 아니라 파이썬의 응답을 받는 것으로 본다. SSE가 결말 전에 흐르는 것
- [ ] **각 사례는 판정을 되돌리면 빨개지는 것을 먼저 본다**(원칙 II). 예: 틀의 `return 404`를 빼면 우회 사례가, `frame-ancestors`를 `*`로 바꾸면 허용 밖 사례가 빨개진다

### CI와 지침

- [ ] **CI 잡 `e2e-widget`.** 관리 화면의 `e2e` 잡과 같은 모양에 러너의 nginx를 쓴다. 필수 검사 `verify`의 `needs`에 더하고, 워크플로 첫머리 주석의 잡 목록도 고친다. 워크플로 감사(zizmor)가 초록이다
- [ ] **로컬 명령을 정한다.** 관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`)의 모양을 따른다
- [ ] **`CLAUDE.md` 검증 명령 절의 셋을 고친다.** web 줄의 괄호에 위젯 e2e의 명령과 치는 때(위젯, api-client의 위젯 몫, 서버의 최종 사용자 경로, `deploy/nginx/`를 건드렸을 때)를 더하고, "게이트는 열다섯"을 열여섯으로, "남은 둘인 e2e와 사진 비교는 CI만 돈다"를 위젯 e2e까지 셋으로 바꾼다. 하네스 문서이므로 새 세션에서 실려 읽히는 것을 확인한다(`CLAUDE.md` 작업 규약 3)
- [ ] **새 잡이 거짓으로 만드는 닫힌 문장을 고친다.** CI 잡의 수, 매 푸시에서 도는 e2e의 수, 실제 `serve`를 띄우는 구동자의 수를 세어 닫은 문장과, 실제 uvicorn·사이트 파일·서명 토큰의 조립을 지나는 자리를 "유일한"으로 닫은 문장이다. 그런 말(잡의 수, "e2e 하나", "구동자", "유일한 자리")로 저장소를 grep해 살아 있는 문서의 잔존이 0인지 본다(`CLAUDE.md` 작업 규약 4). 지금 아는 자리는 `docs/constitution/tech.md` 원격·CI 행의 "잡 다섯", `.claude/rules/http.md`의 "실제 `serve`의 둘째 구동자인 관리 화면의 e2e"와 "매 푸시에서 도는 것은 e2e 하나다", `tests/test_main.py` 최종 사용자 경로 LLM 시험 독스트링의 "실제 실행으로 보는 유일한 자리다", 같은 파일 serve 판정 시험 독스트링의 "매 푸시에서 도는 관리 화면의 e2e(실제 serve 의 둘째 구동자)", `web/apps/admin/e2e/stack.ts` 머리 주석의 "e2e 는 실제 `serve` 의 둘째 구동자이고"다. "구동자"는 같은 앱을 ASGI로 직접 부르는 시험의 이름이기도 하다(`docs/constitution/tech.md`의 같은 절, `tests/channel/http/test_end_user.py` 머리). 그 뜻의 일치는 고치지 않고, 위젯 e2e를 부를 이름이 그 이름과 겹치지 않게 한다. `tech.md`는 헌법 문서이므로 `docs/constitution/README.md`의 판을 patch로 올린다(`tools/check_constitution_version.py`가 본다). 바꾼 rules도 새 세션에서 실려 읽히는 것을 확인한다

### 검증

- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이고, 위젯 e2e를 로컬에서 한 번 돌려 초록이다
