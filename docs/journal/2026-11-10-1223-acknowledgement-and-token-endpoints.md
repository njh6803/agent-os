# 2026-11-10 (12:23) 사이트마다 고지 확인 끝점이 익명 식별자 쿠키를 주고, 토큰 끝점이 그 쿠키로 사이트 토큰을 낸다 (pilot-portal 05)

세션 제목 `feature/05-acknowledgement-and-token-endpoints`. 브랜치 같은 이름, 워크트리 `.claude/worktrees/05-acknowledgement-and-token-endpoints`(기준 `2402362d`, 첫 줄은 `tidy-checkouts`가 루트를 당긴 뒤의 `origin/main`). 모델 Sonnet 5.5 / high(지시문).

## 사용자 프롬프트

> .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/pilot-portal/issues/05-acknowledgement-and-token-endpoints.md
>
> 다음 작업: .scratch/pilot-portal/issues/05-acknowledgement-and-token-endpoints.md. 사이트마다 고지 확인 끝점이 익명 식별자 쿠키를 주고, 토큰 끝점이 그 쿠키로 사이트 토큰을 낸다
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 05-acknowledgement-and-token-endpoints)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/pilot-portal/issues/05-acknowledgement-and-token-endpoints.md
> 브랜치: feature/05-acknowledgement-and-token-endpoints
> 모델: Sonnet 5.5 / high
> 읽을 것: docs/journal/2026-11-10-1015-portal-server-starts-after-checking-config.md의 "다음"(05가 맡을 설정 파일 정리 Minor 넷과 serve.ts 처리기 예외를 정할지 포함)
> 이어받을 상태: 없음
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: 구현·리뷰·커밋까지

이 세션에서 사용자가 더한 말은 없었다.

## 두 번째 세션 (셀프 리뷰, 커밋, PR 준비)

세션 제목 `feature/05-acknowledgement-and-token-endpoints`. 첫 세션의 인계 지시문(`인계: 셀프 리뷰 직전`, 범위 "구현·리뷰·커밋까지")으로 열렸다. 같은 워크트리에 `EnterWorktree(path)`로 들어갔다. 사용자의 말:

> .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. … 인자: .scratch/pilot-portal/issues/05-acknowledgement-and-token-endpoints.md
> (이어받을 상태) 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다.
> (이번 요청 범위) 구현·리뷰·커밋까지

커밋 뒤 사용자가 범위를 넓혔다(원문):

> pr 병합까지

한 일: 셀프 리뷰(위 "셀프 리뷰"), 반영, 티켓 `done`과 `plan_table.py`, 커밋 `feat: …(pilot-portal 05)`, `origin/main`(`a9d7d942`)으로 rebase(충돌은 `probes/README.md`의 표 행 둘 다 남기기), rebase 뒤 전체 러너 통과, PR 직전 CodeRabbit CLI(지적 0), 회고와 "다음" 절, 일지 커밋. 컨텍스트가 문턱(20만 토큰)을 넘은 `커밋 뒤` 경계라 새 세션에 인계한다. 아직 푸시하지 않았고 PR도 없다. 이 절 추가는 커밋하지 않았다.

## 한 일

- `tidy-checkouts`: 루트가 main이고 깨끗해 `c4af6063`에서 `2402362d`로 당겼다. 병합된 `feature/01-site-file-package-and-ui-subpaths`와 `docs/pilot-portal-screens`의 워크트리와 브랜치, 병합된 `worktree-02-e2e-stack-package` 브랜치를 지웠다(쉬는 세션이 쥔 둘은 `end-holders`로 그 세션의 프로세스를 끈 뒤 지웠다). 휴지통 둘(`.claude/worktrees/.tidy-trash/`의 `node_modules`)은 다른 프로세스(`node.exe` 14504, `esbuild.exe` 30772·34812)가 `esbuild.exe`를 쥐어 지우지 못하고 남았다. 그 프로세스가 끝난 뒤의 정리가 다시 비운다.
- 티켓 05 `Status`를 `in-progress`로 바꿨다(첫 편집).
- 순수 처리기를 `handle(request, context)`로 바꾸고 끝점 셋을 더했다(`server/handler.ts`).
  - `GET …/acknowledgement` 200 `{"acknowledged":…}`, `POST …/acknowledgement`는 `Origin`이 공개 출처와 글자 그대로 같을 때 204와 `Set-Cookie`, 아니면 쿠키 없이 403.
  - `POST …/token`은 꼴이 맞는 쿠키가 있으면 200 `text/plain` 토큰과 같은 값의 `Set-Cookie`, 없으면 401 "고지 확인이 필요합니다.". `Origin`은 보지 않는다.
  - 보증 모드가 `login`인 사이트의 세 끝점은 메서드·쿠키와 상관없이 403. `both`는 `anonymous`와 같다. 모르는 사이트 이름과 끝점은 404, 아는 끝점의 다른 메서드는 405와 `Allow`(확인은 `GET, POST`, 토큰은 `POST`). `/portal/sites/` 아래 모든 응답에 `Cache-Control: no-store`.
