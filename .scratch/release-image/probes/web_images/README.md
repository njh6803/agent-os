# web_images 프로브

release-image 명세가 web 쪽 컨테이너 이미지 셋(관리 화면 `admin`, 위젯 `widget`, 위젯 미리보기 페이지 `portal`)을 고르려고, 리눅스 컨테이너에서 시제품 Dockerfile로 이미지를 짓고 띄워 본 사실을 모은다. 결정은 명세가 한다. 시제품 Dockerfile은 측정용이고 최종이 아니다.

진행 상태(2026-11-16): 열일곱 섹션을 모두 다시 돌렸다. 2026-11-13에는 `node:24-bookworm-slim`과 uid 1000으로, 2026-11-16에는 명세가 고른 `node:24-trixie-slim`과 uid 10001로 돌렸다(티켓 08, 맨 끝 절). 아래 값은 2026-11-16의 것이고, 앞 판의 값을 든 자리는 그렇게 적는다. 손으로만 본 것은 항목마다 "손으로 봤다"로 남긴다.

## 다시 돌리기

저장소 루트에서 친다.

```
uv run python .scratch/release-image/probes/web_images/run.py --sections build
uv run python .scratch/release-image/probes/web_images/run.py --sections <이름,이름,...> [--rounds <되풀이 수>] [--work <원본 출력 폴더>]
```

- 필요한 것: 도는 Docker 데몬(리눅스 컨테이너, BuildKit). `build` 섹션에는 Docker Hub와 npm 레지스트리에 닿는 네트워크가 든다. 다른 섹션은 `build`가 지은 `ri-web-img:<단계>` 이미지만 쓴다.
- 섹션: `build`, `admin-time`, `admin-reject`, `admin-upstream`, `admin-standalone`, `common-env`, `common-health`, `common-readonly`, `common-stop`, `portal`, `widget-time`, `widget-memory`, `widget-network`, `widget-user`, `widget-sitefile`, `widget-reflect`, `zombie`. 섹션마다 무엇을 표지로 보는지는 그 함수의 독스트링이 원천이다.
- 걸린 시간(이 PC, 2026-11-16, 다른 세션의 이미지 빌드가 함께 돌았다): `build`는 바탕 이미지를 새로 받고 pnpm 캐시가 빈 채 시작해 1,184초(약 20분. 설치 단계 여섯이 112~197초씩 걸렸다), 관리 화면·portal·공통 섹션 아홉을 `--rounds 2`로 314초, 위젯 섹션 여섯과 `zombie`를 `--rounds 3`으로 1,916초(약 32분). 2026-11-13의 같은 실행은 캐시가 찬 `build` 약 4분, 아홉 섹션 약 8분, 위젯 일곱 섹션 약 14분이었다. 2026-11-16의 위젯 쪽이 두 배 넘게 걸린 것은 아래 "잰 판"의 부하와 1절 때문이다.
- 호스트 포트는 열지 않는다. 세 프로세스가 컨테이너 안의 루프백에만 묶이므로 요청은 `docker exec`로 컨테이너 안에서 건다(`fetch.mjs`).
- 띄운 컨테이너·볼륨·네트워크에는 라벨 `ri-web-probe=<실행 토큰>`을 달고, 끝날 때 그 실행의 토큰이 붙은 것만 지운다. 시작할 때는 다른 토큰이 붙은 것(끊긴 앞 실행이나 함께 도는 다른 실행의 것)을 세어 알리기만 하고, 도는 실행이 없으면 `--filter label=ri-web-probe`로 골라 손으로 지운다. 이미지와 BuildKit 캐시 마운트(`ri-web-pnpm-store`, `ri-web-pnpm-meta`)는 남는다. 2026-11-13의 실행은 라벨 값 없이 시작과 끝에 라벨 키가 붙은 것을 모두 지우던 판이다(맨 끝 절).
- 원본 출력은 `--work`(없으면 시스템 임시 폴더) 아래 `raw.log`, 회차의 값은 `results.jsonl`에 남는다. 표지를 보지 못한 회차가 하나라도 있으면 종료 코드가 1이다(`tools/probe_kit.py`의 `Rounds`).
- 타입 검사: `uv run pyright -p .scratch/release-image/probes/web_images`(이 폴더의 `pyrightconfig.json`, strict).

## 잰 판

- Windows 10의 Docker Desktop, 엔진과 클라이언트 29.9.2, buildx v0.38.1, 저장 드라이버 overlay2, WSL2 커널 6.18.58.1-microsoft-standard-WSL2, cgroup v2, CPU 16개, 메모리 16.7GB.
- 바탕 이미지 `node:24-trixie-slim`, digest `sha256:af02d57b57719b9657a45199a79264a9437940cd55b3c7b3fc99615654f124a0`(Debian 13, curl·wget 없음. 이 프로브의 시제품은 tini를 깔지 않는다. `deploy/images/`의 실제 이미지가 `apt-get`으로 얹는 tini는 0.19.0이다). Node v24.22.3, corepack으로 켠 pnpm 11.24.0. 이미지 안의 Next 16.3.6, TypeScript 5.9.3, Vite 8.3.1(`build` 섹션의 "판" 회차가 적는다). 앱 사용자는 uid·gid 10001 `agentos`이고 시제품 `Dockerfile`의 `base`가 만든다. 앞 판(2026-11-13)은 `node:24-bookworm-slim`, digest `sha256:dc26ae92c9fb15cf6b1d63e20f0944b2efe0f115b20e00be48fb23fceb061c54`(Debian 12, tini 없음)와 이미지에 있는 `node`(uid 1000)였다. 도구의 판은 둘이 같았다.
- Windows 10의 Docker Desktop 엔진은 29.9.2(2026-11-16에 `docker version`으로 다시 봤다). 나머지 환경은 앞 판과 같다.
- 저장소는 워크트리 HEAD `d80690da1`에 티켓 08의 변경(시제품 Dockerfile·프로브)을 얹은 `web/`. 저장소 파일은 고치지 않았고, 고친 판이 필요한 갈래는 이미지 안의 사본을 고쳤다(`patch-admin.mjs`, `patch-widget.mjs`, `prune-manifests.mjs`, `strip-tests.sh`).
- 같은 Docker 데몬과 VM을 다른 측정 세션(같은 기능의 티켓 06·07)이 함께 썼다. 2026-11-16의 위젯 회차는 이 프로브 밖에서 도는 컨테이너가 1~3개였고 컨테이너 안에서 본 VM의 1분 부하는 2.07~8.22였다(다른 세션의 이미지 빌드는 컨테이너로 보이지 않고 부하로만 잡힌다). 시간 값은 범위로만 읽는다. 앞 판(2026-11-13)은 컨테이너가 3~8개, 부하가 5.25~10.29였다.

## 파일

