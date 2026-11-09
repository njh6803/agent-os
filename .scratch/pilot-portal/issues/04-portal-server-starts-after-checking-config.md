# 04: 질문 페이지 서버가 설정과 사이트 파일을 대 본 뒤에야 뜨고, 키 만들기 명령이 공개 키 조각을 낸다

**What to build:** 질문 페이지를 띄우는 운영자가 `pnpm -C web/apps/portal make-key -- --private-key <경로> --kid <kid>`를 치면 RSA 2048 개인 키가 그 경로에 PKCS#8 PEM으로 쓰이고, 사이트 파일에 붙일 `[[sites.public_keys]]` 조각(`kid`와 SPKI PEM `pem`)이 TOML 그대로 화면에 찍힌다. 이미 그 경로에 파일이 있으면 덮어쓰지 않고 종료 코드 1로 끝난다(스토리 10). 이어서 `pnpm -C web/apps/portal start -- --config <질문 페이지 설정> --site-file <사이트 파일>`을 치면, 두 파일과 키가 서로 맞을 때만 서버가 떠서 `질문 페이지가 http://127.0.0.1:<port>/portal/ 에 섰다. 사이트 <N>개.` 한 줄을 찍는다. 어긋나면 뜨지 않고 stderr에 `구성 오류:` 한 줄과 어긋난 자리마다 `sites[1].agent: <까닭>` 꼴의 줄을 모두 찍은 뒤 종료 코드 1로 끝난다(스토리 9). 뜬 서버는 `/portal/health`에 `{"status":"ok"}`로 답하고, 아직 그 밖의 경로는 404다.

04는 01 뒤이고 05를 막는다. 02와 나란히 돈다. 둘 다 README의 트리, `docs/constitution/tech.md` 웹 행, 헌법의 판, `web/pnpm-lock.yaml`을 고칠 수 있으니, 나중에 병합하는 쪽이 main을 받아 그 파일을 맞추고 헌법의 판은 먼저 병합된 판보다 높게 고른다. 질문 페이지 앱을 처음 만드는 티켓이라 앱의 뼈대와 tsconfig도 여기서 둔다(명세 "띄우기와 타입 검사"의 주석 첫째).

**병합 뒤에 틈이 있다(to-tickets에서 사용자가 아홉 장 분할을 골랐다).** 이 티켓만 병합된 main에서는 질문 페이지가 시작 검사와 `/portal/health`만 내고, 페이지(`/portal/`)와 사이트 끝점은 404다. 아직 이 앱을 띄우는 배포나 CI 잡이 없으므로(CI 잡은 06) 바깥에 보이는 것은 바뀌지 않는다.

근거는 `.scratch/pilot-portal/spec.md`의 "앱과 패키지"와 그 2026-11-10 명세 검토 주석 첫째(피할 폴더 이름), "띄우기와 타입 검사"(앱의 `start` 스크립트, tsconfig)와 그 주석 첫째, "질문 페이지 설정"과 그 주석, "시작 검사와 진단"과 그 주석, "경로와 끝점"(그 밖의 경로, 캐시 헤더, `nosniff`), "키 만들기 명령", "HTTP 요청 처리기와 서버", Testing Decisions의 "Vitest"와 그 주석이다. 앞선 결정은 ADR 0050의 결정 "앱과 서버", "시작 인자와 시작 검사", "키 만들기 명령", "기록"과 Consequences "전역 `fetch` 금지"다.

**Blocked by:** 01 (사이트 파일 읽기와 디자인 시스템 서브패스를 패키지로 뽑는다). `@agent-os/site-file`의 넓힌 모델과 허용 출처 판정, `@agent-os/ui/themes`의 `THEMES`·`MODES`를 쓴다

**Status:** ready-for-agent

### 앱의 뼈대

