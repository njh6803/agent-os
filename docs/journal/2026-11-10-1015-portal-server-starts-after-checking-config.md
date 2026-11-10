# 2026-11-10 (10:15) 질문 페이지 서버가 설정과 사이트 파일을 대 본 뒤에야 뜬다 (pilot-portal 04)

세션 제목 `feature/04-portal-server-starts-after-checking-config`. 브랜치 같은 이름, 워크트리 `.claude/worktrees/04-portal-server-starts-after-checking-config`(기준 `c4af6063`). 모델 Sonnet 5.5 / high(지시문).

## 사용자 프롬프트

> .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/pilot-portal/issues/04-portal-server-starts-after-checking-config.md
>
> 다음 작업: .scratch/pilot-portal/issues/04-portal-server-starts-after-checking-config.md. 질문 페이지 서버가 설정과 사이트 파일을 대 본 뒤에야 뜬다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 2 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 이어받을 상태: PR #510의 claude-review 둘째 회차가 낸 Minor 가운데 일지 "다음"에 없는 둘을 보류했다. `@agent-os/site-file`의 `SiteEntry.origins`와 `site.allowedOrigins`가 같은 배열을 두 번 든다. 위젯 전용 값(`buildInput`, `WIDGET_ORIGINS_ENV`, `WIDGET_REQUEST_CHARS_ENV`, `BuildInput`)이 공유 패키지에 있다. 일지 "다음"의 `siteFileInput` export와 `site-file.ts` 나누기와 함께, 이 티켓이 그 패키지를 import하기 전에 고칠지를 정한다(고치면 이 티켓의 요구 밖이므로 따로 harness 티켓이나 고침 티켓으로 한다)
> 이번 요청 범위: PR과 병합까지

## 한 일

`web/apps/portal`(`@agent-os/portal`)을 처음 만들었다. 질문 페이지는 Next가 아니라 `node:http` 서버 하나이고 빌드 없이 node가 `.ts`를 바로 돈다. 이 티켓의 몫은 아래 넷이다.

- 시작 명령 `start`(`tools/start.ts`): `--config`와 `--site-file`을 받아 설정과 사이트 파일, 개인 키가 서로 맞을 때만 서버를 띄운다. 서면 stdout에 `질문 페이지가 http://127.0.0.1:<port>/portal/ 에 섰다. 사이트 <N>개.` 한 줄을 찍는다. 어긋나면 stderr에 `구성 오류:` 한 줄과 어긋난 자리마다 `<자리>: <까닭>` 한 줄을 찍고 종료 코드 1이다.
- 시작 검사(`server/config.ts`, `site-check.ts`, `load.ts`): 설정의 칸과 규칙, 고지 전문 짓기(`notice.ts`, 쿠키 일수는 인자), 사이트 파일 대조 여섯 갈래, 설정 안의 겹침과 개인 키, 루프백 밖 `host`. 어긋남은 두 단계로 모두 모아 낸다. 파일마다 따로 볼 수 있는 것(설정 모양, 사이트 파일 판정)을 먼저 모두 내고, 둘이 읽혀야 하는 대조(개인 키와 사이트 파일 여섯 갈래 가운데 다섯)는 그 뒤에 한다. 개인 키를 읽지 못해도 키가 맞는지만 빼고 대조를 계속한다.
- 순수 요청 처리기(`server/handler.ts`)와 `node:http` 겉(`serve.ts`): `GET /portal/health`만 200이고 모르는 경로는 404, 다른 메서드는 405와 `Allow`, 모든 응답에 `nosniff`.
- 키 만들기 명령 `make-key`(`tools/make-key.ts`): RSA 2048 개인 키를 PKCS#8 PEM으로(`wx` 플래그, 모드 0600) 쓰고 `[[sites.public_keys]]` 조각을 stdout에 낸다. 이미 있는 파일은 덮어쓰지 않고 종료 코드 1이다.

루프백 목록 주석 셋(`main.py`, 관리 화면 `loopback.ts`, 위젯 `start.ts`)의 "셋"을 넷으로 고쳤다. README 트리와 `tech.md` 웹 행에 앱을 더했고 헌법 판을 3.0.80으로 올렸다(형제 02가 3.0.79를 먼저 가져갔다).

