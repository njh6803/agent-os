# prebuilt_start 프로브

widget-runtime-values 명세가 결정을 내리려고, 미리 지어 둔 위젯 이미지의 컨테이너가 뜰 때 사이트 파일의 두 값(허용 출처, 요청 글자 수 상한)만 받아 서는지를 리눅스 컨테이너에서 잰다. 기능 계획(`.scratch/widget-runtime-values/plan.md`)이 "명세 전에 먼저 확인하라"고 한 것이고, ADR 0064 결정 "허용 출처와 요청 글자 수 상한"이 어림으로 남긴 조합이다. 결정은 명세가 한다. 시제품 Dockerfile과 진입 단계(`entry.mjs`)는 측정용이고 최종이 아니다.

재는 꼴은 이렇다. 위젯을 이미지를 지을 때 사이트 파일 없이 한 번 빌드해 둔다. 그때 위젯 페이지를 품어도 되는 사이트를 알리는 응답 머리는 `frame-ancestors 'none'`으로 굳는다. 컨테이너가 뜰 때 진입 단계가 사이트 파일을 읽어 두 가지만 한다. 지어 둔 응답 머리 목록(`.next/routes-manifest.json`)의 원본에서 그 값을 바꿔 뜰 때 쓰는 파일에 쓰고, 위젯의 스크립트가 받아 갈 값 파일(`public/runtime.json`)을 쓴다. 그 뒤 `next start`만 부른다.

## 다시 돌리기

저장소 루트에서 친다.

```
uv run python .scratch/widget-runtime-values/probes/prebuilt_start/run.py --sections build
uv run python .scratch/widget-runtime-values/probes/prebuilt_start/run.py --sections start,reflect,readonly,sitefile,health,browser [--rounds <되풀이 수>] [--work <원본 출력 폴더>]
```

- 필요한 것: 도는 Docker 데몬(리눅스 컨테이너, BuildKit). `build` 섹션에는 Docker Hub와 npm 레지스트리에 닿는 네트워크가 든다. 다른 섹션은 `build`가 지은 `wrv-img:<단계>` 이미지만 쓴다. `browser` 섹션은 호스트의 node와, 깔린 `web/node_modules`(`pnpm -C web install --frozen-lockfile`)와, 그 판의 Playwright가 받은 Chromium과, 빈 호스트 포트 둘(그 실행이 고른다)이 든다.
- 섹션: `build`, `start`, `reflect`, `readonly`, `sitefile`, `health`, `browser`. 섹션마다 무엇을 표지로 보는지는 그 함수의 독스트링이 원천이다.
- 걸린 시간(이 PC, 2026-11-27): 층 캐시가 찬 채 `--rounds 3`으로 일곱 섹션을 한 명령(`--sections build,start,reflect,readonly,sitefile,health,browser`)으로 돌린 실행 4가 126초였다. 그 앞에는 `health`를 뺀 여섯 섹션에 172초, `readonly`와 `health` 둘에 53초가 걸렸다(셋 다 원본 기록 파일 `raw.log`의 처음과 끝 시각으로 손으로 봤다). `build`의 빌드 단계가 캐시 없이 돌면 그 단계만 64~74초가 더 든다(아래 결과 1).
- `browser`만 호스트 포트를 연다(`127.0.0.1`에만 발행한다). 나머지 섹션의 요청은 `docker exec`로 컨테이너 안에서 건다(`fetch.mjs`).
- 띄운 컨테이너와 볼륨에는 라벨 `wrv-probe=<실행 토큰>`을 달고, 끝날 때 그 실행의 토큰이 붙은 것만 지운다. 시작할 때는 다른 토큰이 붙은 것을 세어 알리기만 한다. 이미지(`wrv-img:*`)와 BuildKit 캐시 마운트는 남는다. 캐시 마운트의 id는 실제 위젯 이미지의 것과 같아(`agent-os-pnpm-store`, `agent-os-pnpm-meta`) 서로 다시 쓴다.
- 원본 출력은 `--work`(없으면 시스템 임시 폴더) 아래 `raw.log`, 회차의 값은 `results.jsonl`에 남는다. 표지를 보지 못한 회차가 하나라도 있으면 종료 코드가 1이다(`tools/probe_kit.py`의 `Rounds`).
- 타입 검사: `uv run pyright -p .scratch/widget-runtime-values/probes/prebuilt_start`(이 폴더의 `pyrightconfig.json`, strict).

## 잰 판

