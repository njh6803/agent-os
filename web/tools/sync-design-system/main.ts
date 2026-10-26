/**
 * 디자인 시스템 거꾸로 동기화 스크립트의 진입(design-reverse-sync 명세 "이음매"). 명령 표로 명령을 고르고, 명령마다
 * 모듈 하나를 둔다. 디자인 토큰 CSS 풀기(`theme-css.ts`), `tokens.json` 의 모델과 두 벌의 차이(`tokens-json.ts`),
 * 명령의 공용 꼴(`command.ts`)은 명령들이 같이 쓴다.
 *
 * 보고는 표준 출력의 JSON 한 줄이다. 성공은 `{"command", "ok": true, ...명령의 칸}` 과 종료 코드 0, 실패는
 * `{"command", "ok": false, "error": {"kind", "message"}}` 와 종료 코드 1 이다. 오류의 종류는 `command.ts` 에 있다.
 *
 * 못 보는 것: 명령의 버그(`CommandError` 가 아닌 예외)는 보고 없이 Node 의 스택과 함께 1 로 끝난다.
 *
 * 사용: node tools/sync-design-system/main.ts <명령> [인자 ...]. 명령의 인자는 그 모듈의 독스트링에 있다.
 */

import { build } from "./build.ts";
import { check } from "./check.ts";
import { CommandError, type Command, type ErrorKind } from "./command.ts";
import { record } from "./record.ts";
import type { JsonValue } from "./tokens-json.ts";

/** 명령 표. 명령을 더하는 티켓은 모듈 하나와 이 표의 한 줄을 더한다. */
const COMMANDS: ReadonlyMap<string, Command> = new Map([
  ["build", build],
  ["check", check],
  ["record", record],
]);

interface Outcome {
  readonly report: JsonValue;
  readonly code: number;
}

/** 실패의 보고와 종료 코드. */
function failure(command: string, kind: ErrorKind, message: string): Outcome {
  return { report: { command, ok: false, error: { kind, message } }, code: 1 };
}

/** 명령 하나를 돌려 보고와 종료 코드를 낸다. */
export function run(argv: readonly string[]): Outcome {
  const [name = "", ...args] = argv;
  const command = COMMANDS.get(name);
  if (command === undefined) {
    const known = [...COMMANDS.keys()].join(", ");
    return failure(name, "usage", `모르는 명령 ${JSON.stringify(name)}. 아는 명령: ${known}`);
  }
  try {
    return { report: { command: name, ok: true, ...command(args) }, code: 0 };
  } catch (error) {
    if (!(error instanceof CommandError)) {
      throw error;
    }
    return failure(name, error.kind, error.message);
  }
}

if (import.meta.main) {
  const { report, code } = run(process.argv.slice(2));
  console.log(JSON.stringify(report));
  process.exitCode = code;
}
