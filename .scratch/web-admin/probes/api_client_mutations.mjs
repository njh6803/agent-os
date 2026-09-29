// 티켓 03(생성 클라이언트)의 TS 테스트가 무엇을 재는지 변이로 본다. `tools/mutate.py` 는 pytest 만 돌아서, 같은
// 규약을 따르는 러너를 여기 둔다. 원문이 파일에 정확히 한 번 있는지 먼저 보고(하나라도 틀리면 아무것도 쓰지 않는다),
// 변이 없이 명령이 초록인지 기준선을 본 뒤, 변이마다 원래 바이트를 쥐고 넣어 돌리고 finally 에서 그 바이트를 쓴다.
//
// 쓰는 법: node .scratch/web-admin/probes/api_client_mutations.mjs [이름 ...]   (저장소 루트에서. 명령은 web/ 에서 돈다)
// 네트워크를 타지 않는다. 약 2분. 종료 코드: 모두 기대대로면 0, 어긋나거나 기준선이 초록이 아니면 1, 원문이 틀리거나
// 없는 이름을 주면 2.
//
// 빨강과 오류를 가른다(`tools/mutate.py` 의 규약 4). Vitest 는 실패한 테스트가 셀 때만, tsc 는 변이가 적은 파일
// (`diagnosticIn`)에서 진단이 날 때만 빨강이다. tsc 의 종료 코드는 문법 오류와 타입 에러가 같고(2), 오류 번호로도
// 가를 수 없다(`satisfies` 의 어긋남이 TS1360 이다). 수집 오류나 엉뚱한 자리의 오류로 빨간 변이는 테스트의 이빨을
// 재지 않는다.
//
// 판정자·tsconfig 검사·최신성 검사의 위반 사례는 테스트가 스스로 만들어 넣어 매 실행이 빨강을 다시 잰다. 여기 있는
// 것은 그 테스트들이 기대는 코드와 설정 쪽(최신성 검사의 보고와 쓰기, 판정자의 범위)의 변이다.

import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const WEB = join(process.cwd(), "web");
const VITEST = (file) => `pnpm exec vitest run ${file}`;
const TSC = "pnpm exec tsc --noEmit -p packages/api-client";
const STREAM = "packages/api-client/src/stream.ts";
const STREAM_TEST = VITEST("packages/api-client/src/stream.test.ts");
const GENERATOR = "tools/generate-api-client.ts";
const GENERATOR_TEST = VITEST("tools/generate-api-client.test.ts");