- [ ] **`web/apps/portal`(`@agent-os/portal`)을 만든다.** `start` 스크립트는 `node tools/start.ts --config <질문 페이지 설정> --site-file <사이트 파일>`이고 두 인자는 필수다. 빌드 단계와 `dist` 폴더가 없고 앱 폴더에 산출을 쓰지 않는다(명세 "띄우기와 타입 검사")
- [ ] **앱의 tsconfig는 `web/tsconfig.base.json`을 extends 하고 `module`·`moduleResolution`을 `nodenext`로, `allowImportingTsExtensions`와 `types: ["node"]`를 둔다.** 페이지 스크립트의 DOM 라이브러리는 06이 `lib`에 더한다. `web/tools/check-tsconfig.ts`가 이 tsconfig를 보는지 그 출력으로 확인한다. 확장자 없는 상대 import 하나를 일부러 넣어 `pnpm -C web verify`의 타입 검사가 `TS2835`로 빨개지는 것을 본 뒤 되돌린다
- [ ] **파일 이름은 `route`, `middleware`, `proxy`, `instrumentation`을 피하고, 폴더 이름은 ESLint 층 경계가 요소로 가르는 `app`, `components/*`, `api/*`, `hooks/queries/*`, `types/*`, `stores`를 피한다.** 서버 코드는 그 밖의 폴더(예: `server/`)에 둔다(명세 "앱과 패키지"의 주석 첫째)
- [ ] **README의 트리와 `docs/constitution/tech.md` 웹 행에 앱을 더한다.** 헌법을 고치면 판을 patch로 올린다

### 설정 읽기와 시작 검사