| 파일 | 하는 일 |
|---|---|
| `run.py` | 프로브. 섹션마다 이미지를 짓거나 띄우고 표지를 본 회차만 측정으로 센다 |
| `Dockerfile`, `Dockerfile.dockerignore` | 시제품. 빌드 맥락은 `web/`, 이 폴더는 이름 붙은 둘째 맥락 `probe`. 단계마다 갈래 하나. 바탕은 `node:24-trixie-slim`(digest 고정), 앱 사용자는 uid 10001 `agentos`다(2026-11-16에 바꿨다) |
| `entry-widget.sh` | 위젯 진입. 사이트 파일로 빌드한 뒤 `exec node tools/start.ts start --hostname 127.0.0.1 --port 3000`. `RI_PROBE` 줄(시각, 이전 빌드 유무, cgroup 메모리)을 찍고, `RI_PROBE_WAIT_URL`이 있으면 갈아타기 전에 `wait.mjs`를 뒤에서 띄운다 |
| `entry.sh` | 관리 화면·portal 진입. 표지 한 줄(uid, `HOSTNAME`, `PORT`)을 찍고, `RI_PROBE_WAIT_URL`이 있으면 `wait.mjs`를 뒤에서 띄운 뒤 `exec "$@"` |
| `wait.mjs`, `fetch.mjs` | 컨테이너 안에서 첫 200을 기다리고, 요청 하나의 상태·머리·본문 표지를 JSON으로 낸다 |
| `upstream-stub.mjs` | 가짜 상류. `/ping`은 토큰과 받은 `Authorization`을, `/sse`는 0.4초 간격 이벤트 넷을 내고, `/hits`는 받은 요청의 경로(질의 포함)를 낸다 |
| `portal-fixture.mjs` | portal 설정·사이트 파일·서명 키(`tools/make-key.ts`)를 한 폴더에 만든다 |
| `patch-admin.mjs` | 관리 화면 사본에 `output: "standalone"`을 넣는다(`standalone` 갈래 하나. 측정용 상류 예외 갈래는 03이 같은 예외를 코드에 들여 지웠다) |
| `patch-widget.mjs` | 위젯 사본의 `next.config.ts`에 `typescript.ignoreBuildErrors`를 넣는다 |
| `prune-manifests.mjs`, `strip-tests.sh` | 위젯 lean 갈래. package.json 사본의 개발 의존성을 줄이고 시험 파일을 지운다 |
| `sites_a.toml`, `sites_b.toml`, `sites_broken.toml` | 위젯 사이트 파일. A와 B는 허용 출처와 `request_chars`(771133, 583927)가 달라 응답의 표지가 된다 |
| `pyrightconfig.json` | 이 폴더의 pyright strict 설정 |

## 근거의 종류

- 쟀다: `run.py`의 섹션이 다시 낸다. 섹션 이름을 적는다. 2026-11-16의 실행에서 측정 아닌 회차는 없었다(`build` 26회차, 관리 화면·portal·공통 아홉 섹션 `--rounds 2` 42회차, 위젯 여섯 섹션과 `zombie` `--rounds 3` 48회차). 2026-11-13의 실행도 측정 아닌 회차가 없었다(`build` 셋째 실행 26회차, 아홉 섹션 42회차, 일곱 섹션 40회차, `zombie`만 다시 돌린 12회차).
- 손으로 봤다: 셸에서 친 명령의 원본 출력을 봤다(명령을 함께 적는다). 다시 돌리는 스크립트는 없다.
- 코드를 읽었다: 워크트리 HEAD `1117a170f`(2026-11-13)의 파일이나 이미지 안 `node_modules/next`(16.3.6)의 파일. 2026-11-16에 다시 읽은 것은 4절의 루프백 예외 항목(`web/apps/admin/tools/loopback.ts`)뿐이고, 3절의 나머지 코드를 읽은 항목은 03이 예외를 들이기 전 판의 것이다.
- 어림: 잰 값에서 미룬 것.

## 결과

### 1. 위젯이 뜰 때 하는 빌드(시간, 메모리, 네트워크)

시간과 메모리는 쟀다(`widget-time`, `widget-memory`). 이미지는 `widget-lean-typegen`, `--user 10001:10001`, 사이트 파일 A, `NEXT_TELEMETRY_DISABLED=1`. 빌드는 진입 스크립트가 찍은 빌드 시작·끝 시각의 차, 전체는 컨테이너 시작에서 `/widget`의 첫 200까지, 최고치는 빌드가 끝난 직후 cgroup의 `memory.peak`다. 회차마다 빌드를 시작하고 6초 뒤 VM의 1분 부하(`/proc/loadavg`)와 이 프로브 밖에서 도는 컨테이너 수를 적었다.

| 갈래 | 빌드(초) | 컴파일 / 타입 검사(초) | 전체(초) | 최고치(MiB) | 1분 부하 |
|---|---|---|---|---|---|
| 기본 #1~#3 | 38.0~55.5 | 14.4~24.7 / 14.8~15.8 | 41.2~58.2 | 1,477~1,619 | 2.07~5.02 |
| `--init` | 56.2 | 22.8 / 12.3 | 59.0 | 1,470 | 7.07 |
| `--cpus 2` | 66.4 | 45.0 / 11.4 | 68.4 | 1,551 | 5.91 |
| 타입 검사 건너뜀(`widget-lean-notc`) #1~#2 | 34.9~42.3 | 18.1~19.4 / — | 37.7~46.1 | 1,490~1,516 | 6.22~7.68 |

- 앞 판(2026-11-13, bookworm·uid 1000)의 기본 #1~#3은 빌드 19.7~29.9초, 전체 21.5~31.4초, 최고치 1,476~1,567MiB였다. 이번 기본 회차는 빌드 38.0~55.5초, 최고치 1,477~1,619MiB로, 빌드 시간의 최솟값끼리는 1.9배, 최댓값끼리는 1.9배다. 최고치는 앞 판(1,476~1,567MiB)과 겹친다.
- 그때 부하: 이 프로브 밖에서 도는 컨테이너가 회차마다 1~3개였고 1분 부하는 CPU 16개짜리 WSL2 VM 전체의 값이다(다른 세션이 이미지를 짓는 동안에는 컨테이너로 보이지 않는다). 시간은 이 부하 아래의 범위로만 읽는다.
- 빌드가 끝나 서비스로 갈아탄 뒤 첫 200까지 1.31~2.87초, 그 가운데 Next의 `Ready in`은 0.25~0.70초였다.
- 시간이 앞 판보다 긴 까닭이 trixie인지 부하인지는 둘을 번갈아 띄워 가렸다(손으로 봤다, 세션 스크래치패드 `widget_ab.sh`. 같은 사이트 파일 볼륨, `--network none`, 첫 200까지 `docker run`부터 잰 초): 바탕을 bookworm digest로 바꿔 지은 같은 위젯 이미지가 48.7 / 46.5 / 35.8초, trixie 이미지가 71.3 / 33.2 / 34.5초였고 컨테이너 안의 1분 부하는 4.92~8.75였다. 두 판의 범위가 겹치고 한 판의 안에서도 33.2~71.3초로 갈려, 이 비교로는 trixie가 느리다고도 아니라고도 가르지 못한다(판당 세 번, 부하를 회차마다 짝지어 적지 않았고, 이 비교의 이미지는 `widget-lean-typegen`이 아니라 실제 위젯 이미지다. 양성 대조가 없는 어림이다). 앞 판의 부하는 5.25~10.29였고 이번 기본 회차는 2.07~5.02로 더 낮았는데도 빌드가 1.9배 걸렸으므로, 부하가 높아서 느려졌다는 설명은 이 표의 숫자와 맞지 않는다. 다른 세션의 빌드가 얼마나 돌았는지는 보지 못했다. 느려진 원인은 정하지 못했다.
- 같은 날 `deploy/images/widget.Dockerfile`로 지은 실제 위젯 이미지를 손으로 띄운 값(손으로 봤다, 세션 스크래치패드 `widget_time.sh`, 네트워크 없음)은 첫 200까지 68.9초(처음 한 번, 최고치 1,592MiB), 30.4 / 35.0 / 45.2초(다시 셋, `memory.peak` 1,490~1,514MiB, 컨테이너 안의 1분 부하 8.43~8.87, 밖의 컨테이너 3~7개).
- `--cpus 2` 한 번은 컴파일이 45.0초로 가장 길었지만 부하도 회차마다 흔들려 CPU 수의 효과는 이 측정으로 가르지 못한다(어림).
- 타입 검사를 건너뛴 빌드는 34.9~42.3초로 기본(38.0~55.5초)과 범위가 겹친다. 기본 회차의 타입 검사 구간은 11.4~15.8초였다. 최고치는 기본과 같은 범위라, 최고치는 타입 검사가 정하지 않는다.
- 메모리 제한(`--memory X --memory-swap X`로 스왑 없이, 한 번씩): 2g는 빌드하고 섰다(최고치 1,563MiB). 1g·768m·512m은 빌드를 시작하고 10.2~19.3초 만에 `memory.events`의 `oom_kill 1`, `State.OOMKilled` true, 종료 137로 죽었다. 기록의 끝 줄은 `Killed`였다.
- 앞 판(2026-11-13)에 손으로 본 값(부하를 적지 않았다): uid 1000 빌드 49.9초(컴파일 16.9초, 타입 검사 10.2초), root로 `widget-full`과 같은 내용의 이미지 30.8초, `widget-lean-notc` 19.0초, 최고치 1,454~1,527MiB. 선 뒤 `memory.current`는 약 195MB였다.
- `--network none`(쟀다, `widget-network`): 빌드도 서기도 네트워크 없이 끝났다. 대조로 바탕 이미지에서 1.1.1.1:443에 TCP를 열면 기본 브리지는 `open`, `--network none`은 `closed ENETUNREACH`였다. 위젯 회차 셋(텔레메트리 끔 둘, 켬 하나)은 모두 네트워크 장치가 `lo`뿐이고 바깥 연결이 `closed ENETUNREACH`인 채 빌드 54.4~66.3초, 전체 57.2~69.0초, 최고치 1,356~1,425MiB로 서서 사이트 파일 A의 CSP를 냈다.
- 텔레메트리(쟀다, `widget-network`): `NEXT_TELEMETRY_DISABLED`를 주지 않은 갈래만 빌드 기록에 `Attention: Next.js now collects completely anonymous telemetry ...` 안내를 찍었고, 그 갈래도 네트워크 없이 빌드하고 섰다. 세 회차 모두 `docker diff`에서 앱 폴더(`apps/widget`) 밖의 바뀐 자리가 없었다(기록만 했다. `docker diff`가 쓰는 자리를 잡는 대조는 8절의 root 회차). 컨테이너 안의 `next telemetry status`는 켠 빌드 뒤에도 `Status: Disabled`를 답해(손으로 봤다) 표지로 쓰지 않았다.

