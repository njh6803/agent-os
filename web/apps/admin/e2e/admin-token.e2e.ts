// 읽기 흐름의 첫 조각. 관리 토큰을 넣고 플러그인 목록을 본다(web-admin 티켓 05). 실행 목록과 실행 하나는 runs.e2e.ts 가 잇는다.
// 그 흐름 뒤에 설정에서 고른 테마가 새로 고친 첫 그림부터 그려지는지 본다(admin-style 티켓 09).
// 실제 serve, 시작 래퍼로 띄운 실제 next start, 실제 중계(rewrites)를 지난다. 준비는 stack.ts 다.

import { expect, type Page, test } from "@playwright/test";
import { stack } from "./env";
import { clearTokens, enterAdminToken, openSection, row } from "./screen";

const TOKEN_FIELD_SEEN = "e2e: 관리 토큰 칸이 문서에 붙었다";
/** 운영자가 고른 테마를 남기는 localStorage 키(admin-style 명세 "저장"). 앱이 그 저장소에 남기는 유일한 것이다. 토큰은 거기 없다. */
const THEME_KEY = "agent-os-admin-theme";
/** 초기화 스크립트가 프레임마다 문서 뿌리의 테마를 적는 window 의 자리. */
const THEME_FRAMES = "__e2eThemeFrames";

/** 그 탭의 브라우저 저장소 둘에 든 키와 값 전부. */
function storedEntries(
  page: Page,
): Promise<{ local: [string, string][]; session: [string, string][] }> {
  return page.evaluate(() => {
    const entries = (storage: Storage): [string, string][] => {
      const found: [string, string][] = [];
      for (let index = 0; index < storage.length; index += 1) {
        const key = storage.key(index);
        if (key !== null) {
          found.push([key, storage.getItem(key) ?? ""]);
        }
      }
      return found;
    };
    return { local: entries(localStorage), session: entries(sessionStorage) };
  });
}

/** 값에 그 글자가 든 항목. */
function containing(entries: [string, string][], text: string): [string, string][] {
  return entries.filter(([, value]) => value.includes(text));
}

interface ThemeFrame {
  readonly now: number;
  readonly theme: string | null;
}

/**
 * 초기화 스크립트. 문서가 생기자마자 `requestAnimationFrame` 고리를 걸어 프레임마다 그 시각과 문서 뿌리의 `data-theme` 을
 * 적는다(.scratch/admin-style/probes/prepaint_theme.mjs 의 기록기를 줄였다). 페이지를 읽을 때마다 새로 건다.
 */
function recordThemeFrames(slot: string): void {
  const frames: ThemeFrame[] = [];
  Object.defineProperty(window, slot, { value: frames });
  const frame = (): void => {
    frames.push({
      now: performance.now(),
      theme: document.documentElement.getAttribute("data-theme"),
    });
    requestAnimationFrame(frame);
  };
  requestAnimationFrame(frame);
}

/**
 * 첫 그림의 테마. 첫 그림은 `first-paint` 항목의 `paintTime` 이고 그 시각보다 앞선 마지막 프레임의 속성이 그 그림의
 * 테마다. `startTime` 은 거칠게 잘려 쓰지 않는다. 그 값으로는 첫 그림 뒤에 단 갈래가 앞으로 판정됐다(같은 프로브).
 */
function firstPaintTheme(
  page: Page,
  slot: string,
): Promise<{ paintTime: number | null; framesBefore: number; theme: string | null }> {
  return page.evaluate((frameSlot) => {
    const isFrame = (value: unknown): value is ThemeFrame =>
      typeof value === "object" &&
      value !== null &&
      "now" in value &&
      typeof value.now === "number" &&
      "theme" in value &&
      (typeof value.theme === "string" || value.theme === null);
    const paint = performance.getEntriesByType("paint").find(({ name }) => name === "first-paint");
    const paintTime: unknown = paint === undefined ? null : Reflect.get(paint, "paintTime");
    const recorded: unknown = Reflect.get(window, frameSlot);
    if (typeof paintTime !== "number" || !Array.isArray(recorded)) {
      return { paintTime: null, framesBefore: 0, theme: null };
    }
    const before = recorded.filter(isFrame).filter(({ now }) => now <= paintTime);
    return { paintTime, framesBefore: before.length, theme: before.at(-1)?.theme ?? null };
  }, slot);
}