- 새 모듈: `server/anonymous-cookie.ts`(쿠키 이름 `portal_anon`, 소문자 UUID v4 판정, 같은 이름이 여럿이면 첫 것, `Set-Cookie` 짓기. `Secure`는 `https` 공개 출처일 때만), `server/token.ts`(RS256 JWT 서명과 익명 주체 이름 `anon-<SHA-256 앞 32자>`), `server/context.ts`(시작 검사를 지난 결과에 사이트 파일의 `audience`를 발급자로 맞대 붙이고 시계와 UUID 만들기 자리를 받는 `PortalContext`와 `portalContext`).
- `tools/start.ts`가 `portalContext`로 처리 값을 짓고 `listen((request) => handle(request, context), …)`로 건다. `serve.ts`는 처리기가 던진 예외를 500 `SERVER_ERROR`로 바꾸고 오류의 이름만 stderr에 남긴다.
- 시험 픽스처 `testing/fixtures.ts`의 `SiteSpec`에 선택 칸 `audience`를 더했다(주지 않으면 `agent-os`).
- 변이 표 `.scratch/pilot-portal/probes/endpoints_mutations.toml`(19개)과 그 `README.md` 행, 루트 `README.md` 트리 문장.
- 06 티켓에 "05가 넘긴 메모"를 더했다(처리기의 새 모양, `PortalContext`에 없는 사이트 값, `serve.ts`의 예외 처리와 글꼴 스트림).

## 결정

- 설정 파일 정리 Minor 넷(`config.ts`의 출력 인자 변형, `start.ts`·`make-key.ts`의 실패 분기 되풀이, 오류 코드 뽑기 세 벌, `textOf`·`privateKeyOf`의 이름)은 이 티켓에서 맞추지 않았다. 이 티켓은 `config.ts`와 `make-key.ts`를 건드리지 않고 `start.ts`는 처리 값을 짓는 몇 줄만 더했다. 티켓 체크박스에도 없는 일이라 스킬의 "요구하는 것만 쓴다"를 따랐다. 아래 "다음"에 남긴다.
- `serve.ts`의 처리기 예외는 이 티켓이 끝점을 더하면서 던질 곳이 생겨(서명, 쿠키 판정) 한 요청이 프로세스를 죽이지 않도록 500으로 받게 했다. 선 뒤의 서버 `error`는 처리기를 두지 않고 프로세스가 죽는 것으로 두었고 그 까닭을 `serve.ts` 주석에 적었다(듣던 소켓이 깨진 서버는 요청을 받지 못하니 프로세스 관리자가 다시 띄운다).
- `site-file` 패키지의 보류 넷(`siteFileInput` 공개 표면, `site-file.ts` 약 600줄, `origins`·`allowedOrigins` 중복, 위젯 전용 값)은 고치지 않았다. 이 티켓은 `@agent-os/site-file`을 읽기만 한다(`SiteFile.sites[].audience`).
- `anonymousCookie`는 `secure: boolean` 위치 인자였다가 린트(`no-restricted-syntax`, 불리언 매개변수)에 걸려 `{ id, siteName, secure }` 옵션 객체로 바꿨다. 셀프 리뷰가 그 옵션 객체의 불리언 칸도 `CODING_STANDARDS.md`가 열거로 두라는 자리라고 짚어, 지금은 `{ id, siteName, publicOrigin }`이고 `Secure` 판정이 쿠키 모듈 안에 있다.

## 확인한 것

