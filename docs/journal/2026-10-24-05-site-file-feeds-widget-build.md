# 2026-10-24 (05) 사이트 파일이 위젯 빌드를 채운다 (web-widget 04)

브랜치 `feature/04-site-file-feeds-widget-build`, 워크트리 `.claude/worktrees/04-site-file-feeds-widget-build`. 티켓은 `.scratch/web-widget/issues/04-site-file-feeds-widget-build.md`.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/web-widget/issues/04-site-file-feeds-widget-build.md
>
> 다음 작업: .scratch/web-widget/issues/04-site-file-feeds-widget-build.md. 서버와 위젯 빌드가 같은 사이트 파일에서 합친 허용 출처와 가장 작은 요청 글자 수 상한을 읽고, 허용 출처의 표기를 파이썬과 Node가 같은 픽스처로 판정한다
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/web-widget/issues/04-site-file-feeds-widget-build.md
> 브랜치: feature/04-site-file-feeds-widget-build
> 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-50-widget-app-skeleton.md 의 "다음" 절. 막힌 티켓(05~11)은 .scratch/plan.md 의 web-widget 행
> 이어받을 상태: 없음
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## 정리

tidy-checkouts: 루트(main)를 `96d3e1df` 에서 `51a0417e` 로 당겼다. 병합된 워크트리 `04-ci-checks-ticket-done`, `web-widget-spec-2`(쉬는 세션의 프로세스를 끝낸 뒤)와 브랜치 `worktree-02-runtime-relays-call-events-live` 를 지웠다. 나머지는 병합된 PR 이 없거나, 바뀐 파일·다시 만들 수 없는 무시된 항목이 있거나, 다른 프로세스가 쥐었거나, 앱의 표지가 있어 남겼다.

## 한 것

- 파이썬 `src/agent_os/main.py`: 사이트 파일을 읽을 때 허용 출처마다 `_origin_rule` 로 표기를 판정한다. 규칙은 열셋(wildcard, null, shape, scheme, case, path, userinfo, port, default-port, idn, ipv6, host, ipv4)이고 이 차례로 첫 위반 하나를 낸다. 진단은 `sites[0].allowed_origins[1]: 브라우저가 Origin 헤더에 싣는 표기가 아니다(규칙 ipv4). …` 꼴로 자리와 규칙을 말하고 값을 싣지 않는다. 전에는 `"*"` 하나만 거절했다.
- 위젯 `web/apps/widget/tools/site-file.ts`(새): `buildInput(env)` 가 `AGENT_OS_SITE_FILE` 을 읽어 합친 허용 출처(처음 나온 차례, 겹친 것은 하나)와 가장 작은 `request_chars`(적지 않은 사이트는 기본 20,000)를 낸다. 변수가 없으면 빈 목록과 20,000이고, 빈 글이면 진단을 던진다. 파일을 읽지 못하거나 모양이 서버와 어긋나면 자리마다 진단을 모아 던진다. 파서는 smol-toml 1.9.1이다. `originRule` 은 파이썬과 같은 규칙과 차례이고, IPv6 의 압축형은 RFC 5952 를 손으로 지어 맞댄다(Node 에는 파이썬의 `ipaddress` 가 없다).
- `next.config.ts`: 설정 파일이 읽힐 때 `buildInput(process.env)` 를 부른다. `frame-ancestors` 는 합친 목록이고 비면 `'none'` 이다. `env` 로 `AGENT_OS_WIDGET_ORIGINS`(공백으로 이은 글)와 `AGENT_OS_WIDGET_REQUEST_CHARS`(십진수 글)를 번들에 싣는다.
- 시작 래퍼 `tools/start.ts`: next 를 부르기 전에 상대 경로의 `AGENT_OS_SITE_FILE` 을 부른 자리 기준의 절대 경로로 바꾼다(`absoluteSiteFile`). `start.spawn.test.ts` 가 읽지 못하는 사이트 파일로 실제 `next build` 를 띄워 진단과 종료 코드 1을 본다.
- 픽스처 `tests/fixtures/site_file/`(새): 표기 사례 `origins.json`(지나는 것과 막히는 것, 막히는 것마다 규칙), 두 언어가 함께 읽는 `sites.toml`(사이트 둘, 하나만 기본보다 작은 `request_chars`)과 그 기대값 `sites.json`, 규칙의 뜻과 근거를 적은 `README.md`.
- 시험: 파이썬 `tests/test_main.py` 의 사이트 파일 절에 표기 사례마다의 지남·막힘과 TOML 픽스처의 기대값을 더했다. Node 는 `tools/site-file.test.ts`(새, 표기 사례와 Node 의 `new URL(v).origin` 대조, 모양의 갈래, BOM 과 UTF-8), `next.config.test.ts`(변수 없음, 갈래마다의 실패, TOML 픽스처의 두 값), `tools/start.test.ts`(상대 경로 풀기)다.
- 의존성: 위젯 앱 `dependencies` 에 `smol-toml` `1.9.1`(판 고정). 잠금 파일에는 그 하나만 든다.
- 문서: 헌법 판 3.0.54(`docs/constitution/tech.md` 의 web 행), `README.md` 트리, 티켓 04의 "이 티켓이 정한 것", 05의 머리("04가 넘기는 값"), 06·10의 항목, `.scratch/plan.md` 의 web-widget 행.
- 프로브: 변이 표 `.scratch/web-widget/probes/site_file_mutations.toml`(40, 새)과 그 README 행. 티켓 03의 위젯 변이 표 27번의 원문을 고친 `next.config.ts` 에 맞췄다.

## 결정

