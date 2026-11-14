# 시제품(측정용) Dockerfile. release-image 명세가 결정을 내리려고 재는 데만 쓴다. 최종 Dockerfile 이 아니다.
#
# 빌드 맥락은 저장소의 web/ 이고, 이 폴더는 이름 붙은 둘째 맥락 probe 로 준다(run.py 의 build 단계가 그렇게 부른다).
#   docker build -f <이 파일> --build-context probe=<이 폴더> --target <단계> -t ri-web-<이름> <저장소>/web
# 저장소의 파일은 고치지 않는다. 고친 판이 필요한 갈래는 이미지 안의 사본을 고친다(admin-exception, admin-standalone,
# widget-lean 계열). pnpm 스토어와 메타데이터 캐시는 캐시 마운트라 이미지에 들지 않는다. 사용자(USER)는 정하지 않는다.
# 회차마다 docker run 의 --user 로 준다(root 로 돌려 쓰는 자리를 찾는 회차가 있다).

ARG NODE_IMAGE=node@sha256:dc26ae92c9fb15cf6b1d63e20f0944b2efe0f115b20e00be48fb23fceb061c54

# ---------------------------------------------------------------------------------------------------------------------
# 바탕: node 와 pnpm(web/package.json 의 packageManager 와 같은 판).
FROM ${NODE_IMAGE} AS base
ENV COREPACK_HOME=/opt/corepack \
    COREPACK_ENABLE_DOWNLOAD_PROMPT=0 \
    CI=1
RUN corepack enable pnpm && corepack prepare pnpm@11.24.0 --activate && pnpm --version
WORKDIR /app/web

