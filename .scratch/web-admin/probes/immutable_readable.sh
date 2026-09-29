#!/usr/bin/env bash
# openapi-typescript 의 생성 타입이 openapi-fetch 를 지난 뒤의 모양을 잰다. --immutable 과 가변 생성물, 그리고 헬퍼에
# readonly 배열 갈래를 패치한 --immutable 을 나란히 둔다. 생성 스크립트가 CLI 대신 API 를 부르는 근거도 여기서 잰다.
# 쓰는 법: bash .scratch/web-admin/probes/immutable_readable.sh <작업 디렉터리>   (저장소 루트에서)
# npm 레지스트리에 닿는다. 세 변형에 같은 검사 파일을 tsc 로 돌린다. 검사는 넷이다.
#   1. GET /plugins 의 data 를 for…of 로 순회할 수 있는가
#   2. 트레이스 상세의 events 가 배열인가
#   3. 결정 스트림의 error 가 생성된 ErrorEnvelope 와 같은 타입인가(대입이 아니라 일치)
#   4. 결정 스트림(parseAs: "stream")의 data. 본문이 Decision 타입 값이면 ReadableStream, 인라인 리터럴이면 unknown 인가
# 2026-09-29 결과(openapi-typescript 7.13.0, openapi-fetch 0.17.0, openapi-typescript-helpers 0.1.0, TypeScript 5.9.3):
#   --immutable 은 1·2·3 이 각 자리에서 빨갛다. 1 은 TS2488, 2·3 은 TS2322 다. 헬퍼의 Readable<T> 가 배열을
#   `T extends (infer E)[]` 로 알아보는데 readonly E[] 는 여기 들지 않고, 키를 재매핑하는 객체 갈래가 배열성을 지운다.
#   가변은 넷 모두 초록이다. 헬퍼의 Readable 에 `T extends readonly (infer E)[] ? readonly Readable<E>[]` 한 줄을 더한
#   --immutable 도 넷 모두 초록이다. 4 는 세 변형이 같다(판별 유니온 본문에서 옵션 추론이 제약으로 떨어진다).
#   API 출력(머리 주석 + astToString)은 CLI 출력과 두 생성물 모두 바이트까지 같다.
# 종료 코드는 위 결과와 모두 같으면 0, 하나라도 다르면 1 이다. 판이 바뀌면 값도 바뀔 수 있다.
set -u
repo="$(pwd)"
contract="$repo/openapi.json"
[ -f "$contract" ] || { echo "저장소 루트에서 돌린다: $contract 가 없다"; exit 2; }
work="${1:?작업 디렉터리를 준다}"
mkdir -p "$work" && cd "$work" || exit 1
printf '{ "name": "immutable-readable", "private": true, "type": "module" }\n' > package.json
npm i -s --no-audit --no-fund openapi-typescript@7.13.0 openapi-fetch@0.17.0 typescript@5.9 >/dev/null 2>&1 || exit $?
echo "=== versions ==="
for p in openapi-typescript openapi-fetch openapi-typescript-helpers typescript; do
  printf '%s ' "$p"; node -p "require('./node_modules/$p/package.json').version"
done
ok=0

npx openapi-typescript "$contract" -o immutable.ts --immutable >/dev/null 2>&1 || exit $?
npx openapi-typescript "$contract" -o mutable.ts >/dev/null 2>&1 || exit $?
echo "=== API 와 CLI ==="
CONTRACT="$contract" node --input-type=module -e '
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import openapiTS, { astToString, COMMENT_HEADER } from "openapi-typescript";
const url = pathToFileURL(process.env.CONTRACT);
let same = true;
for (const [file, immutable] of [["immutable.ts", true], ["mutable.ts", false]]) {
  const api = COMMENT_HEADER + astToString(await openapiTS(url, { immutable }));
  const equal = api === readFileSync(file, "utf8");
  console.log(file, "API==CLI:", equal);
  same &&= equal;
}
process.exit(same ? 0 : 1);' || ok=1

# 재귀 Json 은 TS2502 로 any 가 되므로 두 생성물 모두 unknown 으로 바꾼다(생성 스크립트와 같은 일).
node -e '
const fs = require("fs");
for (const file of ["immutable.ts", "mutable.ts"]) {
  const text = fs.readFileSync(file, "utf8");
  const at = text.indexOf("Json: string");
  if (at === -1) { console.log("Json 자리를 찾지 못했다:", file); process.exit(2); }
  const end = text.indexOf("| null;", at) + "| null;".length;
  fs.writeFileSync(file, text.slice(0, at) + "Json: unknown;" + text.slice(end));
}' || exit $?