- [ ] **질문 페이지 설정을 smol-toml로 읽고 명세 "질문 페이지 설정"의 칸과 규칙을 그대로 판정한다.** `schema_version = "1"`이 필수이고 모르는 칸은 거부한다. `[portal]`의 `public_origin`(`@agent-os/site-file`의 허용 출처 표기 규칙), `private_key`(상대 경로는 설정 파일의 폴더 기준), `kid`, `host`(기본 `127.0.0.1`), `port`와 `[[sites]]`의 `name`(`^[a-z][a-z0-9-]{1,62}$`), `issuer`, `agent`, `heading`, `intro`, `theme`(`@agent-os/ui/themes`의 `THEMES`, 기본 `nokcheong`), `mode`(`MODES`), `assurance`(`anonymous`·`login`·`both`), `notice`(적었는데 비었거나 공백뿐이면 구성 오류), `report_url`(`http`·`https`)이다
- [ ] **고지 전문을 사이트마다 시작 때 짓는다.** `notice`를 적었으면 그 글 끝에, 적지 않았으면 기본 글 세 문단으로 짓되 둘째 문단(쿠키 문장)은 늘 끝에 붙고 그 안의 "30일"은 쿠키 수명 상수에서 그린다. 전문을 짓는 함수는 쿠키 수명 일수를 인자로 받고, 설정을 읽는 길이 그 인자로 쿠키 수명 상수를 넘긴다. 시험이 30이 아닌 값을 넘겨 볼 수 있게 하기 위해서다. 짧은 고지는 사이트가 바꾸지 못하는 상수다(명세 "질문 페이지 설정")
- [ ] **시작 검사는 명세 "시작 검사와 진단"의 항목을 모두 보고 어긋남을 모두 모아 알린다.** 사이트 파일 대조는 그 절의 주석이 이름을 든 여섯 갈래다. 사이트 파일이 `site-file` 패키지의 판정을 지나지 못한다, `issuer`가 사이트 파일에 없다, `agent`가 그 사이트의 열 에이전트 밖이다, `public_origin`이 그 사이트의 허용 출처 밖이다, `kid`가 그 사이트의 공개 키에 없다, `kid`로 고른 공개 키가 개인 키에서 난 공개 키와 다르다(SPKI DER 바이트로 견준다). 설정의 갈래(`issuer`·`name`의 겹침, 개인 키를 읽지 못하거나 RSA가 아님(PKCS#8과 PKCS#1 둘 다 받는다), 루프백 밖 `host`)는 따로 본다
- [ ] **진단은 stderr에 `구성 오류:` 한 줄 뒤에 `<자리>: <까닭>` 줄이고 종료 코드는 1이다.** 까닭에 값(키의 글, 경로의 내용)은 싣지 않는다. 예외는 `portal.host: 루프백만 받는다(127.0.0.1, ::1). 받은 값: <값>` 하나다(명세 "시작 검사와 진단"의 주석 둘째)
- [ ] **시작 로그는 stdout에 `질문 페이지가 http://<host>:<port>/portal/ 에 섰다. 사이트 <N>개.` 한 줄이고, `host`가 `::1`이면 호스트 자리는 `[::1]`이다.** 접근 로그는 남기지 않고, 어떤 출력에도 쿠키 값과 토큰을 싣지 않는다(ADR 0050 결정 "기록")
- [ ] **루프백 목록이 네 벌이 된다.** 질문 페이지의 목록에 다른 셋을 가리키는 주석을 달고, `src/agent_os/main.py`의 `LOOPBACK_HOSTS` 위 주석, 관리 화면 `tools/loopback.ts`와 위젯 `tools/start.ts`의 머리 주석이 든 "셋"을 넷으로 고쳐 질문 페이지를 함께 든다(명세 "시작 검사와 진단"의 주석 셋째)

### HTTP 요청 처리기와 서버

- [ ] **서버는 순수 HTTP 요청 처리기 하나(메서드, 경로, 헤더, 쿠키 → 상태, 헤더, 본문)와 그것을 `node:http`에 거는 얇은 겉으로 나뉜다.** 순수 함수는 시계와 UUID 만들기를 인자로 받는다(명세 "HTTP 요청 처리기와 서버"). 서버 코드와 시험은 `fetch`를 쓰지 않는다
- [ ] **이 티켓의 경로는 `GET /portal/health`(200 `application/json` `{"status":"ok"}`, `Cache-Control: no-store`) 하나다.** 모르는 경로는 404, 아는 경로의 다른 메서드는 405와 `Allow`이고, 모든 응답에 `X-Content-Type-Options: nosniff`를 단다(명세 "경로와 끝점")
- [ ] **서버는 설정의 `host`와 `port`에서만 듣는다**

### 키 만들기 명령

- [ ] **앱의 스크립트 `make-key`가 명세 "키 만들기 명령"대로 돈다.** `node:crypto`로 RSA 2048 키 쌍을 만들어 개인 키를 PKCS#8 PEM으로 그 경로에 쓰고(POSIX에서는 모드 0600), stdout에 `[[sites.public_keys]]` 조각을 TOML 그대로 출력한다. `[portal]` 조각은 출력하지 않는다

### Vitest

- [ ] **node 프로젝트에서 순수 함수를 부르는 사례를 명세 "Vitest"와 그 주석 가운데 이 티켓의 몫으로 둔다.** 맞는 설정이 읽힌다. 어긋남마다 그 자리가 진단에 들고 값은 들지 않되 루프백 밖 `host`만 받은 값이 든다. 사이트 파일 대조의 여섯 갈래 각각, 모르는 칸, 판, `name` 꼴, 빈 `sites`, 비었거나 공백뿐인 `notice`, 루프백 밖 `host`, `issuer`·`name`의 겹침, RSA가 아닌 개인 키. 고지 전문(적은 글 끝에 쿠키 문장, 적지 않으면 기본 글 세 문단). 쿠키 문장의 일수는 인자로 넘긴 쿠키 수명에서 그려진다. 30이 아닌 값(예: 7)을 넘겨 "7일"이 서는 것을 보고, 설정을 읽은 결과의 전문에 쿠키 수명 상수의 일수가 서는 것을 본다. 상수만 넘기는 사례는 "30일"을 글로 박은 구현에서도 초록이다(명세 "Vitest"의 주석이 든 "30일" 사례를 잴 수 있게 한 것이다). 시작 로그의 주소(`127.0.0.1`은 그대로, `::1`은 `[::1]`). `/portal/health`, 모르는 경로의 404와 다른 메서드의 405, `nosniff`. 키 명령의 출력이 TOML로 읽히고 그 `pem`이 개인 키의 공개 키와 같으며, 이미 있는 파일을 덮어쓰지 않고 종료 코드 1로 끝나고 그 파일이 그대로다
- [ ] **시험 이름은 행동을 말하는 한국어 문장이다.** 시험이 읽는 사이트 파일은 공유 픽스처(`tests/fixtures/site_file/`)를 쓰거나 시험이 임시 폴더에 짓는다. 키 파일은 커밋하지 않는다

### 검증

- [ ] **빨강을 먼저 본다**(헌법 원칙 II). 설정 읽기와 시작 검사의 시험이 구현 전에 빨갛다
- [ ] **실제로 띄워 본다.** 맞는 설정과 사이트 파일로 `start`를 쳐 시작 로그 한 줄을 보고 `/portal/health`가 답하는 것을 본 뒤, `agent`를 하나 틀리게 바꿔 진단과 종료 코드 1을 본다. 친 명령과 출력은 PR 본문에 적는다
- [ ] **검증 명령이 모두 초록이다.** 손으로 치는 다섯이다
