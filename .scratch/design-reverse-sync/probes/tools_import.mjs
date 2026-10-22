// `web/tools`(루트 tsconfig: `module`·`moduleResolution` 이 `nodenext`, `lib` 가 `es2024` 뿐)의 Node 스크립트가 디자인
// 시스템 패키지(`@agent-os/ui`, `moduleResolution: bundler`, 확장자 없는 상대 import)의 명암비 계산과 짝 표를 부를 수
// 있는지, 실제로 설치한 워크스페이스에서 루트 타입 검사(`tsc --noEmit`)와 `node tools/<파일>.ts` 실행까지 잰다.
//
// 갈래 둘을 같은 커밋의 `web/` 사본 둘에 하나씩 지어 잰다. 두 갈래 모두 루트 `web/package.json` 의 devDependencies 에
// `"@agent-os/ui": "workspace:*"` 를 더하고 패키지의 `exports` 에 새 경로 하나를 더한 뒤 `pnpm install --offline` 한다.
// - `as-is`: 새 경로가 지금의 `src/styles/contrast.ts` 를 그대로 가리킨다. 그 파일은 `"../testing"`·`"../themes"` 를
//   확장자 없이 부른다. 기대: 타입 검사가 그 import 에서 TS2834·TS2835 로 빨갛고, `node` 가 첫 import `"../testing"` 을
//   폴더 import 로 읽어 ERR_UNSUPPORTED_DIR_IMPORT 로 멈춘다(첫 실행의 원본 출력에서 봤다. 그 회차는 표지를
//   ERR_MODULE_NOT_FOUND 로 잘못 골라 측정으로 세지 않았다).
// - `self-contained`: 새 경로가 `src/color/index.ts` 를 가리킨다. 이 파일은 `testing/index.ts` 의 DOM 을 쓰지 않는 앞부분
//   (`contrastRatio`·`composite` 와 도우미, 머리 주석 뒤부터 `SPLIT_BEFORE` 앞까지)과 `contrast.ts` 의 본문(import 두 줄을
//   빼고 `Mode` 를 같은 뜻의 지역 타입으로 둔다)을 이어 붙인 것이라 상대 import 가 없다. 기대: 타입 검사가 초록이고
//   `node` 가 짝 43개와 모두 검은 값의 실패 43개를 찍는다.
//
// 측정의 표지: 설치가 0으로 끝나고 `web/node_modules/@agent-os/ui` 가 섰다. `as-is` 는 타입 검사 출력에 contrast.ts 의
// TS2834/TS2835 가 있고 `node` 의 stderr 에 ERR_UNSUPPORTED_DIR_IMPORT 와 `testing` 폴더 경로가 있다. `self-contained` 는 `node` 의 stdout 이 기대한
// JSON 한 줄이다. 표지가 없는 갈래(설치 실패, 잘라 붙일 자리를 못 찾음, 다른 오류)는 측정이 아니라고 따로 세고 종료
// 코드를 1로 둔다.
//
// 이 측정은 짝 표 파일이 아직 `testing`·`themes` 를 상대 경로로 부르던 판(design-reverse-sync 티켓 01 이 계산 함수를 그
// 파일로 옮기기 전, 예 `96fbe241`)에서만 뜻이 있다. 옮긴 뒤의 판에서 `--commit` 없이 돌리면 `as-is` 는 타입 검사와
// `node` 가 모두 0 이라 표지가 없고 `self-contained` 는 잘라 붙일 자리를 찾지 못해, 둘 다 측정이 아니고 종료 코드가 1 이다
// (`959e3276` 에서 돌려 봤다, 일지 2026-10-22-24). 다시 잴 때는 `--commit` 으로 옮기기 전 판을 준다.
//
// 저장소 루트에서 돈다. 사본은 OS 임시 폴더에 이 실행이 `mkdtemp` 로 만든 폴더이고, 끝에 그 폴더만 지운다
// (`--keep` 이면 남기고 경로를 찍는다). 인자로 폴더를 받지 않는다.
//   node .scratch/design-reverse-sync/probes/tools_import.mjs [--commit <커밋>] [--keep]
// 필요한 것: git, tar, pnpm(`web/package.json` 의 `packageManager` 판), 그 판의 저장소에 이 커밋의 의존성이 이미 받아져
// 있을 것(`pnpm -C web install` 을 한 번 한 기계). 종료 코드: 두 갈래가 모두 측정이고 기대대로면 0, 아니면 1, 인자를
// 읽지 못하면 2.

