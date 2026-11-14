# portal-login 프로브

로그인 사이트의 OIDC 로그인을 설계하며 근거로 들 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다. 이 폴더의 코드는 프로브의 것이고 제품 코드가 아니다.

## 돌리는 법

저장소 루트에서 한 줄씩 돈다(Windows, Git Bash). node 24와 pnpm 11.24.0이 있어야 하고, `tls` 묶음은 `openssl`이 PATH에 있어야 한다. 패키지는 프로브 폴더 안의 독립된 `package.json`으로 npm 공식 레지스트리에서 설치하고 `web/`의 것은 건드리지 않는다. `node_modules/`는 저장소 `.gitignore`가, 산출물 `out/`은 프로브의 `.gitignore`가 무시한다. `registry.mjs`만 바깥(`https://registry.npmjs.org/<패키지 이름>` 읽기 다섯)에 닿는다.

```sh
pnpm -C .scratch/portal-login/probes/oidc_client install --frozen-lockfile
node .scratch/portal-login/probes/oidc_client/probe/typecheck.mjs
node .scratch/portal-login/probes/oidc_client/probe/lint.mjs
node .scratch/portal-login/probes/oidc_client/probe/flow.mjs
node .scratch/portal-login/probes/oidc_client/probe/report.mjs --reasons
node .scratch/portal-login/probes/oidc_client/probe/deps.mjs
node .scratch/portal-login/probes/oidc_client/probe/registry.mjs
node .scratch/portal-login/probes/oidc_client/probe/loc.mjs
```

`flow.mjs`는 `--group <묶음>`으로 묶음 하나만 돌 수 있다(`good`, `fault`, `callback`, `provider`, `insecure`, `transport`, `tls`. 여러 번 줄 수 있다. 모르는 이름이면 돌지 않고 종료 코드 2로 끝난다). `report.mjs`는 재지 않고 `out/flow/summary.json`을 표로 찍기만 한다. 스크립트마다 측정이 아닌 회차가 하나라도 있으면 종료 코드 1이고, 무엇을 표지로 보는지는 각 파일 머리의 주석이 원천이다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `oidc_client/` | OIDC 클라이언트 후보 셋(가 `openid-client`, 나 `oauth4webapi`+`jose`, 다 `node:crypto`와 `node:http`·`node:https`의 `request`로 직접 구현)과 가짜 로그인 서버 후보 둘(ㄱ `node:http`로 직접 만든 것, ㄴ `oidc-provider`)을 위젯 미리보기 페이지 앱과 같은 배치(`apps/portal/server/oidc/`, `apps/portal/testing/`)에 두고 여섯 가지를 본다. `probe/typecheck.mjs`: `web/apps/portal/tsconfig.json`의 복사로 `tsc --noEmit`(복사가 원본과 같은지, tsc가 본 파일 목록, 심은 오류 여섯의 양성 대조). `probe/lint.mjs`: `web/eslint.config.mjs`를 글자 그대로 옮긴 무대에서 ESLint(심은 위반 여섯, 페이지 스크립트 자리의 예외, `node_modules` 안 파일이 범위 밖인지). `probe/flow.mjs`: node가 `.ts`를 빌드 없이 돌려 흐름 한 바퀴(설정 문서, PKCE·state·nonce가 든 인가 요청, 돌아온 요청 검증, 토큰 교환, ID 토큰 검증, `sub`)를 79회차. ID 토큰 고장 여덟, 돌아온 요청 고장 둘, `http` 발급자의 허용과 거부, `customFetch`로 HTTP 바꿔 끼우기, 사설 인증 기관과 `NODE_EXTRA_CA_CERTS`. `probe/deps.mjs`: 전이 의존성까지의 패키지 수·설치 크기·라이선스. `probe/registry.mjs`: 설치한 판과 최신 판이 나온 날짜. `probe/loc.mjs`: 파일마다 줄 수 | ADR 0059의 결정 "로그인 방식"(서명 검사, `http` 발급자 거부, 린트의 `no-deprecated`)과 "시험"(`tls` 묶음), Considered Options(후보 셋의 줄 수와 패키지 수, `oidc-provider`), Consequences "의존성". deploy-package 기능 계획의 `NODE_EXTRA_CA_CERTS` 문장. 일지 2026-11-12-1937의 "측정" 절 | 위 명령. `openid-client`·`oauth4webapi`·`jose`·`oidc-provider`의 판을 올릴 때, `web/eslint.config.mjs`나 `web/apps/portal/tsconfig.json`을 고칠 때, node의 major를 올릴 때. 전체 시간은 재지 않았다 | node 24.19.0, pnpm 11.24.0, typescript 5.9.3, eslint 10.11.0, typescript-eslint 8.70.1, eslint-plugin-boundaries 7.2.0, @types/node 24.19.0, openid-client 6.8.9, oauth4webapi 3.8.8, jose 6.2.17, oidc-provider 9.13.3, @types/oidc-provider 9.13.1, OpenSSL 1.1.1k. Windows 10(이 PC)만. 2026-11-12 |

