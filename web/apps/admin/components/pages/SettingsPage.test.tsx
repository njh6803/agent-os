// 설정 화면과 틀의 탐색(admin-style 티켓 04). 운영자가 탐색으로 화면을 옮기고, 채널 토큰을 설정에서 넣고, 두 토큰을
// 설정에서 지운다.
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 탐색은 옆 탐색과 위 막대가 같은 `nav` 하나라 jsdom
// 에도 하나만 보인다(폭에 따른 배치는 CSS 이고 스토리가 본다).

import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { renderToString } from "react-dom/server";
import { describe, expect, test } from "vitest";
import { api, network } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { acceptTokens, enterAdminToken } from "../../testing/token";
import { HomePage } from "./HomePage";
import { PluginPage } from "./PluginPage";
import { RunPage } from "./RunPage";
import { RunsPage } from "./RunsPage";
import { SettingsPage } from "./SettingsPage";

const ADMIN = "adm-7Hq3-settings-page-token";
const CHANNEL = "chn-5Lm9-settings-page-token";

/** 관리 토큰을 넣어 설정 화면을 연다. 설정 화면은 관리 토큰을 확인하는 목록 요청 밖에 아무것도 읽지 않는다. */
async function openSettings() {
  acceptTokens();
  renderPage(<SettingsPage />);
  const user = userEvent.setup();
  await enterAdminToken(user, ADMIN);
  await screen.findByRole("heading", { level: 1, name: "설정" });
  return user;
}

function navigation(): HTMLElement {
  return screen.getByRole("navigation", { name: "관리 화면" });
}

describe("설정 화면", () => {
  test("관리 토큰이 없으면 설정 대신 관리 토큰 넣기 화면이 서고 관리 요청을 보내지 않는다", async () => {
    renderPage(<SettingsPage />);

    expect(await screen.findByLabelText("관리 토큰")).toBeTruthy();
    expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("관리 토큰 넣기");
    expect(screen.queryByRole("heading", { name: "설정" })).toBeNull();
    expect(screen.queryByLabelText("채널 토큰")).toBeNull();
  });

  test("머리는 h1 설정과 설명이고 채널 토큰과 토큰 지우기가 h2 다", async () => {
    await openSettings();

    expect(screen.getAllByRole("heading", { level: 1 }).map((h) => h.textContent)).toEqual([
      "설정",
    ]);
    expect(
      screen.getByText(
        "테마는 이 브라우저에, 토큰은 이 탭에만 남는다. 서버의 구성은 바꾸지 않는다.",
      ),
    ).toBeTruthy();
    expect(screen.getAllByRole("heading", { level: 2 }).map((h) => h.textContent)).toEqual([
      "채널 토큰",
      "토큰 지우기",
    ]);
    expect(
      screen.getByText(
        (_, element) =>
          element?.tagName === "P" &&
          element.textContent ===
            "일시정지한 실행에 결정을 낼 때 쓴다. agent-os serve 를 띄울 때 AGENT_OS_CHANNEL_TOKEN 에 준 값이다.",
      ),
    ).toBeTruthy();
    expect(screen.getByText("관리 토큰과 채널 토큰을 이 탭에서 모두 지운다.")).toBeTruthy();
    // 읽는 화면이 아니라 새로 고침이 없다.
    expect(screen.queryByRole("button", { name: "새로 고침" })).toBeNull();
  });

  test("채널 토큰은 가린 입력으로 넣고 확인 요청 없이 넣었다고만 말한다", async () => {
    const user = await openSettings();
    const requests: string[] = [];
    network.events.on("request:start", ({ request }) => {
      requests.push(`${request.method} ${request.url}`);
    });

    const field = screen.getByLabelText<HTMLInputElement>("채널 토큰");
    expect(field.getAttribute("type")).toBe("password");
    expect(field.getAttribute("autocomplete")).toBe("off");
    await user.type(field, CHANNEL);
    await user.click(screen.getByRole("button", { name: "채널 토큰 넣기" }));

    expect(await screen.findByText("채널 토큰을 넣었다")).toBeTruthy();
    expect(screen.queryByLabelText("채널 토큰")).toBeNull();
    expect(requests).toEqual([]);
    expect(JSON.stringify(Object.entries(sessionStorage))).toContain(CHANNEL);
    expect(document.body.textContent).not.toContain(CHANNEL);
    network.events.removeAllListeners("request:start");
  });

  test("토큰 지우기를 누르면 두 토큰이 지워지고 관리 토큰 넣기 화면으로 돌아간다", async () => {
    const user = await openSettings();
    await user.type(screen.getByLabelText("채널 토큰"), CHANNEL);
    await user.click(screen.getByRole("button", { name: "채널 토큰 넣기" }));
    await screen.findByText("채널 토큰을 넣었다");

    await user.click(screen.getByRole("button", { name: "토큰 지우기" }));

    expect(await screen.findByLabelText("관리 토큰")).toBeTruthy();
    const stored = JSON.stringify(Object.entries(sessionStorage));
    expect(stored).not.toContain(ADMIN);
    expect(stored).not.toContain(CHANNEL);
    // 지울 채널 토큰이 남지 않아 넣는 자리의 토큰 지우기도 없다.
    expect(screen.queryByRole("button", { name: "토큰 지우기" })).toBeNull();
  });
});