- **Node 의 TOML 파서는 smol-toml 1.9.1이다**(ADR 0024가 티켓에 넘긴 셋째). 의존성이 없고 BSD-3-Clause 이며, 1.9.1은 2026-10-09T10:21:39Z 에 나온 최신 판이다(`pnpm view smol-toml`). 정수를 bigint 로 읽는 `integersAsBigInt: true` 로 정수와 실수를 가른다. 파이썬의 엄격한 정수가 실수 `20000.0` 을 받지 않기 때문이다. `unsafeKeyBehaviour: "throw"` 로 `__proto__` 같은 키를 조용히 넘기지 않는다. ADR 0024가 "Node에 TOML 파서 의존성이 하나 늘고, 그 판은 티켓이 잰다"고 이미 적어 새 ADR 은 쓰지 않았다.
- **BOM 과 UTF-8.** 파일 머리의 BOM 은 smol-toml 이 받고 파이썬 `tomllib` 이 거절해(이 세션에서 둘 다 손으로 봤다), Node 쪽이 BOM 을 따로 막는다. 파일은 `TextDecoder` 의 `fatal: true` 로 풀어 잘못된 UTF-8 을 대체 문자로 바꾸지 않는다. 파이썬도 잘못된 UTF-8 을 거절한다.
- **빌드 값은 `next.config.ts` 의 `env` 로 싣는다.** 설치된 Next 16.3.6 의 `next-config-js/env.md` 는 `env` 의 값을 `process.env.이름` 자리에 빌드 때 바꿔 넣고 `process.env` 를 구조 분해하면 동작하지 않는다고 적는다(53행). `guides/environment-variables.md` 는 `NEXT_PUBLIC_` 변수의 예로, 변수로 고른 이름(`process.env[varName]`)과 `process.env` 를 다른 이름에 담아 읽는 것은 바꿔 넣지 않는다고 적는다(182~191행). `env` 의 값에도 같다는 것은 미루어 본 것이다. 05가 읽는 법은 05의 머리에 옮겼다.
- **상대 경로는 래퍼가 푼다.** 래퍼가 next 를 부르기 전에 작업 폴더를 앱으로 옮기므로, 그대로 두면 설정 파일이 앱 폴더 기준으로 풀어 운영자가 준 파일을 찾지 못한다.
- **호스트의 규칙은 WHATWG URL 의 도메인 파서를 따른다.** 비지 않았고 금지된 도메인 글자가 없으면 지난다. 여기까지 두 번 고쳤다. 첫 판은 CSP 의 `host-char` 로 라벨을 LDH(영문자·숫자·하이픈)로 좁히고 끝 점도 막았는데, 끝 점을 막은 까닭으로 적은 "CSP 의 문법이 끝 점을 받지 않는다"가 틀렸다. CSP3 Working Draft(2026-09-16)를 curl 로 내려받아 읽었다. 2.3.1 Source Lists 의 `host-part = "*" / [ "*." ] 1*host-char *( "." 1*host-char ) [ "." ]` 는 끝 점 하나를 받아, 끝 점 하나를 받게 고쳤다. 그 뒤 셀프 리뷰 명세 축이 LDH 좁히기가 명세의 규칙 목록 밖이라고 짚어(아래 명세 축 1) WHATWG URL 원문(Living Standard, 2026-10-19 갱신본)을 내려받아 읽고 도메인 파서대로 되돌렸다. 끝 라벨(끝 점 하나는 떼고 본다)이 수 꼴인 호스트(`http://127.0.0.1.`, `http://0x7f.`)는 브라우저가 IPv4 로 읽어 정규형으로 다시 적으므로(같은 원문의 ends in a number checker 와 IPv4 parser), 끝 점째 정규형이 아니라고 ipv4 규칙으로 막는다. 밑줄·`$`·빈 라벨이 든 호스트는 같은 원문의 도메인 파서가 실패로 내지 않아 브라우저가 `Origin` 에 그대로 싣는다(Node 24.19.0 의 `new URL` 로도 손으로 봤고, 픽스처의 지나는 사례마다 Node 시험이 맞댄다).
- **IP 호스트와 CSP 의 문법 밖인 호스트의 출처는 지나보낸다.** CSP 의 문법은 호스트 글자를 영문자·숫자·하이픈으로 두고 라벨을 비우지 않아, 밑줄·`$`·빈 라벨이 든 호스트와 대괄호로 적는 IPv6 는 `frame-ancestors` 에 적을 수 없다. 같은 원문의 노트는 IP 주소가 문법에는 맞아도 source expression 에서 실제로 맞는 것은 `127.0.0.1` 뿐이라고 적고, 6.7.2.10 은 host 가 domain 이 아니면 "Does Not Match" 를 낸다. 명세의 규칙 목록이 이 출처들을 막지 않고 서버의 CORS 는 이 출처들도 글자로 맞대므로 막지 않는다. `frame-ancestors` 에서 맞지 않을 수 있다는 것을 픽스처 README 와 06(e2e 는 호스트 이름의 출처만 쓴다)·10(임베드 안내)에 넘겼다. 브라우저에서는 재지 않았다.
- **진단은 값을 싣지 않는다.** 사용자 정보 규칙에 걸리는 값에는 비밀번호가 들 수 있다(원칙 V 의 뜻을 구성 오류 문구에도 둔다).
- **Node 가 서버와 같게 보는 모양의 범위.** 타입·필수 키·모르는 키·판, 1 이상의 `request_chars`, 허용 출처의 표기다. 공개 키의 수, 다른 상한의 범위, 서버만 읽는 값의 뜻은 보지 않는다. 그 값이 틀린 파일로는 빌드가 지나도 serve 가 뜨지 못한다(명세 "빌드의 입력은 사이트 파일 하나다"). smol-toml 이 TOML 1.1 을 따라 tomllib(TOML 1.0)이 거절하는 문법을 받는 파일도 같다(아래 표준 축 1).
- **빈 `AGENT_OS_SITE_FILE` 은 실패다.** 빈 글은 변수를 준 것이라 사이트를 열려는 뜻으로 읽고, 조용히 사이트 없음으로 빌드하지 않는다(아래 명세 축 4).

