// 질문 페이지의 HTML 을 짓는다(pilot-portal 명세 "페이지"). 서버는 질의와 쿠키를 보지 않고 늘 같은 글을 내고, 어느 사이트를
// 그릴지는 페이지 스크립트가 `?site=` 를 읽어 정한다. 그래서 입력은 사이트 목록과 쿠키 수명 일수뿐이고 출력은 결정적이다.
//
// 인라인 스크립트와 인라인 스타일이 없다(CSP 가 `script-src 'self'` 와 `style-src 'self'` 이다). 사이트마다의 값은 JSON 데이터
// 블록(`type="application/json"`, 실행되지 않는다)에 싣고 페이지 스크립트가 읽는다. 뿌리의 테마와 모드는 첫 사이트의 값이라
// 스크립트가 돌기 전 첫 그림도 맞다. 스크립트가 고른 사이트가 다르면 스크립트가 뿌리를 바꾼다.
//
// 고지 확인 흐름의 마크업(뼈대, 덮개, 위젯, 짧은 고지)도 여기서 숨긴 채 내고, 페이지 스크립트가 상태 끝점의 답에 맞춰 면을
// 보인다. 사이트마다 다른 고지 글은 데이터 블록에만 싣고 덮개와 전문 자리는 비워 둔다. 스크립트가 채운다.
//
// 사이트 바꾸기와 보증 모드의 마크업도 같다. 위쪽 띠의 라벨 "사이트"와 셀렉트는 사이트가 둘 이상일 때만 그린다(설정이
// 정하는 것이라 HTML 이 요청에 따라 갈리지 않는다). 둘 다 사이트의 단추 줄, 로그인 사이트의 상자, 사이트를 바꾼 뒤의 정보
// 글, 보고서 링크는 숨긴 채 내고 스크립트가 고른 사이트에 맞춰 보인다. 부품은 React 를 싣지 않는 페이지라 디자인 시스템
// Alert·Button·Switch 의 마크업과 ARIA 를 옮긴 HTML 이다.

import type { PortalSite } from "./config.ts";
import { FONTS_CSS, PAGE_CSS, PAGE_SCRIPT, THEME_CSS, WIDGET_BUNDLE } from "./paths.ts";

const NOSCRIPT = "이 페이지는 스크립트가 있어야 동작합니다.";
const SITE_LABEL = "사이트";
const MODE_LABEL = "다크 모드";
const MODE_OFF = "꺼짐";
const SWITCHED = "사이트를 바꿔 새 대화로 시작합니다.";
const LOGIN_TITLE = "이 사이트는 로그인이 필요합니다.";
const LOGIN_BODY = "로그인은 아직 제공하지 않습니다.";
const LOGIN_BUTTON = "로그인하고 질문하기";
const LOGIN_NOTE = "로그인은 아직 제공하지 않습니다. 지금은 로그인 없이 질문할 수 있습니다.";
const REPORT = "이 에이전트의 평가 보고서";
const COVER_TITLE = "질문하기 전에 읽어 주세요";
const ACKNOWLEDGE = "확인하고 질문하기";
const SKELETON_LABEL = "고지 확인 여부를 묻는 중";
const FAILURE_TITLE = "고지 확인을 기록하지 못했습니다.";
const FAILURE_BODY = "잠시 뒤 다시 눌러 주세요.";
// 짧은 고지는 질문 페이지의 것이고 사이트가 바꾸지 못한다(명세 "질문 페이지 설정").
const SHORT_NOTICE = "질문과 출력은 기록되고 모델 API로 보내집니다. 개인정보를 넣지 마세요.";

