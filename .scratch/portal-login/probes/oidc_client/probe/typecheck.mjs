// 타입 검사 프로브. 후보 셋과 가짜 서버 둘의 코드가 위젯 미리보기 페이지와 같은 tsconfig(`apps/portal/tsconfig.json` 은
// `web/apps/portal/tsconfig.json` 의 복사, `tsconfig.base.json` 은 `web/tsconfig.base.json` 의 복사)에서 `tsc --noEmit` 을
// 지나는지 본다. 두 복사가 저장소의 것과 같은지도 여기서 견준다.
//
// 돌리기: node probe/typecheck.mjs [저장소 경로]
// 산출물: out/typecheck/summary.json, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 측정이 아닌 회차(.claude/rules/probes.md): 종료 코드 0 만으로 맺지 않는다.
// - 본 검사가 0 이 아닌 코드로 끝나면 어긋난 것이다.
// - tsc 가 실제로 본 파일 목록(--listFilesOnly)에 프로브의 `.ts` 아홉과 네 라이브러리의 타입 선언이 모두 있어야 한다.
// - 두 tsconfig 복사가 저장소의 원본과 글자 그대로 같아야 한다(줄 끝만 맞춘다).
// - 양성 대조: 같은 옵션을 물려받은 무대(out/typecheck/control)에 심은 오류가 파일마다 기대한 코드로 걸려야 한다.
//   `noUncheckedIndexedAccess` 의 TS2322(indexed.ts), `erasableSyntaxOnly` 의 TS1294(enum.ts), 그리고 네 라이브러리의
//   반환 타입을 틀린 타입에 넣은 TS2322 넷(library-types.ts 의 줄마다). 뒤의 넷은 라이브러리의 타입이 `any` 로 풀리지
//   않았다는 표지다. 타입 선언을 찾지 못해 `any` 가 됐다면 틀린 대입이 지나간다.
// 어긋나면 종료 코드 1.
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const REPO = process.argv[2] ?? join(ROOT, "..", "..", "..", "..");
const OUT = join(ROOT, "out", "typecheck");
const PROJECT = join(ROOT, "apps", "portal", "tsconfig.json");
const TSC = join(ROOT, "node_modules", "typescript", "bin", "tsc");
const tsc = (...args) => spawnSync(process.execPath, [TSC, ...args], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
const text = (path) => readFileSync(path, "utf8").replaceAll("\r\n", "\n");

rmSync(OUT, { recursive: true, force: true, maxRetries: 5 });
mkdirSync(join(OUT, "control"), { recursive: true });

const main = tsc("--noEmit", "-p", PROJECT);
const listed = tsc("--noEmit", "--listFilesOnly", "-p", PROJECT).stdout.replaceAll("\\", "/");
const mustSee = [
  "apps/portal/server/oidc/contract.ts",
  "apps/portal/server/oidc/openid-client.ts",
  "apps/portal/server/oidc/oauth4webapi.ts",
  "apps/portal/server/oidc/hand.ts",
  "apps/portal/server/oidc/node-fetch.ts",
  "apps/portal/testing/fake-idp.ts",
  "apps/portal/testing/fake-idp-provider.ts",
  "apps/portal/testing/browser.ts",
  "apps/portal/testing/round.ts",
  "node_modules/openid-client/build/index.d.ts",
  "node_modules/oauth4webapi/build/index.d.ts",
  "node_modules/jose/dist/types/index.d.ts",
  "node_modules/@types/oidc-provider/index.d.ts",
];
const notSeen = mustSee.filter((piece) => !listed.includes(piece));

const copies = [
  ["tsconfig.base.json", join(REPO, "web", "tsconfig.base.json")],
  [join("apps", "portal", "tsconfig.json"), join(REPO, "web", "apps", "portal", "tsconfig.json")],
];
const drifted = copies.filter(([copy, original]) => text(join(ROOT, copy)) !== text(original)).map(([copy]) => copy);

writeFileSync(join(OUT, "control", "indexed.ts"), "const items: string[] = [];\nexport const first: string = items[0];\n");
writeFileSync(join(OUT, "control", "enum.ts"), "export enum Mode {\n  Light,\n}\n");
writeFileSync(
  join(OUT, "control", "library-types.ts"),
  [
    'import { base64url } from "jose";',
    'import * as oauth from "oauth4webapi";',
    'import Provider from "oidc-provider";',
    'import * as client from "openid-client";',
    "export const a: number = client.randomState();",
    "export const b: number = oauth.generateRandomState();",
    // 첫 판은 `decodeJwt` 를 썼고 걸리지 않았다. 제네릭 반환이 기대 타입 `number` 로 추론돼 지나간다.
    'export const c: number = base64url.encode("x");',
    'export const d: number = new Provider("http://127.0.0.1").issuer;',
    "",
  ].join("\n"),
);
writeFileSync(
  join(OUT, "control", "tsconfig.json"),
  `${JSON.stringify({ extends: "../../../apps/portal/tsconfig.json", include: ["*.ts"] }, null, 2)}\n`,
);
const control = tsc("--noEmit", "-p", join(OUT, "control", "tsconfig.json"));
const controlOutput = `${control.stdout}${control.stderr}`;
const expectedControl = [
  ["indexed.ts", 2, "TS2322"],
  ["enum.ts", 1, "TS1294"],
  ["library-types.ts", 5, "TS2322"],
  ["library-types.ts", 6, "TS2322"],
  ["library-types.ts", 7, "TS2322"],
  ["library-types.ts", 8, "TS2322"],
];
const missedControl = expectedControl
  .filter(([file, line, code]) => !new RegExp(`${file.replace(".", "\\.")}\\(${String(line)},\\d+\\): error ${code}`).test(controlOutput))
  .map(([file, line, code]) => `${file}:${String(line)} ${code}`);

const problems = [];
if (main.status !== 0) problems.push(`tsc --noEmit 이 ${String(main.status)}로 끝났다(요약의 errors)`);
if (notSeen.length > 0) problems.push(`tsc 가 보지 않은 파일: ${notSeen.join(", ")}`);
if (drifted.length > 0) problems.push(`저장소의 원본과 다른 tsconfig 복사: ${drifted.join(", ")}`);
if (missedControl.length > 0) problems.push(`걸리지 않은 대조: ${missedControl.join(", ")}`);

const summary = {
  probe: "typecheck",
  typescript: JSON.parse(readFileSync(join(ROOT, "node_modules", "typescript", "package.json"), "utf8")).version,
  exit: main.status,
  errors: `${main.stdout}${main.stderr}`.trim().split(/\r?\n/).filter((line) => line !== ""),
  filesSeen: listed.trim().split(/\r?\n/).length,
  control: { exit: control.status, lines: controlOutput.trim().split(/\r?\n/) },
  notMeasured: problems,
};
writeFileSync(join(OUT, "summary.json"), JSON.stringify(summary, null, 2));
console.log(JSON.stringify(summary));
if (problems.length > 0) process.exit(1);
