# release-image serve_image 프로브

`release-image` 명세가 정할 `serve` 컨테이너 이미지의 모양을 본 프로브다. 보는 것은 여덟이다. 판 번호를 이미지에 넣는 법, 바탕 이미지와 크기, root가 아닌 사용자와 `getpass.getuser()`, 예시 MCP 서버를 네트워크 없이 띄우기, 쓰는 자리와 소유권, 플러그인 폴더의 첫 채움, init과 종료, 상태 확인 명령이다. 여기서는 결정하지 않고 본 것만 적는다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거"다.

결과는 2026-11-13에 `run.py`를 항목별로 나눠 돌린 것이다(항목마다 실행 토큰과 회차를 적었다). 측정 세션이 한 번 끊기기 전에 스크래치패드의 탐색 스크립트(`explore_*.sh`, 커밋하지 않는다)로 먼저 본 것은 "손으로 본 것"으로 따로 적었다. 프로브가 다시 낸 줄과 값이 같으면 그렇다고 적었다.

근거의 종류는 다섯이다. 프로브가 다시 낸다(`run.py`가 표지를 보고 센 회차), 손으로 봤다(명령과 함께 적는다), 코드를 읽었다(파일과 판을 적는다), 어림, 웹 요약. 이 README는 웹 요약을 쓰지 않았다.

## 요약

명세가 고를 때 쓸 한 줄씩이다. 근거와 갈래는 아래 결과 절에 있다.

1. 판 번호: `pyproject.toml`의 판만 바꾸고 `uv sync --locked`는 실패한다. 의존성을 `--locked`로 먼저 깔고 판을 바꾼 뒤 프로젝트만 `--frozen`(또는 `uv pip install --no-deps .`)으로 깔면 지나고, `agent-os --version`과 `/openapi.json`의 `info.version`이 `0.1.0-rc.1`(태그에서 `v`만 뗀 글자)로 보인다. 정규화 꼴 `0.1.0rc1`은 dist-info 이름과 uv 로그에만 보인다. 판을 넣는 줄은 바탕의 도구에 따라 조용히 안 들 수 있다(alpine의 busybox sed). 프로브가 다시 낸다.
2. 바탕: `deb-py` 382MB(빌드 19~21초), `deb-node` 476MB(47~70초), `alpine` 311MB(44~55초). 셋 모두 serve와 예시 MCP 서버가 돌았다. 프로브가 다시 낸다.
3. 사용자: 이미지가 만든 사용자(uid 10001, passwd 항목 있음)면 채널의 주체가 그 이름이다. passwd 항목 없는 `--user`는 serve가 시작에서 `KeyError: 'getpwuid(): uid not found'` 트레이스백으로 끝나고, `USER`를 함께 주면 선다. 프로브가 다시 낸다.
4. MCP: 전역 설치가 있어도 `npx -y`는(판을 적어도) 레지스트리에 묻고 네트워크 없이 71.5~73.8초 뒤 실패한다. 실행 파일 이름(`mcp-server-everything`)은 네트워크 없이 0.34~1.18초에 답한다. 프로브가 다시 낸다.
5. 쓰는 자리: 실행 파일 이름 매니페스트면 serve는 `--read-only`에서 플러그인 루트와 트레이스 폴더만 쓰면 된다. `npx`는 홈(`~/.npm`)이 쓰기 가능해야 하고 `/tmp`는 없어도 됐다. 리눅스 엔진의 바인드 마운트는 폴더가 컨테이너 uid에 쓰기 가능해야 하고, 아니면 끄기와 실행이 500이다. 프로브가 다시 낸다.
6. 첫 채움: 빈 이름 있는 볼륨은 이미지의 플러그인을 소유자째 한 번 복사하고, 판을 올려도 채워진 볼륨은 바뀌지 않는다. 빈 바인드 마운트는 비어 있고 serve가 기본 모델 없음으로 끝난다. 프로브가 다시 낸다.
7. init: tini와 `--init`은 고아를 거두고 `docker stop`에 정상 종료한다(143). init 없이 agent-os가 pid 1이면 정상 종료는 하나(0) 고아가 좀비로 남는다. 셸로 감싸면 신호가 닿지 않아 SIGKILL(137)이다. 프로브가 다시 낸다.
8. 상태 확인: 이미지에 든 python 한 줄(`urllib`)이 정상·비정상을 가르고 `--health-cmd`로 healthy·unhealthy에 닿는다. 한 번에 0.6초 남짓. 프로브가 다시 낸다.

## 파일

| 파일 | 무엇 |
|---|---|
| `Dockerfile` | 시제품. 바탕 후보 셋을 마지막 타깃 `deb-py`, `deb-node`, `alpine`으로 둔다. 빌드 컨텍스트는 저장소 루트 |
| `Dockerfile.dockerignore` | 위 빌드의 컨텍스트 허용 목록(`pyproject.toml`, `uv.lock`, `README.md`, `src`, `plugins`만) |
| `Dockerfile.version`, `Dockerfile.version.dockerignore` | 판 번호를 넣는 방법을 견주는 타깃들(항목 1) |
| `Dockerfile.derived` | 시제품 위에 얹는 대조군. 플러그인 폴더를 root 소유로 바꾼 것, 작업 폴더에 npm 패키지를 깐 것, 플러그인 파일을 바꾼 다음 판 흉내. 빌드 컨텍스트는 이 폴더 |
| `inside.py` | 컨테이너 안에서 표준 라이브러리만으로 도는 도우미. `python - <명령> …`으로 표준 입력에 실어 넘기고 마지막 줄 `RESULT <json>`을 읽는다 |
| `run.py` | 측정 전체(항목 1~8). 항목마다 무엇을 표지로 보는지는 독스트링에 있다 |
| `pyrightconfig.json` | 두 파이썬 파일의 타입 검사 설정(strict, 플랫폼 Linux. `inside.py`가 리눅스 컨테이너 안에서 돌기 때문이다) |

## 다시 돌리기

저장소 루트에서 친다.

```sh
uv run python .scratch/release-image/probes/serve_image/run.py --items 1,2,3,4,5,6,7,8
```