### 2. 이미지 갈래와 크기, 실행 때 필요한 것

크기는 `docker image inspect`의 `Size`(풀린 층의 합, 압축 전)를 2^20으로 나눈 MiB다. 쟀다(`build`, 2026-11-16). 괄호 안은 앞 판(2026-11-13, bookworm)의 MiB다. "실행 때 필요한 것" 칸의 근거는 칸 안에 적는다. 손으로 봤다고 적은 칸은 앞 판(2026-11-13)에 본 것이고 이번에 다시 보지 않았다.

| 이미지 | MiB | 담은 것 | 실행 때 필요한 것과 본 것 |
|---|---|---|---|
| `base` | 245.2 (241.1) | 바탕 이미지, uid 10001 `agentos`, pnpm(tini는 없다) | — |
| `widget-full` | 883.3 (874.3) | 워크스페이스 전체 의존성(뿌리의 개발 의존성 포함), `web/` 소스 | 뜰 때 빌드한다. root면 그대로 빌드됐다(쟀다, `widget-user`). uid 10001이면 `public/fonts`를 만들지 못해 멈춘다(쟀다, 8절). `.next`, `public`, `next-env.d.ts`가 그 uid에게 쓰기 가능해야 한다 |
| `widget-full-nonroot`, `widget-full-typegen` | 883.3 (874.3) | 위와 같고 쓰는 자리를 `agentos`(uid 10001) 소유로 미리 만든 것 | 위와 같다 |
| `widget-filter` | 882.9 (873.9) | `pnpm install --filter "@agent-os/widget..."`. 뿌리의 개발 의존성까지 깔려 full과 거의 같다 | full과 같다고 본다(어림) |
| `widget-prod` | 668.2 (664.0) | 같은 범위의 운영 의존성만(`--prod`) | 빌드가 실패한다. `Error [ERR_MODULE_NOT_FOUND]: Cannot find package '@tailwindcss/vite' imported from /app/web/apps/widget/tools/element.ts`, 종료 1(손으로 봤다, `docker run --rm -e AGENT_OS_SITE_FILE=/probe/sites_a.toml -e NEXT_TELEMETRY_DISABLED=1 ri-web-img:widget-prod`) |
| `widget-lean-withtests` | 749.9 (745.7) | 뿌리 개발 의존성을 모두 빼고 위젯·ui의 개발 의존성 가운데 빌드가 import하는 것(vite, `@tailwindcss/vite`·`postcss`, tailwindcss, typescript, 타입 패키지)만 남긴 설치. 시험 파일은 그대로 | 빌드의 타입 검사가 실패한다. 앱 tsconfig가 시험·스토리 파일까지 들어 `error TS2307: Cannot find module 'vitest'`(그 밖에 `@playwright/test`, `msw`, `@testing-library/react`, `@storybook/react-vite`) 뒤 `Failed to type check.`, 종료 1(손으로 봤다, 같은 꼴의 `docker run`) |
| `widget-lean`, `widget-lean-typegen` | 749.9 (745.7) | 위 설치에 시험·스토리·e2e 파일을 지운 것(`strip-tests.sh`). `.storybook`은 선언 파일(`*.d.ts`)만 남긴다. typegen은 지을 때 `next typegen`을 돌리고 `.next`·`public`을 uid 10001 소유로 만든 것 | `widget-lean-typegen`: 사이트 파일 하나(`AGENT_OS_SITE_FILE`), uid 10001(다른 uid는 멈춘다), 빌드 동안 1GiB 넘는 메모리(1g 제한에서 OOM, 2g에서 섰다)가 든다. 네트워크는 없어도 되고, 읽기 전용 루트에 `.next`·`public` tmpfs 둘로 선다(쟀다, 1·7·8절). `strip-tests.sh`의 `.git` 조상 검사는 이미지 안에서 거부하지 않았다(쟀다, `build`가 `widget-lean`을 짓고 종료 0). `.storybook`을 통째로 지운 첫 판은 `element/index.ts(15,17): error TS2307: Cannot find module '../styles/widget.css?inline'`로 실패했다. `*.css?inline`의 선언이 `.storybook/css-inline.d.ts`에 있어서다(손으로 봤다) |
| `widget-lean-notc` | 749.9 (745.7) | `widget-lean-typegen`에 `typescript.ignoreBuildErrors`를 넣은 사본(`patch-widget.mjs`) | 타입 검사 없이 빌드하고 섰다. 기록에 `Skipping validation of types`(쟀다, `widget-time`) |
| `admin-full` | 973.2 (964.1) | 전체 의존성, 소스, `next build` 산출물(`.next`, 캐시 포함) | uid 10001로 서고 읽기 전용에서도 선다(쟀다, 3·7절) |
| `admin-prod` | 691.0 (686.9) | 관리 화면 운영 의존성만, `package.json`·`next.config.ts`·`tools/start.ts`·`tools/loopback.ts`·`public`, 캐시 뺀 `.next` | 위와 같다(쟀다). 시작 래퍼와 `next.config.ts`의 검사가 그대로 돈다 |
| `admin-exception` | 973.2 | `admin-full`에 표지 파일 `/etc/agent-os/image`와 `AGENT_OS_CONTAINER_NETWORK=1`, `AGENT_OS_UPSTREAM=http://serve:8000`을 두고 `next build`한 것(03이 들인 코드의 예외를 그대로 켠다) | 4절 |
| `admin-standalone` | 294.7 (290.6) | `output: "standalone"`을 넣은 사본의 `.next/standalone`과 `static`, `public`. `node server.js`로 뜬다 | `HOSTNAME`을 루프백으로 줘야 루프백에 선다. 시작 래퍼와 `next.config.ts`의 검사를 거치지 않는다(쟀다, 3·4절) |
| `portal-prod` | 355.1 (351.0) | portal 운영 의존성, `apps/portal`, `packages/site-file`, `packages/ui` 소스. 빌드 산출물이 없고 node가 `.ts`를 바로 돈다 | `--config`, `--site-file`, 설정이 가리키는 개인 키 파일(실행 uid가 읽을 수 있어야 한다). uid 10001·`--network none`·`--read-only`로 선다(쟀다, 9절) |
| `portal-full` | 883.3 (874.3) | 전체 의존성과 `web/` 소스 | 비교용 |

