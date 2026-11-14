// 위젯 미리보기 페이지의 페이지 스크립트(pilot-portal 명세 "페이지"). 서버가 시작 때 타입만 벗겨 `/portal/portal.js` 로 내는 고전
// 스크립트라 import 와 export 가 없고 함수 하나로 감싼다(번들러가 없다). 그래서 서버 쪽 `server/paths.ts` 를 읽지 못하고
// 사이트 끝점의 모양을 아래에 다시 적는다. 둘이 어긋나면 위젯 미리보기 페이지 e2e(`e2e/acknowledge.e2e.ts`)가 빨개진다(상태·확인·토큰
// 끝점을 실제로 부르는 사례다). 그 경로를 바꿀 때는 `server/paths.ts` 도 같이 고친다.
//
// 하는 일은 여섯이다. 데이터 블록에서 사이트 목록을 읽는다, `?site=` 의 사이트를(없거나 모르면 첫 사이트를) 고른다, 뿌리와
// 제목과 `<h1>` 과 위젯 요소와 위쪽 띠의 스위치와 보고서 링크를 그 사이트의 값으로 채운다, 위젯이 부를 `tokenProvider` 를 그
// 사이트의 토큰 끝점으로 둔다, 고른 사이트의 고지 확인 여부를 묻고 위젯 자리에 덮개(미확인)나 위젯(확인)을 보인다, 셀렉트로
// 사이트를 바꾸면 같은 일을 다시 한다.
//
// 위젯 자리 안의 면은 하나만 보인다. 상태를 묻는 동안은 아무것도 보이지 않다가 0.3초를 넘기면 뼈대를 보이고, 미확인이면 덮개를,
// 확인했으면 위젯과 짧은 고지를 보이고, 로그인 사이트면 상태를 묻지 않고 로그인 안내 상자를 보인다. 덮개는 나타날 때 포커스를
// 옮기지 않는다. 확인이 기록되면 덮개를 걷고 포커스를 위젯 요소 자신이 아니라 그것을 감싼 상자(`#pp-widget`, `tabindex="-1"`)로
// 옮긴다.
//
// 위젯 요소는 사이트를 고를 때마다 새로 만든다. 위젯은 같은 에이전트의 화면에 든 대화를 그대로 두므로(요소의 `agent` 가 바뀔
// 때만 새로 띄운다), 요소를 재사용하면 같은 에이전트의 두 사이트 사이를 바꿔도 앞 사이트의 대화가 화면에 남는다. 새 요소는
// 붙자마자 저장한 대화의 묶음(발급자와 `sub`)을 새 사이트의 토큰과 견주어 다르면 비운다. 확인이 기록된 뒤에도 새로 만든다.
// 확인 전에 붙은 요소가 저장한 대화를 되돌리려고 토큰을 불렀다가 401 을 받으면 입력창이 막힌 채로 남기 때문이다.
//
// 이 파일에서만 전역 `fetch` 를 쓴다(`web/eslint.config.mjs` 의 예외 블록). 부르는 것이 Agent OS 의 API 가 아니라
// 위젯 미리보기 페이지 자신의 끝점이라 생성 클라이언트를 거치지 않는다.

