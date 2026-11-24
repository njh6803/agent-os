// 플러그인 목록의 접속 확인(connection-check 티켓 04). 켜 둔 원격 MCP 서버와 켜 둔 모델의 행은 스스로 확인하고, 켜 둔
// stdio MCP 서버의 행은 버튼을 눌러야 확인한다.
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 시간은 가짜 시계가 흘린다. 보는 것은 바깥 행동이다.
// 가짜 서버가 받은 요청, 화면에 보이는 글자, 관리 토큰의 자리다.

import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, test, vi } from "vitest";
import { api, envelope, network, type Plugin, type PluginRow } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { acceptTokens, enterAdminToken } from "../../testing/token";
import { HomePage } from "./HomePage";
import { PluginPage } from "./PluginPage";

const TOKEN = "adm-7Qx2-page-token";

type Manifest = Plugin["manifest"];

function manifestOf(kind: Plugin["kind"], name: string, extra: Partial<Manifest> = {}): Manifest {
  return {
    schema_version: "1",
    kind,
    name,
    version: "0.1.0",
    entrypoint: null,
    mcp: [],
    requires_approval: [],
    conversation_limit: null,
    max_turns: null,
    max_tool_calls: null,
    model: null,
    skills: [],
    provider: null,
    model_id: null,
    max_tokens: null,
    temperature: null,
    base_url: null,
    api_key_env: null,
    server: null,
    ...extra,
  };
}

function plugin(
  kind: Plugin["kind"],
  name: string,
  { enabled, ...extra }: { readonly enabled: boolean } & Partial<Manifest>,
): Plugin {
  return { kind, name, enabled, manifest: manifestOf(kind, name, extra) };
}

const HTTP_SERVER: Manifest["server"] = {
  transport: "http",
  url: "https://docs.example.com/mcp",
  headers: {},
  secret_args: {},
};
const STDIO_SERVER: Manifest["server"] = {
  transport: "stdio",
  command: "npx",
  args: [],
  secret_args: {},
};
const ANTHROPIC = { provider: "anthropic", model_id: "claude-sonnet-5-5" } as const;

const REMOTE = plugin("mcp", "remote-docs", { enabled: true, server: HTTP_SERVER });
const REMOTE_OFF = plugin("mcp", "remote-off", { enabled: false, server: HTTP_SERVER });
const LOCAL = plugin("mcp", "local-files", { enabled: true, server: STDIO_SERVER });
const LOCAL_OFF = plugin("mcp", "local-off", { enabled: false, server: STDIO_SERVER });
const MODEL = plugin("model", "sonnet", { enabled: true, ...ANTHROPIC });
const MODEL_OFF = plugin("model", "haiku", { enabled: false, ...ANTHROPIC });
const AGENT = plugin("agent", "calc", { enabled: true, entrypoint: "agent:Calc" });
const SKILL = plugin("skill", "summarize", { enabled: true });
const TORN: PluginRow = {
  kind: "mcp",
  name: "torn",
  enabled: true,
  reason: "매니페스트를 읽을 수 없다: plugins/mcp/torn/plugin.toml",
};

const ALL: PluginRow[] = [
  AGENT,
  TORN,
  REMOTE,
  REMOTE_OFF,
  LOCAL,
  LOCAL_OFF,
  SKILL,
  MODEL,
  MODEL_OFF,
];

const REASON = "연결을 거부했다: https://docs.example.com/mcp (HTTP 401 Unauthorized)";
const INTERVAL = 30_000;

interface Call {
  readonly method: "GET" | "POST";
  readonly kind: string;
  readonly name: string;
  readonly authorization: string;
}

interface Served {
  /** 접속 확인 요청 전부(받은 차례). */
  readonly calls: Call[];
  readonly list: { rows: PluginRow[]; reads: number };
}

function reached(): Response {
  return HttpResponse.json({ status: "reached" });
}

