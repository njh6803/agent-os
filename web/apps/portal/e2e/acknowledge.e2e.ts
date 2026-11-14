// 위젯 미리보기 페이지 e2e 의 고지 확인 흐름 사례(pilot-portal 티켓 07 의 몫). 처음 온 브라우저가 덮개에서 확인한 뒤 로그인 없이 질문하는
// 길을 실제 브라우저로 지난다. 토큰 끝점을 실제로 부르는 사례가 여기서 처음이라, 페이지 스크립트(`browser/portal.ts`)와 서버
// (`server/paths.ts`)에 따로 적힌 끝점 경로가 어긋나면 질문에 답이 서지 않아 이 파일이 빨개진다.

import { createHash } from "node:crypto";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { startedRuns } from "@agent-os/e2e-stack";
import { expect, test, type Locator, type Page, type Route } from "@playwright/test";
import { portalOutput, stack, traces } from "./env.ts";
import { SITES, type E2eSite } from "./sites.ts";

const [FIRST, LIMITED] = SITES;
if (FIRST?.notice === undefined || LIMITED === undefined) {
  throw new Error("e2e 사이트가 기대와 다르다. 첫 사이트가 고지 글을 적고 둘째가 있어야 한다");
}
const FIRST_NOTICE = FIRST.notice;

const COVER_TITLE = "질문하기 전에 읽어 주세요";
const ACKNOWLEDGE = "확인하고 질문하기";
const SHORT_NOTICE = "질문과 출력은 기록되고 모델 API로 보내집니다. 개인정보를 넣지 마세요.";
const COOKIE_SENTENCE =
  "이 브라우저를 알아보기 위해 익명 식별자를 쿠키로 둡니다. 쿠키는 마지막으로 질문한 뒤 30일 동안 남습니다.";
const COOKIE_NAME = "portal_anon";
const NO_ACKNOWLEDGEMENT = '{"acknowledged":false}';

function endpoint(site: E2eSite, name: "acknowledgement" | "token"): string {
  return `${stack().portalOrigin}/portal/sites/${site.name}/${name}`;
}

async function open(page: Page, site: E2eSite): Promise<void> {
  await page.goto(`${stack().portalOrigin}/portal/?site=${site.name}`);
}

function cover(page: Page): Locator {
  return page.getByRole("region", { name: COVER_TITLE });
}

function field(page: Page): Locator {
  return page.getByRole("textbox", { name: "질문" });
}

function acknowledgeButton(page: Page): Locator {
  return cover(page).getByRole("button", { name: ACKNOWLEDGE });
}

/**
 * 요청 컨텍스트(브라우저 밖의 Node 요청)는 브라우저 실행 인자의 `*.localhost` 규칙을 받지 못해 이름을 풀지 못한다. 중계는
 * 호스트 이름을 보지 않으므로 같은 포트의 루프백 주소로 보낸다. 브라우저의 쿠키가 필요한 요청에는 쓰지 않는다.
 */
function loopback(url: string): string {
  return url.replace("portal.localhost", "127.0.0.1");
}

/**
 * 위젯 자리(포커스를 받은 상자)에서 Tab 으로 입력창에 닿는다. 첫 Tab 은 위젯 머리의 "새 대화" 단추가 받고 둘째가 입력창이다.
 * 티켓이 적은 "Tab 한 번에"는 이 위젯과 맞지 않아 실제 차례를 고정한다.
 */
async function tabToField(page: Page): Promise<void> {
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "새 대화" })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(field(page)).toBeFocused();
}

async function acknowledge(page: Page, site: E2eSite): Promise<void> {
  await open(page, site);
  await acknowledgeButton(page).click();
  await expect(cover(page)).toBeHidden();
}

async function ask(page: Page, request: string): Promise<void> {
  await field(page).fill(request);
  await page.getByRole("button", { name: "보내기" }).click();
}

function echoed(page: Page, request: string): Locator {
  return page.getByText(`출력: chars:${String(request.length)}`);
}

/** 이 브라우저가 받은 익명 식별자 쿠키의 값. HttpOnly 라 페이지는 읽지 못하고 브라우저 컨텍스트가 읽는다. */
async function cookieValue(page: Page): Promise<string> {
  const cookie = (await page.context().cookies()).find((found) => found.name === COOKIE_NAME);
  expect(cookie).toBeDefined();
  return cookie?.value ?? "";
}

test("처음 온 브라우저에는 덮개가 보이고 짧은 고지가 없으며, 상태 끝점은 거짓이고 확인 전 토큰 끝점은 401이다", async ({
  page,
  request,
}) => {
  await open(page, FIRST);

  await expect(cover(page)).toBeVisible();
  await expect(page.getByText(SHORT_NOTICE)).toBeHidden();
  const status = await request.get(loopback(endpoint(FIRST, "acknowledgement")));
  expect(await status.text()).toBe(NO_ACKNOWLEDGEMENT);
  const token = await request.post(loopback(endpoint(FIRST, "token")));
  expect(token.status()).toBe(401);
});

