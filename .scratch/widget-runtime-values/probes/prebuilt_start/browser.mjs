// 호스트에서 Playwright 의 Chromium 으로, 떠 있는 시제품 위젯 컨테이너를 사이트 페이지 둘이 iframe 으로 품어 본다.
// 프로브(run.py)의 browser 섹션이 부른다. 본 것을 JSON 한 줄로 찍는다. 종료 코드는 기한을 넘겼을 때만 1 이다(판정은
// 프로브가 한다).
//
// 하는 일
//   - 부모 페이지를 내는 작은 서버를 127.0.0.1:<부모 포트> 에 띄운다. 페이지는 위젯의 iframe 하나를 든다.
//   - Chromium 을 `*.localhost` 를 127.0.0.1 로 푸는 규칙으로 띄운다(위젯 e2e 의 playwright.config.ts 와 같다). 그래서
//     http://<라벨>.localhost:<부모 포트> 가 라벨마다 다른 출처의 부모 페이지가 된다.
//   - 라벨마다 부모 페이지를 열어 iframe 의 주소, 그 안의 문서가 위젯의 것인지, 위젯 페이지 응답의 CSP 머리, 콘솔 오류를
//     적는다. 막힌 iframe 은 Chromium 의 오류 페이지(chrome-error://chromewebdata/)로 끝난다(위젯 e2e 의
//     "허용 출처의 페이지는 위젯을 품고 허용 밖 출처의 페이지는 품지 못한다"가 보는 것과 같다).
//   - 부모 페이지의 문서에서 fetch 로 값 파일(/widget/runtime.json)을 받아 본다. 페이지 안 번들이 사이트의 문서에서
//     값 파일을 받는 길과 같은 교차 출처 요청이다. 대조로 Access-Control-Allow-Origin 이 없는 위젯 페이지(/widget)도
//     같은 fetch 로 받아 본다(브라우저가 본문을 주지 않아야 한다).
//
// 사용: node browser.mjs --playwright <@playwright/test 를 깐 패키지의 package.json> --parent-port <포트>
//         --widget <위젯 출처, 예 http://127.0.0.1:39500> --labels <라벨,라벨>

import { createServer } from "node:http";
import { createRequire } from "node:module";
import { parseArgs } from "node:util";

const DEADLINE_MS = 90_000;
const SETTLE_MS = 1_500;

const { values } = parseArgs({
  options: {
    playwright: { type: "string" },
    "parent-port": { type: "string" },
    widget: { type: "string" },
    labels: { type: "string" },
  },
});
const port = Number(values["parent-port"]);
const widget = values.widget;
const labels = (values.labels ?? "").split(",").filter((label) => label !== "");
if (values.playwright === undefined || !Number.isInteger(port) || widget === undefined || labels.length === 0) {
  console.error("사용: node browser.mjs --playwright <package.json> --parent-port <포트> --widget <출처> --labels <a,b>");
  process.exit(2);
}

const timer = setTimeout(() => {
  console.log(JSON.stringify({ error: "deadline" }));
  process.exit(1);
}, DEADLINE_MS);

const { chromium } = createRequire(values.playwright)("@playwright/test");
const frameUrl = `${widget}/widget`;

const server = createServer((request, response) => {
  response.writeHead(200, { "content-type": "text/html; charset=utf-8" });
  response.end(
    `<!doctype html><meta charset="utf-8"><title>${request.headers.host ?? ""}</title>` +
      `<iframe id="widget" src="${frameUrl}" width="400" height="600"></iframe>`,
  );
});
await new Promise((resolve) => server.listen(port, "127.0.0.1", resolve));

const browser = await chromium.launch({
  args: ["--host-resolver-rules=MAP *.localhost 127.0.0.1"],
});

async function visit(label) {
  const origin = `http://${label}.localhost:${String(port)}`;
  const page = await browser.newPage();
  const consoleErrors = [];
  const frameResponses = [];
  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });
  page.on("response", (response) => {
    if (response.url() === frameUrl) {
      frameResponses.push({
        status: response.status(),
        csp: response.headers()["content-security-policy"] ?? null,
      });
    }
  });
  await page.goto(`${origin}/`, { waitUntil: "load" });
  await page.waitForTimeout(SETTLE_MS);
  const frame = page.frames().find((candidate) => candidate !== page.mainFrame());
  let inside = null;
  if (frame !== undefined) {
    try {
      inside = await frame.evaluate(() => ({
        origin: location.origin,
        title: document.title,
        nextScripts: document.querySelectorAll('script[src*="/widget/_next/"]').length,
      }));
    } catch (error) {
      inside = { error: String(error) };
    }
  }
  const fetched = await page.evaluate(async (base) => {
    const out = {};
    for (const [key, path] of [
      ["values", "/widget/runtime.json"],
      ["page", "/widget"],
    ]) {
      try {
        const response = await fetch(base + path);
        out[key] = { status: response.status, body: (await response.text()).slice(0, 400) };
      } catch (error) {
        out[key] = { error: String(error) };
      }
    }
    return out;
  }, widget);
  const seen = {
    origin,
    frameUrl: frame === undefined ? null : frame.url(),
    inside,
    frameResponses,
    consoleErrors,
    fetched,
  };
  await page.close();
  return seen;
}

const visits = {};
try {
  for (const label of labels) {
    visits[label] = await visit(label);
  }
  console.log(JSON.stringify({ browser: browser.version(), frameUrl, visits }));
} finally {
  clearTimeout(timer);
  await browser.close();
  server.close();
}