- Windows 10의 Docker Desktop, 엔진 29.9.2(linux/amd64), WSL2 커널 6.18.58.1-microsoft-standard-WSL2, cgroup v2. 리눅스 호스트의 Docker Engine이 아니다.
- 바탕 이미지 `node:24-trixie-slim`, digest `sha256:af02d57b57719b9657a45199a79264a9437940cd55b3c7b3fc99615654f124a0`(실제 위젯 이미지 `deploy/images/widget.Dockerfile`과 같다). 이미지 안의 Node v24.22.3, pnpm 11.24.0, Next 16.3.6. 빌드 단계의 Vite 8.3.1, `@tailwindcss/vite` 4.3.3, TypeScript 5.9.3(`build` 섹션의 "깔린 것" 회차가 적는다). init은 tini다.
- 브라우저는 저장소의 Playwright가 받은 Chromium 153.0.8010.12다(`browser` 섹션이 적는다).
- 저장소는 워크트리 HEAD `e7c53cba3`(origin/dev)의 `web/`이다. 저장소 파일은 고치지 않았고, 고친 판이 필요한 자리(값 파일에 다는 응답 머리 규칙 하나)는 이미지 안의 `next.config.ts` 사본을 고쳤다(`patch-config.mjs`).
- 2026-11-27에 쟀다. 같은 Docker 데몬을 다른 세션이 함께 쓰는 PC라 시간 값은 범위로만 읽는다.

## 파일

| 파일 | 하는 일 |
|---|---|
| `run.py` | 섹션을 돌리고 회차마다 표지를 본다 |
| `Dockerfile`, `Dockerfile.dockerignore` | 시제품 이미지. `base`·`manifests`·`deps-full`은 실제 위젯 Dockerfile의 것과 글자까지 같다. `image`는 뜰 때 쓰는 두 파일을 `/run/agent-os-widget`로 가는 심볼릭 링크로 두고, `image-inplace`는 앱 폴더 안의 보통 파일로 둔다. `build-inspect`는 대조용이다 |
| `entry.mjs` | 시제품 진입 단계. 사이트 파일을 `@agent-os/site-file`의 `buildInput`으로 읽고, 두 파일을 쓰고, 같은 프로세스에서 `next start`를 부른다 |
| `patch-config.mjs` | 이미지 안 `next.config.ts` 사본에 값 파일의 `Access-Control-Allow-Origin: *` 규칙을 더한다 |
| `inspect.mjs` | 이미지 안에서 지어 둔 응답 머리 목록과 깔린 패키지를 들여다본다 |
| `fetch.mjs`, `wait.mjs` | 컨테이너 안에서 요청 하나를 걸고, 첫 200의 시각을 찍는다 |
| `browser.mjs` | 호스트의 Chromium으로 사이트 페이지 둘이 위젯을 iframe으로 품어 본다 |
| `sites_a.toml`, `sites_b.toml`, `sites_broken.toml` | 프로브의 사이트 파일. A와 B는 허용 출처와 상한이 다르고, 세 번째는 필수 칸이 빠졌다 |

## 근거의 종류

아래 결과에서 "쟀다"는 `run.py`가 다시 내는 것이고 두 가지다. 하나는 `run.py`가 그 회차의 표지로 단언한 것이다. 어긋나면 그 회차가 측정 아님이 되고 종료 코드가 1이다. 다른 하나는 측정인 회차마다 `run.py`가 값으로 적는 것이다. 시간, 메모리, 크기, 끌 때의 종료 코드 143이 그렇고, 단언이 아니라서 아래에 범위로 옮겨 적었다. 결과는 2026-11-27의 네 실행에서 낸다. 실행 1은 `health`를 뺀 여섯 섹션 전체(32회차), 실행 2는 결과 이름을 고친 뒤의 `readonly,sitefile`(10회차), 실행 3은 회차를 더한 뒤의 `readonly,health`(11회차), 실행 4는 단언하는 표지를 넓힌 뒤의 일곱 섹션 전체(37회차)이고, 넷 모두 측정 아닌 회차가 0이었다(합쳐 90회차). 그 앞에 `build`만 돌린 실행 하나는 "깔린 것" 회차가 측정 아님이었고, 아래 "결과를 본 뒤 바꾼 것"이 그 까닭을 적는다. "손으로 봤다"는 명령을 한 번 쳐서 본 것이고 프로브가 다시 내지 않는다. "어림"은 재지 않은 것이다.

## 결과

### 1. 이미지(`build`)