test("덮개가 나타날 때 포커스를 옮기지 않는다", async ({ page }) => {
  await open(page, FIRST);

  await expect(cover(page)).toBeVisible();
  const stayed = await page.evaluate(() => document.activeElement === document.body);
  expect(stayed).toBe(true);
});

test("사이트의 고지 글이 덮개의 전문이 되고 그 끝에 쿠키 문장이 붙는다", async ({ page }) => {
  await open(page, FIRST);

  const paragraphs = page.locator("#pp-cover-notice p");
  await expect(paragraphs).toHaveText([FIRST_NOTICE, COOKIE_SENTENCE]);
});

test("확인하면 덮개가 걷히고 포커스가 위젯 자리에 서며 Tab 으로 입력창이 포커스를 받아 질문에 답이 선다", async ({
  page,
}) => {
  const request = "anon-subject";
  await open(page, FIRST);
  await acknowledgeButton(page).click();

  await expect(cover(page)).toBeHidden();
  await expect(page.locator("#pp-widget")).toBeFocused();
  await expect(page.getByText(SHORT_NOTICE)).toBeVisible();
  await tabToField(page);

  await ask(page, request);
  await expect(echoed(page, request)).toBeVisible();

  // 트레이스의 주체는 그 브라우저의 쿠키 값에서 낸 이름이고, 그 폴더 어디에도 쿠키 값 원문이 없다.
  const value = await cookieValue(page);
  const hash = createHash("sha256").update(value).digest("hex").slice(0, 32);
  const runs = startedRuns(traces()).filter((run) => run.request === request);
  expect(runs.map((run) => [run.agent, run.principal])).toEqual([
    ["echo", `${FIRST.issuer}|anon-${hash}`],
  ]);
  for (const name of readdirSync(traces())) {
    expect(readFileSync(join(traces(), name), "utf-8")).not.toContain(value);
  }
});

test("확인한 뒤 Tab으로 위젯을 벗어났다가 되돌아오면 입력창이 포커스를 받고 위젯 요소에는 tabindex가 없다", async ({
  page,
}) => {
  await acknowledge(page, FIRST);

  await tabToField(page);
  // 빈 입력창이면 보내기가 쓸 수 없음이라 위젯을 벗어나는 다음 Tab 이 "고지 전문" 단추를 받는다.
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "고지 전문" })).toBeFocused();
  await page.keyboard.press("Shift+Tab");

  await expect(field(page)).toBeFocused();
  await expect(page.locator("agent-os-widget")).not.toHaveAttribute("tabindex", /.*/u);
});

test("확인한 뒤 새로 고치면 덮개 없이 이어서 질문한다", async ({ page }) => {
  await acknowledge(page, FIRST);

  await page.reload();

  await expect(field(page)).toBeVisible();
  await expect(cover(page)).toBeHidden();
  await expect(page.getByText(SHORT_NOTICE)).toBeVisible();
});

test("확인한 뒤 쿠키를 지우고 질문하면 위젯이 로그인 정보를 받지 못했다고 알린다", async ({
  page,
}) => {
  await acknowledge(page, FIRST);

  await page.context().clearCookies();
  await ask(page, "cookie-cleared");

  await expect(page.getByText("로그인 정보를 받지 못했습니다.")).toBeVisible();
});

test("다른 출처 페이지의 폼 POST는 403이고 그 뒤에도 확인이 없으며, 같은 출처의 확인은 204다", async ({
  page,
}) => {
  const sent = page.waitForResponse(
    (response) =>
      response.url() === endpoint(FIRST, "acknowledgement") &&
      response.request().method() === "POST",
  );
  await page.goto(`${stack().otherOrigin}/`);
  await page.getByRole("button", { name: "고지를 확인했다고 보낸다" }).click();

  expect((await sent).status()).toBe(403);
  // 브라우저가 직접 연다. 쿠키가 섰다면 이 탐색에 실려 참이 나온다.
  const status = await page.goto(endpoint(FIRST, "acknowledgement"));
  expect(await status?.text()).toBe(NO_ACKNOWLEDGEMENT);
  const cookies = await page.context().cookies();
  expect(cookies.filter((cookie) => cookie.name === COOKIE_NAME)).toEqual([]);

  // 양성 대조. 같은 출처의 확인은 받아들여져 쿠키가 선다. 쿠키가 없다는 것만으로는 서버의 거절인지 브라우저의 거부인지 가르지 못한다.
  await open(page, FIRST);
  // 끝점 경로가 어긋나도 응답이 잡혀 상태 코드가 값으로 드러나도록 이름이 같은 접두까지 받는다.
  const same = page.waitForResponse(
    (response) =>
      response.url().startsWith(endpoint(FIRST, "acknowledgement")) &&
      response.request().method() === "POST",
  );
  await acknowledgeButton(page).click();
  expect((await same).status()).toBe(204);
});