function unreached(reason: string): Response {
  return HttpResponse.json({ status: "unreached", reason });
}

function refused(): Response {
  return HttpResponse.json(envelope("unauthorized", "토큰이 없거나 틀리다"), { status: 401 });
}

function broken(): Response {
  return HttpResponse.json(envelope("internal_error", "모델 파일이 깨졌다", "req-0042"), {
    status: 500,
  });
}

function enabledOf(body: unknown): boolean {
  return typeof body === "object" && body !== null && "enabled" in body && body.enabled === true;
}

/**
 * 목록과 켜고 끄기와 접속 확인 둘에 답한다. `reply` 는 그 요청과 몇 번째 확인 요청인지(0부터)를 받는다. 켜고 끄기는
 * 목록의 행을 바꿔 다음 읽기가 그 값을 돌려준다.
 */
function serve(
  rows: PluginRow[],
  reply: (call: Call, index: number) => Response | Promise<Response> = reached,
): Served {
  const served: Served = { calls: [], list: { rows, reads: 0 } };
  const answer =
    (method: Call["method"]) =>
    ({
      params,
      request,
    }: {
      params: Record<string, string | readonly string[] | undefined>;
      request: Request;
    }) => {
      const call: Call = {
        method,
        kind: String(params["kind"]),
        name: String(params["name"]),
        authorization: request.headers.get("Authorization") ?? "(없음)",
      };
      served.calls.push(call);
      return reply(call, served.calls.length - 1);
    };
  network.use(
    http.get(api("/plugins"), () => {
      served.list.reads += 1;
      return HttpResponse.json(served.list.rows);
    }),
    http.put(api("/plugins/:kind/:name/enabled"), async ({ params, request }) => {
      const enabled = enabledOf(await request.json());
      served.list.rows = served.list.rows.map((item) =>
        item.kind === String(params["kind"]) && item.name === String(params["name"])
          ? { ...item, enabled }
          : item,
      );
      return new HttpResponse(null, { status: 204 });
    }),
    http.get(api("/plugins/:kind/:name/connection-check"), answer("GET")),
    http.post(api("/plugins/:kind/:name/connection-check"), answer("POST")),
  );
  return served;
}

/** 이름이 `name` 인 플러그인에 간 확인 요청. */
function callsTo(served: Served, name: string, method: Call["method"] = "GET"): Call[] {
  return served.calls.filter((call) => call.name === name && call.method === method);
}

function kindName(kind: string): RegExp {
  return new RegExp(`^${kind} \\d+$`);
}

function row(heading: string, name: string): HTMLElement {
  const found = within(screen.getByRole("region", { name: kindName(heading) }))
    .getAllByRole("listitem")
    .find((item) => within(item).queryByText(name) !== null);
  if (found === undefined) {
    throw new Error(`${heading} 묶음에 ${name} 행이 없다`);
  }
  return found;
}

const REMOTE_ROW = (): HTMLElement => row("MCP", "remote-docs");
const LOCAL_ROW = (): HTMLElement => row("MCP", "local-files");
const MODEL_ROW = (): HTMLElement => row("모델", "sonnet");

function press(target: HTMLElement): HTMLElement {
  return within(target).getByRole("button", { name: "접속 확인" });
}

function clock(): UserEvent {
  vi.useFakeTimers({ shouldAdvanceTime: true });
  return userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
}

/** 관리 토큰을 넣고 목록이 설 때까지 기다린다. */
async function showList(user: UserEvent = userEvent.setup()): Promise<UserEvent> {
  renderPage(<HomePage />);
  await enterAdminToken(user, TOKEN);
  await screen.findByRole("region", { name: kindName("에이전트") });
  return user;
}

async function toggle(user: UserEvent, target: HTMLElement, name: string): Promise<void> {
  await user.click(within(target).getByRole("switch", { name }));
}