## 결과

2026-11-12에 여러 번 돌렸고, 아래 값은 그날 마지막 전체 실행의 것이다(스크립트 여섯 모두 종료 코드 0, 측정이 아닌 회차 0). 근거의 종류는 문장마다 적는다. 설계 추천은 여기 두지 않는다.

### 결과를 본 뒤 바꾼 기준

- `tls` 묶음의 첫 실행은 인증 기관을 준 회차까지 모두 거부였다. 까닭은 프로브가 만든 인증 기관 인증서에 `basicConstraints`가 두 번 든 것이었다(openssl 기본 설정과 프로브의 `-addext`가 겹쳤다). 인증서를 프로브 자신의 설정 파일(`ca.cnf`, `server.cnf`, `server.ext`)로만 만들게 고치고, `openssl verify -CAfile ca.crt server.crt`가 `server.crt: OK`를 내지 않으면 그 묶음의 회차를 측정이 아닌 것으로 세는 조건을 더했다. 고친 뒤 인증 기관을 준 회차가 통과했다.
- `typecheck.mjs`의 양성 대조 가운데 jose의 줄은 첫 판이 `decodeJwt`를 써서 걸리지 않았다(제네릭 반환이 기대 타입으로 추론돼 지나간다). `base64url.encode`로 바꾼 뒤 걸렸다.
- 이 세션의 환경에 `NODE_USE_SYSTEM_CA=1`이 있었다(`node --help`의 "(currently set)"과 `printenv`로 손으로 봤다). 앞선 실행은 그것을 물려받았다. `flow.mjs`가 자식 환경에서 그 변수와 `NODE_EXTRA_CA_CERTS`·`NODE_TLS_REJECT_UNAUTHORIZED`·`NODE_OPTIONS`를 지우게 고치고, 회차의 JSON에 `extraCaGiven`·`systemCaGiven`을 실어 뜻한 환경이 아니면 측정이 아닌 것으로 세게 했다. 고친 뒤 전체를 다시 돌렸고 회차마다의 결과는 앞선 실행과 같았다.
- 2026-11-13에 PR 직전 리뷰의 지적을 받아 `oidc_client/probe/flow.mjs`의 판정 둘을 좁혔다. 재는 것과 재는 방법은 그대로다. `fault` 묶음은 거부를 그대로 그 고장의 거부로 셌는데, 회차가 남긴 오류(원인 사슬 포함)에 그 고장의 문구가 있어야 세게 했다(`FAULT_REASONS`. 오류 코드는 여러 고장이 함께 써서 문구로 댄다. 문구는 `oauth4webapi` 3.8.8, `jose` 6.2.17, `hand.ts`의 것이다). `insecure` 묶음은 거부면 서버가 받은 설정 문서 요청이 0이어야 세게 했다(머리 주석은 처음부터 그렇게 적었는데 코드가 보지 않았다). 고친 뒤 전체를 다시 돌렸고 79회차 모두 측정이며 회차마다의 결과는 아래 표와 같았다(판정을 고친 서브에이전트가 돌렸다고 보고한 것이다). 그 뒤 본 세션이 `alg` 고장 둘의 문구를 `"alg" header parameter`에서 `unexpected JWT "alg" header parameter`로 좁혔다. `oauth4webapi` 3.8.8이 앞의 글자를 다른 까닭(`missing client or server configuration to verify used JWT "alg" header parameter`, `build/index.js` 2062행을 읽었다)에도 쓰기 때문이다. 좁힌 뒤 본 세션이 전체를 한 번 더 돌려 79회차 모두 측정이고 통과와 거부가 아래 표와 같은 것을 봤다(`provider` 묶음의 stderr 경고 줄은 다시 보지 않았다). 좁힌 판정이 실제로 거르는지는 서브에이전트가 손으로 봤다고 보고했고, 본 세션은 아래 두 변이를 다시 넣지 않았다. `FAULT_REASONS`의 `expired` 문구를 `iat`의 것으로 바꾸고 `node .scratch/portal-login/probes/oidc_client/probe/flow.mjs --group fault`를 돌리니 `expired` 여섯 회차와 그 고장의 양성 대조만 측정이 아닌 것으로 빠져 종료 코드 1이었다. `hand.ts`가 설정 문서 요청을 주소 검사 없이 먼저 보내게 바꾸고 같은 명령의 `--group insecure`를 돌리니 `insecure/다`가 앞과 같은 단계(`begin`)와 같은 문구로 거부됐는데 설정 문서 요청이 1이라 측정이 아닌 것으로 빠졌다. 바꾼 두 줄은 되돌렸다. `callback` 묶음의 판정은 그대로다. 거부의 단계(`finish`)만 보고 까닭의 문구는 대지 않는다(문구는 회차의 `error`에 남고 `report.mjs`가 찍는다). `insecure` 묶음도 까닭의 문구는 대지 않고, 거부면 서버가 받은 설정 문서 요청이 0인지만 본다.
- 같은 날 `oidc_client/probe/registry.mjs`는 최신 판(`dist-tags.latest`)이나 그 날짜가 문서에 없는 패키지도 측정이 아닌 것으로 세게 했다. 다시 읽은 다섯 패키지의 값은 아래 표와 같았다(2026-11-12T16:45Z, 한국 시각 2026-11-13 01:45).