## 변이

- `site_file_mutations.toml` 첫 판 28: 도구가 모두 기대대로로 판정했다. 시험 하나가 1분을 넘긴 회차가 셋이었고(도구가 찍은 시간), 그 동안 CPU 사용률은 100%였다(PowerShell `Get-CimInstance Win32_Processor` 로 손으로 봤다). 느린 까닭은 가르지 않았다.
- 끝 점 고침 뒤: 원문이 바뀐 셋(4, 16, 23)과 새 넷(5 파이썬 끝 점 떼기, 6 파이썬 IPv4 판정의 끝 점째, 17·18 그 둘의 Node 쪽)을 번호로 골라 다시 돌려 7 모두 기대대로였다. 표는 32가 됐다.
- 위젯 표 `widget_app_mutations.toml` 을 `--since origin/main` 으로: 27번(frame-ancestors 를 self 로 열기)의 원문을 고친 `next.config.ts` 23행에 맞춘 뒤 1 기대대로(`next.config.test.ts` 의 두 시험이 빨갛다).
- 셀프 리뷰 반영 뒤: 호스트 규칙을 되돌려 하이픈 변이 둘은 원문이 사라졌고, 끝 점을 라벨로 세는 변이 둘은 지나는 사례(`https://shop.example.`)가 더는 빨개지지 않아 막는 사례(`http://127.0.0.1.`)로 겨눔을 옮겼다. 빈 라벨이 지나는 사례가 되어 URL 파서 대조의 변이는 `https://*.shop.example` 의 규칙을 바꾸게 고쳤다. 금지된 도메인 글자의 경계(밑줄·공백·`%`·DEL)를 두 언어에서 넷씩, 필수 키와 판의 Node 시험을 둘 더해 40이 됐다. 모양 판정과 호스트 규칙의 코드가 크게 바뀌어 표 전체를 다시 돌렸고 40 모두 기대대로였다. DEL 변이는 시험 id 를 고를 수 없어 막는 시험 전체를 돌고, `-x` 로 마지막 사례인 DEL 에서 멈췄다(1 failed, 48 passed).

## 셀프 리뷰

base `51a0417e`(HEAD 와 같다), 바뀐 추적 파일 19, 커밋 0, 미추적 8(사이트 파일 모듈과 그 시험, 픽스처 넷, 변이 표, 이 일지). 리뷰가 도는 동안 같은 체크아웃에서 `tools/run_checks.py` 가 돌았다. 그사이 origin/main 이 `eec99a5`(web-widget 02)로 움직여 이 일지를 01 에서 02 로 옮겼다(`sibling_overlap --move`). 반영 뒤 커밋 직전에 origin/main 이 `7496a83` 으로 움직여 2026-10-24-03 까지 가져가, 같은 도구로 05 로 다시 옮겼다.

### 표준 축 (Critical·Major 없음)

맞는 것으로 잰 것: 끝 점 경계 입력 여섯을 두 언어의 판정 함수에 넣어 같은 답, smol-toml 의 사용권·의존성·날짜와 잠금 파일, 파이썬의 엄격한 UTF-8, 변이 32 모두의 `expect_output`, Next 문서 인용 둘의 글자, CSP 발췌와 README 의 끝 점 서술.

