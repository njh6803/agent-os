// 파일 종류마다 맞대는 값의 테스트(design-reverse-sync 명세 "기록"의 2026-10-22 주석의 넷째, "맞대는 것"의
// 2026-10-22 주석). 기록, `pending`, 확인이 모두 이 값으로 맞댄다. README 의 생성 몫 가르기는 페이지 스크립트를
// 옮긴 것이라 실제 꼴(임시 아티팩트에서 받은 시험 자료)과 그 스크립트의 갈래로 본다.

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, expect, test } from "vitest";
import { buildTokensJson } from "./build.ts";
import { fileHash, humanPart, isRecorded } from "./file-hash.ts";
import { comparisonHash, readTokens } from "./tokens-json.ts";

const WEB = dirname(dirname(import.meta.dirname));
const CSS = readFileSync(join(WEB, "packages", "ui", "src", "styles", "theme.css"), "utf-8");

// 아래 머리 둘, 안내 문장, manifest 의 판(3)은 디자인 시스템 아티팩트의 판 1792715827-ef57 에서 받은 `app.js` 의
// 문자열과 같다(손으로 봤다, 일지 2026-10-27-01 의 "셀프 리뷰" 절). 시험 자료에 없는 생성 몫이라 거기서 옮겼다.
const CONSUMING = "## Consuming this system (generated — do not edit)";
const QUICK_START = "## Quick start (generated from tokens.json — do not edit)";
const READ_FIRST =
  "Read this README first; the manifest below lists the files to read and every asset — read tokens.css or components/bundle.js only if the page you build uses them, and read_asset an asset id only if you need that asset.";
const SEPARATOR = "\n\n---\n\n";
const FENCE = "```";
const MANIFEST_BLOCK = `${FENCE}json\n{\n  "manifestVersion": 3\n}\n${FENCE}\n`;

const HUMAN = "# 디자인 시스템\n\n사람이 쓴 몫이다.\n";

function bytes(text: string): Uint8Array {
  return new TextEncoder().encode(text);
}

function sha256(data: Uint8Array): string {
  return createHash("sha256").update(data).digest("hex");
}

describe("README 의 사람 몫", () => {
  test("구분선 뒤에 생성 머리 Consuming 이 오면 구분선 앞까지가 사람 몫이다", () => {
    expect(humanPart(`${HUMAN}${SEPARATOR}${CONSUMING}\n\n생성 몫\n`)).toBe(HUMAN);
  });

  test("구분선 뒤에 생성 머리 Quick start 가 와도 구분선 앞까지가 사람 몫이다", () => {
    expect(humanPart(`${HUMAN}${SEPARATOR}${QUICK_START}\n\n생성 몫\n`)).toBe(HUMAN);
  });

  test("파일 머리가 생성 머리면 통째로 생성 몫이다", () => {
    expect(humanPart(`${CONSUMING}\n\n생성 몫\n`)).toBe("");
    expect(humanPart(`${QUICK_START}\n\n생성 몫\n`)).toBe("");
  });

  test("구분선 없이 글 가운데 놓인 생성 머리에서는 자르지 않는다", () => {
    const text = `${HUMAN}\n${CONSUMING}\n`;
    expect(humanPart(text)).toBe(text);
  });

  test("생성 머리가 없는 구분선은 사람 몫의 일부다", () => {
    const text = `${HUMAN}${SEPARATOR}## 사람이 쓴 다음 절\n`;
    expect(humanPart(text)).toBe(text);
  });

  test("구분선 뒤 읽기 안내와 manifest 블록으로 끝나면 그 구분선에서 자른다", () => {
    expect(humanPart(`${HUMAN}${SEPARATOR}${READ_FIRST}\n\n${MANIFEST_BLOCK}`)).toBe(HUMAN);
  });

  test("manifest 블록 뒤에 다시 생성 몫이 오면 그 앞 구분선에서 자른다", () => {
    const text = `${HUMAN}${SEPARATOR}${MANIFEST_BLOCK}${SEPARATOR}${CONSUMING}\n`;
    expect(humanPart(text)).toBe(HUMAN);
  });

  test("manifest 블록 뒤에 사람의 글이 이어지면 그 구분선에서 자르지 않는다", () => {
    const text = `${HUMAN}${SEPARATOR}${MANIFEST_BLOCK}\n사람이 더 쓴 글\n`;
    expect(humanPart(text)).toBe(text);
  });

  test("CRLF 줄 끝의 구분선도 알아본다", () => {
    expect(humanPart(`${HUMAN}\r\n\r\n---\r\n\r\n${CONSUMING}\r\n`)).toBe(HUMAN);
  });

  test("페이지가 저장하며 생성 몫을 붙인 실제 README 는 올린 사람 몫 238 바이트로 돌아온다", () => {
    // 임시 아티팩트의 판 1792671359-792c 에서 받은 README 다. 올린 README 는 238 바이트였고 Artifact 도구가 낸
    // sha256 의 머리가 5813ed60 이었다(.scratch/design-reverse-sync/probes/README.md).
    const saved = readFileSync(join(import.meta.dirname, "fixtures", "page-saved-README.md"));
    const human = bytes(humanPart(saved.toString("utf-8")));

    expect(human.byteLength).toBe(238);
    expect(sha256(human).startsWith("5813ed60")).toBe(true);
    expect(fileHash("project/README.md", saved)).toBe(sha256(human));
  });
});