- 바탕을 trixie로, 앱 사용자를 uid 10001로 바꾼 뒤 크기가 모두 4.1~9.1MiB 커졌다. 늘어난 폭이 둘로 갈린다. `base`·`widget-prod`·`widget-lean*`·`admin-standalone`·`portal-prod`는 4.1~4.2MiB, `widget-full`·`widget-filter`·`admin-full`·`portal-full`은 9.0~9.1MiB다. 바탕 때문이라면 모두 같아야 하므로 바탕만으로는 설명되지 않는다. 앞 판(`1117a170f`)과 이번 판(`d80690da1`) 사이에 `web/pnpm-lock.yaml`이 46줄 늘고 뿌리 `package.json`에 `@agent-os/react-18`이 더해졌다(`git diff --stat`). 바탕, 사용자, 잠금 파일의 몫을 따로 재지 않았으므로 원인은 가리지 못했다.
- 이 프로브의 시제품이 아니라 `deploy/images/`의 Dockerfile로 지은 실제 이미지의 풀린 크기는 `admin` 690.6, `widget` 885.0, `portal` 356.9MiB다(손으로 봤다, `docker image inspect -f '{{.Size}}'`를 2^20으로 나눴다. 리뷰 반영 뒤 최종 Dockerfile로 다시 지어 같은 값이 나왔다). 지은 시간은 일지에 적는다.
- pnpm 메타데이터 캐시: `pnpm install`이 `/root/.cache/pnpm`에 288MiB를 남긴다. 캐시 마운트로 빼지 않은 `deps-full-homecache`는 1159.7MiB, 뺀 `deps-full`은 880.2MiB였다(쟀다, `build`의 "pnpm 메타데이터 캐시" 회차).
- lean 갈래는 package.json 사본을 고쳐 잠금 파일을 얼리지 않고(`--no-frozen-lockfile`) 설치한다. 이번에도 next·typescript·vite의 판이 full과 같았지만(쟀다, `build`의 "판" 회차) 잠금 파일이 판을 묶지 않는 길이다.
- 관리 화면 빌드(쟀다, `admin-time`, root, 두 번): `next build` 28.6~35.5초(컴파일 8.7~14.0초), `memory.peak` 1,301~1,320MiB. 앞 판은 37.5~61.0초, 1,217~1,294MiB였다.
- 관리 화면 시작(쟀다, `admin-time`, uid 10001, 갈래마다 두 번): 컨테이너 시작에서 `/`의 첫 200까지 `admin-full` 0.93~1.44초, `admin-prod` 1.85~2.42초, `admin-standalone` 1.23~3.03초. 서는 중 `memory.current`는 `admin-full`이 74MiB, `admin-prod`가 73~75MiB, standalone이 54~59MiB.
- 압축 크기(레지스트리에 올라가는 크기)는 재지 않았다.

### 3. 듣는 주소와 루프백 예외가 필요한 자리

- 루프백 목록은 네 벌이다. 파이썬 `serve`(`src/agent_os/main.py`의 `LOOPBACK_HOSTS`, `--host` 검사), 관리 화면(`web/apps/admin/tools/loopback.ts`의 `bindingProblem`과 `upstreamProblem`), 위젯(`web/apps/widget/tools/start.ts`의 `bindingProblem`), portal(`web/apps/portal/server/config.ts`의 `portal.host` 검사). 위젯 래퍼의 머리 주석이 "목록을 바꾸면 넷을 함께 고친다"고 적는다(코드를 읽었다).
- 검사가 도는 때(코드를 읽었다): 위젯·관리 화면의 바인딩 검사는 시작 래퍼가 `dev`·`start`를 next에 넘기기 전에 돈다. 위젯 `build`는 호스트·포트를 받지 않아 바인딩 검사가 없다. 관리 화면의 상류 검사는 `next.config.ts`가 읽힐 때마다(dev, build, start) 돈다. portal은 시작할 때 설정 파일을 읽으며 돈다.
- 무엇이 듣는 주소를 정하나(코드를 읽었다): 위젯과 관리 화면의 래퍼는 `--hostname`이 없으면 127.0.0.1을 쓰고 next에는 늘 `--hostname <호스트>`를 넘긴다. `next start`는 `HOSTNAME` 환경 변수를 읽지 않는다. 포트는 래퍼가 `--port`를 받았을 때만 넘기고, 넘기지 않으면 next가 `PORT` 환경 변수를 읽는다(commander의 `.env('PORT')`, 기본 3000). `HOSTNAME`을 읽는 자리는 standalone `server.js` 틀뿐이다(`process.env.HOSTNAME || '0.0.0.0'`, `next/dist/build/utils.js`). 이미지 안 next 16.3.6의 `dist/bin/next`, `dist/cli`, `dist/server/lib/start-server.js`를 grep했다.
- Docker는 `HOSTNAME`에 컨테이너 ID를 넣는다(standalone 회차의 진입 표지 줄에 `hostname_env=3f2334746d30`). 관리 화면 래퍼에 `--hostname`도 `--port`도 주지 않고(`node tools/start.ts start`) `-e PORT=3005`로 띄우면 127.0.0.1:3005에서 들었다. 래퍼의 기본 호스트가 루프백이고 포트는 `PORT`를 따랐다(쟀다, `common-env`. 듣는 소켓은 `/proc/net/tcp`).
- 시제품의 관리 화면 명령(`node tools/start.ts start --hostname 127.0.0.1 --port 3000`)에 `-e HOSTNAME=0.0.0.0`을 더해도 127.0.0.1:3000이었다(쟀다, `common-env`). 래퍼에 준 인자가 환경 변수보다 앞선다는 것만 보이고, 인자 없이 `HOSTNAME`만 준 갈래는 재지 않았다(래퍼가 늘 `--hostname`을 넘기므로 같다고 본다, 코드를 읽었다).
- standalone `server.js`는 `HOSTNAME`을 주지 않으면 컨테이너 ID에 묶여 컨테이너 주소(172.17.0.3:3000)에서만 들었고 127.0.0.1은 연결 거부였다. `-e HOSTNAME=127.0.0.1`이면 127.0.0.1:3000이다(쟀다, `admin-standalone`). 시작 래퍼를 거치지 않으므로 루프백 검사가 없다.
- portal은 설정 파일의 `host`·`port`로만 선다. `-e PORT=4555 -e HOSTNAME=0.0.0.0`을 줘도 설정의 127.0.0.1:3100에서 들었다(쟀다, `portal`).
- 위젯은 시제품 진입 스크립트가 `node tools/start.ts start --hostname 127.0.0.1 --port 3000`으로 갈아타, `widget-time`의 일곱 회차 모두 127.0.0.1:3000에서 들었다(쟀다). 인자 없이 띄운 갈래는 재지 않았다. 위젯 래퍼도 `--hostname`이 없으면 127.0.0.1을 쓴다(코드를 읽었다).

