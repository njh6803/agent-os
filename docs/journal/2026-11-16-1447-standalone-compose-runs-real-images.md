# 단독 compose가 실제 이미지 넷과 프록시로 뜨고, 브라우저 시험이 그 배치를 잠근다 (release-image 티켓 09)

브랜치 `feature/09-standalone-compose-runs-real-images`. 이 세션은 구현과 이 PC에서 돌려 보는 확인, 프로브 재측정까지 하고 셀프 리뷰 직전에 컨텍스트가 문턱을 넘어 인계한다. 커밋하지 않았고 변경은 모두 워크트리에 있다.

## 사용자 프롬프트 원문

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/release-image/issues/09-standalone-compose-runs-real-images.md
>
> 다음 작업: .scratch/release-image/issues/09-standalone-compose-runs-real-images.md. 단독 compose가 실제 이미지 넷과 프록시로 뜨고, 브라우저 시험이 그 배치를 잠근다
> 다음 단계: 구현
> 어디서: 새 세션. (tidy-checkouts를 먼저 돌고 EnterWorktree로 새 워크트리에 들어간다)
> 시작 프롬프트: /implement .scratch/release-image/issues/09-standalone-compose-runs-real-images.md
> 브랜치: feature/09-standalone-compose-runs-real-images
> 모델: Sonnet 5.5 / high
> 이어받을 상태: 없음. 07(PR 585)과 08(PR 584)이 병합되어 Blocked by 04·07·08이 풀렸다. serve 이미지의 기본 CMD에는 --model과 --host가 없어 compose의 command:로 --model만 덧붙이면 안 된다.
> 이번 요청 범위: PR과 병합까지

사용자의 다른 말은 없었다. 병합은 이 워크트리 사본의 `next-session/merge.md` "워크트리에서 병합할 때"를 Read로 열어 따른다. 형제 06(PR 589)은 다른 세션이 맡아 열려 있다.

## 한 것

- `deploy/standalone/`: `compose.yaml`(이름 `agent-os`, 다섯 서비스, 발행 포트는 프록시 `0.0.0.0:443:8443`·`0.0.0.0:80:8080`과 관리 화면 `127.0.0.1:3000`뿐), `proxy/nginx.conf`·`proxy/site.conf`(IPv4만 `listen`, `resolver 127.0.0.11 valid=5s ipv6=off`, `zone`·`resolve`가 든 `upstream`, 토큰 끝점 빈도 제한 30r/m burst 10 → 429, HSTS, 80 → 443 308, 허용 목록 밖은 404), `.env.example`(`@AGENT_OS_VERSION@`·`@AGENT_OS_NAMESPACE@`), `site/sites.toml`, `portal/portal.toml`, `tls/README.txt`, `portal/keys/README.txt`. 프록시는 `nginx -c /etc/agent-os/proxy/nginx.conf`로 설정 폴더를 `:ro`로 얹는다.
- `web/packages/e2e-standalone/`(`@agent-os/e2e-standalone`): Playwright 시험 패키지. `e2e/stack.ts`(globalSetup)가 이미지 넷을 짓거나(`agent-os-e2e/<이름>:0.1.0-rc.1`) 환경 변수 `AGENT_OS_STANDALONE_NAMESPACE`·`AGENT_OS_STANDALONE_VERSION`으로 받은 이미지를 쓰고, `tools/release.py bundle`로 묶음을 지어 풀어 인증서·키·사이트 파일·설정을 채워 `compose up --wait` 한다. 프로젝트 이름은 실행마다 `agent-os-e2e-<hex>`이고 끝나면 로그를 저장한 뒤 `down --volumes --remove-orphans`로 그 실행의 것만 지운다. 호스트 포트 443·80·3000이 고정이라 시작 전에 비어 있는지 보고 시험은 한 워커로 차례로 돈다. 토큰 끝점 429 사례는 마지막에 돈다(빈도 제한이 IP마다라서).
  - 픽스처 에이전트(`echo`)는 시험 전용 덧씌움 `compose.fixtures.yaml`의 `fixtures` 서비스(serve 이미지, 같은 볼륨 경로)가 uid 10001로 복사한다. 이름 있는 볼륨의 첫 채움과 소유를 깨지 않는다(티켓 S6). `e2e-stack`의 `writeEchoAgent`를 새로 내보냈다.
  - 사례 열둘(`e2e/deployment.e2e.ts`): 위젯 미리보기 페이지가 CSP 위반 없이 그려지고 토큰 CSS와 글꼴이 받아진다, 고지를 확인한 최종 사용자의 질문에 답한다(`출력: chars:N`), 80 → 443 308과 HSTS, 허용 목록 밖과 우회 시도는 404, 관리 화면은 `127.0.0.1:3000`으로만 닿고 프록시의 `/api`는 404, Docker가 보고한 발행 포트가 80·443·3000뿐이고 3000은 루프백에만 묶인다, 컨테이너 사용자가 root가 아니고 `agent-os --version`이 묶음의 판과 같다, 관리 화면 중계가 관리 토큰으로 플러그인을 켜고(204) 토큰 없이는 401, 계산 에이전트의 실행이 도구 연결이 아니라 모델 호출에서 끝난다(네트워크 없는 MCP), `docker run --network none`으로 `--host 0.0.0.0`에 띄우면 0이 아닌 코드로 끝난다, 포털을 다시 만들면 15초 안에 200, 토큰 끝점 몰아치기는 429.
  - 실제 모델 묶음 `e2e/calc.llm.ts`: 환경 변수 `AGENT_OS_STANDALONE_LLM=1`과 `ANTHROPIC_API_KEY`가 있을 때만 프로젝트 `llm`이 선다. CI 잡은 켜지 않는다. 이름은 `docs/constitution/operations.md` LLM 테스트 절에 적었다.
  - 환경 변수 `AGENT_OS_STANDALONE_NO_IPV6=1`은 `compose.no-ipv6.yaml`(프록시·serve·관리 화면·위젯·위젯 미리보기 페이지의 `net.ipv6.conf.all.disable_ipv6: "1"`)을 덧씌운다.
