// 페이지 HTML 짓기. 순수 함수라 사이트 값을 넣고 글을 본다. 서버가 질의와 쿠키를 보지 않고 같은 HTML 을 내므로 입력은 사이트
// 목록과 쿠키 수명 일수뿐이다(pilot-portal 명세 "페이지").

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

test("위젯 자리에 위젯 요소가 속성 없이 서 있다. 속성은 페이지 스크립트가 채운다", () => {
  const html = pageHtml([site()], 30);

  expect(html).toMatch(
    /<div class="pp-widget" id="pp-widget"><agent-os-widget><\/agent-os-widget><\/div>/u,
  );
});

test("위쪽 띠의 자리가 본문 앞에 비어 있다. 내용은 뒤 티켓이 채운다", () => {
  const html = pageHtml([site()], 30);

  expect(html).toContain('<header class="pp-band" id="pp-band"></header>\n<main class="pp-main">');
});

test("질의나 쿠키를 받지 않으므로 같은 입력은 같은 글이다", () => {
  expect(pageHtml([site()], 30)).toBe(pageHtml([site()], 30));
});
