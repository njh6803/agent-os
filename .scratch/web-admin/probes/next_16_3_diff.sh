#!/usr/bin/env bash
# 명세 검토가 옆 저장소의 Next 16.3.3 설치본에서 읽은 것(rewrites 가 빌드에 박힌다, 서버 파일 관례, tsconfig 를 고쳐
# 쓰는 것)이 관리 화면이 고정한 16.3.6 에서도 같은지, 그 코드가 든 파일을 두 판의 tarball 에서 바이트로 견준다.
# 쓰는 법: bash .scratch/web-admin/probes/next_16_3_diff.sh <작업 디렉터리>
# npm 레지스트리에 닿는다(tarball 둘, 합쳐 약 60MB). 판 문자열("16.3.3"/"16.3.6")만 다른 줄은 같은 것으로 센다.
# 2026-09-30 결과: 열여섯 파일이 모두 같다. build/index.js, bin/next, server/lib/start-server.js 는 판 문자열만(세 줄, 두
# 줄, 한 줄) 달랐다. 종료 0.
set -u
work="${1:?작업 디렉터리를 준다}"
mkdir -p "$work" && cd "$work" || exit 1

for version in 16.3.3 16.3.6; do
  if [ ! -d "$version" ]; then
    tarball=$(npm pack -s "next@$version") || exit $?
    mkdir -p "$version" && tar -xzf "$tarball" -C "$version" || exit $?
  fi
done

# 자리마다 무엇을 보는지.
#   rewrites 가 빌드 산출물에 박히고 start 가 그것을 읽는다: build/index.js, lib/load-custom-routes.js,
#     server/next-server.js, server/lib/router-utils/filesystem.js, server/lib/router-utils/resolve-routes.js
#   rewrites 의 목적지를 푸는 것(IPv6 리터럴이 막히는 자리): shared/lib/router/utils/prepare-destination.js
#   서버 파일 관례(route, middleware, proxy, instrumentation): lib/constants.js, build/entries.js
#   tsconfig 를 고쳐 쓰는 것: lib/typescript/writeConfigurationDefaults.js, lib/typescript/writeAppTypeDeclarations.js
#   바인딩과 CLI: cli/next-dev.js, cli/next-start.js, bin/next
#   agentRules 가 끄는 것: server/lib/start-server.js(게이트 `agentRules !== false`), server/lib/generate-agent-files.js(쓰는 내용)
#   설정 불러오기: server/config-shared.js
files=(
  build/index.js
  lib/load-custom-routes.js
  server/next-server.js
  server/lib/router-utils/filesystem.js
  server/lib/router-utils/resolve-routes.js
  shared/lib/router/utils/prepare-destination.js
  lib/constants.js
  build/entries.js
  lib/typescript/writeConfigurationDefaults.js
  lib/typescript/writeAppTypeDeclarations.js
  cli/next-dev.js
  cli/next-start.js
  bin/next
  server/lib/start-server.js
  server/lib/generate-agent-files.js
  server/config-shared.js
)

status=0
for file in "${files[@]}"; do
  old="16.3.3/package/dist/$file"
  new="16.3.6/package/dist/$file"
  if [ ! -f "$old" ] || [ ! -f "$new" ]; then
    echo "없음  $file"
    status=1
  elif cmp -s "$old" "$new"; then
    echo "같음  $file"
  elif cmp -s <(sed 's/16\.3\.3/16.3.x/g' "$old") <(sed 's/16\.3\.6/16.3.x/g' "$new"); then
    echo "같음  $file  (판 문자열 $(diff "$old" "$new" | grep -c '^<') 줄만 다르다)"
  else
    echo "다름  $file"
    diff "$old" "$new" | head -20
    status=1
  fi
done
echo "exit $status"
exit "$status"
