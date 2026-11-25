# 위젯 미리보기 페이지(portal) 이미지. 빌드 맥락은 저장소의 web/ 이다.
#
#   docker build -f deploy/images/portal.Dockerfile \
#     --build-arg IMAGE_VERSION=0.1.0-rc.1 --build-arg IMAGE_REVISION=<커밋 해시 40자> \
#     --build-arg IMAGE_SOURCE=<저장소 주소> -t portal web
#
# 빌드 산출물이 없다. 운영 의존성과 apps/portal, packages/site-file, packages/ui 의 소스를 담고 node 가 .ts 를 빌드 없이
# 돈다. 읽기 전용 루트와 읽기 전용 설정 폴더로 돈다. 설정과 개인 키는 /etc/agent-os/portal/ 에, 사이트 파일은
# /etc/agent-os/site/sites.toml 에 얹힌다(둘은 다른 폴더다. 개인 키를 읽는 것은 이 컨테이너뿐이다).
# 근거는 .scratch/release-image/spec.md 의 "이미지의 구성"의 위젯 미리보기 페이지와 "배포 파일 묶음"이다.

ARG NODE_IMAGE=node:24-trixie-slim@sha256:af02d57b57719b9657a45199a79264a9437940cd55b3c7b3fc99615654f124a0

# ---------------------------------------------------------------------------------------------------------------------
# 바탕: node 와 pnpm, tini, 앱 사용자, 루프백 예외의 표지 파일, 얹을 폴더의 자리.
FROM ${NODE_IMAGE} AS base
ENV COREPACK_HOME=/opt/corepack \
    COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    CI=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 agentos \
    && useradd --uid 10001 --gid 10001 --create-home --home-dir /home/agentos --shell /usr/sbin/nologin agentos \
    && mkdir -p /etc/agent-os/site /etc/agent-os/portal \
    && echo "agent-os image" > /etc/agent-os/image \
    && corepack enable pnpm \
    && corepack prepare pnpm@11.24.0 --activate
WORKDIR /app/web

# 의존성 설치에 드는 파일만. 소스를 고쳐도 설치 층이 다시 돌지 않는다.
FROM base AS manifests
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/admin/package.json apps/admin/package.json
COPY apps/portal/package.json apps/portal/package.json
COPY apps/widget/package.json apps/widget/package.json
COPY packages/api-client/package.json packages/api-client/package.json
COPY packages/e2e-stack/package.json packages/e2e-stack/package.json
COPY packages/e2e-standalone/package.json packages/e2e-standalone/package.json
COPY packages/react-18/package.json packages/react-18/package.json
COPY packages/site-file/package.json packages/site-file/package.json
COPY packages/ui/package.json packages/ui/package.json
COPY packages/widget-admin-client/package.json packages/widget-admin-client/package.json

# 이 앱과 그것이 기대는 워크스페이스 패키지의 운영 의존성만. pnpm 의 저장소와 메타데이터 캐시는 캐시 마운트라 이미지에 남지 않는다.
FROM manifests AS deps-prod
RUN --mount=type=cache,id=agent-os-pnpm-store,target=/pnpm/store \
    --mount=type=cache,id=agent-os-pnpm-meta,target=/root/.cache/pnpm \
    pnpm install --frozen-lockfile --prod --store-dir /pnpm/store --filter "@agent-os/portal..."

# ---------------------------------------------------------------------------------------------------------------------
FROM deps-prod AS image
ARG IMAGE_VERSION=unknown
ARG IMAGE_REVISION=unknown
ARG IMAGE_SOURCE=unknown
LABEL org.opencontainers.image.version=${IMAGE_VERSION} \
      org.opencontainers.image.revision=${IMAGE_REVISION} \
      org.opencontainers.image.source=${IMAGE_SOURCE}
COPY apps/portal apps/portal
COPY packages/site-file packages/site-file
COPY packages/ui packages/ui
WORKDIR /app/web/apps/portal
USER agentos
EXPOSE 3000
ENTRYPOINT ["/usr/bin/tini", "--"]
# 듣는 주소와 포트는 설정 파일의 portal.host 와 portal.port 가 정한다. 0.0.0.0 은 compose 가
# AGENT_OS_CONTAINER_NETWORK=1 을 줄 때만 받는다. 주지 않으면 시작 명령이 진단과 함께 끝난다.
CMD ["node", "--disable-warning=ExperimentalWarning", "tools/start.ts", "--config", "/etc/agent-os/portal/portal.toml", "--site-file", "/etc/agent-os/site/sites.toml"]
