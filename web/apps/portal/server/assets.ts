// 시작 때 지어 메모리에 쥐는 정적 파일(pilot-portal 명세 "페이지"와 "정적 파일"). 질문 페이지는 `dist` 폴더를 두지 않으므로
// 페이지 스크립트는 `browser/portal.ts` 에서 타입만 벗겨 내고, 토큰 CSS 는 Tailwind CLI 를 자식 프로세스로 돌려 지으며,
// 글꼴은 `@agent-os/ui/fonts` 의 목록을 내용 해시와 함께 표로 든다. 요청을 처리하는 동안에는 파일을 읽지 않는다.
//
// `node:module` 의 `stripTypeScriptTypes` 는 실험 기능이라 첫 호출에 `ExperimentalWarning` 을 낸다. 시작 래퍼가 그 경고만
// 끄고(`--disable-warning=ExperimentalWarning`) 다른 경고는 그대로 둔다. 타입만 지울 수 없는 문법(enum 등)은 던져 시작을 멈춘다.

import { execFile } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync, statSync } from "node:fs";
import { createRequire, stripTypeScriptTypes } from "node:module";
import { basename, dirname, join } from "node:path";
import { promisify } from "node:util";
import { type FontFaceSource, fontFaces, fontFiles } from "@agent-os/ui/fonts";
import type { PortalSite } from "./config.ts";
import { COOKIE_LIFETIME_DAYS } from "./cookie-policy.ts";
import { pageHtml } from "./page.ts";
import { fontPath } from "./paths.ts";

const execFileAsync = promisify(execFile);
const require = createRequire(import.meta.url);
const BROWSER = join(import.meta.dirname, "..", "browser");
const TAILWIND_TIMEOUT_MS = 60_000;
const TAILWIND_OUTPUT_LIMIT = 16 * 1024 * 1024;

/** 메모리의 글로 내는 정적 파일 하나. `etag` 는 본문 해시의 앞 32자를 따옴표로 감싼 값이다. */
export interface StaticText {
  readonly body: string;
  readonly contentType: string;
  readonly etag: string;
}

/** 글꼴 파일 하나. 본문은 읽어 두지 않고 요청 때 `path` 를 흘려 보낸다. */
export interface FontFile {
  readonly path: string;
  readonly etag: string;
  readonly size: number;
}

export interface Assets {
  readonly page: StaticText;
  readonly pageScript: StaticText;
  readonly pageCss: StaticText;
  readonly themeCss: StaticText;
  readonly fontsCss: StaticText;
  /** 파일 이름(경로 없이)에서 글꼴 파일로. 목록 밖 이름은 없다. */
  readonly fonts: ReadonlyMap<string, FontFile>;
}

function etagOf(content: string | Buffer): string {
  return `"${createHash("sha256").update(content).digest("hex").slice(0, 32)}"`;
}

export function staticText(body: string, contentType: string): StaticText {
  return { body, contentType, etag: etagOf(body) };
}

/**
 * 페이지 스크립트의 타입을 벗긴다. 타입만 지울 수 없는 문법이 있으면 까닭을 붙여 던진다. `strip` 방식이라 타입이 있던
 * 자리는 공백이 되어 글자 위치가 그대로 남는다.
 */
export function stripPageScript(source: string): string {
  try {
    return stripTypeScriptTypes(source, { mode: "strip" });
  } catch (error: unknown) {
    const reason = error instanceof Error ? error.message : String(error);
    throw new Error(`페이지 스크립트의 타입만 벗길 수 없다(지원하지 않는 문법): ${reason}`, {
      cause: error,
    });
  }
}

/** 앱의 `browser/portal.ts` 를 벗긴 글. */
export function pageScript(): string {
  return stripPageScript(readFileSync(join(BROWSER, "portal.ts"), "utf-8"));
}

/** 글꼴 CSS. 글꼴 파일은 `/portal/fonts/<이름>` 에서 내므로 `url()` 이 그 길을 가리킨다. */
export function fontsCss(faces: readonly FontFaceSource[]): string {
  return faces
    .map(
      (face) =>
        `@font-face {\n  font-family: '${face.family}';\n  font-style: ${face.style};\n  font-weight: ${face.weight};\n  font-display: swap;\n  src: url("${fontPath(face.file)}") format("woff2");\n  unicode-range: ${face.unicodeRange};\n}\n`,
    )
    .join("");
}

/** 목록의 woff2 마다 내용 해시의 `ETag` 와 크기를 든 표. 시작 때 한 번 읽는다. */
export function fontFileTable(): Map<string, FontFile> {
  const table = new Map<string, FontFile>();
  for (const path of fontFiles()) {
    table.set(basename(path), {
      path,
      etag: etagOf(readFileSync(path)),
      size: statSync(path).size,
    });
  }
  return table;
}

/**
 * 디자인 토큰 CSS(`@agent-os/ui/theme.css`)를 Tailwind CLI 로 지어 메모리에 읽는다. `-o` 를 주지 않아 CSS 가 표준 출력으로
 * 나오고, 앱 폴더에 산출을 쓰지 않는다. 진행 표시는 표준 오류로 가므로 버린다.
 */
export async function themeCss(): Promise<string> {
  const cli = join(dirname(require.resolve("@tailwindcss/cli/package.json")), "dist", "index.mjs");
  const input = require.resolve("@agent-os/ui/theme.css");
  const { stdout } = await execFileAsync(process.execPath, [cli, "-i", input], {
    timeout: TAILWIND_TIMEOUT_MS,
    maxBuffer: TAILWIND_OUTPUT_LIMIT,
    encoding: "utf-8",
  });
  return stdout;
}

const CSS = "text/css; charset=utf-8";

/** 시작 때 정적 파일을 모두 짓는다. 어느 하나라도 못 지으면 던져 서버가 뜨기 전에 멈춘다. */
export async function buildAssets(sites: readonly PortalSite[]): Promise<Assets> {
  return {
    page: staticText(pageHtml(sites, COOKIE_LIFETIME_DAYS), "text/html; charset=utf-8"),
    pageScript: staticText(pageScript(), "text/javascript; charset=utf-8"),
    pageCss: staticText(readFileSync(join(BROWSER, "portal.css"), "utf-8"), CSS),
    themeCss: staticText(await themeCss(), CSS),
    fontsCss: staticText(fontsCss(fontFaces()), CSS),
    fonts: fontFileTable(),
  };
}