### 타입 검사와 린트

- `.scratch/portal-login/probes/oidc_client/probe/typecheck.mjs`로 쟀다. `tsc --noEmit -p apps/portal/tsconfig.json`이 종료 코드 0, 오류 0줄이고 tsc가 본 파일 240개에 프로브의 `.ts` 아홉과 네 라이브러리의 타입 선언이 들었다. 두 tsconfig 복사는 원본과 같았다. 양성 대조 여섯(`indexed.ts` TS2322, `enum.ts` TS1294, `library-types.ts` 5~8행 TS2322)이 모두 걸렸다. 후보 셋과 가짜 서버 둘의 코드에 `any`, 타입 단언, 비null 단언 `!`, `@ts-ignore`를 쓴 자리는 없다.
- `oidc-provider`는 타입 선언을 싣지 않는다(`node_modules/oidc-provider/package.json`에 `types`가 없다. 9.13.3에서 읽었다). 위 타입 검사는 `@types/oidc-provider` 9.13.1을 함께 설치한 것이고, 그것 없이 tsc가 어떻게 끝나는지는 돌려 보지 않았다.
- `.scratch/portal-login/probes/oidc_client/probe/lint.mjs`로 쟀다. 판정한 파일 11개에 파싱 오류 0. 프로브 코드에 걸린 것은 `@typescript-eslint/no-deprecated` 셋뿐이다. `server/oidc/openid-client.ts` 15행과 `server/oidc/oauth4webapi.ts` 14·21행이고, 셋 다 `http` 발급자를 허용하는 `allowInsecureRequests`를 든 자리다(두 라이브러리가 그 이름에 `@deprecated`를 달았다. `node_modules/openid-client/build/index.d.ts` 1398~1400행과 `node_modules/oauth4webapi/build/index.d.ts` 222~225행을 6.8.9와 3.8.8에서 읽었다. 판정자는 인라인 끄기 주석을 받지 않는다, `web/eslint.config.mjs` 156행의 `noInlineConfig`). `hand.ts`, `node-fetch.ts`, `contract.ts`, `fake-idp.ts`, `fake-idp-provider.ts`, `browser.ts`, `round.ts`는 오류 0, 경고 0이다.
- 같은 실행의 갈래. 심은 위반은 기대한 규칙 ID로 모두 걸렸다(타입 단언, `any`, `fetch(…)` 호출의 `no-restricted-globals`, `globalThis.fetch`의 `no-restricted-properties`, `fetch`를 값으로 넘기는 `const handedOver: unknown = fetch`의 `no-restricted-globals`, `!`). 타입 자리의 `typeof fetch`(9행)는 걸리지 않았다. `apps/portal/browser/portal.ts` 자리의 `fetch`는 걸리지 않았다. `apps/portal/node_modules/planted-lib/index.ts`에 둔 `fetch` 호출은 판정자가 그 파일을 보지 않았다.

