# syntax=docker/dockerfile:1
# 대조. 지금의 deploy/images/serve.Dockerfile 처럼 루트의 pyproject.toml 과 잠금 파일만 들이고 워크스페이스 루트에서
# 잠금 검사를 켠 채 깐다.
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
RUN uv sync --locked --no-dev --no-install-project