1. Minor: "서버가 거절할 파일이면 빌드가 실패한다"(`site-file.ts` 머리, 티켓, 일지)는 닫힌 주장이 거짓이다. smol-toml 1.9.1 은 TOML 1.1.0 을 따르고(설치본 README), 1.0 만 받는 옵션이 없다(`ParseOptions`). 여러 줄 인라인 표, 끝 쉼표 인라인 표, `\e`·`\x41` 이스케이프, 초 없는 시각을 smol-toml 은 모두 받고 파이썬 3.12.10 의 tomllib 은 모두 거절했다. 대조로 넣은 1.0 문법은 둘 다 받았다(세션 스크래치패드의 스크립트 둘로 손으로 봤다). 판정: 문장을 고친다. 반례 하나를 덧붙이지 않고 성질로 적는다(Node 파서의 TOML 판이 tomllib 보다 새로워, 1.1 에만 있는 문법은 빌드가 받고 serve 가 거절한다). 갈림을 고정하는 시험은 두지 않는다. 그 시험은 smol-toml 이 1.1 을 받는다는 남의 동작을 계약처럼 고정하고, 그런 파일로는 serve 가 뜨지 못해 조용히 지나가지 않는다.
2. Minor: `site-file.ts` 의 모양 판정(`sitesOf`·`siteOf`·`checkKeys`·`checkText`·`checkTexts`·`unknownKeys`·`requestCharsOf`)이 받은 `problems` 배열을 고친다. `CODING_STANDARDS.md` 의 "출력 인자를 쓰지 않는다"와 CQS 에 어긋난다. 판정: 고친다. 판정마다 찾은 문제를 새 배열로 돌려주고, 값도 내는 것은 값과 문제를 함께 돌려준다. 변이 표가 겨누는 줄(`sites.flatMap`, `limits.reduce`)은 글자 그대로 둔다.
3. Minor: 티켓 05 머리와 이 일지가 구조 분해를 가이드(`guides/environment-variables.md`)가 적는다고 썼다. 구조 분해는 `env.md` 53행이 적고, 가이드 182~191행은 `NEXT_PUBLIC_` 변수의 예로 변수로 고른 이름(`process.env[varName]`)과 `process.env` 를 다른 이름에 담아 읽는 것을 든다. 판정: 고친다. `env` 의 값에도 같다고 본 것은 두 문서가 모두 빌드 때 글자를 바꿔 넣는다고 적은 데서 미루어 본 것이라고 적는다.
4. Minor(판단 항목): 픽스처 README 의 IP 문단이 IPv4 와 IPv6 를 가르지 않는다. 원문 노트의 "문법에 맞는다"는 IPv4 의 말이고, 대괄호와 `:` 는 `host-char` 가 아니라 IPv6 는 `host-part` 의 문법 밖이다. 밑줄을 막은 논리라면 IPv6 도 막아야 하는데 지나보낸다. 판정: 막지 않고 README 를 고친다. 명세의 규칙 목록이 IPv6 의 압축형을 지나는 표기로 정했고, 서버의 CORS 는 그 출처를 글자로 맞댄다. 밑줄은 명세가 정하지 않아 이 티켓이 골랐다(티켓의 "이 티켓이 정한 것" 4). 그 갈래를 README 에 적는다.
5. Minor: `start.ts` 독스트링의 "읽지 못하면 next 가 그 진단을 찍고 종료 코드 1로 끝난다(`start.spawn.test.ts`)"에서, 그 시험이 밟는 것은 `build` 와 깨진 TOML 하나다. `next.config.ts` 머리는 dev·build·start 가 멈춘다고 적는다. 판정: 손으로 dev·start 를 띄워 본 뒤 고친다. 없는 사이트 파일로 래퍼의 `dev` 는 3.1초, `start` 는 0.8초 만에 종료 코드 1로 끝났고 둘 다 진단을 찍었다. 다만 둘 다 next 의 "Ready" 를 먼저 찍은 뒤 멈췄다(세션 스크래치패드의 스크립트로 손으로 봤다. 끝난 뒤 포트 3457 에 남은 연결은 없었다). 두 문장에 시험이 보는 것과 손으로 본 것을 가른다.
6. 판단 항목: `site-file.ts` 에 파일 읽기, 모양, 출처 표기, IPv6 압축이 함께 드는 것(Divergent Change 가능성), 파이썬의 규칙 이름이 맨 `str` 인 것(Primitive Obsession 가능성). 판정: 둘 다 남긴다. 파이썬은 같은 규칙을 사이트 파일 읽기 곁(`main.py`)에 두어, 두 언어가 한 자리씩 들어야 "같은 차례"를 맞대기 쉽다. 규칙 이름의 오타는 두 언어의 픽스처 시험이 잡는다.
- Nit: README 의 "`wildcard`, `null`, `scheme`, `host`는 이렇게 정한 금지"가 과하다. `host` 의 사례에는 브라우저도 거절하는 빈 호스트(`https://`)가 든다. 판정: 고친다. 이 넷은 브라우저가 그대로 싣는 값도 막는 규칙이라 URL 파서 대조에서 뺀다고 적는다.
- Nit: 변이 표지 `assert 0 == 1` 둘(파이썬의 끝 점 IPv4, 함께 읽는 TOML 의 `request_chars`)은 단언의 일반 문구다. 두 변이는 시험 하나로 좁혀 있다. 앞의 것은 그 시험의 첫 단언(`code == 1`)이 낸다. 뒤의 것은 `len(refused) == 1` 이 내는데, 같은 시험의 `len(uvicorn_calls) == 1` 도 같은 문구를 낼 수 있어 표지가 고른 단언을 가르지 못한다(`.claude/rules/probes.md` 첫 항목). 판정: 뒤의 것을 고친다. 그 단언에 메시지를 달고 표지를 그 메시지로 바꾼다. 앞의 것은 남긴다.
- Nit: `next.config.test.ts` 의 `it.each` 가 같은 설정을 두 번 읽는다. 판정: 남긴다.

### 명세 축 (Major 1)

맞는 것으로 잰 것: 명세가 든 막히는 아홉이 픽스처에 모두 들고 두 언어가 막는다(픽스처 전체에서 규칙이 어긋난 곳 0, 경계 입력 66개를 두 언어에 넣어 차이 0), Node 가 "읽지 못하는 것" 갈래를 모두 실패로 내고 `next.config.test.ts` 에 티켓이 든 갈래가 모두 있다, 변수 없음과 빈 목록의 `'none'` 과 20,000, `sites.json` 하나를 두 언어가 읽는다, 받는 쪽의 Blocked by 사슬(05→04, 06→05, 10→06), 진단에서 값을 뺀 것이 명세의 "어긋난 항목과 어긴 규칙"과 맞는다, 끝 점 받기·BOM 막기·상대 경로 풀기·`env` 이름 둘이 범위 안이다.