- 필요한 것: 도는 Docker 데몬(리눅스 엔진, BuildKit), 위 "환경"의 바탕 이미지 넷과 uv 이미지(Dockerfile이 digest로 고정한다), Docker-in-Docker 이미지 `docker:29.9.2-dind`(항목 5·6, 로컬에 있어야 한다), 바탕 이미지를 짓는 동안의 네트워크(apt·apk, PyPI, npm, 항목 2의 deb-node는 python-build-standalone 내려받기). 항목 4의 "네트워크 있음" 갈래와 항목 5의 npx 갈래는 npm 레지스트리에 실제로 닿는다. LLM은 부르지 않는다(실행은 API 키가 없어 모델 호출에서 끝난다).
- 하는 일: 시제품 이미지(`ri-serve-proto`)와 그 위의 대조군(`ri-serve-proto-local`, `-rootowned`, `-v2`)을 캐시로 짓고, 항목마다 이미지를 짓거나 컨테이너를 띄운다. 컨테이너와 볼륨은 이름이 `ri-serve-<실행 토큰>-`으로 시작하고 끝에서 그 접두로 찾아 지운다. Docker-in-Docker는 `--privileged`로 띄우고 끝에서 익명 볼륨과 함께 지운다. 이미지는 남긴다. 호스트 포트는 쓰지 않는다. 모든 명령의 원본 출력은 `--work`(없으면 시스템 임시 폴더) 아래 `raw.log`에 남는다.
- `--items`로 항목을 고른다. `--builds`(항목 2의 후보마다 짓는 횟수, 기본 2. 0이면 짓지 않고 지어 둔 이미지만 본다), `--repeat`(항목 7의 갈래마다 회차, 기본 2), `--no-dind`(항목 5의 Docker-in-Docker를 뺀다). 측정이 아닌 회차가 하나라도 있으면 종료 코드가 1이다.
- 이 결과는 항목을 나눠 돌린 것이다. 실행마다 걸린 시간은 1이 5~14분, 2가 6분(`--builds 0`이면 2분), 3이 3분, 4가 3~4분, 5·6이 7~15분, 7이 5~8분, 8이 1분 남짓이었다(손으로 봤다. `raw.log`를 만든 시각과 마지막으로 쓴 시각이고, 다른 실행과 겹쳤다). 5·6은 Docker-in-Docker에 이미지를 싣는 데만 72~353초가 들었다. 항목 7의 리눅스 엔진 기본 기다림(11초 남짓)은 프로브에 없고 스크래치 스크립트로 손으로 봤다.
- 타입 검사: `uv run pyright -p .scratch/release-image/probes/serve_image`. 린트: `uv run ruff check .scratch/release-image/probes/serve_image`, `uv run ruff format --check .scratch/release-image/probes/serve_image`.

## 환경

| 무엇 | 값 | 어떻게 봤나 |
|---|---|---|
| 날짜 | 2026-11-13 | |
| 호스트 | Windows 10 Home 10.0.19045 | 세션 환경 정보 |
| Docker | Docker Desktop 4.97.0 (244584). 엔진·클라이언트 29.9.2, 엔진 linux/amd64, 커널 `6.18.58.1-microsoft-standard-WSL2`, CPU 16, 메모리 16.7GB, 저장 드라이버 overlay2 | 손으로 봤다(`docker version`, `docker info`) |
| 부하 | 같은 데몬을 다른 측정 세션들(이름 `ri-edge-*`, `ri-recover-dind`, `ri-web-*` 등)과 내 항목 실행 둘이 함께 썼다. 프로브가 찍은 Docker 리눅스 VM의 1분 부하는 1.39~8.39(CPU 16), 도는 컨테이너는 둘~아홉이었다. 항목마다의 값은 결과 절에 있다 | 프로브의 `/proc/loadavg`와 `docker ps -q`, 손으로 본 `docker ps` |
| Docker-in-Docker | `docker:29.9.2-dind`(로컬에 있던 이미지, ID `9a5d43f7d029`), `--privileged`, 안의 엔진 29.9.2, 저장 드라이버 overlayfs | 프로브의 `docker info` |
| uv | 이미지 안 0.13.8(`ghcr.io/astral-sh/uv@sha256:5cc1805e2426484abca4ad46ea783bab281fdb225fd82d8ce6d66a81254bac85`, 받을 때 태그 `latest`). 호스트는 0.10.8 | 빌드 로그, `uv --version` |
| python 바탕 | `python:3.12-slim-trixie` = `python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b`, Python 3.12.16 | 손으로 봤다(`docker image inspect`, 컨테이너 안 `python --version`) |
| node 바탕 | `node:24-trixie-slim` = `node@sha256:af02d57b57719b9657a45199a79264a9437940cd55b3c7b3fc99615654f124a0`, node v24.22.3, npm 11.19.1, Debian 13.7 | 같다 |
| alpine 바탕 | `python:3.12-alpine` = `python@sha256:c5ba3deef00c7758561a0f03c26f44f10589263d40e732b8748e0d1f38f6dd89`(Python 3.12.16, Alpine 3.24.4), `node:24-alpine` = `node@sha256:116b800c3754b440ee0aa3ed2f20f5bf3d99a554bfd9adeea09ea8017f6e85f5` | 같다 |
| 파이썬 패키지 | 잠금(`uv.lock`)대로 mcp 2.3.0, uvicorn 0.53.0, fastapi 0.141.1, pydantic 2.13.5. 빌드 백엔드 hatchling 1.33.0 | 잠금 파일, 이미지 안 wheel의 `WHEEL` 파일 |
| 예시 MCP 서버 | `@modelcontextprotocol/server-everything` 2.3.0(설치할 때 판을 고정했다. 서버가 `initialize`에 답한 이름과 판은 `mcp-servers/everything` 2.3.0) | 손으로 봤다(`inside.py handshake`) |

바탕 이미지 넷과 uv 이미지는 이 측정에서 처음 받았다(태그 `python:3.12-slim-trixie`, `node:24-trixie-slim`, `python:3.12-alpine`, `node:24-alpine`, `ghcr.io/astral-sh/uv:latest`). Dockerfile은 그것을 digest로 고정해 쓴다.

## 결과

### 1. 판 번호를 이미지에 넣는 법

CI가 태그 `v0.1.0-rc.1`에서 `0.1.0-rc.1`을 빌드 인자로 넘긴다고 보고 `Dockerfile.version`의 타깃을 지었다. 저장소 파일은 고치지 않고 빌드 단계 안의 사본만 고쳤다. 프로브가 다시 낸다(`run.py --items 1`, 2026-11-13 두 실행). 실행 토큰 `02f9ea`는 22회차가 측정, 1회차가 측정 아님이었다. 측정 아님은 `c-rc` 빌드였고 판정의 결함 때문이었다. 동적 판 갈래는 사본을 고치지 않는데 고친 줄을 표지로 요구했다. 판정을 고친 뒤의 실행 `b035e4`는 23회차 모두 측정이었고 값은 두 실행이 같았다. 갈래마다 마지막 단계만 캐시를 버려(`--no-cache-filter`) 짓는다. 성공을 기대한 갈래의 표지는 둘이다. uv 설치 줄 `+ agent-os==<판>`의 판이 넘긴 판의 정규화 꼴과 같아야 하고, 빌드 기록에 고친 줄이 찍혀야 한다. 동적 판 갈래는 고친 줄 대신 다시 잠그기 줄 `Updated agent-os v0.1.0 -> (dynamic)`을 본다. 실패를 기대한 갈래의 표지는 오류 문구다. 대조군은 아무것도 고치지 않은 `control`이다.

