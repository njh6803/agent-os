/**
 * 위젯의 응답 머리 목록(`.next/routes-manifest.json`)을 다루는 코드. 빌드는 사이트 파일을 읽지 않고 페이지를 품어도 되는
 * 사이트를 알리는 머리를 `frame-ancestors 'none'` 으로 굳힌다. 서비스 시작이 뜰 때 그 자리를 사이트 파일의 허용 출처로 바꾼
 * 사본을 Next 가 읽는 자리에 쓴다(widget-runtime-values 명세 "품어도 되는 사이트를 알리는 응답 머리", 티켓 02, ADR 0064).
 * 그래서 한 번 지은 산출물을 사이트 파일만 바꿔 가며 다시 띄울 수 있다.
 *
 * - 원본. 빌드가 끝나면 `.next/routes-manifest.original.json` 으로 목록을 남긴다. 사본(`.next/routes-manifest.json`)은 서비스 시작이
 *   쓸 때마다 원본에서 새로 바꾸므로, 앞 사본이 남아 있어도 앞 값이 이어지지 않는다.
 * - 원본을 남기는 길. 래퍼는 Next 의 실행 파일을 같은 프로세스 안에서 돌린다(`start.ts` 의 `runNext`). Next 16.3.6 의 그 실행
 *   파일은 빌드가 끝나기를 기다리지 않고 돌아오고(`program.parse`), 빌드를 마치면 `process.exit(0)` 으로 끝난다. Next 를 부른
 *   줄 뒤에서 복사하면 빌드보다 먼저 돌아 앞 빌드의 낡은 목록을 남기거나 목록이 없어 실패한다. 그래서 프로세스가 끝날 때 도는
 *   처리기(`keepOriginalOnExit`)에서 복사한다. 빌드를 자식 프로세스로 돌리는 길도 있었다. 신호와 종료 코드가 Next 의 것 그대로
 *   이어지는 지금의 모양(관리 화면의 래퍼와 같다)을 지키려고 처리기를 골랐다. 대가는 처리기가 `exit` 에서 동기로만 일한다는
 *   것이고, 복사 하나뿐이라 맞는다. 종료 코드가 0 이 아니면(빌드가 실패했다) 복사하지 않는다. Next 의 판이 올라 이 순서가
 *   바뀌는지는 위젯과 위젯 테스트 페이지의 e2e 가 실제 `next build` 로 본다(`start.spawn.test.ts` 는 가로챈 가짜 Next 를 쓴다).
 * - 바꿀 자리. 머리의 이름이 대소문자를 가리지 않고 `Content-Security-Policy` 이고 값이 `frame-ancestors` 로 시작하는 자리가
 *   정확히 하나이고 값이 글자 그대로 `frame-ancestors 'none'` 일 때만 바꾼다. 그 밖에는 아무것도 쓰지 않고 까닭을 적은
 *   진단을 던진다. Next 의 판이 올라 파일의 모양이 바뀌었거나 빌드가 사이트 파일을 읽어 버린 산출물이면, 틀린 값으로 조용히
 *   뜨는 대신 뜨지 않는다. 진단은 그 까닭이 사이트 파일이 아니라 그 판의 산출물이라고 말한다.
 * - 사본은 그 자리를 열어 바로 쓴다. 임시 파일에 쓴 뒤 이름을 바꿔 덮지 않는다. 이미지가 그 자리를 쓰는 폴더 안을 가리키는
 *   링크로 바꿔도(티켓 03) 이 코드를 다시 고치지 않게 하려는 것이다. 이름 바꾸기는 링크를 따라가지 않는다.
 * - 이 파일은 서비스 시작의 길에 든다. 스크립트를 짓는 도구(Vite, Tailwind, TypeScript)를 불러오지 않는다.
 */

