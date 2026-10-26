/**
 * 기록·확인 명령의 입력 읽기. 입력 파일과 폴더를 읽고, 푼 JSON 을 꼴을 본 값으로 옮긴다. 읽을 수 없으면 `input`
 * 오류다(`command.ts`). 파일 종류를 가리지 않는 sha256 과 JSON 풀기도 여기 둔다(파일 종류마다의 맞대는 값은
 * `file-hash.ts`).
 *
 * 경로는 아티팩트의 경로(`project/` 로 시작하고 `/` 로 가른다)다. 기록과 색인은 아티팩트의 쓰는 사람이 쓴 데이터라,
 * 그 안의 경로는 `isArtifactPath` 를 지난 것만 받는다. 그래서 받은 폴더 밖을 읽지 않는다.
 */

import { createHash } from "node:crypto";
import { readdirSync, readFileSync } from "node:fs";
import { join, relative, resolve, sep } from "node:path";
import { CommandError } from "./command.ts";
import type { JsonValue } from "./tokens-json.ts";

/** 바이트의 sha256(16 진수). */
export function sha256(bytes: Uint8Array): string {
  return createHash("sha256").update(bytes).digest("hex");
}

/** JSON 글을 푼다. 풀리지 않으면 undefined. */
export function parseJson(text: string): unknown {
  try {
    const parsed: unknown = JSON.parse(text);
    return parsed;
  } catch {
    return undefined;
  }
}

/** 경로 차례(UTF-16 코드 단위). 기록과 보고의 경로 목록이 이 차례다. */
export function byPath(left: string, right: string): number {
  return left < right ? -1 : left > right ? 1 : 0;
}

/** 겹친 것을 한 번만 두고 경로 차례로 놓은 목록. */
export function sortedPaths(paths: Iterable<string>): string[] {
  return [...new Set(paths)].sort(byPath);
}

/** 입력 파일 `path` 가 `what` 이라는 `input` 오류. */
export function inputError(path: string, what: string): CommandError {
  return new CommandError("input", `${path} 가 ${what}`);
}

export function isRecord(value: unknown): value is Readonly<Record<string, unknown>> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** 푼 JSON 을 JSON 값으로 옮긴다. JSON 이 낼 수 없는 값(함수, 무한대 등)이 있으면 undefined. */
export function jsonValue(value: unknown): JsonValue | undefined {
  if (value === null || typeof value === "string" || typeof value === "boolean") {
    return value;
  }
  if (typeof value === "number") {
    return Number.isFinite(value) ? value : undefined;
  }
  if (Array.isArray(value)) {
    const items: JsonValue[] = [];
    for (const item of value.map((raw: unknown) => raw)) {
      const converted = jsonValue(item);
      if (converted === undefined) {
        return undefined;
      }
      items.push(converted);
    }
    return items;
  }
  if (isRecord(value)) {
    const entries: [string, JsonValue][] = [];
    for (const [key, item] of Object.entries(value)) {
      const converted = jsonValue(item);
      if (converted === undefined) {
        return undefined;
      }
      entries.push([key, converted]);
    }
    // `Object.fromEntries` 는 `__proto__` 키도 자기 속성으로 둔다.
    return Object.fromEntries(entries);
  }
  return undefined;
}

/**
 * 배열이면 항목을 `unknown` 으로 둔 사본, 아니면 undefined. `Array.isArray` 는 `unknown` 을 `any[]` 로 좁혀, 그대로 쓰면
 * 타입 검사가 항목을 보지 않는다.
 */
export function unknownList(value: unknown): unknown[] | undefined {
  return Array.isArray(value) ? value.map((item: unknown) => item) : undefined;
}

/** 항목이 모두 문자열인 배열이면 그 배열, 아니면 undefined. */
export function stringList(value: unknown): string[] | undefined {
  const items = unknownList(value);
  if (items === undefined) {
    return undefined;
  }
  return items.every((item): item is string => typeof item === "string") ? items : undefined;
}

/** 윈도가 파일 이름에 받지 않는 글자, 역슬래시, 제어 문자. */
const RESERVED = /[\\:*?"<>|\p{Cc}]/u;

function isSegment(segment: string): boolean {
  return segment !== "" && segment !== "." && segment !== ".." && !RESERVED.test(segment);
}

/** 아티팩트의 `project/` 아래 경로인가. 빈 토막, `.`·`..`, 역슬래시, 드라이브 문자, 제어 문자를 받지 않는다. */
export function isArtifactPath(path: string): boolean {
  const segments = path.split("/");
  return segments.length >= 2 && segments[0] === "project" && segments.every(isSegment);
}

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/** 입력 파일의 바이트. 읽을 수 없으면 `input` 오류다. */
export function readBytes(path: string): Uint8Array {
  try {
    return readFileSync(resolve(path));
  } catch (error) {
    throw new CommandError("input", `${path} 를 읽을 수 없다: ${messageOf(error)}`);
  }
}

/** 입력 파일을 JSON 으로 푼 값. 읽거나 풀 수 없으면 `input` 오류다. */
export function readJson(path: string): unknown {
  const parsed = parseJson(new TextDecoder().decode(readBytes(path)));
  if (parsed === undefined) {
    throw new CommandError("input", `${path} 가 JSON 으로 풀리지 않는다`);
  }
  return parsed;
}

/** 입력 파일의 경로 목록(JSON 문자열 배열). 아티팩트 경로가 아닌 것이 들면 `input` 오류다. */
export function readPathList(path: string): string[] {
  const list = stringList(readJson(path));
  if (list === undefined) {
    throw new CommandError("input", `${path} 가 경로 문자열의 JSON 배열이 아니다`);
  }
  const wrong = list.find((item) => !isArtifactPath(item));
  if (wrong !== undefined) {
    throw new CommandError(
      "input",
      `${path} 의 ${JSON.stringify(wrong)} 가 project/ 아래 경로가 아니다`,
    );
  }
  return list;
}

/**
 * 폴더 안의 파일을 모두 읽는다. 열쇠는 폴더 안의 상대 경로를 `/` 로 이은 것 앞에 `prefix` 를 붙인 것이다. 링크는
 * 따라가지 않고 건너뛴다. 폴더를 읽을 수 없으면 `input` 오류다.
 */
export function readFolder(folder: string, prefix: string): Map<string, Uint8Array> {
  const root = resolve(folder);
  const files = new Map<string, Uint8Array>();
  try {
    for (const entry of readdirSync(root, { withFileTypes: true, recursive: true })) {
      if (!entry.isFile()) {
        continue;
      }
      const absolute = join(entry.parentPath, entry.name);
      files.set(
        `${prefix}${relative(root, absolute).split(sep).join("/")}`,
        readFileSync(absolute),
      );
    }
  } catch (error) {
    throw new CommandError("input", `${folder} 를 읽을 수 없다: ${messageOf(error)}`);
  }
  return new Map([...files].sort(([left], [right]) => byPath(left, right)));
}
