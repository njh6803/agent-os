/**
 * 관리 화면의 시작 래퍼. 앱의 `dev` 와 `start` 스크립트가 이것을 거친다(ADR 0019, ADR 0011 의 2026-09-28 이력).
 * `next dev`·`next start` 는 인자 없이 `0.0.0.0` 과 `[::]` 에 선다. 래퍼는 바인딩 호스트가 루프백이 아니면 next 를
 * 부르기 전에 구성 오류로 끝나고, `serve` 처럼 SSH 포트 포워딩을 안내한다. 호스트를 주지 않으면 `127.0.0.1` 이다.
 *
 * 받는 인자는 `--hostname`(`-H`)과 `--port`(`-p`) 둘뿐이다. next 에 넘기는 인자는 받은 것을 그대로 옮기지 않고
 * 판정한 값으로 다시 짓는다. 그 밖의 인자는 구성 오류다. next 의 `--inspect [[host:]port]` 는 서버의 디버거를 LAN 에
 * 열 수 있다. 다른 인자가 필요하면 `next` 를 직접 띄운다. 그것은 래퍼가 막지 못한다(ADR 0019).
 *
 * 판정을 지나면 next CLI 를 자식 프로세스가 아니라 이 프로세스에서 부른다. 래퍼와 next CLI 가 한 프로세스라 신호와
 * 종료 코드가 next 의 것 그대로이고, 신호를 넘기는 코드가 없다. `next dev` 가 서버를 자식으로 띄우고 거두는 것은
 * next 의 몫이다.
 *
 * 사용: node tools/start.ts <dev|start> [--hostname <호스트>] [--port <포트>]
 */

import { createRequire } from "node:module";
import { dirname } from "node:path";
import { parseArgs } from "node:util";
import { bindingProblem, DEFAULT_HOST } from "./loopback.ts";

const APP = dirname(import.meta.dirname);
const COMMANDS: readonly string[] = ["dev", "start"];
const USAGE = "관리 화면의 시작 래퍼는 dev 나 start 하나와 --hostname(-H), --port(-p)만 받는다.";

/** next CLI 에 넘길 인자, 또는 띄우지 않을 까닭. */
export type NextCommand = { readonly args: readonly string[] } | { readonly problem: string };

/** 래퍼가 받은 인자를 판정한다. `defaultPort` 는 포트를 주지 않았을 때 next 가 쓸 포트이고 SSH 안내에만 싣는다. */
export function nextCommand(argv: readonly string[], defaultPort: string): NextCommand {
  const parsed = parse(argv);
  if ("problem" in parsed) {
    return parsed;
  }
  const { positionals, values } = parsed;
  const [command] = positionals;
  if (positionals.length !== 1 || command === undefined || !COMMANDS.includes(command)) {
    return { problem: `${USAGE} 받은 명령: ${positionals.join(" ") || "없음"}` };
  }
  const host = values.hostname ?? DEFAULT_HOST;
  const problem = bindingProblem(host, values.port ?? defaultPort);
  if (problem !== null) {
    return { problem };
  }
  const port = values.port === undefined ? [] : ["--port", values.port];
  return { args: [command, "--hostname", host, ...port] };
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

/** 판정을 지난 인자로 next CLI 를 이 프로세스에서 부른다. next 의 진입점은 적재될 때 `process.argv` 를 읽는다. */
function runNext(args: readonly string[]): void {
  const load = createRequire(import.meta.url);
  const bin = load.resolve("next/dist/bin/next");
  process.chdir(APP);
  process.argv = [process.execPath, bin, ...args];
  load(bin);
}

if (import.meta.main) {
  const command = nextCommand(process.argv.slice(2), process.env["PORT"] ?? "3000");
  if ("problem" in command) {
    console.error(command.problem);
    process.exitCode = 1;
  } else {
    runNext(command.args);
  }
}