- `loadPortal`은 설정만이 아니라 시작 때 읽어 둔 개인 키(`privateKey`)와 사이트 파일(`siteFile`)도 낸다. 05 티켓이 04가 시작 때 읽어 둔 개인 키와 사이트 파일의 `audience`를 쓴다고 전제해서다(05 티켓의 Blocked by 줄). 05 티켓에 그 사실을 메모로 넘겼다.
- 순수 처리기에 시계와 UUID 만들기를 인자로 받는 자리는 두지 않았다. 쓰는 끝점이 없어 안 쓰는 인자가 되고, 린트의 `no-unused-vars`에 걸린다(`web/eslint.config.mjs`가 켠 `strictTypeChecked`의 규칙이고 설정을 읽은 것이며, 인자를 두고 돌려 보지는 않았다). 05 티켓이 `handle`의 인자로 더한다(05 티켓 메모). 요청 값에는 헤더와 쿠키(`parseCookieHeader`, 실린 차례의 열)를 넣었다.
- 진단의 `sites[<i>]`는 사이트 파일의 진단과 같은 0부터다(명세의 `sites[1].agent`는 꼴의 예로 읽었다).

## 이어받은 상태의 판단: site-file 패키지 Minor 둘과 일지 "다음" 둘

고치지 않았다. 이 티켓이 `@agent-os/site-file`에 칸을 더하지도, 그 파일을 고치지도 않아서다(`readSiteFile`과 `originRule`, 모델의 `agents`·`allowedOrigins`·`publicKeys`·`audience`를 읽기만 한다). 일지 "다음"이 "04가 칸을 더하기 전에 나눈다"고 적은 조건이 서지 않았고, 이 티켓의 체크박스에 없는 일이라 스킬의 "요구하는 것만 쓴다"에 따른다. 네 건은 아래 "다음"에 남긴다.

## 확인한 것

- 빨강 먼저: 시험 9개 파일을 구현 전에 돌려 모두 빨갛게 보았다(모듈이 없어서). 그 빨강은 모듈 부재라 로직을 증명하지 못한다. 로직의 빨강은 구현 중에 얻었다. 키 대조 정상 사례가 "다르다"로 빨갰고 `createPublicKey`는 공개 키 객체를 받지 못하는데 `catch`가 그 예외를 삼켜 `undefined`로 읽은 것이 원인이었다(`createPublicKey(공개 키 객체)`가 `ERR_CRYPTO_INVALID_KEY_OBJECT_TYPE`로 던지는 것을 임시 스크립트로 손으로 봤고 스크립트는 지웠다). 개인 키 객체를 `spkiOf`에 바로 넘기게 고쳤다. 그 사례가 정상 갈래의 빨강을 지킨다.
- tsconfig: 확장자 없는 상대 import 하나(`./args`)를 넣어 `pnpm -C web run typecheck`가 `tools/start.ts(20,34): error TS2835`로 빨갛게 되는 것을 본 뒤 되돌렸다. `strictNullChecks: false`를 일부러 넣어 `pnpm -C web run check:tsconfig`가 `apps/portal/tsconfig.json: strictNullChecks 가 거짓으로 덮였다`를 내는 것도 본 뒤 되돌렸다(검사가 새 tsconfig를 본다).
- `pnpm`은 `pnpm start -- --config …`의 `--`를 스크립트에 그대로 넘긴다(`$ node tools/start.ts "--" "--config" …`). 그래서 두 명령이 앞의 `--`를 건너뛴다(`tools/args.ts`).
- 실제 실행(아래 PR 본문의 명령과 출력): 맞는 설정과 사이트 파일로 시작 로그 한 줄과 `/portal/health` 200 `{"status":"ok"}`, `/portal/`은 404. `agent`를 틀리게 바꾸면 `구성 오류:` 아래 `sites[0].agent: …` 한 줄과 종료 코드 1.

## 하지 않은 것