test("사이트의 시간당 실행 수 상한을 넘긴 둘째 요청은 거부되어 위젯이 상한 알림을 보인다", async ({
  page,
}) => {
  const first = "limit-first";
  await acknowledge(page, LIMITED);

  await ask(page, first);
  await expect(echoed(page, first)).toBeVisible();
  await ask(page, "limit-second");

  await expect(page.getByText(/뒤에 다시 보낼 수 있습니다\./u).first()).toBeVisible();
});

/** 그 사이트의 확인 끝점 요청을 가로챈다. 메서드별로 처리기가 나누고, 처리하지 않는 요청은 그대로 서버로 보낸다. */
async function intercept(
  page: Page,
  site: E2eSite,
  handler: (method: string, route: Route) => Promise<boolean>,
): Promise<void> {
  await page.route(endpoint(site, "acknowledgement"), async (route) => {
    if (!(await handler(route.request().method(), route))) {
      await route.continue();
    }
  });
}

test("상태를 묻는 답이 늦으면 뼈대가 보이고 답이 오면 덮개로 바뀐다", async ({ page }) => {
  let release = (): void => undefined;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await intercept(page, FIRST, async (method) => {
    if (method === "GET") {
      await held;
    }
    return false;
  });

  await open(page, FIRST);

  const skeleton = page.getByLabel("고지 확인 여부를 묻는 중");
  await expect(skeleton).toBeVisible();
  await expect(cover(page)).toBeHidden();
  release();
  await expect(cover(page)).toBeVisible();
  await expect(skeleton).toBeHidden();
});

test("고지 전문 단추를 누르면 전문이 아래로 펼쳐지고 다시 누르면 접힌다", async ({ page }) => {
  await acknowledge(page, FIRST);
  const toggle = page.getByRole("button", { name: "고지 전문" });
  const full = page.locator("#pp-notice-full");
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(full).toBeHidden();

  await toggle.click();

  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await expect(full).toBeVisible();
  await expect(full.locator("p")).toHaveText([FIRST_NOTICE, COOKIE_SENTENCE]);
  await toggle.click();
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(full).toBeHidden();
});

test("확인을 기록하지 못하면 위험 알림이 뜨고 단추를 다시 눌러 기록할 수 있다", async ({
  page,
}) => {
  let failNext = true;
  await intercept(page, FIRST, async (method, route) => {
    if (method === "POST" && failNext) {
      failNext = false;
      await route.fulfill({ status: 500 });
      return true;
    }
    return false;
  });
  await open(page, FIRST);

  await acknowledgeButton(page).click();

  const alert = cover(page).getByRole("alert");
  await expect(alert).toContainText("고지 확인을 기록하지 못했습니다.");
  await expect(alert).toContainText("잠시 뒤 다시 눌러 주세요.");
  await expect(cover(page)).toBeVisible();
  await acknowledgeButton(page).click();
  await expect(cover(page)).toBeHidden();
  await expect(page.getByText(SHORT_NOTICE)).toBeVisible();
});

test("기록하는 동안 단추를 다시 눌러도 확인 요청은 한 번만 간다", async ({ page }) => {
  let posts = 0;
  let release = (): void => undefined;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await intercept(page, FIRST, async (method) => {
    if (method === "POST") {
      posts += 1;
      await held;
    }
    return false;
  });
  await open(page, FIRST);
  const button = acknowledgeButton(page);

  await button.click();
  await expect(button).toHaveAttribute("aria-busy", "true");
  // 쓸 수 없음으로 읽히는 단추라 강제로 눌러야 두 번째 누름이 페이지에 닿는다.
  await button.click({ force: true });
  release();

  await expect(cover(page)).toBeHidden();
  expect(posts).toBe(1);
});

test("위젯 미리보기 페이지 프로세스의 출력에 쿠키 값과 토큰이 없다", async ({ page }) => {
  const request = "output-check";
  const issued = page.waitForResponse(
    (response) =>
      response.url() === endpoint(FIRST, "token") && response.request().method() === "POST",
  );
  await acknowledge(page, FIRST);
  await ask(page, request);
  await expect(echoed(page, request)).toBeVisible();

  const token = await (await issued).text();
  const value = await cookieValue(page);
  expect(token.split(".")).toHaveLength(3);
  const output = portalOutput();
  // 양성 대조. 출력을 모으지 못해 비어 있어도 "없다"는 초록이라, 시작 로그 한 줄이 있는 것을 함께 본다.
  expect(output).toContain("에 섰다");
  expect(output).not.toContain(value);
  expect(output).not.toContain(token);
});