### 4. 관리 화면의 상류(`AGENT_OS_UPSTREAM`)

쟀다(`admin-upstream`, `admin-reject`).

- 상류는 빌드 산출물에 굳는다. `admin-full`의 `.next/routes-manifest.json`의 중계 대상은 `http://127.0.0.1:8000/:path*`, 상류를 `http://serve:8000`으로 지은 `admin-exception`은 `http://serve:8000/:path*`였다. 같은 값이 `.next/required-server-files.js`·`.json`에도 있다(손으로 봤다).
- 시작 때의 환경 변수는 중계 대상을 바꾸지 않는다. `admin-full`을 `-e AGENT_OS_UPSTREAM=http://127.0.0.1:9999`로 띄우고 컨테이너 안에 가짜 상류 둘(8000은 토큰 `built`, 9999는 `startenv`)을 두자, 9999는 직접은 답했는데 `/api/ping`은 `built`에서 왔다.
- 그래도 시작 때 `next.config.ts`가 다시 읽혀 검사는 돈다. `http://serve:8000`과 `http://localhost:8000`을 시작 때 주면 둘 다 `✓ Ready in ...`이 먼저 찍힌 뒤 `⨯ Failed to load next.config.ts`와 `Error: AGENT_OS_UPSTREAM 의 호스트는 루프백 127.0.0.1 만 받는다. 받은 값: serve`(또는 `localhost`)가 나오고 0.6~0.7초 만에 종료 1이었다(앞 판은 약 1.9초). 기록의 Ready 줄만 보고 떴다고 판정하면 틀린다.
- 빌드 때 `http://serve:8000`을 주면 `> Build error occurred` 다음 같은 문구로 종료 1이었다.
- standalone은 시작 때 `next.config.ts`를 읽지 않아(`✓ Running next.config took 1.3ms`, 손으로 봤다) `AGENT_OS_UPSTREAM=http://serve:8000`을 줘도 거부 없이 섰고 중계 대상은 빌드 때 값 그대로였다.
- 03이 코드에 들인 예외(표지 파일 `/etc/agent-os/image`와 `AGENT_OS_CONTAINER_NETWORK=1`)를 지을 때 켠 `admin-exception`(`AGENT_OS_UPSTREAM=http://serve:8000`)은 같은 사용자 정의 네트워크의 별칭 `serve` 컨테이너(가짜 상류)로 `/api/ping?marker=exception`을 200으로 중계했고 `Authorization: Bearer ...` 머리가 넘어갔다. `/api/sse`의 이벤트 넷은 0.42·0.82·1.22·1.62초에 하나씩 왔다(모아서 한 번에 오지 않았다). 앞 판은 `patch-admin.mjs`가 이미지 안 사본의 검사를 고쳐 같은 예외를 만들었고, 03이 같은 예외를 코드에 들인 뒤로는 그 갈래가 맞지 않아 지웠다(티켓 08).
- 같은 네트워크에서 예외 없이 지은 `admin-full`은 `/api/ping?marker=control`이 500이었다(대조). 이 500이 기대한 원인(빌드 때 굳은 루프백 목적지를 거부당했다)에서 났다는 표지를 둘 본다(쟀다, `admin-upstream`): (가) 관리 화면 컨테이너의 기록에 `Failed to proxy http://127.0.0.1:8000`과 `ECONNREFUSED`가 함께 있다. (나) 별칭 `serve` 서버의 `/hits`가 예외 판의 `marker=exception` 요청은 받았고 이 판의 `marker=control` 요청은 받지 않았다(별칭에 닿는 길은 열려 있었다는 양성 대조). 둘 가운데 하나라도 없으면 측정으로 세지 않는다. 앞 판은 500만 봤다(PR 567 봇이 짚어 이번에 고쳤다). 이번 실행의 두 회차는 둘 다 표지를 보였다.
- 03이 들인 예외는 표지 파일 `/etc/agent-os/image`와 `AGENT_OS_CONTAINER_NETWORK=1`이 함께 있어야 켜진다(코드를 읽었다, `web/apps/admin/tools/loopback.ts`). `deploy/images/admin.Dockerfile`은 `next build` 단계에서 둘을 켜 상류가 `serve`인 채 `.next`가 만들어지게 하고, 이미지의 실행 환경에는 `AGENT_OS_CONTAINER_NETWORK`를 넣지 않는다. 그래서 시작 때는 운영자(compose)가 이 변수를 주어야 하고, 빠지면 `--hostname 은 루프백만 받는다 ... 받은 값: 0.0.0.0` 진단과 함께 종료 1(2.9초)이었다(손으로 봤다, 일지).
- 시작 때 바꿔 넣는 길: 그 `admin-full`의 `routes-manifest.json`에서 `http://127.0.0.1:8000`을 `http://serve:8000`으로 root가 바꾸고 다시 띄우자 다른 컨테이너로 중계했다(200). 산출물에 쓸 수 있어야 하는 길이라 읽기 전용 루트 파일 시스템과는 함께 못 쓴다(어림).
- 예외를 둘 자리(코드를 읽었다): 상류는 `tools/loopback.ts`의 `upstreamProblem`(그것을 `next.config.ts`가 dev·build·start에서 부른다), 바인딩은 같은 파일의 `bindingProblem`(그것을 `tools/start.ts`가 부른다).

### 5. 상태 확인 명령

이미지에 curl·wget이 없어 node로 건다. 후보는 `node -e "fetch('<url>').then(r=>process.exit(r.ok?0:1),()=>process.exit(1))"`이다.

- 관리 화면에 `http://127.0.0.1:3000/`을 걸면 healthy, 듣지 않는 포트(3999)에 걸면 unhealthy였다(쟀다, `common-health`). 확인 한 번은 Health 기록의 Start→End로 183~503ms였다.
- portal에 `/portal/health`를 걸면 healthy였다(쟀다, `portal`, 두 번). 확인 한 번은 247~519ms였고, 한 번은 6,006ms가 기록됐다(`--health-timeout 5s`인데 종료 코드 0으로 남았다. 앞 판에도 14,784ms가 한 번 있었다. 까닭은 보지 못했다).
- 위젯에 `http://127.0.0.1:3000/widget`을 걸면 빌드 중(빌드 시작 6초 뒤)에는 마지막 확인의 종료 코드가 1인 채 상태가 `starting`이었고, 선 뒤에는 healthy·0이었다(쟀다, `widget-time`, 네 번). `--health-start-period 600s`, 간격 2초, 시작 간격 1초, 재시도 3으로 걸었다. 확인 한 번은 269~1,312ms였다.
- 위젯이 컨테이너 시작에서 첫 200까지 걸린 시간(이번 측정의 `widget-time`에서 37.7~68.4초, 앞 판은 13.6~40.7초. 1절의 손으로 본 값은 30.4~71.3초)이 시작 유예(start period)보다 길면 빌드 중의 실패가 재시도에 세어 unhealthy가 된다(Docker의 정의에서 미룬 어림, 짧은 유예로는 재지 않았다).

