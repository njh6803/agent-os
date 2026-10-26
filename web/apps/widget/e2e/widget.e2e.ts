// 위젯 e2e 의 iframe 사례(web-widget 티켓 06·09). 준비(stack.ts)가 띄운 실제 serve·위젯 Next·같은 출처의 중계 앞에서,
// 다른 출처의 사이트 페이지(site.ts)가 iframe 위젯을 품는다. 페이지 안 방식의 사례는 element.e2e.ts 이다. 새로 고친 뒤
// 다시 붙는 사례(09)는 사이트 페이지의 토큰 주체를 고정한다(site.ts).
//
// postMessage 거르기의 "허용 밖 출처" 몫은 여기서 따로 가르지 못한다. 부모가 허용 밖 출처면 `frame-ancestors` 가 먼저
// iframe 을 막아, 부모이면서 허용 밖인 보낸 쪽을 만들 수 없기 때문이다. 그 갈래는 페이지 시험(jsdom)이 본다. 여기의
// 끼어드는 프레임 둘은 부모가 아닌 쪽(같은 허용 출처의 형제와 허용 밖 출처)이다.

import { writeFileSync } from "node:fs";
import { join } from "node:path";
import { expect, type FrameLocator, type Page, type Request, test } from "@playwright/test";
import { stack } from "./env";
import { loopback, recordRequests, send } from "./helpers";
import { HTML_OUTPUT } from "./plugins";

const REQUEST_CHARS = 20_000;

function widget(page: Page): FrameLocator {
  return page.frameLocator('iframe[title="위젯"]');
}

/** 도구 에이전트가 둘째 도구 앞에서 기다리는 문을 연다. */
function openGate(name: string): void {
  writeFileSync(join(stack().gates, name), "");
}

async function siteToken(page: Page): Promise<string> {
  const response = await page.request.get(`${loopback(stack().siteOrigin)}/token`);
  expect(response.status()).toBe(200);
  return response.text();
}

test("허용 출처의 페이지에서 iframe 위젯이 첫 도구 줄을 결말 전에 보이고 요청 하나를 결말까지 보낸다", async ({
  page,
}) => {
  const { siteOrigin, widgetOrigin } = stack();
  const requests = recordRequests(page);
  await page.goto(`${siteOrigin}/?agent=tools`);
  const frame = widget(page);

  await send(frame, "tool-row");

  // 에이전트는 첫 도구를 부른 뒤 문 앞에서 기다린다. 그동안 첫 도구 줄이 서 있고 결말은 아직 없다.
  const tools = frame.getByRole("list", { name: "부른 도구" });
  await expect(tools.getByText("add", { exact: true })).toHaveCount(1);
  await expect(frame.getByText("5/9", { exact: true })).toHaveCount(0);

  openGate("tool-row");
  await expect(frame.getByText("5/9", { exact: true })).toBeVisible();
  await expect(frame.getByRole("button", { name: "도구 2개를 불렀습니다" })).toBeVisible();

  const endUser = requests.filter((request) =>
    request.url().startsWith(`${widgetOrigin}/end-user/`),
  );
  expect(
    endUser.map((request) => `${request.method()} ${new URL(request.url()).pathname}`),
  ).toEqual(["POST /end-user/runs"]);
  // 위젯 페이지와 같은 출처라 CORS 사전 요청이 없다.
  expect(requests.filter((request) => request.method() === "OPTIONS")).toEqual([]);
});

test("iframe 페이지의 위젯은 디자인 토큰의 값으로 칠해진다", async ({ page }) => {
  await page.goto(`${stack().siteOrigin}/?agent=tools`);
  const frame = widget(page);
  // 빈 입력창이면 보내기가 쓸 수 없음의 색이다. 글을 넣어 주 버튼의 색으로 둔다.
  await frame.getByRole("textbox", { name: "요청" }).fill("css");
  const send = frame.getByRole("button", { name: "보내기" });
  await expect(send).toBeEnabled();

  const painted = await send.evaluate((button) => {
    // 같은 부모 안의 탐침으로 토큰을 풀어 버튼의 계산값과 맞댄다. CSS 가 실리지 않았으면 토큰이 풀리지 않는다.
    const probe = document.createElement("span");
    probe.style.backgroundColor = "var(--primary)";
    button.parentElement?.append(probe);
    const token = getComputedStyle(probe).backgroundColor;
    probe.remove();
    return { token, button: getComputedStyle(button).backgroundColor };
  });
  expect(painted.token).not.toBe("rgba(0, 0, 0, 0)");
  expect(painted.button).toBe(painted.token);
});

test("부모가 아닌 프레임이 보낸 토큰 메시지는 버려지고 부모의 토큰으로 실행이 끝난다", async ({
  page,
}) => {
  openGate("intruders");
  await page.goto(`${stack().siteOrigin}/?agent=tools&intruders=1`);
  const frame = widget(page);

  await send(frame, "intruders");

  // 끼어드는 프레임 둘이 그 회차에 실제로 가짜 토큰을 보냈다.
  await expect(page.locator("body")).toHaveAttribute("data-intruded", "2");
  await expect(frame.getByText("5/9", { exact: true })).toBeVisible();
  await expect(frame.getByText("로그인 정보를 받지 못했습니다.")).toHaveCount(0);
});

