// 테마(admin-style 티켓 09, 명세 "설정 화면과 테마"). 운영자가 설정 화면의 테마 카드를 누르면 저장 버튼 없이 화면 전체가
// 그 테마로 바뀌고, 고른 테마가 이 브라우저의 localStorage 에 남는다. 같은 브라우저의 다른 탭이 바꾼 테마는 모든 화면이
// 따르고, 하이드레이션이 실패해 문서 뿌리의 테마가 지워지면 화면이 마운트될 때 다시 단다.
//
// 테마가 그려지는 자리는 문서 뿌리 `html` 의 `data-theme` 이라 그 속성과 저장 값을 본다. 색은 jsdom 이 CSS 를 싣지 않아
// 스토리(organisms/ThemePicker.stories)가 보고, 첫 그림 전에 다는 스크립트는 그 단위 시험(stores/theme.prepaint.test)과
// e2e 가 본다. 테스트 셋업의 afterEach 가 localStorage 와 함께 `html` 의 `data-theme` 도 걷는다.

import { THEMES } from "@agent-os/ui";
import { act, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http } from "msw";
import { describe, expect, test } from "vitest";
import { api, network } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { acceptTokens, enterAdminToken } from "../../testing/token";
import { HomePage } from "./HomePage";
import { RunsPage } from "./RunsPage";
import { SettingsPage } from "./SettingsPage";

/** 테마를 남기는 저장 키. 값은 테마 키의 글자 그대로다(명세 "저장"). */
const KEY = "agent-os-admin-theme";
const ADMIN = "adm-3Rw8-theme-page-token";

/** 문서 뿌리에 단 테마. 없으면 null 이고 기본 테마(녹청)로 그려진다. */
function rootTheme(): string | null {
  return document.documentElement.getAttribute("data-theme");
}

function themeCards(): HTMLElement {
  return screen.getByRole("group", { name: "테마" });
}

function themeRadio(name: string): HTMLElement {
  return within(themeCards()).getByRole("radio", { name });
}

/** 골라진 카드의 라디오. 하나여야 한다. */
function chosenRadio(): HTMLElement {
  return within(themeCards()).getByRole("radio", { checked: true });
}

/** 같은 브라우저의 다른 탭이 저장소를 바꿨을 때 이 탭에 오는 이벤트를 보낸다. */
function storageChangedElsewhere(init: StorageEventInit): void {
  act(() => {
    window.dispatchEvent(new StorageEvent("storage", init));
  });
}

/** 관리 토큰을 넣어 설정 화면을 연다. */
async function openSettings() {
  acceptTokens();
  renderPage(<SettingsPage />);
  const user = userEvent.setup();
  await enterAdminToken(user, ADMIN);
  await screen.findByRole("heading", { level: 1, name: "설정" });
  return user;
}

/** 설정에서 쪽빛을 고른 상태로 둔다. */
async function openSettingsInJjokbit() {
  const user = await openSettings();
  await user.click(themeRadio("쪽빛"));
  expect(rootTheme()).toBe("jjokbit");
  return user;
}

