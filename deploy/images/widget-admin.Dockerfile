# syntax=docker/dockerfile:1
# 위젯 관리 서버 이미지(ADR 0064, ADR 0066, .scratch/widget-admin-server/spec.md "이미지"). 빌드 컨텍스트는
# 저장소 루트이고 들일 파일은 같은 폴더의 widget-admin.Dockerfile.dockerignore 가 고른다. 짓는 명령:
#
#   docker build -f deploy/images/widget-admin.Dockerfile \
#     --build-arg APP_VERSION=0.1.0-rc.1 --build-arg REVISION=<커밋 해시> \
#     --build-arg SOURCE=<저장소 주소> -t widget-admin:0.1.0-rc.1 .
#
# 판 번호(APP_VERSION)는 필수다. 주지 않으면 빌드가 실패한다(serve 이미지와 같은 까닭이다). 저장소 파일은
# 고치지 않고 빌드 단계 안의 멤버 pyproject.toml 사본만 고친다. 제품 판은 하나라 Agent OS 이미지와 같은 번호를 단다.
#
# 바탕 이미지와 uv 이미지는 deploy/images/serve.Dockerfile 과 같은 digest 다. 올릴 때는 두 파일을 함께 바꾼다
# (tests/tools/test_release_ci.py 가 같은지 본다). 이 이미지에는 Agent OS 의 코드도 모델 SDK 도 들지 않는다.
ARG PYTHON_IMAGE=python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b
ARG UV_IMAGE=ghcr.io/astral-sh/uv@sha256:5cc1805e2426484abca4ad46ea783bab281fdb225fd82d8ce6d66a81254bac85

FROM ${UV_IMAGE} AS uv

# ------------------------------ 파이썬 가상 환경 ------------------------------
FROM ${PYTHON_IMAGE} AS build
COPY --from=uv /uv /usr/local/bin/uv
ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_NO_CACHE=1
WORKDIR /build
# 의존성은 멤버 하나만 깐다. 잠금 검사가 작업공간 전체를 읽어야 지나가므로 루트 선언 파일과 잠금 파일과
# 멤버 선언 파일을 들이고, 멤버의 의존성만 깐다(--package). 루트 프로젝트(agent-os)는 깔지 않는다.
COPY pyproject.toml uv.lock ./
COPY widget-admin/pyproject.toml widget-admin/pyproject.toml
RUN uv sync --locked --no-dev --package widget-admin --no-install-workspace
COPY widget-admin/src widget-admin/src
# 판 번호는 여기서만 넣는다. 고친 뒤에는 잠금 검사가 지나지 않으므로 멤버만 --frozen 으로 깐다.
# 바탕의 sed 가 줄을 바꾸지 못해도 오류 없이 끝날 수 있으므로, 깐 뒤 설치된 패키지의 판을 넘긴 번호와
# 대 보고 다르면 빌드를 실패시킨다.
ARG APP_VERSION
RUN test -n "${APP_VERSION}" || { echo "APP_VERSION 빌드 인자가 필요하다(예: 0.1.0-rc.1)" >&2; exit 1; }; \
    printf '%s' "${APP_VERSION}" | grep -Eq '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-rc\.[1-9][0-9]*)?$' \
      || { echo "APP_VERSION 은 X.Y.Z 나 X.Y.Z-rc.N 꼴이어야 한다: ${APP_VERSION}" >&2; exit 1; }; \
    sed -i "0,/^version = \"[^\"]*\"\$/s//version = \"${APP_VERSION}\"/" widget-admin/pyproject.toml \
 && grep -n '^version = ' widget-admin/pyproject.toml \
 && uv sync --frozen --no-dev --package widget-admin --no-editable \
 && installed="$(/app/.venv/bin/python -c 'import importlib.metadata as m; print(m.version("widget-admin"))')" \
 && { [ "${installed}" = "${APP_VERSION}" ] \
      || { echo "설치된 widget-admin 의 판 ${installed} 이 넘긴 번호 ${APP_VERSION} 와 다르다" >&2; exit 1; }; }

# ------------------------------ 끝 이미지 ------------------------------
FROM ${PYTHON_IMAGE} AS widget-admin
RUN apt-get update \
 && apt-get install -y --no-install-recommends tini \
 && rm -rf /var/lib/apt/lists/*
# uid·gid 10001 의 agentos 사용자(serve 이미지와 같다). 표지 파일은 root 소유로 굽는다(루프백 규칙의 예외.
# 앱 사용자는 만들 수 없다). 이 이미지는 파일을 쓰는 자리가 없어 읽기 전용 루트로 돈다.
RUN groupadd --gid 10001 agentos \
 && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin agentos \
 && mkdir -p /etc/agent-os \
 && printf 'agent-os widget-admin image\n' > /etc/agent-os/image
COPY --from=build /app/.venv /app/.venv
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
EXPOSE 8100
ENTRYPOINT ["/usr/bin/tini", "--"]
# 서버는 연결 문자열을 환경 변수 WIDGET_ADMIN_DATABASE_URL 하나로만 받는다. 그 값은 compose 가 준다.
CMD ["widget-admin", "serve"]