- 여섯 단계가 모두 지어졌다(쟀다). 뜬 뒤의 이미지(`image`)는 690.6MiB였다. 같은 실행에서 워크스페이스 전체 의존성 단계(`deps-full`)는 881.9MiB, 위젯과 그것이 기대는 워크스페이스 패키지의 운영 의존성만 깐 단계(`deps-prod`)는 666.9MiB였다. `image` 안에서 `.next`는 22MB, `public`은 7MB, `node_modules`는 480MB였다(`du -sm`, 쟀다).
- `image`에는 next 16.3.6이 깔려 있고 빌드 도구 셋(vite, `@tailwindcss/vite`, typescript)은 없다. 같은 도우미가 전체 의존성 위에 지은 단계(`build-inspect`)에서는 넷 모두 판을 냈다(쟀다. 없다는 답이 도구가 실제로 없어서라는 대조다).
- 지어 둔 응답 머리 목록의 원본에서 `frame-ancestors`가 든 응답 머리는 정확히 하나(`source`는 `/widget/:path*`)이고 값은 `frame-ancestors 'none'`이었다. `.next` 아래에서 `frame-ancestors`라는 글이 든 파일은 그 목록의 원본과 뜰 때 쓰는 사본 둘뿐이었다(쟀다, `image-inplace`에서. `image`에서는 뜰 때 쓰는 파일이 링크다). 값 파일에 건 응답 머리 규칙도 그 목록에 하나 들어 있었다.
- 이미지를 지을 때의 Next 빌드 단계는 캐시 없이 64.2초와 73.8초였다(두 번. 앞의 것은 손으로 친 `docker build`의 기록에서, 뒤의 것은 `build` 섹션의 첫 실행에서 봤다. 이 단계의 시간은 층 캐시가 차면 0에 가까워 프로브가 다시 내지 않는다). 그 기록에 Next의 빌드 머리말 "Creating an optimized production build"가 있었다(손으로 봤다. 결과 2가 "뜰 때는 이 글이 없다"를 표지로 쓴다).

### 2. 빌드 없이 서는가(`start`)

- 사이트 파일 A로 띄운 회차는 실행 1과 실행 4에서 일곱씩 열넷이고(실행마다 `image` 셋, `image-inplace` 셋, CPU 하나와 메모리 256MiB로 제한한 `image` 하나), 모두 빌드 없이 서서 A의 두 값을 냈다(쟀다). 두 실행이 함께 단언한 표지는 셋이다. 실행 4는 이 절 마지막 항목의 머리들도 표지로 단언했다. 페이지와 페이지 안 번들의 응답 머리가 `frame-ancestors https://probe-a.example`이고, 값 파일이 200과 `{"allowedOrigins":["https://probe-a.example"],"requestChars":771133}`을 내며, 컨테이너의 `BUILD_ID`가 이미지의 것과 같고 기록에 빌드 머리말이 없다.
- 시간은 네 실행에서 시간을 찍은 회차 마흔(`start` 열넷, `reflect` 여덟, `readonly`의 뜬 회차 열여덟)에서 컨테이너 시작부터 첫 200까지 0.61~1.78초였다. 가장 긴 것이 CPU 하나와 256MiB로 제한한 실행 1의 회차이고(같은 제한을 건 실행 4의 회차는 0.88초였다), 제한 없는 회차는 0.61~1.67초였다. 진입 단계는 0.008~0.029초, Next가 찍은 `Ready in`은 126~453ms였다. 실행 4의 열여섯 회차만 보면 첫 200까지 0.61~0.88초였다.
- 메모리 최고치(cgroup의 `memory.peak`)는 제한 없는 서른여덟 회차에서 88.9~95.6MiB, 256MiB로 제한한 두 회차에서 78.3MiB와 81.6MiB였다. 요청 몇 개를 받은 뒤의 값이고 오래 띄운 값이 아니다.
- `docker stop`은 끄기를 잰 스물여덟 회차에서 0.16~1.16초에 종료 코드 143으로 끝났다(tini가 첫 프로세스다. 종료 코드는 회차마다 적는 값이고 표지로 단언하지 않는다).
- 뜰 때 빌드하지 않았다는 판단은 세 관찰이 함께 받친다. `BUILD_ID`가 같고, 빌드 머리말이 없고, 첫 응답까지의 시간과 메모리가 빌드를 담을 수 없는 크기다. 지금의 뜰 때 빌드는 release-image의 측정에서 빌드만 19.7~29.9초, 메모리 최고치 1,452~1,567MiB였다(`.scratch/release-image/spec.md`의 "이미지의 구성"을 읽었다). `next build`가 `BUILD_ID`를 새로 짓는다는 것은 Next의 동작으로 아는 것이고 이 프로브가 대조로 보이지는 않았다(어림).
- 값 파일의 응답은 `content-type: application/json; charset=UTF-8`, `cache-control: public, max-age=0`, `access-control-allow-origin: *`와 약한 ETag를 달았다. 페이지 안 번들과 글꼴 파일의 `Access-Control-Allow-Origin: *`는 그대로였다. 응답 머리의 `source`가 `/widget` 아래 전부라 값 파일, 페이지 안 번들, 없는 경로(404)의 응답에도 같은 `frame-ancestors` 값이 붙었다. 페이지의 응답은 `cache-control: s-maxage=31536000`이었다(미리 그려 둔 페이지다). 이 항목의 머리들은 실행 1에서는 적기만 한 값이었고, 실행 4의 일곱 회차가 표지로 단언했다(값 파일의 내용의 종류와 캐시 머리와 비지 않은 ETag, 값 파일과 없는 경로의 `frame-ancestors`, 글꼴의 `Access-Control-Allow-Origin`, 페이지의 `s-maxage=31536000`). ETag가 약한 꼴(`W/`)이라는 것은 적힌 값에서 읽었고 단언하지 않는다.

