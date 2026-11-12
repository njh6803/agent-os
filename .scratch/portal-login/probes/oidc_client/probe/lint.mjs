// 린트 프로브. 저장소의 판정자 설정(web/eslint.config.mjs)을 글자 그대로 옮겨 와 후보 셋과 가짜 서버 둘의 코드에 건다.
//
// 돌리기: node probe/lint.mjs [저장소 경로]
//   저장소 경로를 주지 않으면 이 프로브가 든 저장소의 뿌리(이 폴더에서 네 단계 위)다.
// 산출물: out/lint/(무대), out/lint/eslint.json, out/lint/summary.json, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 무대(out/lint/)는 저장소의 배치를 흉내 낸다. 판정자 설정은 자기 자리에서 `../.gitignore` 를 읽고, 전역 `fetch` 를 푸는
// 예외는 경로(`**/apps/portal/browser/portal.ts`)로 건다.
//   out/lint/.gitignore                          ← 저장소 뿌리의 .gitignore (복사)
//   out/lint/web/eslint.config.mjs               ← 저장소의 web/eslint.config.mjs (복사, 고치지 않는다)
//   out/lint/web/tsconfig.base.json              ← 저장소의 web/tsconfig.base.json (복사)
//   out/lint/web/apps/portal/tsconfig.json       ← 저장소의 web/apps/portal/tsconfig.json (복사)
//   out/lint/web/apps/portal/server/oidc/*.ts, testing/*.ts   ← 프로브의 코드 (복사, 목록은 PROBE_FILES)
//   out/lint/web/apps/portal/server/oidc/planted.ts           ← 일부러 심은 위반(양성 대조)
//   out/lint/web/apps/portal/browser/portal.ts                ← 전역 `fetch` 를 쓰는 페이지 스크립트 자리(예외의 갈래)
//   out/lint/web/apps/portal/node_modules/planted-lib/index.ts ← 전역 `fetch` 를 부르는 라이브러리 자리(범위 밖의 갈래)
// ESLint, typescript-eslint, eslint-plugin-boundaries 는 저장소 잠금 파일과 같은 판(10.11.0, 8.70.1, 7.2.0)을 프로브에
// 설치한 것이고, 무대에서 위로 올라가며 이 프로브 폴더의 node_modules 로 풀린다. 라이브러리의 타입도 같은 길로 풀린다.
//
// 측정이 아닌 회차(.claude/rules/probes.md)
// - ESLint 의 결과에 프로브의 파일 전부와 심은 파일 둘이 있어야 한다(판정자가 실제로 그 파일을 봤다).
// - 어느 파일에도 파싱 오류(fatal)가 없어야 한다. 어느 tsconfig 에도 들지 않는 파일은 규칙이 아니라 파싱 오류로 빨개진다.
// - 심은 위반에서 기대한 규칙 ID 가 기대한 줄에 모두 걸려야 한다. 걸리지 않으면 "0건"은 아무것도 재지 못한 것이다.
// - 페이지 스크립트 자리의 `fetch` 에는 `no-restricted-globals` 가 걸리지 않아야 한다(예외가 그 경로에만 산다는 갈래).
// - `node_modules` 안에 둔 파일은 결과에 없어야 한다(라이브러리 안의 호출이 판정 범위 밖이라는 갈래).
// 하나라도 어긋나면 종료 코드 1. 프로브의 코드에 걸린 규칙이 있으면 그것은 측정 결과이고 종료 코드는 0 이다.
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { copyFileSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const REPO = process.argv[2] ?? join(ROOT, "..", "..", "..", "..");
const STAGE = join(ROOT, "out", "lint");
const WEB = join(STAGE, "web");
const PORTAL = join(WEB, "apps", "portal");

/** 판정자에게 보이는 프로브의 파일(`apps/portal/` 아래의 경로). */
const PROBE_FILES = [
  "server/oidc/contract.ts",
  "server/oidc/openid-client.ts",
  "server/oidc/oauth4webapi.ts",
  "server/oidc/hand.ts",
  "server/oidc/node-fetch.ts",
  "testing/fake-idp.ts",
  "testing/fake-idp-provider.ts",
  "testing/browser.ts",
  "testing/round.ts",
];

const PLANTED_FILE = "server/oidc/planted.ts";
// 줄 번호가 기대에 든다. 줄을 옮기면 EXPECTED_PLANTED 도 옮긴다.
const PLANTED = `// 일부러 심은 위반이다(lint.mjs 의 양성 대조). 판정자가 이 폴더의 파일을 실제로 보고 규칙을 거는지 확인한다.
export async function planted(value: unknown): Promise<string> {
  const forced = value as string;
  const loose: any = value;
  const maybe: string | undefined = forced.length > 0 ? forced : undefined;
  const direct = await fetch("http://127.0.0.1/");
  const viaGlobal = await globalThis.fetch("http://127.0.0.1/");
  const handedOver: unknown = fetch;
  type Fetcher = typeof fetch;
  const typed: Fetcher | undefined = undefined;
  return [maybe!, String(loose), direct.status, viaGlobal.status, handedOver, typed].join(" ");
}
`;
const EXPECTED_PLANTED = [
  [3, "@typescript-eslint/consistent-type-assertions"],
  [4, "@typescript-eslint/no-explicit-any"],
  [6, "no-restricted-globals"],
  [7, "no-restricted-properties"],
  [8, "no-restricted-globals"],
  [11, "@typescript-eslint/no-non-null-assertion"],
];
/** 기대에 넣지 않고 결과로만 적는 줄. 타입 자리의 `typeof fetch` 가 걸리는지는 미리 알지 못했다. */
const OBSERVED_PLANTED_LINES = [9];

const PAGE_SCRIPT_FILE = "browser/portal.ts";
const PAGE_SCRIPT = `// 페이지 스크립트 자리다(lint.mjs 의 갈래). 판정자 설정이 이 경로에서만 전역 fetch 를 푼다.
export async function ping(): Promise<number> {
  const response = await fetch("/portal/health");
  return response.status;
}
`;

// 라이브러리 자리의 갈래. 앱 폴더 안 `node_modules` 에 전역 fetch 를 부르는 `.ts` 를 둔다. 판정자가 이 파일을 보지 않아야
// "라이브러리 안의 fetch 호출은 판정 범위 밖"이 선다. 같은 호출을 한 planted.ts 가 걸리는 것이 양성 대조다.
const LIBRARY_FILE = "node_modules/planted-lib/index.ts";
const LIBRARY = `export async function ping(): Promise<number> {
  const response = await fetch("http://127.0.0.1/");
  return response.status;
}
`;

const sha256 = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");

function stage() {
  rmSync(STAGE, { recursive: true, force: true, maxRetries: 5 });
  for (const folder of ["server/oidc", "testing", "browser", "node_modules/planted-lib"]) mkdirSync(join(PORTAL, ...folder.split("/")), { recursive: true });
  writeFileSync(join(PORTAL, ...LIBRARY_FILE.split("/")), LIBRARY);
  copyFileSync(join(REPO, ".gitignore"), join(STAGE, ".gitignore"));
  copyFileSync(join(REPO, "web", "eslint.config.mjs"), join(WEB, "eslint.config.mjs"));
  copyFileSync(join(REPO, "web", "tsconfig.base.json"), join(WEB, "tsconfig.base.json"));
  copyFileSync(join(REPO, "web", "apps", "portal", "tsconfig.json"), join(PORTAL, "tsconfig.json"));
  for (const path of PROBE_FILES) copyFileSync(join(ROOT, "apps", "portal", ...path.split("/")), join(PORTAL, ...path.split("/")));
  writeFileSync(join(PORTAL, ...PLANTED_FILE.split("/")), PLANTED);
  writeFileSync(join(PORTAL, ...PAGE_SCRIPT_FILE.split("/")), PAGE_SCRIPT);
}

function main() {
  stage();
  const run = spawnSync(
    process.execPath,
    [join(ROOT, "node_modules", "eslint", "bin", "eslint.js"), "--max-warnings", "0", "--format", "json", "apps/portal"],
    { cwd: WEB, encoding: "utf8", maxBuffer: 64 * 1024 * 1024 },
  );
  writeFileSync(join(STAGE, "eslint.stderr.log"), run.stderr ?? "");
  let results;
  try {
    results = JSON.parse(run.stdout);
  } catch {
    writeFileSync(join(STAGE, "eslint.stdout.log"), run.stdout ?? "");
    console.log(JSON.stringify({ probe: "lint", notMeasured: ["ESLint 의 출력이 JSON 이 아니다"], eslintExit: run.status }));
    console.error(run.stderr);
    process.exit(1);
  }
  writeFileSync(join(STAGE, "eslint.json"), JSON.stringify(results, null, 2));

  const underPortal = (filePath) => filePath.replaceAll("\\", "/").split("/apps/portal/").pop();
  const byName = new Map(results.map((r) => [underPortal(r.filePath), r]));
  const notMeasured = [];
  for (const name of [...PROBE_FILES, PLANTED_FILE, PAGE_SCRIPT_FILE]) {
    const result = byName.get(name);
    if (result === undefined) {
      notMeasured.push(`${name} 을 판정자가 보지 않았다`);
    } else if (result.messages.some((m) => m.fatal === true || m.ruleId === null)) {
      notMeasured.push(`${name} 에 파싱 오류가 있다: ${JSON.stringify(result.messages.filter((m) => m.ruleId === null))}`);
    }
  }
  const planted = (byName.get(PLANTED_FILE)?.messages ?? []).map((m) => ({ line: m.line, ruleId: m.ruleId, message: m.message }));
  for (const [line, rule] of EXPECTED_PLANTED) {
    if (!planted.some((m) => m.line === line && m.ruleId === rule)) notMeasured.push(`심은 위반 ${String(line)}행에서 ${rule} 가 걸리지 않았다`);
  }
  const pageScript = (byName.get(PAGE_SCRIPT_FILE)?.messages ?? []).map((m) => ({ line: m.line, ruleId: m.ruleId, message: m.message }));
  if (pageScript.some((m) => m.ruleId === "no-restricted-globals")) notMeasured.push("페이지 스크립트 자리의 fetch 에 no-restricted-globals 가 걸렸다");
  const libraryFilesSeen = results.map((r) => r.filePath.replaceAll("\\", "/")).filter((path) => path.includes("/node_modules/"));
  if (libraryFilesSeen.length > 0) notMeasured.push(`판정자가 node_modules 안의 파일을 봤다: ${libraryFilesSeen.join(", ")}`);

  const files = {};
  for (const name of PROBE_FILES) {
    const result = byName.get(name);
    files[name] = {
      errors: result?.errorCount ?? null,
      warnings: result?.warningCount ?? null,
      messages: (result?.messages ?? []).map((m) => ({ ruleId: m.ruleId, line: m.line, message: m.message })),
    };
  }
  const summary = {
    probe: "lint",
    repo: REPO,
    configSha256: sha256(join(WEB, "eslint.config.mjs")),
    eslintExit: run.status,
    notMeasured,
    planted,
    plantedObservedLines: planted.filter((m) => OBSERVED_PLANTED_LINES.includes(m.line)),
    pageScript,
    filesJudged: results.length,
    libraryFilesSeen,
    files,
  };
  writeFileSync(join(STAGE, "summary.json"), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary));
  if (notMeasured.length > 0) process.exit(1);
}

main();
