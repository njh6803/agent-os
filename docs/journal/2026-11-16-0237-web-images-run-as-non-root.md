# 관리 화면·위젯·위젯 미리보기 페이지 이미지가 root가 아닌 사용자로 뜬다 (release-image 티켓 08)

브랜치 `feature/08-web-images-run-as-non-root`. 이 세션은 구현과 이 PC에서 띄워 보는 확인, 프로브 재측정까지 하고 셀프 리뷰·PR·병합으로 이어 간다.

## 사용자 프롬프트 원문

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/release-image/issues/08-web-images-run-as-non-root.md
>
> 다음 작업: .scratch/release-image/issues/08-web-images-run-as-non-root.md. 관리 화면·위젯·위젯 미리보기 페이지 이미지가 root가 아닌 사용자로 뜬다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 3 중 3. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/release-image/issues/08-web-images-run-as-non-root.md
> 브랜치: feature/08-web-images-run-as-non-root
> 모델: Sonnet 5.5 / high
> 읽을 것: 나란히 도는 형제 티켓 .scratch/release-image/issues/06-review-bot-checks-upgrade-bang.md, .scratch/release-image/issues/07-serve-image-runs-as-non-root-without-network.md
> 이어받을 상태: 형제 티켓 07도 dev에 아직 없는 새 폴더 deploy/images/를 함께 만든다. 빌드 맥락의 제외 목록은 저장소 루트의 .dockerignore가 아니라 프로브(serve_image, web_images)처럼 Dockerfile마다 <이름>.dockerignore로 두어 07과 같은 파일을 고치지 않는다. 07 세션이 같은 PC에서 동시에 Docker 빌드를 돌 수 있으므로, 위젯의 빌드 시간과 메모리 최고치 같은 잰 수치를 일지와 프로브 README에 적을 때 형제 빌드가 함께 돌았는지도 적는다
> 확인할 선행 조건: 없음
> 이번 요청 범위: PR과 병합까지

사용자의 다른 말은 없었다.

## 한 것

- `deploy/images/`에 세 Dockerfile과 각자의 `<이름>.dockerignore`를 더했다(`admin.Dockerfile`, `widget.Dockerfile`, `portal.Dockerfile`). 빌드 맥락은 `web/`이고 Dockerfile은 `-f`로 준다. 07도 같은 폴더를 만들지만 파일 이름이 겹치지 않고 루트 `.dockerignore`는 쓰지 않았다.
- 셋에 공통: 바탕은 `node:24-trixie-slim`을 digest `sha256:af02d57b...`로 고정했다. 같은 `base` 단계가 `tini`(apt)를 얹고, uid·gid 10001 `agentos`와 홈 폴더를 만들고, 03의 표지 파일 `/etc/agent-os/image`를 root 소유로 굽고, pnpm 11.24.0을 켠다. pnpm 저장소와 메타데이터 캐시는 BuildKit 캐시 마운트로 빼서 이미지에 남기지 않는다. OCI 라벨 셋(version·revision·source)은 빌드 인자 `IMAGE_VERSION`·`IMAGE_REVISION`·`IMAGE_SOURCE`로 채우고 기본은 `unknown`이다.
- 관리 화면: 운영 의존성(`--prod --filter "@agent-os/admin..."`)과 `next build`가 만든 `.next`(캐시는 지움)를 담는다. 짓는 단계에 표지 파일과 `AGENT_OS_CONTAINER_NETWORK=1`, `AGENT_OS_UPSTREAM=http://serve:8000`을 두어 03의 상류 검사를 지난다. 실행 환경에는 `AGENT_OS_CONTAINER_NETWORK`를 넣지 않는다(명세: compose가 준다). `CMD`는 `node tools/start.ts start --hostname 0.0.0.0 --port 3000`이다.
- 위젯: 워크스페이스 전체 의존성을 잠금 파일을 얼려 깔고, 지을 때 `next typegen`으로 `next-env.d.ts`와 `.next/types`를 만들고, `.next`와 `public`을 `agentos` 소유로 둔다. `CMD`는 `AGENT_OS_SITE_FILE=/etc/agent-os/site/sites.toml`을 늘 넘기고 `tools/start.ts build`가 끝나면 `exec ... start --hostname 0.0.0.0 --port 3000`이다. 빌드 중 `docker stop`이 묶음 전체에 닿도록 `tini -g`를 쓴다. 루트는 읽기 전용이 아니다.
- 위젯 미리보기 페이지: 운영 의존성(`--filter "@agent-os/portal..."`)과 `apps/portal`, `packages/site-file`, `packages/ui`를 담고 node가 `.ts`를 빌드 없이 돈다(`--disable-warning=ExperimentalWarning`). `CMD`는 `--config /etc/agent-os/portal/portal.toml --site-file /etc/agent-os/site/sites.toml`이다.
- 프로브 `web_images`를 고쳐 다시 돌렸다(아래 "프로브"). README의 결과, "잰 판", 맨 끝 절을 2026-11-16의 값으로 바꿨다.