| 갈래(타깃) | 하는 일 | 잠금 검사 | `agent-os --version` | `/openapi.json`의 `info.version` |
|---|---|---|---|---|
| `control` | 고치지 않고 `uv sync --locked --no-dev --no-editable` | 지난다 | `0.1.0` | `0.1.0` |
| `a1-locked` | 사본 `pyproject.toml`의 `version`만 바꾸고 `uv sync --locked` | 실패. `error: The lockfile at uv.lock needs to be updated, but --locked was provided.` | 짓지 못함 | |
| `a2-frozen` | 같게 바꾸고 `uv sync --frozen` | 보지 않는다(`--frozen`) | `0.1.0-rc.1` | `0.1.0-rc.1` |
| `a3-lock-edited` | 사본 `uv.lock`의 agent-os `version` 줄도 함께 바꾸고 `uv sync --locked` | 지난다. 잠금에 `0.1.0-rc.1`로 적은 갈래와 `0.1.0rc1`로 적은 갈래가 모두 지났다 | `0.1.0-rc.1`(두 갈래 모두) | 보지 않았다 |
| `b1-frozen` | 의존성만 먼저 `uv sync --locked --no-install-project`, 그 뒤 판을 바꾸고 `uv sync --frozen` | 의존성 단계는 `--locked`로 지난다. 프로젝트 단계는 보지 않는다 | `0.1.0-rc.1`. 정식 판 흉내로 `0.2.0`을 넘기면 `0.2.0` | `0.1.0-rc.1`, `0.2.0` |
| `b2-pip` | 의존성은 `b1`과 같고 프로젝트만 `uv pip install --no-deps .` | `b1`과 같다 | `0.1.0-rc.1` | 보지 않았다 |
| `c-dynamic` | hatchling 동적 판(`dynamic = ["version"]`, `[tool.hatch.version] source = "env"`)으로 바꾸고 `AGENT_OS_VERSION=0.0.0`으로 다시 잠근 뒤 `AGENT_OS_VERSION`에 판을 주고 `uv sync --locked` | 지난다 | `0.1.0-rc.1` | `0.1.0-rc.1` |
| `c-dynamic-unset` | 위와 같고 `AGENT_OS_VERSION`을 주지 않음 | 빌드 실패. `RuntimeError: Error getting the version from source env: environment variable AGENT_OS_VERSION is not set` | 짓지 못함 | |

- 판이 보이는 모양(rc 이미지 모두, 두 실행 모두 같았다): `agent-os --version`, `importlib.metadata.version("agent-os")`, 설치된 `METADATA`의 `Version:` 줄, `/openapi.json`의 `info.version`이 모두 `0.1.0-rc.1`이었다. 태그에서 `v`만 뗀 글자다. 정규화된 꼴 `0.1.0rc1`은 설치 폴더 이름 `agent_os-0.1.0rc1.dist-info`와 uv의 설치 줄에만 보였다. wheel은 hatchling 1.33.0이 지었다(`WHEEL`의 `Generator:`). ADR 0056이 어림으로 적은 "이미지 안에서는 `0.1.0rc1` 꼴로 보일 것"은 `--version`과 API 문서의 판 칸에서 맞지 않았다.
- `c-dynamic`의 다시 잠그기(이미지 안 uv 0.13.8)는 잠금 파일에서 agent-os의 `version = "0.1.0"` 줄을 지우고 `revision`을 3에서 5로 바꿨다(빌드 기록에 찍은 diff). 저장소의 `pyproject.toml`과 `uv.lock`을 한 번 바꿔 커밋해야 쓰는 길이다. 잠금에 agent-os의 판이 없으므로, 잠글 때(0.0.0)와 다른 값을 `AGENT_OS_VERSION`에 줘도 `uv sync --locked`가 지났다. `revision`이 바뀐 까닭이 동적 판인지, 잠금을 다시 쓴 uv의 판(이미지 0.13.8, 호스트 0.10.8)인지는 가르지 않았다. 어림으로는 뒤의 것이다.
- `/openapi.json`을 읽으려 띄운 serve가 서기까지 7.8~25.2초였다(두 실행의 열 회차, 다른 항목의 실행과 겹쳤다). 판 실험 이미지는 바이트코드를 미리 만들지 않았고 root로 돈다.

### 2. 바탕 이미지와 크기

프로브가 다시 낸다(`run.py --items 2`, 2026-11-13 실행 토큰 `b2721c`, 15회차 모두 측정. 지은 이미지만 다시 본 `--builds 0` 실행 `6ed827`, 12회차 모두 측정). `Dockerfile`의 세 타깃을 `APP_VERSION=0.1.0-rc.1`, `--no-cache`로 두 번씩 지었다. 바탕 이미지는 미리 받아 둔 상태였으므로 받는 시간은 들지 않는다. 짓는 동안 apt·apk, PyPI, npm을 받고 `deb-node`는 CPython도 받는다. 크기는 엔진이 보고하는 풀린 크기다. 빌드의 표지는 빌드 기록의 `naming to docker.io/library/<태그>` 줄과 크기다. 짓기 직전의 부하(Docker 리눅스 VM의 1분 평균)와 도는 컨테이너 수를 같이 적었다. 지은 이미지마다 판과 도구, 실행 파일 이름으로 띄운 MCP 서버의 `initialize` 답(네트워크 없음), serve의 `/health`(네트워크 없음), 바탕의 sed를 봤다(두 실행에서 한 번씩).

| 후보(타깃) | 구성 | 크기 | 빌드 시간(두 번) | 짓기 직전 부하 | serve가 서기까지 | MCP 서버의 답 |
|---|---|---|---|---|---|---|
| `deb-py` | `python:3.12-slim-trixie` 위에 `node:24-trixie-slim`의 `node` 실행 파일과 전역 npm 패키지 폴더를 복사, tini는 apt | 382MB | 19~21초 | 3.99~4.17, 컨테이너 6 | 6.1~12.8초 | 0.44~1.06초 |
| `deb-node` | `node:24-trixie-slim` 위에 uv가 받은 CPython 3.12.16, tini는 apt | 476MB | 47~70초 | 5.29~5.79, 컨테이너 6 | 5.3~6.1초 | 0.56~0.80초 |
| `alpine` | `python:3.12-alpine` 위에 `node:24-alpine`의 `node`와 전역 npm 패키지 폴더, tini·libstdc++·libgcc는 apk | 311MB | 44~55초 | 8.14~8.39, 컨테이너 6 | 7.1~14.4초 | 0.53~1.12초 |

