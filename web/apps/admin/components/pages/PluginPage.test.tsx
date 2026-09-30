// 플러그인 하나. 운영자가 플러그인 하나를 열어 매니페스트를 통째로 본다(web-admin 티켓 06).
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 주소의 두 조각(종류와 이름)은 라우트가 페이지에
// 넘기는 그대로 준다.

import { screen } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, test } from "vitest";
import { api, envelope, network, type Plugin } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { enterAdminToken } from "../../testing/token";
import { PluginPage } from "./PluginPage";

const TOKEN = "adm-4Kp9-plugin-page-token";

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
    server: null,
  },
};

/** 서버가 준 모양 그대로 두 칸 들여 적은 CALC 의 매니페스트. */
const CALC_MANIFEST = `{
  "schema_version": "1",
  "kind": "agent",
  "name": "calc",
  "version": "0.1.0",
  "entrypoint": "agent:Calc",
  "mcp": [
    "everything"
  ],
  "requires_approval": [
    "add"
  ],
  "server": null
}`;

/** 넣은 관리 토큰을 확인하는 목록 요청에 답한다. 이 화면은 그 밖에는 목록을 읽지 않는다. */
function acceptTokens(): void {
  network.use(http.get(api("/plugins"), () => HttpResponse.json([])));
}

/**
 * `GET /plugins/{kind}/{name}` 하나에 답한다. `reply` 는 몇 번째 요청인지(0부터) 받는다. 요청마다의
 * `Authorization` 을 쌓아 돌려준다.
 */
function servePlugin(
  path: string,
  reply: (call: number) => Response | Promise<Response>,
): string[] {
  const authorizations: string[] = [];
  network.use(
    http.get(api(path), ({ request }) => {
      authorizations.push(request.headers.get("Authorization") ?? "(없음)");
      return reply(authorizations.length - 1);
    }),
  );
  return authorizations;
}

/** 플러그인 하나를 열고 관리 토큰을 넣는다. 이어서 누를 사용자를 돌려준다. */
async function openPlugin(kind: string, name: string): Promise<UserEvent> {
  const user = userEvent.setup();
  renderPage(<PluginPage kind={kind} name={name} />);
  await enterAdminToken(user, TOKEN);
  return user;
}

