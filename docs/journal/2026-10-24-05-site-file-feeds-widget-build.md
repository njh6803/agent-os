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

### PR

- 반영을 200b77d6 으로 커밋했다. pre-commit: ruff 둘, `run_checks` 의 검사 열(web-verify 239.7초, pytest 335.5초), 마크다운 표, 줄 구분 문자, 변이 표, 인용 대조(경고 없음), 커밋 메시지가 모두 Passed. 카나리아 명세와 헌법 판은 대상 파일이 없어 Skipped.
- 커밋 뒤 `커밋 뒤` 인계 계기가 왔지만, 이 세션의 지시문이 `인계: 커밋 뒤` 로 시작해 넘기지 않았다(next-session "인계할 때" 1).
- 푸시하고 PR #379 를 200b77d6 으로 열었다. 연 직후 CI 2 통과, 5 대기였다. 앱의 PR 감시는 이 세션에 묶였다(`get_status` 의 `bound: true`). `@coderabbitai review` 코멘트는 남기지 않았다(새 세션이 남긴다).

## 인계(PR 연 뒤)

컨텍스트가 문턱을 넘은 채 `PR 연 뒤` 경계에 와서 넘긴다. 인계하지 않는 때 다섯에 들지 않았다. PR 이 열렸고, 요청 범위가 병합까지이고, 이어받은 상태가 `인계: 커밋 뒤` 라 이번 경계와 다르고, `인계 못함` 줄이 없고, `get_session` 의 `self` 에 `parentSessionId` 가 없었다. 이 세션의 지금 제목은 `feature/04-site-file-feeds-widget-build` 이다. 이 절은 커밋하지 않았다.