- 세 후보 모두 Python 3.12.16, node v24.22.3, npm 11.19.1이었고 MCP 서버는 `mcp-servers/everything` 2.3.0, 도구 16개로 답했다.
- `deb-node`의 시간에서 CPython 내려받기(33.1MiB)와 설치가 13~23초였다(빌드 기록의 `Installed Python 3.12.16 in`). 전역 npm 설치는 세 후보 모두 7~16초였다(`added 82 packages in`).
- **`alpine` 이미지의 판은 `0.1.0`이었다(두 실행 모두).** 같은 판 넣기 줄(`sed -i "0,/^version = .../s//.../"`)이 `alpine-build`에서는 줄을 바꾸지 않았다. 빌드 기록의 확인 줄이 `3:version = "0.1.0"`이었고 uv가 `agent-os==0.1.0`을 깔았는데도 빌드는 성공했다. Debian 두 후보는 같은 줄로 `0.1.0-rc.1`이 들어갔다. 까닭은 바탕의 sed다. 같은 `0,/정규식/` 주소를 쓴 한 줄을 각 이미지에서 돌리자 Debian 둘(`sed (GNU sed) 4.9`)은 줄을 바꿨고, `alpine`(`sed --version`이 `This is not GNU sed version 4.0`, busybox)은 오류 없이 그대로 두었다. 곧 판을 넣는 단계는 넣은 뒤 판을 대 보는 검사 없이는 조용히 옛 판으로 지어질 수 있다.
- 비교: 판 넣기 실험의 이미지(`ri-serve-ver-*`)는 node·tini·사용자 없이 파이썬 가상 환경만 든 것이고 241MB였다(손으로 봤다, `docker image ls`).
- 손으로 본 것(스크래치 `explore_base.sh`): node 이미지의 `node`는 glibc에 동적으로 링크되어 있어 Debian 계열끼리만 옮겼다. node 이미지에는 curl·wget·tini가 없고, `python:3.12-alpine`에는 busybox `wget`이 있다. 처음 지은 한 번씩은 41초(`deb-py`), 75초(`deb-node`), 36초(`alpine`)였다.

### 3. root가 아닌 사용자와 `getpass.getuser()`

- 부르는 자리(코드를 읽었다, `src/agent_os/main.py` 이 브랜치): `serve`는 시작할 때 한 번 `_serve`의 174행에서 부르고 그 값을 HTTP 채널의 주체(`Principal`)로 넘긴다. 요청마다 부르지 않는다. 예외를 잡지 않는다. `run`·`resume`은 `main`의 121행에서 부른다. `getpass.getuser()`는 `LOGNAME`·`USER`·`LNAME`·`USERNAME`을 먼저 읽고 없을 때만 passwd를 본다(같은 파일 291행 독스트링, Python 3.12).
- 프로브가 다시 낸다(`run.py --items 3`, 2026-11-13 실행 토큰 `30605e`, 6회차 모두 측정). 시제품 `ri-serve-proto`를 `--network none`으로 띄우고 트레이스는 `/tmp/traces`에 둔다(passwd 없는 uid가 `/data/traces`에 못 쓰는 것과 섞이지 않게). 표지는 섰으면 채널 실행 하나(`calc`)의 `run_started.principal`, 서지 못했으면 로그의 `getpwuid()` 줄이다. 항목 1의 실행과 다른 세션의 컨테이너가 함께 돌던 때다.

| 갈래 | 회차 | 결과 |
|---|---|---|
| 이미지의 사용자(uid 10001 `agentos`, passwd 항목 있음) | 2 | 섰다(14.8~24.2초). `principal`이 `agentos`, 도우미의 `getuser()`도 `agentos`, `HOME`은 `/home/agentos`이고 쓸 수 있었다 |
| `--user 12345:12345`(passwd 항목 없음) | 2 | 서지 못했다. 종료 코드 1이고 로그 끝이 `KeyError: 'getpwuid(): uid not found: 12345'`다. 트레이스백은 `main.py` 120행 `main` → 174행 `_serve` → `getpass.py` 169행 `getuser`였다(원본 기록) |
| `--user 12345:12345 -e USER=operator` | 2 | 섰다(8.6~12.2초). `principal`이 `operator`였다. `HOME`이 `/`이고 쓸 수 없었다 |

- "섰다"의 초는 `docker run -d`가 돌아온 뒤 첫 `/health` 200까지이고, 그 사이를 `docker exec`로 0.5초 남짓마다 엿본다. 부하에 따라 크게 흔들렸다(같은 갈래에서 14.8초와 24.2초).
- 읽기: passwd 항목이 없는 uid로 띄우면 serve는 구성 오류 문구가 아니라 트레이스백으로 시작에서 끝난다. `USER`를 함께 주면 그 값이 채널 실행의 주체가 된다. 그때 `HOME`이 `/`이므로 npx처럼 홈에 캐시를 쓰는 도구는 쓸 자리가 없을 것이다(어림, 재지 않았다).
- 손으로 본 것(스크래치 `explore_run.sh`·`explore_serve.sh`, 위와 같은 결과): 도우미만 띄운 `--user 12345:12345`에서 `-e USER=svc`를 주면 `getuser()`가 `svc`였다.

### 4. 예시 MCP 서버를 네트워크 없이 띄우기

지금 매니페스트(`plugins/mcp/everything/plugin.toml`)는 `command = "npx"`, `args = ["-y", "@modelcontextprotocol/server-everything"]`이다. 시제품(`deb-py`)은 그 패키지 2.3.0을 전역(`/usr/local/lib/node_modules`)에 깔고 `/usr/local/bin/mcp-server-everything`을 걸었다. 도우미 `inside.py handshake`가 serve와 같은 환경 변수 여섯(`HOME`·`LOGNAME`·`PATH`·`SHELL`·`TERM`·`USER`, mcp 2.3.0의 stdio 기본값을 코드에서 읽었다)만 넘겨 서버를 띄우고 `initialize`를 보낸다.

프로브가 다시 낸다(`run.py --items 4`, 2026-11-13 두 실행. 토큰 `6db79f`와 `3cee4e` 모두 17회차가 다 측정이었고, 아래 갈래마다 두 실행의 결과가 같았다. 시간만 다르면 범위로 적었다). 표지는 서버를 띄웠다는 것과, `registry.npmjs.org:443`에 TCP로 닿는지가 그 갈래의 네트워크 상태와 같다는 것이다(네트워크 없음 갈래는 닿지 않아야, 있음 갈래는 닿아야 한다). 답의 표지는 `initialize`의 `serverInfo`다. 시작할 때 Docker 리눅스 VM의 부하(1·5·15분)는 앞 실행이 7.60/8.22/7.50에 도는 컨테이너 아홉(항목 1의 둘째 실행이 함께 돌았다), 뒤 실행이 1.39/4.17/5.78에 컨테이너 둘이었다. 오래 걸리는 네 회차(첫 두 줄)는 함께 띄웠다.