for variant in immutable mutable; do
  cat > "check-$variant.ts" <<EOF
import createClient from "openapi-fetch";
import type { components, paths } from "./$variant";
type Same<A, B> = (<T>() => T extends A ? 1 : 2) extends (<T>() => T extends B ? 1 : 2) ? true : false;
type IsUnknown<T> = unknown extends T ? true : false;
const client = createClient<paths>({ baseUrl: "http://127.0.0.1" });
export async function probe(): Promise<void> {
  const plugins = await client.GET("/plugins");
  for (const row of plugins.data ?? []) { void row.kind; } // 검사 1
  const trace = await client.GET("/traces/{run_id}", { params: { path: { run_id: "r1" } } });
  const events: readonly unknown[] | undefined = trace.data?.events; void events; // 검사 2
  const decision: components["schemas"]["Decision"] = { decision: "approve", pause_index: 0 };
  const typed = await client.POST("/runs/{run_id}/approval", {
    params: { path: { run_id: "r1" } }, body: decision, parseAs: "stream",
  });
  const sameError: Same<typeof typed.error, components["schemas"]["ErrorEnvelope"] | undefined> = true; void sameError; // 검사 3
  const stream: ReadableStream<Uint8Array<ArrayBuffer>> | null | undefined = typed.data; void stream; // 검사 4
  const inline = await client.POST("/runs/{run_id}/approval", {
    params: { path: { run_id: "r1" } }, body: { decision: "approve", pause_index: 0 }, parseAs: "stream",
  });
  const unknownData: IsUnknown<typeof inline.data> = true; void unknownData; // 검사 4
}
EOF
done

flags="--noEmit --strict --skipLibCheck --target es2024 --lib es2024,dom --module preserve --moduleResolution bundler"

# 검사 파일에서 표지가 선 줄들. tsc 의 진단이 그 줄마다 있는지 본다.
lines_of() { grep -n "// 검사 $2\$" "$1" | cut -d: -f1; }
expect_red_at() {  # 파일 출력 검사번호...
  local file="$1" out="$2"; shift 2
  for n in "$@"; do
    for line in $(lines_of "$file" "$n"); do
      if grep -q "^$file($line," <<<"$out"; then echo "검사 $n 빨강(줄 $line)"; else echo "검사 $n 이 빨갛지 않다(줄 $line)"; ok=1; fi
    done
  done
}

echo "=== --immutable ==="
# shellcheck disable=SC2086
immutable_out=$(npx tsc $flags check-immutable.ts)
echo "$immutable_out" | cut -c1-160
expect_red_at check-immutable.ts "$immutable_out" 1 2 3
for n in 4; do
  for line in $(lines_of check-immutable.ts "$n"); do
    if grep -q "^check-immutable.ts($line," <<<"$immutable_out"; then echo "검사 $n 이 빨갛다(줄 $line)"; ok=1; fi
  done
done

echo "=== 가변 ==="
# shellcheck disable=SC2086
npx tsc $flags check-mutable.ts
status=$?
echo "exit $status"
[ "$status" -eq 0 ] || ok=1

echo "=== 헬퍼를 패치한 --immutable ==="
# 설치본의 선언 파일 셋(.d.ts, .d.mts, .d.cts)에 같은 한 줄을 넣는다. openapi-fetch 는 ESM 해석으로 .d.mts 를 읽는다.
for declaration in node_modules/openapi-typescript-helpers/dist/index.d.*ts; do
  sed -i 's/T extends (infer E)\[\] ? Readable<E>\[\] :/T extends (infer E)[] ? Readable<E>[] : T extends readonly (infer E)[] ? readonly Readable<E>[] :/' "$declaration"
  grep -q "readonly Readable<E>" "$declaration" || { echo "패치가 들지 않았다: $declaration"; ok=1; }
done
# shellcheck disable=SC2086
npx tsc $flags check-immutable.ts
status=$?
echo "exit $status"
[ "$status" -eq 0 ] || ok=1

exit "$ok"
