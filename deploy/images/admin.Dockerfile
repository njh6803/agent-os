# 관리 화면 이미지. 빌드 맥락은 저장소의 web/ 이다.
#
#   docker build -f deploy/images/admin.Dockerfile \
#     --build-arg IMAGE_VERSION=0.1.0-rc.1 --build-arg IMAGE_REVISION=<커밋 해시 40자> \
#     --build-arg IMAGE_SOURCE=<저장소 주소> -t admin web
#
# 이미지를 지을 때 `next build` 까지 돌려 산출물(.next)을 담는다. 상류(AGENT_OS_UPSTREAM)는 산출물에 굳으므로 지을 때
# http://serve:8000 으로 넣는다. 그 값은 루프백 규칙의 예외(표지 파일 + AGENT_OS_CONTAINER_NETWORK=1)가 켜져야 빌드의
# 검사를 지나므로, 짓는 단계에도 둘을 둔다. 시작 때 다시 도는 검사는 컨테이너의 표지 파일과 compose 가 주는 환경 변수로
# 지난다. 근거는 .scratch/release-image/spec.md 의 "이미지의 구성"과 "관리 화면의 상류"다.

ARG NODE_IMAGE=node:24-trixie-slim@sha256:af02d57b57719b9657a45199a79264a9437940cd55b3c7b3fc99615654f124a0

# ---------------------------------------------------------------------------------------------------------------------
# 바탕: node 와 pnpm, tini, 앱 사용자, 루프백 예외의 표지 파일.
FROM ${NODE_IMAGE} AS base
ENV COREPACK_HOME=/opt/corepack \
    COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    CI=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 agentos \
    && useradd --uid 10001 --gid 10001 --create-home --home-dir /home/agentos --shell /usr/sbin/nologin agentos \
    && mkdir -p /etc/agent-os \
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
COPY packages/react-18/package.json packages/react-18/package.json
COPY packages/site-file/package.json packages/site-file/package.json
COPY packages/ui/package.json packages/ui/package.json

# pnpm 의 저장소와 메타데이터 캐시는 캐시 마운트라 이미지에 남지 않는다.
FROM manifests AS deps-full
RUN --mount=type=cache,id=agent-os-pnpm-store,target=/pnpm/store \
    --mount=type=cache,id=agent-os-pnpm-meta,target=/root/.cache/pnpm \
    pnpm install --frozen-lockfile --store-dir /pnpm/store

FROM manifests AS deps-prod
RUN --mount=type=cache,id=agent-os-pnpm-store,target=/pnpm/store \
    --mount=type=cache,id=agent-os-pnpm-meta,target=/root/.cache/pnpm \
    pnpm install --frozen-lockfile --prod --store-dir /pnpm/store --filter "@agent-os/admin..."

# ---------------------------------------------------------------------------------------------------------------------
# 산출물을 짓는 단계. 상류를 http://serve:8000 으로 넣고, 그 값이 검사를 지나게 예외의 환경 변수를 둔다(표지 파일은 바탕에 있다).
FROM deps-full AS build
COPY . .
WORKDIR /app/web/apps/admin
ENV NEXT_TELEMETRY_DISABLED=1 \
    AGENT_OS_CONTAINER_NETWORK=1 \
    AGENT_OS_UPSTREAM=http://serve:8000
RUN node node_modules/next/dist/bin/next build && rm -rf .next/cache

# ---------------------------------------------------------------------------------------------------------------------
# 이미지: 운영 의존성과 산출물, 시작에 드는 파일만. 읽기 전용 루트로 돈다.
FROM base AS image
ARG IMAGE_VERSION=unknown
ARG IMAGE_REVISION=unknown
ARG IMAGE_SOURCE=unknown
LABEL org.opencontainers.image.version=${IMAGE_VERSION} \
      org.opencontainers.image.revision=${IMAGE_REVISION} \
      org.opencontainers.image.source=${IMAGE_SOURCE}
COPY --from=deps-prod /app/web /app/web
COPY apps/admin/package.json apps/admin/next.config.ts apps/admin/
COPY apps/admin/tools/start.ts apps/admin/tools/loopback.ts apps/admin/tools/
COPY apps/admin/public apps/admin/public
COPY --from=build /app/web/apps/admin/.next apps/admin/.next
WORKDIR /app/web/apps/admin
ENV NEXT_TELEMETRY_DISABLED=1
USER agentos
EXPOSE 3000
ENTRYPOINT ["/usr/bin/tini", "--"]
# 0.0.0.0 은 compose 가 AGENT_OS_CONTAINER_NETWORK=1 을 줄 때만 받는다. 주지 않으면 시작 래퍼가 진단과 함께 끝난다.
CMD ["node", "tools/start.ts", "start", "--hostname", "0.0.0.0", "--port", "3000"]