### 6. docker stop과 init

`docker stop -t 10`. 쟀다(`common-stop`, `portal`, `widget-time`).

| 컨테이너 | init 없음 | `--init` |
|---|---|---|
| 관리 화면 `next start`(pid 1이 `next-server`) | 1.50~4.47초, 종료 143(두 번) | 1.14초, 143 |
| 관리 화면 standalone `server.js` | 0.70~1.16초, 143(두 번) | 0.56초, 143 |
| portal(pid 1이 node) | 12.58초, 137 | 1.12초, 143 |
| 빌드 중인 위젯(pid 1이 `entry-widget.sh`) | 11.88초, 137 | 1.55초, 143 |
| 선 뒤의 위젯(pid 1이 `next-server`) | 1.70~5.73초, 143(세 번, `widget-time`) | 2.11초, 143(`widget-time`) |

- 137은 유예 10초를 다 쓴 뒤 SIGKILL을 받은 것이다. portal은 init 없이 pid 1이 되면 SIGTERM에 끝나지 않았고, 위젯은 빌드 동안 pid 1인 셸이 SIGTERM을 받고도 끝나지 않았다. `--init`(Docker의 `docker-init`)이면 둘 다 143이었다. 실제 이미지는 tini가 그 자리에 선다(손으로 봤다, 일지).
- init 없이는 pid 1이 서비스 자신(`next-server`, portal은 node)이고, 고아를 거두지 않는다. 위 표의 회차가 멈추기 직전에 센 좀비에는 프로브의 몫이 섞였다. 진입 스크립트가 띄운 `wait.mjs`(첫 200을 기다리는 node)가 exec 뒤 서비스의 자식으로 남아, 끝나면 거두어지지 않는다.
- 그것을 가른 `zombie` 섹션(쟀다, 갈래마다 세 번. 서비스가 선 뒤 5초를 두고 `/proc`에서 센다): 관리 화면을 `wait.mjs`와 함께 띄운 대조는 셋 모두 좀비 1(`10<-1:MainThread`, 부모가 pid 1인 node), `wait.mjs` 없이 띄운 관리 화면은 셋 모두 0이었다. 관리 화면 회차가 좀비 하나를 센 것은 이 프로브의 몫이다. portal도 같은 진입 스크립트로 `wait.mjs`를 띄웠으므로 같다고 본다(어림. portal을 `wait.mjs` 없이 띄운 갈래는 없다).
- 위젯은 `wait.mjs` 없이도 init이 없으면 좀비가 남는 회차가 있었다. `zombie` 섹션 세 회차 가운데 둘(`91<-1:MainThread` 둘), `widget-time`의 init 없는 세 회차 모두(`wait.mjs`의 몫을 뺀 `210<-1`, `183<-1`, `236<-1`)이다. `--init`이면 `zombie` 섹션 세 회차 모두 0이었고, `widget-time`의 `--init` 회차에는 `wait.mjs`의 것(`776<-7`, 부모가 pid 7인 서비스)뿐이었다. 앞 판(bookworm·uid 1000)도 같은 모양이었고 trixie·uid 10001에서 달라진 것은 없다. 부모가 pid 1이고 pid가 작아 빌드가 띄운 node 프로세스가 고아로 pid 1에 붙은 것으로 보고, init이 없으면 서비스(`next-server`)가 그것을 거두지 않는다(어림. 좀비는 명령줄이 비어 어느 프로세스였는지는 재지 않았다). 좀비 하나는 pid 하나를 차지할 뿐이지만 restart로 빌드를 거듭하면 쌓일 수 있다(어림).

### 7. 읽기 전용 루트 파일 시스템과 쓰는 자리

- 관리 화면 셋(`admin-full`, `admin-prod`, `admin-standalone`)은 `--read-only`로 uid 10001이 서서 `/`와 `/runs`가 200이었고, 쓰기 시도는 `Read-only file system`으로 실패했다(쟀다, `common-readonly`).
- portal은 `--read-only`, `--network none`, 설정 볼륨 `:ro`로 섰다. `docker diff`에는 볼륨을 붙인 자리(`/cfg`)와 `--init`의 `docker-init`만 있었다(쟀다, `portal`).
- 위젯은 빌드가 쓴다. `widget-lean-typegen`을 root로 띄워 빌드하고 서자 `docker diff`의 바뀐 자리는 `apps/widget/.next`, `apps/widget/public/element.js`, `apps/widget/public/fonts`, `/tmp/node-compile-cache/v24.22.3-x64-...`였다(쟀다, `widget-user`). `next typegen`으로 미리 만든 `next-env.d.ts`는 바뀌지 않았다. typegen 없는 `widget-full`을 root로 띄운 앞 판의 손 실행에서는 `next-env.d.ts`도 바뀌었다(손으로 봤다).
- 저장소의 `web/apps/widget/public`에는 추적하는 파일이 없다(`git ls-files`). 그 폴더는 빌드가 모두 만든다.
- `--read-only`에 `.next`와 `public`만 uid 10001 소유 tmpfs(`--tmpfs <앱>/.next:uid=10001,gid=10001`, `public`도 같게)로 주면 uid 10001이 빌드하고 섰다. 루트에 쓰기는 `Read-only file system`으로 실패했다(쟀다, `widget-user`, 한 번. 빌드 48.7초, 최고치 1,303MiB). 앞 판은 최고치 1,591MiB로 다른 회차보다 컸고 tmpfs에 쓴 산출물이 컨테이너의 메모리 cgroup에 든 탓으로 봤으나(어림), 이번 회차의 최고치는 다른 회차보다 작아 그 어림을 뒷받침하지 못한다. tmpfs 산출물이 메모리를 얼마나 쓰는지는 가르지 못했다.

### 8. root 아닌 사용자로 위젯 빌드

- 이미지의 나무가 root 소유인 채(`widget-full`) uid 10001로 띄우면 `EACCES: permission denied, mkdir '/app/web/apps/widget/public/fonts'`, 종료 1(시작 뒤 3.0초)이었다(쟀다, `widget-user`).
- `.next`와 `public`을 uid 10001 소유로 만든 이미지(`widget-lean-typegen`)를 다른 uid(12345)로 띄워도 같은 `EACCES ... mkdir '.../public/fonts'`, 종료 1(3.9초)이었다(쟀다, `widget-user`). 이 이미지는 지을 때 정한 uid로만 뜬다. 임의의 uid로 띄우는 환경이면 쓰는 자리의 권한을 그룹에도 열어야 한다(어림, 재지 않았다).
- 아래 두 항목과 마지막 항목은 앞 판(uid 1000)에서 손으로 본 것이고 uid 10001로 다시 보지 않았다. 사용자 번호만 다른 같은 파일 소유 문제라 같다고 본다(어림). `.next`와 `public`만 쓰게 tmpfs로 주고 `next-env.d.ts`가 없으면 `Running TypeScript ...` 뒤 `EACCES: permission denied, open '/app/web/apps/widget/next-env.d.ts'`로 실패했다(손으로 봤다).
- root가 미리 지은 `next-env.d.ts`(내용이 맞는 288바이트)가 있으면 `.next`·`public`만 쓰기 가능해도 앱 사용자의 빌드가 끝났다(손으로 봤다). 이미지를 지을 때 `next typegen`이 같은 `next-env.d.ts`와 `.next/types`를 만든다. `widget-*-typegen` 갈래가 이 길이고, `widget-time`의 uid 10001 회차가 모두 이 이미지로 섰다(쟀다).
- `NEXT_TELEMETRY_DISABLED=1`이면 HOME에 쓰지 않았다. 앱 사용자에게는 이미지의 `/tmp/node-compile-cache`(root 소유)가 쓰기 불가라 그 캐시는 쓰이지 않고 빌드는 끝났다(손으로 봤다).

