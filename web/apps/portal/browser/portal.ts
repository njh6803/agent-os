// 질문 페이지의 페이지 스크립트(pilot-portal 명세 "페이지"). 서버가 시작 때 타입만 벗겨 `/portal/portal.js` 로 내는 고전
// 스크립트라 import 와 export 가 없고 함수 하나로 감싼다(번들러가 없다). 그래서 서버 쪽 `server/paths.ts` 를 읽지 못하고
// 사이트 끝점의 모양을 아래에 다시 적는다. 둘이 어긋나면 질문 페이지 e2e(`e2e/acknowledge.e2e.ts`)가 빨개진다(상태·확인·토큰
// 끝점을 실제로 부르는 사례다). 그 경로를 바꿀 때는 `server/paths.ts` 도 같이 고친다.
//
// 하는 일은 다섯이다. 데이터 블록에서 사이트 목록을 읽는다, `?site=` 의 사이트를(없거나 모르면 첫 사이트를) 고른다, 뿌리와
// 제목과 `<h1>` 과 위젯 요소를 그 사이트의 값으로 채운다, 위젯이 부를 `tokenProvider` 를 그 사이트의 토큰 끝점으로 둔다, 고른
// 사이트의 고지 확인 여부를 묻고 위젯 자리에 덮개(미확인)나 위젯(확인)을 보인다.
//
// 위젯 자리 안의 면은 하나만 보인다. 상태를 묻는 동안은 아무것도 보이지 않다가 0.3초를 넘기면 뼈대를 보이고, 미확인이면 덮개를,
// 확인했으면 위젯과 짧은 고지를 보인다. 덮개는 나타날 때 포커스를 옮기지 않는다. 확인이 기록되면 덮개를 걷고 포커스를 위젯 요소
// 자신이 아니라 그것을 감싼 상자(`#pp-widget`, `tabindex="-1"`)로 옮긴다.
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
    readonly notice: string;
  }

  /** 위젯 자리 안에서 한 번에 하나만 보이는 면. 상태를 묻는 답이 오기 전에는 아무것도 보이지 않는다. */
  type View = "asking" | "waiting" | "cover" | "widget";

  interface Parts {
    readonly box: HTMLElement;
    readonly skeleton: HTMLElement;
    readonly cover: HTMLElement;
    readonly coverNotice: HTMLElement;
    readonly failure: HTMLElement;
    readonly acknowledge: HTMLElement;
    readonly widget: HTMLElement;
    readonly notice: HTMLElement;
    readonly toggle: HTMLElement;
    readonly noticeFull: HTMLElement;
  }

  /** 답이 이 시간을 넘기면 뼈대를 보인다. 그 안에는 깜박임 없이 곧바로 다음 면으로 간다. */
  const SKELETON_DELAY_MS = 300;

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
    const { name, agent, heading, intro, theme, mode, notice } = value;
    const introText = textOrNull(intro);
    const modeText = textOrNull(mode);
    if (
      typeof name !== "string" ||
      typeof agent !== "string" ||
      typeof heading !== "string" ||
      typeof theme !== "string" ||
      typeof notice !== "string" ||
      introText === undefined ||
      modeText === undefined
    ) {
      return undefined;
    }
    return { name, agent, heading, intro: introText, theme, mode: modeText, notice };
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

  /** 그 사이트의 끝점 주소. `name` 은 상태·확인·토큰 끝점이다. */
  function endpoint(site: SiteData, name: "acknowledgement" | "token"): string {
    return `/portal/sites/${encodeURIComponent(site.name)}/${name}`;
  }

  function tokenProviderOf(site: SiteData): () => Promise<string> {
    return async (): Promise<string> => {
      const response = await fetch(endpoint(site, "token"), {
        method: "POST",
        credentials: "same-origin",
      });
      if (response.status !== 200) {
        throw new Error(`토큰 끝점이 ${String(response.status)} 로 답했다`);
      }
      return response.text();
    };
  }

  /**
   * 이 브라우저가 그 사이트의 고지를 확인했는지. 답이 200 이고 `acknowledged` 가 참일 때만 참이다. 그 밖(다른 상태, 연결 실패)은
   * 확인하지 않은 것으로 읽어 덮개를 보인다. 상태를 묻다 실패했을 때 보일 모습은 명세가 정하지 않았다.
   */
  async function wasAcknowledged(site: SiteData): Promise<boolean> {
    try {
      const response = await fetch(endpoint(site, "acknowledgement"), {
        credentials: "same-origin",
        cache: "no-store",
      });
      if (response.status !== 200) {
        return false;
      }
      const body: unknown = await response.json();
      return isRecord(body) && body["acknowledged"] === true;
    } catch {
      return false;
    }
  }

  /** 고지 확인을 기록한다. 쿠키는 서버가 이 응답으로 낸다. 204 만 기록된 것이다. */
  async function recordAcknowledgement(site: SiteData): Promise<boolean> {
    try {
      const response = await fetch(endpoint(site, "acknowledgement"), {
        method: "POST",
        credentials: "same-origin",
      });
      return response.status === 204;
    } catch {
      return false;
    }
  }

  function byId(id: string): HTMLElement | null {
    const found = document.getElementById(id);
    return found instanceof HTMLElement ? found : null;
  }

  function findParts(): Parts | undefined {
    const widget = document.querySelector("agent-os-widget");
    const box = byId("pp-widget");
    const skeleton = byId("pp-skeleton");
    const cover = byId("pp-cover");
    const coverNotice = byId("pp-cover-notice");
    const failure = byId("pp-cover-failure");
    const acknowledge = byId("pp-acknowledge");
    const notice = byId("pp-notice");
    const toggle = byId("pp-notice-toggle");
    const noticeFull = byId("pp-notice-full");
    if (
      !(widget instanceof HTMLElement) ||
      box === null ||
      skeleton === null ||
      cover === null ||
      coverNotice === null ||
      failure === null ||
      acknowledge === null ||
      notice === null ||
      toggle === null ||
      noticeFull === null
    ) {
      return undefined;
    }
    return {
      box,
      skeleton,
      cover,
      coverNotice,
      failure,
      acknowledge,
      widget,
      notice,
      toggle,
      noticeFull,
    };
  }

  function show(parts: Parts, view: View): void {
    parts.skeleton.hidden = view !== "waiting";
    parts.cover.hidden = view !== "cover";
    parts.widget.hidden = view !== "widget";
    // 짧은 고지와 "고지 전문" 단추는 위젯이 보일 때만 보인다(ADR 0050 의 2026-11-10 이력).
    parts.notice.hidden = view !== "widget";
  }

  /** 고지 글을 문단으로 나눈다. 서버가 문단 사이를 빈 줄 하나로 잇는다(`server/notice.ts`). */
  function paragraphsOf(text: string): HTMLParagraphElement[] {
    return text
      .split("\n\n")
      .map((paragraph) => paragraph.trim())
      .filter((paragraph) => paragraph !== "")
      .map((paragraph) => {
        const element = document.createElement("p");
        element.textContent = paragraph;
        return element;
      });
  }

  function markBusy(parts: Parts): void {
    parts.acknowledge.setAttribute("aria-busy", "true");
    parts.acknowledge.setAttribute("aria-disabled", "true");
  }

  function clearBusy(parts: Parts): void {
    parts.acknowledge.removeAttribute("aria-busy");
    parts.acknowledge.removeAttribute("aria-disabled");
  }

  /** 고른 사이트의 고지 글을 덮개와 전문 자리에 채우고 덮개의 실패 알림과 전문의 펼침을 처음 상태로 둔다. */
  function fillNotice(parts: Parts, site: SiteData): void {
    parts.coverNotice.replaceChildren(...paragraphsOf(site.notice));
    parts.noticeFull.replaceChildren(...paragraphsOf(site.notice));
    parts.noticeFull.hidden = true;
    parts.toggle.setAttribute("aria-expanded", "false");
    parts.failure.hidden = true;
    clearBusy(parts);
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

  let current: SiteData | undefined;

  /** 그 사이트의 고지 확인 여부를 묻고 답에 맞는 면을 보인다. 답이 오기까지는 아무것도 보이지 않는다. */
  function ask(parts: Parts, site: SiteData): void {
    current = site;
    fillNotice(parts, site);
    show(parts, "asking");
    const timer = window.setTimeout(() => {
      show(parts, "waiting");
    }, SKELETON_DELAY_MS);
    void wasAcknowledged(site).then((acknowledged) => {
      window.clearTimeout(timer);
      show(parts, acknowledged ? "widget" : "cover");
    });
  }

  function bind(parts: Parts): void {
    parts.acknowledge.addEventListener("click", () => {
      // 기록하는 동안의 두 번째 누름은 무시한다. `disabled` 가 아니라 `aria-busy` 라 포커스가 단추에 남는다.
      if (parts.acknowledge.getAttribute("aria-busy") === "true" || current === undefined) {
        return;
      }
      parts.failure.hidden = true;
      markBusy(parts);
      void recordAcknowledgement(current).then((recorded) => {
        clearBusy(parts);
        if (recorded) {
          show(parts, "widget");
          parts.box.focus();
        } else {
          parts.failure.hidden = false;
        }
      });
    });
    parts.toggle.addEventListener("click", () => {
      const open = parts.toggle.getAttribute("aria-expanded") === "true";
      parts.toggle.setAttribute("aria-expanded", open ? "false" : "true");
      parts.noticeFull.hidden = open;
    });
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
  const parts = findParts();
  if (parts !== undefined) {
    bind(parts);
    ask(parts, chosen);
  }
})();
