// 설정 화면과 틀의 탐색(admin-style 티켓 04, admin-login 티켓 09). 운영자가 탐색으로 화면을 옮기고, 설정에서 테마를 고른다.
// 관리 화면은 토큰이 아니라 쿠키로 로그인하므로 이 화면에는 토큰을 넣는 칸도 지우는 단추도 없다.
//
// 주 이음매다. 페이지를 jsdom 에 그리고 HTTP 만 MSW 가 받는다. 탐색은 옆 탐색과 위 막대가 같은 `nav` 하나라 jsdom
// 에도 하나만 보인다(폭에 따른 배치는 CSS 이고 스토리가 본다).

import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, test } from "vitest";
import { api, network } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { signedIn } from "../../testing/session";
import { HomePage } from "./HomePage";
import { PluginPage } from "./PluginPage";
import { RunPage } from "./RunPage";
import { RunsPage } from "./RunsPage";
import { SettingsPage } from "./SettingsPage";

/** 옛 방식이 관리 토큰과 채널 토큰을 담던 탭 저장소의 키. 화면이 마운트될 때 지운다. */
const OLD_TOKENS_KEY = "agent-os-admin-tokens";

/** 로그인한 채로 설정 화면을 연다. */
async function openSettings(): Promise<void> {
  signedIn();
  renderPage(<SettingsPage />);
  await screen.findByRole("heading", { level: 1, name: "설정" });
}

function navigation(): HTMLElement {
  return screen.getByRole("navigation", { name: "관리 화면" });
}

describe("설정 화면", () => {
  test("머리는 h1 설정과 설명이고 그 밖의 소제목은 없다", async () => {
    await openSettings();

    expect(screen.getAllByRole("heading", { level: 1 }).map((h) => h.textContent)).toEqual([
      "설정",
    ]);
    expect(screen.getByText("테마는 이 브라우저에 남는다.")).toBeTruthy();
    // 읽는 화면이 아니라 새로 고침이 없다.
    expect(screen.queryByRole("button", { name: "새로 고침" })).toBeNull();
  });

  test("화면을 그리면 옛 방식이 탭에 남긴 토큰 키를 지운다", async () => {
    sessionStorage.setItem(
      OLD_TOKENS_KEY,
      JSON.stringify({ admin: "adm-old", channel: "chn-old" }),
    );

    await openSettings();

    expect(sessionStorage.getItem(OLD_TOKENS_KEY)).toBeNull();
  });

  test("본문에 토큰을 넣는 칸이 없다", async () => {
    await openSettings();

    expect(screen.queryByLabelText("채널 토큰")).toBeNull();
    expect(screen.queryByLabelText("관리 토큰")).toBeNull();
    expect(screen.queryByRole("button", { name: "토큰 지우기" })).toBeNull();
  });
});

describe("틀과 탐색", () => {
  test("탐색은 관리 화면이라는 이름 하나이고 플러그인, 대화, 실행, 설정의 차례로 그 화면으로 간다", async () => {
    await openSettings();

    expect(screen.getAllByRole("navigation")).toHaveLength(1);
    const links = within(navigation()).getAllByRole("link");
    expect(links.map((link) => [link.textContent, link.getAttribute("href")])).toEqual([
      ["플러그인", "/"],
      ["대화", "/chat"],
      ["실행", "/runs"],
      ["설정", "/settings"],
    ]);
  });

  test("제품 이름은 제목이 아닌 글자이고 옛 틀의 제목 관리 화면은 없다", async () => {
    await openSettings();

    // 제품 이름은 탐색 옆 머리에 선다(탐색 안이 아니다).
    expect(screen.getByText("Agent OS").closest("h1, h2, h3, h4, h5, h6")).toBeNull();
    expect(screen.queryByRole("heading", { name: "관리 화면" })).toBeNull();
    expect(screen.queryByRole("navigation", { name: "화면" })).toBeNull();
  });

  test.each([
    ["플러그인", () => <HomePage />],
    ["실행", () => <RunsPage />],
    ["설정", () => <SettingsPage />],
    ["플러그인", () => <PluginPage kind="agent" name="calc" />],
    ["실행", () => <RunPage runId="r-one" />],
  ])("지금 화면의 탐색 항목 하나에만 aria-current 가 page 다(%s)", async (current, page) => {
    // 읽는 화면은 읽기에 답하지 않아도 틀은 선다. 답하지 않은 요청은 기다리는 채로 둔다.
    signedIn();
    network.use(
      http.get(api("/plugins"), () => HttpResponse.json([])),
      http.get(api("/plugins/agent/calc"), () => new Promise<Response>(() => undefined)),
      http.get(api("/traces"), () => new Promise<Response>(() => undefined)),
      http.get(api("/traces/r-one"), () => new Promise<Response>(() => undefined)),
    );
    renderPage(page());

    const marked = await within(
      await screen.findByRole("navigation", { name: "관리 화면" }),
    ).findAllByRole("link", { current: "page" });
    expect(marked.map((link) => link.textContent)).toEqual([current]);
  });

  test("토큰을 넣는 자리와 토큰 지우기는 읽는 화면의 머리에 없다", async () => {
    signedIn();
    network.use(http.get(api("/traces"), () => new Promise<Response>(() => undefined)));
    renderPage(<RunsPage />);

    await screen.findByRole("navigation", { name: "관리 화면" });
    expect(screen.queryByLabelText("채널 토큰")).toBeNull();
    expect(screen.queryByLabelText("관리 토큰")).toBeNull();
    expect(screen.queryByRole("button", { name: "토큰 지우기" })).toBeNull();
  });
});
