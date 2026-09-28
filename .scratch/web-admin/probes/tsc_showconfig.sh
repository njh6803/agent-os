#!/usr/bin/env bash
# tsconfig 검사의 재료(`tsc --showConfig`)가 extends 를 풀고 strict 계열의 개별 플래그를 드러내는지 잰다.
# 쓰는 법: bash .scratch/web-admin/probes/tsc_showconfig.sh <작업 디렉터리>
# npm 레지스트리에 닿는다. 2026-09-28 결과(TypeScript 5.9.3): 부모의 "strict": true 와 자식의
# "strictNullChecks": false 가 함께 나오고, 나머지 strict 계열 플래그가 true 로 풀려 나온다. 종료 0.
set -u
work="${1:?작업 디렉터리를 준다}"
mkdir -p "$work" && cd "$work" || exit 1
printf '{ "name": "tsc-showconfig", "private": true }\n' > package.json
npm i -s --no-audit --no-fund typescript@5.9 >/dev/null 2>&1 || exit $?
printf '{ "compilerOptions": { "strict": true, "noEmit": true } }\n' > base.json
printf '{ "extends": "./base.json", "compilerOptions": { "strictNullChecks": false }, "files": [] }\n' > tsconfig.json
npx tsc -v || exit $?
# 종료 코드를 찍고 그대로 돌려준다. 마지막 echo 의 0 이 tsc 의 실패를 덮지 않게 한다.
npx tsc --showConfig -p tsconfig.json
status=$?
echo "exit $status"
exit "$status"
