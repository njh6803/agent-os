// 사진 비교가 Storybook 정적 빌드를 여는 길(`@agent-os/ui/visual`). 디자인 시스템 패키지와 위젯이 함께 쓴다(web-widget
// 명세 "위젯 앱의 배치와 빌드"의 사진 비교). 정적 빌드의 자리는 쓰는 쪽이 넘기고, 판정은 둘이 같다.
// - 정적 빌드를 `http://storybook.invalid/` 로 route 해 파일에서 낸다. 그 밖의 요청은 abort 하고 세며, 하나라도 있으면
//   테스트가 실패한다. 측정에서 0 이었고 로컬 컨테이너는 네트워크 없이 돈다(ADR 0026).
// - 스토리를 열면 렌더가 끝날 때까지(play 와 afterEach 의 클래스 판정과 axe) 기다린다. 정적 빌드도
//   play 를 돌리므로 그 전에 찍으면 그림이 그 순간에 달린다. 다만 play 의 `userEvent` 는 빈 객체다. Storybook 10.6.1 은
//   `navigator.clipboard` 가 있을 때만 그것을 채우는데(설치본 `dist/csf/index.js` 의 enhanceContext), 이 출처는 보안
//   맥락이 아니라 clipboard 가 없다. 그래서 그 `userEvent` 를 부르는 play 는 늦어도 첫 호출에서 TypeError 로
//   멈추고(프로브 .scratch/design-system/probes/static_play.mjs) 사진은 그 전의 그림이다. play 가 그렇게 던져도 미리보기의
//   기본값 `throwPlayFunctionExceptions: false` 라 예외는 콘솔에만 찍히고, 렌더는 errored 뒤 afterEach 까지 이어진다(같은
//   프로브가 렌더 단계의 차례를 적었다). 실제 입력의 상태는 패키지의 stories.visual.ts 의 INTERACTIONS 가 찍는다.
//   `userEvent` 가 빈 것은 패키지의 storybook.visual.ts 가 고정한다.
// - 판정 스토리(태그 `judgment`)는 색인에서 뺀다. 태그는 정적 빌드의 `index.json` 항목에 그대로 실린다. 기본 테마가
//   아닌 테마에서 값을 재는 스토리도 그 태그를 단다(사진은 기본 테마만, ADR 0026 의 2026-10-06 이력).
//
// `@playwright/test` 는 타입만 들인다. 쓰는 쪽이 자기 `test` 를 넘긴다. 로컬의 사진 비교는 쓰는 쪽에 깔린 Playwright 만
// 컨테이너에 복사하고(web/tools/visual.ts), 이 파일이 놓인 패키지의 pnpm 링크는 컨테이너 안에서 풀리지 않는다.
import { existsSync, readFileSync, statSync } from "node:fs";
import { join, sep } from "node:path";
import type { Page, test as playwrightTest } from "@playwright/test";
import { DEFAULT_THEME, type Density, type ThemeKey } from "../src/themes.ts";

export const ORIGIN = "http://storybook.invalid";
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

/** 정적 빌드(`site`)의 스토리 가운데 판정 스토리가 아닌 것. 정적 빌드가 없으면 던진다. */
export function photographedStories(site: string): StoryEntry[] {
  const index = join(site, "index.json");
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

/** 스토리가 globals 로 모드를 정하지 않았을 때 찍는 모드. 테마는 기본 테마(녹청)다(ADR 0026 의 2026-10-06 이력). */
export const MODES = ["light", "dark"] as const;
export type Mode = (typeof MODES)[number];

/** 미리보기의 globals(`src/storybook/preview.tsx`). URL 의 `globals=` 로 넘긴다. */
export interface Globals {
  readonly theme: ThemeKey;
  readonly mode: Mode | "system";
  /** auto 면 속성을 두지 않아 창의 폭을 따른다. */
  readonly density: Density | "auto";
  readonly shadow: "off" | "on";
}

/** 기본 테마의 그 모드와 밀도로 문서에 그리는 globals. */
export function inDefaultTheme(mode: Mode, density: Density): Globals {
  return { theme: DEFAULT_THEME, mode, density, shadow: "off" };
}

export interface Storybook {
  /**
   * 스토리를 열고 렌더가 끝날 때까지(play 와 afterEach) 기다린다. 스토리가 globals 를 정했으면 그
   * 값이 URL 의 값을 이긴다.
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

async function open(page: Page, id: string, { theme, mode, density, shadow }: Globals) {
  const query = `theme:${theme};mode:${mode};density:${density};shadow:${shadow}`;
  await page.goto(`${ORIGIN}/iframe.html?id=${id}&viewMode=story&globals=${query}`);
  // Storybook 10.6.1 의 렌더 단계는 playing → played → completing → completed → afterEach → finished 다(설치본의
  // preview 런타임을 읽었다). play 가 던지면 played 대신 errored 이고 나머지는 같다(프로브 static_play.mjs 가 적었다).
  // 그리다 예외가 나도 finished 로 끝나고 오류 화면을 띄운다.
  await page.waitForFunction(renderFinished);
  if ((await page.locator("body.sb-show-errordisplay").count()) > 0) {
    throw new Error(`스토리 ${id} 를 그리다 예외가 나 오류 화면이 떴다`);
  }
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
}

/**
 * 쓰는 쪽의 `test` 에 정적 빌드(`site`)를 여는 `storybook` 픽스처를 더한다. 쓰는 쪽은 자기 `@playwright/test` 의 `test`
 * 를 넘긴다.
 */
export function storybookTest(base: typeof playwrightTest, site: string) {
  return base.extend<{ storybook: Storybook }>({
    storybook: async ({ page }, use) => {
      const outside: string[] = [];
      await page.route("**/*", async (route) => {
        const url = new URL(route.request().url());
        if (url.origin !== ORIGIN) {
          outside.push(url.href);
          await route.abort();
          return;
        }
        // 인코딩한 `/` 는 URL 파서가 접지 않아 디코딩한 경로가 정적 빌드 밖을 가리킬 수 있다(패키지의 storybook.visual.ts).
        const path = join(site, decodeURIComponent(url.pathname));
        if (!path.startsWith(site + sep) || !existsSync(path) || statSync(path).isDirectory()) {
          await route.fulfill({ status: 404 });
          return;
        }
        await route.fulfill({ path });
      });
      await use({ open: (id, globals) => open(page, id, globals) });
      if (outside.length > 0) {
        throw new Error(`정적 빌드 밖으로 나간 요청: ${outside.join(", ")}`);
      }
    },
  });
}