import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync, mkdirSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const SPLIT_BEFORE = "/** 시트들의 스타일 규칙 전부.";
const PROBE_FILE = "tools/probe-import.ts";

function parseArgs(argv) {
  const out = { commit: "HEAD", keep: false };
  for (let i = 0; i < argv.length; i += 1) {
    const name = argv[i];
    if (name === "--keep") {
      out.keep = true;
    } else if (name === "--commit" && argv[i + 1] !== undefined && !argv[i + 1].startsWith("--")) {
      out.commit = argv[i + 1];
      i += 1;
    } else {
      console.error(`인자를 읽지 못했다: ${name}. 쓰는 법: [--commit <커밋>] [--keep]`);
      process.exit(2);
    }
  }
  if (!/^[0-9A-Za-z_./~^-]+$/.test(out.commit) || out.commit.startsWith("-")) {
    console.error(`커밋 값을 받지 않는다: ${out.commit}`);
    process.exit(2);
  }
  return out;
}

const options = parseArgs(process.argv.slice(2));
const commit = execFileSync("git", ["rev-parse", "--verify", `${options.commit}^{commit}`], {
  encoding: "utf-8",
}).trim();

function run(command, args, cwd) {
  const result = spawnSync(command, args, { cwd, encoding: "utf-8", shell: process.platform === "win32" });
  return { status: result.status, stdout: result.stdout ?? "", stderr: result.stderr ?? "" };
}

/** `git archive` 로 그 커밋의 `web/` 을 새 임시 폴더에 꺼낸다. 돌려주는 것은 그 폴더와 그 안의 `web` 경로다. */
function extractWeb() {
  const root = mkdtempSync(join(tmpdir(), "drs-tools-import-"));
  const tarPath = join(root, "web.tar");
  execFileSync("git", ["archive", "--format=tar", "-o", tarPath, commit, "web"]);
  execFileSync("tar", ["-xf", "web.tar"], { cwd: root });
  rmSync(tarPath);
  return { root, web: join(root, "web") };
}

function editJson(path, edit) {
  const data = JSON.parse(readFileSync(path, "utf-8"));
  edit(data);
  writeFileSync(path, `${JSON.stringify(data, null, 2)}\n`);
}