- `tests/tools/test_web_images_manifests.py`: 세 Dockerfile의 `manifests` 단계 `COPY` 목록이 `web/pnpm-workspace.yaml`의 워크스페이스 패키지 전부와 같은지, `corepack prepare pnpm@<판>`이 `web/package.json`의 `packageManager`와 같은지 본다(Docker 없이). 변이 시험 둘 포함 네 개. 세 Dockerfile의 `manifests`에 `packages/e2e-standalone/package.json`을 더했고 `web/pnpm-lock.yaml`에 그 패키지의 importer가 생겼다.
- `.github/workflows/ci.yml`: 새 잡 `e2e-standalone`(ubuntu, uv, node 24, pnpm, Playwright 브라우저 캐시, `pnpm -C web/packages/e2e-standalone exec playwright test`, `timeout-minutes: 45`는 첫 값 어림). main으로 가는 PR과 main 푸시에서만 시험하고, 건너뜀을 빨강으로 읽는 `verify` 때문에 잡을 건너뛰지 않고 첫 단계(`gate`)에서 판정해 뒤 단계를 가른다(셀프 리뷰 반영). `verify`의 `needs`에 넣고 머리 주석의 개수를 일곱 → 여덟으로, 실제 이미지의 compose e2e가 아직 없다던 문장을 고쳤다. `pr-title.yml` 머리 주석의 "무거운 잡 일곱"도 여덟으로 고쳤다.
- 개수와 문서: `docs/constitution/tech.md`·`operations.md`(검사 여덟 잡, 잡 이름, LLM 테스트 절에 단독 배포 실제 모델 시험), `CLAUDE.md`(검증 명령의 web 괄호에 단독 e2e 명령과 조건, 게이트 열아홉, CI만 도는 다섯), `.claude/skills/next-session/merge.md` 74행(출시 PR이 같은 검사 여덟 잡과 `verify`를 다시 지나며, main으로 가는 PR과 main 푸시에서만 실제로 도는 검사는 `llm` 잡과 단독 배포 e2e 잡의 시험이다. 셀프 리뷰를 반영하며 고친 문장이다). 고치기 전에 `writing-for-agents`를 불렀다.
- 헌법 판 3.0.103 → 3.0.104(`docs/constitution/README.md`, 마지막 개정 2026-11-16). 까닭: `operations.md`에 CI 검사 개수·잡 이름과 단독 배포 실제 모델 시험 절이 생겼다. `tools/sibling_overlap.py`를 쳤다: 형제가 쓴 가장 높은 헌법 판 3.0.103(origin/dev), 번호 겹침 없음, 함께 고친 파일 없음.
- 카나리아 명세 `.scratch/harness/probes/canary/next_session_ci_job_count.toml`(새 파일): 고친 `merge.md`가 새 세션에 실리는지. 2026-11-16 통과 4 · 실패 0, "없음" 섞인 통과 0. 고친 문장("검사 여덟 잡", "`llm` 잡과 단독 배포 e2e 잡의 시험")으로 다시 돌린 결과다. 실험군 3/3이 새 문장을 옮겼고 대조군 1/1이 옛 판 "검사 일곱 잡"을 옮겼다(대조군 커밋 `aa215fa3b`). 앞서 돌린 판은 셀프 리뷰가 문장을 고치기 전의 것이라 갈음하지 않는다.
- 프로브: `proxy_config/run.py`(빈 열쇠 회차는 429마다 오류 기록에 `portal_token` 구역의 거부 줄이 있을 때만 측정으로 센다, 대조군 `direct.conf`는 실패의 까닭이 `host not found in upstream`일 때만 측정으로 센다), `bridge_edge/run.py`(양성 대조의 대상이 실제로 답하는 쪽, admin·serve·portal일 때만 그 대상의 공격 회차를 센다). 두 README의 결과·"잰 판"과 `bridge_edge` README의 "PR 직전 리뷰가 좁힌 측정 조건(2026-11-14)" 절에 다시 돈 날짜와 결과를 적었다.