describe("플러그인 하나", () => {
  test("읽히는 플러그인을 열면 켜짐과 들여 적은 매니페스트가 통째로 보인다", async () => {
    acceptTokens();
    const authorizations = servePlugin("/plugins/agent/calc", () => HttpResponse.json(CALC));

    await openPlugin("agent", "calc");

    const manifest = await screen.findByRole("region", { name: "매니페스트" });
    expect(manifest.textContent).toContain(CALC_MANIFEST);
    expect(screen.getByRole("heading", { level: 2, name: "calc" })).toBeTruthy();
    expect(screen.getByText("켜짐")).toBeTruthy();
    expect(authorizations).toEqual([`Bearer ${TOKEN}`]);
  });

  test("매니페스트를 읽을 수 없는 플러그인을 열면 500 봉투의 경로와 이유와 추적 식별자가 보인다", async () => {
    const message =
      "매니페스트를 읽을 수 없다: C:/root/plugins/agents/broken/plugin.toml\nExpected '=' after a key";
    acceptTokens();
    servePlugin("/plugins/agent/broken", () =>
      HttpResponse.json(envelope("internal_error", message, "req-5b21"), { status: 500 }),
    );

    await openPlugin("agent", "broken");

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("C:/root/plugins/agents/broken/plugin.toml");
    expect(alert.textContent).toContain("Expected '=' after a key");
    expect(alert.textContent).toContain("req-5b21");
    expect(screen.queryByRole("region", { name: "매니페스트" })).toBeNull();
  });

  test("없는 이름을 열면 404 봉투의 메시지가 보인다", async () => {
    acceptTokens();
    servePlugin("/plugins/mcp/ghost", () =>
      HttpResponse.json(envelope("not_found", "플러그인이 없다: mcp/ghost"), { status: 404 }),
    );

    await openPlugin("mcp", "ghost");

    expect((await screen.findByRole("alert")).textContent).toContain("플러그인이 없다: mcp/ghost");
  });

  test("플러그인 하나를 읽다 401 을 받으면 관리 토큰을 지우고 입력 화면으로 돌아가 거부됐다고 말한다", async () => {
    acceptTokens();
    servePlugin("/plugins/agent/calc", () =>
      HttpResponse.json(envelope("unauthorized", "토큰이 없거나 틀리다"), { status: 401 }),
    );

    await openPlugin("agent", "calc");

    expect((await screen.findByRole("alert")).textContent).toContain("관리 토큰이 거부됐다");
    expect(screen.getByLabelText("관리 토큰")).toBeTruthy();
    expect(screen.queryByRole("heading", { level: 2, name: "calc" })).toBeNull();
  });

  test("새로 고침 버튼이 그 플러그인을 다시 읽는다", async () => {
    acceptTokens();
    const authorizations = servePlugin("/plugins/agent/calc", (call) =>
      HttpResponse.json(call === 0 ? CALC : { ...CALC, enabled: false }),
    );
    const user = await openPlugin("agent", "calc");
    await screen.findByText("켜짐");

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect(await screen.findByText("꺼짐")).toBeTruthy();
    expect(authorizations).toHaveLength(2);
  });

  test("다시 확인하는 동안에는 이미 보인 매니페스트가 남는다", async () => {
    const again = Promise.withResolvers<Response>();
    acceptTokens();
    servePlugin("/plugins/agent/calc", (call) =>
      call === 0 ? HttpResponse.json(CALC) : again.promise,
    );
    const user = await openPlugin("agent", "calc");
    await screen.findByRole("region", { name: "매니페스트" });

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect((await screen.findByRole("status")).textContent).toContain("다시 확인하는 중");
    expect(screen.getByRole("region", { name: "매니페스트" }).textContent).toContain(CALC_MANIFEST);
    again.resolve(HttpResponse.json(CALC));
  });

  test("이미 보인 플러그인도 다시 읽다 실패하면 매니페스트를 지우고 실패를 보인다", async () => {
    acceptTokens();
    servePlugin("/plugins/agent/calc", (call) =>
      call === 0
        ? HttpResponse.json(CALC)
        : HttpResponse.json(envelope("internal_error", "운영자 파일이 깨졌다"), { status: 500 }),
    );
    const user = await openPlugin("agent", "calc");
    await screen.findByRole("region", { name: "매니페스트" });

    await user.click(screen.getByRole("button", { name: "새로 고침" }));

    expect((await screen.findByRole("alert")).textContent).toContain("운영자 파일이 깨졌다");
    expect(screen.queryByRole("region", { name: "매니페스트" })).toBeNull();
  });

  test("지운 토큰의 늦은 401 은 그 사이 넣은 새 토큰의 플러그인 하나에 섞이지 않고 새 토큰을 내려놓지 않는다", async () => {
    const old = "adm-old-token-cleared";
    const late = Promise.withResolvers<Response>();
    acceptTokens();
    const authorizations = servePlugin("/plugins/agent/calc", (call) =>
      call === 0 ? late.promise : HttpResponse.json(CALC),
    );
    const user = userEvent.setup();
    renderPage(<PluginPage kind="agent" name="calc" />);
    // 옛 토큰의 요청(0)은 응답을 기다린다.
    await enterAdminToken(user, old);
    await user.click(await screen.findByRole("button", { name: "토큰 지우기" }));
    await enterAdminToken(user, TOKEN);

    // 새 토큰은 옛 요청을 나눠 받지 않고 제 요청을 보낸다.
    expect(await screen.findByRole("region", { name: "매니페스트" })).toBeTruthy();
    expect(authorizations).toEqual([`Bearer ${old}`, `Bearer ${TOKEN}`]);
    late.resolve(
      HttpResponse.json(envelope("unauthorized", "토큰이 없거나 틀리다"), { status: 401 }),
    );
    // 늦은 응답이 처리될 틈을 준다. 옛 요청의 401 이 새 토큰을 내려놓으면 넣는 자리로 돌아간다.
    await new Promise((resolve) => setTimeout(resolve, 200));

    expect(screen.queryByLabelText("관리 토큰")).toBeNull();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  test("주소의 종류가 플러그인의 종류가 아니면 요청을 보내지 않고 그렇다고 말한다", async () => {
    acceptTokens();

    // 처리하지 않은 요청은 setup.ts 가 테스트를 빨갛게 한다.
    await openPlugin("agents", "calc");

    expect((await screen.findByRole("alert")).textContent).toContain(
      "플러그인의 종류가 아니다: agents",
    );
  });

  test("주소의 조각이 인코딩된 채로 와도 풀어서 보이고 요청은 한 번만 인코딩한다", async () => {
    // Next 16.3.6 은 동적 조각을 퍼센트 인코딩된 채로 넘긴다(e2e 의 패턴 밖 표지 흐름이 쟀다).
    acceptTokens();
    const authorizations = servePlugin("/plugins/agent/Old%20Calc", () =>
      HttpResponse.json(envelope("invalid_request", "요청의 형식이 올바르지 않다"), {
        status: 422,
      }),
    );

    // 두 번 인코딩한 요청(Old%2520Calc)은 처리하지 않은 요청이라 setup.ts 가 테스트를 빨갛게 한다.
    await openPlugin("agent", "Old%20Calc");

    expect(await screen.findByRole("heading", { level: 2, name: "Old Calc" })).toBeTruthy();
    expect((await screen.findByRole("alert")).textContent).toContain("요청의 형식이 올바르지 않다");
    expect(authorizations).toHaveLength(1);
  });

  test("풀 수 없는 주소의 조각이면 요청을 보내지 않고 그렇다고 말한다", async () => {
    acceptTokens();

    await openPlugin("agent", "%E0%A4%A");

    expect((await screen.findByRole("alert")).textContent).toContain(
      "주소를 풀 수 없다: agent/%E0%A4%A",
    );
  });

  test("플러그인 목록으로 돌아가는 링크가 있다", async () => {
    acceptTokens();
    servePlugin("/plugins/agent/calc", () => HttpResponse.json(CALC));

    await openPlugin("agent", "calc");

    const back = await screen.findByRole("link", { name: "플러그인 목록으로" });
    expect(back.getAttribute("href")).toBe("/");
    await screen.findByRole("region", { name: "매니페스트" });
  });
});
