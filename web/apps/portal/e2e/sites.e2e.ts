// 위젯 미리보기 페이지 e2e 의 사이트 바꾸기와 보증 모드 사례(pilot-portal 티켓 08 의 몫). 셀렉트로 사이트를 바꾸면 위젯이 그 사이트의
// 설정으로 다시 그려지고, 로그인 사이트와 둘 다 사이트가 제 모습을 보이며, 다크 모드 스위치와 보고서 링크가 화면에 서는 것을
// 실제 브라우저로 지난다. 고지 확인 흐름 자체는 `acknowledge.e2e.ts` 가 본다.

import { expect, test, type Locator, type Page, type Route } from "@playwright/test";
import { stack } from "./env.ts";
import { SITES, type E2eSite } from "./sites.ts";

const [FIRST, LIMITED, EITHER, GATED] = SITES;
if (
  FIRST?.reportUrl === undefined ||
  LIMITED === undefined ||
  EITHER?.reportUrl === undefined ||
  GATED === undefined
) {
  throw new Error("e2e 사이트가 기대와 다르다. 첫째와 셋째가 보고서 주소를 적고 넷이 있어야 한다");
}
const FIRST_REPORT = FIRST.reportUrl;
const EITHER_REPORT = EITHER.reportUrl;

const COVER_TITLE = "질문하기 전에 읽어 주세요";
const ACKNOWLEDGE = "확인하고 질문하기";
const SHORT_NOTICE = "질문과 출력은 기록되고 모델 API로 보내집니다. 개인정보를 넣지 마세요.";
const SWITCHED = "사이트를 바꿔 새 대화로 시작합니다.";
const LOGIN_TITLE = "이 사이트는 로그인이 필요합니다.";
const LOGIN_BODY = "로그인은 아직 제공하지 않습니다.";
const LOGIN_BUTTON = "로그인하고 질문하기";
const LOGIN_NOTE = "로그인은 아직 제공하지 않습니다. 지금은 로그인 없이 질문할 수 있습니다.";
const REPORT = "이 에이전트의 평가 보고서";

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

function siteSelect(page: Page): Locator {
  return page.getByLabel("사이트", { exact: true });
}

function darkSwitch(page: Page): Locator {
  return page.getByRole("switch", { name: "다크 모드" });
}

function widget(page: Page): Locator {
  return page.locator("agent-os-widget");
}

function note(page: Page): Locator {
  return page.getByRole("status").getByText(SWITCHED);
}

function reportLink(page: Page): Locator {
  return page.getByRole("link", { name: REPORT });
}

function echoed(page: Page, request: string): Locator {
  return page.getByText(`출력: chars:${String(request.length)}`);
}