| 갈래 | 회차(두 실행) | 결과 |
|---|---|---|
| `--network none`, 전역 설치, `npx -y 패키지@2.3.0`(깐 판과 같은 판) | 4 | 답하지 않았다. 71.5~73.1초에 `npm error request to https://registry.npmjs.org/@modelcontextprotocol%2fserver-everything failed, reason: getaddrinfo EAI_AGAIN registry.npmjs.org`로 스스로 끝났다 |
| `--network none`, 전역 설치, `npx -y 패키지`(판 없음) | 4 | 같다. 71.5~73.8초에 같은 오류로 끝났다 |
| `--network none`, 전역 설치, `npx --offline -y 패키지@2.3.0` | 2 | 0.62~1.53초에 `cache mode is 'only-if-cached' but no cached response is available`로 끝났다 |
| `--network none`, 전역 설치, 실행 파일 `mcp-server-everything` | 6 | 0.34~1.18초에 답했다. `mcp-servers/everything` 2.3.0, 도구 16개. 표준 입력을 닫자 0.02~0.07초 뒤 끝났다 |
| 네트워크 있음, 전역 설치, `npx -y 패키지@2.3.0`, `npm_config_loglevel=http` | 2 | 1.68~2.26초에 답했다. npm의 http 기록에 `200 /npm`과 `200 /@modelcontextprotocol%2fserver-everything (cache miss)`가 찍혔다 |
| 네트워크 있음, 전역 설치, `npx -y 패키지`, 같은 기록 | 2 | 1.09~1.79초에 답했다. 조회는 위와 같다 |
| `--network none`, 작업 폴더 `/app`의 `node_modules`에도 깐 이미지(`Dockerfile.derived`의 `local-npm`), `npx -y 패키지` | 4 | 0.74~1.52초에 답했다 |
| 같은 이미지, `npx -y 패키지@2.3.0` | 2 | 1.03~1.70초에 답했다 |
| 같은 이미지에서 작업 폴더만 `/tmp`, `npx -y 패키지` | 2 | 30초 창 안에 답하지 않았고 stderr도 없었다(창이 다 차 프로세스 그룹을 껐다) |
| 실제 serve(`--network none --read-only`, 플러그인과 트레이스는 이름 있는 볼륨, `--run-timeout 30`), 지금 매니페스트로 `calc` 실행 | 2 | 32.1초 뒤 `run_failed`, 원인 `timeout`, 문구 "실행이 30초 안에 끝나지 않았다" |
| 같은 serve에서 매니페스트를 `command = "mcp-server-everything"`, `args = []`로 바꾸고 `calc` 실행 | 4 | 0.64~1.16초 뒤 `run_failed`, 원인 `model_call`, 문구 `TypeError: Anthropic authentication failed: no API key or authorization credentials were provided. …`. serve 로그에 서버의 `Starting default (STDIO) server...`가 찍혔다 |

- 읽기: 전역에 깔아 둬도 `npx -y`는 판을 적든(깐 판과 같은 판) 적지 않든 레지스트리에 묻는다. 네트워크가 있으면 패키지 문서를 받고(`cache miss`), 없으면 71.5~73.8초 뒤 이름 풀이 실패로 끝난다. 부하가 낮은 뒤 실행에서도 71.5초 남짓이었으므로 이 시간의 대부분은 부하에서 오지 않는다. 그 시간이 이름 풀이의 재시도에서 오는지는 가르지 않았다(어림). 양성 대조는 네트워크 있음 갈래다. 같은 명령이 답해, 네트워크 없음 갈래의 실패가 명령 자체의 실패가 아님을 보인다.
- 실행 파일 이름으로 띄우면 네트워크 없이 1초 안팎에 답했다. 작업 폴더의 `node_modules`에 깔면 `npx -y`도 네트워크 없이 답했지만, 작업 폴더가 바뀌면 다시 레지스트리에 기댔다.
- serve의 두 갈래가 가르는 것: 실행 파일 이름 매니페스트는 MCP 연결을 지나 모델 호출에서 끝났고, 지금 매니페스트는 실행 제한에 걸렸다. 그래서 지금 매니페스트의 실패는 MCP 서버를 띄우는 자리에서 난 것이다. 실행 제한을 30초로 줄였으므로 npx가 스스로 끝나기(71.5~73.8초) 전에 제한이 먼저 걸렸다. 기본 실행 제한에서 어떤 원인으로 끝나는지는 재지 않았다.
- 네트워크 없음의 npx 갈래는 모두 stderr 끝에 실행 기록을 `/home/agentos/.npm/_logs/<시각>-debug-0.log`에 남겼다고 적었다(원본 기록). 곧 npx는 실패하는 길에서도 홈에 쓴다. 읽기 전용 루트에서의 영향은 항목 5가 본다.
- 손으로 본 것(스크래치 `explore_npx.sh`·`explore_npx_local.sh`): 깐 판과 다른 판(`@2.2.1`)도 60초 안에 답하지 않았다. 작업 폴더에 깐 이미지는 uid 12345·읽기 전용 루트에서도 답했고, 네트워크가 있을 때 npm의 판 확인만 있고 패키지 조회는 없었다.

### 5. 쓰는 자리와 소유권

코드를 읽었다(`src/agent_os/adapters/filesystem.py`의 `_swap_in`, `jsonl.py`): `disabled.toml`은 같은 폴더에 임시 파일을 만든 뒤 `os.replace`로 바꿔 끼운다. 그래서 파일이 아니라 플러그인 루트 폴더 자체에 쓰기 권한이 있어야 한다. 트레이스는 폴더를 `mkdir(parents=True, exist_ok=True)`한 뒤 덧붙여 쓴다.

프로브가 다시 낸다(`run.py --items 5,6`, 2026-11-13 두 실행. 토큰 `0c371a`와 `948786` 모두 항목 5·6을 합쳐 19회차가 다 측정이었고, 아래 갈래마다 두 실행의 결과가 같았다. 시간만 다르면 범위로 적었다). 실행은 채널로 `calc` 하나이고, MCP 연결을 지나면 API 키가 없어 모델 호출(`model_call`)에서 끝난다. 끄기·켜기는 관리 API `PUT /plugins/skill/cite-sources/enabled`다. 뒤 실행에서는 서버 로그의 `Errno 13` 줄도 모았다.

**(가) 이미지 밖에 쓰는 자리.** 호스트 엔진에서 볼륨 없이 띄우고 흐름 하나(매니페스트 바꾸기, 끄기·켜기, 실행) 뒤 `docker diff`를 모았다. 표지는 `A /app/plugins/disabled.toml` 줄과 실행의 실패 이벤트다.

