// 타입 검사 프로브(B2). 제한을 건 컴포넌트가 저장소와 같은 strict 옵션(tsconfig.base.json 은 web/tsconfig.base.json 의
// 복사)에서 `tsc --noEmit` 을 지나는지 본다.
//
// 돌리기: node probe/typecheck.mjs
// 산출물: out/typecheck/summary.json, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 측정이 아닌 회차(.claude/rules/probes.md): 종료 코드 0 만으로 맺지 않는다.
// - 본 검사(`tsc --noEmit -p tsconfig.json`)가 0 이 아닌 코드로 끝나면 어긋난 것이다.
// - tsc 가 실제로 본 파일 목록(--listFilesOnly)에 두 컴포넌트와 두 라이브러리의 타입 선언, 그리고 합친 시제품
//   (`AnswerMarkdown.tsx` 와 `lib/answer-markdown/`, `lib/link-url.ts`)의 파일이 모두 있어야 한다.
// - 양성 대조: 같은 옵션을 물려받은 무대(out/typecheck/control)에 심은 오류 둘이 실제로 걸려야 한다.
//   `noUncheckedIndexedAccess` 가 살아 있어야 나는 TS2322(indexed.ts)와, 허용 목록 switch 에서 갈래 하나를 지운
//   컴포넌트 사본의 TS2322(never 대입. 라이브러리가 규칙 종류를 더했을 때 타입 검사가 멈춘다는 주장의 근거)다.
//   첫 시도는 `default` 없이 TS2366("끝에 return 이 없다")을 기대했고 걸리지 않았다. 반환 타입 ReactNode 가
//   undefined 를 품기 때문이다. 그래서 컴포넌트에 never 대입을 넣었다.
// 어긋나면 종료 코드 1.
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "out", "typecheck");
const TSC = join(ROOT, "node_modules", "typescript", "bin", "tsc");
const tsc = (...args) => spawnSync(process.execPath, [TSC, ...args], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });

rmSync(OUT, { recursive: true, force: true });
mkdirSync(join(OUT, "control"), { recursive: true });

const main = tsc("--noEmit", "-p", join(ROOT, "tsconfig.json"));
const listed = tsc("--noEmit", "--listFilesOnly", "-p", join(ROOT, "tsconfig.json")).stdout.replaceAll("\\", "/");
const mustSee = [
  "apps/widget/components/molecules/MarkdownReact.tsx",
  "apps/widget/components/molecules/MarkdownJsx.tsx",
  "apps/widget/lib/safe-url.ts",
  // 합친 시제품(2026-11-11 에 더했다).
  "apps/widget/components/molecules/AnswerMarkdown.tsx",
  "apps/widget/lib/link-url.ts",
  "apps/widget/lib/answer-markdown/index.ts",
  "apps/widget/lib/answer-markdown/tree.ts",
  "apps/widget/lib/answer-markdown/soft-breaks.ts",
  "apps/widget/lib/answer-markdown/literal-marks.ts",
  "apps/widget/lib/answer-markdown/literal-marks-syntax.ts",
  "apps/widget/lib/answer-markdown/cjk-emphasis.ts",
  "apps/widget/lib/answer-markdown/citations.ts",
  "apps/widget/lib/answer-markdown/sources.ts",
  "apps/widget/lib/answer-markdown/footnotes.ts",
  "apps/widget/lib/answer-markdown/task-marks.ts",
  "node_modules/react-markdown/index.d.ts",
  "node_modules/remark-gfm/index.d.ts",
  "node_modules/markdown-to-jsx/dist/react.d.ts",
];
const notSeen = mustSee.filter((piece) => !listed.includes(piece));

// 양성 대조 1: noUncheckedIndexedAccess.
writeFileSync(
  join(OUT, "control", "indexed.ts"),
  "const items: string[] = [];\nexport const first: string = items[0];\n",
);
// 양성 대조 2: 허용 목록 switch 에서 `case RuleType.gfmTask` 갈래를 지운 사본.
const source = readFileSync(join(ROOT, "apps", "widget", "components", "molecules", "MarkdownJsx.tsx"), "utf8");
const removed = source.replace(
  /    case RuleType\.gfmTask:\r?\n      return <Fragment key=\{state\.key\}>\{node\.completed \? "\[x\]" : "\[ \]"\}<\/Fragment>;\r?\n/,
  "",
);
const controlWritten = removed !== source;
writeFileSync(
  join(OUT, "control", "MarkdownJsxMissingCase.tsx"),
  removed.replace('"../../lib/safe-url"', '"../../../apps/widget/lib/safe-url"'),
);
writeFileSync(
  join(OUT, "control", "tsconfig.json"),
  `${JSON.stringify({ extends: "../../../tsconfig.json", include: ["*.ts", "*.tsx"], exclude: [] }, null, 2)}\n`,
);
const control = tsc("--noEmit", "-p", join(OUT, "control", "tsconfig.json"));
const controlOutput = `${control.stdout}${control.stderr}`;
const controlCodes = [...new Set([...controlOutput.matchAll(/error (TS\d+)/g)].map((m) => m[1]))].sort();

const problems = [];
// 본 검사가 오류로 끝나면 종료 코드 1이다(2026-11-11 PR 직전 리뷰가 짚어 더했다. 그 전 판은 요약의 `exit` 를 사람이 읽어야 했다).
if (main.status !== 0) problems.push(`tsc --noEmit 이 ${String(main.status)}로 끝났다(요약의 errors)`);
if (notSeen.length > 0) problems.push(`tsc 가 보지 않은 파일: ${notSeen.join(", ")}`);
if (!controlWritten) problems.push("대조 사본에서 갈래를 지우지 못했다(컴포넌트의 글이 바뀌었다)");
if (!/indexed\.ts.*TS2322/.test(controlOutput)) problems.push("noUncheckedIndexedAccess 대조(TS2322)가 걸리지 않았다");
if (!/MarkdownJsxMissingCase\.tsx.*TS2322/.test(controlOutput)) problems.push("빠진 갈래 대조(TS2322)가 걸리지 않았다");

const summary = {
  probe: "typecheck",
  typescript: JSON.parse(readFileSync(join(ROOT, "node_modules", "typescript", "package.json"), "utf8")).version,
  exit: main.status,
  errors: `${main.stdout}${main.stderr}`.trim().split(/\r?\n/).filter((line) => line !== ""),
  filesSeen: listed.trim().split(/\r?\n/).length,
  control: { exit: control.status, codes: controlCodes, lines: controlOutput.trim().split(/\r?\n/).slice(0, 6) },
  notMeasured: problems,
};
writeFileSync(join(OUT, "summary.json"), JSON.stringify(summary, null, 2));
console.log(JSON.stringify(summary));
if (problems.length > 0) process.exit(1);
