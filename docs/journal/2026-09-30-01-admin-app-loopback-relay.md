# 2026-09-30 (01) 관리 화면 앱 — 루프백에만 서서 `/api`를 파이썬 서버로 중계한다

web-admin 티켓 04. 일지 2026-09-29-05의 "다음"(04가 05~08의 남은 임계 경로)을 이어 새 세션에서 했다. 브랜치는
`feature/04-admin-app-loopback-relay`, 주 체크아웃이다. 요청 범위는 구현·리뷰·커밋·PR·병합까지다. 지시문이 넘긴 것(PR
#101 둘째 claude-review의 Minor 둘)을 05·08의 "03이 남긴 메모"에 더했다.

## 한 것

- `web/apps/admin`을 세웠다. Next 16.3.6(고정), React 19.3.0. `app/`은 레이아웃과 `components/pages/HomePage.tsx`(자리표시)를
  그리는 페이지 하나다. tsconfig는 기준 tsconfig를 extends 하고, Next는 dev와 build 어느 쪽에서도 그것을 고쳐 쓰지 않았다.
- 시작 래퍼 `tools/start.ts`. `dev`와 `start`가 거친다. `--hostname`·`--port`만 받고 next에 넘길 인자를 다시 지으며, 판정을
  지나면 next CLI를 같은 프로세스에서 부른다. 판정은 `tools/loopback.ts`의 순수 함수다.
- `next.config.ts`. `/api/:path*`를 `AGENT_OS_UPSTREAM`(기본 `http://127.0.0.1:8000`)으로 넘기고 `compress: false`,
  `agentRules: false`. 상류는 설정을 읽을 때 판정한다.
- 규칙 파일 `.claude/rules/web-admin.md`, README의 관리 화면 절.
- 판정자: `app/`의 import 정책을 고쳤고, 저장소 `.gitignore`를 그대로 읽어 빌드 산출물을 뺀다. Prettier도 같다.

정한 것과 그 이유는 티켓 파일의 "이 티켓이 정한 것"이 원천이다.

## 구현 중에 멈춘 자리 둘

**IPv6 상류.** 중계 프로브를 처음 돌렸을 때 상류 `http://[::1]:8766`은 빌드를 지나고 `/api` 요청마다 500이었다. 관리 화면
로그는 `TypeError: Missing parameter name at 1`이었다. Next는 `rewrites` 목적지의 호스트 이름도 path-to-regexp 틀로
컴파일한다(`prepare-destination.js`의 `safePathToRegexp(destHostname)`). URL 안의 IPv6 리터럴은 콜론 없이 적을 길이 없다.
관리 화면 자신을 `::1`에 세우는 것은 됐다.

**빌드 산출물.** `next build` 한 번 뒤 `pnpm run lint`가 `.next/`에서 파일 43개를 읽고 그중 14개에서 96건으로 빨갰다.
번들 JS의 전역 `fetch`와 금지 구문, Next가 빌드마다 다시 쓰는 `.next/types/validator.ts`의 `any`·`as`·`@ts-ignore`다.
Prettier도 `.next/`와 `next-env.d.ts`를 봤다. `distDir`은 프로젝트 밖에 둘 수 없다(설치본 문서).

두 자리 모두 ADR 이력 초안을 보이고 물었다.

> 사용자(질문에 답): "상류는 127.0.0.1 하나 (Recommended)" / ".gitignore를 읽고 가드 (Recommended)" — 보인 ADR 0011·0020
> 이력 초안 그대로. 헌법 문구를 patch하는 안은 고르지 않았다

ADR 0011과 0020에 2026-09-30 이력을 쌓았다.

## 잰 것

- **01의 규칙을 실제 자리에서.** `lintText`는 없는 경로에서 `was not found by the project service`로 파싱 오류가 났다.
  그래서 실제 자리에 파일을 잠깐 만들어 verify의 린트 명령을 JSON으로 돌리는 변이 러너를 두었다
  (`probes/admin_app_mutations.mjs`). 여섯 대상과 타입 기반 규칙이 모두 기대한 규칙 ID로 빨갰다.
- **`app/`이 next를 import하면 빨갰다.** 실제 `app/layout.tsx`의 `import type { Metadata } from "next"`다. boundaries의
  디버그 출력(`ESLINT_PLUGIN_BOUNDARIES_DEBUG=1`)을 보니, 앱의 `node_modules`로 풀린 next가 모듈 출처는 `external`인데
  요소는 `workspace-app`으로도 분류됐다. 01의 임시 트리에는 next가 설치되지 않아 드러나지 않았다. 첫 선택자를
  `module: { origin: "local" }`로 좁혔다. 엔티티 수준의 `origin: "local"`은 받아지지만 아무것도 좁히지 않았다(모듈 출처가
  아니라 의존의 종류를 보는 선택자다). 같은 자리에서 `node:fs`가 `core` 출처라 두 선택자 모두를 지나는 것도 보고 막았다.
- **`agentRules`.** 이 세션에는 `CLAUDECODE`와 `AI_AGENT`가 있어 Next가 에이전트를 감지한다. 래퍼로 띄운 `next dev`는
  `127.0.0.1`에만 섰고(netstat의 LISTEN 한 줄) 두 파일을 만들지 않았다. 대조군으로 `agentRules: true`를 주자
  `✓ Generated AGENTS.md and CLAUDE.md for AI agents.`가 찍혔고, `tools/check_instructions.py`가 둘을 빨갛게 봤다(종료 1).
  지우고 설정을 되돌렸다. 대조군 동안 이 세션의 작업 디렉터리가 Bash의 `cd`로 앱 폴더에 가 있었고, 생긴 `CLAUDE.md`의
  `@AGENTS.md`가 이 세션의 컨텍스트에 실렸다. 생긴 블록은 "커밋하면 트리가 깨끗해진다"고 권한다. ADR 0021이 막으려던 길이
  실제로 그 모양이다.
- **Next 16.3.6과 16.3.3.** 옆 저장소의 설치본과 먼저 견줬고, 다시 돌 수 있게 두 판의 tarball로 옮겼다
  (`probes/next_16_3_diff.sh`). 열여섯 파일이 판 문자열 밖으로 같다.
- **중계를 실제로.** `probes/admin_relay.mjs`가 실제 `serve`와 래퍼로 띄운 `next start`를 세운다. 토큰은 무작위로 만들어
  두 프로세스의 환경에만 넘겼다. 17 모두 기대대로다. `/api/plugins`가 파이썬의 JSON과 바이트까지 같고, 토큰 없는 요청과
  다른 출처의 `OPTIONS`는 401이다. `start` 때 상류를 아무것도 없는 포트로 주어도 빌드 때 상류로 넘겼다. `build`, `start`,
  `dev` 모두 루프백이 아닌 상류에서 설정을 읽을 때 종료 1이다. `dev`는 포트를 루프백에 먼저 열고 설정을 읽는다.
  `/api/plugins`의 본문은 497바이트로 압축 하한(1KB) 아래라, `compress: false`는 페이지(4343자)로 봤다.
- **tsc.** `.next`와 `next-env.d.ts`가 없는 상태(CI와 같다)에서도 앱의 `tsc --noEmit`이 초록이었다. `next-env.d.ts`는
  dev면 `.next/dev/types`, build면 `.next/types`를 가리킨다.
- **규칙 파일이 실리는지.** 새로 만든 규칙 파일은 이 세션에서 앱 파일을 Read로 열어도 실리지 않았다. 새 세션을 한 번
  띄워 봤다. 01의 탐침 때 사용자 전역 Stop 훅이 Slack 알림을 보낸 부작용이 있어, `--setting-sources project,local`로 사용자
  설정을 뺐다. 명령은 `claude -p --setting-sources project,local --allowed-tools Read --model claude-haiku-4-5-20251001 "<질문>"`이다.
  앱 파일(`app/page.tsx`)을 열게 하자 규칙의 첫 낱말("Next")을 답했고, 앱 밖 파일(`packages/api-client/src/index.ts`)에서는
  "없음"이었다.

## TDD와 변이

루프백 판정과 래퍼의 테스트를 먼저 썼다. 구현 전의 빨강은 모듈 부재였다. 그래서 러너로 변이를 넣었고, 셀프 리뷰 뒤
31, PR 리뷰 뒤 32 모두 기대대로 빨강이다. 래퍼가 판정하고도 거부하지 않는 변이는 프로세스 테스트
(`start.spawn.test.ts`)로는 재지 않는다. 그것을 재려면 `next dev`가 `0.0.0.0`에 떠야 하고, 시간 제한에 걸려 래퍼가
죽어도 next의 자식 서버가 남는다. 인자 테스트(`start.test.ts`)가 같은 변이를 잡는다.

## 셀프 리뷰

`/code-review`(base `a7a90a5`, 추적 파일 15, 미추적 14, 커밋 0)를 돌렸다. Standards는 Critical·Major가 없었다. Spec은
Major가 하나였다.

고친 것:

- **두 축이 같이 찾은 것.** 루트 `.gitignore`의 앵커 없는 `traces/`와 `dist/`가 관리 화면의 `app/traces/`(07의 실행 목록
  자리)를 git과 판정자에서 함께 뺐다. `git check-ignore`로 확인했다. 추적 파일 가드는 git도 무시해 추적되지 못한 파일을
  보지 못한다. 뿌리에 앵커하고 그 자리를 따로 재는 테스트를 더했다. 자기 판정 범위를 `.gitignore`에 맡긴 결정이 그 파일의
  옛 패턴을 판정의 문제로 만든 자리다.
- **닫은 틈의 미래형 문장.** 명세 다섯 곳과 ADR 0021 하나에 "(2026-09-30, 티켓 04)"를 달았다.
- **Standards.**
  - `start.ts` 독스트링의 과장을 좁혔다. next가 홀로 남지 않는다고 적었는데, `next dev`는 서버를 자식으로 띄운다.
  - 커밋된 근거 없는 "실측"에 이 일지를 달았다.
  - 프로브 README의 근거 자리를 고쳤고, `ruleIdsAt`와 ESLint 인스턴스 셋을 하나로 모았다.
  - SSH 안내를 한 함수로 뺐다.
  - "판을 바꾸면 다시 돈다"를 지침에만 두지 않고 판을 고정한 테스트로 계기를 주었다.
- **Spec.**
  - `next_16_3_diff.sh`에 `agentRules` 게이트 파일(`start-server.js`)을 더했다.
  - dev의 상류 판정을 프로브에 더했다.
  - `127.1` 정규화와 `PORT` 경로의 테스트를 더했다.
  - 08 메모의 "빠뜨리면 컴파일이 실패한다"는 반례가 있어 고쳤다. import를 빠뜨리면 DOM `Event`로 조용히 풀린다.
  - 01의 아이콘 메모를 05로 넘겼다.
  - CI의 ubuntu 상자는 PR의 CI를 보기 전이라 풀었다.

남긴 것:

- **헌법 원칙 III의 "생성물도 판정 범위에서 빼지 않는다"(Spec, Major).** 사용자가 문구를 그대로 두는 안을 골랐다. ADR
  0020 이력이 그 "생성물"을 커밋하는 생성물로 읽는다. PR에서 다시 보인다.
- **요청 밖 동작 둘(Spec, Nit).** 래퍼가 모르는 인자를 거부하는 것과 상류의 형식 검증이다. 티켓의 "이 티켓이 정한 것"에
  이유와 함께 있다.
- **포트가 문자열로 다닌다(Standards, Nit).** next가 검증한다.

## 검사

커밋 전에 `CLAUDE.md`의 검증 명령 다섯을 돌렸다. pytest 1013, ruff 두 명령, pyright 0, lint-imports, `pnpm -C web
verify`(테스트 132) 모두 초록이다. pre-commit 전용인 지침 검사와 타입 우회 검사도 초록이다. 프로브 셋은 모두 종료 0이다
(`next_16_3_diff.sh`, `admin_relay.mjs` 17, `admin_app_mutations.mjs` 31).

## PR 리뷰

PR #102. CI 둘(`verify`, `claude-review`)과 CodeRabbit이 초록이었다. 두 워크플로 모두 HEAD `53c1618`의 것이고,
`verify` 잡(ubuntu-24.04)이 앱의 테스트 파일 셋과 판정자 테스트를 돌렸다. 그래서 티켓의 "윈도우와 CI의 ubuntu" 상자를
채웠다. CodeRabbit은 `53c1618`까지 보고 지적이 없었다. claude-review는 Minor 하나와 Nit 하나였다.

고친 것:

- **테스트 파일 하나가 세 이유로 바뀌었다(claude, Minor, 리뷰 관점 3).** `loopback.test.ts`가 루프백 표, 래퍼의 인자
  규칙, 설정의 상류를 함께 쟀다. 넷으로 나눴다. 표는 순수 함수 둘에 직접 걸고(`loopback.test.ts`), 인자는
  `start.test.ts`, 프로세스는 `start.spawn.test.ts`, 설정 파일은 `next.config.test.ts`다. 인자와 프로세스를 가른 것은
  "판정하고도 거부하지 않는" 변이를 인자 테스트만으로 재려는 것이다. 설정 파일이 판정을 거르지 않는지 보는 변이를 더해
  32 모두 빨강이다.
- **주석이 설명하는 상수 위에 있지 않았다(claude, Nit).** `UPSTREAM_ENV`와 `DEFAULT_UPSTREAM`에 주석을 하나씩 두었다.

둔 것:

- **start 때의 상류 입력과 빌드 때 박힌 목적지가 다르면 드러내자(CodeRabbit, proposed).** 명세는 start 때 설정 파일이
  다른 값을 판정해도 실제 목적지가 빌드 때 값인 것을 받아들였고(중계 절), README가 상류를 바꾸면 다시 빌드하라고 적는다. 막을
  위험이 아니라 운영자의 착각을 줄이는 일이라 이 티켓 밖이다. 끊김과 실패한 빌드의 회복을 재는 검사도 같은 제안에
  들었고, CodeRabbit도 확인된 취약점이 아니라고 적었다.

반영 뒤 검증 명령 다섯을 다시 돌렸다. pytest 1013, `pnpm -C web verify`(테스트 138) 모두 초록이다.

## 회고

후보 여섯을 냈다. 넷을 승인받았고, 이 세션에서는 반영하지 않고 대기열에 적었다.

> 사용자(질문에 답): 기존 행 "59에 2회차, 61에 2회차, 45에 회차" / 새 항목 "rules 확인법 (63)"

- **59(2회차).** `tools/mutate.py`가 pytest 밖의 명령을 돌지 못해 03의 JS 러너를 베껴 둘째 러너를 지었다. 파일을 새로
  만드는 변이와 ESLint 규칙 ID 판정을 더했다. 러너 루프가 두 벌이 됐다.
- **61(2회차).** 측정과 테스트가 소비 지점에서 멈춘 자리가 둘이다. 01의 임시 트리에 next가 설치되지 않아 `app/`의 import
  정책이 next·react를 막는 것이 초록 사례 없이 지나갔다. 설계 측정은 IPv4 상류만 재서, 명세가 `::1`까지 같은 표로 넓힌
  것이 요청마다 500이 될 줄 몰랐다.
- **45(2회차).** ADR 0020 이력과 테스트 주석에 커밋된 근거 없는 "실측"이 들어갔다. Standards 축이 잡았고 이 일지를 달았다.
- **63(새로).** 새 rules 파일은 만든 세션에 실리지 않는다. 확인하는 법(새 세션, 사용자 설정을 뺀 `claude -p`, 카나리아와
  대조군)을 `operations.md`에 적는다.

기각한 것(일지에만 남긴다):

- **중첩 `CLAUDE.md`가 실리는 길.** 대조군 동안 Bash의 `cd`가 이 세션의 작업 디렉터리를 앱 폴더로 옮겼고, 거기 생긴
  `CLAUDE.md`가 실렸다. ADR 0021 이력의 "Read할 때"에 없는 길이다. 한 번 본 관찰이다.
- **PR·CI에 걸린 티켓 상자는 증거와 함께 채운다.** Spec 축이 "CI는 PR에서 본다"로 채운 상자를 짚었다.

## 다음

- **web-admin의 05가 다음이다.** 05는 03과 04를 기다렸고 둘 다 병합된다. 05가 페이지 이음매와 첫 e2e를 세운다.
- 04가 05에 넘긴 것은 05의 "04가 남긴 메모"와 "03이 남긴 메모"의 마지막 항목에 있다. e2e가 관리 화면을 띄우는 모양,
  앱의 단위 테스트가 node 환경에 남는 것, `app/`의 import, 빌드 산출물, README, 아이콘이다.