| 갈래 | 결과 |
|---|---|
| 실행 파일 이름 매니페스트, 네트워크 없음 | 끄기·켜기 204, 실행 `model_call`. 쓴 자리는 `/app/plugins/disabled.toml`(새 파일), `/app/plugins/mcp/everything/plugin.toml`(프로브가 매니페스트를 바꾼 것), `/app/plugins/agents/calc/__pycache__/`(파일 둘, 에이전트 모듈의 바이트코드), `/data/traces/<실행>.jsonl`뿐이었다. `/tmp`와 홈에는 쓰지 않았다 |
| 지금 매니페스트(`npx -y`), 네트워크 있음 | 끄기·켜기 204, 실행 `model_call`. 위에 더해 `/home/agentos/.npm/`(`_cacache`, `_logs`, `_update-notifier-last-checked`)과 `/tmp/node-compile-cache/v24.22.3-x64-…-10001/`(뒤 실행에서 센 `docker diff` 항목 535개)에 썼다 |

**(나) 읽기 전용 루트.** `--read-only`에 `/app/plugins`와 `/data/traces`는 이름 있는 볼륨으로 붙였다.

| 갈래 | 결과 |
|---|---|
| 실행 파일 이름 매니페스트, 네트워크 없음 | 끄기·켜기 204, 실행 `model_call`. 서버 로그에 `EROFS`·`EACCES`·`npm error`가 없었다 |
| 지금 매니페스트(`npx -y`), 네트워크 있음 | 끄기·켜기 204. 실행은 1.3~3.3초 뒤 `tool_connection`, 문구 `ConnectionError: MCP 서버 everything(npx)에 붙지 못했다: MCPError: Connection closed`. 서버 로그에 `npm error code ENOENT` |
| 같고 `/home/agentos`에 tmpfs(`uid=10001,gid=10001,mode=0700`) | 실행이 `model_call`까지 갔다. `/tmp`는 그대로 읽기 전용이었으니 node의 컴파일 캐시는 쓰지 못해도 도는 것이다 |

**(다) 파이썬 바이트코드.** `agent-os --version` 한 번 뒤 `docker diff`의 `__pycache__` 줄을 셌다.

| 이미지와 사용자 | 새로 쓴 `__pycache__` 줄 |
|---|---|
| `ri-serve-ver-b1-rc`(바이트코드를 미리 만들지 않음, root) | 2565(가상 환경과 표준 라이브러리) |
| 시제품(`UV_COMPILE_BYTECODE=1`, uid 10001) | 0 |
| 시제품을 `--user 0:0`으로 | 213. 원본 기록의 `.pyc` 190개가 모두 `/usr/local/lib/python3.12/` 아래였고 가상 환경 아래는 없었다 |

- 읽기: 가상 환경은 미리 컴파일되어 다시 쓰지 않는다. 바탕 이미지의 표준 라이브러리에는 바이트코드가 없었다(root로 띄우자 그 자리에 새로 썼다). uid 10001에서는 그 폴더에 쓸 수 없어 쓰지 않고 오류 없이 돌았다(종료 코드 0, 판 출력). 그 값이 시작 시간에 얼마나 드는지는 재지 않았다.

**(라) 리눅스 엔진의 바인드 마운트.** Docker-in-Docker(`docker:29.9.2-dind`, `--privileged`, 안의 저장 드라이버 overlayfs, 엔진 29.9.2)에 시제품을 싣고(`docker save | docker load`, 71.8초와 352.8초. 뒤의 것은 다른 실행과 겹쳤다), 그 안의 폴더 둘을 플러그인 루트와 트레이스로 바인드 마운트했다. 폴더는 root 컨테이너가 이미지의 플러그인을 옮기고 예시 MCP 서버를 실행 파일 이름으로 바꾼 뒤 소유자와 권한을 줬다. serve는 `--network none --read-only --run-timeout 20`이다. 표지는 준비한 두 폴더의 `stat`이 갈래의 소유자·권한과 같은 것과, 섰으면 끄기 요청의 응답, 서지 못했으면 종료한 로그다.

| 폴더 소유자·권한, 실행 사용자 | 결과 |
|---|---|
| uid 1000 0755, 이미지 사용자(10001) | 섰다. 끄기가 500, `{"code":"internal_error","message":"운영자 파일을 쓸 수 없다: /app/plugins/disabled.toml\n[Errno 13] Permission denied: '/app/plugins/.disabled.toml.<임의>.tmp'"}`. 실행 요청도 500 `서버가 요청을 처리하지 못했다`이고 이벤트가 하나도 없었다. 서버 로그는 `요청 실패: … status=500 PermissionError: [Errno 13] Permission denied: '/data/traces/<실행>.jsonl'`이었다(뒤 실행). 쓰기 시험은 두 폴더 모두 `EACCES` |
| uid 10001 0755(대조군) | 끄기 204, 실행 `model_call`. 바깥에서 본 새 파일은 `10001:10001 600 disabled.toml`, `10001:10001 644 <실행>.jsonl` |
| uid 1000 0777 | 대조군과 같다. 새 파일의 소유자는 10001이다 |
| uid 1000 0755, `--user 1000:1000` | 서지 못했다. 종료 코드 1, `KeyError: 'getpwuid(): uid not found: 1000'`(항목 3과 같은 길) |
| uid 1000 0755, `--user 1000:1000 -e USER=operator` | 끄기 204, 실행 `model_call`. 새 파일은 `1000:1000 600`, `1000:1000 644` |

- 읽기: 바인드 마운트한 폴더는 컨테이너의 uid가 쓸 수 있어야 끄기와 실행이 된다. 길은 셋이 섰다. 폴더를 10001에게 주거나, 모두가 쓰게 열거나, 폴더 주인의 uid로 띄우면서 `USER`를 함께 주는 것이다. 쓸 수 없으면 서버는 뜨지만 끄기가 500으로 끝나고, 실행은 트레이스 파일을 열지 못해 이벤트 하나 없이 500으로 끝난다. 이때도 serve는 `/health` 200으로 섰으므로 항목 8의 상태 확인으로는 이 상태를 가르지 못한다.
- `disabled.toml`은 0600으로 생겼다. 그래서 주인이 아닌 호스트 사용자는 그 파일을 읽지 못할 것이다(어림).

### 6. 플러그인 폴더의 첫 채움

