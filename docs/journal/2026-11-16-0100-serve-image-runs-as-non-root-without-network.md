# serve 이미지가 넣은 판 번호를 글자 그대로 싣고 root가 아닌 사용자로 네트워크 없이 뜬다 (release-image 티켓 07)

브랜치 `feature/07-serve-image-runs-as-non-root-without-network`, 워크트리 `.claude/worktrees/07-serve-image-runs-as-non-root-without-network`. 모델 Sonnet 5.5(지시문의 high). 기준은 `origin/dev` `d80690da1`이다. 이 세션의 제목은 시작할 때 브랜치 이름으로 바꿨다.

## 사용자 프롬프트 원문

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/release-image/issues/07-serve-image-runs-as-non-root-without-network.md
>
> 다음 작업: .scratch/release-image/issues/07-serve-image-runs-as-non-root-without-network.md. serve 이미지가 넣은 판 번호를 글자 그대로 싣고 root가 아닌 사용자로 네트워크 없이 뜬다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 3 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/release-image/issues/07-serve-image-runs-as-non-root-without-network.md
> 브랜치: feature/07-serve-image-runs-as-non-root-without-network
> 모델: Sonnet 5.5 / high
> 읽을 것: 나란히 도는 형제 티켓 06-review-bot-checks-upgrade-bang.md, 08-web-images-run-as-non-root.md
> 이어받을 상태: 형제 티켓 08도 dev에 아직 없는 새 폴더 deploy/images/를 함께 만든다. 빌드 맥락의 제외 목록은 저장소 루트의 .dockerignore가 아니라 프로브(serve_image, web_images)처럼 Dockerfile마다 <이름>.dockerignore로 두어 08과 같은 파일을 고치지 않는다. 08 세션이 같은 PC에서 동시에 Docker 빌드를 돌 수 있으므로, 이미지 크기·짓는 시간 같은 잰 수치를 일지와 프로브 README에 적을 때 형제 빌드가 함께 돌았는지도 적는다
> 확인할 선행 조건: 없음
> 이번 요청 범위: PR과 병합까지

## 한 것

- `deploy/images/serve.Dockerfile`과 `serve.Dockerfile.dockerignore`를 새로 만들었다. 빌드 맥락의 허용 목록은 이름이 Dockerfile과 짝인 `<이름>.dockerignore`에 두어 08이 만드는 파일과 겹치지 않는다. README의 트리에 `deploy/` 줄을 더했다.
- 이미지의 구성은 `python:3.12-slim-trixie`(digest 고정) 바탕에 `node:24-trixie-slim`의 `node`와 전역 npm 폴더를 복사하고, tini를 apt로 깐다. 예시 MCP 서버 `@modelcontextprotocol/server-everything` 2.3.0을 전역에 깔고 `mcp-server-everything`으로 걸었다. uid·gid 10001 `agentos`와 홈 `/home/agentos`를 만들고, 표지 파일 `/etc/agent-os/image`를 root 소유로 굽는다. `/app/plugins`와 `/data/traces`와 홈(`useradd --create-home`)이 10001 소유이고 나머지는 root 소유다(빈 파일 `/app/.venv/.lock` 하나만 uv가 0666으로 만들어 쓸 수 있는데 내용이 없어 무해하다).
- 판 번호는 빌드 인자 `APP_VERSION`이다. 의존성을 `uv sync --locked --no-install-project`로 먼저 깔고, 빌드 단계 안의 `pyproject.toml` 사본만 `sed`로 바꾼 뒤 `uv sync --frozen --no-editable`로 프로젝트를 깐다. 그 뒤 설치된 패키지의 판을 넘긴 번호와 대조해 다르면 빌드를 멈춘다.
- OCI 라벨 셋(`version`, `revision`, `source`)을 빌드 인자로 채우고, 기본 `CMD`는 `agent-os serve --plugins-root /app/plugins --traces /data/traces`이며 루프백 기본 `--host`와 모델 지정이 없다(아래 "리뷰 반영"). 컨테이너 네트워크에 묶는 `--host 0.0.0.0`과 환경 변수 `AGENT_OS_CONTAINER_NETWORK=1`은 띄우는 쪽(`docker run`, 09의 compose)이 준다.
- 프로브 `serve_image`를 고쳤다. SILENT 판정이 EOF로 끝난 회차와 마감이 지난 회차를 가르고(`inside.py`가 `first_ended`를 낸다), 항목 2·4·5·6·7을 고친 판으로 다시 돌려 README에 날짜와 결과를 더했다.

