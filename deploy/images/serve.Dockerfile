# syntax=docker/dockerfile:1
# serve 이미지(ADR 0056, .scratch/release-image/spec.md "이미지의 구성"). 빌드 컨텍스트는 저장소 루트이고
# 들일 파일은 같은 폴더의 serve.Dockerfile.dockerignore 가 고른다. 짓는 명령:
#
#   docker build -f deploy/images/serve.Dockerfile \
#     --build-arg APP_VERSION=0.1.0-rc.1 --build-arg REVISION=<커밋 해시> \
#     --build-arg SOURCE=<저장소 주소> -t serve:0.1.0-rc.1 .
#
# 판 번호(APP_VERSION)는 필수다. 주지 않으면 빌드가 실패한다. 저장소의 판(0.0.0)으로 조용히 지어
# 라벨과 태그가 거짓이 되는 것보다 낫기 때문이다. 판 번호는 `vX.Y.Z[-rc.N]` 태그에서 v 를 뗀 글자다.
# 저장소 파일은 고치지 않고 빌드 단계 안의 pyproject.toml 사본만 고친다.
#
# 바탕 이미지는 2026-11-13 에 받은 태그의 digest 다. 차례로 python:3.12-slim-trixie,
# node:24-trixie-slim, ghcr.io/astral-sh/uv:latest(0.13.8). 올릴 때는 digest 를 새로 받아 바꾼다.
ARG PYTHON_IMAGE=python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
ARG NODE_IMAGE=node@sha256:af02d57b57719b9657a45199a79264a9437940cd55b3c7b3fc99615654f124a0
ARG UV_IMAGE=ghcr.io/astral-sh/uv@sha256:5cc1805e2426484abca4ad46ea783bab281fdb225fd82d8ce6d66a81254bac85

FROM ${UV_IMAGE} AS uv
FROM ${NODE_IMAGE} AS node

# ------------------------------ 파이썬 가상 환경 ------------------------------
FROM ${PYTHON_IMAGE} AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1
WORKDIR /build
# 의존성은 고치지 않은 pyproject.toml 과 잠금 파일로, 잠금 검사를 켠 채 깐다.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY README.md ./
COPY src ./src
# 판 번호는 여기서만 넣는다. 고친 뒤에는 잠금 검사가 지나지 않으므로 프로젝트만 --frozen 으로 깐다.
# 바탕의 sed 가 줄을 바꾸지 못해도 오류 없이 끝날 수 있으므로(busybox), 깐 뒤 설치된 패키지의 판을
# 넘긴 번호와 대 보고 다르면 빌드를 실패시킨다.
ARG APP_VERSION
RUN test -n "${APP_VERSION}" || { echo "APP_VERSION 빌드 인자가 필요하다(예: 0.1.0-rc.1)" >&2; exit 1; }; \
    printf '%s' "${APP_VERSION}" | grep -Eq '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-rc\.[1-9][0-9]*)?$' \
      || { echo "APP_VERSION 은 X.Y.Z 나 X.Y.Z-rc.N 꼴이어야 한다: ${APP_VERSION}" >&2; exit 1; }; \
    sed -i "0,/^version = \"[^\"]*\"\$/s//version = \"${APP_VERSION}\"/" pyproject.toml \
 && grep -n '^version = ' pyproject.toml \
 && uv sync --frozen --no-dev --no-editable \
 && installed="$(/app/.venv/bin/python -c 'import importlib.metadata as m; print(m.version("agent-os"))')" \
 && { [ "${installed}" = "${APP_VERSION}" ] \
      || { echo "설치된 agent-os 의 판 ${installed} 이 넘긴 번호 ${APP_VERSION} 와 다르다" >&2; exit 1; }; }

# ------------------------------ 예시 MCP 서버 ------------------------------
FROM node AS mcp
ARG MCP_EVERYTHING_VERSION=2.3.0
RUN npm install --global --omit=dev --no-audit --no-fund --no-update-notifier \
      "@modelcontextprotocol/server-everything@${MCP_EVERYTHING_VERSION}"

# ------------------------------ 끝 이미지 ------------------------------
FROM ${PYTHON_IMAGE} AS serve
RUN apt-get update \
 && apt-get install -y --no-install-recommends tini \
 && rm -rf /var/lib/apt/lists/*
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=mcp /usr/local/lib/node_modules /usr/local/lib/node_modules
# uid·gid 10001 의 agentos 사용자. passwd 항목이 없는 uid 로 띄우면 serve 가 시작할 때 부르는
# getpass.getuser() 가 KeyError 트레이스백으로 끝난다(serve_image README 3번). 표지 파일은 root 소유로
# 굽는다(루프백 규칙의 예외. 앱 사용자는 만들 수 없다). 쓰는 자리는 플러그인 루트와 트레이스 폴더뿐이고
# 그 둘과 홈 폴더(useradd --create-home)가 10001 소유다. 그 밖은 root 소유라 읽기 전용 루트로 돌 수
# 있다(빈 파일 /app/.venv/.lock 하나만 uv 가 0666 으로 만들어 두었으나 내용이 없어 무해하다).
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
 && ln -s ../lib/node_modules/@modelcontextprotocol/server-everything/dist/index.js \
      /usr/local/bin/mcp-server-everything \
 && groupadd --gid 10001 agentos \
 && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin agentos \
 && mkdir -p /etc/agent-os /data/traces \
 && printf 'agent-os serve image\n' > /etc/agent-os/image \
 && chown 10001:10001 /data/traces
COPY --from=build /app/.venv /app/.venv
COPY --chown=10001:10001 plugins /app/plugins
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /app
ARG APP_VERSION
ARG REVISION
ARG SOURCE
LABEL org.opencontainers.image.version="${APP_VERSION}" \
      org.opencontainers.image.revision="${REVISION}" \
      org.opencontainers.image.source="${SOURCE}"
USER 10001:10001
EXPOSE 8000
ENTRYPOINT ["/usr/bin/tini", "--"]
# 기본 모델은 CMD 에 박지 않는다. 플래그가 환경 변수 AGENT_OS_MODEL 을 이기므로(resolve_model_name),
# 박으면 운영자가 환경 변수로 고른 모델이 조용히 무시된다(ADR 0040). 운영자는 환경 변수로 준다.
# docker run <이미지> --model X 는 CMD 를 통째로 바꿔 tini 가 --model 을 실행하려다 실패하므로, 플래그를 쓰려면 CMD 전체를 다시 적는다.
CMD ["agent-os", "serve", "--plugins-root", "/app/plugins", "--traces", "/data/traces"]