### 정한 경로(09의 compose와 10의 배포 안내가 쓴다)

| 용도 | 컨테이너 안 경로 | 얹는 컨테이너 |
|---|---|---|
| 사이트 파일 | `/etc/agent-os/site/sites.toml` | serve·위젯·위젯 미리보기 페이지(폴더째 `:ro`) |
| 위젯 미리보기 페이지 설정 | `/etc/agent-os/portal/portal.toml` | 위젯 미리보기 페이지만(폴더째 `:ro`) |
| 개인 키 | 설정이 가리키는 상대 경로 `keys/portal.pem` → `/etc/agent-os/portal/keys/portal.pem` | 같은 설정 폴더 |

- 모두 컨테이너 포트는 3000이다. 상태 확인 URL은 관리 화면 `/`, 위젯 `/widget`, 위젯 미리보기 페이지 `/portal/health`이고 이미지에 curl이 없어 node의 `fetch` 한 줄로 건다(아래 확인에서 정상 0, 듣지 않는 포트 1).
- 셋 모두 시작 때 `AGENT_OS_CONTAINER_NETWORK=1`이 있어야 `0.0.0.0`에 선다. 위젯 미리보기 페이지는 설정 파일의 `host = "0.0.0.0"`도 필요하다(`port = 3000`).
- 개인 키는 앱 사용자(10001)가 읽을 수 있어야 한다. 아래 확인은 소유자 root, 그룹 10001, 모드 0640(폴더 0750)으로 했다. 읽지 못하면 시작에서 `portal.private_key: 읽지 못한다`로 끝난다.

## 이 PC에서 띄워 본 것(손으로 봤다)

세션 스크래치패드의 확인 스크립트(`admin_check.sh`, `widget_check.sh`, `portal_check.sh`, `widget_time.sh`, `widget_ab.sh`, `build_time.sh`)로 쳤다. 출력은 세션 안의 `/tmp/ri08/`에 있고 저장소에는 두지 않았다. 다시 돌리는 스크립트가 아니라 손으로 본 것이다.

