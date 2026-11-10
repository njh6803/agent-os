// 질문 페이지의 페이지 스크립트(pilot-portal 명세 "페이지"). 서버가 시작 때 타입만 벗겨 `/portal/portal.js` 로 내는 고전
// 스크립트라 import 와 export 가 없고 함수 하나로 감싼다(번들러가 없다). 그래서 서버 쪽 `server/paths.ts` 를 읽지 못하고
// 사이트 끝점의 모양을 아래에 다시 적는다. 둘이 어긋나는지는 이 티켓의 e2e 가 보지 못한다(토큰 끝점을 부르는 사례가 아직
// 없다). 그 경로를 바꿀 때는 `server/paths.ts` 도 같이 고친다.
//
// 하는 일은 넷이다. 데이터 블록에서 사이트 목록을 읽는다, `?site=` 의 사이트를(없거나 모르면 첫 사이트를) 고른다, 뿌리와
// 제목과 `<h1>` 과 위젯 요소를 그 사이트의 값으로 채운다, 위젯이 부를 `tokenProvider` 를 그 사이트의 토큰 끝점으로 둔다.
//
// 이 파일에서만 전역 `fetch` 를 쓴다(`web/eslint.config.mjs` 의 예외 블록). 부르는 것이 Agent OS 의 API 가 아니라 질문
// 페이지 자신의 끝점이라 생성 클라이언트를 거치지 않는다.

(function (): void {
  interface SiteData {
    readonly name: string;
    readonly agent: string;
    readonly heading: string;
    readonly intro: string | null;
    readonly theme: string;
    readonly mode: string | null;
  }

  function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
  }

  function textOrNull(value: unknown): string | null | undefined {
    return value === null || typeof value === "string" ? value : undefined;
  }

  function readSite(value: unknown): SiteData | undefined {
    if (!isRecord(value)) {
      return undefined;
    }
    const { name, agent, heading, intro, theme, mode } = value;
    const introText = textOrNull(intro);
    const modeText = textOrNull(mode);
    if (
      typeof name !== "string" ||
      typeof agent !== "string" ||
      typeof heading !== "string" ||
      typeof theme !== "string" ||
      introText === undefined ||
      modeText === undefined
    ) {
      return undefined;
    }
    return { name, agent, heading, intro: introText, theme, mode: modeText };
  }

  function readSites(): SiteData[] {
    const block = document.getElementById("pp-data");
    const parsed: unknown = JSON.parse(block?.textContent ?? "{}");
    const list = isRecord(parsed) ? parsed["sites"] : undefined;
    const sites: SiteData[] = [];
    if (Array.isArray(list)) {
      const entries: unknown[] = list;
      for (const entry of entries) {
        const site = readSite(entry);
        if (site !== undefined) {
          sites.push(site);
        }
      }
    }
    return sites;
  }

  /** 값이 있으면 속성으로 달고 없으면 뗀다. */
  function setOrRemove(element: Element, name: string, value: string | null): void {
    if (value === null) {
      element.removeAttribute(name);
    } else {
      element.setAttribute(name, value);
    }
  }

  function tokenProviderOf(site: SiteData): () => Promise<string> {
    return async (): Promise<string> => {
      const response = await fetch(`/portal/sites/${encodeURIComponent(site.name)}/token`, {
        method: "POST",
        credentials: "same-origin",
      });
      if (response.status !== 200) {
        throw new Error(`토큰 끝점이 ${String(response.status)} 로 답했다`);
      }
      return response.text();
    };
  }

  function draw(site: SiteData): void {
    const root = document.documentElement;
    root.setAttribute("data-theme", site.theme);
    setOrRemove(root, "data-mode", site.mode);
    document.title = site.heading;
    const heading = document.getElementById("pp-heading");
    if (heading !== null) {
      heading.textContent = site.heading;
    }
    const widget = document.querySelector("agent-os-widget");
    if (widget === null) {
      return;
    }
    widget.setAttribute("agent", site.agent);
    widget.setAttribute("heading", site.heading);
    setOrRemove(widget, "intro", site.intro);
    widget.setAttribute("theme", site.theme);
    setOrRemove(widget, "mode", site.mode);
    // 위젯 번들이 아직 요소를 정의하지 않았을 수 있다. 속성은 요소가 올라올 때 읽히고, 이 프로퍼티는 정의 전후 어느 때든 둔다.
    Reflect.set(widget, "tokenProvider", tokenProviderOf(site));
  }

  const sites = readSites();
  const wanted = new URLSearchParams(window.location.search).get("site");
  const chosen = sites.find((site) => site.name === wanted) ?? sites[0];
  if (chosen === undefined) {
    return;
  }
  const url = new URL(window.location.href);
  url.searchParams.set("site", chosen.name);
  window.history.replaceState(null, "", url);
  draw(chosen);
})();
