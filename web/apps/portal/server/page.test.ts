// 페이지 HTML 짓기. 순수 함수라 사이트 값을 넣고 글을 본다. 서버가 질의와 쿠키를 보지 않고 같은 HTML 을 내므로 입력은 사이트
// 목록과 쿠키 수명 일수뿐이다(pilot-portal 명세 "페이지").

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "vitest";
import type { PortalSite } from "./config.ts";
import { pageHtml } from "./page.ts";

function site(overrides: Partial<PortalSite> = {}): PortalSite {
  return {
    name: "demo",
    issuer: "https://demo.example",
    agent: "calc",
    heading: "계산기",
    intro: undefined,
    theme: "nokcheong",
    mode: undefined,
    assurance: "anonymous",
    notice: "기본 고지",
    reportUrl: undefined,
    ...overrides,
  };
}

const DATA_BLOCK = /<script type="application\/json" id="pp-data">([^<]*)<\/script>/u;

function dataOf(html: string): unknown {
  const text = DATA_BLOCK.exec(html)?.[1];
  if (text === undefined) {
    throw new Error("데이터 블록이 없다");
  }
  const value: unknown = JSON.parse(text);
  return value;
}

test("뿌리에 한국어와 보통 밀도와 첫 사이트의 테마와 모드를 단다", () => {
  const html = pageHtml([site({ theme: "jacho", mode: "dark" }), site({ name: "other" })], 30);

  expect(html).toMatch(/^<!doctype html>\n<html lang="ko" data-density="regular"/u);
  expect(html).toContain('data-theme="jacho"');
  expect(html).toContain('data-mode="dark"');
});

test("첫 사이트에 모드가 없으면 뿌리에 data-mode 를 달지 않는다", () => {
  const html = pageHtml([site({ mode: undefined })], 30);

  expect(html).not.toContain("data-mode");
});

test("페이지 제목과 화면 읽기 프로그램만 읽는 h1 이 첫 사이트의 heading 이다", () => {
  const html = pageHtml(
    [site({ heading: "첫째 사이트" }), site({ name: "two", heading: "둘째" })],
    30,
  );

  expect(html).toContain("<title>첫째 사이트</title>");
  expect(html).toMatch(/<h1 class="pp-sr-only" id="pp-heading">첫째 사이트<\/h1>/u);
});

test("heading 의 꺾쇠와 앰퍼샌드와 따옴표는 HTML 글자로 이스케이프한다", () => {
  const html = pageHtml([site({ heading: `<b>"A" & 'B'</b>` })], 30);

  expect(html).toContain("<title>&lt;b&gt;&quot;A&quot; &amp; &#39;B&#39;&lt;/b&gt;</title>");
  expect(html).not.toContain("<b>");
});

test("데이터 블록이 사이트마다 이름과 에이전트와 제목과 소개와 테마와 모드와 보증과 고지와 보고서 주소를 든다", () => {
  const html = pageHtml(
    [
      site({
        intro: "소개 한 줄",
        mode: "light",
        notice: "전문",
        reportUrl: "https://report.example/calc",
      }),
      site({ name: "gate", heading: "관문", assurance: "login" }),
    ],
    30,
  );

  expect(dataOf(html)).toEqual({
    cookieDays: 30,
    sites: [
      {
        name: "demo",
        agent: "calc",
        heading: "계산기",
        intro: "소개 한 줄",
        theme: "nokcheong",
        mode: "light",
        assurance: "anonymous",
        notice: "전문",
        reportUrl: "https://report.example/calc",
      },
      {
        name: "gate",
        agent: "calc",
        heading: "관문",
        intro: null,
        theme: "nokcheong",
        mode: null,
        assurance: "login",
        notice: "기본 고지",
        reportUrl: null,
      },
    ],
  });
});

test("데이터 블록은 </script> 가 든 고지 글을 이스케이프해 블록을 닫지 못하게 한다", () => {
  const evil = 'x</script><script>alert("p")</script>&';
  const html = pageHtml([site({ notice: evil })], 30);

  // 스크립트 열기는 셋(데이터 블록, 페이지 스크립트, 위젯 번들)뿐이다.
  expect(html.match(/<script/gu)).toHaveLength(3);
  expect(html.match(/<\/script>/gu)).toHaveLength(3);
  expect(html).toContain("\\u003c/script");
  expect(dataOf(html)).toMatchObject({ sites: [{ notice: evil }] });
});