## 이 PC에서 돌린 결과

이 PC는 Docker Desktop(바깥 Engine 29.9.2, WSL2)이다. 다른 세션의 일이 함께 돌았는지는 재지 않았다.

- 단독 e2e 전체(이미지 넷을 지어 둔 뒤 캐시를 쓴 실행): 12 passed, 4.8분. 이미지 넷의 짓는 시간은 따로 재지 않았다(앞 단계의 백그라운드 빌드 출력에서 시간을 받아 두지 못했다). 08 일지에 `--no-cache`로 지은 시간이 있다(admin 163초, widget 155초, portal 50초). serve 이미지는 07 일지를 본다.
- IPv6 끈 실행: `AGENT_OS_STANDALONE_NO_IPV6=1 pnpm -C web/packages/e2e-standalone exec playwright test` → 12 passed, 3.8분(이미지는 캐시). 같은 옵션을 준 `debian:bookworm-slim`은 `disable_ipv6`이 1이고 `/proc/net/if_inet6`이 비었으며 옵션 없이는 0과 `lo`의 `::1` 한 줄이었다(손으로 봤다). e2e가 띄운 컨테이너 안의 값은 읽지 않았다(어림). 결과는 `proxy_config` README에 적었다.
- 실제 모델 한 번: `AGENT_OS_STANDALONE_LLM=1`로 13 사례 중 12 passed, 1 skipped(네트워크 없는 MCP 사례는 모델 모드에서 건너뛰게 만들었다), 49.9초(이미지 캐시). `calc.llm.ts`가 6.1초에 통과했다. 모델 호출 비용은 재지 않았다.
  - 처음 적은 명령 `uv run --env-file .env pnpm ...`은 윈도에서 uv가 `pnpm`을 띄우지 못해 `program not found`(exit 2)로 끝났다. 상대 경로 `--env-file=../../../../../../.env`는 node가 찾지 못했다(exit 9). 절대 경로로 되었다: `AGENT_OS_STANDALONE_LLM=1 pnpm -C web/packages/e2e-standalone exec node --env-file C:/project/agent/.env ./node_modules/@playwright/test/cli.js test`. `operations.md`의 명령을 `<루트>/.env` 꼴로 고쳤다.
- `proxy_config` 재측정: 측정 37회차, 측정 아님 0, 종료 코드 0. 값이 옛 README와 같았다.
- `bridge_edge` 재측정(`--sections 1,3,8 --engines 28.3.3`): 측정 134회차, 측정 아님 0, 종료 코드 0. 1·8·9절의 값이 그대로였고 항목 1이 28.3.3에서 다른 세 엔진과 같았다. 양성 대조(서버 자신 → admin·serve·portal 컨테이너)가 모두 기대한 대역으로 답했다. 항목 7과 다른 엔진은 돌지 않았다.
- 두 프로브 타입 검사 통과(`uv run pyright -p .scratch/release-image/probes/{bridge_edge,proxy_config}/pyrightconfig.json`, 0 errors). `uv run ruff check . && uv run ruff format --check .` 통과. `pnpm -C web verify`는 이 시점에는 IPv6 덧씌움 뒤로 다시 치지 않았다(아래 "검증"에서 셀프 리뷰 반영 뒤 통과를 적었다).

