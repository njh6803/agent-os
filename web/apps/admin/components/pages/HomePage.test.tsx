// 관리 화면의 첫 화면. 관리 토큰을 넣고 플러그인 목록을 본다(web-admin 티켓 05).
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 생성 클라이언트, SWR 훅, 스토어는 진짜다. 보는 것은
// 바깥 행동이다. 화면에 보이는 역할과 글자, 경계를 지나는 요청의 헤더, 브라우저 저장소에 남은 것이다.

import { fireEvent, screen, within } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { inspect } from "node:util";
import { afterEach, describe, expect, test, vi } from "vitest";
import { api, envelope, network, type PluginRow } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { HomePage } from "./HomePage";

const TOKEN = "adm-7Qx2-page-token";
const REJECTED = "admin-token-the-server-refuses";

const ROWS: PluginRow[] = [
  {
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
      server: null,
    },
  },
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
      server: null,
    },
  },
];

const NO_EFFECT = "로더가 생기기 전에는 효과가 없다";
const KIND_HEADINGS = ["에이전트", "MCP", "스킬", "모델"];

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

async function enterAdminToken(user: UserEvent, token: string): Promise<void> {
  await user.type(screen.getByLabelText("관리 토큰"), token);
  await user.click(screen.getByRole("button", { name: "넣기" }));
}

function group(heading: string): HTMLElement {
  return screen.getByRole("region", { name: heading });
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
    expect(screen.queryByRole("region", { name: "에이전트" })).toBeNull();
  });

  test("넣은 관리 토큰이 확인 요청의 Authorization 에 실리고 받아들여지면 플러그인 목록이 보인다", async () => {
    const authorizations = servePlugins(rows);
    renderPage(<HomePage />);

    await enterAdminToken(userEvent.setup(), TOKEN);

    expect(await screen.findByRole("region", { name: "에이전트" })).toBeTruthy();
    expect(screen.queryByLabelText("관리 토큰")).toBeNull();
    expect(authorizations.length).toBeGreaterThan(0);
    expect(new Set(authorizations)).toEqual(new Set([`Bearer ${TOKEN}`]));
  });

  test("확인 요청이 401 이면 관리 토큰이 거부됐다를 보이고 토큰을 저장하지 않는다", async () => {
    const authorizations = servePlugins(refused);
    renderPage(<HomePage />);

    await enterAdminToken(userEvent.setup(), REJECTED);

    expect((await screen.findByRole("alert")).textContent).toContain("관리 토큰이 거부됐다");
    expect(authorizations).toEqual([`Bearer ${REJECTED}`]);
    // 넣는 자리로 남되 거부된 토큰은 칸에도 남지 않는다.
    expect(screen.getByLabelText<HTMLInputElement>("관리 토큰").value).toBe("");
    expect(entries(sessionStorage).filter(([, value]) => value.includes(REJECTED))).toEqual([]);
  });

  test("받아들여진 관리 토큰은 sessionStorage 에만 남고 그 밖의 상태는 저장되지 않는다", async () => {
    servePlugins(rows);
    renderPage(<HomePage />);

    await enterAdminToken(userEvent.setup(), TOKEN);
    await screen.findByRole("region", { name: "에이전트" });

    expect(entries(localStorage)).toEqual([]);
    const stored = entries(sessionStorage);
    expect(stored).toHaveLength(1);
    const [[, value] = ["", ""]] = stored;
    const parsed: unknown = JSON.parse(value);
    // persist 가 붙이는 판 번호(수) 밖에 저장된 값은 토큰 하나다. 넣는 자리의 알림과 받아들인 횟수 같은 화면의 상태는 남지 않는다.
    expect(leaves(parsed).filter((leaf) => typeof leaf !== "number")).toEqual([TOKEN]);
  });

  test("같은 탭에서 새로 고쳐도 관리 토큰을 다시 넣지 않는다", async () => {
    const authorizations = servePlugins(rows);
    const first = renderPage(<HomePage />);
    await enterAdminToken(userEvent.setup(), TOKEN);
    await screen.findByRole("region", { name: "에이전트" });
    first.unmount();

    // 새로 고침. 모듈을 다시 읽으면 스토어가 새로 서고 그 탭의 sessionStorage 에서 토큰을 되살린다.
    vi.resetModules();
    const reloaded = await import("./HomePage");
    const before = authorizations.length;
    renderPage(<reloaded.HomePage />);

    expect(await screen.findByRole("region", { name: "에이전트" })).toBeTruthy();
    expect(screen.queryByLabelText("관리 토큰")).toBeNull();
    expect(authorizations.slice(before)).toEqual([`Bearer ${TOKEN}`]);
  });

  test("관리 요청이 401 을 받으면 관리 토큰을 지우고 입력 화면으로 돌아가 거부됐다고 말한다", async () => {
    servePlugins((call) => (call < 2 ? rows() : refused()));
    renderPage(<HomePage />);
    const user = userEvent.setup();
    await enterAdminToken(user, TOKEN);
    await screen.findByRole("region", { name: "에이전트" });

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect((await screen.findByRole("alert")).textContent).toContain("관리 토큰이 거부됐다");
    expect(screen.getByLabelText("관리 토큰")).toBeTruthy();
    expect(screen.queryByRole("region", { name: "에이전트" })).toBeNull();
    expect(entries(sessionStorage).filter(([, value]) => value.includes(TOKEN))).toEqual([]);
  });

  test("지운 토큰의 늦은 401 은 그 사이 넣은 새 토큰의 목록에 섞이지 않고 새 토큰을 내려놓지 않는다", async () => {
    const late = Promise.withResolvers<Response>();
    const authorizations = servePlugins((call) => (call === 1 ? late.promise : rows()));
    renderPage(<HomePage />);
    const user = userEvent.setup();
    // 옛 토큰은 확인(0)을 지나고, 목록(1)은 응답을 기다린다.
    await enterAdminToken(user, REJECTED);
    await user.click(await screen.findByRole("button", { name: "토큰 지우기" }));
    await enterAdminToken(user, TOKEN);

    // 새 토큰의 목록은 옛 요청을 나눠 받지 않고 제 요청을 보낸다.
    expect(await screen.findByRole("region", { name: "에이전트" })).toBeTruthy();
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
    await screen.findByRole("region", { name: "에이전트" });

    await user.click(screen.getByRole("button", { name: "토큰 지우기" }));

    expect(await screen.findByLabelText("관리 토큰")).toBeTruthy();
    expect(screen.queryByRole("region", { name: "에이전트" })).toBeNull();
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
    await screen.findByRole("region", { name: "에이전트" });

    for (const token of [REJECTED, TOKEN]) {
      expect(location.href).not.toContain(token);
      expect(whileRejected).not.toContain(token);
      expect(document.documentElement.outerHTML).not.toContain(token);
      expect(printed.map((arg) => inspect(arg)).join("\n")).not.toContain(token);
    }
  });
});