### 실행 — `flow.mjs`

`.scratch/portal-login/probes/oidc_client/probe/flow.mjs`로 쟀다. node v24.19.0이 `.ts`를 빌드 없이 돌렸고 79회차 모두 측정이다. 변형은 가-기본, 가-서명(`enableNonRepudiationChecks`), 나-기본(`oauth4webapi`만), 나-자체서명(`validateApplicationLevelSignature`), 나-jose(`jwtVerify`), 다.

| 묶음 | 결과 |
|---|---|
| `good`(ㄱ, `http://127.0.0.1` 발급자, http 허용) | 여섯 변형 모두 통과, `sub`가 서버가 정한 무작위 계정과 같음. 공개 키 요청은 가-기본·나-기본이 0, 나머지가 1. 전역 `fetch` 호출은 가-기본 3, 가-서명 4, 나-기본 3, 나-자체서명 4, 나-jose 4, 다 0. stderr 0줄(타입 벗기기 경고 없음) |
| `fault`(ID 토큰 고장 여덟 × 변형 여섯) | `bad_signature`를 가-기본과 나-기본이 받아들였고(공개 키 요청 0) 가-서명·나-자체서명·나-jose·다는 거부. `wrong_issuer`, `wrong_audience`, `expired`, `wrong_nonce`, `missing_nonce`, `alg_none`, `alg_hs256`은 여섯 변형 모두 거부 |
| `callback`(남의 `state`, `error=access_denied`) | 가-서명·나-jose·다 모두 `finish`에서 거부, 토큰 요청 0 |
| `provider`(ㄴ `oidc-provider`, `http://127.0.0.1` 발급자) | 가-서명·나-jose·다 모두 통과. 회차마다 stderr에 `oidc-provider WARNING` 세 줄(개발용 메모리 저장소, 개발용 서명 키, `devInteractions`) |
| `insecure`(`http` 발급자, 허용 끔) | 셋 다 `begin`에서 거부. 가·나는 `OAUTH_HTTP_REQUEST_FORBIDDEN`("only requests to HTTPS are allowed"), 다는 자기 검사. 서버가 받은 설정 문서 요청 0, 전역 `fetch` 0 |
| `transport`(`customFetch`에 `node:http`의 `request`로 만든 함수) | 가-서명·나-자체서명·나-jose 통과, 전역 `fetch` 0, 바꿔 끼운 함수 호출 4 |
| `tls`(사설 인증 기관의 인증서로 `https://127.0.0.1` 발급자, http 허용 끔) | `NODE_EXTRA_CA_CERTS`를 준 회차는 가-서명·나-jose(전역 `fetch` 4)·다(`node:https`)와 `customFetch` 변형 둘 모두 통과. 주지 않은 회차는 다섯 모두 `begin`에서 `UNABLE_TO_VERIFY_LEAF_SIGNATURE`로 거부 |

