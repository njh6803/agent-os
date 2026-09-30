/**
 * 생성 클라이언트의 타입을 루트 `openapi.json` 에서 만든다(ADR 0021). 생성물은 커밋하고 손으로 고치지 않는다.
 * `--check` 는 다시 생성한 결과가 커밋된 생성물과 바이트까지 같은지 보는 `pnpm -C web verify` 의 한 단계다.
 * 파이썬 티켓이 계약을 바꾸고 다시 생성하지 않으면 이 단계가 빨개져, 생성물이 같은 PR 에 담긴다.
 *
 * 만드는 차례는 셋이다.
 * 1. openapi-typescript 의 기본 출력. CLI 가 아니라 API 를 부른다. CLI 는 머리 주석을 붙이고 Redocly 설정을 따로 찾는다
 *    (`redocly.yaml`, 없으면 `minimal`). API 는 operationId 중복을 에러로 보는 기본 설정이다. 이 계약에서 두 출력은
 *    머리 주석 밖에서 바이트까지 같았다(`.scratch/web-admin/probes/immutable_readable.sh`). `--immutable` 을 주지 않는다.
 *    openapi-fetch 0.17.0 이 readonly 배열을 배열로 보지 못해 응답을 순회할 수 없다(ADR 0021 의 2026-09-29 이력).
 *    열거는 기본값으로 리터럴 유니온이다.
 * 2. 재귀 `Json` 한 자리를 `unknown` 으로 바꾼다. openapi-typescript 는 `Json` 이 제 자신을 가리키는 그 자리에서
 *    TS2502 를 내고 그것을 `any` 로 둔다(ADR 0020). 다른 곳에 `any` 가 생기면 판정자가 빨개지도록 그 자리만 바꾼다.
 * 3. Prettier. 생성물도 verify 의 포맷 검사(`pnpm run format`) 범위다. 저장소가 `* text=auto eol=lf` 라 윈도우와 CI 가 같은 바이트를 본다.
 *
 * 사용: node tools/generate-api-client.ts [--check] [계약 파일]. 계약 파일을 주지 않으면 루트 `openapi.json` 이다.
 * 쓰는 곳은 늘 커밋된 생성물 하나다. `--check` 는 쓰지 않고, 어긋나면 한 줄 쓰고 1.
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { pathToFileURL } from "node:url";
import openapiTS, { astToString } from "openapi-typescript";
import { format, resolveConfig } from "prettier";

const WEB = dirname(import.meta.dirname);
export const CONTRACT = join(dirname(WEB), "openapi.json");
export const GENERATED = join(WEB, "packages", "api-client", "src", "generated", "openapi.ts");

const HEADER = [
  "// 생성물이다. 손으로 고치지 않는다. 루트 openapi.json 에서 `pnpm -C web run generate:api-client` 로 만든다.",
  "// openapi-typescript 의 출력에서 재귀 Json 한 자리만 unknown 으로 바꿨다(web/tools/generate-api-client.ts).",
  "",
  "",
].join("\n");

// openapi-typescript 7.13.0 이 낸 재귀 Json 의 자리 그대로다. 모양이 바뀌면 조용히 지나가지 않는다.
const RECURSIVE_JSON = [
  'Json: string | number | boolean | components["schemas"]["Json"][] | {',
  '            [key: string]: components["schemas"]["Json"];',
  "        } | null;",
].join("\n");

/** openapi-typescript 가 낸 재귀 `Json` 한 자리를 `unknown` 으로 바꾼다. 다른 바이트는 그대로다. */
export function replaceRecursiveJson(source: string): string {
  const at = source.indexOf(RECURSIVE_JSON);
  if (at === -1 || source.includes(RECURSIVE_JSON, at + 1)) {
    throw new Error(
      "재귀 Json 자리가 정확히 한 번 있지 않다. 생성기나 계약의 Json 스키마가 바뀌었다. 새 출력을 보고 이 스크립트를 고친다",
    );
  }
  return `${source.slice(0, at)}Json: unknown;${source.slice(at + RECURSIVE_JSON.length)}`;
}

/** 계약 파일에서 커밋될 생성물의 바이트를 만든다. */
export async function generate(contract: string): Promise<string> {
  const types = astToString(await openapiTS(pathToFileURL(contract)));
  const options = await resolveConfig(GENERATED);
  return format(HEADER + replaceRecursiveJson(types), { ...options, filepath: GENERATED });
}

/** 커밋될 생성물을 쓴다. */
async function write(contract: string): Promise<void> {
  const generated = await generate(contract);
  mkdirSync(dirname(GENERATED), { recursive: true });
  writeFileSync(GENERATED, generated);
}

/** 커밋된 생성물이 계약에서 다시 생성한 것과 다르면 그 진단, 같으면 null. 쓰지 않는다. */
async function staleness(contract: string): Promise<string | null> {
  const generated = await generate(contract);
  if (existsSync(GENERATED) && readFileSync(GENERATED, "utf-8") === generated) {
    return null;
  }
  return `생성물이 계약과 다르다: ${contract}. pnpm -C web run generate:api-client 로 다시 생성해 같은 커밋에 담는다`;
}

if (import.meta.main) {
  const args = process.argv.slice(2);
  const contract = args.find((arg) => arg !== "--check") ?? CONTRACT;
  if (args.includes("--check")) {
    const problem = await staleness(contract);
    if (problem !== null) {
      console.log(problem);
      process.exitCode = 1;
    }
  } else {
    await write(contract);
  }
}