# 프로브의 도우미 파일. 윈도 체크아웃이 줄 끝을 CRLF 로 바꿨을 수 있어 벗긴다.
FROM base AS probe-files
COPY --from=probe entry.sh entry-widget.sh strip-tests.sh /probe/
COPY --from=probe wait.mjs fetch.mjs upstream-stub.mjs portal-fixture.mjs prune-manifests.mjs patch-admin.mjs patch-widget.mjs /probe/
COPY --from=probe sites_a.toml sites_b.toml sites_broken.toml /probe/
RUN sed -i 's/\r$//' /probe/* && chmod 0755 /probe/*.sh && chmod 0644 /probe/*.mjs /probe/*.toml

# 의존성 설치에 드는 파일만. 소스를 고쳐도 설치 층이 다시 돌지 않는다.
FROM base AS manifests
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/admin/package.json apps/admin/package.json
COPY apps/portal/package.json apps/portal/package.json
COPY apps/widget/package.json apps/widget/package.json
COPY packages/api-client/package.json packages/api-client/package.json
COPY packages/e2e-stack/package.json packages/e2e-stack/package.json
COPY packages/site-file/package.json packages/site-file/package.json
COPY packages/ui/package.json packages/ui/package.json

# ---------------------------------------------------------------------------------------------------------------------
# 의존성 갈래. 이름의 뒤는 pnpm 에 준 범위다.
# full: 워크스페이스 전체(뿌리의 개발 의존성까지).
FROM manifests AS deps-full
RUN --mount=type=cache,id=ri-web-pnpm-store,target=/pnpm/store \
    --mount=type=cache,id=ri-web-pnpm-meta,target=/root/.cache/pnpm \
    pnpm install --frozen-lockfile --store-dir /pnpm/store

# full-homecache: 위와 같되 pnpm 의 메타데이터 캐시(/root/.cache/pnpm)를 캐시 마운트로 빼지 않은 것. 그 캐시가 이미지에
# 얼마나 얹히는지의 대조다. 다른 갈래는 모두 그 캐시를 마운트로 빼 이미지에 싣지 않는다.
FROM manifests AS deps-full-homecache
RUN --mount=type=cache,id=ri-web-pnpm-store,target=/pnpm/store \
    pnpm install --frozen-lockfile --store-dir /pnpm/store

# widget-filter: 위젯과 그것이 기대는 워크스페이스 패키지의 의존성(개발 의존성 포함). pnpm 은 뿌리의 것도 함께 깔았다.
FROM manifests AS deps-widget-filter
RUN --mount=type=cache,id=ri-web-pnpm-store,target=/pnpm/store \
    --mount=type=cache,id=ri-web-pnpm-meta,target=/root/.cache/pnpm \
    pnpm install --frozen-lockfile --store-dir /pnpm/store --filter "@agent-os/widget..."

# widget-prod: 같은 범위의 운영 의존성만.
FROM manifests AS deps-widget-prod
RUN --mount=type=cache,id=ri-web-pnpm-store,target=/pnpm/store \
    --mount=type=cache,id=ri-web-pnpm-meta,target=/root/.cache/pnpm \
    pnpm install --frozen-lockfile --prod --store-dir /pnpm/store --filter "@agent-os/widget..."

# widget-lean: 빌드가 쓰지 않는 개발 의존성을 package.json 사본에서 뺀 뒤 같은 범위로 설치한다. 잠금 파일과 어긋나므로
# --frozen-lockfile 을 쓰지 못한다. 설치된 판이 잠금 파일과 같은지는 run.py 가 따로 본다.
FROM manifests AS deps-widget-lean
COPY --from=probe-files /probe/prune-manifests.mjs /probe/prune-manifests.mjs
RUN node /probe/prune-manifests.mjs
RUN --mount=type=cache,id=ri-web-pnpm-store,target=/pnpm/store \
    --mount=type=cache,id=ri-web-pnpm-meta,target=/root/.cache/pnpm \
    pnpm install --no-frozen-lockfile --store-dir /pnpm/store --filter "@agent-os/widget..."

# admin-prod, portal-prod: 그 앱과 그것이 기대는 워크스페이스 패키지의 운영 의존성만.
FROM manifests AS deps-admin-prod
RUN --mount=type=cache,id=ri-web-pnpm-store,target=/pnpm/store \
    --mount=type=cache,id=ri-web-pnpm-meta,target=/root/.cache/pnpm \
    pnpm install --frozen-lockfile --prod --store-dir /pnpm/store --filter "@agent-os/admin..."

FROM manifests AS deps-portal-prod
RUN --mount=type=cache,id=ri-web-pnpm-store,target=/pnpm/store \
    --mount=type=cache,id=ri-web-pnpm-meta,target=/root/.cache/pnpm \
    pnpm install --frozen-lockfile --prod --store-dir /pnpm/store --filter "@agent-os/portal..."

# ---------------------------------------------------------------------------------------------------------------------
# 위젯. 컨테이너가 뜰 때 빌드한다(entry-widget.sh). 갈래는 의존성의 범위와 시험 파일을 지웠는지로 갈린다.
FROM deps-full AS widget-full
COPY . .
COPY --from=probe-files /probe /probe
WORKDIR /app/web/apps/widget
ENTRYPOINT ["/probe/entry-widget.sh"]

# 위와 같되 uid 1000(node)이 쓸 자리를 미리 만든다. 쓰는 자리는 root 로 돌린 회차의 docker diff 에서 찾았다.
FROM widget-full AS widget-full-nonroot
RUN mkdir -p .next public && touch next-env.d.ts && chown -R node:node .next public next-env.d.ts

# next typegen 으로 next-env.d.ts 를 미리 지어 두고(root 소유 그대로) .next 와 public 만 uid 1000 의 것으로 둔다.
FROM widget-full AS widget-full-typegen
RUN node node_modules/next/dist/bin/next typegen \
    && rm -rf .next && mkdir -p .next public && chown node:node .next public

FROM deps-widget-filter AS widget-filter
COPY . .
COPY --from=probe-files /probe /probe
WORKDIR /app/web/apps/widget
ENTRYPOINT ["/probe/entry-widget.sh"]

FROM deps-widget-prod AS widget-prod
COPY . .
COPY --from=probe-files /probe /probe
WORKDIR /app/web/apps/widget
ENTRYPOINT ["/probe/entry-widget.sh"]

# lean 의존성에 시험 파일을 그대로 둔 것(타입 검사가 시험 쪽 패키지를 요구하는지의 대조)과 지운 것.
FROM deps-widget-lean AS widget-lean-withtests
COPY . .
COPY --from=probe-files /probe /probe
WORKDIR /app/web/apps/widget
ENTRYPOINT ["/probe/entry-widget.sh"]

FROM widget-lean-withtests AS widget-lean
RUN /probe/strip-tests.sh /app/web/apps/widget

# lean 에 next typegen 으로 next-env.d.ts 를 미리 지어 두고(root 소유 그대로) .next 와 public 만 uid 1000 의 것으로 둔다.
# 읽기 전용 루트 파일 시스템에서 그 둘만 쓰기 가능한 자리로 붙여 빌드가 되는지 본다.
FROM widget-lean AS widget-lean-typegen
RUN node node_modules/next/dist/bin/next typegen \
    && rm -rf .next && mkdir -p .next public && chown node:node .next public

# 위와 같되 next build 의 타입 검사를 건너뛴다(patch-widget.mjs). 타입 검사가 시간과 메모리의 얼마인지의 대조다.
FROM widget-lean-typegen AS widget-lean-notc
RUN node /probe/patch-widget.mjs notypecheck

# ---------------------------------------------------------------------------------------------------------------------
# 관리 화면. 이미지를 지을 때 빌드한다. admin-src 는 빌드 전의 나무다(빌드 시간과 거부를 docker run 으로 잰다).
FROM deps-full AS admin-src
COPY . .
COPY --from=probe-files /probe /probe
WORKDIR /app/web/apps/admin
ENV NEXT_TELEMETRY_DISABLED=1
ENTRYPOINT ["/probe/entry.sh"]
CMD ["node", "tools/start.ts", "start", "--hostname", "127.0.0.1", "--port", "3000"]

# 상류를 주지 않은 빌드(기본값 http://127.0.0.1:8000 이 산출물에 박힌다). 앱의 build 스크립트가 next build 다.
FROM admin-src AS admin-full
RUN node node_modules/next/dist/bin/next build

# 산출물만 추린 것(Turbopack 캐시를 뺀다).
FROM admin-full AS admin-out
RUN rm -rf .next/cache

# 운영 의존성만 깐 나무에 산출물과 시작에 드는 파일만 얹는다.
FROM deps-admin-prod AS admin-prod
COPY apps/admin/package.json apps/admin/next.config.ts apps/admin/
COPY apps/admin/tools/start.ts apps/admin/tools/loopback.ts apps/admin/tools/
COPY apps/admin/public apps/admin/public
COPY --from=admin-out /app/web/apps/admin/.next apps/admin/.next
COPY --from=probe-files /probe /probe
WORKDIR /app/web/apps/admin
ENV NEXT_TELEMETRY_DISABLED=1
ENTRYPOINT ["/probe/entry.sh"]
CMD ["node", "tools/start.ts", "start", "--hostname", "127.0.0.1", "--port", "3000"]

# 상류 판정에 측정용 예외를 둔 판. 호스트 이름인 상류(http://serve:8000)로 빌드해 중계가 닿는지 본다.
FROM admin-src AS admin-exception
RUN node /probe/patch-admin.mjs exception
ENV RI_PROBE_UPSTREAM_HOST=serve \
    AGENT_OS_UPSTREAM=http://serve:8000
RUN node node_modules/next/dist/bin/next build

# output: "standalone" 을 더한 판. 크기와, server.js 가 HOSTNAME 을 읽는지 본다.
FROM admin-src AS admin-standalone-build
RUN node /probe/patch-admin.mjs standalone
RUN node node_modules/next/dist/bin/next build

FROM base AS admin-standalone
COPY --from=admin-standalone-build /app/web/apps/admin/.next/standalone /app/standalone
COPY --from=admin-standalone-build /app/web/apps/admin/.next/static /app/standalone/apps/admin/.next/static
COPY --from=admin-standalone-build /app/web/apps/admin/public /app/standalone/apps/admin/public
COPY --from=probe-files /probe /probe
WORKDIR /app/standalone/apps/admin
ENV NEXT_TELEMETRY_DISABLED=1
ENTRYPOINT ["/probe/entry.sh"]
CMD ["node", "server.js"]

# ---------------------------------------------------------------------------------------------------------------------
# 위젯 미리보기 페이지(portal). 빌드 산출물이 없다. 소스와 node_modules 를 담고 node 가 .ts 를 바로 돈다.
FROM deps-portal-prod AS portal-prod
COPY apps/portal apps/portal
COPY packages/site-file packages/site-file
COPY packages/ui packages/ui
COPY --from=probe-files /probe /probe
WORKDIR /app/web/apps/portal
ENTRYPOINT ["/probe/entry.sh"]
CMD ["node", "--disable-warning=ExperimentalWarning", "tools/start.ts", "--config", "/cfg/portal.toml", "--site-file", "/cfg/sites.toml"]

FROM deps-full AS portal-full
COPY . .
COPY --from=probe-files /probe /probe
WORKDIR /app/web/apps/portal
ENTRYPOINT ["/probe/entry.sh"]
CMD ["node", "--disable-warning=ExperimentalWarning", "tools/start.ts", "--config", "/cfg/portal.toml", "--site-file", "/cfg/sites.toml"]