프로브가 다시 낸다(`run.py --items 5,6`의 Docker-in-Docker 몫, 실행 토큰 `0c371a`와 `948786`, 갈래마다 두 실행의 결과가 같았다). 리눅스 엔진(위 항목 5 (라)와 같은 Docker-in-Docker)에서 serve를 `--network none --read-only`로 띄웠다. 대조군은 둘이다. 플러그인 폴더를 root 소유로 바꾼 이미지(`Dockerfile.derived`의 `rootowned`)는 볼륨이 이미지의 소유자를 옮기는지를 가르고, 빈 볼륨에 다음 판 이미지를 붙인 갈래는 다음 판의 내용이 볼륨에 실릴 수 있다는 양성 대조다. 다음 판은 `plugins-v2`(`mcp/everything`의 판을 0.2.0으로 바꾸고 새 파일 `NEW_IN_V2.txt`를 더한 것)다.

| 갈래 | 결과 |
|---|---|
| 빈 이름 있는 볼륨, 시제품 | 이미지의 내용 26항목이 복사됐다. 소유자는 모두 uid 10001, 폴더 자체도 uid 10001·0755. 끄기 204, `disabled.toml`이 생겼다 |
| 빈 이름 있는 볼륨, root 소유로 바꾼 이미지(대조군) | 26항목이 복사됐고 소유자는 모두 0, 폴더도 0·0755였다. 끄기가 500 `운영자 파일을 쓸 수 없다 … Permission denied`, `disabled.toml`은 생기지 않았다 |
| 빈 바인드 마운트, Docker가 만든 폴더(root 소유) | 컨테이너 안에서 0항목이었다. serve는 종료 코드 1로 끝났고 로그는 `기본 모델 플러그인이 없다: claude-opus-5` / `/app/plugins/models/claude-opus-5/plugin.toml 을 두거나 --model·AGENT_OS_MODEL 의 이름을 고친다.`였다 |
| 빈 바인드 마운트, 미리 만든 폴더(10001 소유) | 위와 같다(0항목, 같은 종료와 로그) |
| 앞 판(시제품)이 채운 볼륨에 다음 판 이미지 | 매니페스트가 `version = "0.1.0"` 그대로였고 `NEW_IN_V2.txt`가 없었다 |
| 빈 볼륨에 다음 판 이미지(양성 대조) | `version = "0.2.0"`, `NEW_IN_V2.txt`가 있었다 |

- 읽기: 이름 있는 볼륨은 비어 있을 때 처음 한 번만 이미지의 내용을 소유자째 복사한다. 그래서 이미지 안 플러그인 폴더의 소유자가 볼륨에서 끄기가 되는지를 정한다. 판을 올려도 이미 채워진 볼륨의 플러그인은 바뀌지 않는다. 바인드 마운트는 복사하지 않고, 빈 폴더면 serve가 기본 모델 플러그인이 없다는 구성 오류로 시작에서 끝난다.
- 손으로 본 것(스크래치 `explore_serve.sh`, Docker Desktop): 빈 이름 있는 볼륨의 첫 채움이 위 첫 줄과 같았다.

### 7. init과 종료

프로브가 다시 낸다(`run.py --items 7`, 2026-11-13 두 실행. 토큰 `e9f746`은 8회차, `c41665`는 11회차이고 모두 측정. 시작할 때 부하는 6.48/6.56/6.94와 5.12/5.55/6.43, 도는 컨테이너는 다섯과 여섯이었다. 앞 실행에는 항목 8의 실행이, 뒤 실행에는 항목 5·6의 Docker-in-Docker 실행이 함께 돌았다). 이미지는 작업 폴더에도 예시 MCP 패키지를 깐 `local-npm`이고 `--network none`이다. 그래서 지금 매니페스트(`npx -y`)로도 MCP 서버가 뜬다(항목 4). 회차마다 실행 넷(지금 매니페스트 둘, 실행 파일 이름으로 바꾼 뒤 둘. 넷 모두 MCP를 지나 `model_call`에서 끝났다) 뒤 좀비를 세고, 도우미가 손자 프로세스를 고아로 만들어 그 끝을 본 뒤 `docker stop`을 건다. 표지는 pid 1의 명령줄이다. 셸 감싸기는 셸이 신호를 넘기지 않는 대조군이다.

| 갈래(두 실행, 회차 넷씩) | pid 1 | MCP 실행 넷 뒤 좀비 | 고아가 끝난 뒤 | `docker stop` | 종료 코드 | uvicorn 정상 종료 줄 |
|---|---|---|---|---|---|---|
| tini(이미지의 ENTRYPOINT) | `/usr/bin/tini -- agent-os serve …` | 0 | 거둬졌다(부모 1) | 0.73~3.53초 | 143 | 있음 |
| `docker run --init`(`--entrypoint agent-os`) | `/sbin/docker-init -- agent-os serve …` | 0 | 거둬졌다(부모 1) | 0.59~2.88초 | 143 | 있음 |
| init 없음(`--entrypoint agent-os`) | `/app/.venv/bin/python /app/.venv/bin/agent-os serve …` | 0 | 좀비(`Z`)로 남았다(부모 1) | 1.50~3.24초 | 0 | 있음 |
| 셸 감싸기(대조군, `sh -c "agent-os serve …; echo serve-exited"`) | `sh -c agent-os serve …` | 0 | 거둬졌다(부모 1) | 3.81~5.41초 | 137 | 없음 |
| SIGTERM 처리기 없는 pid 1(`--entrypoint sleep`), `-t` 없이(둘째 실행, 회차 둘) | | | | 4.22~4.70초 | 137 | |
| 같고 `docker stop -t 10`(둘째 실행, 회차 하나) | | | | 11.92초 | 137 | |

- 읽기: MCP 서버를 띄우고 닫는 길은 네 갈래 모두에서 좀비를 남기지 않았다. 갈래를 가른 것은 pid 1이 남의 고아를 거두는지다. init 없이 agent-os가 pid 1이면 다른 프로세스가 남긴 고아가 좀비로 남는다. 이 실행에서 그런 고아를 만든 것은 도우미뿐이고, MCP 서버 쪽이 고아를 남기는 경우는 보지 않았다.
- init 없음에서 종료 코드가 0이고 tini와 docker-init 아래에서는 143(SIGTERM)이었다. uvicorn은 정상 종료 뒤 처리기를 되돌리고 받은 신호를 스스로 다시 일으킨다(코드를 읽었다, uvicorn 0.53.0 `server.py`의 `capture_signals`). pid 1에게는 기본 처리의 신호가 닿지 않아 그 신호가 무시되고 0으로 끝났다는 것이 까닭일 것이다(어림, 가르는 갈래를 두지 않았다).
- 셸 감싸기는 SIGTERM을 serve에 넘기지 못해 엔진이 SIGKILL로 끝냈다(137, 정상 종료 줄 없음). 걸린 시간이 10초가 아니라 4~5초인 것은 이 PC의 Docker Desktop이 `-t` 없는 `docker stop`에서 4초 남짓만 기다리기 때문이다(표의 마지막 두 줄. `-t 10`을 주면 10초를 기다렸다). 까닭은 가르지 않았다.
- 손으로 본 것(스크래치 `stop_wait_dind.sh`): 리눅스 엔진(Docker-in-Docker 29.9.2)에서 같은 처리기 없는 pid 1에 `-t` 없이 `docker stop`을 걸자 11.17초와 11.63초 뒤 137이었고 `-t 10`은 10.87초였다. 곧 리눅스 엔진의 기본 기다림은 10초이고 4초 남짓은 이 PC의 Docker Desktop에서만 봤다. 같은 PC에서 프로브 전에 손으로 친 `time docker stop`도 4.4초(`-t` 없음)와 11.3초(`-t 10`)였다.

