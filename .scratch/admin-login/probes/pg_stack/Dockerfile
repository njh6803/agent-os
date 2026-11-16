# pg_stack 프로브의 리눅스 갈래. release-image 명세가 serve 의 바탕으로 고른 python:3.12-slim-trixie 에
# 저장소의 잠금과 후보 패키지를 함께 깐다. 빌드 컨텍스트는 이 폴더이고, 후보를 더한 pyproject.toml 과
# uv.lock 은 `--build-context tree=<사본 폴더>` 로 받는다(README 의 다시 돌리기).
FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy
WORKDIR /app
COPY --from=tree pyproject.toml uv.lock README.md /app/
RUN uv sync --frozen --no-install-project
COPY . /app/.scratch/admin-login/probes/pg_stack/
ENV PYTHONPATH=/app/.scratch/admin-login/probes/pg_stack PYTHONUTF8=1
