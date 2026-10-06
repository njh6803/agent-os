// tokens 프로브의 사진 비교. Storybook 정적 빌드의 스토리를 기본 테마(먹)의 라이트·다크로 찍는다. 정적 빌드는
// http://sb.probe/ 로 route 해 파일에서 내고, 그 밖의 요청은 abort 하고 센다(컨테이너는 네트워크 없이 돈다).
// 주 버튼은 실제 입력의 상태(올림, 누름, 키보드 포커스)도 찍는다.
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { extname, join } from "node:path";
import { expect, test } from "@playwright/test";

const SITE = process.env.VISUAL_SITE ?? "";
const OUT = process.env.VISUAL_OUT ?? "";
const STORIES = ["atoms-button--primary", "atoms-button--secondary", "atoms-button--danger", "probe-tokens--korean-sample"];
const MODES = ["light", "dark"];
const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".woff2": "font/woff2",
  ".woff": "font/woff",
  ".svg": "image/svg+xml",
};

async function open(page, story, mode) {
  const outside = [];
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    if (url.host !== "sb.probe") {
      outside.push(url.href);
      await route.abort();
      return;
    }
    const path = join(SITE, decodeURIComponent(url.pathname));
    if (!existsSync(path) || statSync(path).isDirectory()) {
      await route.fulfill({ status: 404, body: "" });
      return;
    }
    await route.fulfill({ status: 200, body: readFileSync(path), contentType: TYPES[extname(path)] ?? "application/octet-stream" });
  });
  await page.goto(`http://sb.probe/iframe.html?id=${story}&viewMode=story&globals=theme:muk;mode:${mode};shadow:off`);
  await page.locator("#storybook-root > *").first().waitFor();
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
  mkdirSync(join(OUT, "raw"), { recursive: true });
  return outside;
}

async function shoot(page, name) {
  writeFileSync(join(OUT, "raw", `${name}.png`), await page.screenshot());
  await expect(page).toHaveScreenshot(`${name}.png`, { maxDiffPixels: 0 });
}

for (const story of STORIES) {
  for (const mode of MODES) {
    test(`${story} ${mode}`, async ({ page }) => {
      const outside = await open(page, story, mode);
      await shoot(page, `${story}-${mode}`);
      writeFileSync(join(OUT, "raw", `${story}-${mode}.outside.json`), JSON.stringify(outside));
    });
  }
}

for (const mode of MODES) {
  test(`atoms-button--primary states ${mode}`, async ({ page }) => {
    const outside = await open(page, "atoms-button--primary", mode);
    const button = page.getByRole("button", { name: "승인" });
    await button.hover();
    await shoot(page, `atoms-button--primary-hover-${mode}`);
    await page.mouse.down();
    await shoot(page, `atoms-button--primary-press-${mode}`);
    await page.mouse.up();
    // 빈 자리를 눌러 순차 탐색의 출발점을 문서 처음으로 돌린다(measure.mjs 의 states 와 같다).
    await page.mouse.click(1, 1);
    await page.keyboard.press("Tab");
    await shoot(page, `atoms-button--primary-focus-${mode}`);
    writeFileSync(join(OUT, "raw", `states-${mode}.outside.json`), JSON.stringify(outside));
  });
}
