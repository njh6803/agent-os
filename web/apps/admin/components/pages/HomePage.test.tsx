// 관리 화면의 첫 화면. 관리 토큰을 넣고 플러그인 목록을 본다(web-admin 티켓 05).
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 생성 클라이언트, SWR 훅, 스토어는 진짜다. 보는 것은
// 바깥 행동이다. 화면에 보이는 역할과 글자, 경계를 지나는 요청의 헤더, 브라우저 저장소에 남은 것이다.

import { act, fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { inspect } from "node:util";
import { afterEach, describe, expect, test, vi } from "vitest";
import { api, envelope, network, type Plugin, type PluginRow } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { clearTokens, enterAdminToken, enterChannelToken } from "../../testing/token";
import { HomePage } from "./HomePage";
import { PluginPage } from "./PluginPage";

const TOKEN = "adm-7Qx2-page-token";
const REJECTED = "admin-token-the-server-refuses";
const CHANNEL = "chn-5Ht9-page-token";
/** 운영자가 고른 테마를 남기는 localStorage 키(admin-style 명세 "저장"). */
const THEME_KEY = "agent-os-admin-theme";

const CALC: Plugin = {
  kind: "agent",
  name: "calc",
  enabled: true,
  manifest: {
    schema_version: "1",
    kind: "agent",
    name: "calc",
    version: "0.1.0",
    entrypoint: "agent:Calc",
    mcp: ["everything"],
    requires_approval: ["add"],
    conversation_limit: null,
    server: null,
  },
};

const ROWS: PluginRow[] = [
  CALC,
  {
    kind: "agent",
    name: "broken",
    enabled: true,
    reason: "매니페스트를 읽을 수 없다: plugins/agents/broken/plugin.toml",
  },
  {
    kind: "mcp",
    name: "everything",
    enabled: true,
    manifest: {
      schema_version: "1",
      kind: "mcp",
      name: "everything",
      version: "0.1.0",
      entrypoint: null,
      mcp: [],
      requires_approval: [],
      conversation_limit: null,
      server: { command: "npx", args: ["-y", "server-everything"], secret_args: {} },
    },
  },
  {
    kind: "skill",
    name: "summarize",
    enabled: false,
    manifest: {
      schema_version: "1",
      kind: "skill",
      name: "summarize",
      version: "0.1.0",
      entrypoint: null,
      mcp: [],
      requires_approval: [],
      conversation_limit: null,
      server: null,
    },
  },
  {
    kind: "model",
    name: "sonnet",
    enabled: true,
    manifest: {
      schema_version: "1",
      kind: "model",
      name: "sonnet",
      version: "0.1.0",
      entrypoint: null,
      mcp: [],
      requires_approval: [],
      conversation_limit: null,
      server: null,
    },
  },
];

const NO_EFFECT = "로더가 생기기 전에는 효과가 없다";
/** ROWS 의 종류 머리. 종류 이름 옆에 그 종류의 개수가 붙는다. */
const KIND_HEADINGS = ["에이전트 2", "MCP 1", "스킬 1", "모델 1"];

/** 에이전트 묶음의 이름. 머리의 개수는 시험마다 목록이 달라 가리지 않는다. 목록이 섰는지 볼 때 쓴다. */
const AGENTS = kindName("에이전트");

/** 종류 묶음의 이름(종류 이름과 개수)에 맞는 패턴. */
function kindName(kind: string): RegExp {
  return new RegExp(`^${kind} \\d+$`);
}

/**
 * `GET /plugins` 에 답한다. `reply` 는 몇 번째 요청인지(0부터) 받는다. 돌려주는 목록에 요청마다의 `Authorization`
 * 을 쌓는다. 화면이 몇 번 읽었는지와 어떤 토큰을 실었는지가 여기서 보인다.
 */
function servePlugins(reply: (call: number) => Response | Promise<Response>): string[] {
  const authorizations: string[] = [];
  network.use(
    http.get(api("/plugins"), ({ request }) => {
      authorizations.push(request.headers.get("Authorization") ?? "(없음)");
      return reply(authorizations.length - 1);
    }),
  );
  return authorizations;
}

function rows(): Response {
  return HttpResponse.json(ROWS);
}

function refused(): Response {
  return HttpResponse.json(envelope("unauthorized", "토큰이 없거나 틀리다"), { status: 401 });
}

function group(heading: string): HTMLElement {
  return screen.getByRole("region", { name: kindName(heading) });
}

function row(heading: string, name: string): HTMLElement {
  const found = within(group(heading))
    .getAllByRole("listitem")
    .find((item) => within(item).queryByText(name) !== null);
  if (found === undefined) {
    throw new Error(`${heading} 묶음에 ${name} 행이 없다`);
  }
  return found;
}

/** 관리 토큰을 넣고 목록이 설 때까지 기다린다. 이어서 누를 사용자를 돌려준다. */
async function showList(): Promise<UserEvent> {
  const user = userEvent.setup();
  renderPage(<HomePage />);
  await enterAdminToken(user, TOKEN);
  await screen.findByRole("region", { name: AGENTS });
  return user;
}

/** 브라우저 저장소 하나의 [키, 값] 전부. */
function entries(storage: Storage): [string, string][] {
  const found: [string, string][] = [];
  for (let index = 0; index < storage.length; index += 1) {
    const key = storage.key(index);
    if (key !== null) {
      found.push([key, storage.getItem(key) ?? ""]);
    }
  }
  return found;
}

/** JSON 값의 잎(객체도 배열도 아닌 값) 전부. */
function leaves(value: unknown): unknown[] {
  if (Array.isArray(value)) {
    return value.flatMap(leaves);
  }
  if (typeof value === "object" && value !== null) {
    return Object.values(value).flatMap(leaves);
  }
  return [value];
}

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("관리 토큰", () => {
  test("관리 토큰이 없으면 넣는 자리가 보이고 관리 요청을 보내지 않는다", async () => {
    renderPage(<HomePage />);

    expect(await screen.findByLabelText("관리 토큰")).toBeTruthy();
    expect(screen.queryByRole("region", { name: AGENTS })).toBeNull();
  });

  test("넣는 자리는 틀 없이 제품 이름과 화면 머리, 설명, 가린 입력과 그 도움말로 선다", async () => {
    renderPage(<HomePage />);

    const field = await screen.findByLabelText<HTMLInputElement>("관리 토큰");
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("관리 토큰 넣기");
    // 제품 이름은 제목 요소가 아닌 글자다. 틀(탐색)과 옛 틀의 제목 "관리 화면"은 없다.
    expect(screen.getByText("Agent OS").closest("h1, h2, h3, h4, h5, h6")).toBeNull();
    expect(screen.queryByRole("navigation")).toBeNull();
    expect(screen.queryByRole("heading", { name: "관리 화면" })).toBeNull();
    expect(
      screen.getByText(
        (_, element) =>
          element?.tagName === "P" &&
          element.textContent ===
            "agent-os serve 를 띄울 때 AGENT_OS_ADMIN_TOKEN 에 준 값이다. 이 탭에만 남고 탭을 닫으면 사라진다.",
      ),
    ).toBeTruthy();
    expect(field.getAttribute("type")).toBe("password");
    expect(field.getAttribute("autocomplete")).toBe("off");
    expect(document.getElementById(field.getAttribute("aria-describedby") ?? "")?.textContent).toBe(
      "넣으면 플러그인 목록을 한 번 읽어 맞는 토큰인지 본다.",
    );
    expect(screen.getByRole("button", { name: "넣기" }).getAttribute("type")).toBe("submit");
    // 지울 채널 토큰이 없으면 아래 줄도 없다. 문서 뿌리에 모드와 밀도를 달지 않는다.
    expect(screen.queryByText("이 탭에 채널 토큰이 남아 있다.")).toBeNull();
    expect(screen.queryByRole("button", { name: "토큰 지우기" })).toBeNull();
    expect(document.documentElement.hasAttribute("data-mode")).toBe(false);
    expect(document.documentElement.hasAttribute("data-density")).toBe(false);
  });

  test("넣은 관리 토큰이 확인 요청의 Authorization 에 실리고 받아들여지면 플러그인 목록이 보인다", async () => {
    const authorizations = servePlugins(rows);
    renderPage(<HomePage />);

    await enterAdminToken(userEvent.setup(), TOKEN);

    expect(await screen.findByRole("region", { name: AGENTS })).toBeTruthy();
    expect(screen.queryByLabelText("관리 토큰")).toBeNull();
    expect(authorizations.length).toBeGreaterThan(0);
    expect(new Set(authorizations)).toEqual(new Set([`Bearer ${TOKEN}`]));
  });

  test("확인 요청이 401 이면 관리 토큰이 거부됐다를 보이고 토큰을 저장하지 않는다", async () => {
    const authorizations = servePlugins(refused);
    renderPage(<HomePage />);

    await enterAdminToken(userEvent.setup(), REJECTED);

    const notice = await screen.findByRole("alert");
    expect(notice.textContent).toContain("관리 토큰이 거부됐다");
    expect(notice.textContent).toContain("서버를 띄울 때 준 값과 같은지 보고 다시 넣는다.");
    expect(authorizations).toEqual([`Bearer ${REJECTED}`]);
    // 넣는 자리로 남되 거부된 토큰은 칸에도 남지 않는다.
    expect(screen.getByLabelText<HTMLInputElement>("관리 토큰").value).toBe("");
    expect(entries(sessionStorage).filter(([, value]) => value.includes(REJECTED))).toEqual([]);
  });

  test("받아들여진 관리 토큰과 넣은 채널 토큰은 sessionStorage 에만 남고 localStorage 에는 테마 밖의 것이 남지 않는다", async () => {
    // 이 브라우저의 localStorage 에는 운영자가 고른 테마가 남을 수 있다(admin-style 티켓 09). 토큰은 거기 없다.
    localStorage.setItem(THEME_KEY, "jjokbit");
    servePlugins(rows);
    renderPage(<HomePage />);
    const user = userEvent.setup();

    await enterAdminToken(user, TOKEN);
    await enterChannelToken(user, CHANNEL);

    const local = entries(localStorage);
    expect(local.filter(([, value]) => value.includes(TOKEN) || value.includes(CHANNEL))).toEqual(
      [],
    );
    expect(local.map(([key]) => key).filter((key) => key !== THEME_KEY)).toEqual([]);
    const stored = entries(sessionStorage);
    expect(stored).toHaveLength(1);
    const [[, value] = ["", ""]] = stored;
    const parsed: unknown = JSON.parse(value);
    // persist 가 붙이는 판 번호(수) 밖에 저장된 값은 토큰 둘이다. 넣는 자리의 알림과 받아들인 횟수 같은 화면의 상태는 남지 않는다.
    expect(leaves(parsed).filter((leaf) => typeof leaf !== "number")).toEqual([TOKEN, CHANNEL]);
  });

  test("같은 탭에서 새로 고쳐도 관리 토큰을 다시 넣지 않는다", async () => {
    const authorizations = servePlugins(rows);
    const first = renderPage(<HomePage />);
    await enterAdminToken(userEvent.setup(), TOKEN);
    await screen.findByRole("region", { name: AGENTS });
    first.unmount();

    // 새로 고침. 모듈을 다시 읽으면 스토어가 새로 서고 그 탭의 sessionStorage 에서 토큰을 되살린다.
    vi.resetModules();
    const reloaded = await import("./HomePage");
    const before = authorizations.length;
    renderPage(<reloaded.HomePage />);

    expect(await screen.findByRole("region", { name: AGENTS })).toBeTruthy();
    expect(screen.queryByLabelText("관리 토큰")).toBeNull();
    expect(authorizations.slice(before)).toEqual([`Bearer ${TOKEN}`]);
  });

  test("관리 요청이 401 을 받으면 관리 토큰을 지우고 입력 화면으로 돌아가 거부됐다고 말한다", async () => {
    servePlugins((call) => (call < 2 ? rows() : refused()));
    renderPage(<HomePage />);
    const user = userEvent.setup();
    await enterAdminToken(user, TOKEN);
    await screen.findByRole("region", { name: AGENTS });

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect((await screen.findByRole("alert")).textContent).toContain("관리 토큰이 거부됐다");
    expect(screen.getByLabelText("관리 토큰")).toBeTruthy();
    expect(screen.queryByRole("region", { name: AGENTS })).toBeNull();
    expect(entries(sessionStorage).filter(([, value]) => value.includes(TOKEN))).toEqual([]);
  });

  test("지운 토큰의 늦은 401 은 그 사이 넣은 새 토큰의 목록에 섞이지 않고 새 토큰을 내려놓지 않는다", async () => {
    const late = Promise.withResolvers<Response>();
    const authorizations = servePlugins((call) => (call === 1 ? late.promise : rows()));
    renderPage(<HomePage />);
    const user = userEvent.setup();
    // 옛 토큰은 확인(0)을 지나고, 목록(1)은 응답을 기다린다.
    await enterAdminToken(user, REJECTED);
    await clearTokens(user);
    await enterAdminToken(user, TOKEN);

    // 새 토큰의 목록은 옛 요청을 나눠 받지 않고 제 요청을 보낸다.
    expect(await screen.findByRole("region", { name: AGENTS })).toBeTruthy();
    expect(authorizations.filter((sent) => sent === `Bearer ${TOKEN}`)).toHaveLength(2);
    late.resolve(refused());
    // 늦은 응답이 처리될 틈을 준다. 옛 요청의 401 이 새 토큰을 내려놓으면 넣는 자리로 돌아간다.
    await new Promise((resolve) => setTimeout(resolve, 200));

    expect(screen.queryByLabelText("관리 토큰")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
    expect(entries(sessionStorage).filter(([, value]) => value.includes(TOKEN))).toHaveLength(1);
  });

  test("토큰 지우기를 누르면 관리 토큰이 사라지고 입력 화면으로 돌아간다", async () => {
    servePlugins(rows);
    renderPage(<HomePage />);
    const user = userEvent.setup();
    await enterAdminToken(user, TOKEN);
    await screen.findByRole("region", { name: AGENTS });

    await clearTokens(user);

    expect(await screen.findByLabelText("관리 토큰")).toBeTruthy();
    expect(screen.queryByRole("region", { name: AGENTS })).toBeNull();
    expect(entries(sessionStorage).filter(([, value]) => value.includes(TOKEN))).toEqual([]);
  });

  test("관리 토큰이 주소에도 화면의 글자에도 콘솔에도 나오지 않는다", async () => {
    const printed: unknown[] = [];
    for (const method of ["log", "info", "warn", "error", "debug"] as const) {
      vi.spyOn(console, method).mockImplementation((...args: unknown[]) => {
        printed.push(...args);
      });
    }
    servePlugins((call) => (call === 0 ? refused() : rows()));
    renderPage(<HomePage />);
    const user = userEvent.setup();

    expect(screen.getByLabelText("관리 토큰").getAttribute("type")).toBe("password");
    await enterAdminToken(user, REJECTED);
    await screen.findByRole("alert");
    const whileRejected = document.documentElement.outerHTML;
    await enterAdminToken(user, TOKEN);
    await screen.findByRole("region", { name: AGENTS });

    for (const token of [REJECTED, TOKEN]) {
      expect(location.href).not.toContain(token);
      expect(whileRejected).not.toContain(token);
      expect(document.documentElement.outerHTML).not.toContain(token);
      expect(printed.map((arg) => inspect(arg)).join("\n")).not.toContain(token);
    }
  });
});

describe("채널 토큰", () => {
  test("채널 토큰을 넣어도 확인 요청을 보내지 않고 넣었다고만 말한다", async () => {
    const authorizations = servePlugins(rows);
    const user = await showList();
    const before = authorizations.length;

    await enterChannelToken(user, CHANNEL);

    expect(authorizations).toHaveLength(before);
  });

  test("채널 토큰을 넣어도 관리 요청에는 관리 토큰만 실린다", async () => {
    const authorizations = servePlugins(rows);
    const user = await showList();
    await enterChannelToken(user, CHANNEL);

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    await waitFor(() => {
      expect(authorizations.length).toBeGreaterThan(2);
    });
    expect(new Set(authorizations)).toEqual(new Set([`Bearer ${TOKEN}`]));
  });

  test("같은 탭에서 새로 고쳐도 채널 토큰을 다시 넣지 않는다", async () => {
    servePlugins(rows);
    const user = userEvent.setup();
    const first = renderPage(<HomePage />);
    await enterAdminToken(user, TOKEN);
    await enterChannelToken(user, CHANNEL);
    first.unmount();

    vi.resetModules();
    const reloaded = await import("./SettingsPage");
    renderPage(<reloaded.SettingsPage />);

    expect(await screen.findByText("채널 토큰을 넣었다")).toBeTruthy();
    expect(screen.queryByLabelText("채널 토큰")).toBeNull();
  });

  test("관리 요청이 401 을 받으면 관리 토큰만 지우고 채널 토큰은 sessionStorage 에 남는다", async () => {
    servePlugins((call) => (call < 2 ? rows() : refused()));
    const user = await showList();
    await enterChannelToken(user, CHANNEL);

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect((await screen.findByRole("alert")).textContent).toContain("관리 토큰이 거부됐다");
    const stored = entries(sessionStorage)
      .map(([, value]) => value)
      .join("\n");
    expect(stored).not.toContain(TOKEN);
    expect(stored).toContain(CHANNEL);
  });

  test("관리 토큰이 거부돼 넣는 자리로 돌아가도 남은 채널 토큰을 토큰 지우기로 지울 수 있다", async () => {
    servePlugins((call) => (call < 2 ? rows() : refused()));
    const user = await showList();
    await enterChannelToken(user, CHANNEL);
    await user.click(screen.getByRole("button", { name: "새로 고침" }));
    expect((await screen.findByRole("alert")).textContent).toContain("관리 토큰이 거부됐다");
    expect(screen.getByText("이 탭에 채널 토큰이 남아 있다.")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "토큰 지우기" }));

    const stored = entries(sessionStorage)
      .map(([, value]) => value)
      .join("\n");
    expect(stored).not.toContain(CHANNEL);
    // 지울 토큰이 없으면 그 줄도 버튼도 없다.
    expect(screen.queryByText("이 탭에 채널 토큰이 남아 있다.")).toBeNull();
    expect(screen.queryByRole("button", { name: "토큰 지우기" })).toBeNull();
    expect(screen.getByLabelText("관리 토큰")).toBeTruthy();
  });

  test("토큰 지우기를 누르면 두 토큰이 모두 사라진다", async () => {
    servePlugins(rows);
    const user = await showList();
    await enterChannelToken(user, CHANNEL);

    await clearTokens(user);

    expect(await screen.findByLabelText("관리 토큰")).toBeTruthy();
    const stored = () =>
      entries(sessionStorage)
        .map(([, value]) => value)
        .join("\n");
    expect(stored()).not.toContain(TOKEN);
    expect(stored()).not.toContain(CHANNEL);
    // 관리 토큰을 다시 넣어도 지운 채널 토큰은 돌아오지 않는다.
    await enterAdminToken(user, TOKEN);
    await screen.findByRole("region", { name: AGENTS });
    expect(stored()).toContain(TOKEN);
    expect(stored()).not.toContain(CHANNEL);
  });

  test("채널 토큰이 주소에도 화면의 글자에도 콘솔에도 나오지 않는다", async () => {
    const printed: unknown[] = [];
    for (const method of ["log", "info", "warn", "error", "debug"] as const) {
      vi.spyOn(console, method).mockImplementation((...args: unknown[]) => {
        printed.push(...args);
      });
    }
    servePlugins(rows);
    const user = await showList();

    await enterChannelToken(user, CHANNEL);

    expect(location.href).not.toContain(CHANNEL);
    expect(document.documentElement.outerHTML).not.toContain(CHANNEL);
    expect(printed.map((arg) => inspect(arg)).join("\n")).not.toContain(CHANNEL);
  });
});