## 판단과 번복

- 카나리아는 `e2e-standalone` 낱말을 쓰지 않는다. 이 브랜치의 git 상태 경로(`web/packages/e2e-standalone/`)에 그 낱말이 실려 돌리기 전의 확인이 막기 때문이다. "검사 여덟 잡"과 "`llm` 잡과 단독 배포 e2e 잡의 시험"을 골랐다.
- 위젯 미리보기 페이지의 e2e처럼 `.env`는 세션이 읽지 않는다. 키는 node의 `--env-file`이 playwright 프로세스의 환경으로만 올린다.
- `pr-title.yml`의 "무거운 잡 일곱"은 티켓이 든 목록 밖에 남은 자리였다. grep으로 찾아 고쳤다. `tools/run_checks.py`의 "검사 일곱"과 `docs/adr`·`docs/journal`의 일곱은 pre-commit 훅 개수이거나 기록이라 고치지 않았다.
- 계산 에이전트 사례(네트워크 없는 MCP)는 모델 호출이 실패해도 통과해야 하므로 끝이 `failed`이고 원인이 `model_call`이며 `tool_connection`이 아닌 것으로 단언한다. 모델 모드에서는 이 사례가 건너뛴다.
- 티켓: 체크박스 31개를 모두 채우고 `Status: done`으로 바꿨다. 아래 남은 일이 빨강이면 되돌린다.

## 셀프 리뷰 (`/code-review`, 기준 `origin/dev`, 표준 축과 명세 축)

Critical은 없었고 Major가 셋이었다. 고친 것:

- **Major, CI 잡이 모든 PR과 푸시에서 돌았다**: 티켓과 명세는 main으로 가는 PR과 main 푸시에서만 돌라고 했다. 잡 수준의 `if:`로 건너뛰면 `verify`가 건너뜀을 빨강으로 읽으므로, 잡 첫 단계에 판정 단계(`gate`)를 두고 뒤 단계마다 `steps.gate.outputs.run == 'true'`를 걸었다. 이벤트 값은 `env`로 넘겨 zizmor 규칙(스크립트 안 직접 보간 금지)을 지켰다. `timeout-minutes: 45`는 첫 값의 어림이고 근거를 그대로 적었다.
- **Major, 개수 문서와 카나리아가 어긋났다**: `merge.md`·`ci.yml` 머리·`http.md`·카나리아 명세가 "main에서만 도는 검사"를 서로 다르게 말했다. 넷을 같은 문장(`llm` 잡과 단독 배포 e2e 잡의 시험)으로 맞췄고 카나리아를 고친 판으로 다시 돌렸다(위 4/4).
- **Major, 플러그인 사례가 쓰기를 지나지 않았다**: 이미 켜진 플러그인을 켜는 요청은 볼륨에 쓰지 않고 204이다. 끄고 켜는 두 요청이 모두 204인지 본다.
- 발행 포트 사례에 80·443이 `0.0.0.0`에 묶이고 루프백에 갇히지 않는지를 더했다.
- 렌더 사례에 응답 상태 400 이상 수집과 불러온 글꼴 면이 하나 이상인지를 더했다. 처음 쓴 `[...document.fonts]`는 `face`를 `any`로 읽어 ESLint(`no-unsafe-member-access`)가 막았고, `forEach`로 바꿨다.
- `tests/tools/test_web_images_manifests.py`는 작업공간 묶음을 `web/pnpm-workspace.yaml`의 `packages:`에서 읽는다(시험 하나 추가, 다섯 개 통과).
- `operations.md`의 "끝까지 본다"를 `calc.llm.ts`가 실제로 단언하는 것(`finished`와 `llm_called`)으로 고쳤다. 사례 안의 같은 표현도 고쳤다.
- `proxy_config` README: 표지가 옛 판의 헛된 통과를 걸러 냈는지는 옛 판과 비교하지 않았으므로 **어림**으로, 단독 e2e 12 passed는 프로브 밖에서 보고를 읽었으므로 **손으로 봤다**로 바꿨다.
- `bridge_edge` README: 새 검사는 보호를 끈 네트워크의 대조용 컨테이너가 자기 안에서 답하는지(`answers`) 하나뿐이다. admin·serve·portal이 답하는지 걷는 검사는 이전 판에 이미 있었다. 귀속을 바로잡고 효과는 **어림**으로 적었다.
- 루트 `README.md`의 트리에 `deploy/standalone/`과 `e2e-standalone`을 올렸다.

