// 티켓 04(관리 화면 앱)의 변이 32. 둘을 잰다.
//
// 1. 01 이 경로와 무관하게 쓴 규칙이 앱의 실제 자리에서 빨간가(`lint`). 서버 파일 넷, "use server", 전역 fetch,
//    dangerouslySetInnerHTML, app/ 의 import, 층 경계, 그리고 01 이 재지 못한 타입 기반 규칙이다. 위반을 실제 앱의
//    자리에 쓰거나 실제 파일에 넣고, verify 의 린트 명령(`eslint --max-warnings 0`)을 JSON 으로 돌려 그 파일에서 기대한
//    규칙 ID 가 보고됐는지 본다. 파싱 오류(규칙 ID 없음)가 섞이면 빨강이 아니라 오류다. 임시 트리가 아니라 Next 가
//    읽는 tsconfig 와 실제 node_modules 위에서 잰다. 그 자리에 없는 파일은 lintText 로 잴 수 없어(프로젝트 서비스가
//    찾지 못한다) 커밋하는 테스트가 아니라 여기 둔다.
// 2. 이 티켓의 테스트가 무엇을 재는가(`vitest`). 루프백 판정, 시작 래퍼, 설정의 상류, Next 판 고정, 판정자 설정(app/ 의
//    import, 빌드 산출물, 추적 파일 가드, .gitignore 의 앵커)의 변이다.
//
// 규약은 `tools/mutate.py`·`api_client_mutations.mjs` 와 같다. 원문이 파일에 정확히 한 번 있는지 먼저 보고(하나라도
// 틀리면 아무것도 쓰지 않는다), 변이 없이 명령이 초록인지 기준선을 본 뒤, 변이마다 원래 바이트를 쥐고 넣어 돌리고
// finally 에서 그 바이트를 쓰며 새로 만든 파일은 지운다. Vitest 는 실패한 테스트가 셀 때만 빨강이다.
//
// 래퍼가 판정하고도 거부하지 않는 변이는 인자 테스트(start.test.ts)로만 잰다. 프로세스 테스트(start.spawn.test.ts)가
// 그것을 잡으려면 next dev 가 0.0.0.0 에 떠야 하고, 시간 제한에 걸려 래퍼가 죽어도 next 의 자식 서버가 남는다.
//
// 쓰는 법: node .scratch/web-admin/probes/admin_app_mutations.mjs [이름 ...]   (저장소 루트에서. 명령은 web/ 에서 돈다)
// 네트워크를 타지 않는다. 약 5분. 종료 코드: 모두 기대대로면 0, 어긋나거나 기준선이 초록이 아니면 1, 원문이 틀리거나
// 없는 이름을 주면 2.

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, rmdirSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";

const WEB = join(process.cwd(), "web");
const VITEST = (file) => `pnpm exec vitest run ${file}`;
const LOOPBACK_TEST = VITEST("apps/admin/tools/loopback.test.ts");
const START_TEST = VITEST("apps/admin/tools/start.test.ts");
const SPAWN_TEST = VITEST("apps/admin/tools/start.spawn.test.ts");
const CONFIG_TEST = VITEST("apps/admin/next.config.test.ts");
const JUDGE_TEST = VITEST("eslint.config.test.ts");
const LOOPBACK = "apps/admin/tools/loopback.ts";
const START = "apps/admin/tools/start.ts";
const CONFIG = "apps/admin/next.config.ts";
const JUDGE = "eslint.config.mjs";
const HOME = "apps/admin/components/pages/HomePage.tsx";
const PAGE = "apps/admin/app/page.tsx";
const SERVER_FILE = "export const 값 = 1;\n";
const RESTRICTED_SYNTAX = "no-restricted-syntax";
const BOUNDARIES = "boundaries/dependencies";

