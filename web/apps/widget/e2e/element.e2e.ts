// 위젯 e2e 의 페이지 안 사례(web-widget 티켓 10). 준비(stack.ts)가 띄운 실제 serve·위젯 Next·같은 출처의 중계 앞에서,
// 다른 출처의 사이트 페이지(element-site.ts)가 번들 script 한 줄과 `<agent-os-widget>` 하나로 위젯을 넣는다. 번들은 준비의
// 위젯 빌드가 시작 래퍼로 짓는다(tools/element.ts).
//
// Playwright 의 위치 지정자는 open shadow root 안까지 찾는다. 그래서 위젯의 화면을 페이지에서 바로 찾는다.

import { expect, type Locator, type Page, test } from "@playwright/test";
import { elementCsp } from "./element-site";
import { stack } from "./env";
import { loopback, recordRequests, send } from "./helpers";

/** 그 페이지의 console.error 글을 모은다. */
function consoleErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      errors.push(message.text());
    }
  });
  return errors;
}

/** 위젯의 첫 화면이 서고 그때 받기 시작한 글꼴이 다 올 때까지 기다린다. */
async function settled(page: Page, agent: string): Promise<void> {
  await expect(page.getByRole("heading", { name: agent })).toBeVisible();
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
}

function output(page: Page, text: string): Locator {
  // 화면 읽기 알림(status)도 같은 글을 싣는다. 대화 목록의 출력 문단으로 좁힌다.
  return page.getByRole("region", { name: "대화" }).getByText(`출력: ${text}`, { exact: true });
}

/** 그 문서에 받아 온 글꼴의 family 이름. */
function loadedFamilies(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const loaded: string[] = [];
    document.fonts.forEach((face) => {
      if (face.status === "loaded") {
        loaded.push(face.family);
      }
    });
    return loaded;
  });
}

/** 위젯 안 요소 하나의 크기와 글자에 관한 계산값. */
function measure(locator: Locator) {
  return locator.evaluate((element) => {
    const style = getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    return {
      width: rect.width,
      height: rect.height,
      fontFamily: style.fontFamily,
      fontSize: style.fontSize,
      lineHeight: style.lineHeight,
      letterSpacing: style.letterSpacing,
      wordSpacing: style.wordSpacing,
      color: style.color,
      padding: style.padding,
      backgroundColor: style.backgroundColor,
    };
  });
}

/**
 * 위젯의 크기. 글자 폭에 기대는 요소(제목, 보내기)는 높이만 본다. 호스트는 상자의 크기만 본다. 호스트는 사이트의 light
 * DOM 에 있어 글자 크기·글자 간격 같은 상속 속성을 바깥 문서에서 그대로 물려받고, 글자를 그리는 것은 그 값을 다시 정하는
 * 감싼 요소 아래다(디자인 토큰 CSS 의 `[data-ui-root]`).
 */
async function widgetLayout(page: Page) {
  return {
    host: await page.locator("agent-os-widget").evaluate((element) => {
      const rect = element.getBoundingClientRect();
      return { width: rect.width, height: rect.height };
    }),
    root: await measure(page.locator("[data-ui-root]")),
    heading: { ...(await measure(page.getByRole("heading", { name: "echo" }))), width: null },
    field: await measure(page.getByRole("textbox", { name: "요청" })),
    button: { ...(await measure(page.getByRole("button", { name: "보내기" }))), width: null },
  };
}

/** 사이트 쪽 요소의 계산값과 문서의 시트 수. 위젯의 CSS 가 새면 바뀐다. */
function siteStyles(page: Page) {
  return page.evaluate(() => {
    const pick = (element: Element | null) => {
      if (element === null) {
        return null;
      }
      const style = getComputedStyle(element);
      return {
        fontFamily: style.fontFamily,
        fontSize: style.fontSize,
        lineHeight: style.lineHeight,
        letterSpacing: style.letterSpacing,
        color: style.color,
        backgroundColor: style.backgroundColor,
        padding: style.padding,
        margin: style.margin,
        borderTopWidth: style.borderTopWidth,
        boxSizing: style.boxSizing,
      };
    };
    return {
      html: pick(document.documentElement),
      body: pick(document.body),
      text: pick(document.getElementById("site-text")),
      button: pick(document.getElementById("site-button")),
      sheets: document.styleSheets.length,
      adopted: document.adoptedStyleSheets.length,
    };
  });
}