남긴 것(Nit, 이유):

- `Compose` 생성과 포트 상수의 중복, `ensure`의 이름: 동작과 무관한 정리라 이 티켓에서 건드리지 않았다. 10이 같은 파일을 만지면 그때 합친다.
- serve의 `env_file`이 판과 이름공간 값을 함께 넘기는 것을 문서에 더 적자는 제안: `.env.example`의 주석이 이미 설명한다.

## 검증

- `uv run ruff check . && uv run ruff format --check .`: 통과.
- `uv run pyright`(바뀐 시험 파일): 0 errors.
- `pnpm -C web verify`: 렌더 사례를 고친 뒤 통과(ESLint 한 건을 고친 다음).
- 단독 e2e: 셀프 리뷰 반영 뒤 두 번 12 passed(4.0분, 5.6분. 이미지는 캐시, 다른 세션이 함께 돌아 시간이 흔들렸다). 이미지를 처음부터 짓는 시간은 이 세션에서 재지 않았다(위 결과 절의 이유).
- `uv run python tools/run_checks.py`: 7740개 가운데 2개 실패(`tests/channel/cli/test_interrupt.py`의 닫는 도중 Ctrl+C 사례, `tests/tools/test_rerun_runner.py`의 오염 두 번 사례), web-verify 통과. 한 바퀴가 18분 39초로 평소보다 길었고 이 PC에 다른 세션이 함께 돌았다. 두 시험은 실제 프로세스·기한을 재는 것이고 이 브랜치가 건드린 파일이 아니다. 둘만 홀로 다시 치니 2 passed(103초). `.claude/rules/tests.md`가 말한 부하 아래의 시간 단언 흔들림으로 보지만, 원인을 부하로 가려내는 비교는 하지 않았다(어림). 같은 시험이 병합 전에 CI에서도 빨개지면 diagnosing-bugs로 간다.
- `.claude/rules/http.md`를 고쳐서 그 규칙을 원천으로 든 카나리아 셋(`http_rule_continuation_422`, `http_rule_pre_owner_damage`, `http_rule_llm_widget`)을 새 `claude -p` 세션에서 다시 돌렸다: 셋 모두 통과 4 · 실패 0 · "없음" 섞인 통과 0. 세 명세의 "최신 결과" 줄을 고쳤다. 처음에는 `.scratch/harness/probes/canary/` 아래에 있다고 잘못 적어 명세를 읽지 못했고(종료 2, 아무것도 돌지 않았다), 이어 명세의 "돌리는 법"에 없는 `--control-commit`을 주어 도구가 거절했다. `Glob`으로 실제 위치를 찾고 "돌리는 법" 그대로 쳤다.
- 사진 비교와 `-m llm` 계열은 이 변경의 범위 밖이라 치지 않았다. 실제 모델 단독 e2e는 위 결과 절의 한 번이 전부다.

## 남은 일 (병합하는 세션이 한다)

- 이 일지의 `## 다음`은 병합하는 세션이 쓴다. 회고는 병합 세션이 돈다.
- 티켓 09는 마지막 열린 티켓이 아니다(10·11이 남았다). 기능 계획의 `**끝:**` 줄과 기능 단락은 적지 않는다.
- 10이 받을 것: 프록시의 `nginx -t`·`nginx -s reload`는 `-c /etc/agent-os/proxy/nginx.conf`를 줘야 한다(설정 폴더를 그 경로에 얹었다). 호스트 포트 443·80·3000이 고정이라 같은 PC에서 두 배치를 동시에 띄울 수 없다. 모델 호출 사례의 `ANTHROPIC_API_KEY` 이름은 `.env.example`과 `operations.md` 둘에 있다.
- `mcp__ccd_session_mgmt__get_session self`에는 `parentSessionId`가 없다(곁 세션이 아니다).

- open-session을 부른다 2026-11-16T05:48Z

- 인계 못함 셀프 리뷰 직전: open-session의 send 호출(tools/open_session.ps1)을 자동 모드 분류기가 거부했다(이유 없음). 제목은 되돌렸고 이 세션이 셀프 리뷰부터 잇는다. 워크트리 잠금은 이미 풀었고 다시 잠그지 않는다. 멈춘 run_checks는 다시 띄운다.
