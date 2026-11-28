// 읽기 흐름의 첫 조각. 로그인 화면으로 들어가 플러그인 목록을 보고, 로그아웃하고, 설정에서 고른 테마가 첫 그림부터 그려지는지
// 본다(admin-login 티켓 09, 앞은 web-admin 티켓 05, 테마는 admin-style 티켓 09). 대화 목록과 대화 하나는 chat.e2e.ts 와 reading.e2e.ts 가 잇는다.
// 실제 serve, 시작 래퍼로 띄운 실제 next start, 실제 중계(rewrites)를 지난다. 준비는 stack.ts 이고, 계정은 준비가 `agent-os
// operator system-admin` 으로 만든 것이다.

import { expect, type Page, test } from "@playwright/test";
import { stack } from "./env";
import { logIn, openSection, row, signInTo } from "./screen";

/** 운영자가 고른 테마를 남기는 localStorage 키(admin-style 명세 "저장"). 앱이 그 저장소에 남기는 유일한 것이다. */
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

test("로그인하지 않고 열면 로그인 화면으로 가고, 틀린 비밀번호는 거절되며, 맞으면 처음 열던 화면에서 플러그인 목록이 보이고 새로 고쳐도 남는다", async ({
  page,
  context,
}) => {
  const { adminUrl, accountName, accountPassword } = stack();
  const printed: string[] = [];
  const crashes: string[] = [];
  page.on("console", (message) => printed.push(`${message.type()} ${message.text()}`));
  page.on("pageerror", (error) => crashes.push(error.message));

  await page.goto(adminUrl);
  await expect(page).toHaveURL(`${adminUrl}/login?next=%2F`);
  await expect(page.getByRole("heading", { level: 1, name: "로그인", exact: true })).toBeVisible();

  await logIn(page, accountName, "e2e-a-password-the-server-refuses");
  // Next 가 두는 경로 알림도 alert 라 글자로 거른다. 거절되면 비밀번호 칸만 비고 이름은 남는다.
  await expect(page.getByRole("alert").filter({ hasText: "로그인하지 못했다" })).toBeVisible();
  await expect(page.getByLabel("비밀번호", { exact: true })).toHaveValue("");
  await expect(page.getByLabel("계정 이름", { exact: true })).toHaveValue(accountName);

  await logIn(page);

  await expect(page).toHaveURL(`${adminUrl}/`);
  await expect(row(page, "에이전트", "echo")).toContainText("켜짐");
  await expect(row(page, "에이전트", "broken")).toContainText("읽을 수 없는 매니페스트");
  await expect(row(page, "MCP", "fixture")).toContainText("켜짐");
  await expect(row(page, "스킬", "summarize")).toContainText("꺼짐");
  await expect(row(page, "스킬", "summarize")).not.toContainText(
    "로더가 생기기 전에는 효과가 없다",
  );
  await expect(row(page, "모델", "sonnet")).not.toContainText("로더가 생기기 전에는 효과가 없다");
  // 계정 자리에 이름과 단계가 보인다.
  await expect(page.getByRole("button", { name: new RegExp(accountName) })).toContainText(
    "시스템 관리자",
  );

  await page.reload();
  await expect(row(page, "에이전트", "echo")).toBeVisible();
  await expect(page.getByLabel("계정 이름", { exact: true })).toHaveCount(0);
  // 이미 로그인한 채 로그인 화면을 열면 첫 화면으로 돌아온다.
  await page.goto(`${adminUrl}/login`);
  await expect(page).toHaveURL(`${adminUrl}/`);

  // 로그인은 쿠키 둘이 들고(HttpOnly 에 Secure) 화면의 스크립트는 읽지 못한다. 브라우저 저장소와 주소와 문서와 콘솔에는
  // 비밀번호가 없다. 저장소에 남을 수 있는 키는 이 브라우저의 테마 하나다.
  const cookies = await context.cookies();
  const login = cookies.filter(({ name }) => name.startsWith("__Host-aos_"));
  expect(login.map(({ name }) => name).toSorted()).toEqual(["__Host-aos_at", "__Host-aos_rt"]);
  expect(login.every(({ httpOnly, secure }) => httpOnly && secure)).toBe(true);
  expect(await page.evaluate(() => document.cookie)).not.toContain("aos_");
  const stored = await storedEntries(page);
  expect(stored.local.map(([key]) => key).filter((key) => key !== THEME_KEY)).toEqual([]);
  expect(stored.session).toEqual([]);
  expect(page.url()).not.toContain(accountPassword);
  expect(await page.content()).not.toContain(accountPassword);
  expect(printed.join("\n")).not.toContain(accountPassword);
  // 서버가 그린 첫 그림과 브라우저의 첫 그림이 어긋나면(hydration) 여기에 잡힌다. 로그인 전의 401 은 이 흐름이 받는 것이다.
  expect(crashes).toEqual([]);
  expect(
    printed.filter(
      (line) => line.startsWith("error") && !line.includes("401") && !line.includes("429"),
    ),
  ).toEqual([]);
});

test("로그아웃하면 로그아웃했다는 알림과 함께 로그인 화면으로 가고 그 뒤에는 화면을 열 때마다 로그인을 요구한다", async ({
  page,
}) => {
  const { adminUrl, accountName } = stack();
  await signInTo(page, adminUrl);
  await expect(row(page, "에이전트", "echo")).toBeVisible();

  await page.getByRole("button", { name: new RegExp(accountName) }).click();
  await page.getByRole("menuitem", { name: "로그아웃", exact: true }).click();

  await expect(page).toHaveURL(`${adminUrl}/login?notice=logged-out`);
  await expect(page.getByText("로그아웃했다", { exact: true })).toBeVisible();
  await page.goto(`${adminUrl}/chat`);
  await expect(page).toHaveURL(`${adminUrl}/login?next=%2Fchat`);
});

test("설정에서 고른 쪽빛은 새로 고쳐도 첫 그림부터 쪽빛이고 다른 화면으로 옮겨도 남는다", async ({
  page,
}) => {
  const { adminUrl } = stack();
  const html = page.locator("html");
  await page.addInitScript(recordThemeFrames, THEME_FRAMES);
  await signInTo(page, adminUrl);
  await openSection(page, "설정");

  await page.getByRole("radio", { name: "쪽빛", exact: true }).check();
  await expect(html).toHaveAttribute("data-theme", "jjokbit");

  await page.reload();
  // 본문은 로그인한 계정을 읽은 뒤에만 선다.
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
  expect(stored.session).toEqual([]);
});