describe("테마 카드", () => {
  test("테마마다 라디오 하나인 카드가 테마 묶음에 서고 아무것도 고르지 않았으면 기본인 녹청이 골라져 있다", async () => {
    await openSettings();

    // 라디오의 이름은 테마 이름 그대로다. 카드 안의 표본 글자("승인", "끝남")가 이름에 섞이지 않는다.
    expect(within(themeCards()).getAllByRole("radio")).toEqual(
      THEMES.map(({ name }) => themeRadio(name)),
    );
    expect(chosenRadio()).toBe(themeRadio("녹청"));
    expect(screen.getByText("모드(라이트·다크)는 시스템 설정을 따른다.")).toBeTruthy();
    expect(rootTheme()).toBeNull();
  });

  test("카드를 누르면 저장 없이 바로 html 의 data-theme 과 이 브라우저의 저장 값이 그 키가 되고 그 카드가 골라진다", async () => {
    const user = await openSettings();

    await user.click(themeRadio("쪽빛"));

    expect(rootTheme()).toBe("jjokbit");
    expect(localStorage.getItem(KEY)).toBe("jjokbit");
    expect(chosenRadio()).toBe(themeRadio("쪽빛"));
    expect(screen.queryByRole("button", { name: /저장/ })).toBeNull();

    // 기본을 골라도 그 키를 적는다.
    await user.click(themeRadio("녹청"));

    expect(rootTheme()).toBe("nokcheong");
    expect(localStorage.getItem(KEY)).toBe("nokcheong");
    expect(chosenRadio()).toBe(themeRadio("녹청"));
  });

  test("토큰을 지워도 고른 테마는 지우지 않는다", async () => {
    const user = await openSettings();
    await user.click(themeRadio("자초"));

    await user.click(screen.getByRole("button", { name: "토큰 지우기" }));

    expect(await screen.findByLabelText("관리 토큰")).toBeTruthy();
    expect(localStorage.getItem(KEY)).toBe("jacho");
    expect(rootTheme()).toBe("jacho");
  });
});

describe("다른 탭에서 바꾼 테마", () => {
  test("다른 탭이 저장 값을 바꾸면 html 과 테마 카드가 그 테마를 따른다", async () => {
    await openSettingsInJjokbit();

    storageChangedElsewhere({ key: KEY, oldValue: "jjokbit", newValue: "guncheong" });

    expect(rootTheme()).toBe("guncheong");
    expect(chosenRadio()).toBe(themeRadio("군청"));
  });

  test.each([
    ["목록에 없는 값이 오면", { key: KEY, oldValue: "jjokbit", newValue: "purple" }],
    ["테마 키가 지워지면", { key: KEY, oldValue: "jjokbit", newValue: null }],
    ["저장소 전체가 비워지면(키가 없는 이벤트)", { key: null, oldValue: null, newValue: null }],
  ])("%s 속성을 걷어 기본으로 그리고 녹청 카드가 골라진다", async (_, init) => {
    await openSettingsInJjokbit();

    storageChangedElsewhere(init);

    expect(rootTheme()).toBeNull();
    expect(chosenRadio()).toBe(themeRadio("녹청"));
  });

  test("테마 키가 아닌 키의 이벤트는 무시한다", async () => {
    await openSettingsInJjokbit();

    storageChangedElsewhere({ key: "agent-os-admin-tokens", oldValue: "{}", newValue: null });
    storageChangedElsewhere({ key: "another-key", oldValue: null, newValue: "guncheong" });

    expect(rootTheme()).toBe("jjokbit");
    expect(chosenRadio()).toBe(themeRadio("쪽빛"));
  });

  test("설정이 아닌 화면에서도 다른 탭이 바꾼 테마를 html 이 따른다", async () => {
    acceptTokens();
    network.use(http.get(api("/traces"), () => new Promise<Response>(() => undefined)));
    renderPage(<RunsPage />);
    await enterAdminToken(userEvent.setup(), ADMIN);
    await screen.findByRole("navigation", { name: "관리 화면" });

    storageChangedElsewhere({ key: KEY, oldValue: null, newValue: "jacho" });

    expect(rootTheme()).toBe("jacho");
  });
});

describe("화면이 마운트될 때", () => {
  test("저장 값이 테마 키이고 html 과 다르면 다시 단다", () => {
    localStorage.setItem(KEY, "jjokbit");
    // 앞 시험이 단 속성이 남아 초록이 되는 길을 막는다.
    expect(rootTheme()).toBeNull();

    renderPage(<HomePage />);

    expect(rootTheme()).toBe("jjokbit");
  });

  test("저장 값이 목록에 없으면 아무것도 달지 않는다", () => {
    localStorage.setItem(KEY, "purple");

    renderPage(<HomePage />);

    expect(rootTheme()).toBeNull();
  });
});
