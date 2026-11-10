// 질문 페이지 e2e 의 사례(pilot-portal 티켓 06 의 몫). 준비가 띄운 실제 질문 페이지와 위젯을 실제 브라우저로 연다.

import { expect, test } from "@playwright/test";
import { stack } from "./env.ts";
import { SITES } from "./sites.ts";

const [FIRST, SECOND] = SITES;
if (FIRST === undefined || SECOND === undefined) {
  throw new Error("e2e 사이트가 둘보다 적다");
}

test("페이지에 CSP 위반이 없고 본문의 글꼴 변수가 토큰 값으로 풀린다", async ({ page }) => {
  const messages: string[] = [];
  page.on("console", (message) => {
    messages.push(message.text());
  });
  const failures: string[] = [];
  page.on("requestfailed", (request) => {
    failures.push(request.url());
  });

  await page.goto(`${stack().portalOrigin}/portal/`);
  await page.evaluate(() => document.fonts.ready);

  expect(messages.filter((text) => text.includes("Content Security Policy"))).toEqual([]);
  expect(failures).toEqual([]);
  const resolved = await page.evaluate(() => {
    const root = getComputedStyle(document.documentElement);
    return {
      sans: root.getPropertyValue("--sans").trim(),
      body: getComputedStyle(document.body).fontFamily,
    };
  });
  // 토큰 CSS 가 실려 `--sans` 가 풀리고, 본문이 그 글꼴 묶음을 쓴다.
  expect(resolved.sans).toContain("Noto Sans KR");
  expect(resolved.body).toContain("Noto Sans KR");
});

test("첫 사이트의 설정으로 위젯 요소의 속성 다섯이 채워진다", async ({ page }) => {
  await page.goto(`${stack().portalOrigin}/portal/`);

  const widget = page.locator("agent-os-widget");
  await expect(widget).toHaveAttribute("agent", "echo");
  await expect(widget).toHaveAttribute("heading", FIRST.heading);
  await expect(widget).toHaveAttribute("intro", FIRST.intro ?? "");
  await expect(widget).toHaveAttribute("theme", FIRST.theme);
  await expect(widget).toHaveAttribute("mode", FIRST.mode ?? "");
  await expect(page).toHaveTitle(FIRST.heading);
  // 위젯의 머리글도 h1 이라 페이지 쪽 것을 id 로 짚는다.
  await expect(page.locator("#pp-heading")).toHaveText(FIRST.heading);
  // 스크립트가 고른 사이트를 주소에 적는다.
  await expect(page).toHaveURL(`${stack().portalOrigin}/portal/?site=${FIRST.name}`);
});

test("?site= 로 열면 그 사이트가 골라지고 페이지 제목이 그 사이트의 heading 이다", async ({
  page,
}) => {
  await page.goto(`${stack().portalOrigin}/portal/?site=${SECOND.name}`);

  const widget = page.locator("agent-os-widget");
  await expect(widget).toHaveAttribute("heading", SECOND.heading);
  await expect(widget).toHaveAttribute("theme", SECOND.theme);
  // 둘째 사이트는 소개 글과 모드를 적지 않아 속성이 없다.
  await expect(widget).not.toHaveAttribute("intro", /.*/u);
  await expect(widget).not.toHaveAttribute("mode", /.*/u);
  await expect(page).toHaveTitle(SECOND.heading);
  await expect(page.locator("html")).toHaveAttribute("data-theme", SECOND.theme);
});

test("루트로 들어오면 질의를 지킨 채 질문 페이지로 넘어간다", async ({ page }) => {
  await page.goto(`${stack().portalOrigin}/?site=${SECOND.name}`);

  await expect(page).toHaveURL(`${stack().portalOrigin}/portal/?site=${SECOND.name}`);
  await expect(page).toHaveTitle(SECOND.heading);
});