```
다음 작업: .scratch/web-widget/issues/04-site-file-feeds-widget-build.md. 서버와 위젯 빌드가 같은 사이트 파일에서 합친 허용 출처와 가장 작은 요청 글자 수 상한을 읽고, 허용 출처의 표기를 파이썬과 Node가 같은 픽스처로 판정한다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/04-site-file-feeds-widget-build.md
브랜치: feature/04-site-file-feeds-widget-build
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-24-05-site-file-feeds-widget-build.md 의 "이어 받은 세션(커밋 뒤)"부터 끝까지. 막힌 티켓(05~11)은 .scratch/plan.md 의 web-widget 행
이어받을 상태: 인계: PR 연 뒤. PR #379를 200b77d6으로 열었고 next-session 순서 1의 2(봇 회차)부터 한다. 첫 @coderabbitai review 코멘트도 새 세션이 남긴다. PR 직전 리뷰에서 남긴 Minor(;·, 가 든 호스트가 판정을 지난다. 명세의 규칙 목록 밖이라 막지 않았다)와 보류(파이썬 3.13의 IPv6 표기)는 PR 본문 "남긴 위험"에 근거가 있다. 봇이 같은 자리를 짚으면 그 근거로 답한다. 일지 "다음"에 넘길 것: 반영 전 run_checks 에서 test_hook_edit_during_commit 이 다른 세션의 git 프로세스와 겹쳐 한 번 빨갰던 일(일지 "검사"). 일지의 이 인계 절은 커밋하지 않았다. 일지 docs/journal/2026-10-24-05-site-file-feeds-widget-build.md
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

- 제목: `feature/04-site-file-feeds-widget-build (인계함)`. 멈출 백그라운드 작업은 없었다. 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-23T18:40:16Z

## 이어 받은 세션(PR 연 뒤)

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/web-widget/issues/04-site-file-feeds-widget-build.md

(지시문은 위 "인계(PR 연 뒤)"의 것과 같다. 제목을 `feature/04-site-file-feeds-widget-build` 로 바꾸고 워크트리에 `EnterWorktree(path)` 로 들어갔다. origin/main 은 7496a830 그대로라 합칠 것이 없었다.)

### 봇 회차 1

- `@coderabbitai review` 코멘트를 남기고(6372203760) `tools/wait_ci.py 379` 를 백그라운드로 띄웠다. 끝 줄은 `끝: 실패 python, verify` 였다. CodeRabbit 은 `Review completed`, claude-review·e2e·web·visual·ticket 은 초록이었다.
- CI `python`(실행 40004989726): 3 failed, 5509 passed. 실패는 셋이다.
  - `test_브라우저가_싣는_표기의_허용_출처는_사이트_파일을_지난다[http://[::ffff:102:304]]`(`assert 1 == 0`)와 `test_브라우저가_싣지_않는_표기의_허용_출처는_serve_를_세우지_않고_그_항목과_규칙을_말한다[http://[::ffff:1.2.3.4]]`(`assert 0 == 1`). CI 의 파이썬은 `cpython-3.12.15`(잡 로그의 `Installed Python 3.12.15`)이고 이 PC 는 3.12.10 이다. 이 PC 에서 `IPv6Address('::ffff:1.2.3.4').compressed` 는 `::ffff:102:304` 였다(손으로 봤다). CI 의 두 실패는 3.12.15 가 그 주소를 `::ffff:1.2.3.4` 로 적을 때 나는 결과와 맞는다. PR 직전 리뷰에서 3.13 의 일로 보류한 위험이 3.12 의 패치 판에서 먼저 났다.
  - `tests/tools/test_proc_command_line.py::test_살아_있는_프로세스의_명령_줄을_낱말로_읽는다`(`assert None is not None`). 이 브랜치가 건드리지 않은 시험이고 대기열 456 이다. 일지 2026-10-24-03 과 같은 판단으로 잡을 다시 돌리지 않는다. 반영 푸시의 CI 가 이 시험 하나로만 빨가면 사용자에게 묻는다.
- CodeRabbit 첫 회차: 지적 없음(`No actionable comments`).
- claude-review 첫 회차(코멘트 6372157187): Critical·Major 없음. 판정은 지적마다 했다.
  - [Minor, 뒤로 넘긴다] `main.py` 의 출처 표기 판정(약 120줄)을 조합 층 밖의 모듈로 옮기라. 사이트 파일 읽기와 검증 전체(pydantic 모델, `_sites_of`, `_keys_of`, `_key_id_problems`)가 `main.py` 에 있고 출처 표기 판정은 그 검증의 하나다. 판정만 옮기면 사이트 파일 검증이 두 모듈로 갈리고, 읽기 전체를 옮기는 일은 변이 표 `site_file_mutations.toml` 의 `file` 과 독스트링을 함께 옮기는 따로의 리팩터다. 일지 "다음"에 적는다.
  - [Minor, 뒤로 넘긴다] `site-file.ts`(532줄)의 출처 표기 부분을 `origin-rule.ts` 같은 파일로 빼라. 위와 같은 일이라 함께 넘긴다. 한쪽만 옮기면 두 언어의 배치가 갈린다.
  - [Minor, 고쳤다] 파이썬의 규칙 이름이 `str` 이라 오타가 타입에서 잡히지 않는다. `type _OriginRule = Literal[...]` 로 닫고 `_ORIGIN_RULES`, `_origin_rule`, `_host_rule` 에 붙였다(이 저장소의 별칭은 `type` 문을 쓴다, `admin/http.py` 의 `PluginRow` 등).
  - [Nit, 보류] 규칙 문구 열셋이 두 언어에 이중으로 있고 픽스처는 이름만 단언한다. 문구는 판정에 들지 않아 두 언어의 결과(받느냐 막느냐, 어느 규칙이냐)를 바꾸지 않고, 픽스처의 계약은 이름·차례·사례다(픽스처 README 머리). 이번에 고친 `ipv6` 문구는 두 언어에 같은 글로 넣었다.
  - 넷의 판정은 푸시 뒤 PR 코멘트로 남긴다(아직 남기지 않았다).

### 반영(커밋하지 않았다)

- 결정: 서버는 `ipaddress.IPv6Address` 로 주소를 읽기만 하고 글은 `packed` 에서 직접 짓는다(`_serialized_ipv6`). Node 의 `compressedIpv6` 와 같은 차례다(0 이 둘 이상 이어진 가장 긴 열 가운데 앞의 것을 `::`). 근거: RFC 5952 는 5절에서 IPv4 를 품은 주소의 점 표기를 권하고, WHATWG URL 의 IPv6 serializer 는 늘 소문자 16진수로 적는다(두 원문 모두 WebFetch 의 웹 요약으로 봤다, `https://www.rfc-editor.org/rfc/rfc5952.txt`, `https://url.spec.whatwg.org/`). 브라우저 쪽은 Node 의 시험이 지나는 사례 `[::ffff:102:304]` 를 `new URL(v).origin` 에 넣어 같은 값인지 이미 본다.
- 시험을 먼저 썼다. `tests/test_main.py` 의 `dotted_ipv4_mapped` 픽스처가 `IPv6Address.__str__` 을 바꿔 점으로 적는 판을 흉내 내고(`compressed` 는 `str` 을 부른다), 시험 둘이 픽스처의 대괄호 사례로 판정이 그 글 꼴에 기대지 않는지 본다. 고치기 전 이 PC 에서 CI 와 같은 두 사례가 빨갰다(2 failed, 10 passed). 고친 뒤 새 시험과 표기 픽스처 시험이 90 passed 였다.
- 고친 파일: `src/agent_os/main.py`(판정, `Literal`, `ipv6` 문구), `web/apps/widget/tools/site-file.ts`(`ipv6` 문구와 독스트링 셋. 파이썬의 `compressed` 를 기준으로 든 문장을 뺐다), `tests/fixtures/site_file/README.md`(`ipv6` 행과 RFC 5952 와 갈리는 갈래의 문단), 티켓 04 의 규칙 줄과 `spec.md` 187행(살아 있는 문서다. "파이썬 `compressed` 와 같다"가 3.12.15 에서 틀린 사실이 되어 고쳤다), 변이 표(원문이 바뀐 하나와 새 셋 10~13, 40 → 43), 프로브 README 행.
- 새로 쓴 사실 문장(PR 직전 리뷰에 밀 주장으로 넘길 것): ① `_serialized_ipv6` 독스트링의 "3.12.15 는 `::ffff:1.2.3.4`, 3.12.10 은 `::ffff:102:304`" 와 "앞의 것은 RFC 5952 5절의 권고이고 브라우저는 그렇게 적지 않는다", ② 픽스처 README 의 "RFC 5952 는 4.2.3절에서 가장 긴 0의 열(같으면 앞의 것)을 줄이라고 하고, 5절에서 IPv4를 품은 주소는 끝 32비트를 점으로 적으라고 권한다", ③ `dotted_ipv4_mapped` 의 "`compressed` 는 `str` 을 부르므로". 3.12.15 의 표기는 CI 의 실패 모양에서 끌어낸 것이고 3.12.15 를 띄워 직접 보지는 않았다.
- 다시 돌린 것: 새 시험과 표기 시험 90 passed, `uv run pyright src/agent_os/main.py tests/test_main.py` 0 errors, 두 파일의 `ruff check` 통과, `tools/mutate.py --check` 로 표 둘(43, 34) 모두 원문이 한 번씩 있다, `tools/mutate.py … site_file_mutations.toml 10 11 12 13` 이 `변이 4 모두 기대대로`. 돌리지 않은 것: `run_checks` 전체, `site-file.ts` 의 Vitest·Prettier(문구와 주석만 바꿨다).
- 워크트리 가드가 heredoc 으로 스크래치에 스크립트를 쓰고 바로 돌리는 한 명령을 거부했다(`too complex to verify`). Edit 도구로 고쳤다.
- PR 본문에 고칠 자리(푸시 전 `gh pr edit`): "남긴 위험"의 "파이썬 판을 올리면 IPv6 판정을 다시 본다" 항목(이제 고쳤다), 체크리스트의 PR 직전 리뷰 줄에 있는 "보류: 파이썬 3.13 의 IPv6 표기", "확인 방법"의 변이 40, "리뷰어 참고"의 "Node 쪽은 RFC 5952 를 손으로 지었다".

### 일지 "다음"에 넘길 것

- 앞 인계가 넘긴 것: 반영 전 `run_checks` 에서 `test_hook_edit_during_commit` 이 다른 세션의 git 프로세스와 겹쳐 한 번 빨갰던 일(위 "검사").
- 봇 회차 1에서 뒤로 넘긴 것: 출처 표기 판정을 두 언어 모두 사이트 파일 모듈 밖으로 옮길지(위 claude-review Minor 둘).

이 세션의 지금 제목은 `feature/04-site-file-feeds-widget-build` 이다.

## 인계(셀프 리뷰 직전)

컨텍스트가 문턱을 넘은 채 `셀프 리뷰 직전` 경계에 와서 넘긴다. 인계하지 않는 때 다섯에 들지 않았다. `code-review` 를 부르는 데 성공했고, 요청 범위가 병합까지이고, 이어받은 상태가 `인계: PR 연 뒤` 라 이번 경계와 다르고, `인계 못함` 줄이 없고, `get_session` 의 `self` 에 `parentSessionId` 가 없었다. 이 절은 커밋하지 않았다.

```
다음 작업: .scratch/web-widget/issues/04-site-file-feeds-widget-build.md. 서버와 위젯 빌드가 같은 사이트 파일에서 합친 허용 출처와 가장 작은 요청 글자 수 상한을 읽고, 허용 출처의 표기를 파이썬과 Node가 같은 픽스처로 판정한다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/04-site-file-feeds-widget-build.md
브랜치: feature/04-site-file-feeds-widget-build
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-24-05-site-file-feeds-widget-build.md 의 "이어 받은 세션(PR 연 뒤)"부터 끝까지. 막힌 티켓(05~11)은 .scratch/plan.md 의 web-widget 행
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review 200b77d6)부터 한다. docs/journal/2026-10-24-05-site-file-feeds-widget-build.md. 그 변경은 PR #379 봇 회차 1의 반영분이다(CI 파이썬 3.12.15에서 빨개진 IPv6 판정을 서버가 글을 직접 짓게 고침, claude-review Minor 하나 반영). 리뷰를 반영한 뒤 단계를 닫는 세션으로 회고와 일지 "다음"을 마쳐 같은 커밋에 싣고, 푸시 전에 gh pr edit로 PR 본문을 고치고(고칠 자리는 일지), 푸시 뒤 claude-review 첫 회차 넷의 판정을 PR 코멘트로 남긴다. 반영 푸시의 CI가 test_proc_command_line(대기열 456) 하나로만 빨가면 사용자에게 묻는다. 일지의 이 세션 절은 커밋하지 않았다
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

- 제목: `feature/04-site-file-feeds-widget-build (인계함)`. 멈출 백그라운드 작업은 없었다(`wait_ci` 는 끝났다). 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-23T19:07:20Z

## 이어 받은 세션(셀프 리뷰 직전)

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/web-widget/issues/04-site-file-feeds-widget-build.md

(지시문은 위 "인계(셀프 리뷰 직전)"의 것과 같다. 제목을 `feature/04-site-file-feeds-widget-build` 로 바꾸고 워크트리에 `EnterWorktree(path)` 로 들어갔다. origin/main 은 7496a830 그대로라 합칠 것이 없었다.)

### 셀프 리뷰(봇 회차 1 반영분)

`/code-review 200b77d6`. 범위: base 200b77d6, 파일 9, 커밋 0, 미추적 0(모두 커밋하지 않은 작업). 표준 축은 sonnet·high, 명세 축은 이 세션의 모델로 나란히 돌렸다. 두 축 모두 Critical·Major 가 없다.

- [Minor, 고침] 두 축이 함께 짚었다. 3.12.15 의 표기를 CI 실패의 모양에서 끌어냈는데 `_serialized_ipv6` 독스트링, 픽스처 README, `dotted_ipv4_mapped` 독스트링에 관측처럼 적었다. 명세 축이 `gh api` 로 CPython v3.12.15 의 `Lib/ipaddress.py` 를 받아 읽었고, 이 세션도 v3.12.15 와 v3.12.10 의 같은 파일을 `gh api repos/python/cpython/contents/Lib/ipaddress.py?ref=<태그>` 로 받아 `_ipv4_mapped_ipv6_to_str` 를 셌다(v3.12.15 에 둘, v3.12.10 에 0). v3.12.15 의 `IPv6Address.__str__` 은 `ipv4_mapped` 가 있으면 그 함수로 `::ffff:1.2.3.4` 꼴을 짓는다. 그래서 세 자리의 근거를 두 판의 원문 읽기로 바꿨다. 명세 축이 함께 짚은 범위도 좁혔다. 점으로 적는 것은 IPv4 매핑 주소(`::ffff:0:0/96`)뿐이고 `::1.2.3.4` 는 16진수로 적는다. 티켓 04 의 규칙 줄과 `spec.md` 187행의 "그 주소를 점으로 적어"도 "IPv4 매핑 주소(`::ffff:0:0/96`)를 점으로 적어"로 고쳤다.
- [Nit, 고침] `_serialized_ipv6` 독스트링이 RFC 5952 와 WHATWG URL 을 근거의 종류 없이 들었다(표준 축). "두 원문의 웹 요약을 봤다, 픽스처 README 의 `ipv6`" 를 붙였다. 픽스처 README 의 5절 요약도 조건("잘 알려진 접두사로 그것을 알 수 있을 때")을 더했다.
- [Nit, 고침] 새 `ipv6` 문구에 "앞의 0 없이"가 빠져 `[2001:db8::01]` 이 막혀도 문구가 까닭을 말하지 않는다(명세 축). 두 언어의 문구에 "앞의 0 이 없는"을 같은 글로 넣었다. 변이 표와 시험은 문구가 아니라 규칙 이름을 본다(grep 으로 봤다).
- [Nit, 고침] 티켓 04 의 "`http://[::ffff:1.2.3.4]`(Node와 파이썬 3.12.10이 모두 `[::ffff:102:304]`로 바꾼다)"는 이제 기준이 아닌 파이썬을 막는 까닭으로 든다(명세 축). "(Node의 `new URL(v).origin`이 `[::ffff:102:304]`로 바꾼다)"로 고쳤다. `spec.md` 의 같은 관측 문장은 판과 날짜가 붙은 관측 기록이고 바로 앞 괄호가 파이썬을 기준에서 뺀다고 적어 두었다.
- [Nit, 고침] TS 의 `compressedIpv6` 가 파이썬의 `_serialized_ipv6` 와 이름이 갈린다(표준 축 Mysterious Name). `serializedIpv6` 로 바꿨다. 변이 표는 그 이름을 겨누지 않는다(grep 으로 봤다).
- [Nit, 남김] `dict[_OriginRule, str]` 은 오타는 막아도 빠진 키는 pyright 가 잡지 않는다(두 축). 픽스처의 막히는 사례가 규칙 열셋을 모두 지나 문구를 찾으므로 빠진 키는 시험에서 `KeyError` 로 빨개진다. 타입으로 막으려면 dict 를 다른 꼴로 바꿔야 해 두 언어의 대칭이 깨진다.
- [Nit, 남김] `_serialized_ipv6` 한 함수에 바이트를 그룹으로 읽기, 가장 긴 0 열 찾기, 글 짓기가 섞였다(표준 축). Node 의 `serializedIpv6` 와 같은 모양이라 두 언어를 나란히 읽기 쉽다. 출처 표기 판정을 모듈 밖으로 옮기는 일(봇 회차 1에서 뒤로 넘긴 것)에서 함께 본다.
- 확인해서 맞은 것: 두 축이 파이썬 `_origin_rule` 과 Node `originRule` 에 픽스처 전부와 경계 입력(모두 0, 0 하나, 같은 길이의 0 열 둘, 끝의 0 열, 점 표기 셋 등)을 대어 어긋난 것이 0 이었다. 명세 축은 보통 판과 점 표기 흉내 판 둘 다로 돌렸다. `compressed` 가 `str(self)` 인 것은 이 세션이 3.12.10 에서 `inspect.getsource` 로, 명세 축이 v3.12.15 원문으로 봤다. 변이 표의 변이는 43 이고 10~13 이 겨누는 시험 id 가 collect 에 있다. 옛 표현의 잔존은 살아 있는 문서에 없다.
- 반영 뒤 다시 돌린 것: 표기 시험 91 passed, `uv run ruff check`·`ruff format --check`·`pyright`(두 파일) 통과, `pnpm -C web exec vitest run --project node apps/widget/tools/site-file.test.ts apps/widget/next.config.test.ts` 190 passed, Prettier 통과, `tools/mutate.py --check` 로 표 둘(43, 34) 모두 원문이 한 번씩 있다. `main.py` 를 건드려 `uv run --env-file ../../../.env pytest -m llm` 도 돌렸다: 7 passed(282.14초), LLM 토큰 합계 51,554(입력 50,473, 출력 1,081), 트레이스 10개, 모델 호출 21건. 트레이스를 남기지 않은 LLM 시험 1개는 세지 못했다. 손으로 치는 다섯은 커밋의 pre-commit 으로 갈음한다.
- 이 반영으로 새로 쓴 사실 문장: ① `_serialized_ipv6` 독스트링의 "CPython v3.12.15 의 `IPv6Address.__str__` 은 그 주소를 `_ipv4_mapped_ipv6_to_str` 로 `::ffff:1.2.3.4` 처럼 점으로 적고, v3.12.10 에는 그 갈래가 없어 `::ffff:102:304` 로 적는다", ② 픽스처 README 의 "그래서 `compressed`와 견주던 판정이 CI의 3.12.15에서는 `[::ffff:102:304]`를 막고 `[::ffff:1.2.3.4]`를 지나보냈고". PR 이 이미 열려 PR 직전 리뷰는 돌지 않는다. 이 커밋을 푸시하면 claude-review 둘째 회차가 본다.

## 회고

이 단계를 닫는 세션(셀프 리뷰 직전에 이어 받은 세션)이 이 일지 전체와 이 세션을 보고 돌렸다. 후보 열, 승인 다섯, 넘김 하나, 기각 넷이다. 이 세션에서 반영한 것은 없고, 승인한 것은 모두 대기열에 두었다.

1. **넘김 → 대기열 457(1회차).** CI 의 `uv python install 3.12` 가 가장 새 3.12 패치(3.12.15)를 깔고 이 PC 는 3.12.10 이라, 표준 라이브러리 `ipaddress` 가 IPv4 매핑 주소를 적는 꼴이 갈려 이 PC 에서 초록인 시험이 PR CI 에서만 빨갰다(봇 회차 1). 처방(CI 와 로컬의 판을 정확한 패치로 고정)은 `docs/constitution/tech.md` 의 스택 결정이라 ADR 이 들어 넘겼다.
   > 사용자: (선택) "회차만 센다 (권장)" — "지금은 아무것도 바꾸지 않고, 대기열에 1회차로 적어 둡니다. 같은 일이 세 번째 나면 판 고정을 ADR로 올립니다."
2. **승인, 더하는 것 → 대기열 458(1회차).** 사건: PR 직전 `bug-perf-review` 가 낸 판에 따른 상류 동작 주장(리뷰어는 3.13 으로 기억했다)을 이 PC 에 그 판이 없다며 보류했는데, 같은 변화가 CI 의 3.12.15 에서 났다. 그 판의 원문은 `gh api` 한 번으로 읽혔다(위 셀프 리뷰). 층: 보류를 다루는 자리(`docs/constitution/operations.md` 리뷰 파이프라인 2)의 문장이다. 판에 따른 동작의 갈래는 검사로 잡을 수 없다. 첫 회차라 반영하지 않는다.
3. **승인, 회차로 세는 것 → 대기열 445에 10회차(421의).** 사건: 3.12.15 의 표기를 CI 실패의 모양에서 끌어내고 코드 독스트링·시험 독스트링·픽스처 README 에 본 것처럼 적어 셀프 리뷰 두 축이 Minor 로 잡았다(위 셀프 리뷰). `CLAUDE.md` 가 근거 문장에 따르라는 `docs/agents/issue-tracker.md` 프로브와 근거 절을 어겼다. 445 의 처방은 일지를 쓸 때의 계기 훅인데 이번 자리는 일지 밖이었다. 반영하는 chore 가 범위를 고를 때 이 자리를 함께 본다.
4. **승인, 회차로 세는 것 → 대기열 420에 5회차.** 사건: 파이썬의 `compressed` 를 기준에서 뺀 뒤에도 티켓 04 의 막히는 사례 괄호가 "Node와 파이썬 3.12.10이 모두"로 파이썬을 막는 까닭으로 들어 셀프 리뷰 명세 축이 Nit 로 잡았다. `CLAUDE.md` 작업 규약 4(옛 표현의 잔존을 grep 해 0 인지 본다)를 어겼다.
5. **승인, 고침 → 대기열 456에 3회차.** 사건: `tests/tools/test_proc_command_line.py` 의 시험이 PR #379 의 CI(실행 40004989726)에서 다시 빨갰다(봇 회차 1). 이 브랜치가 건드리지 않은 시험이다. 3회차라 chore 배치의 조건이 찼다.
6. **승인, 고침 → 대기열 459(1회차).** 사건: 반영 전 `run_checks` 에서 `tests/tools/test_hook_edit_during_commit.py` 의 실행 파일 경로 단언이 한 번 빨갰다(위 "검사"). 그 단언은 그 시험이 세운 커밋이 아니라 그때 도는 모든 커밋의 프로세스에 걸려, 다른 세션의 `git.exe` 가 상대 경로로 떠 있으면 빨개진다(코드를 읽어 본 것이고 재현하지 않았다). 고침이라 사건 하나로 반영할 수 있지만, 봇 회차 중인 기능 PR 의 범위를 넓히지 않으려 이 PR 에 싣지 않았다.
7. **기각.** 워크트리 가드가 거부한 명령 둘(앞 세션의 스크래치 스크립트 heredoc, 이 세션의 `for`·`sed` 루프)은 앱 가드가 그 자리에서 막았고 `CLAUDE.md` 환경 함정에 이미 있다.
8. **기각.** 파이프 뒤의 판정 명령, WebFetch 웹 요약, 큰 Read 결과는 훅이 그 자리에서 알렸다.
9. **기각.** 새 `ipv6` 문구가 "앞의 0 없이"를 빠뜨린 것은 리뷰가 잡도록 둔 기준이라 리뷰가 제 몫을 했고, 문구의 뜻을 검사로 옮길 수 없다.
10. **기각.** 변이 시험 하나가 1분을 넘긴 회차가 셋이었지만(위 "변이") 느린 까닭을 가르지 않아 처방의 층을 고를 근거가 없다.

만료: `uv run python tools/queue_open_rows.py` 와 `git fetch origin` 뒤 `--ref origin/main` 모두 만료할 행이 없었다.

## 다음

- 04 가 병합되면 05(Blocked by 01·04)가 열린다. 01·02·03 은 병합됐다. 06 은 02 와 05 를, 07·10·11 은 06 을, 08 은 07 을, 09 는 08 을 기다린다(`.scratch/plan.md` 의 web-widget 행).
- 봇 회차 1에서 뒤로 넘긴 것: 출처 표기 판정(파이썬 `_origin_rule`·`_serialized_ipv6` 등, Node `originRule`·`serializedIpv6` 등)을 두 언어 모두 사이트 파일 모듈 밖으로 옮길지(claude-review Minor 둘). 한쪽만 옮기면 두 언어의 배치가 갈리고, 변이 표 `site_file_mutations.toml` 의 `file` 과 독스트링이 함께 옮겨진다. 따로의 리팩터로 한다. 봇 회차 2의 claude-review 가 같은 리팩터에서 함께 볼 것 둘을 더 냈다. ① 규칙 문구 열셋이 `main.py` 의 `_ORIGIN_RULES`, `site-file.ts` 의 `ORIGIN_RULES`, 픽스처 README 세 곳에 손으로 복제되어 한쪽만 고쳐도 아무 검사가 빨개지지 않는다(Minor. 문구를 픽스처 JSON 에 두고 두 언어가 읽거나, 두 언어의 문구를 견주는 시험을 둔다). ② TS `splitHost` 가 `startsWith("[")` 를 두 번 평가해 파이썬 `_split_host` 와 분기 모양이 다르다(Nit).
- 반영 전 `run_checks` 에서 `test_hook_edit_during_commit` 이 한 번 빨갰던 일은 대기열 459, CI 의 `test_proc_command_line` 은 대기열 456(3회차)이다.
- 이 PR 은 워크트리에서 병합한다. 주 체크아웃은 당기지 않는다.

### 커밋과 PR 본문(셀프 리뷰 직전에 이어 받은 세션)

- 셀프 리뷰 반영, 회고, "다음"을 d2d6b993 으로 커밋했다(아직 푸시하지 않았다). pre-commit: ruff 둘, `run_checks` 의 검사 열(web-verify 234.8초, pytest 312.5초), 마크다운 표, 줄 구분 문자, 변이 표, 커밋 메시지가 Passed. 카나리아 명세와 헌법 판은 대상 파일이 없어 Skipped. 인용 대조는 경고 7건을 냈다. 일곱 모두 이 일지가 고치기 전의 옛 문장(봇 회차 1 절의 독스트링·PR 본문 문구, 셀프 리뷰 절의 티켓 괄호)을 인용한 것이라 원문이 이제 저장소에 없다.
- 푸시 전에 `gh pr edit 379 --body-file` 로 PR 본문을 고쳤다. "왜 이렇게 했나"에 IPv6 직렬화와 `Literal`, 원문 줄에 봇 회차 1·셀프 리뷰 절과 대기열 457~459·420·445·456, "남긴 위험"의 IPv6 항목을 CI 와 이 PC 의 패치 판 차이(대기열 457)로, 체크리스트의 보류 줄·셀프 리뷰 줄·`-m llm` 줄, "확인 방법"의 변이 43, "리뷰어 참고"의 IPv6 글 짓기, 변경된 영역의 `_serialized_ipv6`.

## 인계(커밋 뒤)

컨텍스트가 문턱을 넘은 채(342,908 토큰) `커밋 뒤` 경계에 와서 넘긴다. 인계하지 않는 때 다섯에 들지 않았다. 커밋이 pre-commit 을 지났고, 요청 범위가 병합까지이고, 이어받은 상태가 `인계: 셀프 리뷰 직전` 이라 이번 경계와 다르고, `인계 못함` 줄이 없고, `get_session` 의 `self` 에 `parentSessionId` 가 없었다. 이 세션의 지금 제목은 `feature/04-site-file-feeds-widget-build` 이다. 이 절과 위 "커밋과 PR 본문" 절은 커밋하지 않았다.

```
다음 작업: .scratch/web-widget/issues/04-site-file-feeds-widget-build.md. 서버와 위젯 빌드가 같은 사이트 파일에서 합친 허용 출처와 가장 작은 요청 글자 수 상한을 읽고, 허용 출처의 표기를 파이썬과 Node가 같은 픽스처로 판정한다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/04-site-file-feeds-widget-build.md
브랜치: feature/04-site-file-feeds-widget-build
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-24-05-site-file-feeds-widget-build.md 의 "봇 회차 1"부터 끝까지. 막힌 티켓(05~11)은 .scratch/plan.md 의 web-widget 행
이어받을 상태: 인계: 커밋 뒤. PR #379 봇 회차 1의 반영(IPv6 직렬화, Literal), 그 셀프 리뷰와 반영, 회고와 일지 "다음"을 d2d6b993 으로 커밋했고 아직 푸시하지 않았다. PR 본문은 이미 gh pr edit 로 넓힌 범위에 맞췄다. 남은 단계는 푸시와 next-session 순서 1의 2(봇 회차)부터다: @coderabbitai review 코멘트와 tools/wait_ci.py 대기, claude-review 첫 회차 넷의 판정(일지 "봇 회차 1"의 넷)을 PR 코멘트로 남기기, 둘째 회차부터는 Critical·Major만 고치고 나머지는 보류 이유를 PR 코멘트로, 병합. 반영 푸시의 CI가 test_proc_command_line(대기열 456) 하나로만 빨가면 사용자에게 묻는다. 일지의 "커밋과 PR 본문" 절과 이 인계 절은 커밋하지 않았다. 다음에 커밋할 일이 생기면 함께 싣는다. docs/journal/2026-10-24-05-site-file-feeds-widget-build.md
확인할 선행 조건: 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

- 제목: `feature/04-site-file-feeds-widget-build (인계함)`. 멈출 백그라운드 작업은 없었다(`-m llm` 과 커밋은 끝났다). 워크트리 잠금은 이미 풀려 있었다(`is not locked`).

open-session을 부른다 2026-10-24T04:15:37Z

## 이어 받은 세션(커밋 뒤에 넘겨받음)

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/web-widget/issues/04-site-file-feeds-widget-build.md

(지시문은 위 "인계(커밋 뒤)"의 것과 같다. 제목을 `feature/04-site-file-feeds-widget-build` 로 바꾸고 워크트리에 `EnterWorktree(path)` 로 들어갔다. origin/main 은 7496a830 그대로라 합칠 것이 없었다.)

### 봇 회차 2

- d2d6b993 을 푸시하고 `@coderabbitai review` 코멘트를 남겼다(6379774715). 상태를 한 번 읽으니 ticket 만 끝났고 나머지는 pending 이라 `tools/wait_ci.py 379` 를 백그라운드로 띄웠다.
- claude-review 첫 회차 넷의 판정(위 "봇 회차 1")을 PR 코멘트로 남겼다(6379779913).
- `wait_ci` 의 끝 줄은 `끝: 모두 통과. CodeRabbit: Review rate limited` 였다. python 도 초록이라 대기열 456 의 `test_proc_command_line` 은 이번에 빨개지지 않았다. CodeRabbit 은 한도에 걸려 리뷰가 없어 회차로 세지 않는다.
- claude-review 둘째 회차(코멘트 6379781461, 헤드 d2d6b993): Critical·Major 없음. 둘째 회차라 고치지 않고 셋 모두 보류 이유를 PR 코멘트로 남겼다(6379861959).
  - [Minor, 뒤로 넘긴다] `main.py` 에 출처 표기 판정이 들어가 바뀌는 이유가 둘로 늘었다. 첫 회차의 Minor 와 같은 일이다.
  - [Minor, 뒤로 넘긴다] 규칙 문구 열셋이 세 곳에 손으로 복제되어 한쪽만 고쳐도 검사가 빨개지지 않는다. 판정은 갈라지지 않고 진단 글만 갈라질 수 있다. 규칙 표를 새 모듈로 옮기는 리팩터에서 함께 정한다.
  - [Nit, 뒤로 넘긴다] TS `splitHost` 가 `startsWith("[")` 를 두 번 평가해 파이썬과 분기 모양이 다르다(`site-file.ts` 420행에서 봤다). 결과는 같다.
  - 셋 모두 일지 "다음" 의 출처 표기 리팩터 항목에 더했다. 고친 것이 없는 회차라 이 일지만 실은 커밋을 푸시한다(next-session 순서 1의 2 "뒤로 넘긴 일"). 그 푸시로 도는 셋째 회차에서 보류하는 것은 일지에 다시 적지 않고 PR 코멘트와 다음 지시문의 "이어받을 상태"에 적는다.