- 빨강 먼저: 시험 다섯 파일(`token`, `anonymous-cookie`, `handler`, `context`, `serve`)을 구현 전에 돌려 25개 실패와 10개 통과를 보았다. 대부분은 모듈이 없어서라 로직의 빨강이 아니다. 로직의 빨강은 `tools/mutate.py`로 얻었다. 변이 19개를 `endpoints_mutations.toml`에 적고, 표지를 맞지 않는 값(`§§없는표지§§`)으로 바꾼 사본으로 한 번 돌려 `표지 없음` 줄 밑의 실제 실패 출력을 읽고 표지를 골랐다. 표지를 넣은 판으로 다시 돌려 `변이 19 모두 기대대로`(종료 코드 0)를 보았다. 변이는 `Origin` 검사 둘, 쿠키 판정 여섯, 토큰 여섯, 로그인 사이트와 `no-store`, `audience` 찾기, 서버 겉의 예외 다시 던지기다.
- `serve.test.ts`의 마지막 사례는 처음에 응답이 오지 않아 시험의 시간 제한 60초까지 걸려 빨갰다. 클라이언트에 5초 제한(`setTimeout`)을 더해 빨강이 빨리 나게 했고, 변이 19의 표지는 그 제한이 낸 `Error: 응답이 없다`다.
- 포털 시험 전체(`pnpm -C web/apps/portal exec vitest run`)는 초록이다(마지막 실행 기준 로그에서 종료 코드 0. 수는 반영 전 실행에서 156개 통과, 1개 건너뜀이었다). `pnpm -C web run typecheck`와 `pnpm -C web exec eslint apps/portal`은 종료 코드 0이고 prettier로 두 파일(`handler.test.ts`, `serve.ts`)의 줄바꿈을 정리했다. `uv run ruff check .`와 `uv run ruff format --check .`는 통과했다.
- 실제 소켓: 임시 폴더에 `make-key`로 키를 만들고 설정과 사이트 파일을 써서 `pnpm -C web/apps/portal start -- --config … --site-file …`로 포트 18811에 띄워 `curl`로 불렀다. 쿠키 없는 `GET …/acknowledgement` 200 `{"acknowledged":false}`, `Origin: http://evil.example`의 `POST …/acknowledgement` 403 "허용하지 않는 출처입니다."(쿠키 없음), 같은 출처의 `POST` 204와 `Set-Cookie: portal_anon=<UUID>; HttpOnly; SameSite=Strict; Path=/portal/sites/demo; Max-Age=2592000`, 그 쿠키 항아리로 `POST …/token` 200과 같은 값의 `Set-Cookie`와 JWT 세 토막(헤더 `kid`가 `portal-1`), 쿠키 없는 토큰 401, `gate`(login) 사이트의 `POST …/acknowledgement` 403 "이 사이트는 로그인이 필요합니다. 로그인은 아직 제공하지 않습니다.", 모르는 사이트 이름의 토큰 404, `GET …/token` 405 `Allow: POST`. 서버의 stdout은 시작 로그 한 줄뿐이었다. 끝난 뒤 그 포트를 쥔 `node` 프로세스(명령 줄이 이 세션이 띄운 `tools/start.ts`와 일치)만 `Stop-Process`로 끝냈고 듣는 연결이 0이 된 것을 확인했다.

## 셀프 리뷰 (두 번째 세션, 기준 `2402362d`, 수정 9개·미추적 9개·커밋 0개)

표준 축은 sonnet·high, 명세 축은 세션 모델이 돌았다. 아래 두 축의 판정은 서브에이전트의 보고이고(각자 포털 시험을 돌려 156 통과·1 건너뜀을 보았다고 했다), 이 세션이 직접 다시 본 것은 변이 표의 `--check`와 변이 전체 실행, 포털 시험, 린트·타입체크, 그리고 `handler.ts`·`anonymous-cookie.ts`·`serve.ts` 읽기다. 두 축 모두 코드 결함은 내지 않았고, 명세 요구의 누락도 없다고 했다(클레임 다섯, `exp-iat` 120, `sub` 해시, 쿠키 속성, 405 `Allow`, 로그인 403 본문, 인계 메모의 판단 셋이 명세와 맞는다고 명세 축이 보고했다).