const MUTATIONS = [
  {
    name: "재귀 Json 자리가 없어도 지나간다",
    file: GENERATOR,
    old: "  if (at === -1 || source.includes(RECURSIVE_JSON, at + 1)) {",
    new: "  if (at === -1) {\n    return source;\n  }\n  if (source.includes(RECURSIVE_JSON, at + 1)) {",
    command: GENERATOR_TEST,
    expect: "red",
  },
  {
    name: "재귀 Json 자리가 둘이어도 첫째를 바꾼다",
    file: GENERATOR,
    old: "  if (at === -1 || source.includes(RECURSIVE_JSON, at + 1)) {",
    new: "  if (at === -1) {",
    command: GENERATOR_TEST,
    expect: "red",
  },
  {
    name: "최신성 검사가 어긋남을 보고하지 않는다",
    file: GENERATOR,
    old: "  if (existsSync(GENERATED) && readFileSync(GENERATED, \"utf-8\") === generated) {",
    new: "  if (existsSync(GENERATED)) {",
    command: GENERATOR_TEST,
    expect: "red",
  },
  {
    name: "최신성 검사가 생성물을 고쳐 쓴다",
    file: GENERATOR,
    old: "async function staleness(contract: string): Promise<string | null> {\n  const generated = await generate(contract);\n",
    // 보고는 그대로 하되(종료 1과 안내) 생성물을 사본의 결과로 덮어쓴다. "고쳐 쓰지 않는다" 테스트 하나만 빨개야 한다.
    new: "async function staleness(contract: string): Promise<string | null> {\n  const generated = await generate(contract);\n  const before = existsSync(GENERATED) ? readFileSync(GENERATED, \"utf-8\") : \"\";\n  writeFileSync(GENERATED, generated);\n  if (before !== generated) {\n    return \"pnpm -C web run generate:api-client\";\n  }\n",
    command: GENERATOR_TEST,
    expect: "red",
    // 이 변이는 생성물을 바꾼 사본의 결과로 덮어쓴다. 되돌리기는 생성물도 쥔다.
    also: ["packages/api-client/src/generated/openapi.ts"],
  },
  {
    name: "줄 끝의 \\r 를 벗기지 않는다",
    file: STREAM,
    old: 'buffer[end - 1] === "\\r" ? end - 1 : end',
    new: "end",
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "data: 뒤의 공백을 벗기지 않는다",
    file: STREAM,
    old: 'return [value.startsWith(" ") ? value.slice(1) : value];',
    new: "return [value];",
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "data: 뒤의 공백을 모두 벗긴다",
    file: STREAM,
    old: 'return [value.startsWith(" ") ? value.slice(1) : value];',
    new: "return [value.trimStart()];",
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "여러 data 줄을 줄바꿈 없이 잇는다",
    file: STREAM,
    old: 'data.push(values.join("\\n"));',
    new: 'data.push(values.join(""));',
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "data 가 아닌 필드도 값으로 읽는다",
    file: STREAM,
    old: '  if (name !== "data") {\n    return [];\n  }',
    new: '  if (name === "") {\n    return [];\n  }',
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "끝나지 않은 프레임의 앞부분을 남기지 않는다",
    file: STREAM,
    old: "  return { data, rest: buffer.slice(frameStart) };",
    new: "  return { data, rest: buffer.slice(lineStart) };",
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "술어가 프로토타입의 이름을 종류로 본다",
    file: STREAM,
    old: "    Object.hasOwn(EVENT_TYPES, value.type)",
    new: "    value.type in EVENT_TYPES",
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "술어가 판별자 밖의 필드를 요구한다",
    file: STREAM,
    old: '    "type" in value &&',
    new: '    "type" in value &&\n    "run_id" in value &&',
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "JSON 이 아닌 프레임을 버린다",
    file: STREAM,
    old: "    : { kind: \"raw\", raw: data };",
    new: "    : { kind: \"raw\", raw: parsed.ok ? data : \"\" };",
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "스트림이 끝날 때 남은 프레임을 버린다",
    file: STREAM,
    old: "    buffer += done ? `${decoder.decode()}\\n\\n` : decoder.decode(value, { stream: true });",
    new: "    buffer += done ? decoder.decode() : decoder.decode(value, { stream: true });",
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "조각을 이어 해독하지 않는다",
    file: STREAM,
    old: "decoder.decode(value, { stream: true })",
    new: "decoder.decode(value)",
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "스트림이 에러로 끝나면 에러를 삼킨다",
    file: STREAM,
    old: "  try {\n    yield* framesFrom(reader);\n  } finally {",
    new: "  try {\n    yield* framesFrom(reader);\n  } catch (error) {\n    void error;\n  } finally {",
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "스트림이 에러로 끝나면 잠금을 풀지 않는다",
    file: STREAM,
    old: "  try {\n    yield* framesFrom(reader);\n  } finally {\n    reader.releaseLock();\n  }",
    new: "  try {\n    yield* framesFrom(reader);\n  } catch (error) {\n    throw error;\n  }\n  reader.releaseLock();",
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "잠금을 풀지 않는다",
    file: STREAM,
    old: "  } finally {\n    reader.releaseLock();\n  }",
    new: "  } finally {\n    void reader;\n  }",
    command: STREAM_TEST,
    expect: "red",
  },
  {
    name: "관리 클라이언트가 채널 경로도 안다",
    diagnosticIn: "clients.test-d.ts(",
    file: "packages/api-client/src/clients.ts",
    old: "export type AdminPaths = Omit<paths, ChannelPath>;",
    new: "export type AdminPaths = paths;",
    command: TSC,
    expect: "red",
  },
  {
    name: "채널 클라이언트가 실행을 일으키는 경로도 안다",
    diagnosticIn: "clients.test-d.ts(",
    file: "packages/api-client/src/clients.ts",
    old: 'export type ChannelPaths = Pick<paths, "/runs/{run_id}/approval">;',
    new: "export type ChannelPaths = Pick<paths, ChannelPath>;",
    command: TSC,
    expect: "red",
  },
  {
    name: "목록 응답이 readonly 배열이다(--immutable 을 다시 켠 모양)",
    diagnosticIn: "clients.test-d.ts(",
    file: "packages/api-client/src/generated/openapi.ts",
    old: '          "application/json": components["schemas"]["PluginRow"][];',
    new: '          "application/json": readonly components["schemas"]["PluginRow"][];',
    command: TSC,
    expect: "red",
  },
  {
    name: "종류 목록에서 하나가 빠진다",
    diagnosticIn: "stream.ts(",
    file: STREAM,
    old: "  run_failed: true,\n",
    new: "",
    command: TSC,
    expect: "red",
  },
  {
    name: "패키지의 타입 에러를 typecheck 가 본다",
    diagnosticIn: "clients.ts(",
    file: "packages/api-client/src/clients.ts",
    old: "function bearer(token: string): { readonly Authorization: string } {",
    new: "export const 틀린_값: number = \"문자열\";\n\nfunction bearer(token: string): { readonly Authorization: string } {",
    command: "pnpm run typecheck",
    expect: "red",
  },
  {
    name: "판정자가 생성물을 범위에서 뺀다",
    file: "eslint.config.mjs",
    old: "  {\n    linterOptions: { noInlineConfig: true },\n  },",
    new: '  {\n    linterOptions: { noInlineConfig: true },\n  },\n  { ignores: ["**/generated/**"] },',
    command: VITEST("eslint.config.test.ts"),
    expect: "red",
  },
  {
    name: "클라이언트가 상대 경로 /api 를 baseUrl 로 쓴다",
    file: "packages/api-client/src/clients.ts",
    old: '  return new URL("/api", location.origin).href;',
    new: '  return "/api";',
    command: VITEST("packages/api-client/src/clients.test.ts"),
    expect: "red",
  },
];