test("관리 토큰을 넣으면 종류별로 묶인 플러그인 목록이 보이고 새로 고쳐도 남는다", async ({
  page,
}) => {
  const { adminUrl, adminToken } = stack();
  const printed: string[] = [];
  const crashes: string[] = [];
  page.on("console", (message) => printed.push(`${message.type()} ${message.text()}`));
  page.on("pageerror", (error) => crashes.push(error.message));
  // 문서가 읽히는 동안 관리 토큰 넣는 칸이 한 번이라도 붙으면 콘솔에 남긴다. 페이지를 읽을 때마다 새로 건다. 칸은
  // 운영자가 보는 이름(라벨)으로 찾는다. 라벨은 칸을 감싸지 않고 `for` 로 잇는다(디자인 시스템의 TextField, admin-style
  // 티켓 03). 채널 토큰의 칸도 가린 입력이고, 관리 토큰이 있으면 설정 화면에 선다(admin-style 티켓 04).
  await page.addInitScript((marker) => {
    let seen = false;
    const adminTokenField = (): boolean =>
      Array.from(document.querySelectorAll("label")).some(
        (label) =>
          label.textContent === "관리 토큰" &&
          label.control instanceof HTMLInputElement &&
          label.control.type === "password",
      );
    new MutationObserver(() => {
      if (!seen && adminTokenField()) {
        seen = true;
        console.debug(marker);
      }
    }).observe(document, { childList: true, subtree: true });
  }, TOKEN_FIELD_SEEN);

  await page.goto(adminUrl);
  await enterAdminToken(page, "e2e-a-token-the-server-refuses");
  // Next 가 두는 경로 알림도 alert 라 글자로 거른다.
  await expect(page.getByRole("alert").filter({ hasText: "관리 토큰이 거부됐다" })).toBeVisible();

  await enterAdminToken(page, adminToken);

  await expect(row(page, "에이전트", "echo")).toContainText("켜짐");
  await expect(row(page, "에이전트", "broken")).toContainText("읽을 수 없는 매니페스트");
  await expect(row(page, "MCP", "fixture")).toContainText("켜짐");
  await expect(row(page, "스킬", "summarize")).toContainText("꺼짐");
  await expect(row(page, "스킬", "summarize")).toContainText("로더가 생기기 전에는 효과가 없다");
  await expect(row(page, "모델", "sonnet")).toContainText("로더가 생기기 전에는 효과가 없다");

  const beforeReload = printed.length;
  await page.reload();
  await expect(row(page, "에이전트", "echo")).toBeVisible();
  await expect(page.getByLabel("관리 토큰", { exact: true })).toHaveCount(0);
  // 토큰을 가진 운영자가 새로 고칠 때 넣는 칸이 번쩍이지 않는다. 서버가 미리 그린 HTML 에도 없다.
  expect(printed.slice(beforeReload).filter((line) => line.includes(TOKEN_FIELD_SEEN))).toEqual([]);

  const stored = await storedEntries(page);
  // 토큰은 localStorage 에 없다. 그 저장소에 남을 수 있는 키는 이 브라우저의 테마 하나다.
  expect(containing(stored.local, adminToken)).toEqual([]);
  expect(stored.local.map(([key]) => key).filter((key) => key !== THEME_KEY)).toEqual([]);
  expect(containing(stored.session, adminToken)).toHaveLength(1);
  expect(page.url()).not.toContain(adminToken);
  expect(await page.content()).not.toContain(adminToken);
  expect(printed.join("\n")).not.toContain(adminToken);
  expect(printed.slice(0, beforeReload).some((line) => line.includes(TOKEN_FIELD_SEEN))).toBe(true);
  // 서버가 그린 첫 그림과 브라우저의 첫 그림이 어긋나면(hydration) 여기에 잡힌다.
  expect(crashes).toEqual([]);
  expect(printed.filter((line) => line.startsWith("error") && !line.includes("401"))).toEqual([]);

  await clearTokens(page);
  await expect(page.getByLabel("관리 토큰", { exact: true })).toBeVisible();
  const cleared = await storedEntries(page);
  expect(containing(cleared.session, adminToken)).toEqual([]);
});

test("설정에서 고른 쪽빛은 새로 고쳐도 첫 그림부터 쪽빛이고 다른 화면으로 옮겨도 남는다", async ({
  page,
}) => {
  const { adminUrl, adminToken } = stack();
  const html = page.locator("html");
  await page.addInitScript(recordThemeFrames, THEME_FRAMES);
  await page.goto(adminUrl);
  await enterAdminToken(page, adminToken);
  await openSection(page, "설정");

  await page.getByRole("radio", { name: "쪽빛", exact: true }).check();
  await expect(html).toHaveAttribute("data-theme", "jjokbit");

  await page.reload();
  // 본문은 하이드레이션 뒤에만 선다(관리 토큰은 이 탭의 sessionStorage 에 남아 있다).
  await expect(page.getByRole("heading", { level: 1, name: "설정" })).toBeVisible();
  await page.waitForFunction(() =>
    performance.getEntriesByType("paint").some(({ name }) => name === "first-paint"),
  );
  const first = await firstPaintTheme(page, THEME_FRAMES);
  expect(first.paintTime, "first-paint 의 paintTime").not.toBeNull();
  expect(first.framesBefore, "첫 그림보다 앞선 프레임").toBeGreaterThan(0);
  expect(first.theme, "첫 그림의 테마").toBe("jjokbit");
  await expect(html).toHaveAttribute("data-theme", "jjokbit");
  await expect(page.getByRole("radio", { name: "쪽빛", exact: true })).toBeChecked();

  await openSection(page, "플러그인");
  await expect(row(page, "에이전트", "echo")).toBeVisible();
  await expect(html).toHaveAttribute("data-theme", "jjokbit");

  const stored = await storedEntries(page);
  expect(stored.local).toEqual([[THEME_KEY, "jjokbit"]]);
  expect(containing(stored.session, adminToken)).toHaveLength(1);
});