describe("맞대는 값", () => {
  test("뿌리 README 는 사람 몫의 sha256 이라 생성 몫만 붙은 것과 같다", () => {
    const uploaded = fileHash("project/README.md", bytes(HUMAN));
    expect(fileHash("project/README.md", bytes(`${HUMAN}${SEPARATOR}${CONSUMING}\n생성\n`))).toBe(
      uploaded,
    );
    expect(fileHash("project/README.md", bytes(`${HUMAN}더 쓴 줄\n`))).not.toBe(uploaded);
  });

  test("컴포넌트의 README 는 바이트의 sha256 이다. 페이지는 뿌리 README 에만 생성 몫을 붙인다", () => {
    const text = `${HUMAN}${SEPARATOR}${CONSUMING}\n`;
    expect(fileHash("project/components/Button/README.md", bytes(text))).toBe(sha256(bytes(text)));
  });

  test("tokens.json 은 맞대는 몫의 값이라 페이지가 꼴만 다시 쓴 것과 같다", () => {
    const built = buildTokensJson(CSS);
    const parsed: unknown = JSON.parse(built);
    const compact = JSON.stringify(parsed);

    expect(fileHash("project/tokens.json", bytes(built))).toBe(comparisonHash(readTokens(parsed)));
    expect(fileHash("project/tokens.json", bytes(compact))).toBe(
      fileHash("project/tokens.json", bytes(built)),
    );
  });

  test("JSON 으로 풀리지 않는 tokens.json 은 바이트의 sha256 이다", () => {
    const broken = bytes("{ 깨진");
    expect(fileHash("project/tokens.json", broken)).toBe(sha256(broken));
  });

  test("다른 파일은 바이트의 sha256 이다", () => {
    const data = bytes("<html></html>\n");
    expect(fileHash("project/foundations/colors/index.html", data)).toBe(sha256(data));
  });
});

describe("기록에 드는 경로", () => {
  test.each([
    ["project/tokens.json", true],
    ["project/README.md", true],
    ["project/components/Button/README.md", true],
    ["project/api/notes.md", true],
    ["project/api/components/nested/Button.md", true],
    ["project/sync-record.json", false],
    ["project/design-system.json", false],
    ["project/tokens.css", false],
    ["project/manifest.json", false],
    ["project/api/tokens.md", false],
    ["project/api/icons.md", false],
    ["project/api/tokens/color.md", false],
    ["project/api/components/Button.md", false],
    ["project/api/assets/notes.md", false],
    ["artifact-type/app.js", false],
    ["index.html", false],
  ] as const)("%s 는 기록에 드는가: %s", (path, recorded) => {
    expect(isRecorded(path)).toBe(recorded);
  });
});