function setVisibility(state: "visible" | "hidden"): void {
  Object.defineProperty(document, "visibilityState", { configurable: true, get: () => state });
}

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  Reflect.deleteProperty(document, "visibilityState");
});

describe("스스로 하는 확인", () => {
  test("켜 둔 원격 MCP 서버와 켜 둔 모델의 행마다 확인이 한 건 나가고 나머지 행에는 나가지 않는다", async () => {
    const served = serve(ALL);

    await showList();
    await within(REMOTE_ROW()).findByText("붙음");
    await within(MODEL_ROW()).findByText("붙음");

    expect(
      served.calls.map(({ method, kind, name }) => `${method} ${kind}/${name}`).sort(),
    ).toEqual(["GET mcp/remote-docs", "GET model/sonnet"]);
  });

  test("확인 요청이 관리 토큰을 싣는다", async () => {
    const served = serve([REMOTE]);

    await showList();
    await within(REMOTE_ROW()).findByText("붙음");

    expect(served.calls).toHaveLength(1);
    expect(served.calls[0]?.authorization).toContain(TOKEN);
  });

  test("첫 응답 전에는 확인하는 중이 보이고 응답이 붙었다고 하면 붙음이 보인다", async () => {
    const first = Promise.withResolvers<Response>();
    serve([REMOTE], () => first.promise);

    await showList();

    expect(await within(REMOTE_ROW()).findByText("확인하는 중")).toBeTruthy();
    first.resolve(reached());
    expect(await within(REMOTE_ROW()).findByText("붙음")).toBeTruthy();
    expect(within(REMOTE_ROW()).queryByText("확인하는 중")).toBeNull();
  });

  test("붙지 못했다는 응답은 붙지 못함과 까닭의 글 전체를 보인다", async () => {
    serve([REMOTE], () => unreached(REASON));

    await showList();

    expect(await within(REMOTE_ROW()).findByText("붙지 못함")).toBeTruthy();
    expect(within(REMOTE_ROW()).getByText(REASON)).toBeTruthy();
  });

  test("상태는 행의 상태 영역에 글자로 있다", async () => {
    serve([REMOTE], () => unreached(REASON));

    await showList();
    await within(REMOTE_ROW()).findByText("붙지 못함");

    expect(within(REMOTE_ROW()).getByRole("status").textContent).toBe(`붙지 못함${REASON}`);
  });

  test("30초마다 다시 확인하고 그동안 앞선 결과가 남는다", async () => {
    const user = clock();
    const second = Promise.withResolvers<Response>();
    const served = serve([REMOTE], (_call, index) => (index === 0 ? reached() : second.promise));
    await showList(user);
    await within(REMOTE_ROW()).findByText("붙음");

    await vi.advanceTimersByTimeAsync(INTERVAL);

    await waitFor(() => {
      expect(callsTo(served, "remote-docs")).toHaveLength(2);
    });
    // 두 번째 응답을 기다리는 동안에도 앞선 결과가 지워지지 않고 확인하는 중으로 돌아가지도 않는다.
    expect(within(REMOTE_ROW()).getByText("붙음")).toBeTruthy();
    expect(within(REMOTE_ROW()).queryByText("확인하는 중")).toBeNull();
    second.resolve(unreached(REASON));
    expect(await within(REMOTE_ROW()).findByText("붙지 못함")).toBeTruthy();
    expect(within(REMOTE_ROW()).queryByText("붙음")).toBeNull();

    await vi.advanceTimersByTimeAsync(INTERVAL);
    await waitFor(() => {
      expect(callsTo(served, "remote-docs")).toHaveLength(3);
    });
  });

  test("같은 결과가 다시 와도 상태 영역을 건드리지 않는다", async () => {
    const user = clock();
    const served = serve([REMOTE]);
    await showList(user);
    const status = await within(REMOTE_ROW()).findByRole("status");
    expect(status.textContent).toBe("붙음");
    const changes: MutationRecord[] = [];
    const watcher = new MutationObserver((records) => changes.push(...records));
    watcher.observe(status, {
      subtree: true,
      childList: true,
      characterData: true,
      attributes: true,
    });

    await vi.advanceTimersByTimeAsync(INTERVAL);
    await waitFor(() => {
      expect(callsTo(served, "remote-docs")).toHaveLength(2);
    });
    await vi.advanceTimersByTimeAsync(1_000);

    changes.push(...watcher.takeRecords());
    watcher.disconnect();
    expect(changes).toEqual([]);
    expect(within(REMOTE_ROW()).getByRole("status")).toBe(status);
  });

  test("확인 요청이 실패하면 앞선 결과를 지우고 확인하지 못함과 실패의 글을 보인다", async () => {
    const user = clock();
    const served = serve([MODEL], (_call, index) => (index === 0 ? reached() : broken()));
    await showList(user);
    await within(MODEL_ROW()).findByText("붙음");

    await vi.advanceTimersByTimeAsync(INTERVAL);

    expect(await within(MODEL_ROW()).findByText("확인하지 못함")).toBeTruthy();
    expect(within(MODEL_ROW()).getByText("모델 파일이 깨졌다")).toBeTruthy();
    expect(within(MODEL_ROW()).queryByText("붙음")).toBeNull();
    expect(callsTo(served, "sonnet")).toHaveLength(2);
  });

  test("서버에 닿지 못했으면 서버에 닿지 못했다를 보인다", async () => {
    serve([MODEL], () => HttpResponse.error());

    await showList();

    expect(await within(MODEL_ROW()).findByText("확인하지 못함")).toBeTruthy();
    expect(within(MODEL_ROW()).getByText("서버에 닿지 못했다")).toBeTruthy();
  });

  test("확인하지 못함이 된 행도 30초 뒤 다시 확인을 보낸다", async () => {
    const user = clock();
    const served = serve([MODEL], (_call, index) => (index < 2 ? broken() : reached()));
    await showList(user);
    await within(MODEL_ROW()).findByText("확인하지 못함");

    await vi.advanceTimersByTimeAsync(INTERVAL);
    await waitFor(() => {
      expect(callsTo(served, "sonnet")).toHaveLength(2);
    });
    expect(await within(MODEL_ROW()).findByText("확인하지 못함")).toBeTruthy();
    await vi.advanceTimersByTimeAsync(INTERVAL);

    expect(await within(MODEL_ROW()).findByText("붙음")).toBeTruthy();
    expect(callsTo(served, "sonnet")).toHaveLength(3);
  });

  test("확인 요청이 401 이면 관리 토큰을 내려놓는다", async () => {
    const served = serve([MODEL], refused);
    renderPage(<HomePage />);
    await enterAdminToken(userEvent.setup(), TOKEN);

    // 목록이 선 뒤 확인이 나가고, 그 401 로 목록이 토큰과 함께 걷힌다.
    await waitFor(() => {
      expect(served.calls).toHaveLength(1);
    });
    await waitFor(() => {
      expect(screen.queryByRole("region", { name: kindName("모델") })).toBeNull();
    });
    expect(screen.getByLabelText("관리 토큰")).toBeTruthy();
  });

  test("보이지 않는 동안에는 확인을 보내지 않고 돌아오면 바로 한 번 확인한다", async () => {
    const user = clock();
    const served = serve([REMOTE]);
    await showList(user);
    await within(REMOTE_ROW()).findByText("붙음");
    setVisibility("hidden");

    await vi.advanceTimersByTimeAsync(INTERVAL * 3);

    expect(callsTo(served, "remote-docs")).toHaveLength(1);
    setVisibility("visible");
    fireEvent(document, new Event("visibilitychange"));
    await waitFor(() => {
      expect(callsTo(served, "remote-docs")).toHaveLength(2);
    });
    await vi.advanceTimersByTimeAsync(INTERVAL);
    await waitFor(() => {
      expect(callsTo(served, "remote-docs")).toHaveLength(3);
    });
  });

  test("목록의 새로 고침 버튼을 누르면 확인도 바로 한 번 다시 한다", async () => {
    const served = serve([REMOTE, MODEL]);
    const user = await showList();
    await within(REMOTE_ROW()).findByText("붙음");
    await within(MODEL_ROW()).findByText("붙음");

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    await waitFor(() => {
      expect(callsTo(served, "remote-docs")).toHaveLength(2);
    });
    await waitFor(() => {
      expect(callsTo(served, "sonnet")).toHaveLength(2);
    });
    expect(served.list.reads).toBeGreaterThanOrEqual(3);
  });

  test("확인이 날아가는 동안 새로 고침을 눌러도 그 행의 요청은 하나다", async () => {
    const first = Promise.withResolvers<Response>();
    const served = serve([REMOTE], () => first.promise);
    const user = await showList();
    await within(REMOTE_ROW()).findByText("확인하는 중");
    const reads = served.list.reads;

    await user.click(screen.getByRole("button", { name: "새로 고침" }));
    await waitFor(() => {
      expect(served.list.reads).toBe(reads + 1);
    });
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "새로 고침" }).getAttribute("aria-busy")).not.toBe(
        "true",
      );
    });

    expect(callsTo(served, "remote-docs")).toHaveLength(1);
    first.resolve(reached());
    expect(await within(REMOTE_ROW()).findByText("붙음")).toBeTruthy();
    expect(callsTo(served, "remote-docs")).toHaveLength(1);
  });

  test("플러그인을 끄면 결과가 사라지고 확인이 멈추며 다시 켜면 옛 결과 없이 바로 확인한다", async () => {
    const user = clock();
    const again = Promise.withResolvers<Response>();
    const served = serve([REMOTE], (_call, index) => (index === 0 ? reached() : again.promise));
    await showList(user);
    await within(REMOTE_ROW()).findByText("붙음");

    await toggle(user, REMOTE_ROW(), "remote-docs");
    await waitFor(() => {
      expect(within(REMOTE_ROW()).queryByRole("status")).toBeNull();
    });
    await vi.advanceTimersByTimeAsync(INTERVAL * 3);
    expect(callsTo(served, "remote-docs")).toHaveLength(1);

    await toggle(user, REMOTE_ROW(), "remote-docs");

    await waitFor(() => {
      expect(callsTo(served, "remote-docs")).toHaveLength(2);
    });
    expect(await within(REMOTE_ROW()).findByText("확인하는 중")).toBeTruthy();
    expect(within(REMOTE_ROW()).queryByText("붙음")).toBeNull();
    again.resolve(unreached(REASON));
    expect(await within(REMOTE_ROW()).findByText("붙지 못함")).toBeTruthy();
  });

  test("끈 사이에 늦게 도착한 옛 응답은 다시 켠 행의 결과가 되지 않는다", async () => {
    const stale = Promise.withResolvers<Response>();
    const served = serve([REMOTE], (_call, index) =>
      index === 0 ? stale.promise : unreached(REASON),
    );
    const user = await showList();
    await within(REMOTE_ROW()).findByText("확인하는 중");

    await toggle(user, REMOTE_ROW(), "remote-docs");
    await waitFor(() => {
      expect(within(REMOTE_ROW()).queryByRole("status")).toBeNull();
    });
    await toggle(user, REMOTE_ROW(), "remote-docs");
    await waitFor(() => {
      expect(callsTo(served, "remote-docs")).toHaveLength(2);
    });
    stale.resolve(reached());

    expect(await within(REMOTE_ROW()).findByText("붙지 못함")).toBeTruthy();
    expect(within(REMOTE_ROW()).queryByText("붙음")).toBeNull();
  });

  test("응답이 꺼져 있다고 하면 그 행의 결과를 지우고 목록을 다시 읽는다", async () => {
    const served = serve([REMOTE], () => {
      served.list.rows = [REMOTE_OFF];
      return HttpResponse.json({ status: "disabled" });
    });
    await showList();

    await waitFor(() => {
      expect(served.list.reads).toBe(3);
    });

    await waitFor(() => {
      expect(row("MCP", "remote-off")).toBeTruthy();
    });
    expect(within(row("MCP", "remote-off")).queryByRole("status")).toBeNull();
    expect(callsTo(served, "remote-docs")).toHaveLength(1);
  });

  test("응답이 대상이 아니라고 해도 그 행의 결과를 지우고 목록을 다시 읽는다", async () => {
    const served = serve([REMOTE], () => HttpResponse.json({ status: "not_applicable" }));
    await showList();

    await waitFor(() => {
      expect(served.list.reads).toBe(3);
    });

    expect(within(REMOTE_ROW()).queryByText("붙음")).toBeNull();
    expect(within(REMOTE_ROW()).queryByText("붙지 못함")).toBeNull();
  });

  test("페이지를 떠나면 확인이 멈춘다", async () => {
    const user = clock();
    const served = serve([REMOTE]);
    const view = renderPage(<HomePage />);
    await enterAdminToken(user, TOKEN);
    await within(await screen.findByRole("region", { name: kindName("MCP") })).findByText("붙음");
    expect(served.calls).toHaveLength(1);

    view.unmount();
    await vi.advanceTimersByTimeAsync(INTERVAL * 3);

    expect(served.calls).toHaveLength(1);
  });

  test("에이전트와 스킬과 표지 행과 꺼 둔 행에는 접속 확인이 없다", async () => {
    serve(ALL);
    await showList();
    await within(REMOTE_ROW()).findByText("붙음");

    for (const target of [
      row("에이전트", "calc"),
      row("MCP", "torn"),
      row("MCP", "remote-off"),
      row("스킬", "summarize"),
      row("모델", "haiku"),
    ]) {
      expect(within(target).queryByRole("status")).toBeNull();
      expect(within(target).queryByRole("button", { name: "접속 확인" })).toBeNull();
    }
  });
});