// 아이콘은 Lucide 모양의 인라인 SVG 이고 선은 크기와 상관없이 화면 1.5px 이다(명세 "모양"). 글자와 함께 놓이는 꾸밈이라 화면
// 읽기 프로그램에서 숨긴다.
const ICON_SHAPES = {
  "loader-circle": '<path d="M21 12a9 9 0 1 1-6.219-8.56" vector-effect="non-scaling-stroke"/>',
  info: '<circle cx="12" cy="12" r="10" vector-effect="non-scaling-stroke"/><path d="M12 16v-4" vector-effect="non-scaling-stroke"/><path d="M12 8h.01" vector-effect="non-scaling-stroke"/>',
  "circle-x":
    '<circle cx="12" cy="12" r="10" vector-effect="non-scaling-stroke"/><path d="m15 9-6 6" vector-effect="non-scaling-stroke"/><path d="m9 9 6 6" vector-effect="non-scaling-stroke"/>',
  "chevron-down": '<path d="m6 9 6 6 6-6" vector-effect="non-scaling-stroke"/>',
  "external-link":
    '<path d="M15 3h6v6" vector-effect="non-scaling-stroke"/><path d="M10 14 21 3" vector-effect="non-scaling-stroke"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" vector-effect="non-scaling-stroke"/>',
} as const;

function icon(name: keyof typeof ICON_SHAPES, size: number, className: string): string {
  return `<svg class="${className}" aria-hidden="true" width="${String(size)}" height="${String(size)}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">${ICON_SHAPES[name]}</svg>`;
}

/**
 * 위젯 자리 안의 세 면. 한 번에 하나만 보이고 보이는 쪽은 페이지 스크립트가 정한다(처음에는 모두 숨겨 있다).
 * 뼈대는 상태를 묻는 답이 0.3초를 넘길 때만 보이고 움직이지 않는다. 덮개는 대화 상자가 아니라 제목을 단 영역이라 나타날 때
 * 포커스를 옮기지 않는다. 위젯 요소에는 `tabindex` 를 두지 않는다(음수 `tabindex` 가 호스트에 있으면 위젯 밖에서 Tab 으로 오는
 * 사람이 안쪽 입력창을 건너뛴다).
 */
function widgetPlaceHtml(): string {
  return [
    '<div class="pp-widget" id="pp-widget" tabindex="-1">',
    `<div class="pp-skeleton" id="pp-skeleton" aria-busy="true" aria-label="${SKELETON_LABEL}" hidden>`,
    '<span class="pp-bar pp-bar-title"></span>',
    '<span class="pp-bar pp-bar-line pp-bar-wide"></span>',
    '<span class="pp-bar pp-bar-line pp-bar-medium"></span>',
    '<span class="pp-bar pp-bar-line pp-bar-narrow"></span>',
    '<span class="pp-bar pp-bar-action"></span>',
    "</div>",
    '<section class="pp-cover" id="pp-cover" aria-labelledby="pp-cover-title" hidden>',
    `<h2 class="pp-cover-title" id="pp-cover-title">${COVER_TITLE}</h2>`,
    '<div class="pp-cover-notice" id="pp-cover-notice"></div>',
    '<div class="pp-cover-actions">',
    '<div class="pp-alert" id="pp-cover-failure" role="alert" hidden>',
    `<span class="pp-alert-icon">${icon("circle-x", 20, "pp-icon")}</span>`,
    '<div class="pp-alert-text">',
    `<p class="pp-alert-title">${FAILURE_TITLE}</p>`,
    `<p class="pp-alert-body">${FAILURE_BODY}</p>`,
    "</div>",
    "</div>",
    `<button type="button" class="pp-primary" id="pp-acknowledge"><span class="pp-primary-label">${ACKNOWLEDGE}</span>${icon("loader-circle", 16, "pp-spinner")}</button>`,
    "</div>",
    "</section>",
    '<div class="pp-login" id="pp-login" hidden>',
    '<div class="pp-alert pp-alert-info" role="status">',
    `<span class="pp-alert-icon">${icon("info", 20, "pp-icon")}</span>`,
    '<div class="pp-alert-text">',
    `<p class="pp-alert-title">${LOGIN_TITLE}</p>`,
    `<p class="pp-alert-body">${LOGIN_BODY}</p>`,
    "</div>",
    "</div>",
    "</div>",
    "<agent-os-widget hidden></agent-os-widget>",
    "</div>",
  ].join("\n");
}

/**
 * 위쪽 띠. 사이트가 둘 이상이면 라벨 "사이트"와 셀렉트가 앞에 오고, 다크 모드 스위치는 늘 있다. 셀렉트의 항목은 사이트마다
 * 하나이고 값이 이름, 글이 heading 이다. 어느 항목이 골라져 있는지는 스크립트가 `?site=` 로 정한다.
 */