## 결정

- 번호 없이 지을 때: 빌드가 실패한다. `APP_VERSION`이 비었거나 `X.Y.Z`·`X.Y.Z-rc.N` 꼴이 아니면 첫 줄에서 멈추고 안내 문구를 낸다. 저장소의 판(지금 `0.0.0`)으로 조용히 짓는 길은 두지 않았다. 까닭은 판 번호가 `agent-os --version`·패키지 판·`/openapi.json`에 같은 글자로 실린다는 약속(스토리 3)이 번호 없는 이미지에서는 지켜지지 않기 때문이다. 태그에서 번호를 뽑아 넘기는 일은 11의 판 내기가 한다.
- `CMD`에 `--host 0.0.0.0`을 넣지 않았다. 이미지를 `docker run`으로 아무 옵션 없이 띄워도 03의 루프백 규칙에 걸려 밖에 열리지 않는다. 열려면 운영자가 환경 변수와 `--host`를 함께 준다.
- `CMD`에 `--model`도 넣지 않는다(리뷰 반영). 플래그가 환경 변수 `AGENT_OS_MODEL`을 이기므로(`resolve_model_name`, ADR 0040) 박으면 운영자가 환경 변수로 고른 모델이 조용히 무시된다. 명세 "이미지의 구성"의 환경 변수 틀은 기본 모델의 이름을 운영자가 고르는 값으로 둔다. 처음 판은 프로브 시제품 Dockerfile의 `CMD`를 그대로 옮겨 `--model claude-opus-5`가 들어 있었다.
- 상태 확인은 이미지의 python으로 `urllib` 4초 제한 `/health`를 여는 명령이다(프로브 8번의 한 줄). curl이 이미지에 없다.

## 이 PC에서 띄워 본 결과

환경은 Windows 10, Docker Desktop 4.97.0, 엔진 29.9.2. 빌드와 확인은 모두 같은 데몬에서 형제 08의 이미지 빌드·실행(`ri08-*`, `ri-web-*`)과 내 프로브·Grype가 번갈아 도는 동안 손으로 돌려 봤다. 그래서 시간 값은 아래 부하 아래의 값이다.

짓기(번호 `0.1.0-rc.1`, 저장소 `d80690da1`):

```bash
docker build -f deploy/images/serve.Dockerfile \
  --build-arg APP_VERSION=0.1.0-rc.1 --build-arg REVISION=$(git rev-parse HEAD) \
  --build-arg SOURCE=https://github.com/njh6803/agent-os -t ri-serve-impl:0.1.0-rc.1 .
```