test("허용 출처의 페이지에서 script 한 줄로 실린 위젯이 번들 출처의 최종 사용자 경로로 요청 하나를 결말까지 보낸다", async ({
  page,
}) => {
  const { siteOrigin, widgetOrigin } = stack();
  const requests = recordRequests(page);
  const errors = consoleErrors(page);
  await page.goto(`${siteOrigin}/element?agent=echo`);
  await settled(page, "echo");

  await send(page, "element");

  await expect(output(page, "chars:7")).toBeVisible();
  // 사이트 스크립트는 요소가 정의되기 전에 토큰 함수를 대입했다. 업그레이드가 그것을 옮겨 담아 한 번 불렀다.
  await expect(page.locator("body")).toHaveAttribute("data-token-calls", "1");
  const endUser = requests.filter((request) =>
    request.url().startsWith(`${widgetOrigin}/end-user/`),
  );
  expect(
    endUser.map((request) => `${request.method()} ${new URL(request.url()).pathname}`),
  ).toEqual(["POST /end-user/runs"]);
  const host = page.locator("agent-os-widget");
  expect(await host.evaluate((element) => element.shadowRoot?.mode)).toBe("open");
  await expect(host).toHaveAttribute("data-density", "regular");
  expect(errors.filter((error) => error.includes("위젯"))).toEqual([]);
});

test('crossorigin="anonymous" 를 붙인 script 로도 번들이 실린다', async ({ page }) => {
  const { siteOrigin, widgetOrigin } = stack();
  const bundle = page.waitForResponse(
    (response) => response.url() === `${widgetOrigin}/widget/element.js`,
  );
  await page.goto(`${siteOrigin}/element?agent=echo&crossorigin=1`);

  const response = await bundle;
  expect(response.headers()["access-control-allow-origin"]).toBe("*");
  await settled(page, "echo");
  await send(page, "cors");
  await expect(output(page, "chars:4")).toBeVisible();
});

test("document.currentScript 가 이름 있는 요소에 가려진 페이지에서는 그 출처로 아무것도 보내지 않고 위험 알림을 보인다", async ({
  page,
}) => {
  const { siteOrigin, widgetOrigin, otherOrigin } = stack();
  const requests = recordRequests(page);
  const errors = consoleErrors(page);
  await page.goto(`${siteOrigin}/element?agent=echo&clobber=1`);

  await expect(page.getByText("위젯 설정이 올바르지 않습니다.")).toBeVisible();
  await expect(page.getByRole("textbox", { name: "요청" })).toBeDisabled();
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
  // 가린 요소가 실제로 그 자리에 섰다.
  expect(
    await page.evaluate(() => {
      const found: unknown = document.currentScript;
      return found instanceof HTMLImageElement;
    }),
  ).toBe(true);
  await expect
    .poll(() => errors.filter((error) => error.includes("document.currentScript")).length)
    .toBe(1);
  await expect(page.locator("body")).toHaveAttribute("data-token-calls", "0");
  // 가린 출처로 간 것은 사이트가 둔 그 이미지 하나다. 글꼴도 토큰도 요청도 가지 않았다.
  expect(
    requests
      .filter((request) => request.url().startsWith(`${otherOrigin}/`))
      .map((request) => `${request.resourceType()} ${new URL(request.url()).pathname}`),
  ).toEqual(["image /clobber"]);
  // 위젯 출처로 간 것은 번들 하나다. 기준 주소가 없으면 글꼴을 등록하지 않는다.
  expect(
    requests
      .filter((request) => request.url().startsWith(`${widgetOrigin}/`))
      .map((request) => new URL(request.url()).pathname),
  ).toEqual(["/widget/element.js"]);
});

test("페이지 안 방식의 CORS 는 허용 출처의 페이지에서 읽히고 허용 밖 출처의 페이지에서 읽히지 않는다", async ({
  page,
}) => {
  const { siteOrigin, otherOrigin, widgetOrigin } = stack();
  await page.goto(`${otherOrigin}/element?agent=echo`);
  await settled(page, "echo");

  await send(page, "cors");

  await expect(page.getByText("요청을 처리하지 못했습니다.")).toBeVisible();
  // 토큰은 받았다. 막은 것은 브라우저가 읽은 CORS 다.
  await expect(page.locator("body")).toHaveAttribute("data-token-calls", "1");
  await expect(page.getByText("chars:", { exact: false })).toHaveCount(0);

  const preflight = (origin: string) =>
    page.request.fetch(`${loopback(widgetOrigin)}/end-user/runs`, {
      method: "OPTIONS",
      headers: {
        Origin: origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
      },
    });
  expect((await preflight(siteOrigin)).headers()["access-control-allow-origin"]).toBe(siteOrigin);
  expect((await preflight(otherOrigin)).headers()["access-control-allow-origin"]).toBeUndefined();
});