1. Major: 명세의 규칙 목록 밖의 금지. 명세는 "호스트는 소문자 ASCII(국제화 도메인은 퓨니코드)"까지만 정했는데(명세가 정했다: 규칙의 목록), `host` 규칙이 CSP 의 `host-char` 를 근거로 밑줄과 빈 라벨을 막는다. `http://my_host:3000` 은 Node 의 `new URL` 이 그대로 직렬화하고 전에는 CORS 에서 맞던 항목인데 이제 serve 가 뜨지 못한다. 명세 188행과 티켓 27행의 "조여서 막히는 표기는 두 갈래다"가 거짓이 되고, 같은 문법 밖인 IPv6 는 지나보내 근거도 앞뒤가 맞지 않는다. 판정: 명세대로 되돌린다. 명세를 고치는 것은 사용자의 승인이 드는 일이고, 명세는 `frame-ancestors` 에서 맞지 않는 IP 출처도 이미 지나보낸다. WHATWG URL 원문(Living Standard, 2026-10-19 갱신본)을 curl 로 내려받아 읽었다. 도메인 파서는 ASCII 도메인을 소문자로 바꿔 돌려주고, 빈 결과와 금지된 도메인 글자(금지된 호스트 글자, C0 제어 문자, `%`, DEL)가 든 결과만 실패로 낸다. 그래서 `host` 규칙을 "비지 않았고 금지된 도메인 글자가 없다"로 바꾼다. 밑줄·빈 라벨·`$` 같은 글자가 든 호스트는 지나고, CSP 의 `host-part` 문법 밖이라 iframe 페이지에서는 맞지 않을 수 있다는 것을 IP 출처와 함께 픽스처 README 와 06·10 에 넘긴다. 후보 스물일곱을 Node 24.19.0 의 `new URL(v).origin` 에 넣어 보니 원문의 목록과 맞았다(세션 스크래치패드의 스크립트로 손으로 봤다).
2. Minor: 깨진 퓨니코드(`https://xn--zz.example`, `https://xn--.example`)가 두 언어에서 지나는데 Node 의 `new URL` 은 `ERR_INVALID_URL` 로 거절한다. 판정: 남긴다. 위 원문의 도메인 파서는 ASCII 도메인을 "Unicode ToASCII 의 결과와 상관없이" 소문자로 돌려준다고 적어(web compatibility), 지금의 표준으로는 브라우저가 그대로 싣는 표기다. Node 24.19.0 이 그보다 옛 동작이라 그 사례는 픽스처에 두지 않고 README 에 적는다.
3. Minor: `main.py` 의 "이 모양과 표기를 같은 규칙으로 판정한다"와 `site-file.ts` 의 "서버가 거절할 파일은 둘이다"가 거짓이다. `public_keys = []` 와 `hourly_runs_per_site = 0` 을 파이썬은 거절하고 Node 는 받는다. 판정: 표준 축 1과 함께 고친다. Node 가 서버와 같게 보는 것만 적고, 서버만 보는 제약(공개 키의 수, 다른 상한의 범위, 서버만 읽는 값의 뜻)과 TOML 1.1 문법은 빌드가 받고 serve 가 거절한다고 적는다.
4. Minor: 이 일지의 "빈 글이면 빈 목록과 20,000이다"가 코드와 다르다. 코드는 빈 글에서 던진다. 판정: 일지를 고치고, 빈 글을 실패로 보는 결정을 티켓의 "이 티켓이 정한 것"에 더한다. 빈 글은 변수를 준 것이라 사이트를 열려는 뜻이고(명세 "빌드의 입력은 사이트 파일 하나다"의 까닭), 조용히 사이트 없음으로 빌드하지 않는다.
5. Minor: 필수 키 가운데 `issuer`·`audience`·`public_keys` 와 `schema_version` 이 빠진 경우를 보는 Node 시험이 없다. `REQUIRED_SITE_KEYS` 에서 빼도 초록이다. 판정: 시험을 더하고 변이로 빨강을 본다.
6. Minor: `site-file.ts` 머리와 `next.config.ts` 머리가 아직 없는 05 의 동작을 현재형으로 적었다(대기열 35). 판정: 고친다. 값을 싣는다는 것만 적고, 쓰는 자리는 05 의 머리를 가리킨다.
- Nit: 05 메모의 출처. 판정: 표준 축 3과 함께 고친다.
- Nit: "브라우저는 밑줄 호스트를 그대로 싣는다", "브라우저는 끝 점을 떼고 IPv4 로 읽는다"와 "ends in a number" 의 근거가 Node 를 손으로 본 것이다. 판정: 고친다. 위에서 내려받은 WHATWG 원문의 ends in a number checker 와 IPv4 파서를 근거로 들고, Node 는 손으로 본 것으로 적는다.
- Nit: 잰 것보다 넓게 적은 dev·start. 판정: 표준 축 5와 함께 고친다.

### 반영