고친 것:
- **Major(두 축이 같은 것을 냄).** 변이 표 14번의 `old`(`anonymousCookie(id, site.name, secure(context))`)가 코드에 없었다. `anonymousCookie`를 옵션 객체로 바꾸고 `cookieFor`를 뽑으며 표가 따라가지 않았고 `--check`가 "변이 19 중 문제 1"이었다. 표를 맞췄고(`cookieFor(id, site, context)`) `--check`가 19개 원문이 한 번씩 있다고 답했다.
- **Minor, 문서화된 표준(`CODING_STANDARDS.md` "불리언 플래그 인자를 만들지 않는다": 갈래를 고르는 인터페이스의 불리언 칸은 열거로).** `CookieSpec.secure: boolean`을 `publicOrigin: string`으로 바꾸고 `Secure` 판정(`startsWith("https://")`)을 `anonymous-cookie.ts` 안으로 옮겼다. 변이 표의 `Secure` 변이 둘(6번, 7번)도 따라 고쳤다(7번의 대상 파일이 `handler.ts`에서 `anonymous-cookie.ts`로 바뀌어 이름도 "쿠키가 https 를…"로 고침).
- 고친 뒤 변이 19개를 실제로 다시 돌려 `변이 19 모두 기대대로`(종료 코드 0)를 보았다. 포털 시험 156 통과·1 건너뜀, `pnpm -C web run typecheck`·`eslint apps/portal`·`prettier --check apps/portal` 모두 출력 없이 통과.

남긴 것과 이유:
- 경로 모양 `/portal/sites/<이름>`이 `handler.ts`(`SITES_PREFIX`·`SITE_ENDPOINT`)와 `anonymous-cookie.ts`(`Path=/portal/sites/${siteName}`)에 따로 있다(Minor). 핸들러 시험이 사이트 `demo`의 쿠키 `Path`를 `Path=/portal/sites/demo`로 글자 그대로 본다(`handler.test.ts` 138·298행, grep으로 봤다). 06이 페이지 경로를 더하면 같은 모양이 또 나오므로 그때 한 곳으로 모은다.
- `serve.ts` `flatten`의 `Array.isArray` 갈래(Minor). `IncomingHttpHeaders`의 값 타입이 `string | string[] | undefined`라 타입 단언 없이 한 글로 만들려면 필요하다(`@types/node`의 `IncomingHttpHeaders extends NodeJS.Dict<string | string[]>`, `http.d.ts` 50행을 grep으로 봤다. 원칙 III).
- `serve.ts` `answer` 주석이 `writeHead`가 던지는 경우를 덮는 것처럼 읽힐 수 있다(Minor). 주석 제목이 "처리기가 던져도"라 범위를 말하고 있어 그대로 두었다.
- `(request, context, site)` 세 인자가 함께 다닌다는 Data Clumps(판단 항목). 세 함수에 그치고 06이 쓸 값이 아니라 두었다.
- 명세 축의 범위 넘침 셋(`serve.ts`의 500 경로, 변이 표와 README 행, 06 티켓의 "05가 넘긴 메모")은 근거가 있어 둔다. 500 경로는 04 일지 "다음"이 05가 정하라고 넘긴 판단이고 이 티켓이 서명과 쿠키 판정으로 던질 곳을 만들었다. 변이 표는 빨강을 본 적 없는 시험의 규약(`tools/mutate.py`)이고 06의 메모는 스킬이 시키는 넘기는 길이다.
- 명세 축이 짚은 약한 자리 둘: `tools/start.ts`의 출력에 비밀이 없는지 보는 시험은 없고(시작 로그는 한 줄뿐이다), `/portal/health`의 405에는 `no-store`가 없다. 뒤의 것은 04의 동작이고 명세 문장("끝점 응답")의 해석이라 이 티켓이 바꾸지 않는다.

## PR 직전 리뷰 (origin/main `a9d7d942` 위로 rebase한 뒤, 커밋 하나)

- rebase: `git rebase origin/main`에서 `.scratch/pilot-portal/probes/README.md` 한 파일만 충돌했다. 형제 02와 이 브랜치가 표 끝에 행을 하나씩 더한 자리라 표지 세 줄만 지워 두 행을 남겼다(`grep`으로 표지 0개와 두 행의 연속을 보았다). `README.md`는 자동으로 합쳐졌다.
- CodeRabbit CLI: `coderabbit review --agent --committed --base origin/main`이 18개 파일에서 끝까지 돌아 `review_completed`와 `findings: 0`을 냈다(서브에이전트의 보고, CLI 0.7.5, `auth status`는 `Seat: not assigned`·`Plan: Free`였다). 이 세션이 그 명령을 다시 치지는 않았다.
- 같은 서브에이전트가 보안 축을 따로 코드를 읽어 보았고(CLI 결과가 아니라 서브에이전트가 읽은 것이다) 유효나 보류 항목은 없다고 했다. 쿠키 속성과 `Set-Cookie`에 사이트 이름이 끼어드는 길(`config.ts`의 `NAME_SHAPE`가 시작 때 막는다), `Origin` 검사, 접근 로그와 오류 출력에 비밀이 실리는 길, 개인 키가 응답에 실리는 길을 보았다.
- 고친 것 없음. 남긴 것은 위 "셀프 리뷰"의 Minor 넷 그대로다.