- 가와 나의 기본 호출은 ID 토큰의 서명을 보지 않는다. 표지는 서명이 틀린 토큰을 서버가 실제로 내줬고(`faultyTokens` 1) 공개 키 요청이 0인 채 통과한 것이고, 양성 대조는 같은 토큰을 나머지 네 변형이 서명 오류로 거부한 것이다. `openid-client`의 타입 선언 주석은 서명 검증이 필수가 아니라고 적는다(`node_modules/openid-client/build/index.d.ts` 1481~1486행, 6.8.9에서 읽었다).
- 가와 나는 `http` 발급자를 요청을 보내기 전에 막고 `127.0.0.1`도 봐주지 않는다. `oauth4webapi`의 검사는 프로토콜만 본다(`node_modules/oauth4webapi/build/index.js` 638~641행, 3.8.8에서 읽었다). 푸는 선택지는 가의 `allowInsecureRequests(configuration)`, 나의 `[allowInsecureRequests]: true`이고 둘 다 `@deprecated`다. jose의 `createRemoteJWKSet`은 선택지 없이 `http` 공개 키 끝점을 받았다(`good`의 나-jose).
- 가와 나는 HTTP를 전역 `fetch`로 낸다(부르는 순간에 전역을 찾는다. `oauth4webapi/build/index.js` 229행의 `(options?.[customFetch] || fetch)`, `jose/dist/webapi/jwks/remote.js` 10행을 읽었다). `customFetch`로 바꿔 끼우면 전역 `fetch`를 한 번도 부르지 않는다(`transport`).
- `NODE_EXTRA_CA_CERTS`는 전역 `fetch`와 `node:https` 모두에 듣는다. 양성 대조는 같은 인증서에 그 변수를 주지 않은 회차가 TLS 검증 오류로 거부된 것이다. 시스템 인증 기관 저장소(`--use-system-ca`, `NODE_USE_SYSTEM_CA`)에 사설 인증 기관을 넣는 길은 시스템 설정을 바꿔야 해서 돌려 보지 않았다.
- `ㄴ`은 고장 심기와 TLS를 붙이지 않았다. `fault`·`callback`·`insecure`·`transport`·`tls` 묶음은 ㄱ으로만 돌았다.

### 의존성과 코드 분량

`.scratch/portal-login/probes/oidc_client/probe/deps.mjs`와 `registry.mjs`와 `loc.mjs`로 쟀다. 설치 크기는 패키지 폴더 안 파일 크기의 합이고, 뿌리 패키지의 값은 레지스트리의 `unpackedSize`와 같았다. 날짜는 2026-11-12T11:24Z에 읽은 것이다.

| 후보 | 패키지 수(전이 포함) | 설치 크기 | 라이선스 | 판과 나온 날 |
|---|---|---|---|---|
| 가 `openid-client` | 3(`jose`, `oauth4webapi` 포함) | 770,234바이트 | MIT 3 | 6.8.9, 2026-11-02 |
| 나 `oauth4webapi` + `jose` | 2 | 548,439바이트 | MIT 2 | 3.8.8, 2026-09-05 / 6.2.17, 2026-11-09 |
| 다 직접 구현 | 0 | 0 | 없음 | 없음 |
| ㄱ 직접 만든 가짜 서버 | 0 | 0 | 없음 | 없음 |
| ㄴ `oidc-provider` | 40 | 1,755,723바이트 | MIT 38, ISC 2 | 9.13.3, 2026-10-29(최신은 9.14.0, 2026-11-11) |
| ㄴ의 타입 `@types/oidc-provider` | 19(`@types/node`와 `undici-types` 포함) | 3,177,785바이트 | MIT 19 | 9.13.1, 2026-10-29 |

- 설치 스크립트를 가진 패키지는 없다. `oidc-provider`는 재던 때 최신(9.14.0)이 나온 지 하루가 안 돼 pnpm의 공급망 유예에 걸려 9.13.3을 적었다(`oidc_client/pnpm-workspace.yaml`의 주석).
- 줄 수(전체/코드). 가 `openid-client.ts` 64/56, 나 `oauth4webapi.ts` 112/99, 다 `hand.ts` 319/273, 함께 쓰는 `contract.ts` 35/22, `node-fetch.ts` 92/80, ㄱ `fake-idp.ts` 305/274(고장 심기와 TLS 포함), ㄴ `fake-idp-provider.ts` 108/98, `browser.ts` 138/121(쿠키와 폼 제출은 ㄴ에만 필요하다), `round.ts` 159/137(2026-11-13에 인자 검사 둘을 서버를 띄우기 전으로 올린 뒤의 값이고 그 전은 156/135였다). 손으로 맞춘 줄바꿈이고 Prettier를 돌린 것이 아니다. 후보 파일에는 변형을 가르는 코드가 섞여 있다.
- 다가 한 검증과 하지 않은 검증의 목록은 `oidc_client/apps/portal/server/oidc/hand.ts` 머리의 주석이 원천이다.

### 돌려 보지 않은 것

`localhost` 이름의 발급자, ㄴ에 고장 심기와 TLS, 시스템 인증 기관 저장소에 넣은 사설 인증 기관, `@types/oidc-provider` 없는 타입 검사, 걸리는 시간, Windows 10 밖의 운영체제.