test("인라인 스크립트와 인라인 스타일이 없다", () => {
  const html = pageHtml([site()], 30);

  expect(html).not.toContain("<style");
  expect(html).not.toMatch(/\sstyle=/u);
  const scripts = [...html.matchAll(/<script\b([^>]*)>/gu)].map((found) => found[1] ?? "");
  expect(scripts).toHaveLength(3);
  for (const attributes of scripts) {
    expect(attributes).toMatch(/src="|type="application\/json"/u);
  }
  expect(html).not.toMatch(/\son[a-z]+=/u);
});

test("토큰 CSS와 글꼴 CSS와 페이지 CSS를 링크하고 페이지 스크립트가 위젯 번들보다 앞서 돈다", () => {
  const html = pageHtml([site()], 30);

  expect(html).toContain('<link rel="stylesheet" href="/portal/theme.css">');
  expect(html).toContain('<link rel="stylesheet" href="/portal/fonts.css">');
  expect(html).toContain('<link rel="stylesheet" href="/portal/portal.css">');
  const page = html.indexOf('<script defer src="/portal/portal.js">');
  const widget = html.indexOf('<script defer src="/widget/element.js">');
  expect(page).toBeGreaterThan(-1);
  expect(widget > page).toBe(true);
});

test("스크립트를 끈 브라우저에 보일 한 줄을 noscript 에 둔다", () => {
  const html = pageHtml([site()], 30);

  expect(html).toContain("<noscript>이 페이지는 스크립트가 있어야 동작합니다.</noscript>");
});

test("위젯 자리는 tabindex -1 의 상자이고 뼈대와 덮개와 위젯 요소를 차례로 든다", () => {
  const html = pageHtml([site()], 30);

  expect(html).toContain('<div class="pp-widget" id="pp-widget" tabindex="-1">');
  const skeleton = html.indexOf('id="pp-skeleton"');
  const cover = html.indexOf('id="pp-cover"');
  const widget = html.indexOf("<agent-os-widget");
  expect(skeleton).toBeGreaterThan(html.indexOf('id="pp-widget"'));
  expect(cover).toBeGreaterThan(skeleton);
  expect(widget).toBeGreaterThan(cover);
});

test("위젯 요소는 속성 없이 숨겨져 서 있고 tabindex 를 두지 않는다. 속성은 페이지 스크립트가 채운다", () => {
  const html = pageHtml([site()], 30);

  expect(html).toContain("<agent-os-widget hidden></agent-os-widget>");
  expect(html).not.toMatch(/<agent-os-widget[^>]*tabindex/u);
});

test("뼈대는 처음에 숨겨져 있고 움직이지 않으며 상태를 묻는 중이라고 이름을 단다", () => {
  const html = pageHtml([site()], 30);

  expect(html).toMatch(
    /<div class="pp-skeleton" id="pp-skeleton" aria-busy="true" aria-label="고지 확인 여부를 묻는 중" hidden>/u,
  );
});

test("덮개는 대화 상자가 아니라 제목을 단 영역이고 처음에 숨겨져 있으며 자동 포커스가 없다", () => {
  const html = pageHtml([site()], 30);

  expect(html).toMatch(
    /<section class="pp-cover" id="pp-cover" aria-labelledby="pp-cover-title" hidden>/u,
  );
  expect(html).toContain(
    '<h2 class="pp-cover-title" id="pp-cover-title">질문하기 전에 읽어 주세요</h2>',
  );
  expect(html).not.toContain("autofocus");
  expect(html).not.toContain('role="dialog"');
  expect(html).not.toContain("aria-modal");
});

test("덮개의 주 버튼은 폭을 채우는 확인 단추이고 도는 표시는 꾸밈이라 화면 읽기 프로그램에서 숨긴다", () => {
  const html = pageHtml([site()], 30);

  const button =
    /<button type="button" class="pp-primary" id="pp-acknowledge">(.*?)<\/button>/su.exec(html);
  expect(button?.[1]).toContain('<span class="pp-primary-label">확인하고 질문하기</span>');
  expect(button?.[1]).toMatch(/<svg class="pp-spinner"[^>]*aria-hidden="true"/u);
});

test("덮개 안의 위험 알림은 role alert 이고 처음에 숨겨져 있다", () => {
  const html = pageHtml([site()], 30);

  const alert =
    /<div class="pp-alert" id="pp-cover-failure" role="alert" hidden>(.*?)<\/div>\s*<\/div>/su.exec(
      html,
    );
  expect(alert?.[1]).toContain("고지 확인을 기록하지 못했습니다.");
  expect(alert?.[1]).toContain("잠시 뒤 다시 눌러 주세요.");
  expect(alert?.[1]).toMatch(/<svg[^>]*aria-hidden="true"/u);
});

test("짧은 고지와 고지 전문 단추는 처음에 숨겨져 있고 단추가 펼침 상태와 전문을 알린다", () => {
  const html = pageHtml([site()], 30);

  expect(html).toMatch(/<div class="pp-notice" id="pp-notice" hidden>/u);
  expect(html).toContain("질문과 출력은 기록되고 모델 API로 보내집니다. 개인정보를 넣지 마세요.");
  expect(html).toContain(
    '<button type="button" class="pp-link" id="pp-notice-toggle" aria-expanded="false" aria-controls="pp-notice-full">고지 전문</button>',
  );
  expect(html).toMatch(/<div class="pp-notice-full" id="pp-notice-full" hidden><\/div>/u);
});

test("짧은 고지는 위젯 자리 바로 뒤에 와서 Tab 차례가 위젯 또는 덮개의 단추, 고지 전문 단추 순이다", () => {
  const html = pageHtml([site()], 30);

  const acknowledgeAt = html.indexOf('id="pp-acknowledge"');
  const widgetAt = html.indexOf("<agent-os-widget");
  const toggleAt = html.indexOf('id="pp-notice-toggle"');
  expect(widgetAt).toBeGreaterThan(acknowledgeAt);
  expect(toggleAt).toBeGreaterThan(widgetAt);
});

test("고지 글은 HTML 에 박지 않는다. 사이트마다의 글은 데이터 블록에서 스크립트가 채운다", () => {
  const html = pageHtml([site({ notice: "사이트 고지 글" })], 30);

  const outsideData = html.replace(DATA_BLOCK, "");
  expect(outsideData).not.toContain("사이트 고지 글");
  expect(html).toContain('<div class="pp-cover-notice" id="pp-cover-notice"></div>');
});

/** 위쪽 띠(`<header id="pp-band">`)의 안쪽. */
function bandOf(html: string): string {
  const band = /<header class="pp-band" id="pp-band">(.*?)<\/header>/su.exec(html);
  if (band?.[1] === undefined) {
    throw new Error("위쪽 띠가 없다");
  }
  return band[1];
}

const TWO_SITES = [
  site({ name: "calc-demo", heading: "계산 도우미" }),
  site({ name: "store", heading: "매장 계산 도우미" }),
];

test("위쪽 띠는 본문 앞에 서고 사이트가 여럿이면 라벨 사이트와 셀렉트가 스위치보다 앞에 온다", () => {
  const html = pageHtml(TWO_SITES, 30);

  expect(html.indexOf('id="pp-band"')).toBeLessThan(html.indexOf('<main class="pp-main">'));
  const band = bandOf(html);
  expect(band).toContain('<label class="pp-site-label" for="pp-site">사이트</label>');
  expect(band).toMatch(/<select class="pp-select-control" id="pp-site">/u);
  expect(band.indexOf('id="pp-site"')).toBeLessThan(band.indexOf('role="switch"'));
});

test("셀렉트의 항목은 사이트마다 하나이고 값이 이름, 글이 heading 이며 꺾쇠는 이스케이프한다", () => {
  const html = pageHtml(
    [
      site({ name: "calc-demo", heading: "계산 도우미" }),
      site({ name: "store", heading: "<매장>" }),
    ],
    30,
  );

  const options = [...bandOf(html).matchAll(/<option value="([^"]*)">([^<]*)<\/option>/gu)].map(
    (found) => [found[1], found[2]],
  );
  expect(options).toEqual([
    ["calc-demo", "계산 도우미"],
    ["store", "&lt;매장&gt;"],
  ]);
});