### 8. 상태 확인 명령

serve는 `127.0.0.1`과 `::1`에만 묶이므로(코드를 읽었다, `src/agent_os/main.py`의 루프백 목록) 검사 명령은 컨테이너 안에서 돈다. 시제품에는 curl과 wget이 없다(손으로 봤다, 항목 2). 프로브가 다시 낸다(`run.py --items 8`, 2026-11-13 실행 토큰 `ed994d`, 8회차 모두 측정). 시작할 때 부하는 5.74/6.44/6.91, 도는 컨테이너 넷이었고 항목 7의 실행이 함께 돌았다. 대조군은 아무것도 듣지 않는 포트 8001이다.

| 명령(컨테이너 안, uid 10001) | 포트 8000(serve) | 포트 8001(대조군) |
|---|---|---|
| `python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"` | 세 번 모두 종료 코드 0, 576~641ms | 세 번 모두 1, 642~768ms |
| `node -e "fetch('http://127.0.0.1:8000/health').then(r => process.exit(r.ok ? 0 : 1), () => process.exit(1))"` | 세 번 모두 0, 184~194ms | 세 번 모두 1, 134~191ms |

- 같은 명령을 바깥에서 `docker exec`로 치면 종료 코드는 같고 0.31~1.27초 걸렸다.
- `--health-cmd`(셸 꼴, 위 python 한 줄, `--health-interval 2s --health-timeout 5s`)를 단 컨테이너:

| 갈래 | 회차 | 결과 |
|---|---|---|
| 포트 8000, `--health-retries 3 --health-start-period 30s` | 2 | 띄운 뒤 12.2~12.5초에 `healthy`. 기록된 검사 둘, 마지막 종료 코드 0 |
| 포트 8001(대조군), `--health-retries 2 --health-start-period 0s` | 2 | 띄운 뒤 5.8~5.9초에 `unhealthy`. 기록된 검사 둘, 마지막 종료 코드 1, 출력 끝 `urllib.error.URLError: <urlopen error [Errno 111] Connection refused>` |

- 읽기: python 한 줄은 바탕에 더 깔 것 없이 정상과 비정상을 갈랐고 한 번에 0.6초 남짓이었다. node 한 줄은 0.2초 남짓이었다. `healthy`까지의 12초 남짓에는 serve가 서는 시간이 든다.

## 재지 못한 것

- 실제 리눅스 호스트의 바인드 마운트. 호스트 사용자의 uid와 이미지의 uid 10001이 다른 장면, rootless Docker·Podman의 uid 옮김, SELinux 라벨(`:z`)은 보지 않았다. 이 PC에는 리눅스 호스트가 없어 Docker-in-Docker로 리눅스 엔진만 흉내 냈다(항목 5 (라), 6).
- 레지스트리에 올린 이미지의 압축 크기와 받는 시간. 이 측정은 바깥에 올리지 않았다. 위 크기는 엔진이 보고하는 풀린 크기다.
- arm64 이미지. 엔진이 linux/amd64 하나라 짓지 않았다.
- `docker compose`의 `stop_grace_period`, `healthcheck`, `depends_on`의 `service_healthy`. 같은 뜻의 `docker run` 옵션만 봤다.
- 기본 실행 제한에서 지금 매니페스트(`npx -y`)가 네트워크 없이 어떤 원인으로 끝나는지. 실행 제한을 30초로 줄여 봤다(항목 4).
- 표준 라이브러리에 바이트코드가 없는 것이 uid 10001의 시작 시간에 드는 값(항목 5 (다)).
- 이 PC의 Docker Desktop에서 `-t` 없는 `docker stop`이 4초 남짓만 기다리는 까닭(항목 7). 사용자 폴더의 `.docker/daemon.json`에는 빌더 정리와 `experimental` 칸만 있었다(손으로 봤다).
- MCP 서버 쪽이 고아를 남기는 경우. 예시 서버는 남기지 않았고, 항목 7의 고아는 도우미가 만들었다.
- 까닭을 어림으로만 적은 셋. init 없음의 종료 코드 0, npx가 실패하기까지의 약 72초, 다시 잠그기의 `revision` 3→5.
- `--user`에 `USER`를 함께 준 컨테이너(`HOME`이 `/`)에서 npx가 도는지(항목 3, 어림).
- 실제 모델 호출. 측정의 제약으로 부르지 않았고, 실행은 모두 API 키가 없어 모델 호출에서 끝났다.
- 이미지의 취약점 검사와 SBOM.

## 남긴 이미지

이미지는 다시 돌릴 때 캐시로 쓰도록 남겼다. 끝에 `docker image ls --filter reference=ri-serve-*`로 본 열아홉 태그다.

- 시제품과 그 위의 대조군: `ri-serve-proto`(`ri-serve-base-deb-py`와 이미지 ID가 같다), `ri-serve-proto-local`, `ri-serve-proto-rootowned`, `ri-serve-proto-v2`
- 바탕 후보(항목 2): `ri-serve-base-deb-py`, `ri-serve-base-deb-node`, `ri-serve-base-alpine`
- 판 번호(항목 1): `ri-serve-ver-control`, `ri-serve-ver-a2-rc`, `ri-serve-ver-a3-rc-raw`, `ri-serve-ver-a3-rc-norm`, `ri-serve-ver-b1-rc`, `ri-serve-ver-b1-final`, `ri-serve-ver-b2-rc`, `ri-serve-ver-c-rc`
- 손으로 본 탐색: `ri-serve-explore-deb-py`, `ri-serve-explore-deb-node`, `ri-serve-explore-alpine`, `ri-serve-explore-local`

컨테이너와 볼륨은 프로브와 탐색 스크립트가 끝에서 지웠고, 남은 것이 없는지 `name=ri-serve-`로 걸러 손으로 봤다. Docker-in-Docker는 익명 볼륨과 함께 지웠다. 바탕 이미지 넷과 uv 이미지는 받은 채로 두었고, `docker:29.9.2-dind`는 측정 전부터 있던 것이다.