function bandHtml(sites: readonly PortalSite[]): string {
  const options = sites.map(
    (site) => `<option value="${escapeHtml(site.name)}">${escapeHtml(site.heading)}</option>`,
  );
  const siteField =
    sites.length < 2
      ? []
      : [
          '<div class="pp-site">',
          `<label class="pp-site-label" for="pp-site">${SITE_LABEL}</label>`,
          '<span class="pp-select">',
          `<select class="pp-select-control" id="pp-site">${options.join("")}</select>`,
          icon("chevron-down", 16, "pp-icon pp-select-icon"),
          "</span>",
          "</div>",
        ];
  return [
    '<header class="pp-band" id="pp-band">',
    ...siteField,
    // 디자인 시스템 Switch 의 마크업과 ARIA. 이름은 라벨 하나이고 상태 글은 checked 와 같은 뜻이라 숨긴다.
    '<label class="pp-switch">',
    '<span class="pp-switch-text">',
    `<span class="pp-switch-label" id="pp-mode-label">${MODE_LABEL}</span>`,
    `<span class="pp-switch-state" id="pp-mode-state" aria-hidden="true">${MODE_OFF}</span>`,
    "</span>",
    '<span class="pp-switch-control">',
    '<input class="pp-switch-input" id="pp-mode" type="checkbox" role="switch" aria-labelledby="pp-mode-label">',
    '<span class="pp-switch-hover"></span>',
    '<span class="pp-switch-knob"></span>',
    "</span>",
    "</label>",
    "</header>",
  ].join("\n");
}

/** 둘 다 사이트의 줄. 쓸 수 없는 단추는 포커스를 받지 않고, 글이 읽는 차례에서 단추 바로 뒤에 온다. */
function bothHtml(): string {
  return [
    '<div class="pp-both" id="pp-both" hidden>',
    `<button type="button" class="pp-secondary" id="pp-login-button" disabled>${LOGIN_BUTTON}</button>`,
    `<p class="pp-both-text">${LOGIN_NOTE}</p>`,
    "</div>",
  ].join("\n");
}

/**
 * 사이트를 바꾼 뒤의 정보 글. 자리는 늘 있는 빈 `role="status"` 이고, 글은 템플릿을 복제해 자리에 넣을 때 읽히며 자리를
 * 비울 때 거둬진다. 있던 자리의 글을 보였다 숨기는 것보다 화면 읽기 프로그램이 새 글로 알아듣는다.
 */
function switchedHtml(): string {
  return [
    '<div class="pp-switched" id="pp-switched" role="status"></div>',
    '<template id="pp-switched-template">',
    '<div class="pp-switched-line">',
    icon("info", 14, "pp-icon pp-switched-icon"),
    `<p>${SWITCHED}</p>`,
    "</div>",
    "</template>",
  ].join("\n");
}

/** 보고서 링크. 주소는 사이트마다 달라 스크립트가 데이터 블록에서 채우고, 없는 사이트는 숨긴 채로 둔다. */
function reportHtml(): string {
  return `<a class="pp-report" id="pp-report" target="_blank" rel="noopener" hidden>${REPORT}${icon("external-link", 14, "pp-icon")}</a>`;
}

/** 위젯이 보일 때만 보이는 짧은 고지와 "고지 전문" 단추. 전문의 글은 스크립트가 데이터 블록에서 채운다. */
function noticeHtml(): string {
  return [
    '<div class="pp-notice" id="pp-notice" hidden>',
    '<div class="pp-notice-line">',
    icon("info", 14, "pp-icon pp-notice-icon"),
    `<p>${SHORT_NOTICE} <button type="button" class="pp-link" id="pp-notice-toggle" aria-expanded="false" aria-controls="pp-notice-full">고지 전문</button></p>`,
    "</div>",
    '<div class="pp-notice-full" id="pp-notice-full" hidden></div>',
    "</div>",
  ].join("\n");
}

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
    bandHtml(sites),
    '<main class="pp-main">',
    `<h1 class="pp-sr-only" id="pp-heading">${heading}</h1>`,
    '<div class="pp-column">',
    bothHtml(),
    switchedHtml(),
    widgetPlaceHtml(),
    noticeHtml(),
    reportHtml(),
    "</div>",
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