describe("틀과 탐색", () => {
  test("탐색은 관리 화면이라는 이름 하나이고 플러그인, 실행, 설정의 차례로 그 화면으로 간다", async () => {
    await openSettings();

    expect(screen.getAllByRole("navigation")).toHaveLength(1);
    const links = within(navigation()).getAllByRole("link");
    expect(links.map((link) => [link.textContent, link.getAttribute("href")])).toEqual([
      ["플러그인", "/"],
      ["실행", "/runs"],
      ["설정", "/settings"],
    ]);
  });

  test("제품 이름은 제목이 아닌 글자이고 옛 틀의 제목 관리 화면은 없다", async () => {
    await openSettings();

    expect(within(navigation()).getByText("Agent OS").closest("h1, h2, h3, h4, h5, h6")).toBeNull();
    expect(screen.queryByRole("heading", { name: "관리 화면" })).toBeNull();
    expect(screen.queryByRole("navigation", { name: "화면" })).toBeNull();
  });

  test("하이드레이션 전의 첫 그림은 틀과 탐색만 서고 본문도 관리 토큰 넣기 화면도 없다", () => {
    // 서버가 그린 그림과 하이드레이션의 첫 그림은 서버 스냅숏으로 그려져, 이 탭에 관리 토큰이 있는지 아직 모른다.
    // 그동안 틀만 서지 않으면 토큰을 가진 운영자가 새로 고칠 때마다 넣는 자리가 잠깐 보인다(`hooks/useHydrated`).
    // 넣는 것은 이 시험이 그린 서버 그림이다. 역할로 찾으려고 문서에 붙이고, 단언이 실패해도 걷는다.
    const container = document.createElement("div");
    document.body.append(container);
    try {
      container.innerHTML = renderToString(<SettingsPage />);

      const nav = within(container).getByRole("navigation", { name: "관리 화면" });
      expect(
        within(nav)
          .getAllByRole("link")
          .map((link) => link.textContent),
      ).toEqual(["플러그인", "실행", "설정"]);
      expect(within(container).getByRole("main").textContent).toBe("");
      expect(within(container).queryByLabelText("관리 토큰")).toBeNull();
    } finally {
      container.remove();
    }
  });

  test.each([
    ["플러그인", () => <HomePage />],
    ["실행", () => <RunsPage />],
    ["설정", () => <SettingsPage />],
    ["플러그인", () => <PluginPage kind="agent" name="calc" />],
    ["실행", () => <RunPage runId="r-one" />],
  ])("지금 화면의 탐색 항목 하나에만 aria-current 가 page 다(%s)", async (current, page) => {
    // 읽는 화면은 읽기에 답하지 않아도 틀은 선다. 답하지 않은 요청은 기다리는 채로 둔다.
    network.use(
      http.get(api("/plugins"), () => HttpResponse.json([])),
      http.get(api("/plugins/agent/calc"), () => new Promise<Response>(() => undefined)),
      http.get(api("/traces"), () => new Promise<Response>(() => undefined)),
      http.get(api("/traces/r-one"), () => new Promise<Response>(() => undefined)),
    );
    renderPage(page());
    await enterAdminToken(userEvent.setup(), ADMIN);

    const marked = await within(
      await screen.findByRole("navigation", { name: "관리 화면" }),
    ).findAllByRole("link", { current: "page" });
    expect(marked.map((link) => link.textContent)).toEqual([current]);
  });

  test("채널 토큰을 넣는 자리와 토큰 지우기는 읽는 화면의 머리에 없다", async () => {
    acceptTokens();
    network.use(http.get(api("/traces"), () => new Promise<Response>(() => undefined)));
    renderPage(<RunsPage />);

    await enterAdminToken(userEvent.setup(), ADMIN);

    await screen.findByRole("navigation", { name: "관리 화면" });
    expect(screen.queryByLabelText("채널 토큰")).toBeNull();
    expect(screen.queryByRole("button", { name: "채널 토큰 넣기" })).toBeNull();
    expect(screen.queryByRole("button", { name: "토큰 지우기" })).toBeNull();
  });
});
