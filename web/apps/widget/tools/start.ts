/**
 * 위젯의 시작 래퍼. 앱의 `dev`·`build`·`start` 스크립트가 이것을 거친다(ADR 0024 의 "Next는 루프백에만 선다").
 *
 * - `dev`·`start` 는 관리 화면의 래퍼와 같은 모양이다. 바인딩 호스트가 루프백이 아니면 next 를 부르기 전에 구성
 *   오류로 끝나고 SSH 포트 포워딩을 안내한다. 호스트를 주지 않으면 `127.0.0.1` 이다. `next dev`·`next start` 는 인자
 *   없이 `0.0.0.0` 과 `[::]` 에 서서, 위젯이 nginx 와 TLS 를 거치지 않고 LAN 에 평문으로 열린다.
 * - `dev`·`build` 는 next 를 부르기 전에 빌드의 입력을 준비한다. 지금은 글꼴 파일을 `public/fonts/` 에 복사하는
 *   것이다(`fonts.ts`). 페이지 안 번들(티켓 10)이 이 자리에 든다. `start` 는 빌드 산출물과 그 `public/` 을 그대로 낸다.
 * - 사이트 파일(티켓 04)은 준비하지 않고 설정 파일(`next.config.ts`)이 `AGENT_OS_SITE_FILE` 로 읽는다. next 를 이
 *   프로세스에서 부르므로 변수는 그대로 이어지고, 래퍼는 상대 경로를 부른 자리 기준의 절대 경로로 바꿔 넘긴다. 읽지
 *   못하면 next 가 그 진단을 찍고 종료 코드 1로 끝난다. `build` 는 `start.spawn.test.ts` 가 보고, `dev`·`start` 는 손으로
 *   봤다(일지 2026-10-24-05).
 *
 * 받는 인자는 `--hostname`(`-H`)과 `--port`(`-p`) 둘뿐이고 `build` 는 둘 다 받지 않는다. next 에 넘기는 인자는 받은
 * 것을 옮기지 않고 판정한 값으로 다시 짓는다. 다른 인자가 필요하면 `next` 를 직접 띄운다. 그것은 래퍼가 막지 못한다.
 *
 * 공유 자리로 옮기지 않고 위젯이 자기 래퍼를 둔다(web-widget 티켓 03 이 정했다). 관리 화면의 래퍼(apps/admin/tools)를
 * 옮기면 관리 화면의 e2e 와 시험까지 고치게 되고, 위젯의 래퍼는 빌드도 맡아 하는 일이 다르다. 대가로 루프백 목록이
 * 세 벌이 된다(`serve` 의 `src/agent_os/main.py` 의 `LOOPBACK_HOSTS`, 관리 화면의 `tools/loopback.ts`, 이 파일).
 * 앱 사이 import 는 층 경계가 막는다. 목록을 바꾸면 셋을 함께 고친다.
 *
 * 판정을 지나면 next CLI 를 이 프로세스에서 부른다. 신호와 종료 코드가 next 의 것 그대로다(관리 화면의 래퍼와 같다).
 *
 * 사용: node tools/start.ts <dev|build|start> [--hostname <호스트>] [--port <포트>]
 */

import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { parseArgs } from "node:util";
import { copyFonts } from "./fonts.ts";
import { SITE_FILE_ENV } from "./site-file.ts";

const APP = dirname(import.meta.dirname);
// 순서가 진단의 문장이 된다. serve 의 진단과 같은 순서다.
const LOOPBACK_HOSTS: readonly string[] = ["127.0.0.1", "::1"];
const DEFAULT_HOST = "127.0.0.1";
const SERVING: readonly string[] = ["dev", "start"];
const USAGE =
  "위젯의 시작 래퍼는 dev·build·start 하나를 받고, dev 와 start 만 --hostname(-H), --port(-p)를 받는다.";

/** next CLI 에 넘길 인자와 그 전에 빌드의 입력을 준비할지, 또는 띄우지 않을 까닭. */
export type NextCommand =
  { readonly args: readonly string[]; readonly prepare: boolean } | { readonly problem: string };