async function chooseSite(page: Page, site: E2eSite): Promise<void> {
  await siteSelect(page).selectOption(site.name);
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

/** 앞서 보낸 응답이 페이지의 처리기에 닿을 틈을 준다. 늦게 온 답이 화면을 덮지 않는 것처럼 "일어나지 않는 일"을 볼 때 쓴다. */
async function settle(page: Page): Promise<void> {
  await page.evaluate(
    () =>
      new Promise<void>((resolve) => {
        requestAnimationFrame(() => {
          requestAnimationFrame(() => {
            resolve();
          });
        });
      }),
  );
}

/** 그 사이트의 상태 끝점(GET)에 주어진 답을 한 번 준다. */
async function answerStatus(
  page: Page,
  site: E2eSite,
  fulfill: (route: Route) => Promise<void>,
): Promise<void> {
  await page.route(endpoint(site, "acknowledgement"), async (route) => {
    if (route.request().method() === "GET") {
      await fulfill(route);
    } else {
      await route.continue();
    }
  });
}

// ---- 사이트 바꾸기 ---------------------------------------------------------------------------------------------

test("사이트가 여럿이면 라벨 사이트와 셀렉트가 있고 항목은 사이트마다 하나이며 고른 사이트가 골라져 있다", async ({
  page,
}) => {
  await open(page, LIMITED);

  const select = siteSelect(page);
  await expect(select).toBeVisible();
  await expect(select.locator("option")).toHaveText(SITES.map((site) => site.heading));
  await expect(select).toHaveValue(LIMITED.name);
});

test("셀렉트로 바꾸면 위젯이 그 사이트의 설정으로 다시 그려지고 주소와 제목이 따라 바뀐다", async ({
  page,
}) => {
  await open(page, FIRST);
  await expect(widget(page)).toHaveAttribute("heading", FIRST.heading);

  await chooseSite(page, LIMITED);

  await expect(widget(page)).toHaveAttribute("heading", LIMITED.heading);
  await expect(widget(page)).toHaveAttribute("theme", LIMITED.theme);
  await expect(widget(page)).not.toHaveAttribute("intro", /.*/u);
  await expect(page.locator("html")).toHaveAttribute("data-theme", LIMITED.theme);
  await expect(page.locator("#pp-heading")).toHaveText(LIMITED.heading);
  await expect(page).toHaveTitle(LIMITED.heading);
  await expect(page).toHaveURL(`${stack().portalOrigin}/portal/?site=${LIMITED.name}`);
  await expect(siteSelect(page)).toHaveValue(LIMITED.name);
});

test("확인한 사이트에서 확인한 다른 사이트로 바꾸면 앞 대화가 없고 정보 글이 보인다", async ({
  page,
}) => {
  const before = "before-switch";
  await acknowledge(page, LIMITED);
  await acknowledge(page, FIRST);
  await ask(page, before);
  await expect(echoed(page, before)).toBeVisible();

  await chooseSite(page, LIMITED);

  // 위젯이 저장한 대화를 되돌릴 차례를 마친 뒤(입력창이 켜진 뒤)에도 앞 사이트의 대화가 보이지 않는다.
  await expect(field(page)).toBeEnabled();
  await expect(echoed(page, before)).toHaveCount(0);
  await expect(cover(page)).toBeHidden();
  await expect(page.getByText(SHORT_NOTICE)).toBeVisible();
  await expect(note(page)).toBeVisible();
});

test("확인한 사이트에서 확인하지 않은 사이트로 바꾸면 덮개가 보이고 위젯과 짧은 고지가 없다", async ({
  page,
}) => {
  await acknowledge(page, FIRST);

  await chooseSite(page, LIMITED);

  await expect(cover(page)).toBeVisible();
  await expect(field(page)).toHaveCount(0);
  await expect(page.getByText(SHORT_NOTICE)).toBeHidden();
  await expect(note(page)).toBeVisible();
});

test("사이트를 바꾼 뒤의 정보 글은 role status 이고 다음 사이트 바꾸기에 거둬졌다 다시 서며 첫 요청을 보낼 때 거둬진다", async ({
  page,
}) => {
  await acknowledge(page, LIMITED);
  await acknowledge(page, FIRST);
  await expect(page.locator("#pp-switched")).toHaveAttribute("role", "status");
  await expect(note(page)).toHaveCount(0);

  await chooseSite(page, LIMITED);
  await expect(note(page)).toBeVisible();
  await page
    .locator("#pp-switched > *")
    .first()
    .evaluate((line) => {
      line.setAttribute("data-seen", "first-switch");
    });

  // 다음 사이트 바꾸기는 있던 글을 거두고 새 글을 세운다(화면 읽기 프로그램이 새 글로 읽는다).
  await chooseSite(page, FIRST);
  await expect(note(page)).toBeVisible();
  await expect(page.locator("#pp-switched > [data-seen]")).toHaveCount(0);

  await expect(field(page)).toBeEnabled();
  await ask(page, "first-request");
  await expect(echoed(page, "first-request")).toBeVisible();
  await expect(page.locator("#pp-switched")).toBeEmpty();
});

test("사이트를 바꾼 뒤 위젯이 저장한 대화를 되돌리려고 토큰을 불러도 정보 글은 거두지 않는다", async ({
  page,
}) => {
  await acknowledge(page, LIMITED);
  await acknowledge(page, FIRST);
  await ask(page, "restore-token");
  await expect(echoed(page, "restore-token")).toBeVisible();
  const issued = page.waitForResponse(
    (response) =>
      response.url() === endpoint(LIMITED, "token") && response.request().method() === "POST",
  );

  await chooseSite(page, LIMITED);

  // 저장한 대화가 있어 위젯은 붙자마자 토큰을 받아 묶음을 견준다. 사람이 요청을 보낸 것이 아니다.
  expect((await issued).status()).toBe(200);
  await expect(field(page)).toBeEnabled();
  await expect(note(page)).toBeVisible();
});

test("쿠키를 잃어 저장한 대화만 남은 브라우저가 다시 확인하면 입력창이 열려 질문에 답이 선다", async ({
  page,
}) => {
  await acknowledge(page, FIRST);
  await ask(page, "before-cookie-loss");
  await expect(echoed(page, "before-cookie-loss")).toBeVisible();

  // 덮개 뒤에 숨은 위젯이 저장한 대화를 되돌리려고 토큰을 받다 401을 받는다. 확인한 뒤에도 그 위젯이 남으면 입력창이 막힌다.
  await page.context().clearCookies();
  await page.reload();
  await expect(cover(page)).toBeVisible();
  await acknowledgeButton(page).click();

  await expect(field(page)).toBeEnabled();
  await ask(page, "after-ack");
  await expect(echoed(page, "after-ack")).toBeVisible();
});

// ---- 상태를 묻는 일 -------------------------------------------------------------------------------------------

test("상태를 묻는 답이 200이 아니면 확인하지 않은 것으로 읽어 덮개를 보인다", async ({ page }) => {
  await answerStatus(page, FIRST, async (route) => {
    await route.fulfill({ status: 503 });
  });

  await open(page, FIRST);

  await expect(cover(page)).toBeVisible();
  await expect(field(page)).toHaveCount(0);
  await expect(page.getByText(SHORT_NOTICE)).toBeHidden();
});

test("상태를 묻다 연결이 끊기면 확인하지 않은 것으로 읽어 덮개를 보인다", async ({ page }) => {
  await answerStatus(page, FIRST, async (route) => {
    await route.abort();
  });

  await open(page, FIRST);

  await expect(cover(page)).toBeVisible();
  await expect(page.getByText(SHORT_NOTICE)).toBeHidden();
});

test("로그인 사이트는 상태를 묻지 않으므로 상태 끝점의 실패가 로그인 알림과 겹치지 않는다", async ({
  page,
}) => {
  const asked: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes("/acknowledgement")) {
      asked.push(request.url());
    }
  });

  await open(page, GATED);

  await expect(page.getByText(LOGIN_TITLE)).toBeVisible();
  await expect(cover(page)).toBeHidden();
  expect(asked).toEqual([]);
});