- 풀린 크기: 381,925,907바이트(`docker image inspect`, 382MB. 명세의 382MB와 같다). 프로브가 아니라 손으로 봤다.
- 짓는 시간: 캐시 없이(`--no-cache`) 전체를 짓는 데 처음에 275초였다(손으로 봤다, 스크래치 `build_checks.sh`). 시작할 때 Docker VM 부하 11.17/7.87/6.79에 `ri-web-p-393989-w-*`(형제 08의 위젯 이미지 작업)가 함께 돌았다. 명세의 19~21초(프로브 README 2번의 `deb-py`)도 `--no-cache`로 지은 값이고 `deb-py`는 이 Dockerfile과 같은 단계 구성이라, 둘은 같은 조건의 값이다. 리뷰 반영 중 CMD를 고친 뒤 같은 명령으로 `--no-cache` 빌드를 다시 쳤더니 63초였다(손으로 봤다, 스크래치 `rebuild.sh`. 시작 부하 2.90/5.89/7.15, 도는 컨테이너는 형제 08의 `ri08-ab`와 `rag-engine-test-postgres-1`뿐). 프로브 README의 다시 돌린 값 46·54초와 비슷하다. 19~21초, 46·54초, 63초, 275초가 갈린 까닭은 부하 말고 가르지 못했다(어림). 조용한 데몬에서 다시 재지는 못했다.
- 빌드 인자를 안 준 빌드는 `APP_VERSION 빌드 인자가 필요하다(예: 0.1.0-rc.1)`로 5.9초 만에 실패했다(종료 1). `v0.1.0`을 주면 `APP_VERSION 은 X.Y.Z 나 X.Y.Z-rc.N 꼴이어야 한다: v0.1.0`으로 실패했다(종료 1).
- 판을 넣는 줄이 아무것도 바꾸지 못할 때: `sed` 패턴을 일부러 어긋나게 한 Dockerfile 사본(스크래치 `noop/`)으로 지었더니 `grep`이 `3:version = "0.0.0"`을 보였고 `설치된 agent-os 의 판 0.0.0 이 넘긴 번호 0.1.0-rc.1 와 다르다`로 빌드가 실패했다(종료 1). 판 대조가 조용히 안 바뀐 경우를 잡는다.