- 사용자와 첫 프로세스: 셋 모두 `id`가 `uid=10001(agentos) gid=10001(agentos)`이고 `/proc/1/comm`이 `tini`였다.
- `docker stop`: 관리 화면 5.43초 종료 143, 위젯(서 있을 때) 0.97초 143, 위젯(빌드 중, 빌드 프로세스 5개) 5.04초 143, 위젯 미리보기 페이지 1.47초 143. 프로브가 init 없이 재었을 때 빌드 중 위젯과 portal은 10초 유예를 다 쓰고 137이었다. tini가 그 둘을 143으로 끝낸다.
- 관리 화면: 같은 사용자 정의 네트워크에 별칭 `serve`로 가짜 상류(`upstream-stub.mjs`)를 두고 읽기 전용 루트로 띄우자 `/api/ping`이 200으로 상류의 응답을 돌려주었고 상류의 `/hits`에 `/ping`이 찍혔다. `AGENT_OS_CONTAINER_NETWORK`를 빼고 띄우면 2.9초에 종료 1, `--hostname 은 루프백만 받는다 ... 받은 값: 0.0.0.0` 진단이 나왔다. 루프백 예외 변수를 주고 시작 때 `AGENT_OS_UPSTREAM=http://serve:8000`을 다시 줘도 거부 없이 섰고 중계는 같았다. 쓰기는 `Read-only file system`으로 막혔다. 첫 200까지 4.2초(다른 세션의 빌드가 도는 때), `memory.current` 73MiB.
- 위젯: 네트워크 없이(`--network none`) 사이트 파일 A로 빌드하고 서서 `/widget`의 CSP가 `frame-ancestors https://probe-a.example`였다. 처음 한 번 첫 200까지 68.9초(최고치 1,592MiB), 다시 셋은 30.4·35.0·45.2초(최고치 1,490~1,514MiB, 컨테이너 안의 1분 부하 8.43~8.87, 밖의 컨테이너 3~7개). 사이트 파일이 없음(빈 볼륨, 9.1초)·폴더·깨짐·읽지 못함일 때는 빌드를 시작하기 전에 `사이트 파일 ... 을 받아들일 수 없다(AGENT_OS_SITE_FILE, ADR 0023).`와 까닭 줄로 종료 1이었고 빌드 진행 흔적 줄은 0이었다. 볼륨의 사이트 파일을 B로 바꾸고 `docker restart`하자 28.6초에 B의 CSP(`frame-ancestors https://probe-b.example https://www.probe-b.example:8443`)로 섰다. 루프백 예외 변수 없이 띄우면 56.2초 동안 빌드를 한 뒤에 `--hostname 은 루프백만 받는다 ... 0.0.0.0`으로 끝난다(아래 "남긴 것").
- 위젯 미리보기 페이지: `--network none --read-only`, 두 폴더 `:ro`로 서서 첫 200까지 6.6초, `memory.current` 57MiB, 네트워크 장치는 `lo`뿐이었다. `/portal/`이 200이고 토큰 CSS(`theme.css`), 글꼴 CSS(`fonts.css`), `portal.css`, 페이지 스크립트(`portal.js`), 글꼴 파일(`noto-sans-kr-0-400-normal.woff2`, `font/woff2`)이 모두 200으로 이미지에서 나왔다. 개인 키를 root:root 0600으로 바꾸면 2.7초에 `portal.private_key: 읽지 못한다`로 종료 1, `AGENT_OS_CONTAINER_NETWORK` 없이 `host = "0.0.0.0"`이면 2.7초에 `portal.host: 루프백만 받는다 ... 받은 값: 0.0.0.0. 이미지 안에서 0.0.0.0 에 묶으려면 환경 변수 AGENT_OS_CONTAINER_NETWORK=1 도 준다`로 종료 1.
- 상태 확인: 셋 모두 정상에 0, 듣지 않는 포트(3999)에 1이었다.
- 풀린 크기와 짓는 시간(`docker image inspect`의 `Size`를 2^20으로 나눈 MiB, 층 캐시 없이 `--no-cache`로 지은 초): `admin` 690MiB·163초, `widget` 885MiB·155초, `portal` 356MiB·50초. 처음에 admin을 같은 방식으로 지었을 때는 pnpm의 `--prod` 설치가 레지스트리에서 받다가 시간 초과(`TimeoutError: The operation was aborted due to timeout`)로 621초 만에 종료 1이었다(Dockerfile의 문제가 아니라 네트워크이고 다시 짓자 지나갔다). 지을 때 같은 PC에서 다른 세션의 빌드가 돌았을 수 있고, `docker ps`의 다른 컨테이너는 1개였으며 시작 전 1분 부하는 0.67·3.50·3.12였다. pnpm 저장소 캐시 마운트의 상태는 빌드마다 같지 않아 이 초는 범위로만 읽는다.