describe("플러그인 목록", () => {
  async function showList(): Promise<void> {
    renderPage(<HomePage />);
    await enterAdminToken(userEvent.setup(), TOKEN);
    await screen.findByRole("region", { name: "에이전트" });
  }

  test("플러그인이 종류별로 묶여 켜짐과 함께 보인다", async () => {
    servePlugins(rows);

    await showList();

    const headings = screen.getAllByRole("heading", { level: 3 }).map((h) => h.textContent);
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
    expect(alert.textContent).toContain(message);
    expect(alert.textContent).toContain("req-9f3c");
    expect(screen.queryByRole("region", { name: "에이전트" })).toBeNull();
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
    await showList();

    await userEvent.setup().click(screen.getByRole("button", { name: "새로 고침" }));

    expect((await screen.findByRole("alert")).textContent).toContain("운영자 파일이 깨졌다");
    expect(screen.queryByRole("region", { name: "에이전트" })).toBeNull();
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
      expect(screen.queryByRole("status")).toBeNull();
    });
    expect(screen.getByRole("alert").textContent).toContain("서버에 닿지 못했다");
    expect(screen.queryByRole("region", { name: "에이전트" })).toBeNull();
  });

  test("관리 토큰을 확인하다 서버에 닿지 못하면 그렇게 말하고 토큰을 저장하지 않는다", async () => {
    servePlugins(() => Response.error());
    renderPage(<HomePage />);

    await enterAdminToken(userEvent.setup(), TOKEN);

    expect((await screen.findByRole("alert")).textContent).toContain("서버에 닿지 못했다");
    expect(screen.getByLabelText("관리 토큰")).toBeTruthy();
    expect(entries(sessionStorage).filter(([, value]) => value.includes(TOKEN))).toEqual([]);
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
    await screen.findByRole("region", { name: "에이전트" });
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
    await screen.findByRole("region", { name: "에이전트" });
    const before = authorizations.length;

    await vi.advanceTimersByTimeAsync(60 * 60 * 1000);

    expect(authorizations.length).toBe(before);
  });

  test("네트워크 연결이 돌아와도 스스로 다시 읽지 않는다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const authorizations = servePlugins(rows);
    renderPage(<HomePage />);
    await enterAdminToken(userEvent.setup({ advanceTimers: vi.advanceTimersByTime }), TOKEN);
    await screen.findByRole("region", { name: "에이전트" });
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
    await screen.findByRole("region", { name: "에이전트" });
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

    expect((await screen.findByRole("status")).textContent).toContain("불러오는 중");
    expect(screen.queryByRole("region", { name: "에이전트" })).toBeNull();
    first.resolve(rows());
    await screen.findByRole("region", { name: "에이전트" });
    expect(screen.queryByRole("status")).toBeNull();

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect((await screen.findByRole("status")).textContent).toContain("다시 확인하는 중");
    expect(within(row("에이전트", "calc")).getByText("켜짐")).toBeTruthy();
    again.resolve(rows());
    await vi.waitFor(() => {
      expect(screen.queryByRole("status")).toBeNull();
    });
    expect(within(row("에이전트", "calc")).getByText("켜짐")).toBeTruthy();
  });
});
