// 린트 프로브. 저장소의 판정자 설정(web/eslint.config.mjs)을 글자 그대로 옮겨 와 제한을 건 컴포넌트에 건다.
//
// 돌리기: node probe/lint.mjs [저장소 경로]
//   저장소 경로를 주지 않으면 이 프로브가 든 저장소의 뿌리(이 폴더에서 네 단계 위)다. 저장소 밖 임시 폴더에서
//   지어 돌릴 때는 기본값이 그 워크트리의 절대 경로였고, 저장소로 옮기며 바꿨다.
// 산출물: out/lint/(무대), out/lint/eslint.json, out/lint/summary.json, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 무대(out/lint/)는 저장소의 배치를 흉내 낸다. 판정자 설정은 자기 자리에서 `../.gitignore` 를 읽고, 층 경계는 경로의
// 끝(`components/molecules/…`, `lib/…`)으로 요소를 가른다.
//   out/lint/.gitignore                         ← 저장소 뿌리의 .gitignore (복사)
//   out/lint/web/eslint.config.mjs              ← 저장소의 web/eslint.config.mjs (복사, 고치지 않는다)
//   out/lint/web/tsconfig.base.json             ← 저장소의 web/tsconfig.base.json (복사)
//   out/lint/web/apps/widget/tsconfig.json      ← 위젯의 tsconfig 에서 Next 플러그인과 Next 산출물 include 만 뺀 것
//   out/lint/web/apps/widget/components/molecules/{MarkdownReact,MarkdownJsx}.tsx, lib/safe-url.ts  ← 프로브의 컴포넌트 (복사)
//   out/lint/web/apps/widget/components/molecules/AnswerMarkdown.tsx, lib/link-url.ts, lib/answer-markdown/*.ts
//                                               ← 합친 시제품 (복사, 2026-11-11 에 더했다. 목록은 COMPONENT_FILES)
//   out/lint/web/apps/widget/components/molecules/Planted.tsx  ← 일부러 심은 위반(양성 대조)
// ESLint, typescript-eslint, eslint-plugin-boundaries 는 저장소 잠금 파일과 같은 판(10.11.0, 8.70.1, 7.2.0)을 프로브에
// 설치한 것이고, 무대에서 위로 올라가며 이 프로브 폴더의 node_modules 로 풀린다.
//
// 측정이 아닌 회차(.claude/rules/probes.md)
// - ESLint 의 결과에 부품 파일 전부(COMPONENT_FILES)와 심은 파일이 있어야 한다(판정자가 실제로 그 파일을 봤다).
// - 어느 파일에도 파싱 오류(fatal)가 없어야 한다. 어느 tsconfig 에도 들지 않는 파일은 규칙이 아니라 파싱 오류로 빨개진다.
// - 심은 위반에서 기대한 규칙 ID 넷이 모두 걸려야 한다. 걸리지 않으면 "0건"은 아무것도 재지 못한 것이다.
// 하나라도 어긋나면 종료 코드 1. 컴포넌트에 걸린 규칙이 있으면 그것은 측정 결과이고 종료 코드는 0 이다.
import { spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { copyFileSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const REPO = process.argv[2] ?? join(ROOT, "..", "..", "..", "..");
const STAGE = join(ROOT, "out", "lint");
const WEB = join(STAGE, "web");
const WIDGET = join(WEB, "apps", "widget");

const PLANTED = `// 일부러 심은 위반이다(lint.mjs 의 양성 대조). 판정자가 이 폴더의 파일을 실제로 보고 규칙을 거는지 확인한다.
export function Planted({ html, value }: { readonly html: string; readonly value: unknown }) {
  const forced = value as string;
  const loose: any = value;
  const maybe: string | undefined = html.length > 0 ? html : undefined;
  return (
    <div>
      <p dangerouslySetInnerHTML={{ __html: html }} />
      <p>{forced}</p>
      <p>{String(loose)}</p>
      <p>{maybe!}</p>
    </div>
  );
}
`;
const EXPECTED_PLANTED_RULES = [
  "@typescript-eslint/consistent-type-assertions",
  "@typescript-eslint/no-explicit-any",
  "@typescript-eslint/no-non-null-assertion",
  "no-restricted-syntax",
];

const WIDGET_TSCONFIG = {
  extends: "../../tsconfig.base.json",
  compilerOptions: {
    target: "es2024",
    lib: ["es2024", "dom", "dom.iterable"],
    module: "esnext",
    moduleResolution: "bundler",
    jsx: "react-jsx",
    allowImportingTsExtensions: true,
    types: ["node"],
  },
  include: ["**/*.ts", "**/*.tsx"],
  exclude: ["node_modules"],
};

const sha256 = (path) => createHash("sha256").update(readFileSync(path)).digest("hex");

function stage() {
  rmSync(STAGE, { recursive: true, force: true });
  mkdirSync(join(WIDGET, "components", "molecules"), { recursive: true });
  mkdirSync(join(WIDGET, "lib"), { recursive: true });
  copyFileSync(join(REPO, ".gitignore"), join(STAGE, ".gitignore"));
  copyFileSync(join(REPO, "web", "eslint.config.mjs"), join(WEB, "eslint.config.mjs"));
  copyFileSync(join(REPO, "web", "tsconfig.base.json"), join(WEB, "tsconfig.base.json"));
  writeFileSync(join(WIDGET, "tsconfig.json"), `${JSON.stringify(WIDGET_TSCONFIG, null, 2)}\n`);
  mkdirSync(join(WIDGET, "lib", "answer-markdown"), { recursive: true });
  for (const path of COMPONENT_FILES) {
    copyFileSync(join(ROOT, "apps", "widget", ...path.split("/")), join(WIDGET, ...path.split("/")));
  }
  writeFileSync(join(WIDGET, "components", "molecules", "Planted.tsx"), PLANTED);
}

/** 판정자에게 보이는 프로브의 부품 파일(`apps/widget/` 아래의 경로). 뒤의 열은 2026-11-11 에 더한 합친 시제품이다. */
const COMPONENT_FILES = [
  "components/molecules/MarkdownReact.tsx",
  "components/molecules/MarkdownJsx.tsx",
  "lib/safe-url.ts",
  "components/molecules/AnswerMarkdown.tsx",
  "lib/link-url.ts",
  "lib/answer-markdown/index.ts",
  "lib/answer-markdown/tree.ts",
  "lib/answer-markdown/soft-breaks.ts",
  "lib/answer-markdown/literal-marks.ts",
  "lib/answer-markdown/literal-marks-syntax.ts",
  "lib/answer-markdown/cjk-emphasis.ts",
  "lib/answer-markdown/citations.ts",
  "lib/answer-markdown/sources.ts",
  "lib/answer-markdown/footnotes.ts",
  "lib/answer-markdown/task-marks.ts",
];
const PLANTED_FILE = "components/molecules/Planted.tsx";

function main() {
  stage();
  const run = spawnSync(
    process.execPath,
    [join(ROOT, "node_modules", "eslint", "bin", "eslint.js"), "--max-warnings", "0", "--format", "json", "apps/widget"],
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

  // 결과는 `apps/widget/` 아래의 경로로 찾는다(같은 이름의 파일이 폴더마다 있을 수 있다).
  const underWidget = (filePath) => filePath.replaceAll("\\", "/").split("/apps/widget/").pop();
  const byName = new Map(results.map((r) => [underWidget(r.filePath), r]));
  const notMeasured = [];
  for (const name of [...COMPONENT_FILES, PLANTED_FILE]) {
    const result = byName.get(name);
    if (result === undefined) {
      notMeasured.push(`${name} 을 판정자가 보지 않았다`);
    } else if (result.messages.some((m) => m.fatal === true || m.ruleId === null)) {
      notMeasured.push(`${name} 에 파싱 오류가 있다: ${JSON.stringify(result.messages.filter((m) => m.ruleId === null))}`);
    }
  }
  const plantedRules = [...new Set((byName.get(PLANTED_FILE)?.messages ?? []).map((m) => m.ruleId))].sort();
  for (const rule of EXPECTED_PLANTED_RULES) {
    if (!plantedRules.includes(rule)) notMeasured.push(`심은 위반에서 ${rule} 가 걸리지 않았다`);
  }

  const files = {};
  for (const name of COMPONENT_FILES) {
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
    plantedRules,
    files,
  };
  writeFileSync(join(STAGE, "summary.json"), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary));
  if (notMeasured.length > 0) process.exit(1);
}

main();