/** 초록, 빨강(테스트가 잡았다), 오류(코드가 깨졌거나 엉뚱한 자리가 빨갛다)를 가른다. */
function run(command, diagnosticIn) {
  const result = spawnSync(command, { cwd: WEB, shell: true, encoding: "utf-8" });
  const out = `${result.stdout}${result.stderr}`;
  if (result.status === 0) {
    return "green";
  }
  if (command.includes("vitest")) {
    return /Tests\s+\d+ failed/.test(out) ? "red" : `error(${result.status})`;
  }
  return diagnosticIn !== undefined && out.includes(diagnosticIn) ? "red" : `error(${result.status})`;
}

const selected = process.argv.slice(2);
const unknown = selected.filter((name) => !MUTATIONS.some((m) => m.name === name));
if (unknown.length > 0) {
  console.log(`없는 변이 이름: ${unknown.join(", ")}`);
  process.exit(2);
}
const chosen = selected.length > 0 ? MUTATIONS.filter((m) => selected.includes(m.name)) : MUTATIONS;

for (const mutation of chosen) {
  const text = readFileSync(join(WEB, mutation.file), "utf-8");
  if (text.split(mutation.old).length !== 2) {
    console.log(`원문이 ${mutation.file} 에 정확히 한 번 있지 않다: ${mutation.name}`);
    process.exit(2);
  }
}

const baselines = [...new Set(chosen.map((m) => m.command))];
for (const command of baselines) {
  const status = run(command);
  console.log(`기준선 ${status}: ${command}`);
  if (status !== "green") {
    process.exit(1);
  }
}

let mismatches = 0;
for (const mutation of chosen) {
  const files = [mutation.file, ...(mutation.also ?? [])];
  const originals = new Map(files.map((file) => [file, readFileSync(join(WEB, file))]));
  let status = "";
  try {
    const text = readFileSync(join(WEB, mutation.file), "utf-8");
    writeFileSync(join(WEB, mutation.file), text.replace(mutation.old, mutation.new));
    status = run(mutation.command, mutation.diagnosticIn);
  } finally {
    for (const [file, bytes] of originals) {
      writeFileSync(join(WEB, file), bytes);
    }
  }
  const ok = status === mutation.expect;
  if (!ok) {
    mismatches += 1;
  }
  console.log(`${ok ? "기대대로" : "어긋남"} ${status} (기대 ${mutation.expect}): ${mutation.name}`);
}
process.exit(mismatches === 0 ? 0 : 1);