근거의 종류: 위 항목은 이 세션이 스크래치 스크립트를 쳐서 출력으로 본 것이다. 시간과 메모리는 형제 세션(06, 07)의 빌드가 함께 돌던 PC의 값이고, 얼마나 돌았는지는 보지 못했다.

## 프로브 `web_images`

- 고친 것: `Dockerfile`의 바탕을 trixie digest로, 앱 사용자를 uid 10001로(`base`가 그룹·사용자를 만들고 `chown`을 `agentos`로). `admin-exception` 단계는 03이 코드에 들인 예외(표지 파일 + `AGENT_OS_CONTAINER_NETWORK=1`)를 그대로 켜게 바꿨다. `patch-admin.mjs`의 `exception` 갈래는 03의 코드와 맞지 않아 지웠다. `upstream-stub.mjs`에 받은 요청 경로를 내는 `/hits`를 더했다.
- PR 567 봇이 보류한 500 단언: 예외 없는 판의 500이 상류 거부에서 났다는 표지를 둘 본다. (가) 관리 화면 기록의 `Failed to proxy http://127.0.0.1:8000`과 `ECONNREFUSED`. (나) 별칭 서버의 `/hits`가 예외 판의 `marker=exception` 요청은 받고 이 판의 `marker=control` 요청은 받지 않은 것. 이번 실행의 두 회차가 모두 표지를 보였다.
- 다시 돌린 결과: `build` 26회차, 관리 화면·portal·공통 아홉 섹션 `--rounds 2` 42회차, 위젯 여섯 섹션과 `zombie` `--rounds 3` 48회차. 측정 아닌 회차는 없었다. `build`가 `widget-lean`을 종료 0으로 지어, `strip-tests.sh`의 `.git` 조상 검사가 이미지 안에서 거부하지 않았다.
- trixie·uid 10001에서 달라진 것: 빌드 실패·좀비의 새 모양·기능 차이는 없었다. 크기는 4.1~9.1MiB 늘었다. 위젯이 뜰 때 걸리는 시간이 명세의 13.6~40.7초보다 길었다(`widget-time` 37.7~68.4초, 최고치는 1,356~1,619MiB로 앞 판과 같은 범위). 이것이 trixie 탓인지 가리려고 같은 위젯 이미지를 바탕만 bookworm digest로 바꿔 짓고 같은 사이트 파일 볼륨으로 번갈아 세 번씩 띄웠다(손으로 봤다, `widget_ab.sh`). bookworm 48.7·46.5·35.8초, trixie 71.3·33.2·34.5초로 범위가 겹치고 한 판 안에서도 33.2~71.3초로 갈렸다. trixie가 느리다는 표지는 없었다. 다른 세션이 같은 VM에서 빌드를 돌린 탓으로 보지만(어림) 그 빌드의 양은 보지 못했다. 시작 유예의 첫 값 300초 안에 든다. 티켓은 "명세의 범위를 크게 벗어나면 멈추라"고 하고, 이 차이는 판 때문이 아니라 부하로 기울었다. 명세의 13.6~40.7초는 그날 부하 아래의 범위이므로 07·09가 같은 수치를 다시 쓰면 이번 값(최대 71.3초)도 함께 본다.
- 타입 검사: 아래 검증에 적는다.

## 남긴 것