## 하지 않은 것

- `sync-design-system 확인`은 웹 편집 훅이 알렸지만 돌리지 않았다. 이 티켓은 화면 코드도 디자인 토큰도 건드리지 않는다(서버 코드와 시험, 픽스처).
- 관리 화면·위젯 e2e와 사진 비교는 돌리지 않았다(그 앱의 변경이 없다).
- 이 세션이 띄운 `uv run python tools/run_checks.py`(백그라운드)는 인계 계기가 오기 전에 끝나지 않았고 이 세션은 그 결과를 읽지 못했다. 인계하며 멈춘다. 새 세션이 셀프 리뷰를 반영한 뒤 커밋의 pre-commit(러너)과 필요하면 같은 명령으로 갈음한다.
- (옮김) 티켓 05는 두 번째 세션이 셀프 리뷰를 반영한 뒤 체크박스를 채우고 `Status`를 `done`으로 바꿨고 `uv run python tools/plan_table.py`를 돌려 `.scratch/plan.md`까지 같은 커밋에 싣는다(05는 기능의 마지막 열린 티켓이 아니라 `**끝:**` 줄은 쓰지 않는다. 06~09가 열려 있다).

## 회고

후보 넷, 판정은 승인 0, 기각 3, 넘김 1이다. 대기열에 새로 쓴 항목과 회차를 더한 항목은 없다. `queue_open_rows.py`의 만료 대상도 없다(열린 100개, 만료할 항목 없음. 그 명령을 이 세션에서 쳤다).

- 이 PR의 변이 표 14번 원문이 인계 전의 리팩터링(`anonymousCookie` 옵션 객체화, `cookieFor` 뽑기)을 따라가지 않아 셀프 리뷰 두 축이 같이 Major로 잡았다: 기각. 커밋의 pre-commit `--staged`(`mutation tables` 검사)가 같은 어긋남을 알리므로 이미 있는 검사가 그 자리에서 잡는다. 이 세션에서 표를 고친 뒤 그 검사가 `Passed`인 것을 보았다. 인계 메모가 그 위험을 미리 적었던 것도 사실이나 새 문장을 더할 문턱(다섯 번째나 손상)에 못 미친다.
- `CookieSpec.secure: boolean`이 `CODING_STANDARDS.md`의 "불리언 플래그 인자를 만들지 않는다"에 걸려 표준 축이 잡았다: 기각. 리뷰가 잡도록 둔 기준을 어겨 리뷰가 잡은 사건이라 회차 셈에서 뺀다(retro 4단계). 린트가 보지 못하는 자리(갈래를 고르는 필드의 불리언)임을 그 표준 줄이 이미 적고 있어 검사로 옮길 수도 없다.
- 구현 중간 문장을 영어로 쓴 것을 훅이 두 번 알렸다: 기각. 알리는 훅이 있고 알린 뒤 한국어로 고쳤다(이미 있는 훅이 그 자리에서 알린 것).
- 웹 편집 훅(`tools/hook_web_edit_check.py`)이 `web/apps/portal/server/*.ts`처럼 화면이 없는 서버 코드의 편집에도 `sync-design-system 확인`을 권했다: 넘김. 사건은 있다(앞 세션 일지의 "하지 않은 것"과 이 세션의 편집 알림에서 두 번 알렸고 두 번 다 그 티켓이 화면을 건드리지 않아 돌리지 않았다). 훅이 `web/apps/<앱>/` 아래 모든 파일을 화면 코드로 읽는다는 것은 그 독스트링 1행과 75행을 읽어 확인했다. 그러나 고치는 길은 훅의 범위를 좁히는 것이라 retro 4단계의 넘김(훅을 좁히는 것)이다. 이 세션은 사용자의 "pr 병합까지" 요청 중이라 그 판정을 묻기 위해 병합을 멈추지 않고 마지막 보고에서 묻는다. 사용자가 답하면 이 항목을 대기열에 쓴다(지금은 쓰지 않았다).

## 다음

