# 시제품(측정용) Dockerfile. widget-runtime-values 명세가 결정을 내리려고 재는 데만 쓴다. 최종 Dockerfile 이 아니다.
#
# 빌드 맥락은 저장소의 web/ 이고, 이 폴더는 이름 붙은 둘째 맥락 probe 로 준다(run.py 의 build 섹션이 그렇게 부른다).
#   docker build -f <이 파일> --build-context probe=<이 폴더> --target <단계> -t wrv-img:<단계> <저장소>/web
# base, manifests, deps-full 세 단계는 deploy/images/widget.Dockerfile 의 것을 글자까지 그대로 옮겼다(같은 층 캐시와
# pnpm 캐시 마운트를 쓴다). 저장소의 파일은 고치지 않는다. 고친 판이 필요한 자리는 이미지 안의 사본을 고친다
# (patch-config.mjs).
#
# 재려는 꼴. 위젯을 이미지를 지을 때 사이트 파일 없이 한 번 빌드해 둔다(응답 머리는 frame-ancestors 'none'). 컨테이너가
# 뜰 때 진입 단계(entry.mjs)가 사이트 파일을 읽어 두 가지만 한다. 지어 둔 routes-manifest 의 frame-ancestors 값을 바꿔
# 쓰고, 위젯의 스크립트가 받아 갈 값 파일(public/runtime.json)을 쓴다. 그 뒤 next start 만 부른다.

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

# 워크스페이스 전체 의존성. 이미지를 지을 때의 빌드만 쓴다(Vite, Tailwind, 타입 검사가 요구하는 시험 쪽 패키지).
FROM manifests AS deps-full
RUN --mount=type=cache,id=agent-os-pnpm-store,target=/pnpm/store \
    --mount=type=cache,id=agent-os-pnpm-meta,target=/root/.cache/pnpm \
    pnpm install --frozen-lockfile --store-dir /pnpm/store

# 위젯과 그것이 기대는 워크스페이스 패키지의 운영 의존성만. 뜬 뒤의 이미지가 이것으로 서는지가 재려는 것 가운데 하나다.
FROM manifests AS deps-prod
RUN --mount=type=cache,id=agent-os-pnpm-store,target=/pnpm/store \
    --mount=type=cache,id=agent-os-pnpm-meta,target=/root/.cache/pnpm \
    pnpm install --frozen-lockfile --prod --store-dir /pnpm/store --filter "@agent-os/widget..."

# 프로브의 도우미 파일. 윈도 체크아웃이 줄 끝을 CRLF 로 바꿨을 수 있어 벗긴다.
FROM base AS probe-files
COPY --from=probe entry.mjs fetch.mjs wait.mjs inspect.mjs /probe/
COPY --from=probe sites_a.toml sites_b.toml sites_broken.toml /probe/
RUN sed -i 's/\r$//' /probe/* && chmod 0644 /probe/*

# ---------------------------------------------------------------------------------------------------------------------
# 산출물을 짓는 단계. 사이트 파일을 주지 않는다. 그래서 응답 머리는 frame-ancestors 'none' 으로 굳는다.
# patch-config.mjs 는 이미지 안의 next.config.ts 사본에 값 파일의 응답 머리 규칙 하나를 더한다. 이 단계는 프로브 파일
# 가운데 그것 하나만 받는다. 다른 도우미를 고쳐도 빌드 층이 다시 돌지 않는다.
FROM deps-full AS build
COPY . .
COPY --from=probe patch-config.mjs /probe/patch-config.mjs
WORKDIR /app/web/apps/widget
ENV NEXT_TELEMETRY_DISABLED=1
RUN node /probe/patch-config.mjs next.config.ts
RUN node tools/start.ts build && rm -rf .next/cache
# 지어 둔 routes-manifest 는 원본으로 남기고(.build.json), 뜰 때 쓰는 파일과 값 파일의 자리를 빈 파일로 만들어 둔다.
RUN cp .next/routes-manifest.json .next/routes-manifest.build.json \
    && : > public/runtime.json

# 대조용. 워크스페이스 전체 의존성이 깔린 build 단계에 들여다보는 도우미만 얹는다. "뜬 뒤의 이미지에는 빌드 도구가
# 없다"는 답이 도구가 실제로 없어서인지를, 같은 도우미가 여기서는 판을 내는지로 가른다. 빌드 층은 다시 돌지 않는다.
FROM build AS build-inspect
COPY --from=probe-files /probe/inspect.mjs /probe/inspect.mjs

# ---------------------------------------------------------------------------------------------------------------------
# 뜬 뒤의 이미지 둘에 공통인 바탕: 운영 의존성, 산출물, 시작에 드는 파일만.
FROM base AS runtime
COPY --from=deps-prod /app/web /app/web
COPY packages/site-file/src packages/site-file/src
COPY --from=build /app/web/apps/widget/next.config.ts apps/widget/next.config.ts
COPY --from=build /app/web/apps/widget/.next apps/widget/.next
COPY --from=build /app/web/apps/widget/public apps/widget/public
COPY --from=probe-files /probe /probe
COPY --from=probe-files /probe/entry.mjs apps/widget/tools/entry.mjs
WORKDIR /app/web/apps/widget
ENV NEXT_TELEMETRY_DISABLED=1
EXPOSE 3000
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["node", "tools/entry.mjs", "--hostname", "127.0.0.1", "--port", "3000"]

# 갈래 하나: 뜰 때 쓰는 두 파일이 앱 폴더 안의 보통 파일이다(앱 사용자 소유). 루트가 쓰기 가능해야 선다.
FROM runtime AS image-inplace
RUN chown agentos:agentos .next/routes-manifest.json public/runtime.json
USER agentos

# 갈래 둘: 뜰 때 쓰는 두 파일의 자리를 쓰기 가능한 폴더 하나(/run/agent-os-widget)로 가는 심볼릭 링크로 둔다. 읽기 전용
# 루트에서는 그 폴더를 tmpfs 로 준다. 폴더는 이미지에도 앱 사용자 소유로 만들어 두어 tmpfs 없이도 선다.
FROM runtime AS image
RUN mkdir -p /run/agent-os-widget \
    && chown agentos:agentos /run/agent-os-widget \
    && chmod 0700 /run/agent-os-widget \
    && rm .next/routes-manifest.json public/runtime.json \
    && ln -s /run/agent-os-widget/routes-manifest.json .next/routes-manifest.json \
    && ln -s /run/agent-os-widget/runtime.json public/runtime.json
USER agentos