const MUTATIONS = [
  // ---- 1. 실제 자리 ----
  {
    name: "app/ 아래의 라우트 핸들러",
    create: { "apps/admin/app/api/[...path]/route.ts": SERVER_FILE },
    lint: "apps/admin/app/api/[...path]/route.ts",
    rule: RESTRICTED_SYNTAX,
  },
  {
    name: "앱 뿌리의 middleware",
    create: { "apps/admin/middleware.ts": SERVER_FILE },
    lint: "apps/admin/middleware.ts",
    rule: RESTRICTED_SYNTAX,
  },
  {
    name: "앱 뿌리의 proxy",
    create: { "apps/admin/proxy.ts": SERVER_FILE },
    lint: "apps/admin/proxy.ts",
    rule: RESTRICTED_SYNTAX,
  },
  {
    name: "앱 뿌리의 instrumentation",
    create: { "apps/admin/instrumentation.ts": SERVER_FILE },
    lint: "apps/admin/instrumentation.ts",
    rule: RESTRICTED_SYNTAX,
  },
  {
    name: '페이지의 "use server"',
    file: HOME,
    old: "// 자리표시.",
    new: '"use server";\n\n// 자리표시.',
    lint: HOME,
    rule: RESTRICTED_SYNTAX,
  },
  {
    name: "페이지의 전역 fetch",
    file: HOME,
    old: "export function HomePage() {",
    new: 'export const 부른다 = (): Promise<Response> => fetch("/api/plugins");\n\nexport function HomePage() {',
    lint: HOME,
    rule: "no-restricted-globals",
  },
  {
    name: "페이지의 dangerouslySetInnerHTML",
    file: HOME,
    old: "<h1>관리 화면</h1>",
    new: '<h1 dangerouslySetInnerHTML={{ __html: "관리 화면" }} />',
    lint: HOME,
    rule: RESTRICTED_SYNTAX,
  },
  {
    name: "app/ 이 pages·templates 밖의 앱 파일을 import",
    file: PAGE,
    old: 'import { HomePage } from "../components/pages/HomePage";',
    new: 'import { HomePage } from "../components/pages/HomePage";\nimport { DEFAULT_HOST } from "../tools/loopback.ts";\n\nexport const 호스트 = DEFAULT_HOST;',
    lint: PAGE,
    rule: BOUNDARIES,
  },
  {
    name: "atoms 가 pages 를 import",
    create: {
      "apps/admin/components/atoms/Title.tsx":
        'import { HomePage } from "../pages/HomePage";\n\nexport const 제목 = HomePage;\n',
    },
    lint: "apps/admin/components/atoms/Title.tsx",
    rule: BOUNDARIES,
  },
  {
    name: "타입 기반 규칙이 앱의 실제 파일에서 돈다",
    file: HOME,
    old: "export function HomePage() {",
    new: 'export const 수: number = JSON.parse("1");\n\nexport function HomePage() {',
    lint: HOME,
    rule: "@typescript-eslint/no-unsafe-assignment",
  },

  // ---- 2. 이 티켓의 테스트 ----
  {
    name: "localhost 를 루프백으로 받는다",
    file: LOOPBACK,
    old: 'const LOOPBACK_HOSTS: readonly string[] = ["127.0.0.1", "::1"];',
    new: 'const LOOPBACK_HOSTS: readonly string[] = ["127.0.0.1", "::1", "localhost"];',
    command: LOOPBACK_TEST,
  },
  {
    name: "상류가 ::1 도 받는다",
    file: LOOPBACK,
    old: "  if (host === UPSTREAM_HOST) {",
    new: "  if (isLoopback(host)) {",
    command: LOOPBACK_TEST,
  },
  {
    name: "상류 호스트의 대괄호를 벗기지 않는다",
    file: LOOPBACK,
    old: '  const host = url.hostname.replace(/^\\[(.*)\\]$/, "$1");',
    new: "  const host = url.hostname;",
    command: LOOPBACK_TEST,
  },
  {
    name: "상류의 경로·질의·계정을 조용히 버린다",
    file: LOOPBACK,
    old: '  if (url === null || url.protocol !== "http:" || url.href !== `${url.origin}/`) {',
    new: '  if (url === null || url.protocol !== "http:") {',
    command: LOOPBACK_TEST,
  },
  {
    name: "상류가 https 도 받는다",
    file: LOOPBACK,
    old: '  if (url === null || url.protocol !== "http:" || url.href !== `${url.origin}/`) {',
    new: "  if (url === null || url.href !== `${url.origin}/`) {",
    command: LOOPBACK_TEST,
  },
  {
    name: "상류 형식의 진단이 받은 값을 싣는다",
    file: LOOPBACK,
    old: "경로, 질의, 계정은 받지 않는다.`;",
    new: "경로, 질의, 계정은 받지 않는다. 받은 값: ${value}`;",
    command: LOOPBACK_TEST,
  },
  {
    name: "래퍼의 기본 호스트가 next 의 기본값이다",
    file: START,
    old: "  const host = values.hostname ?? DEFAULT_HOST;",
    new: '  const host = values.hostname ?? "0.0.0.0";',
    command: START_TEST,
  },
  {
    name: "래퍼가 모르는 인자를 받는다",
    file: START,
    old: "      strict: true,",
    new: "      strict: false,",
    command: START_TEST,
  },
  {
    name: "래퍼가 판정하고도 거부하지 않는다",
    file: START,
    old: "  if (problem !== null) {\n    return { problem };\n  }",
    new: "",
    command: START_TEST,
  },
  {
    name: "래퍼가 거부하고 0 으로 끝난다",
    file: START,
    old: "    process.exitCode = 1;",
    new: "    process.exitCode = 0;",
    command: SPAWN_TEST,
  },
  {
    name: "래퍼의 진단이 표준 출력으로 간다",
    file: START,
    old: "    console.error(command.problem);",
    new: "    console.log(command.problem);",
    command: SPAWN_TEST,
  },
  {
    name: "래퍼의 SSH 안내가 PORT 를 보지 않는다",
    file: START,
    old: '  const command = nextCommand(process.argv.slice(2), process.env["PORT"] ?? "3000");',
    new: '  const command = nextCommand(process.argv.slice(2), "3000");',
    command: SPAWN_TEST,
  },
  {
    name: "상류 호스트를 URL 의 정규화 없이 원문에서 읽는다",
    file: LOOPBACK,
    old: '  const host = url.hostname.replace(/^\\[(.*)\\]$/, "$1");',
    new: '  const host = value.slice("http://".length).replace(/:\\d+\\/?$/, "").replace(/^\\[(.*)\\]$/, "$1");',
    command: LOOPBACK_TEST,
  },
  {
    name: "Next 판 고정이 설치본과 어긋난다",
    file: "apps/admin/tools/next-version.test.ts",
    old: 'const MEASURED = "16.3.6";',
    new: 'const MEASURED = "16.3.7";',
    command: VITEST("apps/admin/tools/next-version.test.ts"),
  },
  {
    name: "설정 파일이 상류를 판정하지 않는다",
    file: CONFIG,
    old: "if (problem !== null) {\n  throw new Error(problem);\n}\n",
    new: "",
    command: CONFIG_TEST,
  },
  {
    name: "빈 상류 입력을 기본값으로 읽지 않는다",
    file: CONFIG,
    old: 'const upstream = given === undefined || given === "" ? DEFAULT_UPSTREAM : given;',
    new: "const upstream = given ?? DEFAULT_UPSTREAM;",
    command: CONFIG_TEST,
  },
  {
    name: "목적지가 출처가 아니라 받은 값 그대로다",
    file: CONFIG,
    old: "destination: `${origin}/:path*`",
    new: "destination: `${upstream}/:path*`",
    command: CONFIG_TEST,
  },
  {
    name: "app/ 의 로컬 선택자를 좁히지 않는다",
    file: JUDGE,
    old: '                    module: { origin: "local" },\n',
    new: "",
    command: JUDGE_TEST,
  },
  {
    name: "app/ 이 노드 내장 모듈을 import 해도 된다",
    file: JUDGE,
    old: '{ module: { origin: "{external,core}", source: "!{next,react}" } },',
    new: '{ module: { origin: "external", source: "!{next,react}" } },',
    command: JUDGE_TEST,
  },
  {
    name: "판정자가 .gitignore 를 읽지 않는다",
    file: JUDGE,
    old: '  includeIgnoreFile(GITIGNORE, { gitignoreResolution: true, name: ".gitignore 가 무시하는 것" }),\n',
    new: "",
    command: JUDGE_TEST,
  },
  {
    name: ".gitignore 의 traces/ 가 뿌리에 앵커되지 않는다",
    file: "../.gitignore",
    old: "\n/traces/\n",
    new: "\ntraces/\n",
    command: JUDGE_TEST,
  },
  {
    name: ".gitignore 한 줄이 추적하는 소스를 판정에서 뺀다",
    file: "../.gitignore",
    old: "next-env.d.ts\n",
    new: "next-env.d.ts\nweb/tools/\n",
    command: JUDGE_TEST,
  },
];

