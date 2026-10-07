// 사진 비교가 Storybook 정적 빌드를 여는 길. 사진(stories.visual.ts)과 미디어 특성(media.visual.ts)이 함께 쓴다.
// - 정적 빌드(`../storybook-static`)를 `http://storybook.invalid/` 로 route 해 파일에서 낸다. 그 밖의 요청은 abort 하고
//   세며, 하나라도 있으면 테스트가 실패한다. 측정에서 0 이었고 로컬 컨테이너는 네트워크 없이 돈다(ADR 0026).
// - 스토리를 열면 play 와 afterEach(클래스 판정, axe)가 끝날 때까지 기다린다. 정적 빌드도 play 를 돌리므로 그 전에
//   찍으면 그림이 그 순간에 달린다.
// - 판정 스토리(태그 `judgment`)는 색인에서 뺀다. 태그는 정적 빌드의 `index.json` 항목에 그대로 실린다. 기본 테마가
//   아닌 테마에서 값을 재는 스토리도 그 태그를 단다(사진은 기본 테마만, ADR 0026 의 2026-10-06 이력).
import { existsSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { test as base, expect, type Page } from "@playwright/test";
import { DEFAULT_THEME, type ThemeKey } from "../src/themes.ts";

const SITE = join(import.meta.dirname, "..", "storybook-static");
const ORIGIN = "http://storybook.invalid";
const JUDGMENT_TAG = "judgment";

export interface StoryEntry {
  readonly id: string;
  readonly tags: readonly string[];
}

function isStoryEntry(value: unknown): value is StoryEntry {
  return (
    typeof value === "object" &&
    value !== null &&
    "type" in value &&
    value.type === "story" &&
    "id" in value &&
    typeof value.id === "string" &&
    "tags" in value &&
    Array.isArray(value.tags) &&
    value.tags.every((tag) => typeof tag === "string")
  );
}

/** 정적 빌드의 스토리 가운데 판정 스토리가 아닌 것. 정적 빌드가 없으면 던진다. */
export function photographedStories(): StoryEntry[] {
  const index = join(SITE, "index.json");
  if (!existsSync(index)) {
    throw new Error(`정적 빌드가 없다: ${index}. build-storybook 을 먼저 친다`);
  }
  const data: unknown = JSON.parse(readFileSync(index, "utf-8"));
  if (typeof data !== "object" || data === null || !("entries" in data)) {
    throw new Error("index.json 에 entries 가 없다");
  }
  const entries: unknown = data.entries;
  if (typeof entries !== "object" || entries === null) {
    throw new Error("index.json 의 entries 가 객체가 아니다");
  }
  return Object.values(entries)
    .filter(isStoryEntry)
    .filter((entry) => !entry.tags.includes(JUDGMENT_TAG));
}

/** 스토리가 globals 로 모드를 정하지 않았을 때 찍는 모드. 테마는 기본 테마(먹)다(ADR 0026 의 2026-10-06 이력). */
export const MODES = ["light", "dark"] as const;
export type Mode = (typeof MODES)[number];

/** 미리보기의 globals(`src/storybook/preview.tsx`). URL 의 `globals=` 로 넘긴다. */
export interface Globals {
  readonly theme: ThemeKey;
  readonly mode: Mode | "system";
  readonly shadow: "off" | "on";
}

/** 기본 테마의 그 모드로 문서에 그리는 globals. */
export function muk(mode: Mode): Globals {
  return { theme: DEFAULT_THEME, mode, shadow: "off" };
}

export interface Storybook {
  /**
   * 스토리를 열고 play 와 afterEach 가 끝날 때까지 기다린다. 스토리가 globals 를 정했으면 그 값이 URL 의 값을 이긴다.
   * 그리다 예외가 나 오류 화면이 뜨면 실패한다. play 의 실패는 정적 빌드에서 오류 화면을 띄우지 않아(변이로 봤다) 여기서
   * 가르지 않는다. 그것은 스토리 테스트가 본다.
   */
  open(id: string, globals: Globals): Promise<void>;
}

function renderFinished(): boolean {
  if (!("__STORYBOOK_PREVIEW__" in window)) {
    return false;
  }
  const preview = window.__STORYBOOK_PREVIEW__;
  if (typeof preview !== "object" || preview === null || !("currentRender" in preview)) {
    return false;
  }
  const render = preview.currentRender;
  return (
    typeof render === "object" &&
    render !== null &&
    "phase" in render &&
    render.phase === "finished"
  );
}

async function open(page: Page, id: string, { theme, mode, shadow }: Globals) {
  const query = `theme:${theme};mode:${mode};shadow:${shadow}`;
  await page.goto(`${ORIGIN}/iframe.html?id=${id}&viewMode=story&globals=${query}`);
  // Storybook 10.6.1 의 렌더 단계는 playing → played → completing → completed → afterEach → finished 다(설치본의
  // preview 런타임을 읽었다). 그리다 예외가 나도 finished 로 끝나고 오류 화면을 띄운다.
  await page.waitForFunction(renderFinished);
  await expect(page.locator("body.sb-show-errordisplay")).toHaveCount(0);
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
}

export const test = base.extend<{ storybook: Storybook }>({
  storybook: async ({ page }, use) => {
    const outside: string[] = [];
    await page.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      if (url.origin !== ORIGIN) {
        outside.push(url.href);
        await route.abort();
        return;
      }
      const path = join(SITE, decodeURIComponent(url.pathname));
      if (!existsSync(path) || statSync(path).isDirectory()) {
        await route.fulfill({ status: 404 });
        return;
      }
      await route.fulfill({ path });
    });
    await use({ open: (id, globals) => open(page, id, globals) });
    expect(outside, "정적 빌드 밖으로 나간 요청").toEqual([]);
  },
});

export { expect };