describe("플러그인 목록", () => {
  test("플러그인이 종류별로 묶여 켜짐과 함께 보인다", async () => {
    servePlugins(rows);

    await showList();

    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("플러그인 5");
    expect(screen.getByText("종류마다 등록된 플러그인을 켜고 끈다.")).toBeTruthy();
    const headings = screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    expect(headings).toEqual(KIND_HEADINGS);
    expect(within(group("에이전트")).getAllByRole("listitem")).toHaveLength(2);
    expect(within(row("에이전트", "calc")).getByText("켜짐")).toBeTruthy();
    expect(within(row("MCP", "everything")).getByText("켜짐")).toBeTruthy();
    expect(within(row("스킬", "summarize")).getByText("꺼짐")).toBeTruthy();
    expect(within(row("모델", "sonnet")).getByText("켜짐")).toBeTruthy();
  });

  test("표지 행은 읽을 수 없는 이유를 글자로 보인다", async () => {
    servePlugins(rows);

    await showList();

    const broken = row("에이전트", "broken");
    expect(broken.textContent).toContain("읽을 수 없는 매니페스트");
    expect(broken.textContent).toContain(
      "매니페스트를 읽을 수 없다: plugins/agents/broken/plugin.toml",
    );
  });

  test("등록된 것이 없는 종류는 개수 0 과 등록된 것이 없다 한 줄이다", async () => {
    servePlugins(() => HttpResponse.json(ROWS.filter((plugin) => plugin.kind !== "model")));

    await showList();

    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("플러그인 4");
    expect(group("모델").textContent).toBe("모델 0등록된 것이 없다");
    expect(within(group("모델")).queryByRole("switch")).toBeNull();
  });

  test("이미 보인 목록도 다시 읽다 실패하면 머리에서 개수가 걷힌다", async () => {
    // 실패 뒤에도 읽기 훅은 옛 목록을 들고 있다. 옛 행을 지우듯 옛 개수도 믿지 않는다.
    servePlugins((call) =>
      call < 2
        ? rows()
        : HttpResponse.json(envelope("internal_error", "운영자 파일이 깨졌다"), { status: 500 }),
    );
    const user = await showList();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("플러그인 5");

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    await screen.findByRole("alert");
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("플러그인");
  });

  test("행마다 그 플러그인을 여는 매니페스트 링크가 있고 표지 행도 그렇다", async () => {
    // 디렉터리 이름이 패턴을 어긴 표지는 이름에 주소에 쓸 수 없는 글자가 들 수 있다.
    const odd: PluginRow = {
      kind: "agent",
      name: "Old Calc",
      enabled: true,
      reason: "패턴을 어긴다",
    };
    servePlugins(() => HttpResponse.json([...ROWS, odd]));

    await showList();

    const href = (heading: string, name: string): string | null =>
      within(row(heading, name)).getByRole("link", { name: "매니페스트" }).getAttribute("href");
    expect(href("에이전트", "calc")).toBe("/plugins/agent/calc");
    expect(href("에이전트", "broken")).toBe("/plugins/agent/broken");
    expect(href("에이전트", "Old Calc")).toBe("/plugins/agent/Old%20Calc");
    expect(href("MCP", "everything")).toBe("/plugins/mcp/everything");
    expect(href("스킬", "summarize")).toBe("/plugins/skill/summarize");
    expect(href("모델", "sonnet")).toBe("/plugins/model/sonnet");
    // 이름은 스위치의 이름이라 링크가 아니다.
    expect(within(row("에이전트", "calc")).queryByRole("link", { name: "calc" })).toBeNull();
  });

  test("스킬과 모델 행에만 로더가 생기기 전에는 효과가 없다가 보인다", async () => {
    servePlugins(rows);

    await showList();

    expect(within(row("스킬", "summarize")).getByText(NO_EFFECT)).toBeTruthy();
    expect(within(row("모델", "sonnet")).getByText(NO_EFFECT)).toBeTruthy();
    expect(within(group("에이전트")).queryByText(NO_EFFECT)).toBeNull();
    expect(within(group("MCP")).queryByText(NO_EFFECT)).toBeNull();
  });

  test("운영자 파일이 깨지면 목록 대신 봉투의 메시지와 추적 식별자가 보인다", async () => {
    const message = "운영자 파일이 깨졌다: C:/root/plugins/disabled.toml";
    servePlugins(() =>
      HttpResponse.json(envelope("internal_error", message, "req-9f3c"), { status: 500 }),
    );
    renderPage(<HomePage />);

    await enterAdminToken(userEvent.setup(), TOKEN);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("플러그인 목록을 읽지 못했다");
    expect(alert.textContent).toContain(message);
    expect(alert.textContent).toContain("추적 식별자: req-9f3c");
    expect(screen.queryByRole("region", { name: AGENTS })).toBeNull();
    // 500 봉투는 인증을 지난 뒤의 실패라 토큰은 받아들여졌다. 넣는 자리가 아니라 목록 자리가 실패를 말한다.
    expect(screen.queryByLabelText("관리 토큰")).toBeNull();
    expect(screen.getByRole("button", { name: "새로 고침" })).toBeTruthy();
    expect(entries(sessionStorage).filter(([, value]) => value.includes(TOKEN))).toHaveLength(1);
  });

  test("이미 보인 목록도 다시 읽다 실패하면 옛 행을 지우고 실패를 보인다", async () => {
    // 무엇이 꺼져 있는지 모르는 채 옛 목록을 믿으면 안 된다(스토리 16).
    servePlugins((call) =>
      call < 2
        ? rows()
        : HttpResponse.json(envelope("internal_error", "운영자 파일이 깨졌다"), { status: 500 }),
    );
    const user = await showList();

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect((await screen.findByRole("alert")).textContent).toContain("운영자 파일이 깨졌다");
    expect(screen.queryByRole("region", { name: AGENTS })).toBeNull();
  });

  test("네트워크 실패도 중계가 상류에 닿지 못한 것도 서버에 닿지 못했다로 보인다", async () => {
    // 둘째는 네트워크 에러, 셋째는 봉투가 아닌 500 이다. 중계(rewrites)가 상류에 닿지 못하면 봉투가 아닌 것을 준다.
    const authorizations = servePlugins((call) =>
      call === 0
        ? rows()
        : call === 1
          ? Response.error()
          : new Response("Internal Server Error", { status: 500 }),
    );
    renderPage(<HomePage />);
    const user = userEvent.setup();
    await enterAdminToken(user, TOKEN);

    expect((await screen.findByRole("alert")).textContent).toContain("서버에 닿지 못했다");
    await user.click(screen.getByRole("button", { name: "새로 고침" }));
    await vi.waitFor(() => {
      expect(authorizations).toHaveLength(3);
    });
    await vi.waitFor(() => {
      expect(screen.queryByRole("progressbar")).toBeNull();
    });
    expect(screen.getByRole("alert").textContent).toContain("서버에 닿지 못했다");
    expect(screen.queryByRole("region", { name: AGENTS })).toBeNull();
  });

  test("관리 토큰을 확인하다 서버에 닿지 못하면 그렇게 말하고 토큰을 저장하지 않는다", async () => {
    servePlugins(() => Response.error());
    renderPage(<HomePage />);

    await enterAdminToken(userEvent.setup(), TOKEN);

    const notice = await screen.findByRole("alert");
    expect(notice.textContent).toContain("서버에 닿지 못했다");
    expect(notice.textContent).toContain("agent-os serve가 떠 있는지 보고 다시 넣는다.");
    expect(screen.getByLabelText("관리 토큰")).toBeTruthy();
    expect(entries(sessionStorage).filter(([, value]) => value.includes(TOKEN))).toEqual([]);
  });
});

