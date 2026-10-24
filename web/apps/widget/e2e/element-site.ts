// 페이지 안 위젯을 품는 사이트 페이지(web-widget 티켓 10, 명세 "임베드"의 페이지 안 방식). site.ts 의 서버가 같은 두 호스트
// 이름(허용 출처 `site.localhost`, 허용 밖 출처 `other.localhost`)으로 낸다.
//
// - `/element` 는 `<agent-os-widget>` 하나와 번들 script 한 줄을 둔 페이지다. 질의 `agent` 가 요소의 에이전트다.
// - 사이트 스크립트(`/element/page.js`)는 요소 뒤, 번들 앞에서 돈다. 요소가 정의되기 전에 `tokenProvider` 를 대입하고
//   (업그레이드가 그 값을 옮겨 담는 길), 부른 횟수를 body 의 `data-token-calls` 에, CSP 위반을 `data-violations` 에 적는다.
//   토큰은 이 서버의 `/token` 에서 받는다.
// - 질의로 판을 고른다. `crossorigin=1` 은 번들 script 에 `crossorigin="anonymous"` 를 붙인다. `clobber=1` 은 번들 script
//   앞에 `<img name="currentScript">`(src 는 허용 밖 출처)를 두어 `document.currentScript` 를 가린다. `hostile=1` 은 위젯을
//   깨려는 사이트 CSS(`/element/hostile.css`)를 싣는다. `bare=1` 은 요소와 번들 없이 같은 사이트만 낸다. `csp=1` 은
//   `elementCsp()` 의 정책을 응답 헤더로 단다.
// - 요소의 크기는 사이트 CSS(`/element/site.css`)가 정한다. 인라인 script 와 style 속성을 쓰지 않아 CSP 판도 `'self'` 로
//   사이트 자기 파일을 싣는다.

import type { SiteOrigins } from "./site";

/** site.ts 의 서버가 그대로 내는 답. */
export interface Answer {
  readonly status: number;
  readonly headers: Readonly<Record<string, string>>;
  readonly body: string;
}

/**
 * CSP 판의 사이트 정책. 임베드 안내(EMBED.md)가 페이지 안 방식에 열라고 한 자리(`script-src`·`connect-src`·`font-src`에
 * 위젯 출처)만 열고 `style-src` 는 `'self'` 다. 나머지는 `default-src 'none'` 이 막는다. `img-src 'self'` 는 브라우저가
 * 스스로 받는 파비콘의 위반을 막는다.
 */
export function elementCsp(widgetOrigin: string): string {
  return [
    "default-src 'none'",
    `script-src 'self' ${widgetOrigin}`,
    `connect-src 'self' ${widgetOrigin}`,
    `font-src ${widgetOrigin}`,
    "style-src 'self'",
    "img-src 'self'",
  ].join("; ");
}

const SITE_SCRIPT = `// 페이지 안 위젯의 사이트 스크립트. 번들보다 먼저 돈다.
document.body.dataset.tokenCalls = "0";
document.body.dataset.violations = "";
document.addEventListener("securitypolicyviolation", (event) => {
  document.body.dataset.violations += event.violatedDirective + " " + event.blockedURI + "\\n";
});
const widget = document.querySelector("agent-os-widget");
if (widget !== null) {
  widget.tokenProvider = async () => {
    document.body.dataset.tokenCalls = String(Number(document.body.dataset.tokenCalls) + 1);
    return (await fetch("/token")).text();
  };
}
`;

/** 사이트가 정하는 요소의 크기. */
const SITE_CSS = `agent-os-widget {
  width: 400px;
  height: 600px;
}
`;

/**
 * 위젯을 깨려는 사이트 CSS. 뿌리 글자 크기와 상속 속성(글자 간격 등)은 shadow 경계를 넘어 물려지고, 태그 선택자는 넘지
 * 못한다. 위젯의 크기가 이것과 무관해야 한다.
 */
const HOSTILE_CSS = `html {
  font-size: 10px;
}
body {
  color: rgb(200, 0, 0);
  font-family: serif;
  letter-spacing: 3px;
  line-height: 3;
  word-spacing: 8px;
}
button,
textarea {
  background: rgb(255, 0, 0);
  padding: 40px;
}
p,
div,
h2 {
  font-size: 2rem;
  margin: 30px;
}
`;

function attribute(value: string): string {
  return value.replaceAll("&", "&amp;").replaceAll('"', "&quot;").replaceAll("<", "&lt;");
}

interface PageOptions {
  readonly agent: string;
  readonly crossorigin: boolean;
  readonly clobber: boolean;
  readonly hostile: boolean;
  readonly bare: boolean;
}

function page(origins: SiteOrigins, options: PageOptions): string {
  const crossorigin = options.crossorigin ? ' crossorigin="anonymous"' : "";
  return `<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>사이트(페이지 안)</title>
<link rel="stylesheet" href="/element/site.css">
${options.hostile ? '<link rel="stylesheet" href="/element/hostile.css">' : ""}
</head>
<body>
<h1>사이트</h1>
<p id="site-text">사이트의 문단</p>
<button id="site-button" type="button">사이트의 버튼</button>
${options.bare ? "" : `<agent-os-widget agent="${attribute(options.agent)}"></agent-os-widget>`}
<script src="/element/page.js"></script>
${options.clobber ? `<img name="currentScript" alt="" src="${origins.other}/clobber">` : ""}
${options.bare ? "" : `<script src="${origins.widget}/widget/element.js"${crossorigin}></script>`}
</body>
</html>
`;
}

/** 페이지 안 방식의 경로면 그 답, 아니면 null. */
export function elementAnswer(url: URL, origins: SiteOrigins): Answer | null {
  const flag = (name: string): boolean => url.searchParams.get(name) === "1";
  switch (url.pathname) {
    case "/element": {
      const headers: Record<string, string> = { "Content-Type": "text/html; charset=utf-8" };
      if (flag("csp")) {
        headers["Content-Security-Policy"] = elementCsp(origins.widget);
      }
      const body = page(origins, {
        agent: url.searchParams.get("agent") ?? "echo",
        crossorigin: flag("crossorigin"),
        clobber: flag("clobber"),
        hostile: flag("hostile"),
        bare: flag("bare"),
      });
      return { status: 200, headers, body };
    }
    case "/element/page.js":
      return {
        status: 200,
        headers: { "Content-Type": "text/javascript; charset=utf-8" },
        body: SITE_SCRIPT,
      };
    case "/element/site.css":
      return {
        status: 200,
        headers: { "Content-Type": "text/css; charset=utf-8" },
        body: SITE_CSS,
      };
    case "/element/hostile.css":
      return {
        status: 200,
        headers: { "Content-Type": "text/css; charset=utf-8" },
        body: HOSTILE_CSS,
      };
    default:
      return null;
  }
}