function vitest(command) {
  const result = spawnSync(command, { cwd: WEB, shell: true, encoding: "utf-8" });
  if (result.status === 0) {
    return "green";
  }
  return /Tests\s+\d+ failed/.test(`${result.stdout}${result.stderr}`)
    ? "red"
    : `error(${result.status})`;
}

/** verify 의 린트 명령으로 한 파일을 돌려 기대한 규칙이 보고됐는가. 파싱 오류가 섞이면 오류다. */
function lint(path, rule) {
  const result = spawnSync(
    `pnpm exec eslint --max-warnings 0 -f json "${path}"`,
    { cwd: WEB, shell: true, encoding: "utf-8" },
  );
  const start = result.stdout.indexOf("[");
  if (start === -1) {
    return `error(${result.status}: JSON 없음)`;
  }
  const [report] = JSON.parse(result.stdout.slice(start));
  const found = (report?.messages ?? []).map((message) => message.ruleId);
  if (found.includes(null)) {
    return "error(파싱 오류)";
  }
  if (found.length === 0) {
    return "green";
  }
  return found.includes(rule) ? "red" : `error(다른 규칙: ${found.join(", ")})`;
}

function judge(mutation) {
  return mutation.lint === undefined ? vitest(mutation.command) : lint(mutation.lint, mutation.rule);
}