### 3. 사이트 파일을 바꾸고 다시 띄우기(`reflect`, `readonly`의 마지막 회차)

- 이름 붙은 볼륨의 사이트 파일을 A에서 B로 바꾸고 `docker restart`로 다시 띄운 열두 회차(실행 1과 실행 4의 `image` 셋과 `image-inplace` 하나씩, 네 실행마다 하나씩인 읽기 전용 루트의 `image` 넷)가 모두 빌드 없이 B의 두 값을 냈다(쟀다). 응답 머리는 `frame-ancestors https://probe-b.example https://www.probe-b.example:8443`으로, 값 파일은 그 두 출처와 583927로 바뀌었다. 값 파일의 ETag도 바뀌었다(실행 4의 다섯 회차가 표지로 단언했다. 앞 세 실행에서는 적힌 값에서 읽었다).
- 떠 있는 동안 사이트 파일만 바꾸면 값이 그대로라는 것은 재지 않았다. 진입 단계가 뜰 때 한 번만 쓰므로 그렇다고 본다(어림).

### 4. 읽기 전용 루트(`readonly`)

- `image`를 읽기 전용 루트, 능력 모두 빼기, `no-new-privileges`, 네트워크 없음, `/run/agent-os-widget`의 tmpfs 하나(`uid=10001,gid=10001,mode=0700`)로 띄운 회차가 실행마다 셋씩 열두 번 모두 A의 두 값을 냈다(쟀다). 그 회차마다 앱의 `public`과 `/tmp`에 쓰기가 "Read-only file system"으로 거절됐고, tmpfs 폴더에는 써졌으며, 그 폴더가 `/proc/mounts`에 tmpfs로 있었고, 요청 뒤의 기록에 `EROFS`도 `EACCES`도 없었다. Next가 `public` 안의 심볼릭 링크를 따라가 값 파일을 냈고, 링크인 응답 머리 목록도 읽었다.
- 단독 compose가 web 컨테이너에 주는 꼴 그대로 읽기 전용 하나만 건 회차도 같았다(쟀다, 실행 3과 실행 4에서 한 번씩).
- 대조 둘은 같은 제한에서 서지 않았다(쟀다, 실행마다). tmpfs를 뺀 `image`와 링크 없는 `image-inplace`는 진입 단계가 응답 머리 목록을 쓰다 `EROFS`로 끝났고 Next를 부르지 않았다. 그래서 읽기 전용 루트에서 서게 한 것은 tmpfs 폴더와 링크다.
- 읽기 전용 회차 열여덟의 메모리 최고치는 89.1~95.6MiB로, 쓰기 가능한 루트로 띄운 회차 스물(실행 1과 실행 4의 `start`의 제한 없는 여섯씩과 `reflect`의 넷씩)의 88.9~95.6MiB와 겹친다. tmpfs에 쓴 두 파일이 최고치를 눈에 띄게 올리지 않았다는 뜻으로 읽는다(두 파일의 크기는 따로 재지 않았다).

### 5. 사이트 파일이 없거나 깨졌을 때(`sitefile`)