import { copyFileSync, existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import type { RuntimeValuesFile } from "./runtime.ts";

/** 빌드가 굳히는 머리의 값. 서비스 시작이 바꿀 자리를 이 값으로 알아본다. */
export const PLACEHOLDER = "frame-ancestors 'none'";

const MANIFEST_FILE = "routes-manifest.json";
const ORIGINAL_FILE = "routes-manifest.original.json";

/** 사이트 파일이 아니라 산출물의 문제라는 것을 운영자가 읽게 하는 끝 문장. */
const NOT_THE_SITE_FILE =
  "  사이트 파일의 문제가 아니다. 이 위젯 판의 빌드 산출물이 기대한 모양이 아니라서 위젯을 다시 띄워도 풀리지 않는다. 앞 판으로 되돌리고 알린다.";

/** Next 가 읽는 사본의 자리와 빌드가 남긴 원본의 자리. 둘 다 앱 폴더의 `.next` 안이다. */
export function manifestPaths(appDir: string): {
  readonly served: string;
  readonly original: string;
} {
  const dist = join(appDir, ".next");
  return { served: join(dist, MANIFEST_FILE), original: join(dist, ORIGINAL_FILE) };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** `Array.isArray` 는 `any[]` 로 좁혀 타입을 우회하게 되므로 원소를 `unknown` 으로 읽는 판정을 따로 둔다. */
function isList(value: unknown): value is readonly unknown[] {
  return Array.isArray(value);
}

/** 규칙마다의 머리 가운데 `frame-ancestors` 를 정하는 것. 이름은 대소문자를 가리지 않는다. */
function ancestorSlots(root: Record<string, unknown>): readonly Record<string, unknown>[] {
  const rules = root["headers"];
  if (!isList(rules)) {
    return [];
  }
  const slots: Record<string, unknown>[] = [];
  for (const rule of rules) {
    const headers = isRecord(rule) ? rule["headers"] : undefined;
    if (!isList(headers)) {
      continue;
    }
    for (const header of headers) {
      if (!isRecord(header)) {
        continue;
      }
      const { key, value } = header;
      if (
        typeof key === "string" &&
        typeof value === "string" &&
        key.toLowerCase() === "content-security-policy" &&
        value.startsWith("frame-ancestors")
      ) {
        slots.push(header);
      }
    }
  }
  return slots;
}

/**
 * 원본의 글에서 `frame-ancestors` 값 하나만 허용 출처로 바꾼 글. 목록이 비면 값은 그대로 `'none'` 이다. 바꿀 자리가 기대와
 * 다르면 아무것도 바꾸지 않고 까닭을 돌려준다.
 */
export function fillAncestors(
  original: string,
  allowedOrigins: readonly string[],
): { readonly text: string } | { readonly problem: string } {
  let root: unknown;
  try {
    root = JSON.parse(original);
  } catch {
    return { problem: `응답 머리 목록의 원본을 JSON 으로 읽지 못했다.\n${NOT_THE_SITE_FILE}` };
  }
  if (!isRecord(root)) {
    return { problem: `응답 머리 목록의 원본이 객체가 아니다.\n${NOT_THE_SITE_FILE}` };
  }
  const slots = ancestorSlots(root);
  const [slot] = slots;
  if (slot === undefined) {
    return {
      problem: `응답 머리 목록에서 frame-ancestors 를 정하는 자리가 없다.\n${NOT_THE_SITE_FILE}`,
    };
  }
  if (slots.length > 1) {
    const count = slots.length === 2 ? "둘" : `${String(slots.length)}개`;
    return {
      problem: `응답 머리 목록에서 frame-ancestors 를 정하는 자리가 ${count}이다. 값: ${JSON.stringify(slots.map((each) => each["value"]))}\n${NOT_THE_SITE_FILE}`,
    };
  }
  if (slot["value"] !== PLACEHOLDER) {
    return {
      problem: [
        `응답 머리 목록에서 frame-ancestors 를 정하는 자리의 값이 ${PLACEHOLDER} 가 아니다. 찾은 값: ${JSON.stringify(slot["value"])}`,
        "  빌드가 사이트 파일을 읽어 값을 굳힌 산출물이거나 Next 의 판이 올라 모양이 바뀐 것이다.",
        NOT_THE_SITE_FILE,
      ].join("\n"),
    };
  }
  const ancestors = allowedOrigins.length === 0 ? "'none'" : allowedOrigins.join(" ");
  slot["value"] = `frame-ancestors ${ancestors}`;
  return { text: JSON.stringify(root) };
}

/**
 * 서비스 시작이 뜰 때마다 부른다. 원본을 읽어 합친 허용 출처로 바꾼 사본을 Next 가 읽는 자리에 쓴다. 원본이 없거나 바꿀 자리가
 * 기대와 다르면 아무것도 쓰지 않고 까닭을 든 오류를 던진다. 원본은 고치지 않는다.
 */
export function writeServedManifest(
  appDir: string,
  { allowedOrigins }: Pick<RuntimeValuesFile, "allowedOrigins">,
): void {
  const { served, original } = manifestPaths(appDir);
  if (!existsSync(original)) {
    throw new Error(
      `응답 머리 목록의 원본 ${original} 이 없다. 빌드가 원본을 남기지 않은 산출물이다.\n${NOT_THE_SITE_FILE}`,
    );
  }
  const result = fillAncestors(readFileSync(original, "utf-8"), allowedOrigins);
  if ("problem" in result) {
    throw new Error(`응답 머리 목록 ${original} 을 바꾸지 못했다.\n${result.problem}`);
  }
  writeFileSync(served, result.text);
}

/** 빌드가 낸 목록을 원본으로 복사한다. 빌드가 목록을 남기지 않았으면 던진다. */
export function keepOriginal(appDir: string): void {
  const { served, original } = manifestPaths(appDir);
  if (!existsSync(served)) {
    throw new Error(`빌드가 응답 머리 목록을 남기지 않았다: ${served}`);
  }
  copyFileSync(served, original);
}

/**
 * 프로세스가 종료 코드 0 으로 끝날 때 빌드가 낸 목록을 원본으로 남기게 처리기를 등록한다. Next 의 빌드는 이 프로세스의 끝에서
 * 마치므로(위 머리 주석) 등록한 뒤 빌드가 쓴 목록이 복사된다. 복사하지 못하면 종료 코드를 1 로 바꾸고 까닭을 말한다.
 */
export function keepOriginalOnExit(appDir: string): void {
  process.once("exit", (code) => {
    if (code !== 0) {
      return;
    }
    try {
      keepOriginal(appDir);
    } catch (error: unknown) {
      console.error(error instanceof Error ? error.message : String(error));
      process.exitCode = 1;
    }
  });
}