- 고친 것:
  - 표준 1·명세 3: `main.py` 의 사이트 파일 주석, `site-file.ts` 머리, 티켓 04의 6, 이 일지의 결정. Node 가 서버와 같게 보는 것만 적고, 서버만 보는 제약과 TOML 1.1 에만 있는 문법은 빌드가 받고 serve 가 거절한다고 적었다.
  - 표준 2: `site-file.ts` 의 모양 판정이 받은 배열을 고치지 않고, 값과 문제를 함께 든 `Read<T>` 나 새 문제 배열을 돌려준다.
  - 표준 3·명세 Nit(05 메모의 출처): 05 머리와 이 일지의 Next 출처를 `env.md` 53행과 가이드 182~191행으로 갈라 적었다.
  - 표준 4: 명세 축 1의 되돌림에 덮였다. README 의 CSP 문단이 CSP 의 문법 밖인 호스트(밑줄, `$`, 빈 라벨, IPv6)와 IPv4 를 가른다.
  - 표준 5·명세 Nit(dev·start): `start.ts` 와 `next.config.ts` 의 문장에 시험이 보는 것(`build`)과 손으로 본 것(`dev`·`start`)을 갈랐다.
  - 표준 Nit(README 의 정한 금지): 정한 금지는 `wildcard`·`null`·`scheme` 셋이고, `host` 는 Node 시험의 URL 파서 대조에 넣었다.
  - 표준 Nit(표지): `request_chars` 단언에 메시지를 달고 그 변이의 표지를 그 메시지로 바꿨다.
  - 명세 1(Major): `host` 규칙을 WHATWG URL 의 금지된 도메인 글자로 되돌렸다. 두 언어의 코드, 규칙 문구, 픽스처(밑줄·`$`·빈 라벨·끝 점 둘·`https://.` 은 지나는 사례로, 공백·`%`·`^`·`|`·`<`·`\`·C0·DEL 은 막는 사례로), README, 티켓 04의 4, 06·10.
  - 명세 2: 깨진 퓨니코드는 픽스처에 두지 않고 README 에 적었다.
  - 명세 4: 한 것의 빈 글 줄을 고치고, 빈 글을 실패로 보는 결정을 티켓 04의 3과 이 일지의 결정에 더했다.
  - 명세 5: Node 의 필수 키 시험 여섯(사이트 항목의 키 다섯, `schema_version`)을 더했다.
  - 명세 6: `site-file.ts`·`next.config.ts` 머리의 05 현재형을 빼고 05의 머리를 가리켰다.
  - 명세 Nit(근거): 밑줄·끝 점·ends in a number 의 근거를 WHATWG 원문으로 들고, Node 는 손으로 본 것으로 적었다.
  - 반영 도중 드러난 것: DEL 사례를 픽스처에 넣자 파이썬 시험의 도우미 `_toml_strings` 가 DEL 을 날 글자로 TOML 에 써서 tomllib 이 거절했다(`json.dumps(…, ensure_ascii=False)` 는 DEL 을 이스케이프하지 않는다). ASCII 표기(`json.dumps(value)`)로 바꿨다.
- 남긴 것과 이유: 표준 6(두 언어가 같은 규칙을 한 자리씩 드는 편이 차례를 맞대기 쉽고, 규칙 이름의 오타는 두 언어의 픽스처 시험이 잡는다), 표준 Nit `it.each`(같은 설정을 두 번 읽는 값은 시험 시간뿐이다), 명세 2의 사례(지금의 표준과 Node 24.19.0 이 갈려 픽스처에 두면 한쪽이 틀린다), 막는 시험의 표지 `assert 0 == 1`(그 시험의 첫 단언 `code == 1` 만 내는 문구다).
- 다시 돌린 것: 변이 표 전체(40 모두 기대대로, 위 변이 절), `-m llm`(아래 검사 절). 손으로 치는 다섯은 커밋의 pre-commit 으로 갈음한다(결과는 아래 검사 절).

PR 직전 `bug-perf-review` 에 밀 주장(반영으로 새로 쓴 사실 문장, 원문):

1. 픽스처 README 의 `host` 행: "그 밖의 호스트는 비지 않았고, 금지된 도메인 글자(C0 제어 문자, 공백, `#`, `%`, `/`, `:`, `<`, `>`, `?`, `@`, `[`, `\`, `]`, `^`, `\|`, DEL)가 없다"
2. 같은 README 의 `ipv4` 행: "브라우저는 그런 호스트를 IPv4로 읽어 정규형으로 다시 적고 끝 점도 뗀다(`http://127.0.0.1.`은 `http://127.0.0.1`이 된다)"
3. 같은 README: "domain parser는 ASCII 도메인을 소문자로 바꿔 돌려주고 빈 결과와 금지된 도메인 글자가 든 결과만 실패로 낸다. `%`는 그 앞에서 퍼센트 인코딩을 풀어, 든 값은 바뀌거나 실패한다."
4. 같은 README: "깨진 퓨니코드 라벨(`https://xn--zz.example`)도 지금의 표준으로는 그대로 실린다. 그런데 Node 24.19.0의 `new URL`은 그것을 `ERR_INVALID_URL`로 거절해"
5. 같은 README: "문법은 호스트 글자(`host-char`)를 영문자·숫자·하이픈으로 두고 라벨을 비우지 않으므로, 밑줄·`$`·빈 라벨이 든 호스트와 대괄호로 적는 IPv6는 `frame-ancestors`에 적을 수 없다." "명세의 규칙 목록이 이 출처들을 막지 않아(서버의 CORS는 이 출처들도 글자로 맞댄다)"
6. 티켓 04의 4: "명세의 규칙 목록 밖이고 서버의 CORS에서는 맞던 항목을 serve가 거절하게 되어"
7. 티켓 04의 6, `main.py` 주석, `site-file.ts` 머리: "smol-toml은 TOML 1.1을 따라 파이썬의 tomllib(TOML 1.0)이 거절하는 문법도 받으므로, 그런 파일도 같다", "서버만 보는 제약(공개 키의 수, 다른 상한의 범위, 발급자의 겹침, 공개 키의 PEM 과 `kid`, 열 에이전트의 이름)은 다시 판정하지 않는다"
8. 티켓 04의 3: "빈 글은 변수를 준 것으로 보아 빌드가 실패한다."
9. 티켓 05: "`next-config-js/env.md`는 `env`의 값을 `process.env.이름`의 자리에 빌드 때 바꿔 넣고, `process.env`를 구조 분해하면 동작하지 않는다고 적는다." "그 예는 `NEXT_PUBLIC_` 변수다."
10. `next.config.ts`·`start.ts`: "dev·start 는 손으로 봤다(둘 다 next 의 Ready 를 찍은 뒤 멈췄다, 일지 2026-10-24-05)"
11. 티켓 06·10: "CSP3(2026-09-16 Working Draft)의 문법은 호스트 글자를 영문자·숫자·하이픈으로 두고, host-part 대조는 host가 domain이 아니면 맞지 않는다고 적는다"
12. `tests/test_main.py` 의 `_toml_strings` 독스트링: "보이는 ASCII 밖(제어 문자, DEL, 비ASCII)은 모두 이스케이프로 적는다. TOML 은 기본 문자열 안의 날 DEL 을 받지 않는다."
13. `origins.json` 의 메모: "밑줄. 브라우저는 그대로 싣고 CSP 의 host-char 는 받지 않는다", "퍼센트 인코딩. 브라우저는 풀어서 싣는다", "역슬래시. 브라우저는 경로의 시작으로 읽는다"

## 검사

- 반영 전 `uv run python tools/run_checks.py`: pytest 하나(`tests/tools/test_hook_edit_during_commit.py` 의 images 단언)만 빨갰다. 같은 때 다른 세션의 `git.exe` 가 상대 경로의 실행 파일로 떠 있었고, 그 시험만 홀로 다시 돌리면 0.69초에 지났다. 이 변경과 무관한 것으로 보고 아래 "다음"에 넘긴다.
- 반영 뒤 `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 1036 files already formatted.
- 반영 뒤 `uv run --env-file ../../../.env pytest -m llm`: 7 passed(133.89초). LLM 토큰 합계 51,325(입력 50,308, 출력 1,017), 트레이스 10개, 모델 호출 21건. 트레이스를 남기지 않은 LLM 시험 1개는 세지 못했다. 반영 전의 실행은 7 passed(275.97초), 토큰 54,968(입력 53,871, 출력 1,097), 트레이스 10개, 모델 호출 22건이었다.
- 반영 뒤 `pnpm -C web visual:widget`(Docker): 5 passed(16.0초).
- 반영 뒤 변이: 위 변이 절(40 모두 기대대로).
- 첫 커밋 시도는 pre-commit 에 막혔다. 둘이었다. web-verify 의 ESLint 가 `site-file.ts` 의 `[...host]` 를 `@typescript-eslint/no-misused-spread` 로 막았다(반영으로 호스트 규칙을 다시 쓰며 들인 줄이라 반영 전의 `run_checks` 는 보지 못했다). `Array.from(host)` 로 바꾸고, 앞의 idn 규칙이 ASCII 밖을 막아 글자 하나가 코드 단위 하나라는 주석을 달았다. 변이 표 검사는 `.scratch/end-user-channel/probes/contract_mutations.toml` 의 27(허용 출처의 와일드카드를 받는다)이 옛 `"*"` 검사를 겨눠 원문이 0번이라고 막았다. `*` 는 이제 모양 규칙에도 막혀 `wildcard` 판정만 바꾸면 그 시험이 빨개지지 않으므로, `_origin_rule` 의 `return "wildcard"` 를 `return None` 으로 바꾸는 변이로 옮겼다. 그 27과 `site_file_mutations.toml` 의 22~25(금지된 글자의 Node 쪽)를 다시 돌려 5 모두 기대대로였고, Node 위젯 시험은 222 passed 였다. 그 표의 README 행에 적었다.
- 둘째 커밋 시도의 pre-commit: ruff 둘, `run_checks` 의 검사 열(check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, web-verify 242.9초, pytest 302.3초), 마크다운 표, 줄 구분 문자, 변이 표, 헌법 판, 인용 대조(경고만 내는 검사다. 일지 아홉 줄과 헌법 README 한 줄에 경고 10건을 냈고, 하나씩 가르지 않았다), 커밋 메시지가 모두 Passed. 카나리아 명세는 대상 파일이 없어 Skipped. 반영 전 `run_checks` 에서 빨갰던 `test_hook_edit_during_commit` 의 시험은 두 번의 pre-commit 에서 모두 지났다.
- 관리 화면 e2e 는 로컬에서 치지 않았다. 건드린 시작 래퍼는 위젯의 것이고, 관리 화면의 e2e 는 사이트 파일을 쓰지 않는다(`web/apps/admin` 에 `site-file` 이 없다). CI 의 `e2e` 잡이 본다.

## 인계

커밋 뒤에 세션 컨텍스트가 인계 문턱(20만 토큰)을 넘어 `hook_handoff` 의 계기가 왔다(`커밋 뒤`). 인계하지 않는 때 다섯에 들지 않았다. 커밋이 pre-commit 을 지났고, 요청 범위가 병합까지이고, 이어받은 상태가 없고, `인계 못함` 줄이 없고, `get_session` 의 `self` 에 `parentSessionId` 가 없었다. 이 세션의 지금 제목은 `feature/04-site-file-feeds-widget-build` 이다. 이 절은 커밋하지 않고, `## 다음` 은 새 세션이 쓴다.

지시문:

```
다음 작업: .scratch/web-widget/issues/04-site-file-feeds-widget-build.md. 서버와 위젯 빌드가 같은 사이트 파일에서 합친 허용 출처와 가장 작은 요청 글자 수 상한을 읽고, 허용 출처의 표기를 파이썬과 Node가 같은 픽스처로 판정한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/04-site-file-feeds-widget-build.md
브랜치: feature/04-site-file-feeds-widget-build
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-24-05-site-file-feeds-widget-build.md 전체(특히 "반영" 끝의 PR 직전 bug-perf-review 에 밀 주장 열셋과 "검사"). 막힌 티켓(05~11)은 .scratch/plan.md 의 web-widget 행
이어받을 상태: 인계: 커밋 뒤. 구현, 셀프 리뷰와 그 반영, 변이, -m llm, visual:widget, 커밋(pre-commit 통과)까지 마쳤고 남은 단계는 implement 의 커밋 다음부터다, 일지 docs/journal/2026-10-24-05-site-file-feeds-widget-build.md. 남은 차례: origin/main 병합(.scratch/web-widget/probes/README.md 에서 main 이 더한 relay_mutations 행과 글자 충돌이 난다), 일지의 커밋 절, PR 직전 리뷰(bug-perf-review 브리프에 일지 "반영"의 밀 주장 열셋을 싣는다), PR, 봇 회차, 병합, next-session. 일지의 "인계" 절은 이 세션이 커밋하지 않고 남겼다. 일지 "다음"에 넘길 것: 반영 전 run_checks 에서 test_hook_edit_during_commit 이 다른 세션의 git 프로세스와 겹쳐 한 번 빨갰던 일(일지 "검사")
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `feature/04-site-file-feeds-widget-build (인계함)` 으로 바꿨고, 멈출 백그라운드 작업은 없었고, `git worktree unlock` 으로 이 워크트리의 잠금을 풀었다.

open-session을 부른다 2026-10-23T18:09:05Z

## 이어 받은 세션(커밋 뒤)

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/web-widget/issues/04-site-file-feeds-widget-build.md

(지시문은 위 "인계"의 것과 같다. 제목을 `feature/04-site-file-feeds-widget-build` 로 바꾸고 워크트리에 `EnterWorktree(path)` 로 들어갔다.)

### 합치기

- `git merge origin/main` 으로 `7496a830`(PR #378, #377)을 합쳤다(405511c0). `.scratch/web-widget/probes/README.md` 는 자동으로 합쳐졌고, main 이 더한 `relay_mutations.toml` 행 아래에 이 브랜치의 `site_file_mutations.toml` 행이 든다. 앞 세션과 같은 까닭으로 앱의 `sync_with_base_branch` 는 쓰지 않았다(일지 2026-10-24-01, 앱이 만든 워크트리가 아니다).
- `sibling_overlap`: 번호 겹침 없음. 함께 고친 파일은 `.scratch/plan.md` 하나(PR #356, 워크트리 `02-build-tokens-json`·`mcp-shutdown-spec`)다.
- 합친 뒤 `uv run python tools/run_checks.py`: 종료 코드 0(web-verify 257.0초, pytest 342.4초).

### PR 직전 리뷰

CodeRabbit CLI 는 `Seat: not assigned`(Plan: Free)라 대체 둘을 나란히 돌렸다.

- `/security-review`(합친 뒤): 지적 없음. 판정을 지난 값에 공백·CR·LF·제어 문자가 들지 못해 CSP 헤더를 쪼개거나 출처를 덧붙일 수 없고, 서버의 CORS 는 Starlette 의 글자 그대로 비교라 넓어지지 않으며, 두 언어의 진단에 값이 실리지 않고, smol-toml 은 `unsafeKeyBehaviour: "throw"` 로 `__proto__` 를 거절한다. `;`·`,` 가 든 호스트가 판정을 지나는 것은 운영자 구성에서만 나고 좁히는 쪽이라 지적이 아니라고 봤다(LOW 강화안).
- `bug-perf-review`: 두 언어의 `originRule`·`_origin_rule` 에 무작위 입력 30만 개를 넣어 규칙 이름이 어긋난 것이 0 이었다. 유효 Minor 다섯, 보류 셋. 밀 주장 열셋 가운데 어긋난 것은 7 하나(지적 1)다.
  - [Minor, 고침] `site-file.ts` 머리의 서버만 보는 제약 열거에 발급자의 빈 값과 `|` 가 빠졌다. "발급자의 빈 값·겹침·`|`" 로 고쳤다. `main.py` 주석과 티켓 04 는 "서버만 읽는 값의 뜻" 이라는 포괄어라 두었다.
  - [Minor, 고침] 줄 끝이 `\r` 하나인 파일을 서버는 받고 빌드는 거절했다. 서버의 `path.read_text` 는 텍스트 모드라 보편 줄바꿈으로 `\r\n`·`\r` 을 `\n` 으로 바꾼다. `site-file.ts` 의 `readSiteFile` 이 `universalNewlines` 로 같게 바꾼 뒤 `siteFileInput` 에 넘긴다. 변이 표가 원문으로 겨누는 `textOf` 의 `TextDecoder` 줄은 그대로 둔다. `next.config.test.ts` 에 시험을 먼저 더해 빨강(`each key-value declaration must be followed by an end-of-line (1행 21열)`)을 본 뒤 고쳤다.
  - [Minor, 남김] `;`·`,` 가 든 호스트(`https://shop.example,other.example`)가 두 언어의 `host` 규칙을 지나고, `frame-ancestors` 헤더에서 그 글자부터 뒤의 출처가 빠진다. 막지 않는다. 명세의 규칙 목록 밖의 금지이고(셀프 리뷰 명세 축 1 과 같은 까닭), 결과는 출처가 줄어드는 쪽이다. 픽스처 README 의 CSP 문단에 그 효과를 적었다. 헤더를 가르는 글자는 CSP3 2026-09-16 Working Draft 를 WebFetch 로 읽은 웹 요약으로 봤다(지시문은 `;`, 정책은 `,`).
  - [Minor, 고침] `request_chars` 가 10^21 이상이면 `String(number)` 가 `1e+21` 을 실었다. tomllib 과 smol-toml(`integersAsBigInt`) 모두 10^21 을 받는 것을 손으로 봤다. `next.config.ts` 가 `BigInt(input.requestChars).toString()` 으로 십진수 글을 짓는다. 시험을 먼저 더해 빨강(`Received "1e+21"`)을 본 뒤 고쳤다. 2^53 을 넘는 상한은 `number` 를 거쳐 가까운 정수가 되는 것을 `WIDGET_REQUEST_CHARS_ENV` 의 독스트링에 적었다.
  - [Minor, 고침] `tests/test_main.py` 의 `_toml_strings` 가 BMP 밖 글자를 서로게이트 쌍 이스케이프로 적어 tomllib 이 거절한다(`Escaped character is not a Unicode scalar value` 를 손으로 봤다). 표기 픽스처에 그런 글자가 없어 독스트링에 한계를 적었다.
  - [보류] 파이썬 3.13 부터 `IPv6Address.compressed` 가 IPv4 를 품은 주소를 점 표기로 적는다는 리뷰어의 기억. 이 프로젝트는 `requires-python = "==3.12.*"` 이고 3.12.10 은 `::ffff:102:304` 를 냈다. 이 PC 에 3.13 이 없어 확인하지 못했다. PR 의 "남긴 위험"에 적는다.
  - [보류] 빈 파일·BOM·잘못된 UTF-8·실수·겹친 출처를 두 프로세스에 같은 파일로 먹이는 대조는 리뷰어가 스크립트 쓰기 거부로 하지 못했다. 각 갈래는 두 언어의 시험이 따로 고정한다.
  - [보류] 밀 주장 10(dev·start 를 손으로 봄)과 11(CSP3 원문)은 원문을 열지 못한 보류다. 앞 세션이 손으로 보고 내려받아 읽은 것이 근거다.
- 반영 뒤: `pnpm -C web exec vitest run --project node apps/widget/next.config.test.ts apps/widget/tools/site-file.test.ts` 190 passed, Prettier 통과, `tools/mutate.py --check` 로 `site_file_mutations.toml`(40)·`widget_app_mutations.toml`(34) 모두 원문이 한 번씩 있다. 손으로 치는 다섯은 커밋의 pre-commit 으로 갈음한다.