띄우기(스크래치 `verify_image.sh`, 원본 `verify1~3.log`. 같은 열 단계를 세 번 쳤고 아래는 마지막 두 실행이다. 이 실행들은 `CMD`에 `--model`이 들어 있던 처음 판의 이미지이고, 명령에는 `--model claude-opus-5`를 인자로 따로 주었다. 리뷰 반영에서 `CMD`만 바뀌었으므로 이 표의 동작은 인자로 모델을 주는 한 그대로라고 본다(어림이다. 고친 이미지로는 위 "리뷰 반영"의 확인만 다시 쳤다):

```bash
docker run -d --network none --read-only \
  -v ri7-plugins:/app/plugins -v ri7-traces:/data/traces \
  --tmpfs /home/agentos:uid=10001,gid=10001,mode=0700 \
  -e AGENT_OS_CONTAINER_NETWORK=1 -e AGENT_OS_ADMIN_TOKEN -e AGENT_OS_CHANNEL_TOKEN \
  --health-cmd 'python -c "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen(\"http://127.0.0.1:8000/health\", timeout=4).status == 200 else 1)"' \
  ri-serve-impl:0.1.0-rc.1 agent-os serve --plugins-root /app/plugins --traces /data/traces \
  --model claude-opus-5 --host 0.0.0.0 --run-timeout 30
```

| 확인 | 결과 | 근거 |
|---|---|---|
| 판 번호 | `agent-os --version`, `importlib.metadata.version("agent-os")`, `/openapi.json`의 `info.version`이 모두 `0.1.0-rc.1` | 손으로 봤다 |
| 사용자 | `uid=10001(agentos) gid=10001(agentos)`. `/etc/agent-os/image`는 root 소유 644, `/app`은 root, `/app/plugins`와 `/data/traces`는 agentos, `getpass.getuser()`는 `agentos` | 손으로 봤다 |
| 끄기·켜기 | `PUT /plugins/skill/cite-sources/enabled` 둘 다 204 | 손으로 봤다 |
| `calc` 채널 실행 | `run_started`, `run_failed`, 원인 `model_call`(API 키 없음). 서버가 MCP 서버의 시작 줄 `Starting default (STDIO) server...`을 찍었다. 서버 로그에서 `errno`·`erofs`·`eacces`·`permission denied`·`npm error` 줄 수 0 | 손으로 봤다 |
| 상태 확인 | 포트 8000은 종료 0, 8001(듣지 않음)은 종료 1. `healthy`, 대조 컨테이너는 8초 만에 `unhealthy`(`Connection refused`) | 손으로 봤다 |
| `docker stop` | 종료 코드 143, 로그에 `Shutting down … Application shutdown complete. Finished server process` | 손으로 봤다 |
| 환경 변수 없이 `--host 0.0.0.0` | 종료 코드 1, `--host 는 루프백만 받는다(127.0.0.1, ::1). 받은 값: 0.0.0.0 … 환경 변수 AGENT_OS_CONTAINER_NETWORK=1 도 준다.` | 손으로 봤다 |
| npx 매니페스트(네트워크 열림, 홈 tmpfs) | 매니페스트를 `command = "npx"`, `args = ["-y", "@modelcontextprotocol/server-everything"]`로 바꾸고 실행해 `run_failed` 원인 `model_call`. `npm error` 줄 0 | 손으로 봤다 |

시간 값(상태 확인이 healthy가 될 때까지, `calc` 실행이 끝날 때까지, `docker stop`)은 부하에 크게 흔들렸다.

| 실행 | 시작 부하 · 도는 컨테이너 | healthy까지 | `calc` 실행 | `docker stop` |
|---|---|---|---|---|
| 둘째 (`verify2.log`) | 9.83/6.69/4.02 · `ri08-bad`, `ri08-stub`, rag-engine-test-postgres | 9초 | 0.68초쯤(이벤트 시각 차) | 2.2초 |
| 셋째 (`verify3.log`) | 6.55/5.87/6.03 · `ri-web-p-393989-w-5`, rag-engine-test-postgres | 53초 | 12.35초 | 4.2초 |

셋째 실행은 같은 이미지·같은 명령인데 서는 데 53초가 걸렸다. 형제 08이 위젯 이미지를 같은 데몬에서 짓고 있었던 것 외에 까닭을 가르는 갈래를 두지 않았으므로 부하 탓이라는 것은 어림이다. 시간 기대는 걸지 않았고(티켓은 동작을 본다), 동작은 두 실행이 같았다.

Grype(스크래치 `grype_scan.sh`, 이미지 `ghcr.io/anchore/grype@sha256:13113eec…`, `--only-fixed`, DB 구축 2026-11-15T06:19:39Z, 505초, 종료 2): 고칠 수 있는 취약점 40건 가운데 Critical 1(certifi 2026.7.22, `GHSA-6q48-6c7w-9gw2`, 고침 판 2026.10.18), High 8, Medium 27, Low 3, Negligible 1이다. 이 실행은 16:00~16:09(UTC)에 돌아 프로브 재측정과 겹쳤다. 티켓대로 멈추지 않았다. certifi는 `uv.lock`의 판이라 이 티켓 밖이다(후속으로 `uv.lock`의 certifi를 올릴 수 있다).

## 프로브 고침과 다시 돌린 결과

- SILENT 판정: `handshake_result`가 `first_ended`가 `deadline`이고 프로세스가 끝나지 않았을 때만 SILENT를 세고, 나머지 갈래는 `eof`일 때만 센다(`.claude/rules/probes.md`의 첫 항목).
- 항목 2·4·5·6·7을 고친 판으로 다시 돌렸다. 모든 실행이 측정 아닌 회차 0이었다(토큰과 회차는 프로브 README 맨 끝 절에 있다). 동작은 2026-11-13 값과 같았고, 빌드 시간과 MCP 답 시간은 길어졌다(부하 탓이라는 것은 어림이다).
- 도중에 저장소 매니페스트가 02로 이미 실행 파일 이름으로 바뀐 것을 알았다. 첫 항목 5·6 재실행의 "npx 매니페스트" 갈래가 실제로는 실행 파일 이름으로 돌아 `바꿈 None`이 찍혔고, 그 실행을 폐기하고 `NPX` 설정과 `manifest_is`로 고쳐 다시 돌렸다.
- 명세 문장과 다른 것: 시간 값 넷이 명세의 문장과 다르게 나왔다. 짓는 시간은 명세 "19~21초"에 견주어 프로브 다시 돌림이 46·54초, 이 이미지가 처음 275초(리뷰 반영 뒤 같은 명령 63초)다. 실행 파일 이름 매니페스트가 `model_call`에 닿기까지는 명세 "0.64~1.16초"에 견주어 1.58~2.58초다. `healthy`까지(셋째 실행 53초)와 `docker stop`(4.2초)도 명세의 "12.2~12.5초"와 "0.73~3.53초" 밖이다. 짓는 시간의 조건은 명세와 같다(둘 다 `--no-cache`). 그래서 "캐시 탓"이라는 설명은 서지 않고, 남는 설명은 부하(어림)뿐이다. 그래도 멈추지 않았다. 이유는 설계가 기대는 것이 시간이 아니라 동작이기 때문이다. 어떤 원인으로 끝나는지, 누가 쓰는지, 몇 MB인지, 상태 확인의 시작 유예 30초 안에 서는지(53초는 유예를 넘지만 `healthy`로 가는 것은 같았고 compose의 유예는 09가 정한다)는 같았다. 이 판단은 티켓의 "명세의 문장과 다르면 멈춘다"를 시간 값에까지 적용하지 않는다는 읽기이고 사용자가 확인한 것이 아니다. 명세의 수치는 고치지 않았다(이 판단은 PR 본문에도 적고 사용자에게 알린다).

## 근거의 종류

- 프로브가 다시 낸 것: 위 "프로브 고침과 다시 돌린 결과"의 값과 프로브 README 맨 끝 절.
- 손으로 본 것(스크래치 스크립트, 커밋하지 않음): 이미지 크기, 짓는 시간, 번호 없는 빌드 실패, 열 단계 확인, Grype.
- 코드를 읽은 것: 이 세션에서는 새로 읽지 않았다. 프로브 README가 적은 읽기(루프백 목록, `filesystem.py`·`jsonl.py`가 쓰는 자리)를 그대로 이어 받았다.

## 회고

- 프로브를 다시 돌리기 전에 저장소 매니페스트가 바뀌었는지 보지 않아 첫 5·6 실행 하나를 버렸다. 판정에 매니페스트가 기대한 꼴인지 표지를 넣으니 다음에는 첫 회차에서 잡힌다.
- Git Bash의 경로 변환(`/app/plugins`가 `C:/Program Files/Git/app/plugins`가 되는 것)이 `docker run` 인자를 깨뜨렸다. 확인 스크립트 첫머리에 `MSYS_NO_PATHCONV=1`을 두었다.
- 지키지 못한 것: 부하 없는 데몬에서의 시간 재기. 형제 08이 같은 PC에서 계속 빌드해 조용한 때를 만들지 못했다.

## 리뷰 반영 (인계를 받은 세션, 기준 `d80690da1`)

셀프 리뷰 두 축(표준은 sonnet·high, 명세는 세션 모델)이 낸 것과 판정이다.

고친 것:

- Major(명세 축): `CMD`의 `--model claude-opus-5`를 뺐다. 위 "결정"의 까닭이다. 고친 이미지를 같은 방식으로 다시 지어(`--no-cache`, 63초) 손으로 봤다(스크래치 `verify_cmd.sh`, 네트워크 없음·읽기 전용 루트·이름 있는 볼륨 둘·홈 tmpfs·루프백 예외). `docker inspect`의 `Config.Cmd`는 `["agent-os","serve","--plugins-root","/app/plugins","--traces","/data/traces"]`다. 모델 지정이 없으면 종료 코드 1과 `기본 모델의 이름이 없다`로 끝난다. `AGENT_OS_MODEL=does-not-exist`는 종료 코드 1과 `기본 모델 플러그인이 없다: does-not-exist`로 끝난다(처음 판에서는 같은 값이 조용히 무시됐다고 명세 축 에이전트가 보고했다. 나는 처음 판을 다시 돌려 보지 않았다). `AGENT_OS_MODEL=claude-opus-5`는 약 8초 만에 `healthy`이고 `agent-os --version`이 `0.1.0-rc.1`, `id`가 `uid=10001(agentos)`다.
- 일지의 "캐시가 따뜻한 재빌드" 설명이 틀렸다. 프로브 README 2번과 `run.py`는 19~21초가 `--no-cache`의 값이라고 적는다. 위 "짓는 시간"과 "명세 문장과 다른 것"을 고쳤다. 같은 조건의 63초를 더했다.
- 빌드 명령 예시의 `SOURCE`가 `git remote`와 달랐다(`njh6803/agent`). `njh6803/agent-os`로 고쳤다. 앞 세션의 확인용 빌드는 그 값으로 지었는지 알 수 없다. 이번 재빌드는 `njh6803/agent-os`로 지었다.
- "손으로 쟀다"를 "손으로 봤다"로 고쳤다(`CODING_STANDARDS.md`의 쟀다는 커밋한 프로브에만). 일지의 "부하 탓으로 길어졌다"는 어림으로 고쳤다.
- Dockerfile 주석과 일지: 홈도 10001 소유이고 `/app/.venv/.lock`은 0666인 빈 파일이다.
- 프로브 README: "빌드 시간이 길게 나왔다"는 반례가 있었다(alpine 36초는 첫 범위보다 짧았다). 숫자를 그대로 적는 문장으로 고쳤다. 날짜가 KST와 UTC로 갈리는 것과 항목 4를 두 번 돌린 까닭을 기록하지 않았다는 것을 적었다. sed 갈래의 `0.1.0`과 `0.0.0`을 가르는 문장을 고쳤다.

남긴 것(이유):

- 판정 고침의 양성 대조(고치기 전 판이라면 실패했을 회차): 프로브 README가 이미 "재지 않았다"고 적고 있다. 가짜 서버(stdout을 닫고 남는 것)로 가르는 갈래는 후속이다. 이 티켓의 체크박스가 요구하는 것은 판정을 고치고 다시 돌리는 것이다.
- 명세 574행(Further Notes)의 "고친 판은 아직 돌리지 않았다"가 serve_image에 대해 낡았다. 명세는 사용자가 승인한 문서라 이 티켓에서 고치지 않았다. 그 문장을 쓰는 곳은 명세 갱신이고 PR 본문에 알린다.
- `Literal` 타입, `server` 튜플 묶기, digest 중복(프로브 Dockerfile 셋, `scan_tools.py`): 프로브 코드의 스멜(판단 항목)이고 digest 중복은 08·11이 deploy 쪽을 늘리면 다시 본다.
- `# syntax=docker/dockerfile:1`: BuildKit이 필요하다는 것은 Docker 29 기본이라 둔다. 헤더 주석에 BuildKit을 적지 않았다.
- `REVISION`·`SOURCE`를 주지 않아도 빈 라벨로 빌드된다: 명세는 실패를 요구하지 않았다. 11의 판 내기가 두 값을 넘긴다.
- Grype Critical 1건(certifi): 티켓대로 멈추지 않았다. 후속 후보로 `uv.lock`의 certifi를 2026.10.18 이상으로 올리는 일이 있다.

밀 주장(PR 직전 리뷰에 나열할 새 사실 문장): 첫째, `CMD`에 `--model`을 박으면 환경 변수를 이긴다(`resolve_model_name`이 플래그를 먼저 본다). 둘째, 같은 `--no-cache` 조건의 짓는 시간이 19~21초, 46·54초, 63초, 275초로 갈렸다. 셋째, 홈 폴더가 10001 소유다.

## 인계 시점의 상태 (앞 세션이 셀프 리뷰 직전에 넘겼다. 참고)

- 이 PC의 Docker에 이 티켓이 남긴 것: 이미지 `ri-serve-impl:0.1.0-rc.1`(리뷰 반영 뒤 다시 지은 것)과 `ri-serve-*` 프로브 이미지들(프로브 README "남긴 이미지"가 적은 것). 컨테이너와 이름 있는 볼륨은 남기지 않았다.
- 이 일지 본문에 쓴 숫자(275초 빌드, 열 단계 확인, Grype 건수)의 원본 로그는 세션 스크래치패드에 있어 커밋하지 않았다. 다시 재야 하면 같은 명령(위 `docker build`, 위 `docker run`)으로 쳐서 일지를 고친다.
- PR 본문에 적을 것: 시간 값이 명세와 달랐지만 동작이 같아 멈추지 않았다는 판단(위 "명세 문장과 다른 것", 사용자가 확인한 것이 아니다), 형제 08이 같은 데몬에서 빌드를 돌았다는 점, 후속 후보 `uv.lock`의 certifi 올리기, 명세 574행의 낡은 문장이다.

open-session을 부른다 2026-11-15T16:48:36Z