test("앞 사이트의 늦게 온 상태 답은 지금 화면을 덮지 못한다", async ({ page }) => {
  let release = (): void => undefined;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  let fulfilled = (): void => undefined;
  const answered = new Promise<void>((resolve) => {
    fulfilled = resolve;
  });
  await answerStatus(page, FIRST, async (route) => {
    await held;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: '{"acknowledged":true}',
    });
    fulfilled();
  });
  await open(page, FIRST);
  await chooseSite(page, LIMITED);
  await expect(cover(page)).toBeVisible();

  release();
  await answered;
  await settle(page);

  // 앞 사이트가 확인했다고 늦게 답해도 지금 화면은 확인하지 않은 둘째 사이트의 덮개다.
  await expect(cover(page)).toBeVisible();
  await expect(page.getByText(SHORT_NOTICE)).toBeHidden();
  await expect(siteSelect(page)).toHaveValue(LIMITED.name);
});

test("앞 사이트의 늦게 온 확인 기록은 지금 화면을 덮지 못하고 포커스를 옮기지 못한다", async ({
  page,
}) => {
  let release = (): void => undefined;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route(endpoint(FIRST, "acknowledgement"), async (route) => {
    if (route.request().method() === "POST") {
      await held;
    }
    await route.continue();
  });
  await open(page, FIRST);
  const recorded = page.waitForResponse(
    (response) =>
      response.url() === endpoint(FIRST, "acknowledgement") &&
      response.request().method() === "POST",
  );
  await acknowledgeButton(page).click();
  await chooseSite(page, LIMITED);
  await expect(cover(page)).toBeVisible();

  release();
  expect((await recorded).status()).toBe(204);
  await settle(page);

  await expect(cover(page)).toBeVisible();
  await expect(page.locator("#pp-widget")).not.toBeFocused();
  await expect(page.getByText(SHORT_NOTICE)).toBeHidden();
});

// ---- 보증 모드별 모습 ----------------------------------------------------------------------------------------

test("로그인 사이트는 위젯 요소 없이 정보 알림을 보이고 짧은 고지와 덮개가 없다", async ({
  page,
}) => {
  await open(page, GATED);

  const alert = page.getByRole("status").filter({ hasText: LOGIN_TITLE });
  await expect(alert).toBeVisible();
  await expect(alert).toContainText(LOGIN_BODY);
  await expect(widget(page)).toHaveCount(0);
  await expect(cover(page)).toBeHidden();
  await expect(page.getByText(SHORT_NOTICE)).toBeHidden();
  await expect(page.getByRole("button", { name: LOGIN_BUTTON })).toHaveCount(0);
  // 알림 상자는 위젯 자리와 같은 크기다.
  const box = await page.locator("#pp-widget").boundingBox();
  expect(box?.height).toBe(560);
  expect(box?.width).toBe(400);
});