test("사이트의 뿌리 글자 크기와 상속 속성이 위젯의 크기를 바꾸지 않고, 위젯의 CSS 가 사이트로 새지 않는다", async ({
  page,
}) => {
  const { siteOrigin } = stack();
  await page.goto(`${siteOrigin}/element?agent=echo`);
  await settled(page, "echo");
  const plain = await widgetLayout(page);
  const withWidget = await siteStyles(page);
  // 호스트는 블록이라 사이트 CSS 가 준 폭과 높이(element-site.ts 의 site.css)를 받고, 위젯은 그 자리를 채운다.
  expect(plain.host).toEqual({ width: 400, height: 600 });
  expect([plain.root.width, plain.root.height]).toEqual([400, 600]);

  await page.goto(`${siteOrigin}/element?agent=echo&hostile=1`);
  await settled(page, "echo");
  // 사이트 CSS 가 실제로 실렸다.
  expect(await page.evaluate(() => getComputedStyle(document.documentElement).fontSize)).toBe(
    "10px",
  );
  expect(await widgetLayout(page)).toEqual(plain);
  await expect(page.locator("agent-os-widget")).toHaveAttribute("data-density", "regular");

  await page.goto(`${siteOrigin}/element?bare=1`);
  expect(await siteStyles(page)).toEqual(withWidget);
  expect(withWidget.adopted).toBe(0);
});

test("글꼴은 위젯 출처의 /widget/fonts/ 에서 Access-Control-Allow-Origin 과 함께 오고 위젯만 쓰는 이름으로 그린다", async ({
  page,
}) => {
  const { siteOrigin, widgetOrigin } = stack();
  const font = page.waitForResponse((response) =>
    response.url().startsWith(`${widgetOrigin}/widget/fonts/`),
  );
  await page.goto(`${siteOrigin}/element?agent=echo`);

  const response = await font;
  expect(response.status()).toBe(200);
  expect(response.headers()["access-control-allow-origin"]).toBe("*");
  await settled(page, "echo");
  expect(await loadedFamilies(page)).toContain("agent-os-widget-sans");
  expect(
    await page.locator("[data-ui-root]").evaluate((root) => getComputedStyle(root).fontFamily),
  ).toMatch(/^"?agent-os-widget-sans"?,/);
  expect(
    await page.locator("#site-text").evaluate((text) => getComputedStyle(text).fontFamily),
  ).not.toContain("agent-os-widget");
});

test("CSP 가 style-src 'self' 인 사이트 페이지에서도 위젯이 디자인 토큰으로 칠해지고 요청과 글꼴이 선다", async ({
  page,
}) => {
  const { siteOrigin, widgetOrigin } = stack();
  const answered = page.waitForResponse((response) =>
    response.url().startsWith(`${siteOrigin}/element?`),
  );
  await page.goto(`${siteOrigin}/element?agent=echo&csp=1`);
  expect((await answered).headers()["content-security-policy"]).toBe(elementCsp(widgetOrigin));
  await settled(page, "echo");

  // 빈 입력창이면 보내기가 쓸 수 없음의 색이다. 글을 넣어 주 버튼의 색으로 둔다.
  await page.getByRole("textbox", { name: "요청" }).fill("csp");
  const button = page.getByRole("button", { name: "보내기" });
  await expect(button).toBeEnabled();
  const painted = await button.evaluate((element) => {
    // 같은 부모 안의 탐침으로 토큰을 풀어 버튼의 계산값과 맞댄다. 시트가 막혔으면 토큰이 풀리지 않는다.
    const probe = document.createElement("span");
    probe.style.backgroundColor = "var(--primary)";
    element.parentElement?.append(probe);
    const token = getComputedStyle(probe).backgroundColor;
    probe.remove();
    return { token, button: getComputedStyle(element).backgroundColor };
  });
  expect(painted.token).not.toBe("rgba(0, 0, 0, 0)");
  expect(painted.button).toBe(painted.token);

  await button.click();
  await expect(output(page, "chars:3")).toBeVisible();
  expect(await loadedFamilies(page)).toContain("agent-os-widget-sans");
  expect(await page.locator("body").getAttribute("data-violations")).toBe("");
});