/** 래퍼가 받은 인자를 판정한다. `defaultPort` 는 포트를 주지 않았을 때 next 가 쓸 포트이고 SSH 안내에만 싣는다. */
export function nextCommand(argv: readonly string[], defaultPort: string): NextCommand {
  const parsed = parse(argv);
  if ("problem" in parsed) {
    return parsed;
  }
  const { positionals, values } = parsed;
  const [command] = positionals;
  if (positionals.length !== 1 || command === undefined) {
    return { problem: `${USAGE} 받은 명령: ${positionals.join(" ") || "없음"}` };
  }
  if (command === "build") {
    if (values.hostname !== undefined || values.port !== undefined) {
      return { problem: `${USAGE} build 는 서지 않아 호스트와 포트를 받지 않는다` };
    }
    return { args: ["build"], prepare: true };
  }
  if (!SERVING.includes(command)) {
    return { problem: `${USAGE} 받은 명령: ${command}` };
  }
  const host = values.hostname ?? DEFAULT_HOST;
  const problem = bindingProblem(host, values.port ?? defaultPort);
  if (problem !== null) {
    return { problem };
  }
  const port = values.port === undefined ? [] : ["--port", values.port];
  return { args: [command, "--hostname", host, ...port], prepare: command === "dev" };
}

/** 위젯이 설 호스트의 구성 오류. 루프백이면 null. `port` 는 SSH 안내에 싣는다. */
function bindingProblem(host: string, port: string): string | null {
  if (LOOPBACK_HOSTS.includes(host)) {
    return null;
  }
  return [
    `--hostname 은 루프백만 받는다(${LOOPBACK_HOSTS.join(", ")}). 받은 값: ${host}`,
    "  벗어나면 위젯이 nginx 와 TLS 를 거치지 않고 LAN 에 평문으로 열린다.",
    `  원격에서 보려면 SSH 포트 포워딩을 쓴다: ssh -L ${port}:127.0.0.1:${port} <서버>`,
  ].join("\n");
}

function parse(argv: readonly string[]) {
  try {
    return parseArgs({
      args: [...argv],
      options: {
        hostname: { type: "string", short: "H" },
        port: { type: "string", short: "p" },
      },
      allowPositionals: true,
      strict: true,
    });
  } catch (error: unknown) {
    return { problem: `${USAGE}\n  ${error instanceof Error ? error.message : String(error)}` };
  }
}

/**
 * 사이트 파일의 경로를 래퍼를 부른 자리 기준의 절대 경로로 바꾼다. next 를 부르기 전에 작업 폴더를 앱으로 옮기므로, 상대
 * 경로를 그대로 두면 설정 파일이 앱 폴더에서 풀어 운영자가 준 파일을 찾지 못한다. 비었거나 없으면 그대로 둔다. 그
 * 판정은 설정 파일(tools/site-file.ts)이 한다.
 */
export function absoluteSiteFile(value: string | undefined, cwd: string): string | undefined {
  return value === undefined || value === "" ? value : resolve(cwd, value);
}

/** 판정을 지난 인자로 next CLI 를 이 프로세스에서 부른다. next 의 진입점은 적재될 때 `process.argv` 를 읽는다. */
function runNext(args: readonly string[]): void {
  const load = createRequire(import.meta.url);
  const bin = load.resolve("next/dist/bin/next");
  const siteFile = absoluteSiteFile(process.env[SITE_FILE_ENV], process.cwd());
  if (siteFile !== undefined) {
    process.env[SITE_FILE_ENV] = siteFile;
  }
  process.chdir(APP);
  process.argv = [process.execPath, bin, ...args];
  load(bin);
}

/** 빌드의 입력 준비와 next 부르기. 시험은 둘을 바꿔 끼워 차례를 본다. */
export interface LaunchSteps {
  readonly prepare: () => void;
  readonly run: (args: readonly string[]) => void;
}

const REAL_STEPS: LaunchSteps = {
  prepare: () => {
    copyFonts(join(APP, "public", "fonts"));
  },
  run: runNext,
};

/** 판정을 지난 명령을 따른다. 준비할 명령이면 빌드의 입력을 준비한 뒤 next 를 부른다. */
export function launch(
  command: Exclude<NextCommand, { readonly problem: string }>,
  steps: LaunchSteps = REAL_STEPS,
): void {
  if (command.prepare) {
    steps.prepare();
  }
  steps.run(command.args);
}

if (import.meta.main) {
  const command = nextCommand(process.argv.slice(2), process.env["PORT"] ?? "3000");
  if ("problem" in command) {
    console.error(command.problem);
    process.exitCode = 1;
  } else {
    launch(command);
  }
}