- `sync-design-system 확인`은 계기 훅이 부르라고 알렸지만(`web/apps/` 아래 첫 편집) 돌리지 않았다. 이 티켓은 화면 코드도 디자인 토큰도 건드리지 않고(서버, 설정, 키 명령) 페이지와 CSS는 06이 짓는다. 06 티켓이 화면을 처음 고칠 때는 돌린다.

## 셀프 리뷰

범위는 기준 `c4af6063`, 변경 파일 9개, 커밋 0개(전부 미커밋), 미추적 묶음 2개(일지 한 파일과 `web/apps/portal/`)다. 표준 축은 sonnet·high, 명세 축은 세션 모델이다. Critical은 없고 Major도 없었다.

- 고친 것(명세 축 c1) 앞선 사이트가 다른 칸 때문에 어긋나면 뒤 사이트의 `issuer`·`name` 겹침이 진단에서 가려졌다(`sites[0].heading` 빠짐과 `sites[1]`의 같은 `issuer`를 함께 넣으면 앞의 것만 나왔다). 겹침 비교를 사이트 전체가 유효한지와 상관없이 두 값(`identityOf`)만 보게 하고 시험 하나를 더했다.
- 고친 것(표준 5, 6) 실패를 기대하는 시험 셋(`start.test.ts`의 둘, `make-key.test.ts`의 빈 kid)이 까닭을 단언하게 했다. 윈도우에서 단언 없이 초록이던 0600 모드 시험을 `test.skipIf`로 건너뜀을 드러냈다. 이 PC(윈도우)에서는 그 시험이 한 번도 돌지 않았다. CI의 ubuntu에서 돈다.
- 고친 것(표준 7, 8, 명세 a) 헌법 판 README에 3.0.79를 형제 02가 비워 둔 문장을 더했다. 형제 02가 3.0.79를 쥔 것은 그 워크트리의 미커밋 README로 `sibling_overlap.py`가 알렸고, origin/main과 02 브랜치의 커밋에는 아직 없다. 루트 README 트리가 빠뜨린 `cookies`·`cookie-policy`·`diagnostics`·`tools/args.ts`를 더했다.
- 고친 것(명세 c2, c3, c5) `handler.ts`의 헤더 주석(`cookie`는 `; `로 이어진다), 미사용 인자를 잡는 것이 타입 검사가 아니라 린트라는 05 티켓 메모와 이 일지의 문장, 재지 않고 적은 시간 어림 둘(`fixtures.ts`, `start.spawn.test.ts`)을 고쳤다.
- 남긴 것 표준 1~4는 Minor다. `config.ts`의 함수들이 `problems`를 출력 인자로 변형하고, `start.ts`·`make-key.ts`가 실패 분기마다 같은 출력·종료 코드·return을 되풀이하며, 오류 코드를 뽑는 줄이 세 벌이고, `textOf`·`privateKeyOf`가 `CONTEXT.md`의 `_of` 동사(포트에 닿지 않는다)와 어긋난다. 이 가운데 CQS와 출력 인자 줄은 파이썬 기준으로 적힌 `CODING_STANDARDS.md`의 줄이고, `config.ts`의 모양은 `site-file` 패키지의 `sitesOf`(`{value, problems}`)와 다르다. 05가 같은 파일을 더 고치기 전에 한꺼번에 맞추는 편이 싸서 후속으로 둔다(아래 "다음").
- 남긴 것 명세 c4는 Nit이다. `portal.host` 진단이 받은 값을 날것으로 실어 개행이 든 값이면 `구성 오류:` 줄을 흉내 낼 수 있다. 값을 싣는 것은 명세대로이고 설정은 운영자 본인이 쓴다.
- 다시 돌린 명령 `uv run python tools/run_checks.py`는 반영 전 판으로 아홉 모두 통과했다(pytest 644초, web-verify 747초). 반영 뒤에는 portal 시험(102개 통과, 1개 건너뜀)을 다시 쳤고, 전체는 커밋이 부르는 pre-commit으로 갈음한다. ruff 둘은 반영 전에 통과했다(변경은 `.ts`와 마크다운뿐이다).