test("익명 사이트에서 로그인 사이트로 바꾸면 위젯이 사라지고 다시 익명 사이트로 바꾸면 새 위젯이 선다", async ({
  page,
}) => {
  await acknowledge(page, FIRST);
  await expect(widget(page)).toHaveCount(1);

  await chooseSite(page, GATED);
  await expect(page.getByText(LOGIN_TITLE)).toBeVisible();
  await expect(widget(page)).toHaveCount(0);
  await expect(page.getByText(SHORT_NOTICE)).toBeHidden();
  await expect(note(page)).toBeVisible();

  await chooseSite(page, FIRST);
  await expect(page.getByText(LOGIN_TITLE)).toBeHidden();
  await expect(field(page)).toBeVisible();
  await expect(widget(page)).toHaveCount(1);
});

test("둘 다 사이트는 익명 흐름에 더해 위젯 자리 위에 쓸 수 없는 단추와 그 바로 뒤의 글을 보인다", async ({
  page,
}) => {
  await open(page, EITHER);

  const button = page.getByRole("button", { name: LOGIN_BUTTON });
  await expect(button).toBeDisabled();
  await expect(button.locator("xpath=following-sibling::*[1]")).toHaveText(LOGIN_NOTE);
  const above = await button.boundingBox();
  const place = await page.locator("#pp-widget").boundingBox();
  expect((above?.y ?? Infinity) + (above?.height ?? 0)).toBeLessThanOrEqual(place?.y ?? 0);
  // 넓은 창(Playwright 의 기본 1280px)에서는 글이 단추 옆 같은 줄에 놓인다.
  const note = await page.getByText(LOGIN_NOTE).boundingBox();
  expect(note?.y ?? Infinity).toBeLessThan((above?.y ?? 0) + (above?.height ?? 0));
  expect(note?.x ?? 0).toBeGreaterThanOrEqual((above?.x ?? Infinity) + (above?.width ?? 0));
  // 익명 흐름은 그대로다. 확인하면 위젯이 서고 단추 줄도 남는다.
  await expect(cover(page)).toBeVisible();
  await acknowledgeButton(page).click();
  await expect(field(page)).toBeVisible();
  await expect(button).toBeDisabled();
  await expect(page.getByText(LOGIN_NOTE)).toBeVisible();
});

test("둘 다 사이트의 쓸 수 없는 단추는 포커스를 받지 않아 Tab 이 셀렉트, 스위치, 덮개의 단추로 간다", async ({
  page,
}) => {
  await open(page, EITHER);
  await expect(cover(page)).toBeVisible();

  await page.keyboard.press("Tab");
  await expect(siteSelect(page)).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(darkSwitch(page)).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(acknowledgeButton(page)).toBeFocused();
});

test("익명 사이트와 로그인 사이트에는 둘 다 사이트의 단추 줄이 없다", async ({ page }) => {
  await open(page, FIRST);
  await expect(page.getByRole("button", { name: LOGIN_BUTTON })).toHaveCount(0);

  await chooseSite(page, EITHER);
  await expect(page.getByRole("button", { name: LOGIN_BUTTON })).toBeVisible();

  await chooseSite(page, GATED);
  await expect(page.getByRole("button", { name: LOGIN_BUTTON })).toHaveCount(0);
});

// ---- 다크 모드 스위치와 보고서 링크 ------------------------------------------------------------------------------

test("다크 모드 스위치의 처음 값은 그 사이트의 모드이고 켜고 끄면 뿌리와 위젯의 모드가 함께 바뀐다", async ({
  page,
}) => {
  await acknowledge(page, FIRST);
  const root = page.locator("html");
  // 첫 사이트의 모드가 dark 라 스위치가 켜져 있다.
  await expect(darkSwitch(page)).toBeChecked();
  await expect(page.locator("#pp-mode-state")).toHaveText("켜짐");
  await expect(root).toHaveAttribute("data-mode", "dark");
  await expect(widget(page)).toHaveAttribute("mode", "dark");

  await darkSwitch(page).click();

  await expect(darkSwitch(page)).not.toBeChecked();
  await expect(page.locator("#pp-mode-state")).toHaveText("꺼짐");
  await expect(root).toHaveAttribute("data-mode", "light");
  await expect(widget(page)).toHaveAttribute("mode", "light");
  // 위젯 요소가 속성을 읽어 제 모드로 옮긴다.
  await expect(widget(page)).toHaveAttribute("data-mode", "light");

  await darkSwitch(page).click();
  await expect(root).toHaveAttribute("data-mode", "dark");
  await expect(widget(page)).toHaveAttribute("mode", "dark");
  await expect(widget(page)).toHaveAttribute("data-mode", "dark");
});