### 9. portal을 띄우는 요건

쟀다(`portal`. `portal-fixture.mjs`가 root로 이름 붙은 볼륨에 설정·사이트 파일·키를 만든다).

- root가 만든 개인 키(0600, root 소유)를 uid 10001이 읽으면 `구성 오류:` 다음 `portal.private_key: 읽지 못한다`, 종료 1.
- 키를 uid 10001 소유로 바꾸면 `--user 10001:10001 --network none --read-only`, 볼륨 `:ro`로 `위젯 미리보기 페이지가 http://127.0.0.1:3100/portal/ 에 섰다. 사이트 1개.`가 찍히고 `/portal/health`가 200(`{"status":"ok"}`)이었다. 네트워크 장치는 `lo`뿐. 컨테이너 시작에서 첫 200까지 1.36~2.03초(두 번, 앞 판은 3.07~8.15초), 서는 중 `memory.current` 55~58MiB.
- uid 10001이 빈 새 이름 붙은 볼륨(root 소유 755)에 `tools/make-key.ts`로 키를 만들면 `개인 키를 쓰지 못했다(EACCES)`, 종료 1.
- 시작 인자는 `--config <설정 TOML>`과 `--site-file <사이트 파일>` 둘 다 반드시 든다(`tools/start.ts`, 코드를 읽었다). 설정이 개인 키 경로(`[portal] private_key`)와 듣는 주소를 든다.

### 10. 사이트 파일이 없거나 깨졌을 때(위젯)

쟀다(`widget-sitefile`, uid 10001, `widget-lean-typegen`). 실패하는 다섯 경우는 모두 빌드 전에 멈춰 시작 뒤 2.5~9.0초에 종료 1이었다(앞 판은 1.7~2.6초. 9.0초는 첫 회차이고 나머지는 2.5~4.5초).

- 없는 파일: `사이트 파일 /probe/none.toml 을 받아들일 수 없다(AGENT_OS_SITE_FILE, ADR 0023).` 다음 줄 `- 파일이 없다`.
- 빈 값: `AGENT_OS_SITE_FILE 가 비었다. 사이트 파일의 경로를 주거나 변수를 뺀다.`
- 디렉터리: `- 읽을 수 없다(EISDIR: illegal operation on a directory, read)`.
- 깨진 파일(`sites_broken.toml`): `- sites[0].unknown_probe_key: 모르는 키다`, `- sites[0].issuer: 빠졌다`(앞 판의 손으로 본 실행에서는 `- sites[0].public_keys: 빠졌다`도 함께 나왔다).
- 실행 uid가 읽지 못하는 파일(root 소유 0600을 볼륨으로 붙임): `- 읽을 수 없다(EACCES: permission denied, open '/cfg/sites.toml')`.
- 변수를 주지 않으면 멈추지 않고 빌드하고 섰고, `/widget`의 CSP는 `frame-ancestors 'none'`이었다. 어느 사이트에도 끼워 넣을 수 없는 위젯이 조용히 뜬다.

### 11. 사이트 파일을 바꾸고 다시 띄우기(위젯)

쟀다(`widget-reflect`, 한 번). 사이트 파일 A를 이름 붙은 볼륨(`:ro`)에 두고 uid 10001로 띄운 뒤, 볼륨의 파일을 B로 바꾸고 같은 컨테이너를 `docker restart -t 10`했다.

- 처음 실행은 A로 섰다(빌드 45.9초, 전체 48.4초, 최고치 1,491MiB, 1분 부하 6.20, 밖의 컨테이너 1개).
- 다시 띄운 실행은 B로 다시 빌드하고 섰다. CSP가 `frame-ancestors https://probe-b.example https://www.probe-b.example:8443`이고 `element.js`에 B의 `request_chars`(583927)가 있고 A의 것(771133)은 없었다(회차의 측정 표지). 다른 이미지를 짓지 않고 사이트 파일만 바꿔 다시 띄우면 반영된다.
- 다시 띄울 때 앞 빌드의 `.next`가 남아 있었고(`prior-build present`), 그 빌드는 66.3초(컴파일 12.7초, 타입 검사 31.8초), 최고치 908MiB였다. 앞 판은 19.2초, 896MiB였다. 최고치는 처음 빌드(1,491MiB)보다 작았다는 점이 앞 판과 같고, 시간은 이번에 처음 빌드보다 길었다(한 번이라 범위가 아니고 부하에 따라 흔들린다). `.next`를 tmpfs로 준 읽기 전용 갈래는 다시 띄울 때 tmpfs가 비어 늘 처음부터 빌드한다고 본다(어림, 재지 않았다).

## 결과를 본 뒤 바꾼 것

- `pnpm install --filter "@agent-os/widget..."`가 뿌리의 개발 의존성까지 깔아(`deps-widget-filter` ≈ `deps-full`) 처음에 둔 "filter에서 시험 파일만 지운" 갈래가 뜻이 없어졌다. 뿌리 개발 의존성을 모두 빼는 lean 갈래(`prune-manifests.mjs`)로 바꿨다.
- 첫 `build` 실행의 lean 이미지에서 `/root/.cache/pnpm` 412MB를 보고 모든 설치 단계에 메타데이터 캐시 마운트를 더했다. 첫 실행(갈래를 바꾸는 도중의 실행이라 바뀐 단계 하나가 측정 아님)의 크기는 버렸다.
- `strip-tests.sh`의 첫 판은 `.storybook`을 통째로 지워 운영 빌드의 타입 검사가 `*.css?inline` 선언을 잃었다. `.storybook`의 `*.d.ts`는 남기게 고치고 셋째 `build` 실행으로 다시 지었다(크기는 셋째 실행의 값이다. 둘째와 0.1MiB 안에서 같았다).
- 위젯 빌드의 시간 구간 가운데 타입 검사가 얼마인지 보려고 `widget-lean-notc` 갈래를 더했다.
- 텔레메트리를 켠 갈래의 표지로 처음에는 `next telemetry status`를 쓰려 했으나, 켠 빌드 뒤에도 `Disabled`를 답해(손으로 봤다) 빌드 기록의 안내 줄로 바꿨다.
- 첫 관리 화면·portal 실행의 좀비 수가 프로브의 `wait.mjs`를 셀 수 있어, `wait.mjs` 없이 세는 `zombie` 섹션을 더했다. 첫 판은 갈래마다 한 번이라, 위젯의 여분 좀비가 회차마다 갈린 것(6절)을 보고 `--rounds`만큼 되풀이하게 고쳐 다시 돌렸다.

## 재지 못한 것