/** 갈래 하나를 짓고 잰다. 돌려주는 것은 결과 한 줄이다. */
function measure(variant) {
  const { root, web } = extractWeb();
  const line = { variant, commit, measured: false, marker: [], copy: options.keep ? root : null };
  try {
    const exportPath = variant === "as-is" ? "./src/styles/contrast.ts" : "./src/color/index.ts";
    const subpath = variant === "as-is" ? "./contrast" : "./color";
    if (variant === "self-contained") {
      const testing = readFileSync(join(web, "packages/ui/src/testing/index.ts"), "utf-8");
      const contrast = readFileSync(join(web, "packages/ui/src/styles/contrast.ts"), "utf-8");
      const cut = testing.indexOf(SPLIT_BEFORE);
      const firstCode = testing.indexOf("type Channels");
      const importLines = contrast.match(/^import .*;\n/gm) ?? [];
      if (cut === -1 || firstCode === -1 || importLines.length !== 2) {
        line.reason = `잘라 붙일 자리를 찾지 못했다(cut ${cut}, firstCode ${firstCode}, import ${importLines.length})`;
        return line;
      }
      let body = contrast;
      for (const importLine of importLines) {
        body = body.replace(importLine, "");
      }
      const module = [
        "// 프로브가 지은 파일: testing/index.ts 의 DOM 없는 앞부분과 contrast.ts 의 본문.",
        testing.slice(firstCode, cut).trimEnd(),
        "",
        'type Mode = "light" | "dark";',
        body,
      ].join("\n");
      mkdirSync(join(web, "packages/ui/src/color"), { recursive: true });
      writeFileSync(join(web, "packages/ui/src/color/index.ts"), module);
    }
    editJson(join(web, "packages/ui/package.json"), (data) => {
      data.exports[subpath] = exportPath;
    });
    editJson(join(web, "package.json"), (data) => {
      data.devDependencies["@agent-os/ui"] = "workspace:*";
    });
    writeFileSync(
      join(web, PROBE_FILE),
      [
        `import { CONTRAST_PAIRS, contrastFailures } from "@agent-os/ui/${subpath.slice(2)}";`,
        "",
        'const black = (): string => "#000000";',
        'const failures = contrastFailures("nokcheong", "light", black);',
        "console.log(JSON.stringify({ pairs: CONTRAST_PAIRS.length, failures: failures.length }));",
        "",
      ].join("\n"),
    );

    const install = run("pnpm", ["install", "--offline", "--no-frozen-lockfile", "--ignore-scripts"], web);
    line.install = install.status;
    const linked = existsSync(join(web, "node_modules/@agent-os/ui/package.json"));
    line.linked = linked;
    if (install.status !== 0 || !linked) {
      line.reason = `설치가 끝나지 않았거나 링크가 없다: ${install.stderr.slice(-400)}`;
      return line;
    }

    const tsc = run("node", ["node_modules/typescript/bin/tsc", "--noEmit"], web);
    const tscOut = `${tsc.stdout}${tsc.stderr}`;
    line.tsc = { status: tsc.status, codes: [...new Set(tscOut.match(/TS\d{4}/g) ?? [])] };
    const node = run("node", [PROBE_FILE], web);
    line.node = { status: node.status, stdout: node.stdout.trim(), stderrCode: (node.stderr.match(/ERR_[A-Z_]+/) ?? [null])[0] };

    if (variant === "as-is") {
      const extensionError = /contrast\.ts\(\d+,\d+\): error TS283[45]/.test(tscOut);
      const notFound =
        node.stderr.includes("ERR_UNSUPPORTED_DIR_IMPORT") && /[\\/]src[\\/]testing'/.test(node.stderr);
      if (extensionError) line.marker.push("tsc: contrast.ts 의 확장자 없는 import 가 TS2834/TS2835");
      if (notFound) line.marker.push("node: '../testing' 을 폴더 import 로 읽어 ERR_UNSUPPORTED_DIR_IMPORT");
      line.measured = extensionError && notFound;
      line.expected = line.measured && tsc.status !== 0 && node.status !== 0;
    } else {
      const printed = node.stdout.trim() === JSON.stringify({ pairs: 43, failures: 43 });
      if (printed) line.marker.push("node: 짝 43개와 실패 43개를 찍었다");
      line.measured = printed;
      line.expected = printed && tsc.status === 0 && line.tsc.codes.length === 0 && node.status === 0;
    }
    if (!line.measured) {
      line.reason = `표지가 없다. tsc: ${tscOut.slice(0, 600)} node: ${node.stderr.slice(0, 400)}`;
    }
    return line;
  } finally {
    if (!options.keep) {
      rmSync(root, { recursive: true, force: true });
    }
  }
}

const lines = ["as-is", "self-contained"].map(measure);
for (const line of lines) {
  console.log(JSON.stringify(line));
}
const notMeasured = lines.filter((line) => !line.measured).length;
const unexpected = lines.filter((line) => line.measured && !line.expected).length;
console.log(JSON.stringify({ summary: { measured: lines.length - notMeasured, notMeasured, unexpected } }));
process.exit(notMeasured === 0 && unexpected === 0 ? 0 : 1);