describe("켜고 끄기", () => {
  interface Put {
    readonly path: string;
    readonly authorization: string;
    readonly body: unknown;
  }

  /** `PUT /plugins/{kind}/{name}/enabled` 에 답한다. 요청마다 경로, `Authorization`, 본문을 쌓는다. */
  function serveSwitch(reply: (call: number) => Response | Promise<Response>): Put[] {
    const puts: Put[] = [];
    network.use(
      http.put(api("/plugins/:kind/:name/enabled"), async ({ request }) => {
        puts.push({
          path: new URL(request.url).pathname,
          authorization: request.headers.get("Authorization") ?? "(없음)",
          body: await request.json(),
        });
        return reply(puts.length - 1);
      }),
    );
    return puts;
  }

  function applied(): Response {
    return new HttpResponse(null, { status: 204 });
  }

  /** ROWS 에서 이름 하나의 켜짐만 바꾼 목록. */
  function rowsWith(name: string, { enabled }: { readonly enabled: boolean }): Response {
    return HttpResponse.json(
      ROWS.map((plugin) => (plugin.name === name ? { ...plugin, enabled } : plugin)),
    );
  }

  function switchOf(heading: string, name: string): HTMLInputElement {
    return within(row(heading, name)).getByRole<HTMLInputElement>("switch");
  }

  test("스위치를 누르면 관리 토큰을 실은 PUT 이 끄기를 보내고 204 뒤에 다시 읽은 목록이 꺼짐을 보인다", async () => {
    // 0은 토큰 확인, 1은 목록, 2는 쓰기 직후의 다시 읽기다.
    const authorizations = servePlugins((call) =>
      call < 2 ? rows() : rowsWith("calc", { enabled: false }),
    );
    const puts = serveSwitch(applied);
    const user = await showList();
    expect(switchOf("에이전트", "calc").checked).toBe(true);

    await user.click(switchOf("에이전트", "calc"));

    expect(await within(row("에이전트", "calc")).findByText("꺼짐")).toBeTruthy();
    expect(switchOf("에이전트", "calc").checked).toBe(false);
    // 204 는 성공이다. 실패로 읽어도 다시 읽은 목록은 꺼짐이라, 실패가 보이지 않는 것을 따로 본다.
    expect(screen.queryByRole("alert")).toBeNull();
    expect(puts).toEqual([
      {
        path: "/api/plugins/agent/calc/enabled",
        authorization: `Bearer ${TOKEN}`,
        body: { enabled: false },
      },
    ]);
    expect(authorizations).toEqual(Array(3).fill(`Bearer ${TOKEN}`));
  });

  test("스위치의 이름은 플러그인 이름이고 그 이름을 눌러도 켜고 끄는 요청이 간다", async () => {
    servePlugins((call) => (call < 2 ? rows() : rowsWith("calc", { enabled: false })));
    const puts = serveSwitch(applied);
    const user = await showList();
    expect(within(row("에이전트", "calc")).getByRole("switch", { name: "calc" })).toBeTruthy();

    await user.click(within(row("에이전트", "calc")).getByText("calc"));

    expect(await within(row("에이전트", "calc")).findByText("꺼짐")).toBeTruthy();
    expect(puts.map(({ path, body }) => [path, body])).toEqual([
      ["/api/plugins/agent/calc/enabled", { enabled: false }],
    ]);
  });

  test("꺼진 행의 스위치를 누르면 켜기를 보낸다", async () => {
    servePlugins((call) => (call < 2 ? rows() : rowsWith("summarize", { enabled: true })));
    const puts = serveSwitch(applied);
    const user = await showList();
    expect(switchOf("스킬", "summarize").checked).toBe(false);

    await user.click(switchOf("스킬", "summarize"));

    expect(await within(row("스킬", "summarize")).findByText("켜짐")).toBeTruthy();
    expect(puts.map(({ path, body }) => [path, body])).toEqual([
      ["/api/plugins/skill/summarize/enabled", { enabled: true }],
    ]);
  });

  test("다시 읽을 때까지 스위치는 뒤집히지 않은 채 막혀 있고 그동안의 누름은 요청을 더 보내지 않는다", async () => {
    const answer = Promise.withResolvers<Response>();
    const reread = Promise.withResolvers<Response>();
    const authorizations = servePlugins((call) => (call < 2 ? rows() : reread.promise));
    const puts = serveSwitch(() => answer.promise);
    const user = await showList();

    await user.click(switchOf("에이전트", "calc"));
    await vi.waitFor(() => {
      expect(puts).toHaveLength(1);
    });

    // PUT 의 응답 전.
    expect(switchOf("에이전트", "calc").checked).toBe(true);
    expect(switchOf("에이전트", "calc").disabled).toBe(true);
    expect(within(row("에이전트", "calc")).getByText("켜짐")).toBeTruthy();
    await user.click(switchOf("에이전트", "calc"));
    // PUT 은 답했고 목록을 다시 읽는 중. 스위치는 아직 옛 값이라 풀리면 같은 PUT 을 한 번 더 보낼 수 있다.
    answer.resolve(applied());
    await vi.waitFor(() => {
      expect(authorizations).toHaveLength(3);
    });
    expect(switchOf("에이전트", "calc").disabled).toBe(true);
    await user.click(switchOf("에이전트", "calc"));
    reread.resolve(rowsWith("calc", { enabled: false }));
    expect(await within(row("에이전트", "calc")).findByText("꺼짐")).toBeTruthy();
    await vi.waitFor(() => {
      expect(switchOf("에이전트", "calc").disabled).toBe(false);
    });
    expect(puts).toHaveLength(1);
    expect(authorizations).toHaveLength(3);
  });

  test("켜고 끄기가 실패하면 메시지와 추적 식별자를 보이고 스위치는 다시 읽은 값이다", async () => {
    const message = "운영자 파일이 깨졌다: C:/root/plugins/disabled.toml";
    // 그 사이 다른 곳에서 꺼졌다. 스위치가 누르기 전의 값이 아니라 다시 읽은 값을 따르는지 여기서 가린다.
    const authorizations = servePlugins((call) =>
      call < 2 ? rows() : rowsWith("calc", { enabled: false }),
    );
    serveSwitch(() =>
      HttpResponse.json(envelope("internal_error", message, "req-77aa"), { status: 500 }),
    );
    const user = await showList();

    await user.click(switchOf("에이전트", "calc"));

    const alert = await screen.findByRole("alert");
    expect(within(alert).getByText("켜고 끄지 못했다: agent/calc")).toBeTruthy();
    expect(alert.textContent).toContain(message);
    expect(alert.textContent).toContain("추적 식별자: req-77aa");
    expect(alert.textContent).toContain("스위치는 다시 읽은 값이다.");
    await vi.waitFor(() => {
      expect(switchOf("에이전트", "calc").checked).toBe(false);
    });
    expect(authorizations).toHaveLength(3);
  });

  test("그 사이 플러그인이 사라져 404 이면 다시 읽은 목록에 그 행이 없어도 메시지가 남는다", async () => {
    servePlugins((call) =>
      call < 2 ? rows() : HttpResponse.json(ROWS.filter((plugin) => plugin.name !== "calc")),
    );
    serveSwitch(() =>
      HttpResponse.json(envelope("not_found", "플러그인이 없다: agent/calc", "req-404c"), {
        status: 404,
      }),
    );
    const user = await showList();

    await user.click(switchOf("에이전트", "calc"));

    await vi.waitFor(() => {
      expect(within(group("에이전트")).getAllByRole("listitem")).toHaveLength(1);
    });
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("플러그인이 없다: agent/calc");
    expect(alert.textContent).toContain("req-404c");
  });

  test("다음 켜고 끄기를 시작하면 앞의 실패가 걷힌다", async () => {
    servePlugins((call) => (call < 3 ? rows() : rowsWith("summarize", { enabled: true })));
    serveSwitch((call) =>
      call === 0
        ? HttpResponse.json(envelope("internal_error", "운영자 파일이 깨졌다"), { status: 500 })
        : applied(),
    );
    const user = await showList();
    await user.click(switchOf("에이전트", "calc"));
    await screen.findByRole("alert");

    await user.click(switchOf("스킬", "summarize"));

    expect(await within(row("스킬", "summarize")).findByText("켜짐")).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("표지 행도 끌 수 있다", async () => {
    servePlugins((call) => (call < 2 ? rows() : rowsWith("broken", { enabled: false })));
    const puts = serveSwitch(applied);
    const user = await showList();

    await user.click(switchOf("에이전트", "broken"));

    expect(await within(row("에이전트", "broken")).findByText("꺼짐")).toBeTruthy();
    expect(puts.map(({ path, body }) => [path, body])).toEqual([
      ["/api/plugins/agent/broken/enabled", { enabled: false }],
    ]);
  });

  test("켜고 끄기가 401 을 받으면 관리 토큰을 지우고 입력 화면으로 돌아가며 목록을 다시 읽지 않는다", async () => {
    const authorizations = servePlugins(rows);
    serveSwitch(refused);
    const user = await showList();

    await user.click(switchOf("에이전트", "calc"));

    expect((await screen.findByRole("alert")).textContent).toContain("관리 토큰이 거부됐다");
    expect(screen.getByLabelText("관리 토큰")).toBeTruthy();
    expect(entries(sessionStorage).filter(([, value]) => value.includes(TOKEN))).toEqual([]);
    // 거부된 토큰으로 다시 읽을 까닭이 없다.
    await new Promise((resolve) => setTimeout(resolve, 100));
    expect(authorizations).toHaveLength(2);
  });

  test("켜고 끈 뒤 다시 읽기도 실패하면 스위치 대신 목록의 실패가 보인다", async () => {
    servePlugins((call) =>
      call < 2
        ? rows()
        : HttpResponse.json(envelope("internal_error", "운영자 파일이 깨졌다"), { status: 500 }),
    );
    serveSwitch(applied);
    const user = await showList();

    await user.click(switchOf("에이전트", "calc"));

    expect((await screen.findByRole("alert")).textContent).toContain("운영자 파일이 깨졌다");
    expect(screen.queryByRole("switch")).toBeNull();
  });

  test("켜고 끈 뒤 전에 열어 본 그 플러그인을 다시 열면 옛 켜짐 없이 새로 읽는다", async () => {
    // 화면을 옮겨 다녀도 SWR 의 캐시는 하나다. 세 번의 그리기에 캐시 하나를 넘긴다.
    const cache = new Map();
    // 0은 토큰 확인, 1은 목록, 2는 쓰기 직후의 다시 읽기다.
    servePlugins((call) => (call < 2 ? rows() : rowsWith("calc", { enabled: false })));
    serveSwitch(applied);
    const reads: string[] = [];
    network.use(
      http.get(api("/plugins/agent/calc"), ({ request }) => {
        reads.push(request.headers.get("Authorization") ?? "(없음)");
        return HttpResponse.json({ ...CALC, enabled: reads.length === 1 });
      }),
    );
    const user = userEvent.setup();
    const opened = renderPage(<PluginPage kind="agent" name="calc" />, cache);
    await enterAdminToken(user, TOKEN);
    expect(await within(screen.getByRole("main")).findByText("켜짐")).toBeTruthy();
    opened.unmount();
    const list = renderPage(<HomePage />, cache);
    await screen.findByRole("region", { name: AGENTS });
    await user.click(within(row("에이전트", "calc")).getByRole("switch"));
    expect(await within(row("에이전트", "calc")).findByText("꺼짐")).toBeTruthy();
    list.unmount();

    renderPage(<PluginPage kind="agent" name="calc" />, cache);

    expect(screen.queryByText("켜짐")).toBeNull();
    expect(await within(screen.getByRole("main")).findByText("꺼짐")).toBeTruthy();
    expect(reads).toHaveLength(2);
  });
});

describe("새로 고침과 상태", () => {
  test("창에 포커스가 돌아오면 목록을 다시 읽는다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const extra: PluginRow = {
      kind: "agent",
      name: "later",
      enabled: true,
      reason: "나중에 생겼다",
    };
    const authorizations = servePlugins((call) =>
      HttpResponse.json(call < 2 ? ROWS : [...ROWS, extra]),
    );
    renderPage(<HomePage />);
    await enterAdminToken(userEvent.setup({ advanceTimers: vi.advanceTimersByTime }), TOKEN);
    await screen.findByRole("region", { name: AGENTS });
    const before = authorizations.length;

    // SWR 은 마운트한 뒤 한동안(focusThrottleInterval) 포커스를 흘려보낸다. 그 너머로 민다.
    await vi.advanceTimersByTimeAsync(10_000);
    fireEvent.focus(window);

    expect(await screen.findByText("later")).toBeTruthy();
    expect(authorizations.length).toBe(before + 1);
  });

  test("시간이 흘러도 스스로 다시 읽지 않는다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const authorizations = servePlugins(rows);
    renderPage(<HomePage />);
    await enterAdminToken(userEvent.setup({ advanceTimers: vi.advanceTimersByTime }), TOKEN);
    await screen.findByRole("region", { name: AGENTS });
    const before = authorizations.length;

    await vi.advanceTimersByTimeAsync(60 * 60 * 1000);

    expect(authorizations.length).toBe(before);
  });

  test("네트워크 연결이 돌아와도 스스로 다시 읽지 않는다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const authorizations = servePlugins(rows);
    renderPage(<HomePage />);
    await enterAdminToken(userEvent.setup({ advanceTimers: vi.advanceTimersByTime }), TOKEN);
    await screen.findByRole("region", { name: AGENTS });
    const before = authorizations.length;

    await vi.advanceTimersByTimeAsync(10_000);
    fireEvent(window, new Event("online"));
    await vi.advanceTimersByTimeAsync(10_000);

    expect(authorizations.length).toBe(before);
  });

  test("실패한 뒤에도 시간이 흘러 스스로 다시 읽지 않는다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const authorizations = servePlugins(() =>
      HttpResponse.json(envelope("internal_error", "운영자 파일이 깨졌다"), { status: 500 }),
    );
    renderPage(<HomePage />);
    await enterAdminToken(userEvent.setup({ advanceTimers: vi.advanceTimersByTime }), TOKEN);
    await screen.findByRole("alert");
    const before = authorizations.length;

    await vi.advanceTimersByTimeAsync(60 * 60 * 1000);

    expect(authorizations.length).toBe(before);
  });

  test("새로 고침 버튼이 목록을 다시 읽는다", async () => {
    const extra: PluginRow = {
      kind: "model",
      name: "haiku",
      enabled: false,
      reason: "새로 생겼다",
    };
    const authorizations = servePlugins((call) =>
      HttpResponse.json(call < 2 ? ROWS : [...ROWS, extra]),
    );
    renderPage(<HomePage />);
    const user = userEvent.setup();
    await enterAdminToken(user, TOKEN);
    await screen.findByRole("region", { name: AGENTS });
    const before = authorizations.length;

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect(await screen.findByText("haiku")).toBeTruthy();
    expect(authorizations.length).toBe(before + 1);
  });

  test("처음 불러오는 중에는 자리표시가 보이고 다시 확인하는 동안에는 이미 보인 행이 남는다", async () => {
    const first = Promise.withResolvers<Response>();
    const again = Promise.withResolvers<Response>();
    servePlugins((call) => (call === 0 ? rows() : call === 1 ? first.promise : again.promise));
    renderPage(<HomePage />);
    const user = userEvent.setup();
    await enterAdminToken(user, TOKEN);

    expect(
      await screen.findByRole("progressbar", { name: "플러그인 목록을 불러오는 중" }),
    ).toBeTruthy();
    // 상태 영역은 상태가 바뀌는 동안 같은 노드로 남고 글만 바뀐다. 영역째 새로 들어오면 알리지 않는 프로그램이 있다.
    const live = within(screen.getByRole("region", { name: "플러그인" })).getByRole("status");
    expect(live.textContent).toBe("플러그인 목록을 불러오는 중");
    expect(screen.queryByRole("region", { name: AGENTS })).toBeNull();
    first.resolve(rows());
    await screen.findByRole("region", { name: AGENTS });
    expect(screen.queryByRole("progressbar")).toBeNull();
    expect(live.isConnected).toBe(true);
    expect(live.textContent).toBe("");

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect(await screen.findByRole("progressbar", { name: "다시 확인하는 중" })).toBeTruthy();
    expect(live.isConnected).toBe(true);
    expect(live.textContent).toBe("다시 확인하는 중");
    expect(screen.getByRole("button", { name: "새로 고침" }).getAttribute("aria-busy")).toBe(
      "true",
    );
    expect(within(row("에이전트", "calc")).getByText("켜짐")).toBeTruthy();
    again.resolve(rows());
    await vi.waitFor(() => {
      expect(screen.queryByRole("progressbar")).toBeNull();
    });
    expect(live.textContent).toBe("");
    expect(screen.getByRole("button", { name: "새로 고침" }).getAttribute("aria-busy")).toBeNull();
    expect(within(row("에이전트", "calc")).getByText("켜짐")).toBeTruthy();
  });

  test("처음 불러오는 표시는 0.3초가 지나야 선다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const first = Promise.withResolvers<Response>();
    servePlugins((call) => (call === 0 ? rows() : first.promise));
    renderPage(<HomePage />);
    await enterAdminToken(userEvent.setup({ advanceTimers: vi.advanceTimersByTime }), TOKEN);
    await screen.findByRole("heading", { level: 1, name: "플러그인" });
    const live = within(screen.getByRole("region", { name: "플러그인" })).getByRole("status");

    // 빨리 끝나는 읽기에서 표시가 번쩍이지 않게 0.3초 전에는 아무것도 서지 않는다(admin-style 명세 "공통 상태").
    // shouldAdvanceTime 이라 실제로 흐른 시간도 가짜 시계에 더해진다. 앞의 단언은 0.1초만 밀어, 지연이 없으면
    // 빨개지고 머리가 선 뒤 흐른 실제 시간이 0.2초를 넘지 않는 한 초록이다. 뒤의 단언은 모두 0.3초를 민 뒤다.
    // 상태 영역은 글보다 먼저 비어서 서 있어야 글이 들어올 때 알린다.
    await act(() => vi.advanceTimersByTimeAsync(100));
    expect(screen.queryByRole("progressbar")).toBeNull();
    expect(live.textContent).toBe("");
    await act(() => vi.advanceTimersByTimeAsync(200));
    expect(screen.getByRole("progressbar", { name: "플러그인 목록을 불러오는 중" })).toBeTruthy();
    expect(live.textContent).toBe("플러그인 목록을 불러오는 중");
    first.resolve(rows());
    expect(await screen.findByRole("region", { name: AGENTS })).toBeTruthy();
  });
});
