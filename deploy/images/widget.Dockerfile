# 위젯 이미지. 빌드 맥락은 저장소의 web/ 이다.
#
#   docker build -f deploy/images/widget.Dockerfile \
#     --build-arg IMAGE_VERSION=0.1.0-rc.1 --build-arg IMAGE_REVISION=<커밋 해시 40자> \
#     --build-arg IMAGE_SOURCE=<저장소 주소> -t widget web
#
# 위젯은 컨테이너가 뜰 때 운영자의 사이트 파일로 빌드한 뒤 서비스를 시작한다(ADR 0056 결정 "위젯 이미지"). 사이트 파일은
# 컨테이너 안의 /etc/agent-os/site/sites.toml 에 얹힌다. 그 경로는 시작 명령이 늘 환경 변수로 넘기므로, 파일이 없거나
# 깨졌거나 읽을 수 없으면 위젯의 시작 래퍼가 빌드 전에 까닭을 적고 종료 1로 끝난다.
# 빌드는 앱 폴더 안에 쓰므로 루트를 읽기 전용으로 두지 않는다. 쓰는 자리(.next, public)는 앱 사용자 소유다.
# 근거는 .scratch/release-image/spec.md 의 "이미지의 구성"의 위젯이다.

ARG NODE_IMAGE=node:24-trixie-slim@sha256:af02d57b57719b9657a45199a79264a9437940cd55b3c7b3fc99615654f124a0

# ---------------------------------------------------------------------------------------------------------------------
# 바탕: node 와 pnpm, tini, 앱 사용자, 루프백 예외의 표지 파일, 사이트 파일 폴더.
FROM ${NODE_IMAGE} AS base
ENV COREPACK_HOME=/opt/corepack \
    COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    CI=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 agentos \
    && useradd --uid 10001 --gid 10001 --create-home --home-dir /home/agentos --shell /usr/sbin/nologin agentos \
    && mkdir -p /etc/agent-os/site \
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

# 워크스페이스 전체 의존성을 잠금 파일을 얼려 깐다. 뿌리의 개발 의존성까지 든다(뜰 때의 빌드가 @tailwindcss/vite 등을
# import 하고, 앱의 tsconfig 가 시험 파일까지 담아 타입 검사가 시험 쪽 패키지를 요구한다). pnpm 의 저장소와 메타데이터
# 캐시는 캐시 마운트라 이미지에 남지 않는다.
FROM manifests AS deps-full
RUN --mount=type=cache,id=agent-os-pnpm-store,target=/pnpm/store \
    --mount=type=cache,id=agent-os-pnpm-meta,target=/root/.cache/pnpm \
    pnpm install --frozen-lockfile --store-dir /pnpm/store

# ---------------------------------------------------------------------------------------------------------------------
FROM deps-full AS image
ARG IMAGE_VERSION=unknown
ARG IMAGE_REVISION=unknown
ARG IMAGE_SOURCE=unknown
LABEL org.opencontainers.image.version=${IMAGE_VERSION} \
      org.opencontainers.image.revision=${IMAGE_REVISION} \
      org.opencontainers.image.source=${IMAGE_SOURCE}
COPY . .
WORKDIR /app/web/apps/widget
ENV NEXT_TELEMETRY_DISABLED=1
# root 가 아닌 사용자의 빌드가 next-env.d.ts 를 쓰려다 실패하므로, 지을 때 next typegen 으로 next-env.d.ts 와 .next/types
# 를 미리 만든다. 그 뒤 빌드가 쓰는 자리(.next, public)를 앱 사용자 소유로 둔다. 이 이미지는 지을 때 정한 uid(10001)로만
# 뜬다. 다른 uid 는 public 아래에 폴더를 만들지 못해 멈춘다.
RUN node node_modules/next/dist/bin/next typegen \
    && mkdir -p public \
    && chown -R agentos:agentos .next public
USER agentos
EXPOSE 3000
# 관리 화면·위젯 미리보기 페이지와 달리 -g 를 준다. 위젯은 뜰 때 sh 아래에서 빌드 자식 여럿이 도므로, 빌드 중에 docker stop 이
# 오면 tini 가 시그널을 프로세스 그룹 전체에 보내 묶음 전체에 닿게 한다.
ENTRYPOINT ["/usr/bin/tini", "-g", "--"]
# 사이트 파일의 경로를 늘 넘긴다(환경 변수를 주지 않으면 위젯이 어느 사이트에도 끼워 넣을 수 없는 채로 조용히 뜬다).
# 빌드가 실패하면 서비스를 시작하지 않고 그 종료 코드로 끝난다. 서비스로는 exec 로 갈아타 tini 의 자식이 서비스가 된다.
# 0.0.0.0 은 compose 가 AGENT_OS_CONTAINER_NETWORK=1 을 줄 때만 받는다. 주지 않으면 시작 래퍼가 진단과 함께 끝난다.
CMD ["sh", "-c", "export AGENT_OS_SITE_FILE=/etc/agent-os/site/sites.toml; node tools/start.ts build && exec node tools/start.ts start --hostname 0.0.0.0 --port 3000"]