describe("눌러서 하는 확인", () => {
  test("켜 둔 stdio 서버의 행에는 접속 확인 버튼이 있고 누르기 전에는 결과도 요청도 없다", async () => {
    const served = serve([LOCAL]);

    await showList();

    expect(press(LOCAL_ROW()).hasAttribute("disabled")).toBe(false);
    expect(within(LOCAL_ROW()).queryByRole("status")).toBeNull();
    expect(served.calls).toEqual([]);
  });

  test("누르면 요청이 한 건 나가고 응답까지 버튼이 눌리지 않으며 응답 뒤에 결과와 확인한 시각이 보인다", async () => {
    const answer = Promise.withResolvers<Response>();
    const served = serve([LOCAL], () => answer.promise);
    const user = clock();
    await showList(user);

    await user.click(press(LOCAL_ROW()));

    expect(await within(LOCAL_ROW()).findByText("확인하는 중")).toBeTruthy();
    expect(press(LOCAL_ROW()).getAttribute("aria-busy")).toBe("true");
    await user.click(press(LOCAL_ROW()));
    expect(callsTo(served, "local-files", "POST")).toHaveLength(1);
    expect(served.calls[0]?.authorization).toContain(TOKEN);
    expect(callsTo(served, "local-files", "GET")).toHaveLength(0);

    const answeredAt = Date.now();
    answer.resolve(reached());
    expect(await within(LOCAL_ROW()).findByText("붙음")).toBeTruthy();
    expect(press(LOCAL_ROW()).getAttribute("aria-busy")).not.toBe("true");
    expect(within(LOCAL_ROW()).getByText("확인한 시각")).toBeTruthy();
    const stamp = LOCAL_ROW().querySelector("time");
    expect(stamp?.textContent).toMatch(/^\d{2}:\d{2}:\d{2}$/);
    expect(
      Math.abs(new Date(stamp?.getAttribute("datetime") ?? "").getTime() - answeredAt),
    ).toBeLessThan(5_000);
  });

  test("응답이 오면 확인하는 중이던 상태 영역이 그대로 이어져 결과가 알려진다", async () => {
    const answer = Promise.withResolvers<Response>();
    serve([LOCAL], () => answer.promise);
    const user = clock();
    await showList(user);
    await user.click(press(LOCAL_ROW()));
    const status = await within(LOCAL_ROW()).findByRole("status");
    expect(status.textContent).toBe("확인하는 중");

    answer.resolve(reached());

    await waitFor(() => {
      expect(status.textContent).toBe("붙음");
    });
    expect(within(LOCAL_ROW()).getByRole("status")).toBe(status);
  });

  test("붙지 못했으면 붙지 못함과 까닭의 글과 확인한 시각을 보인다", async () => {
    serve([LOCAL], () => unreached("프로세스가 시작하자마자 끝났다(종료 코드 1)"));
    const user = await showList();

    await user.click(press(LOCAL_ROW()));

    expect(await within(LOCAL_ROW()).findByText("붙지 못함")).toBeTruthy();
    expect(
      within(LOCAL_ROW()).getByText("프로세스가 시작하자마자 끝났다(종료 코드 1)"),
    ).toBeTruthy();
    expect(within(LOCAL_ROW()).getByText("확인한 시각")).toBeTruthy();
  });

  test("누른 확인의 요청이 실패하면 앞선 결과를 지우고 확인하지 못함과 실패의 글과 누른 시각을 보이며 버튼이 다시 눌린다", async () => {
    const user = clock();
    const late = Promise.withResolvers<Response>();
    const served = serve([LOCAL], (_call, index) => (index === 0 ? reached() : late.promise));
    await showList(user);
    await user.click(press(LOCAL_ROW()));
    await within(LOCAL_ROW()).findByText("붙음");

    const pressedAt = Date.now();
    await user.click(press(LOCAL_ROW()));
    await waitFor(() => {
      expect(callsTo(served, "local-files", "POST")).toHaveLength(2);
    });
    await vi.advanceTimersByTimeAsync(10_000);
    late.resolve(broken());

    expect(await within(LOCAL_ROW()).findByText("확인하지 못함")).toBeTruthy();
    expect(within(LOCAL_ROW()).getByText("모델 파일이 깨졌다")).toBeTruthy();
    expect(within(LOCAL_ROW()).queryByText("붙음")).toBeNull();
    expect(within(LOCAL_ROW()).getByText("누른 시각")).toBeTruthy();
    const stamp = LOCAL_ROW().querySelector("time");
    expect(
      Math.abs(new Date(stamp?.getAttribute("datetime") ?? "").getTime() - pressedAt),
    ).toBeLessThan(5_000);
    expect(press(LOCAL_ROW()).getAttribute("aria-busy")).not.toBe("true");
    expect(press(LOCAL_ROW()).hasAttribute("disabled")).toBe(false);
  });

  test("스스로 새로워지지 않는다", async () => {
    const user = clock();
    const served = serve([LOCAL]);
    await showList(user);
    await user.click(press(LOCAL_ROW()));
    await within(LOCAL_ROW()).findByText("붙음");

    await vi.advanceTimersByTimeAsync(INTERVAL * 3);

    expect(served.calls).toHaveLength(1);
  });

  test("목록을 다시 읽어도 결과가 남는다", async () => {
    const served = serve([LOCAL]);
    const user = await showList();
    await user.click(press(LOCAL_ROW()));
    await within(LOCAL_ROW()).findByText("붙음");
    const reads = served.list.reads;

    await user.click(screen.getByRole("button", { name: "새로 고침" }));
    await waitFor(() => {
      expect(served.list.reads).toBe(reads + 1);
    });
    await waitFor(() => {
      expect(screen.queryByRole("progressbar")).toBeNull();
    });

    expect(within(LOCAL_ROW()).getByText("붙음")).toBeTruthy();
    expect(callsTo(served, "local-files", "POST")).toHaveLength(1);
  });

  test("플러그인을 끄면 결과가 사라지고 다시 켜도 옛 결과가 없다", async () => {
    serve([LOCAL]);
    const user = await showList();
    await user.click(press(LOCAL_ROW()));
    await within(LOCAL_ROW()).findByText("붙음");

    await toggle(user, LOCAL_ROW(), "local-files");
    await waitFor(() => {
      expect(within(LOCAL_ROW()).queryByRole("status")).toBeNull();
    });
    expect(press(LOCAL_ROW()).hasAttribute("disabled")).toBe(true);
    await toggle(user, LOCAL_ROW(), "local-files");

    await waitFor(() => {
      expect(press(LOCAL_ROW()).hasAttribute("disabled")).toBe(false);
    });
    expect(within(LOCAL_ROW()).queryByRole("status")).toBeNull();
  });

  test("끈 사이에 도착한 응답은 버린다", async () => {
    const answer = Promise.withResolvers<Response>();
    serve([LOCAL], () => answer.promise);
    const user = await showList();
    await user.click(press(LOCAL_ROW()));
    await within(LOCAL_ROW()).findByText("확인하는 중");

    await toggle(user, LOCAL_ROW(), "local-files");
    await waitFor(() => {
      expect(within(LOCAL_ROW()).queryByRole("status")).toBeNull();
    });
    answer.resolve(reached());
    await toggle(user, LOCAL_ROW(), "local-files");

    await waitFor(() => {
      expect(press(LOCAL_ROW()).hasAttribute("disabled")).toBe(false);
    });
    expect(within(LOCAL_ROW()).queryByRole("status")).toBeNull();
  });

  test("꺼 둔 stdio 서버의 행은 버튼이 눌리지 않고 결과가 없다", async () => {
    const served = serve([LOCAL_OFF]);
    const user = await showList();

    const button = press(row("MCP", "local-off"));
    await user.click(button);

    expect(button.hasAttribute("disabled")).toBe(true);
    expect(within(row("MCP", "local-off")).queryByRole("status")).toBeNull();
    expect(served.calls).toEqual([]);
  });

  test("응답이 꺼져 있다고 하면 그 행의 결과를 지우고 목록을 다시 읽는다", async () => {
    const served = serve([LOCAL], () => HttpResponse.json({ status: "disabled" }));
    const user = await showList();
    const reads = served.list.reads;

    await user.click(press(LOCAL_ROW()));

    await waitFor(() => {
      expect(served.list.reads).toBe(reads + 1);
    });
    expect(within(LOCAL_ROW()).queryByRole("status")).toBeNull();
  });

  test("401 이면 관리 토큰을 내려놓는다", async () => {
    serve([LOCAL], refused);
    const user = await showList();

    await user.click(press(LOCAL_ROW()));

    expect(await screen.findByLabelText("관리 토큰")).toBeTruthy();
  });
});

describe("플러그인 상세 페이지", () => {
  test("접속 확인을 두지 않는다", async () => {
    acceptTokens();
    network.use(http.get(api("/plugins/model/sonnet"), () => HttpResponse.json(MODEL)));
    const user = userEvent.setup();
    renderPage(<PluginPage kind="model" name="sonnet" />);
    await enterAdminToken(user, TOKEN);

    await screen.findByRole("heading", { level: 1, name: "sonnet" });

    // 접속 확인의 요청이 가면 처리하지 않은 요청으로 이 시험이 실패한다.
    expect(screen.queryByRole("button", { name: "접속 확인" })).toBeNull();
    expect(screen.queryByText("확인하는 중")).toBeNull();
  });
});