- 리눅스 호스트의 Docker Engine. 이 측정은 Windows의 Docker Desktop(WSL2 커널)에서 돌았다.
- 호스트 폴더를 붙이는 바인드 마운트의 소유자와 모드(이름 붙은 볼륨만 썼다).
- 압축 크기, 레지스트리 푸시·풀 시간.
- 다른 컨테이너(nginx)에서 오는 요청. 세 프로세스는 루프백에만 묶여, 다른 컨테이너에서 닿는 길은 루프백 예외 티켓(03)이 코드에 들였고, 관리 화면의 중계가 다른 컨테이너의 상류에 닿는 것은 이 프로브의 `admin-exception`이 그 코드의 예외를 켜서 봤다(4절).
- 위젯을 지을 때 정하지 않은 uid로 띄우는 길(쓰는 자리의 그룹 권한). 다른 uid가 멈추는 것만 봤다(8절).
- 상태 확인의 시작 유예를 빌드 시간보다 짧게 준 갈래. 600초만 걸었다(5절).
- CPU 수가 위젯 빌드 시간에 주는 효과. `--cpus 2` 한 번뿐이고 부하가 흔들렸다(1절).
- 메모리 제한의 문턱(1g와 2g 사이)과 스왑을 허용한 제한(1절).
- `.next`를 tmpfs로 준 위젯을 다시 띄울 때의 빌드 시간(11절).
- init 없는 위젯에 남는 좀비가 어느 프로세스였는지(6절). 좀비는 명령줄이 비어 `comm`(`MainThread`)과 부모만 남는다.
- portal 상태 확인 한 번이 14,784ms로 기록된 까닭(5절).
- standalone 이미지에 시작 래퍼의 루프백 검사를 다시 얹는 길(4절).

## PR 직전 리뷰가 좁힌 측정 조건(2026-11-14)

위 결과를 낸 실행 뒤에 CodeRabbit CLI가 짚어 측정 조건을 좁혔다. 좁힌 판은 다시 돌리지 않았다.

- `section_admin_upstream`의 "시작 때 환경 변수" 회차: 중계 응답이 두 가짜 상류의 토큰(`built`, `startenv`) 가운데 정확히 하나를 실었을 때만 측정으로 센다. 기록한 회차는 4절 둘째 항목의 "`/api/ping`은 `built`에서 왔다"가 `built` 토큰을 이미 보였다. `startenv`가 없었다고는 적지 않았지만, 가짜 상류는 본문에 자기 토큰 하나만 싣는다(`upstream-stub.mjs`).
- `section_common_stop`의 빌드 중인 위젯 회차: 같은 기록 읽기에서 `build-start` 줄이 있고 `build-exit` 줄이 없을 때만 빌드 중으로 센다. 기록한 회차는 기록으로는 가를 수 없다. 6절 표는 멈출 때 pid 1이 `entry-widget.sh`였다고 적어 서비스로 갈아탄 뒤가 아니었다는 것만 보이고, 빌드 시작 시각은 적지 않았다(진입 스크립트의 `build-start` 줄 앞에는 기다리는 명령이 없다).
- `zombie_round`의 대조 갈래(관리 화면을 `wait.mjs`와 함께): 부모가 pid 1인 좀비를 하나 이상 찾았을 때만 측정으로 센다. 기록한 회차는 6절 셋째 항목의 "대조는 넷 모두 좀비 1(`10<-1:MainThread`, 부모가 pid 1인 node)"이 이미 그 표지를 보였다.
- `sweep`과 시작 때의 정리(정리 흐름): 만드는 자원의 라벨을 `ri-web-probe=<실행 토큰>`으로 바꾸고 끝날 때 그 토큰의 것만 지운다. 시작할 때 라벨 키가 붙은 것을 모두 지우던 판은 같은 프로브를 함께 돌리는 다른 실행의 컨테이너·볼륨·네트워크를 지울 수 있어, 그런 자원을 세어 알리기만 하게 바꿨다. 끊긴 앞 실행이 남긴 자원을 저절로 치우던 몫은 잃었다(손으로 지운다). 기록한 실행에는 측정 아닌 회차가 없어(근거의 종류) 다른 실행에 자원을 잃은 회차는 없었다.
- `fetch.mjs`(시간 제한): `--timeout`은 소켓의 비활성 기한이라 조각이 계속 오는 응답을 끊지 못한다. 요청 전체의 기한 `--deadline`(기본 40초, 부르는 `docker exec`의 60초 제한보다 짧다)을 더해, 닿으면 그때까지 본 것을 `partial`에 담아 찍고 그 회차는 측정이 아니게 했다. 전에도 `run.py`의 60초 제한으로 프로브는 끝났지만 그때까지 본 것은 잃었다(가짜 서버로 손으로 봤다, 세션 스크래치의 `fetch_deadline_check.mjs`·`fetch_old_control.mjs`. 0.2초마다 조각을 보내는 응답에 고친 판은 1.5초 기한에 `partial`을 찍었고, 고치기 전 판은 8초 뒤 끌 때까지 아무것도 찍지 않았다). 기록한 SSE는 마지막 이벤트가 1.62초에 왔다(4절).

## 다시 돌린 기록(2026-11-16, 티켓 08)

명세가 고른 꼴인 `node:24-trixie-slim`(digest 고정)과 uid 10001로 시제품을 바꾸고 `build`와 열여섯 섹션을 모두 다시 돌렸다.

- 바꾼 것: `Dockerfile`의 바탕과 사용자(`base` 단계가 uid·gid 10001 `agentos`를 만든다), `chown node:node`를 `agentos`로, 프로브의 `NODE_USER`와 tmpfs의 uid. `admin-exception` 단계는 03이 코드에 들인 예외를 그대로 켠다(표지 파일 + `AGENT_OS_CONTAINER_NETWORK=1`). 이에 맞지 않는 `patch-admin.mjs`의 `exception` 갈래는 지웠다. `upstream-stub.mjs`에 `/hits`를 더했고, 500 대조 회차가 그 표지를 본다(4절).
- 결과: 측정 아닌 회차가 없었다. 빌드 실패, 좀비의 새 모양, 기능 차이는 없었다. 바탕과 사용자를 바꿔도 명세의 문장(루프백 규칙, 읽기 전용, 143 종료, 사이트 파일 진단)과 다른 결과는 나오지 않았다. 크기는 4.1~9.1MiB 늘었다(2절).
- 명세의 범위를 벗어난 것 하나: 위젯이 뜰 때 걸리는 시간이 명세에 든 13.6~40.7초보다 길었다(`widget-time` 37.7~68.4초). 최고치는 1,356~1,619MiB로 앞 판 기본 회차의 1,476~1,567MiB와 겹치지만 낮은 쪽이 앞 판의 최소보다 낮다. `widget-lean-typegen`의 빌드 시간은 앞 판의 1.9배였다(1절). 같은 VM을 쓰는 다른 세션의 빌드가 함께 돌았을 수 있으나, 부하는 앞 판보다 낮았고, 바탕만 bookworm으로 바꿔 지은 같은 이미지와 번갈아 띄운 비교(판당 세 번)는 trixie 탓인지 가르지 못했다(1절). 원인은 정하지 못했다. 시작 유예의 첫 값이 300초이므로(명세) 이 시간으로도 유예 안에 든다(5절의 어림대로면 unhealthy가 되지 않는다). 티켓의 "크게 벗어나면 멈춘다"는 조건은 1.7~1.9배를 크게로 보지 않고 계속한 판단이며 근거는 유예 안에 든다는 어림 하나다. 명세의 13.6~40.7초는 이 시간으로 다시 쓰이기 전까지 낡은 값이다.
- 확인한 것: `strip-tests.sh`의 `.git` 조상 검사는 이미지 안에서 거부하지 않았다(`build`가 `widget-lean`을 종료 0으로 지었다, 2절).
- 고친 것: `section_admin_upstream`의 500 단언을 기대한 원인의 표지(관리 화면 기록의 `Failed to proxy ...`와 `ECONNREFUSED`, 별칭 서버의 `/hits`)까지 보게 했다(PR 567 봇의 보류 지적).
- 시간: 이 PC에서 다른 세션이 함께 돌아 `build` 1,184초, 아홉 섹션 314초, 위젯 일곱 섹션 1,916초가 걸렸다.
