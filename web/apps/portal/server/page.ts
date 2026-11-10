// 질문 페이지의 HTML 을 짓는다(pilot-portal 명세 "페이지"). 서버는 질의와 쿠키를 보지 않고 늘 같은 글을 내고, 어느 사이트를
// 그릴지는 페이지 스크립트가 `?site=` 를 읽어 정한다. 그래서 입력은 사이트 목록과 쿠키 수명 일수뿐이고 출력은 결정적이다.
//
// 인라인 스크립트와 인라인 스타일이 없다(CSP 가 `script-src 'self'` 와 `style-src 'self'` 이다). 사이트마다의 값은 JSON 데이터
// 블록(`type="application/json"`, 실행되지 않는다)에 싣고 페이지 스크립트가 읽는다. 뿌리의 테마와 모드는 첫 사이트의 값이라
// 스크립트가 돌기 전 첫 그림도 맞다. 스크립트가 고른 사이트가 다르면 스크립트가 뿌리를 바꾼다.

import type { PortalSite } from "./config.ts";
import { FONTS_CSS, PAGE_CSS, PAGE_SCRIPT, THEME_CSS, WIDGET_BUNDLE } from "./paths.ts";

const NOSCRIPT = "이 페이지는 스크립트가 있어야 동작합니다.";

const HTML_ESCAPES: Readonly<Record<string, string>> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/gu, (char) => HTML_ESCAPES[char] ?? char);
}

/** JSON 을 `<script>` 안에 싣는 글로 바꾼다. `<` 를 글자 코드로 바꿔 `</script>` 가 블록을 닫지 못하게 한다. */
function jsonForScript(value: unknown): string {
  return JSON.stringify(value).replace(/</gu, "\\u003c");
}

function dataOf(sites: readonly PortalSite[], cookieDays: number): unknown {
  return {
    cookieDays,
    sites: sites.map((site) => ({
      name: site.name,
      agent: site.agent,
      heading: site.heading,
      intro: site.intro ?? null,
      theme: site.theme,
      mode: site.mode ?? null,
      assurance: site.assurance,
      notice: site.notice,
      reportUrl: site.reportUrl ?? null,
    })),
  };
}

export function pageHtml(sites: readonly PortalSite[], cookieDays: number): string {
  const [first] = sites;
  if (first === undefined) {
    throw new Error("질문 페이지에 사이트가 하나도 없다. 시작 검사가 어긋났다.");
  }
  const heading = escapeHtml(first.heading);
  const mode = first.mode === undefined ? "" : ` data-mode="${first.mode}"`;
  return [
    "<!doctype html>",
    `<html lang="ko" data-density="regular" data-theme="${first.theme}"${mode}>`,
    "<head>",
    '<meta charset="utf-8">',
    '<meta name="viewport" content="width=device-width, initial-scale=1">',
    `<title>${heading}</title>`,
    `<link rel="stylesheet" href="${THEME_CSS}">`,
    `<link rel="stylesheet" href="${FONTS_CSS}">`,
    `<link rel="stylesheet" href="${PAGE_CSS}">`,
    "</head>",
    '<body class="pp-body">',
    '<header class="pp-band" id="pp-band"></header>',
    '<main class="pp-main">',
    `<h1 class="pp-sr-only" id="pp-heading">${heading}</h1>`,
    '<div class="pp-widget" id="pp-widget"><agent-os-widget></agent-os-widget></div>',
    `<noscript>${NOSCRIPT}</noscript>`,
    "</main>",
    `<script type="application/json" id="pp-data">${jsonForScript(dataOf(sites, cookieDays))}</script>`,
    `<script defer src="${PAGE_SCRIPT}"></script>`,
    `<script defer src="${WIDGET_BUNDLE}"></script>`,
    "</body>",
    "</html>",
    "",
  ].join("\n");
}
