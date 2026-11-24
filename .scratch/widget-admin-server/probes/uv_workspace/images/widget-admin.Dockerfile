# syntax=docker/dockerfile:1
# 위젯 관리 서버 이미지의 파이썬 단계만(프로브). 바탕과 uv 는 deploy/images/serve.Dockerfile 과 같은 digest 다.
# 멤버 하나만 깔고(--package), 판 번호는 멤버의 pyproject.toml 사본에만 넣는다.
ARG PYTHON_IMAGE=python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
ARG UV_IMAGE=ghcr.io/astral-sh/uv@sha256:5cc1805e2426484abca4ad46ea783bab281fdb225fd82d8ce6d66a81254bac85

FROM ${UV_IMAGE} AS uv

FROM ${PYTHON_IMAGE} AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1
WORKDIR /build
COPY pyproject.toml uv.lock ./
COPY widget-admin/pyproject.toml widget-admin/pyproject.toml
RUN uv sync --locked --no-dev --package widget-admin --no-install-workspace
COPY widget-admin/src widget-admin/src
ARG APP_VERSION
RUN test -n "${APP_VERSION}" \
 && sed -i "0,/^version = \"[^\"]*\"\$/s//version = \"${APP_VERSION}\"/" widget-admin/pyproject.toml \
 && uv sync --frozen --no-dev --package widget-admin --no-editable