const selected = process.argv.slice(2);
const unknown = selected.filter((name) => !MUTATIONS.some((m) => m.name === name));
if (unknown.length > 0) {
  console.log(`없는 변이 이름: ${unknown.join(", ")}`);
  process.exit(2);
}
const chosen = selected.length > 0 ? MUTATIONS.filter((m) => selected.includes(m.name)) : MUTATIONS;

for (const mutation of chosen) {
  if (mutation.file !== undefined) {
    const text = readFileSync(join(WEB, mutation.file), "utf-8");
    if (text.split(mutation.old).length !== 2) {
      console.log(`원문이 ${mutation.file} 에 정확히 한 번 있지 않다: ${mutation.name}`);
      process.exit(2);
    }
  }
  for (const path of Object.keys(mutation.create ?? {})) {
    if (existsSync(join(WEB, path))) {
      console.log(`만들 파일이 이미 있다: ${path}`);
      process.exit(2);
    }
  }
}

// 기준선. 테스트 명령은 초록, 실제 자리의 린트는 앱 전체가 깨끗하다.
const baselines = [...new Set(chosen.filter((m) => m.command).map((m) => m.command))];
for (const command of baselines) {
  const status = vitest(command);
  console.log(`기준선 ${status}: ${command}`);
  if (status !== "green") {
    process.exit(1);
  }
}
if (chosen.some((m) => m.lint !== undefined)) {
  const clean = spawnSync("pnpm exec eslint --max-warnings 0 apps/admin", { cwd: WEB, shell: true });
  console.log(`기준선 ${clean.status === 0 ? "green" : "red"}: eslint apps/admin`);
  if (clean.status !== 0) {
    process.exit(1);
  }
}

let mismatches = 0;
for (const mutation of chosen) {
  const originals =
    mutation.file === undefined
      ? new Map()
      : new Map([[mutation.file, readFileSync(join(WEB, mutation.file))]]);
  const created = Object.keys(mutation.create ?? {});
  let status = "";
  try {
    for (const [path, source] of Object.entries(mutation.create ?? {})) {
      mkdirSync(dirname(join(WEB, path)), { recursive: true });
      writeFileSync(join(WEB, path), source);
    }
    if (mutation.file !== undefined) {
      const text = readFileSync(join(WEB, mutation.file), "utf-8");
      writeFileSync(join(WEB, mutation.file), text.replace(mutation.old, mutation.new));
    }
    status = judge(mutation);
  } finally {
    for (const [file, bytes] of originals) {
      writeFileSync(join(WEB, file), bytes);
    }
    for (const path of created) {
      rmSync(join(WEB, path), { force: true });
    }
    // 만들며 생긴 빈 디렉터리(app/api/[...path] 같은)를 앱 폴더까지 거슬러 지운다.
    for (const path of created) {
      let directory = dirname(join(WEB, path));
      while (relative(join(WEB, "apps", "admin"), directory).split(sep)[0] !== "" && existsSync(directory)) {
        try {
          rmdirSync(directory);
        } catch {
          break;
        }
        directory = dirname(directory);
      }
    }
  }
  const ok = status === "red";
  if (!ok) {
    mismatches += 1;
  }
  console.log(`${ok ? "기대대로" : "어긋남"} ${status} (기대 red): ${mutation.name}`);
}
process.exit(mismatches === 0 ? 0 : 1);