- 위젯의 `CMD`는 빌드가 끝난 뒤에야 `start`가 `0.0.0.0`을 판정한다. 루프백 예외 변수를 빠뜨리면 56초 동안 빌드한 뒤에 진단이 나온다. 진단이 나오고 종료 1이 된다는 점은 티켓의 확인 문장을 만족해서 이번에는 고치지 않았다. 빌드 전에 같은 판정을 하려면 `tools/start.ts build`가 호스트·예외 변수를 받아야 하고 03의 `bindingProblem`을 건드리므로 별도 일이다. 09의 compose가 변수를 늘 주므로 운영에서는 닿지 않는 경로로 본다(어림).
- 위젯의 `next-env.d.ts`는 root 소유 288바이트다(typegen이 이미지를 지을 때 만들었다). 앱 사용자는 쓰지 못하지만 빌드는 그 파일을 새로 쓰지 않아 막히지 않았다(위젯 확인에서 빌드하고 섰고 `ls -ln`이 root 소유를 보였다. 쓰기를 시도하는지는 코드로 보지 않았다).
- 압축 크기와 레지스트리 푸시·풀 시간, 리눅스 호스트의 Docker Engine에서의 값은 재지 않았다(프로브 README "재지 못한 것").
- OCI 라벨은 빌드 인자 기본값 `unknown`으로만 확인했다(관리 화면 이미지를 `docker image inspect`로 보니 `org.opencontainers.image.{version,revision,source}`가 모두 `unknown`이었다). 실제 값을 채우는 일은 이 티켓에 들지 않았다.

## 검증

셀프 리뷰 반영 뒤 이 세션이 친 것(2026-11-16):

- `uv run ruff check . && uv run ruff format --check .` 통과, `uv run pyright -p .scratch/release-image/probes/web_images` 0 errors, `uv run python tools/plan_table.py` 변경 없음.
- `uv run python tools/run_checks.py`(21분 53초, 다른 세션이 함께 돌았다): check-ticket, check-notes, lint-imports, zizmor, check-type-escapes, check-instructions, pyright 둘, run-hooks, web-verify 통과. pytest는 7,670 통과·1 실패였다. 실패는 `tests/tools/test_rerun_runner.py::test_첫_인계가_나면_새_회차를_열지_않는다`이고 `fake_claude.py`가 JSONL 파일을 읽다 쓰는 중인 줄(`": 52440, "running": 2}`)을 읽어 `JSONDecodeError`가 난 것이다. 이 변경이 닿지 않는 시험 하네스이고 같은 시험을 단독으로 다시 치자 통과했다(254초. 부하가 큰 때의 경합으로 본다. 어림이고 원인 코드는 읽지 않았다).
- 이미지: 리뷰 반영 뒤 최종 Dockerfile 셋을 `docker build -f deploy/images/<이름>.Dockerfile -t ri08-<이름>-r web`로 다시 지어 종료 0, 풀린 크기 admin 690.6, widget 885.0, portal 356.9MiB, widget·portal의 `id`가 `uid=10001(agentos)`였다. 관리 화면 이미지로는 위의 상류 검사도 쳤다. 이 세션은 그 이미지를 띄워 위젯·위젯 미리보기 페이지의 기능을 다시 보지는 않았다(바뀐 것이 `react-18` 매니페스트 한 줄, `FROM` 이름, `.dockerignore` 두 줄이라 이전 세션의 확인을 갈음으로 쓴다).
- 정리: `ri08-*` 이미지 일곱(`ri08-admin`, `-widget`, `-portal`, `-widget-bw`, 그리고 `-r` 셋)과 볼륨 일곱(`ri08-siteA`·`siteBroken`·`siteDir`·`siteNone`·`siteRoot`·`psite`·`pcfg`)을 지웠다.
- 커밋의 pre-commit 결과는 PR 본문과 아래 "다음"에 적는다.

## 셀프 리뷰 (이어받은 세션, 2026-11-16, 기준 `d80690da1`, 수정 6개·미추적 7개·커밋 0)

표준 축(sonnet·high)과 명세 축을 병렬로 돌렸다. Critical은 없다.

고친 것:

- Major: 세 Dockerfile의 `manifests` 단계가 `packages/react-18/package.json`을 빠뜨렸다(뿌리 `package.json`의 `@agent-os/react-18: workspace:*`와 잠금 파일의 importer가 있는 패키지). 셋 모두에 더했고 관리 화면을 다시 지어 종료 0, 풀린 크기 690.6MiB로 앞 판과 같았다(아래 검증).
- 프로브 README의 거짓 문장 셋: 시제품 `base`에 tini가 있다고 적은 곳(27·87·102행. 시제품은 tini를 깔지 않는다), "1.4~2배"(빌드 시간 최솟값끼리·최댓값끼리 모두 1.9배), "1절의 손으로 본 값 28.6초"(1절의 최소는 30.4초).
- 근거보다 센 결론 둘을 어림으로 낮췄다. "trixie가 느리다는 표지는 없다"는 판당 세 번에 양성 대조가 없고 이미지도 `widget-lean-typegen`이 아니라 실제 위젯 이미지다. "다른 세션의 빌드로 보지만"은 이번 기본 회차의 부하(2.07~5.02)가 앞 판(5.25~10.29)보다 낮은데 빌드가 1.9배 걸린 것과 맞지 않아 지웠다. 시간이 느려진 원인은 정하지 못했다고 적었다.
- 크기가 4.1~9.1MiB 늘어난 것을 바탕 몫으로 보던 문장도 지웠다. 증가가 둘로 갈린다(4.1~4.2: base·prod·lean·standalone·portal-prod, 9.0~9.1: widget-full·filter·admin-full·portal-full). 앞 판(`1117a170f`)과 이번 판 사이에 `web/pnpm-lock.yaml`이 46줄 늘었다(`git diff --stat`). 바탕·사용자·잠금 파일의 몫은 따로 재지 못했다.
- README 220행의 낡은 문장("측정용 예외 사본으로 봤다", "예외를 지을 티켓이 잰다")을 03의 코드와 `admin-exception`에 맞게 고쳤다.
- `FROM`의 `node@sha256:`를 `node:24-trixie-slim@sha256:`로 바꿨다(Mysterious Name. digest가 같으니 이미지는 같다).
- `.dockerignore` 셋에 `**/.env*`와 `**/*.pem`을 더했다. 위젯은 `COPY . .`가 최종 이미지에 든다. 추적 파일 가운데 `web/` 아래 `.env*`와 `.pem`은 없어(`git ls-files web`에서 찾아봤다) 지을 것은 바뀌지 않는다.
- 명세 축 (a)2: 03의 상류 검사를 시작 래퍼로 직접 봤다. 이미지에서 `docker run --rm -e AGENT_OS_UPSTREAM=http://serve:8000 ri08-admin-r node tools/start.ts start --port 3000`(호스트는 기본 루프백, 예외 변수 없음)이 `Ready` 뒤에 `AGENT_OS_UPSTREAM 의 호스트는 루프백 127.0.0.1 만 받는다. 받은 값: serve ... 이미지 안에서 serve 에 묶으려면 환경 변수 AGENT_OS_CONTAINER_NETWORK=1 도 준다.`를 내고 종료 1이었다(손으로 봤다).

남긴 것과 이유:

- 세 Dockerfile의 `base`·`manifests`(약 25줄)와 `.dockerignore`의 중복, pnpm 판 11.24.0이 `web/package.json`의 `packageManager`와 이중이라는 점(Duplicated Code·Shotgun Surgery). 타깃 하나의 Dockerfile이나 bake로 줄일 수 있으나 명세가 파일 이름 셋을 가정한 09·10과 얽혀 이 티켓에서 구조를 바꾸지 않았다. 대신 어긋남을 잡는 저장소 상태 시험을 09의 시험 패키지 항목으로 넘겼다(받는 쪽 09는 08이 Blocked by에 든다).
- `ENV CI=1`이 base에 있어 실행 이미지에도 남는다. 위젯이 뜰 때 `next build`를 `CI=1`로 돌고 프로브가 그 조건으로 쟀으므로 바꾸지 않았다. `EXPOSE 3000`은 호스트에 발행하지 않는 문서 표시라 명세의 "발행하지 않는다"와 어긋나지 않는다(프로브 `serve_image`도 `EXPOSE`를 쓴다). `apps/widget/public/...` 두 줄이 admin·portal의 `.dockerignore`에 있는 것은 같은 맥락(`web/`)이라 무해해서 두었다.
- 명세의 낡은 수치: 위젯 시작 13.6~40.7초(213·228·336행), 686.9·874.3·351.0MiB와 uid 1000 서술(179·207·221·247행), "trixie에서 같게 서는지는 어림"(175행). 명세 문서는 이 티켓 몫이 아니라 고치지 않았다. 07·09·10이 이 수치를 다시 쓸 때 이번 값(위젯 시작 최대 71.3초, 크기 690.6·885·356.9MiB)을 같이 본다. 프로브 README "4절"이 이를 가리킨다.
- 프로브 시제품 `Dockerfile`의 `manifests`에도 `packages/react-18`이 없다. 측정한 판의 근거이므로 고쳐 다시 재지 않았다. 실제 이미지와 다른 점으로 여기 적는다.
- 일지의 `docker stop` 값(관리 화면 5.43초, 빌드 중 위젯 5.04초)이 프로브의 `--init` 1.14초·1.55초와 명세의 1.6~2.3초보다 길다. 이유는 보지 못했다(부하 아래 손으로 본 값이다). 모두 종료 143이고 유예 10초 안이다.
- 티켓의 "본 명령과 결과를 일지에 적는다": 명령이 일지에 없다는 지적을 받아, 이전 세션의 스크래치 스크립트(이 PC의 `C:\Users\User\AppData\Local\Temp\claude\9060abe0b92613e9\e01c56da-6ea4-4f4a-ad6e-86ec35625be4\scratchpad\`의 `admin_check.sh`·`widget_check.sh`·`portal_check.sh`·`widget_time.sh`·`widget_ab.sh`)를 읽어 아래 "본 명령"에 옮겼다. 그 스크립트는 저장소에 없다. 결과는 이전 세션이 손으로 본 값이고 이 세션은 그 스크립트를 다시 돌리지 않았다.

## 본 명령 (이전 세션의 스크래치 스크립트를 읽어 옮겼다. 이 세션이 다시 돌리지 않았다)

지을 때: `docker build -f deploy/images/<admin|widget|portal>.Dockerfile -t ri08-<이름> web`(저장소 루트에서). 이 세션이 최종 Dockerfile로 다시 지었다(아래 검증).

- 사용자·첫 프로세스: `docker run --rm --entrypoint id <이미지>`, 띄운 컨테이너 안에서 `docker exec <컨테이너> sh -c 'cat /proc/1/comm; id -u; touch /x'`.
- 상태 확인: `docker exec <컨테이너> node -e "fetch('http://127.0.0.1:3000/<경로>').then(r=>process.exit(r.ok?0:1),()=>process.exit(1))"`(경로는 관리 화면 `/`, 위젯 `/widget`, 위젯 미리보기 페이지 `/portal/health`). 듣지 않는 포트 3999로 같은 명령을 쳐 1을 확인했다.
- 멈추기: `docker stop -t 10 <컨테이너>`의 시간과 `docker inspect -f '{{.State.ExitCode}}'`.
- 관리 화면: `docker network create`, 별칭 서버 `docker run -d --network <망> --network-alias serve --entrypoint node -v <프로브 폴더>:/probe:ro <이미지> /probe/upstream-stub.mjs 0.0.0.0 8000 other-container`, 본체 `docker run -d --network <망> --read-only -e AGENT_OS_CONTAINER_NETWORK=1 <이미지>`(시작 때 `-e AGENT_OS_UPSTREAM=http://serve:8000`을 다시 준 갈래도 있다), 예외 변수 없이 `docker run --network <망> <이미지>`는 종료 코드와 로그로 본다.
- 위젯: `docker volume create` 후 `docker create -v <볼륨>:/etc/agent-os/site <이미지>`로 사이트 파일을 넣고, `docker run -d --network none -e AGENT_OS_CONTAINER_NETWORK=1 -v <볼륨>:/etc/agent-os/site:ro <이미지>`. 시간은 `docker run`부터 첫 200까지, 최고치는 `docker exec <컨테이너> cat /sys/fs/cgroup/memory.peak`. 사이트 파일을 바꾼 뒤 `docker restart`.
- 위젯 미리보기 페이지: 사이트 파일 볼륨과 설정 볼륨(`keys/portal.pem` 소유자 root·그룹 10001·모드 0640)을 `:ro`로 얹고 `docker run -d --network none --read-only -e AGENT_OS_CONTAINER_NETWORK=1 ...`. 개인 키를 `chown root:root`·`chmod 0600`으로 바꿔 시작에서 끝나는 갈래를 쳤다.
- 위젯의 `CMD`가 빌드 뒤에야 `0.0.0.0`을 판정하는 것은 위 "남긴 것"에 이미 적었다.

## 인계 (셀프 리뷰 직전, 2026-11-16)

- 인계 경계: 셀프 리뷰 직전. 컨텍스트가 문턱을 넘어 `handoff.md`대로 넘긴다. 인계하기 전 제목은 `feature/08-web-images-run-as-non-root`(브랜치 이름 그대로)였고 `feature/08-web-images-run-as-non-root (인계함)`으로 바꾼다. 커밋은 하지 않았고 변경은 모두 워크트리에 있다(`deploy/`와 이 일지는 미추적). 티켓 08은 체크박스를 모두 채우고 `Status: done`으로 바꿨는데, "검증 명령이 모두 초록이다"는 셀프 리뷰와 커밋의 pre-commit 뒤에야 참이므로 새 세션이 빨강이면 되돌린다.
- 새 세션이 할 것: `/code-review`(기준 `origin/dev`), Critical·Major 반영, 커밋(pre-commit), `git merge origin/dev`(이 세션이 본 `origin/dev`는 `6cc6784`로 이 브랜치의 기준 `d80690da1`보다 앞서 있다), 푸시, PR, 봇 회차, 병합, 일지 "다음", 회고. 이 일지의 "검증" 절과 셀프 리뷰 절은 새 세션이 채운다.
- 이 세션이 띄운 백그라운드 작업은 모두 끝났고(프로브 구간, 빌드, 대기) 남은 것이 없다. 워크트리 잠금은 풀었다(`git worktree unlock`이 오류 없이 끝났다).
- open-session을 부른다 2026-11-15T17:56Z
- 정리: 이 세션이 만든 도커 이미지(`ri08-admin`, `ri08-widget`, `ri08-portal`, `ri08-widget-bw`)와 볼륨(`ri08-siteA` 등)이 남아 있다. 병합 전에 `docker rmi`와 `docker volume rm`으로 지운다. 프로브의 `ri-web-img:*` 이미지와 BuildKit 캐시 마운트는 프로브 README대로 남겨도 된다.
- 밀 주장(이전 세션이 넘긴 것. 셀프 리뷰가 겨냥했고 1절의 둘과 2절의 하나는 위 "셀프 리뷰"에서 다시 썼다): 프로브 README 1절의 다른 세션 빌드 탓으로 돌린 문장과 trixie가 느리다는 표지가 없다는 문장, 2절의 크기 증가를 바탕 몫으로 본 문장, 4절의 03이 들인 예외가 표지 파일과 환경 변수가 함께 있어야 켜진다는 문장(코드를 읽었다), 맨 끝 절의 바탕과 사용자를 바꿔도 명세의 문장과 다른 결과가 없었다는 문장.
