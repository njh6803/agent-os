/**
 * 명령의 공용 꼴. 진입 파일(`main.ts`)이 명령 표로 명령을 고르고, 명령은 명령 이름 뒤의 인자를 받아 보고의 칸을
 * 돌려준다. 입력과 출력은 파일이고 상대 경로는 작업 폴더에서 푼다(design-reverse-sync 명세 "이음매").
 *
 * 명령은 실패를 `CommandError` 로 알린다. 진입 파일이 받아 보고 JSON 의 오류 칸에 종류와 문구를 넣고 1 로 끝난다.
 * 종류는 기계가 가르는 값이다.
 *
 * - `usage`: 명령이나 인자가 틀렸거나 빠졌다. 받은 상태로는 부를 수 없는 인자 조합도 든다(웹 편집을 찾은 확인 보고에
 *   `--overwrite` 가 없다, `pending` 이 든 기록에 확인 보고가 없다 등).
 * - `input`: 입력 파일을 읽거나 풀 수 없거나, 입력끼리 맞지 않는다(기록에 적을 파일이 이번 산출에 없다 등). 짓기
 *   명령에서는 빌드가 실패했거나 지은 산출이 형식의 규칙(금지 문자열, 카드 README)을 어긴 것도 든다.
 * - `limit`: 형식의 한도(테마 8, 색 600, 다른 계열 60, 짓기 명령의 묶음·카드·카드 README 의 바이트)나 기록의 한도
 *   (512,000 바이트)를 넘는다.
 * - `output`: 출력 파일을 쓸 수 없다. 짓기 명령에서는 산출 폴더 자리에 쓸 수 없는 것(그 자리가 파일이다, 비어 있지 않은
 *   폴더다, 산출을 옮길 수 없다)과 임시 폴더를 만들 수 없는 것도 든다.
 */

import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import type { JsonValue } from "./tokens-json.ts";

export const ERROR_KINDS = ["usage", "input", "limit", "output"] as const;

export type ErrorKind = (typeof ERROR_KINDS)[number];

export class CommandError extends Error {
  readonly kind: ErrorKind;

  constructor(kind: ErrorKind, message: string) {
    super(message);
    this.name = "CommandError";
    this.kind = kind;
  }
}

/** 성공한 명령의 보고 칸. 진입 파일이 앞에 `command` 와 `ok` 를 붙인다. */
export type ReportFields = Readonly<Record<string, JsonValue>>;

/** 명령 하나. 인자는 명령 이름 뒤의 것이다. */
export type Command = (args: readonly string[]) => ReportFields;

/** 잡은 오류의 문구. `Error` 가 아닌 값은 글로 바꾼다. */
export function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/** 인자 풀기(`node:util` 의 `parseArgs`)가 던지는 오류를 `usage` 오류로 바꾼다. */
export function parsedArgs<T>(parse: () => T): T {
  try {
    return parse();
  } catch (error) {
    throw new CommandError("usage", messageOf(error));
  }
}

/** 입력 파일을 UTF-8 글로 읽는다. 읽을 수 없으면 `input` 오류다. */
export function readInput(path: string): string {
  try {
    return readFileSync(resolve(path), "utf-8");
  } catch (error) {
    throw new CommandError("input", `${path} 를 읽을 수 없다: ${messageOf(error)}`);
  }
}

/** 출력 파일을 쓰고 그 절대 경로를 돌려준다. 폴더가 없으면 만든다. 쓸 수 없으면 `output` 오류다. */
export function writeOutput(path: string, text: string): string {
  const absolute = resolve(path);
  try {
    mkdirSync(dirname(absolute), { recursive: true });
    writeFileSync(absolute, text);
  } catch (error) {
    throw new CommandError("output", `${path} 를 쓸 수 없다: ${messageOf(error)}`);
  }
  return absolute;
}
