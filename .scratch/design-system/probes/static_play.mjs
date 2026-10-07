// 사진 비교와 같은 길(정적 빌드를 http://storybook.invalid/ 로 route)로 스토리를 열어 play 가 끝난 뒤를 읽는다.
// 보안 맥락인지, navigator.clipboard 가 있는지, 콘솔의 오류(play 의 예외), 그린 칸의 값과 포커스. Storybook 10.6.1 은
// clipboard 가 있을 때만 play 맥락의 userEvent 를 채운다(설치본 dist/csf/index.js 의 enhanceContext).
//   pnpm -C web/packages/ui run build-storybook
//   node .scratch/design-system/probes/static_play.mjs [스토리 id ...]
// 호스트에 깔린 Playwright 의 chromium 을 쓰고 아무것도 설치하지 않는다. 정적 빌드 밖의 요청은 abort 한다.
import { existsSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";

const UI = join(import.meta.dirname, "..", "..", "..", "web", "packages", "ui");
const SITE = join(UI, "storybook-static");
const ORIGIN = "http://storybook.invalid";
const STORIES = process.argv.slice(2);
const ids = STORIES.length > 0 ? STORIES : ["molecules-textfield--typing", "atoms-button--primary"];

if (!existsSync(join(SITE, "index.json"))) {
  throw new Error(`정적 빌드가 없다: ${SITE}. build-storybook 을 먼저 친다`);
}
const { chromium } = createRequire(join(UI, "package.json"))("playwright");
const browser = await chromium.launch();
try {
  for (const id of ids) {
    const page = await browser.newPage();
    const errors = [];
    page.on("console", (message) => {
      if (message.type() === "error") {
        errors.push(message.text().split("\n")[0]);
      }
    });
    await page.route("**/*", async (route) => {
      const url = new URL(route.request().url());
      const path = join(SITE, decodeURIComponent(url.pathname));
      if (url.origin !== ORIGIN) {
        await route.abort();
      } else if (!existsSync(path) || statSync(path).isDirectory()) {
        await route.fulfill({ status: 404 });
      } else {
        await route.fulfill({ path });
      }
    });
    await page.goto(
      `${ORIGIN}/iframe.html?id=${id}&viewMode=story&globals=theme:muk;mode:light;shadow:off`,
    );
    await page.waitForFunction(
      () => window.__STORYBOOK_PREVIEW__?.currentRender?.phase === "finished",
    );
    const seen = await page.evaluate(() => ({
      secure: window.isSecureContext,
      clipboard: typeof navigator.clipboard,
      values: Array.from(document.querySelectorAll("input, textarea"), (field) => field.value),
      active: document.activeElement?.tagName ?? null,
    }));
    console.log(JSON.stringify({ id, ...seen, errors }));
    await page.close();
  }
} finally {
  await browser.close();
}