(function (): void {
  type Assurance = "anonymous" | "login" | "both";

  interface SiteData {
    readonly name: string;
    readonly agent: string;
    readonly heading: string;
    readonly intro: string | null;
    readonly theme: string;
    readonly mode: string | null;
    readonly assurance: Assurance;
    readonly notice: string;
    readonly reportUrl: string | null;
  }

  /** 위젯 자리 안에서 한 번에 하나만 보이는 면. 상태를 묻는 답이 오기 전에는 아무것도 보이지 않는다. */
  type View = "asking" | "waiting" | "cover" | "widget" | "login";

  interface Parts {
    readonly box: HTMLElement;
    readonly skeleton: HTMLElement;
    readonly cover: HTMLElement;
    readonly coverNotice: HTMLElement;
    readonly failure: HTMLElement;
    readonly acknowledge: HTMLElement;
    readonly login: HTMLElement;
    readonly notice: HTMLElement;
    readonly toggle: HTMLElement;
    readonly noticeFull: HTMLElement;
    readonly both: HTMLElement;
    readonly switched: HTMLElement;
    readonly switchedTemplate: HTMLTemplateElement;
    readonly report: HTMLAnchorElement;
    readonly modeSwitch: HTMLInputElement;
    readonly modeState: HTMLElement;
    /** 사이트가 하나면 서버가 셀렉트를 그리지 않아 없다. */
    readonly select: HTMLSelectElement | null;
  }

  /** 답이 이 시간을 넘기면 뼈대를 보인다. 그 안에는 깜박임 없이 곧바로 다음 면으로 간다. */
  const SKELETON_DELAY_MS = 300;

  function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
  }

  function textOrNull(value: unknown): string | null | undefined {
    return value === null || typeof value === "string" ? value : undefined;
  }

  function assuranceOf(value: unknown): Assurance | undefined {
    return value === "anonymous" || value === "login" || value === "both" ? value : undefined;
  }

  function readSite(value: unknown): SiteData | undefined {
    if (!isRecord(value)) {
      return undefined;
    }
    const { name, agent, heading, intro, theme, mode, assurance, notice, reportUrl } = value;
    const introText = textOrNull(intro);
    const modeText = textOrNull(mode);
    const reportText = textOrNull(reportUrl);
    const assuranceValue = assuranceOf(assurance);
    if (
      typeof name !== "string" ||
      typeof agent !== "string" ||
      typeof heading !== "string" ||
      typeof theme !== "string" ||
      typeof notice !== "string" ||
      introText === undefined ||
      modeText === undefined ||
      reportText === undefined ||
      assuranceValue === undefined
    ) {
      return undefined;
    }
    return {
      name,
      agent,
      heading,
      intro: introText,
      theme,
      mode: modeText,
      assurance: assuranceValue,
      notice,
      reportUrl: reportText,
    };
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

  /**
   * 위젯이 요청을 보낼 때 부르는 토큰 함수. `onUse` 는 토큰을 받으러 나가기 직전에 불린다. 토큰은 사람이 요청을 보낼 때만이
   * 아니라 위젯이 붙자마자 저장한 대화를 되돌리려고도 받는다.
   */
  function tokenProviderOf(site: SiteData, onUse: () => void): () => Promise<string> {
    return async (): Promise<string> => {
      onUse();
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
   * 확인하지 않은 것으로 읽어 덮개를 보인다. 확인 없이 위젯이 열리지 않는 쪽이 안전하고, e2e 가 이 갈래를 고정한다. 로그인
   * 사이트는 상태 끝점이 403 이라 아예 묻지 않으므로(`choose`) 이 갈래와 로그인 안내가 만나지 않는다.
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

  function inputById(id: string): HTMLInputElement | null {
    const found = document.getElementById(id);
    return found instanceof HTMLInputElement ? found : null;
  }

  function templateById(id: string): HTMLTemplateElement | null {
    const found = document.getElementById(id);
    return found instanceof HTMLTemplateElement ? found : null;
  }

  function anchorById(id: string): HTMLAnchorElement | null {
    const found = document.getElementById(id);
    return found instanceof HTMLAnchorElement ? found : null;
  }

  function findParts(): Parts | undefined {
    const box = byId("pp-widget");
    const skeleton = byId("pp-skeleton");
    const cover = byId("pp-cover");
    const coverNotice = byId("pp-cover-notice");
    const failure = byId("pp-cover-failure");
    const acknowledge = byId("pp-acknowledge");
    const login = byId("pp-login");
    const notice = byId("pp-notice");
    const toggle = byId("pp-notice-toggle");
    const noticeFull = byId("pp-notice-full");
    const both = byId("pp-both");
    const switched = byId("pp-switched");
    const switchedTemplate = templateById("pp-switched-template");
    const report = anchorById("pp-report");
    const modeSwitch = inputById("pp-mode");
    const modeState = byId("pp-mode-state");
    const picked = document.getElementById("pp-site");
    if (
      box === null ||
      skeleton === null ||
      cover === null ||
      coverNotice === null ||
      failure === null ||
      acknowledge === null ||
      login === null ||
      notice === null ||
      toggle === null ||
      noticeFull === null ||
      both === null ||
      switched === null ||
      switchedTemplate === null ||
      report === null ||
      modeSwitch === null ||
      modeState === null
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
      login,
      notice,
      toggle,
      noticeFull,
      both,
      switched,
      switchedTemplate,
      report,
      modeSwitch,
      modeState,
      select: picked instanceof HTMLSelectElement ? picked : null,
    };
  }

  /** 지금 위젯 자리에 붙은 위젯 요소. 로그인 사이트에는 없다. */
  let widget: HTMLElement | null = null;

  function show(parts: Parts, view: View): void {
    parts.skeleton.hidden = view !== "waiting";
    parts.cover.hidden = view !== "cover";
    parts.login.hidden = view !== "login";
    if (widget !== null) {
      widget.hidden = view !== "widget";
    }
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

  /** 사이트를 바꾼 뒤의 정보 글을 세운다. 템플릿을 복제해 `role="status"` 자리에 넣어야 화면 읽기 프로그램이 새 글로 읽는다. */
  function announceSwitched(parts: Parts): void {
    parts.switched.replaceChildren(parts.switchedTemplate.content.cloneNode(true));
  }

  function clearSwitched(parts: Parts): void {
    parts.switched.replaceChildren();
  }

  /** 스위치를 눌러 고른 모드. 사이트를 고르면 지우고, 없으면 그 사이트의 `mode`(그것도 없으면 시스템 설정)를 따른다. */
  let modeOverride: "dark" | "light" | null = null;

  function effectiveMode(site: SiteData): string | null {
    return modeOverride ?? site.mode;
  }

  function showModeState(parts: Parts): void {
    parts.modeState.textContent = parts.modeSwitch.checked ? "켜짐" : "꺼짐";
  }

  /** 스위치의 처음 값. 사이트의 `mode` 가 있으면 그것이고 없으면 시스템 설정이다. */
  function syncModeSwitch(parts: Parts, site: SiteData): void {
    const system = window.matchMedia("(prefers-color-scheme: dark)").matches;
    parts.modeSwitch.checked = site.mode === null ? system : site.mode === "dark";
    showModeState(parts);
  }

  /**
   * 위젯 요소를 새로 만들어 위젯 자리에 붙인다(로그인 사이트는 만들지 않는다). 속성 다섯을 채우고 토큰 함수를 둔다. 위젯
   * 번들이 아직 요소를 정의하지 않았을 수 있다. 속성은 요소가 올라올 때 읽히고, 이 프로퍼티는 정의 전후 어느 때든 둔다.
   * 사람이 위젯을 만진 뒤(눌렀거나 키를 눌렀다)의 토큰 요청만 정보 글을 거둔다. 위젯이 붙자마자 저장한 대화를 되돌리려고
   * 토큰을 받는 것은 사람이 요청을 보낸 것이 아니다.
   */
  function mountWidget(parts: Parts, site: SiteData): void {
    // 서버가 내린 속성 없는 자리표시 요소도 함께 걷는다. 남기면 위젯이 둘이 되고 그 요소는 설정 오류를 그린다.
    parts.box.querySelectorAll("agent-os-widget").forEach((old) => {
      old.remove();
    });
    widget = null;
    if (site.assurance === "login") {
      return;
    }
    const element = document.createElement("agent-os-widget");
    element.hidden = true;
    element.setAttribute("agent", site.agent);
    element.setAttribute("heading", site.heading);
    setOrRemove(element, "intro", site.intro);
    element.setAttribute("theme", site.theme);
    setOrRemove(element, "mode", effectiveMode(site));
    let touched = false;
    for (const type of ["pointerdown", "keydown"]) {
      element.addEventListener(
        type,
        () => {
          touched = true;
        },
        true,
      );
    }
    Reflect.set(
      element,
      "tokenProvider",
      tokenProviderOf(site, () => {
        if (touched) {
          clearSwitched(parts);
        }
      }),
    );
    parts.box.append(element);
    widget = element;
  }

  /** 고른 사이트의 값으로 뿌리와 제목과 띠와 단추 줄과 보고서 링크와 위젯 요소를 채운다. */
  function draw(parts: Parts, site: SiteData): void {
    const root = document.documentElement;
    root.setAttribute("data-theme", site.theme);
    setOrRemove(root, "data-mode", effectiveMode(site));
    document.title = site.heading;
    const heading = document.getElementById("pp-heading");
    if (heading !== null) {
      heading.textContent = site.heading;
    }
    syncModeSwitch(parts, site);
    parts.both.hidden = site.assurance !== "both";
    if (site.reportUrl === null) {
      parts.report.removeAttribute("href");
      parts.report.hidden = true;
    } else {
      parts.report.setAttribute("href", site.reportUrl);
      parts.report.hidden = false;
    }
    mountWidget(parts, site);
  }

  let current: SiteData | undefined;
  /** 사이트를 고를 때마다 하나 늘어난다. 앞 사이트가 보낸 요청의 늦은 답이 지금 화면을 덮지 못하게 가리는 번호다. */
  let generation = 0;
  let skeletonTimer: number | undefined;

  /** 그 사이트의 고지 확인 여부를 묻고 답에 맞는 면을 보인다. 답이 오기까지는 아무것도 보이지 않는다. */
  function ask(parts: Parts, site: SiteData): void {
    const mine = generation;
    show(parts, "asking");
    skeletonTimer = window.setTimeout(() => {
      show(parts, "waiting");
    }, SKELETON_DELAY_MS);
    void wasAcknowledged(site).then((acknowledged) => {
      if (mine !== generation) {
        return;
      }
      window.clearTimeout(skeletonTimer);
      show(parts, acknowledged ? "widget" : "cover");
    });
  }

  /** 사이트를 고른다. 처음 열 때도 셀렉트로 바꿀 때도 같은 일이다(정보 글만 바꿀 때 더한다). */
  function choose(parts: Parts, site: SiteData): void {
    generation += 1;
    window.clearTimeout(skeletonTimer);
    current = site;
    modeOverride = null;
    const url = new URL(window.location.href);
    url.searchParams.set("site", site.name);
    window.history.replaceState(null, "", url);
    if (parts.select !== null) {
      parts.select.value = site.name;
    }
    fillNotice(parts, site);
    draw(parts, site);
    if (site.assurance === "login") {
      show(parts, "login");
    } else {
      ask(parts, site);
    }
  }

  function bind(parts: Parts, sites: readonly SiteData[]): void {
    parts.acknowledge.addEventListener("click", () => {
      // 기록하는 동안의 두 번째 누름은 무시한다. `disabled` 가 아니라 `aria-busy` 라 포커스가 단추에 남는다.
      if (parts.acknowledge.getAttribute("aria-busy") === "true" || current === undefined) {
        return;
      }
      const site = current;
      const mine = generation;
      parts.failure.hidden = true;
      markBusy(parts);
      void recordAcknowledgement(site).then((recorded) => {
        // 기록하는 동안 사이트를 바꿨으면 이 답은 앞 사이트의 것이다. 지금 화면의 덮개와 포커스를 건드리지 않는다.
        if (mine !== generation) {
          return;
        }
        clearBusy(parts);
        if (recorded) {
          mountWidget(parts, site);
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
    parts.modeSwitch.addEventListener("change", () => {
      modeOverride = parts.modeSwitch.checked ? "dark" : "light";
      document.documentElement.setAttribute("data-mode", modeOverride);
      widget?.setAttribute("mode", modeOverride);
      showModeState(parts);
    });
    parts.select?.addEventListener("change", () => {
      const picked = sites.find((site) => site.name === parts.select?.value);
      if (picked === undefined || picked === current) {
        return;
      }
      choose(parts, picked);
      announceSwitched(parts);
    });
  }

  const sites = readSites();
  const wanted = new URLSearchParams(window.location.search).get("site");
  const chosen = sites.find((site) => site.name === wanted) ?? sites[0];
  const parts = findParts();
  if (chosen === undefined || parts === undefined) {
    return;
  }
  bind(parts, sites);
  choose(parts, chosen);
})();