## 회고

후보 다섯, 판정은 승인 0, 기각 5, 넘김 0이다. 대기열에 새로 쓴 항목과 회차를 더한 항목은 없다. `queue_open_rows.py`의 만료 대상도 없다(열린 100개, 만료할 항목 없음).

- 키 대조가 정상 사례에서 "다르다"로 나온 버그(`createPublicKey`에 공개 키 객체를 넘기면 던지는 예외를 `catch`가 삼켜 `undefined`로 읽었다): 기각. 사건은 있으나 이 세션의 시험 사례가 구현 중에 바로 잡았고, 같은 꼴을 다른 곳에서 겪은 기록이 없다. 새 검사를 더할 문턱(다섯 번째, 또는 손상)에 한참 못 미친다.
- 안 쓰는 인자 때문에 명세가 말한 시계·UUID 인자를 두지 못한 것: 기각. 린트의 `no-unused-vars`가 알릴 자리라(이미 있는 검사), 05 티켓 메모로 넘겨 이 일이 닫혔다.
- Bash `cd` 거부와 복합 heredoc 거부(워크트리 가드): 기각. 훅과 가드가 그 자리에서 막았고 `CLAUDE.md`의 환경 함정이 같은 모양을 이미 적고 있다.
- `pnpm start -- --opt`가 `--`를 스크립트에 그대로 넘긴 것: 기각. `tools/args.ts`와 그 시험이 막고, 낯선 동작이지만 코드의 `withoutSeparator` 주석이 까닭을 든다(환경이 원천인 사실을 문서에 복사하지 않는다).
- 형제 02와 헌법 판·락 파일이 겹칠 후보: 기각. `sibling_overlap.py`가 이미 알렸고 이 세션은 그대로 따랐다.

## 다음

- 05 티켓(고지 확인과 토큰 끝점)이 프런티어다. 02(e2e 준비 패키지)는 나란히 돈다. 둘 다 `web/pnpm-lock.yaml`, README 트리, `tech.md` 웹 행, 헌법 판을 고쳐 나중에 병합하는 쪽이 main을 받아 맞춘다(헌법 판은 3.0.79 위로).
- 05는 `handle`에 시계와 UUID 만들기를 인자로 더하고, `loadPortal`의 `privateKey`와 `siteFile`을 쓴다(05 티켓 메모).
- 06이 질문 페이지 앱의 DOM 라이브러리를 `lib`에 더하고, 페이지 스크립트의 `fetch` 예외 블록을 eslint 설정에 둔다. 앱의 `browser/` 폴더 이름은 04가 정한 금지 폴더 목록과 겹치지 않는다.
- 05가 `config.ts`와 `start.ts`·`make-key.ts`를 더 고치기 전에 셀프 리뷰의 Minor 넷(출력 인자 변형, 실패 분기의 되풀이, 오류 코드 뽑기 세 벌, `_of`·`read` 이름)을 맞출지 정한다. 맞추면 이 앱 안의 정리이고 계약은 건드리지 않는다.
- site-file 패키지의 보류 넷은 아직 안 고쳤다. (1) `siteFileInput`이 테스트만 부르는 export이고 `index.ts`의 `export *`로 공개 표면에 오른다. (2) `site-file.ts`가 약 600줄 한 파일이다. (3) `SiteEntry.origins`와 `site.allowedOrigins`가 같은 배열을 두 번 든다. (4) 위젯 전용 값(`buildInput`, `WIDGET_ORIGINS_ENV`, `WIDGET_REQUEST_CHARS_ENV`, `BuildInput`)이 공유 패키지에 있다. 질문 페이지가 그 패키지에 칸을 더하는 일이 생기면 그 전에 harness 티켓이나 고침 티켓으로 나눈다. 칸을 더하지 않으면 급하지 않다.
- 변이 표 `site_file_mutations.toml`의 남은 표지 다섯(10~13, 16)은 앞 일지의 "다음"대로 그대로 남아 있다.

## 인계 (커밋 뒤)

컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤` 경계에 와서 넘긴다. 이 세션의 제목은 `feature/04-portal-server-starts-after-checking-config`였다.

- 커밋 `e18d6283`이 pre-commit을 모두 지났다(ruff 둘, 러너, 헌법 판, 커밋 메시지. 카나리아 모양은 해당 파일이 없어 `Skipped`). 그 뒤 이 일지만 고쳤다(인용 경고 한 줄 정리와 이 절). 이 변경은 커밋하지 않았다.
- 남은 단계는 푸시, PR(본문에 실제 기동 명령과 출력), PR 직전 리뷰(`coderabbit-review`, CLI가 못 돌면 `bug-perf-review`), `ccd_pr`의 `get_status`와 `bind_pr`, `tools/wait_ci.py <PR번호>`, 병합(`next-session` `merge.md`의 "워크트리에서 병합할 때")이다.
- PR 본문의 실제 기동 확인은 새 세션이 다시 친다. 이 일지의 "확인한 것"에 적은 동작(시작 로그 한 줄, `/portal/health` 200 `{"status":"ok"}`, `/portal/` 404, `agent`를 틀리게 한 설정의 `구성 오류:`와 종료 코드 1)을 `pnpm -C web/apps/portal start -- --config <설정> --site-file <사이트 파일>`로 임시 폴더의 파일로 다시 보고, 그 명령과 출력을 본문에 싣는다. 이 세션은 그 출력을 컨텍스트에 남기지 못했다.
- 셀프 리뷰 결과는 위 "셀프 리뷰" 절이다. 반영 뒤 web 전체(`pnpm -C web verify`)는 커밋의 pre-commit이 돌려 통과했고, 관리 화면·위젯 e2e와 사진 비교는 돌리지 않았다(그 앱의 변경은 주석 한 줄씩이다).
- PR 직전 리뷰에 밀 주장(셀프 리뷰 반영으로 새로 쓴 사실 문장): (1) 헌법 판 README의 3.0.79 문장("형제 브랜치(`feature/02-e2e-stack-package`)가 먼저 매겨 비워 두었다")은 `sibling_overlap.py`가 02 워크트리의 미커밋 README에서 읽은 값이다. (2) `handler.ts` 주석의 `cookie` 헤더가 `; `로 이어진다는 것. (3) 05 티켓 메모와 이 일지가 말하는 미사용 인자를 잡는 쪽이 린트(`no-unused-vars`)라는 것(설정을 읽은 것이고 돌려 보지 않았다). (4) `config.ts`의 `identityOf`가 사이트 전체의 유효 여부와 상관없이 `issuer`·`name`만 뽑는다는 것.
- 제목을 `feature/04-portal-server-starts-after-checking-config (인계함)`으로 바꾸고 워크트리 잠금을 풀었다. 이 세션이 띄운 백그라운드 작업은 없었다.
- open-session을 부른다 2026-11-10T01:43:31Z

## 이어받은 세션 (PR 단계)

세션 제목 `feature/04-portal-server-starts-after-checking-config`. 이 일지에서 PR 전까지의 몫을 이었다.

- 이전 세션이 띄운 `start` 프로세스(포트 18765, 세션 `ff01fd7e`의 스크래치패드 설정)가 남아 있었다. 손으로 봤다: 처음 돌린 기동 확인에서 설정이 틀려 서버가 서지 못했는데도 `curl`이 그 포트의 `/portal/health`에 200을 받았고, PowerShell `Get-NetTCPConnection -LocalPort 18765 -State Listen`과 `Get-CimInstance Win32_Process`로 그 포트를 쥔 `node` 명령 줄이 `tools/start.ts`와 `ff01fd7e` 경로의 설정이었다. 위 "인계"의 "이 세션이 띄운 백그라운드 작업은 없었다"는 틀렸다. 명령 줄이 이 티켓의 시작 명령과 일치하는 그 PID만 `Stop-Process`로 끝냈고(그 뒤 같은 포트의 듣는 연결 0개), 기동 확인은 다른 포트(18799)에서 다시 쳤다.
- 손으로 봤다: `make-key`는 개인 키 경로의 폴더가 없으면 만들지 않고 `개인 키를 쓰지 못했다(ENOENT)`로 끝난다(종료 코드 1, 폴더 없이 친 첫 실행의 출력). 명세는 폴더 만들기를 요구하지 않아 고치지 않았다. 운영자가 폴더를 먼저 둔다.
## PR 직전 리뷰 (`coderabbit-review`)

서브에이전트가 `coderabbit review --agent --include-untracked --base origin/main`을 돌렸고(CLI 0.7.5, `Plan: Free`, `Seat: not assigned`) 파일 34개에서 `review_completed`, 지적 0건으로 끝났다. 좌석이 없어도 리뷰는 돌았다(서브에이전트 보고). 같은 서브에이전트가 코드를 읽고 직접 올린 Minor 7건 가운데 아래 하나만 이 PR에서 고쳤다. 서브에이전트는 서버를 띄우는 프로브와 `make-key` 실행을 하지 못했고(워크트리 가드가 heredoc 쓰기를 거부), 그 부분은 코드를 읽은 판정이다.

- 고친 것(서브에이전트가 스크래치 프로브로 재현했고, 이 세션이 시험으로 다시 빨강을 봤다): 사이트 파일의 `pem`에 개인 키 PEM이 들어 있어도 `spkiOf`가 `createPublicKey`로 그 개인 키에서 공개 키를 뽑아 키 대조를 통과시켰다. `load.test.ts`에 시험을 먼저 더해 `어긋난 파일이 받아들여졌다`로 빨간 것을 보고(`pnpm -C web/apps/portal exec vitest run server/load.test.ts`), `site-check.ts`의 `spkiOf`가 글을 `BEGIN PUBLIC KEY` 표지가 있는 것만 받게 고쳤다. 서버 쪽이 SPKI 공개 키 PEM만 받는 것은 `src/agent_os/main.py`의 `_SPKI_HEADER`와 그 독스트링을 Grep으로 읽어 확인했다. 고친 뒤 portal 시험 103개 통과, 1개 건너뜀.
- 남긴 것(모두 Minor, 코드를 읽은 판정이고 실행으로 재현하지 않았다. 05가 같은 파일을 만질 때 함께 정한다): (1) `config.ts`의 `unknownKeys`가 모르는 칸 이름을 날것으로 진단에 싣는다. 서브에이전트가 ESC와 개행이 든 이름으로 `parseConfig`를 불러 가짜 진단 줄이 서는 것을 재현했다. 앞의 `portal.host` Nit과 같은 종류다. (2) `site-file` 패키지의 `읽을 수 없다(${error.message})`는 경로와 errno를 싣고 `load.ts`는 싣지 않는다. 진단에 값을 싣지 않는다는 규칙이 두 곳에서 다르다. (3) `make-key`가 쓰다 실패하면 잘린 키 파일이 남고 다음 실행은 `이미 파일이 있다`고만 말한다. (4) `HEAD /portal/health`가 405다. (5) `serve.ts`가 서면 `error` 처리기를 떼고 요청 콜백의 동기 예외를 잡지 않는다. 지금은 `health`만 있어 던질 곳이 없고 05가 끝점을 더할 때 문제가 된다. (6) RSA 키 길이의 하한이 없다.
- 밀어 달라고 한 주장 판정(서브에이전트): 3.0.79는 02 브랜치의 푸시된 커밋(`origin/feature/02-e2e-stack-package`)에도 이미 있었다(앞의 "셀프 리뷰"와 "인계"가 이 값을 "02 워크트리의 미커밋 README"에서 읽은 것으로 적은 것은 틀렸다. 판 README 문장 자체는 그대로 맞다). `cookie`가 `; `로 이어진다는 것은 서버를 띄운 프로브를 못 돌려 확인하지 못했다(`cookies.ts`는 `;`로 쪼개 `trim`하므로 동작은 같다). `identityOf`는 코드를 읽어 맞다. `make-key`의 `wx`와 0600은 코드를 읽어 맞다. 진단이 값을 싣지 않는다는 주장은 위 (1)과 (2) 때문에 예외가 둘 더 있다.