- 없는 파일과 깨진 파일은 진입 단계가 지금의 빌드가 내는 것과 같은 진단("파일이 없다", "모르는 키다" 등)을 찍고 Next를 부르지 않은 채 종료 1로 끝났다(쟀다, 실행 1과 2와 4에서 한 번씩. 이 절의 다른 회차도 같다).
- 사이트 파일의 환경 변수를 주지 않으면 멈추지 않고 섰고, 응답 머리는 `frame-ancestors 'none'`, 값 파일은 빈 허용 출처와 기본 상한 20000이었다(쟀다). 어느 사이트도 품지 못하는 채로 조용히 뜨는 것이라, 실제 이미지는 지금처럼 사이트 파일의 자리를 늘 넘겨야 한다.
- 진입 단계를 건너뛰고 `next start`를 바로 부르면 `image`에서는 뜰 때 쓰는 응답 머리 목록이 끊긴 링크라 Next가 그 파일을 열지 못하고(`ENOENT`) 종료 1로 끝났다(쟀다). 값을 바꿔 넣지 않은 채 뜨는 길이 `image`에는 없다.
- 서지 않는 세 회차(없는 파일, 깨진 파일, 진입 단계를 건너뛴 시작)의 종료 코드가 1이라는 것은 실행 4가 표지로 단언했다. 앞의 두 실행은 0이 아닌 것만 단언했다.

### 6. 상태 확인(`health`)

- compose의 위젯 상태 확인과 같은 node 한 줄을, compose의 공통 값(간격 30초, 제한 10초, 재시도 3, 시작 간격 2초)에 시작 유예 30초를 둔 옵션으로 달고 읽기 전용 루트의 `image`를 띄우자, 실행 3과 실행 4의 세 회차씩 여섯 회차 모두 띄우기 시작한 뒤 2.59~2.66초에 healthy가 됐다(쟀다. 첫 확인이 시작 간격 2초 뒤에 돈다).
- 대조로 같은 명령을 아무도 듣지 않는 포트에 걸면 지켜본 25초 동안 Docker에 남은 확인 기록이 모두 종료 코드 1이었고 상태는 starting으로 남았다(쟀다, 두 실행에서 한 번씩). 남은 기록은 두 번 모두 다섯이었다. Docker가 최근 기록만 남기는 것으로 알고 있어(재지 않았다) 그 수를 돈 확인의 수로 읽지 않는다.
- 다른 점: compose는 그 명령을 셸 없이 부르고(`CMD`) 프로브의 `docker run --health-cmd`는 `sh -c`로 부른다. 유예가 끝난 뒤 재시도 셋을 다 써 unhealthy가 되는 데까지는 지켜보지 않았다.

### 7. 브라우저(`browser`)

- 읽기 전용 루트로 띄운 `image`를 호스트의 Chromium이 사이트 페이지 둘로 품어 봤다. 사이트 파일의 허용 출처가 `http://allowed.localhost:<포트>` 하나일 때 그 출처의 페이지의 iframe에는 위젯의 문서가 실렸고, 다른 출처(`other.localhost`)의 페이지의 iframe은 Chromium의 오류 페이지로 끝났으며 콘솔 오류가 바꿔 넣은 `frame-ancestors` 값을 들었다(쟀다. 이 절의 두 회차는 실행 1과 실행 4에서 돌았다).
- 허용 밖 출처의 문서에서 `fetch`로 값 파일을 받으면 두 값이 읽혔고, 같은 `fetch`로 `Access-Control-Allow-Origin`이 없는 위젯 페이지를 받으면 실패했다(쟀다. 값 파일이 읽힌 것이 그 머리 덕이라는 대조다). 페이지 안 번들이 사이트의 문서에서 값 파일을 받는 길과 같은 교차 출처 요청이다.
- 사이트 파일의 허용 출처를 `other`로, 상한을 583927로 바꾸고 다시 띄우자 두 페이지의 결과가 뒤바뀌고 값 파일이 새 값을 냈다(쟀다).

## 결과를 본 뒤 바꾼 것