test("셀렉트의 꺾쇠 아이콘은 꾸밈이라 화면 읽기 프로그램에서 숨긴다", () => {
  const band = bandOf(pageHtml(TWO_SITES, 30));

  expect(band).toMatch(/<svg class="pp-icon pp-select-icon" aria-hidden="true"/u);
});

test("사이트가 하나면 라벨 사이트도 셀렉트도 그리지 않는다", () => {
  const band = bandOf(pageHtml([site()], 30));

  expect(band).not.toContain('<label class="pp-site-label"');
  expect(band).not.toContain("<select");
  expect(band).not.toContain("사이트");
  expect(band).toContain('role="switch"');
});

test("다크 모드 스위치는 이름이 라벨 하나이고 상태 글은 화면 읽기 프로그램에서 숨긴다", () => {
  const band = bandOf(pageHtml([site()], 30));

  expect(band).toMatch(/<label class="pp-switch">/u);
  expect(band).toContain('<span class="pp-switch-label" id="pp-mode-label">다크 모드</span>');
  expect(band).toContain(
    '<span class="pp-switch-state" id="pp-mode-state" aria-hidden="true">꺼짐</span>',
  );
  expect(band).toContain(
    '<input class="pp-switch-input" id="pp-mode" type="checkbox" role="switch" aria-labelledby="pp-mode-label">',
  );
});