test("모드를 적지 않은 사이트의 스위치는 시스템 설정에서 시작하고 사이트를 바꾸면 그 사이트의 값으로 돌아간다", async ({
  page,
}) => {
  await open(page, LIMITED);
  const root = page.locator("html");
  await expect(darkSwitch(page)).not.toBeChecked();
  await expect(root).not.toHaveAttribute("data-mode", /.*/u);

  await darkSwitch(page).click();
  await expect(root).toHaveAttribute("data-mode", "dark");
  await expect(widget(page)).toHaveAttribute("mode", "dark");

  await chooseSite(page, FIRST);
  await expect(darkSwitch(page)).toBeChecked();
  await expect(widget(page)).toHaveAttribute("mode", "dark");
  await darkSwitch(page).click();
  await expect(widget(page)).toHaveAttribute("mode", "light");

  // 저장하지 않는다. 사이트를 바꿔 돌아오면 그 사이트의 값이다.
  await chooseSite(page, LIMITED);
  await expect(darkSwitch(page)).not.toBeChecked();
  await expect(root).not.toHaveAttribute("data-mode", /.*/u);
  await chooseSite(page, FIRST);
  await expect(darkSwitch(page)).toBeChecked();
  await expect(root).toHaveAttribute("data-mode", "dark");
});

test("보고서 주소를 적은 사이트에는 새 탭으로 열리는 링크가 있고 적지 않은 사이트에는 없다", async ({
  page,
}) => {
  await open(page, FIRST);
  await expect(reportLink(page)).toHaveAttribute("href", FIRST_REPORT);
  await expect(reportLink(page)).toHaveAttribute("target", "_blank");
  await expect(reportLink(page)).toHaveAttribute("rel", /noopener/u);
  // 바깥 링크 아이콘은 꾸밈이라 링크의 이름에 들지 않는다.
  await expect(reportLink(page).locator("svg")).toHaveAttribute("aria-hidden", "true");

  await chooseSite(page, LIMITED);
  await expect(reportLink(page)).toHaveCount(0);

  await chooseSite(page, EITHER);
  await expect(reportLink(page)).toHaveAttribute("href", EITHER_REPORT);

  await chooseSite(page, GATED);
  await expect(reportLink(page)).toHaveCount(0);
});

test("시스템 설정이 어두운 브라우저에서 모드를 적지 않은 사이트의 스위치는 켜진 채 시작한다", async ({
  page,
}) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await open(page, LIMITED);

  await expect(darkSwitch(page)).toBeChecked();
  await expect(page.locator("#pp-mode-state")).toHaveText("켜짐");
});

test("읽는 차례는 셀렉트, 다크 모드 스위치, 위젯 안의 단추, 고지 전문 단추, 보고서 링크다", async ({
  page,
}) => {
  await acknowledge(page, FIRST);
  await page.reload();
  await expect(field(page)).toBeVisible();

  await page.keyboard.press("Tab");
  await expect(siteSelect(page)).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(darkSwitch(page)).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "새 대화" })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(field(page)).toBeFocused();
  // 빈 입력창이면 보내기가 쓸 수 없음이라 다음 Tab 이 위젯을 벗어난다.
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "고지 전문" })).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(reportLink(page)).toBeFocused();
});

// ---- 사이트 하나 ----------------------------------------------------------------------------------------------

test("설정에 사이트 하나만 적은 위젯 미리보기 페이지에는 셀렉트도 라벨 사이트도 없고 스위치는 있다", async ({
  page,
}) => {
  await page.goto(`${stack().secondOrigin}/portal/`);

  // 스크립트가 돌아 사이트를 골랐는지 먼저 본다. 그래야 "없다"가 스크립트가 돌기 전의 빈 화면이 아니다.
  await expect(page.locator("#pp-heading")).toHaveText(FIRST.heading);
  await expect(page).toHaveTitle(FIRST.heading);
  await expect(page.getByText("사이트", { exact: true })).toHaveCount(0);
  await expect(page.locator("select")).toHaveCount(0);
  await expect(darkSwitch(page)).toBeVisible();
  await expect(cover(page)).toBeVisible();
});
