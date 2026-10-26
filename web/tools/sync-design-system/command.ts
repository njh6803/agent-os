/**
 * 명령의 공용 꼴. 진입 파일(`main.ts`)이 명령 표로 명령을 고르고, 명령은 명령 이름 뒤의 인자를 받아 보고의 칸을
 * 돌려준다. 입력과 출력은 파일이고 상대 경로는 작업 폴더에서 푼다(design-reverse-sync 명세 "이음매").
 *
 * 명령은 실패를 `CommandError` 로 알린다. 진입 파일이 받아 보고 JSON 의 오류 칸에 종류와 문구를 넣고 1 로 끝난다.
 * 종류는 기계가 가르는 값이다.
 *
 * - `usage`: 명령이나 인자가 틀렸다.
 * - `input`: 입력 파일을 읽거나 풀 수 없다.
 * - `limit`: 형식의 한도(테마 8, 색 600, 다른 계열 60)를 넘는다.
 * - `output`: 출력 파일을 쓸 수 없다.
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