- **깔린 것을 보는 방법.** 첫 판은 패키지의 `package.json`을 `require`로 풀어 판을 읽었다. `build` 섹션의 첫 실행에서 대조 쪽이 빈 답을 내 그 회차가 측정 아님이 됐다. `@tailwindcss/vite`가 `package.json`을 내보내지 않아, 깔려 있어도 `ERR_PACKAGE_PATH_NOT_EXPORTED`로 실패한 것이다(`docker run`으로 패키지마다 손으로 봤다). 그래서 앱 폴더에서 위로 올라가며 `node_modules/<이름>/package.json` 파일이 있는지를 보게 바꾸고, 같은 도우미를 대조 단계(`build-inspect`)에도 쓰게 했다. 첫 판의 방법으로는 `image`에 그 패키지가 있었어도 "없다"가 나왔을 것이다.
- **서지 않는 회차의 결과 이름과 표지.** 첫 판은 서지 않는 회차 다섯에 "next를 부르기 전에 그 까닭으로 끝났다"는 이름 하나를 붙였다. 진입 단계를 건너뛴 회차는 Next를 바로 부른 것이라 그 이름이 틀렸다. 회차마다 이름을 따로 두고, 그 회차의 표지를 `routes-manifest`라는 글에서 `ENOENT`와 `routes-manifest.json`으로, 읽기 전용 대조 둘의 표지를 `EROFS`에서 `EROFS`와 `routes-manifest.json`으로 좁혔다. 고친 판으로 `readonly,sitefile`을 다시 돌려 열 회차가 모두 측정이었다.
- **더한 회차.** 읽기 전용 하나만 건 회차와 `health` 섹션은 첫 전체 실행 뒤에 더했다. 명세가 정할 값(compose의 위젯에 읽기 전용을 주는 것, 시작 유예 30초)이 그 꼴 그대로 서는지 보려는 것이다.
- **넓힌 표지(실행 4).** 명세의 셀프 리뷰가, 결과 2와 3과 5가 "쟀다"로 적은 것 가운데 `run.py`가 적기만 하고 단언하지 않는 것을 짚었다. 값 파일과 없는 경로의 `frame-ancestors`, 값 파일의 캐시 머리와 내용의 종류와 ETag, 글꼴의 `Access-Control-Allow-Origin`, 페이지의 `s-maxage`, 다시 띄운 뒤 ETag가 달라지는 것, 서지 않는 회차의 종료 코드 1이다. 글을 낮추는 대신 `serves`와 `reflect_round`와 `exits_round`가 이것들을 표지로 단언하게 고치고 일곱 섹션 전체를 다시 돌렸고, 37회차가 모두 측정이었다. 기대하는 값은 앞 세 실행이 적은 값에서 옮긴 것이다. 그래서 실행 4가 보이는 것은 같은 이미지가 그 값을 다시 냈다는 것이고, 다른 Next 판에서도 같다는 뜻은 아니다.

## 손으로만 본 것

`run.py`를 쓰기 전에 PowerShell의 `docker run`, `docker logs`, `docker exec`로 `image`를 한 번 띄워 봤다. 진입 단계 약 0.02초, `Ready in 333ms`, 첫 200까지 약 0.97초, `memory.peak` 약 88MiB였고 결과 2의 범위 안이다. Git Bash는 컨테이너 경로 인자(`-e AGENT_OS_SITE_FILE=/probe/…`)를 윈도 경로로 바꿔, 손으로 치는 `docker` 명령은 PowerShell로 쳤다. `run.py`는 셸을 거치지 않고 `docker`를 부른다.

## 재지 못한 것

- 리눅스 호스트의 Docker Engine. 이 프로브가 돈 곳은 Windows의 Docker Desktop이다. 실제 리눅스 엔진 위에서는 단독 배포 e2e가 GitHub의 리눅스 러너에서 처음 본다.
- 호스트 폴더를 붙이는 바인드 마운트. 사이트 파일은 이름 붙은 볼륨이나 이미지 안의 파일로 줬다. 단독 compose는 `./site`를 읽기 전용 바인드 마운트로 붙인다.
- 프록시(nginx)를 거친 요청. 값 파일의 경로는 프록시가 이미 위젯으로 넘기는 `/widget/` 아래다(`deploy/standalone/proxy/site.conf`를 읽었다).
- 위젯의 코드가 값 파일을 받아 쓰는 것. 브라우저의 `fetch`로 받을 수 있는지까지만 봤다. iframe 페이지와 페이지 안 번들이 받은 값으로 토큰을 묻고 입력의 상한을 거는 것은 구현 티켓의 시험이 본다.
- 위젯 시작 래퍼의 루프백 검사와 컨테이너 네트워크 예외. 시제품 진입 단계는 그 래퍼를 거치지 않는다.
- Next의 다른 판. 응답 머리 목록의 모양은 16.3.6에서만 봤다.
- Chromium 밖의 브라우저, 오래 띄운 컨테이너의 메모리, 캐시 없는 이미지 빌드 전체에 걸리는 시간.