test("허용 출처의 페이지는 위젯을 품고 허용 밖 출처의 페이지는 품지 못한다", async ({ page }) => {
  const { siteOrigin, otherOrigin, widgetOrigin } = stack();
  await page.goto(`${siteOrigin}/?agent=tools`);
  await expect(widget(page).getByRole("heading", { name: "tools" })).toBeVisible();

  const answered = page.waitForResponse((response) =>
    response.url().startsWith(`${widgetOrigin}/widget`),
  );
  // goto 는 iframe 까지 load 를 기다린다. 막힌 iframe 은 chromium 의 오류 페이지로 끝난다.
  await page.goto(`${otherOrigin}/?agent=tools`);
  const response = await answered;
  expect(page.frames().map((frame) => frame.url())).toEqual([
    `${otherOrigin}/?agent=tools`,
    "chrome-error://chromewebdata/",
  ]);
  // 위젯 페이지는 답했다. 막은 것은 브라우저가 그 응답의 frame-ancestors 를 읽은 것이다.
  expect(response.status()).toBe(200);
  expect(response.headers()["content-security-policy"]).toBe(`frame-ancestors ${siteOrigin}`);
});

test("출력의 HTML 조각은 글로 보이고 실행되지 않는다", async ({ page }) => {
  await page.goto(`${stack().siteOrigin}/?agent=html`);
  const frame = widget(page);

  await send(frame, "html");

  // 화면 읽기 알림(status)도 같은 글을 싣는다. 대화 목록의 출력 문단으로 좁힌다.
  const conversation = frame.getByRole("region", { name: "대화" });
  await expect(conversation.getByText(`출력: ${HTML_OUTPUT}`, { exact: true })).toBeVisible();
  const pwned = await frame.locator("body").evaluate(() => "__widgetE2ePwned" in window);
  expect(pwned).toBe(false);
});

/** 위젯이 보낸 구독 요청. */
function subscriptions(requests: readonly Request[]): Request[] {
  const { widgetOrigin } = stack();
  return requests.filter(
    (request) =>
      request.method() === "GET" &&
      request.url().startsWith(`${widgetOrigin}/end-user/runs/`) &&
      request.url().endsWith("/subscription"),
  );
}

test("새로 고친 뒤 도는 실행에 처음부터 다시 붙어 받은 도구 줄을 다시 짓고 결말을 받는다", async ({
  page,
}) => {
  const requests = recordRequests(page);
  await page.goto(`${stack().siteOrigin}/?agent=tools&sub=reload-running`);
  const frame = widget(page);
  await send(frame, "reload-running");
  const tools = frame.getByRole("list", { name: "부른 도구" });
  await expect(tools.getByText("add", { exact: true })).toHaveCount(1);

  await page.reload();

  // 저장한 요청과, 처음부터 받은 항목으로 다시 지은 첫 도구 줄이 선다. 에이전트는 아직 문 앞에서 기다린다.
  const conversation = frame.getByRole("region", { name: "대화" });
  await expect(conversation.getByText("reload-running")).toBeVisible();
  await expect(tools.getByText("add", { exact: true })).toHaveCount(1);
  await expect(frame.getByText("5/9", { exact: true })).toHaveCount(0);
  const [subscription, ...more] = subscriptions(requests);
  expect(more).toEqual([]);
  expect(subscription?.headers()["last-event-id"]).toBeUndefined();

  openGate("reload-running");
  await expect(conversation.getByText("출력: 5/9", { exact: true })).toBeVisible();
  await expect(frame.getByRole("button", { name: "도구 2개를 불렀습니다" })).toBeVisible();
});

test("새로 고친 뒤 멈춘 실행에 다시 붙으면 승인 카드가 다시 서고, 그 카드로 승인해 결말을 받는다", async ({
  page,
}) => {
  const requests = recordRequests(page);
  await page.goto(`${stack().siteOrigin}/?agent=approval&sub=reload-paused`);
  const frame = widget(page);
  await send(frame, "reload-paused");
  const card = frame.getByRole("group", { name: "승인 묻기" });
  await expect(card).toBeVisible();

  await page.reload();

  await expect(card).toBeVisible();
  const [subscription, ...more] = subscriptions(requests);
  expect(more).toEqual([]);
  expect(subscription?.headers()["last-event-id"]).toBeUndefined();

  await card.getByRole("button", { name: "승인" }).click();
  const conversation = frame.getByRole("region", { name: "대화" });
  await expect(conversation.getByText("출력: total:5", { exact: true })).toBeVisible();
});

test("입력창의 글자 수 상한은 서버의 기본값과 같다", async ({ page }) => {
  const { siteOrigin, widgetOrigin } = stack();
  await page.goto(`${siteOrigin}/?agent=echo`);
  const frame = widget(page);
  const field = frame.getByRole("textbox", { name: "요청" });
  const sendButton = frame.getByRole("button", { name: "보내기" });

  await field.fill("a".repeat(REQUEST_CHARS + 1));
  await expect(frame.getByText("20,000자를 넘었습니다")).toBeVisible();
  await expect(sendButton).toBeDisabled();

  await field.fill("a".repeat(REQUEST_CHARS));
  await expect(frame.getByText("20,000자를 넘었습니다")).toHaveCount(0);
  await expect(sendButton).toBeEnabled();

  // 서버에 직접 보낸 상한의 글자는 받고 하나 넘으면 422 다.
  const post = async (chars: number) =>
    page.request.post(`${loopback(widgetOrigin)}/end-user/runs`, {
      headers: { Authorization: `Bearer ${await siteToken(page)}` },
      data: { agent: "echo", request: "a".repeat(chars) },
    });
  const accepted = await post(REQUEST_CHARS);
  expect(accepted.status()).toBe(200);
  expect(await accepted.text()).toContain(`chars:${String(REQUEST_CHARS)}`);
  const refused = await post(REQUEST_CHARS + 1);
  expect(refused.status()).toBe(422);
});