test("사이트를 바꾼 뒤의 정보 글 자리는 비어 있는 role status 이고 글은 템플릿에서 복제해 채운다", () => {
  const html = pageHtml([site()], 30);

  expect(html).toContain('<div class="pp-switched" id="pp-switched" role="status"></div>');
  const template = /<template id="pp-switched-template">(.*?)<\/template>/su.exec(html);
  expect(template?.[1]).toContain("사이트를 바꿔 새 대화로 시작합니다.");
  expect(template?.[1]).toMatch(/<svg[^>]*aria-hidden="true"/u);
});

test("둘 다 사이트의 줄은 처음에 숨겨져 있고 쓸 수 없는 단추 바로 뒤에 글이 오며 위젯 자리보다 앞이다", () => {
  const html = pageHtml([site()], 30);

  const both = /<div class="pp-both" id="pp-both" hidden>(.*?)<\/div>/su.exec(html);
  expect(both?.[1]).toBe(
    [
      '\n<button type="button" class="pp-secondary" id="pp-login-button" disabled>로그인하고 질문하기</button>',
      '<p class="pp-both-text">로그인은 아직 제공하지 않습니다. 지금은 로그인 없이 질문할 수 있습니다.</p>\n',
    ].join("\n"),
  );
  expect(html.indexOf('id="pp-both"')).toBeLessThan(html.indexOf('id="pp-widget"'));
});

test("로그인 사이트의 상자는 위젯 자리 안에서 처음에 숨겨져 있고 정보 알림을 제목과 본문으로 든다", () => {
  const html = pageHtml([site()], 30);

  const login =
    /<div class="pp-login" id="pp-login" hidden>(.*?)<\/div>\s*<\/div>\s*<\/div>/su.exec(html);
  expect(login?.[1]).toContain('<div class="pp-alert pp-alert-info" role="status">');
  expect(login?.[1]).toContain("이 사이트는 로그인이 필요합니다.");
  expect(login?.[1]).toContain("로그인은 아직 제공하지 않습니다.");
  expect(login?.[1]).toMatch(/<svg[^>]*aria-hidden="true"/u);
  expect(html.indexOf('id="pp-login"')).toBeGreaterThan(html.indexOf('id="pp-widget"'));
  expect(html.indexOf('id="pp-login"')).toBeLessThan(html.indexOf("<agent-os-widget"));
});

test("보고서 링크는 처음에 숨겨져 있고 새 탭에 noopener 로 열며 바깥 링크 아이콘은 꾸밈이다", () => {
  const html = pageHtml([site({ reportUrl: "https://report.example/calc" })], 30);

  const link = /<a class="pp-report" id="pp-report"([^>]*)>(.*?)<\/a>/su.exec(html);
  expect(link?.[1]).toContain('target="_blank"');
  expect(link?.[1]).toContain('rel="noopener"');
  expect(link?.[1]).toContain("hidden");
  expect(link?.[2]).toContain("이 에이전트의 평가 보고서");
  expect(link?.[2]).toMatch(/<svg[^>]*aria-hidden="true"/u);
  // 주소는 사이트마다 달라 데이터 블록에서 스크립트가 채운다.
  expect(html.replace(DATA_BLOCK, "")).not.toContain("report.example");
});

test("읽는 차례는 셀렉트, 다크 모드 스위치, 위젯 자리, 고지 전문 단추, 보고서 링크 순이다", () => {
  const html = pageHtml(TWO_SITES, 30);

  const order = [
    'id="pp-site"',
    'id="pp-mode"',
    'id="pp-widget"',
    'id="pp-notice-toggle"',
    'id="pp-report"',
  ].map((marker) => html.indexOf(marker));
  expect(order.every((at) => at > -1)).toBe(true);
  expect([...order].sort((a, b) => a - b)).toEqual(order);
});

test("페이지 스크립트가 id 로 찾는 요소가 모두 마크업에 있다", () => {
  // 요소 하나가 빠지면 스크립트의 부품 찾기가 실패해 아무 표시 없이 멈춘다(티켓 07 의 PR 봇이 짚었다). 스크립트의 원문에서
  // 찾는 id 를 모아 사이트가 여럿인 페이지의 마크업과 맞댄다.
  const script = readFileSync(join(import.meta.dirname, "..", "browser", "portal.ts"), "utf-8");
  const wanted = new Set(
    [...script.matchAll(/(?:[Bb]yId|getElementById)\(\s*"(pp-[a-z-]+)"/gu)].flatMap((found) =>
      found[1] === undefined ? [] : [found[1]],
    ),
  );
  const html = pageHtml(TWO_SITES, 30);

  expect(wanted.size).toBeGreaterThanOrEqual(19);
  const missing = [...wanted].filter((id) => !html.includes(`id="${id}"`));
  expect(missing).toEqual([]);
});

test("질의나 쿠키를 받지 않으므로 같은 입력은 같은 글이다", () => {
  expect(pageHtml([site()], 30)).toBe(pageHtml([site()], 30));
});