- 프런티어는 06 티켓(질문 페이지가 위젯을 그린다)이다. 05가 넘긴 메모가 06 티켓에 있다(처리기의 새 모양 `handle(request, context)`, `PortalContext`에 없는 사이트 값, `serve.ts`의 예외 처리와 글꼴 스트림). 06~09가 아직 열려 있고 05는 기능의 마지막 열린 티켓이 아니라 `**끝:**` 줄을 쓰지 않았다.
- 경로 모양 `/portal/sites/<이름>`이 `handler.ts`(`SITES_PREFIX`·`SITE_ENDPOINT`)와 `anonymous-cookie.ts`(`Path=/portal/sites/${siteName}`)에 따로 있다(셀프 리뷰가 낸 Minor). 06이 페이지 경로를 더하면 같은 모양이 또 나오므로 그때 한 곳으로 모은다.
- 설정 파일 정리 Minor 넷(`config.ts`의 출력 인자 변형, `start.ts`·`make-key.ts`의 실패 분기 되풀이, 오류 코드 뽑기 세 벌, `textOf`·`privateKeyOf`의 이름)과 `site-file` 패키지의 보류 넷은 05가 건드리지 않았다. `config.ts`나 `start.ts`를 더 고치는 티켓이 오면 그 전에 맞출지 정한다.
- `tools/start.ts` 출력에 비밀이 실리지 않는지 보는 시험은 없다(시작 로그는 한 줄뿐이고 `serve.ts`의 500 경로는 `serve.test.ts`가 본다). `start.ts`에 출력을 더하는 변경이 오면 그 시험을 같이 쓴다.
- 웹 편집 훅의 포털 서버 오탐은 위 회고의 넘김이고 사용자 답을 기다린다.

## 인계 메모 (새 세션이 이어서 볼 것, 처리됨)

(처리됨) 아래 일은 두 번째 세션이 셀프 리뷰, 반영, 커밋, rebase, PR 직전 리뷰, 회고까지 마쳤다. 위 "셀프 리뷰"와 "PR 직전 리뷰"와 "회고"가 그 결과다. 이 절은 인계 시점의 기록으로 남긴다.

- 셀프 리뷰(`/code-review`)부터 한다. 범위는 기준 `2402362d`와의 `git diff`와 미추적 파일(`web/apps/portal/server/{anonymous-cookie,token,context}.ts`와 그 시험, `serve.test.ts`, `.scratch/pilot-portal/probes/endpoints_mutations.toml`, 이 일지)이다. 표준 축은 sonnet·high, 명세 축은 세션 모델이다.
- 리뷰가 낼 만한 자리로 이 세션이 미리 본 것: (1) 로그인 사이트가 `GET …/acknowledgement`와 `POST` 외 메서드에도 403이라 405 `Allow`를 주지 않는다(티켓 "메서드와 쿠키와 상관없이"를 그대로 따랐다). (2) `handle`이 `/portal/sites/` 아래 404에도 `no-store`를 단다(명세 "끝점 응답(`/portal/sites/…`)"을 그대로 읽었다). (3) `anonymousIdOf`가 첫 쿠키의 꼴이 틀리면 뒤 것으로 넘어가지 않고 없는 것으로 본다(명세 "같은 이름이 둘 이상 실리면 첫 것을 쓴다"와 "꼴이 아니면 없는 것으로 본다"를 함께 읽은 판단).
- 반영 뒤: 티켓 05를 `done`으로 바꾸고(체크박스 `[x]`) `plan_table.py`를 돌린다. 커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`를 친다(형제 02가 README 트리와 `tech.md` 웹 행, 헌법 판을 먼저 병합했거나 병합할 수 있다). 커밋 뒤에는 푸시, PR, PR 직전 리뷰, `merge.md`의 순서다. 이번 요청 범위는 "구현·리뷰·커밋까지"라 커밋에서 멈춘다.
- 설정 파일 정리 Minor 넷과 `site-file` 패키지의 보류 넷은 아직 안 고쳤다(위 "결정").
- 변이 표 `endpoints_mutations.toml`은 구현 뒤 커밋하지 않은 작업 트리에서 두 번 돌았다. 커밋 뒤 `--check`가 pre-commit `--staged`로 알릴 수 있다. 표의 `old` 원문(`handler.ts`의 `Math.floor(context.now() / 1000)`, `startsWith("https://")` 등)은 반영 뒤 코드가 옮기면 따라 고친다.

open-session을 부른다 2026-11-10T03:26Z

open-session을 부른다 2026-11-10T04:26Z
