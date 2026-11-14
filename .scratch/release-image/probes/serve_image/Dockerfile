# syntax=docker/dockerfile:1
# release-image 명세의 측정용 시제품이다. 최종 Dockerfile 이 아니다. 빌드 컨텍스트는 저장소 루트이고
# 들일 파일은 같은 폴더의 Dockerfile.dockerignore 가 고른다. 저장소의 파일은 고치지 않고, 판 번호는
# 빌드 단계 안의 pyproject.toml 사본에만 넣는다(길은 Dockerfile.version 의 b1-frozen 이다).
#
# 끝 타깃 셋이 바탕 이미지 후보다. run.py 가 --target 으로 고른다.
#   deb-py    파이썬 공식 이미지(Debian trixie slim)에 Node 실행 파일과 npm 을 옮겨 넣는다
#   deb-node  Node 공식 이미지(Debian trixie slim)에 uv 가 받은 파이썬(python-build-standalone)을 넣는다
#   alpine    파이썬 공식 이미지(Alpine)에 Node(Alpine 판) 실행 파일과 npm 을 옮겨 넣는다
#
# 바탕 이미지는 2026-11-13 에 받은 태그의 digest 다. 차례로 python:3.12-slim-trixie,
# node:24-trixie-slim, python:3.12-alpine, node:24-alpine, ghcr.io/astral-sh/uv:latest(0.13.8).
ARG PYTHON_IMAGE=python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
ARG NODE_IMAGE=node@sha256:af02d57b57719b9657a45199a79264a9437940cd55b3c7b3fc99615654f124a0
ARG PYTHON_ALPINE_IMAGE=python@sha256:c5ba3deef00c7758561a0f03c26f44f10589263d40e732b8748e0d1f38f6dd89
ARG NODE_ALPINE_IMAGE=node@sha256:116b800c3754b440ee0aa3ed2f20f5bf3d99a554bfd9adeea09ea8017f6e85f5
ARG UV_IMAGE=ghcr.io/astral-sh/uv@sha256:5cc1805e2426484abca4ad46ea783bab281fdb225fd82d8ce6d66a81254bac85

FROM ${UV_IMAGE} AS uv
FROM ${NODE_IMAGE} AS node
FROM ${NODE_ALPINE_IMAGE} AS node-alpine

# ============================== deb-py ==============================
FROM ${PYTHON_IMAGE} AS deb-py-build
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
ARG APP_VERSION=0.0.0
RUN sed -i "0,/^version = \"[^\"]*\"\$/s//version = \"${APP_VERSION}\"/" pyproject.toml \
 && grep -n '^version = ' pyproject.toml \
 && uv sync --frozen --no-dev --no-editable

FROM node AS deb-mcp
ARG MCP_EVERYTHING_VERSION=2.3.0
RUN npm install --global --omit=dev --no-audit --no-fund --no-update-notifier \
      "@modelcontextprotocol/server-everything@${MCP_EVERYTHING_VERSION}"

FROM ${PYTHON_IMAGE} AS deb-py
RUN apt-get update \
 && apt-get install -y --no-install-recommends tini \
 && rm -rf /var/lib/apt/lists/*
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=deb-mcp /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
 && ln -s ../lib/node_modules/@modelcontextprotocol/server-everything/dist/index.js \
      /usr/local/bin/mcp-server-everything \
 && groupadd --gid 10001 agentos \
 && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin agentos \
 && mkdir -p /data/traces \
 && chown 10001:10001 /data/traces
COPY --from=deb-py-build /app/.venv /app/.venv
COPY --chown=10001:10001 plugins /app/plugins
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /app
USER 10001:10001
EXPOSE 8000
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["agent-os", "serve", "--plugins-root", "/app/plugins", "--traces", "/data/traces", "--model", "claude-opus-5"]

# ============================== deb-node ==============================
FROM ${NODE_IMAGE} AS deb-node-build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_INSTALL_DIR=/opt/python \
    UV_PYTHON_PREFERENCE=only-managed \
    UV_NO_CACHE=1
WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN uv python install 3.12 \
 && uv sync --locked --no-dev --no-install-project
COPY README.md ./
COPY src ./src
ARG APP_VERSION=0.0.0
RUN sed -i "0,/^version = \"[^\"]*\"\$/s//version = \"${APP_VERSION}\"/" pyproject.toml \
 && grep -n '^version = ' pyproject.toml \
 && uv sync --frozen --no-dev --no-editable

FROM ${NODE_IMAGE} AS deb-node
ARG MCP_EVERYTHING_VERSION=2.3.0
RUN apt-get update \
 && apt-get install -y --no-install-recommends tini \
 && rm -rf /var/lib/apt/lists/* \
 && npm install --global --omit=dev --no-audit --no-fund --no-update-notifier \
      "@modelcontextprotocol/server-everything@${MCP_EVERYTHING_VERSION}" \
 && npm cache clean --force \
 && groupadd --gid 10001 agentos \
 && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin agentos \
 && mkdir -p /data/traces \
 && chown 10001:10001 /data/traces
COPY --from=deb-node-build /opt/python /opt/python
COPY --from=deb-node-build /app/.venv /app/.venv
COPY --chown=10001:10001 plugins /app/plugins
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /app
USER 10001:10001
EXPOSE 8000
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["agent-os", "serve", "--plugins-root", "/app/plugins", "--traces", "/data/traces", "--model", "claude-opus-5"]

# ============================== alpine ==============================
FROM ${PYTHON_ALPINE_IMAGE} AS alpine-build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1
WORKDIR /build
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY README.md ./
COPY src ./src
ARG APP_VERSION=0.0.0
RUN sed -i "0,/^version = \"[^\"]*\"\$/s//version = \"${APP_VERSION}\"/" pyproject.toml \
 && grep -n '^version = ' pyproject.toml \
 && uv sync --frozen --no-dev --no-editable

FROM node-alpine AS alpine-mcp
ARG MCP_EVERYTHING_VERSION=2.3.0
RUN npm install --global --omit=dev --no-audit --no-fund --no-update-notifier \
      "@modelcontextprotocol/server-everything@${MCP_EVERYTHING_VERSION}"

FROM ${PYTHON_ALPINE_IMAGE} AS alpine
RUN apk add --no-cache tini libstdc++ libgcc
COPY --from=node-alpine /usr/local/bin/node /usr/local/bin/node
COPY --from=alpine-mcp /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
 && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
 && ln -s ../lib/node_modules/@modelcontextprotocol/server-everything/dist/index.js \
      /usr/local/bin/mcp-server-everything \
 && addgroup -g 10001 agentos \
 && adduser -D -u 10001 -G agentos agentos \
 && mkdir -p /data/traces \
 && chown 10001:10001 /data/traces
COPY --from=alpine-build /app/.venv /app/.venv
COPY --chown=10001:10001 plugins /app/plugins
ENV PATH=/app/.venv/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /app
USER 10001:10001
EXPOSE 8000
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["agent-os", "serve", "--plugins-root", "/app/plugins", "--traces", "/data/traces", "--model", "claude-opus-5"]
