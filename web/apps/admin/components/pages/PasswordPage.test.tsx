// 내 비밀번호 바꾸기 화면(admin-login 티켓 12). 누구나 열고, 규칙 목록은 처음부터 보이며 칸에 적는 대로 셈이 바뀐다. 서버의 422 는
// 칸마다 그 칸 아래에, 409 는 잠김 알림으로 보인다. 주 이음매다. 화면을 그려 보고 HTTP 만 MSW 가 받는다.

import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, test } from "vitest";
import { api, envelope, network } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { signedIn } from "../../testing/session";
import { PasswordPage } from "./PasswordPage";

type User = ReturnType<typeof userEvent.setup>;

async function open(): Promise<void> {
  signedIn();
  renderPage(<PasswordPage />);
  await screen.findByRole("heading", { level: 1, name: "내 비밀번호 바꾸기" });
}

/** 칸에 글을 붙여 넣는다. 긴 글도 한 번에 들어간다. */
async function fill(user: User, label: string, text: string): Promise<void> {
  await user.click(screen.getByLabelText(label));
  await user.paste(text);
}

/** 규칙 목록에서 한 규칙의 상태 글("맞음" 또는 "맞지 않음"). */
function ruleState(rule: string): string {
  const list = screen.getByRole("list", { name: "비밀번호 규칙" });
  const item = within(list).getByText(rule).closest("li");
  return item?.textContent.slice(rule.length) ?? "";
}

describe("화면", () => {
  test("머리에 계정 이름이, 버튼 위에 다른 로그인이 길어야 N분 안에 끊긴다는 안내가 처음부터 보인다", async () => {
    await open();

    expect(screen.getByText("kim.dev의 비밀번호를 바꾼다.")).toBeTruthy();
    expect(
      screen.getByText(
        "바꾸면 이 계정의 다른 로그인은 길어야 5분 안에 모두 끊긴다. 이 브라우저의 로그인은 그대로다.",
      ),
    ).toBeTruthy();
  });

  test("탐색의 어느 항목에도 들지 않고 규칙 네 줄이 처음부터 맞지 않음으로 보인다", async () => {
    await open();

    const nav = screen.getByRole("navigation", { name: "관리 화면" });
    expect(
      within(nav)
        .queryAllByRole("link")
        .filter((link) => link.getAttribute("aria-current") === "page"),
    ).toEqual([]);
    for (const rule of ["8자 이상", "영문 대문자 1자 이상", "숫자 1자 이상", "특수문자 1자 이상"]) {
      expect(ruleState(rule)).toBe("맞지 않음");
    }
  });
});

describe("규칙 목록의 셈", () => {
  test("규칙을 맞추는 만큼 맞음으로 바뀐다", async () => {
    const user = userEvent.setup();
    await open();

    await fill(user, "새 비밀번호", "Aa1!aaaa");

    for (const rule of ["8자 이상", "영문 대문자 1자 이상", "숫자 1자 이상", "특수문자 1자 이상"]) {
      expect(ruleState(rule)).toBe("맞음");
    }
  });

  test("자모로 적힌 한글은 정규화한 뒤의 글자로 세어 아홉 자가 일곱 자가 된다", async () => {
    const user = userEvent.setup();
    await open();
    const syllable = "각".normalize("NFD");
    expect(syllable).toHaveLength(3);

    await fill(user, "새 비밀번호", `Aa1!${syllable.repeat(3)}`);
    expect(ruleState("8자 이상")).toBe("맞지 않음");

    await user.clear(screen.getByLabelText("새 비밀번호"));
    await fill(user, "새 비밀번호", `Aa1!${syllable.repeat(4)}`);
    expect(ruleState("8자 이상")).toBe("맞음");
  });

  test("전각 대문자와 숫자는 정규화한 뒤에 대문자와 숫자로 센다", async () => {
    const user = userEvent.setup();
    await open();

    await fill(user, "새 비밀번호", "Ａ１!aaaaa");

    expect(ruleState("영문 대문자 1자 이상")).toBe("맞음");
    expect(ruleState("숫자 1자 이상")).toBe("맞음");
  });

  test("한글은 특수문자로 센다", async () => {
    const user = userEvent.setup();
    await open();

    await fill(user, "새 비밀번호", "가");

    expect(ruleState("특수문자 1자 이상")).toBe("맞음");
  });

  test("그림 문자 128자는 막지 않고 129자부터 128자 이하로 줄이라고 알린다", async () => {
    const user = userEvent.setup();
    await open();

    await fill(user, "새 비밀번호", "😀".repeat(128));
    expect(ruleState("8자 이상")).toBe("맞음");
    expect(screen.queryByText("128자 이하로 줄인다")).toBeNull();

    await user.click(screen.getByLabelText("새 비밀번호"));
    await user.paste("😀");
    expect(screen.getByText("128자 이하로 줄인다")).toBeTruthy();
  });
});

describe("바꾸기", () => {
  test("규칙을 다 맞추지 않으면 보내지 않고 규칙 목록이 알린다", async () => {
    const user = userEvent.setup();
    await open();
    await fill(user, "지금 비밀번호", "old-Pass1!");
    await fill(user, "새 비밀번호", "short");

    await user.click(screen.getByRole("button", { name: "비밀번호 바꾸기" }));

    expect(ruleState("8자 이상")).toBe("맞지 않음");
    expect(screen.getByRole("button", { name: "비밀번호 바꾸기" })).toBeTruthy();
  });

  test("맞게 적어 보내면 두 비밀번호를 보내고 바꿨다는 알림과 로그인이 끊기는 분을 보이며 칸을 비운다", async () => {
    let sent: unknown = null;
    network.use(
      http.post(api("/auth/password"), async ({ request }) => {
        sent = await request.json();
        return new Response(null, { status: 204 });
      }),
    );
    const user = userEvent.setup();
    await open();
    await fill(user, "지금 비밀번호", "old-Pass1!");
    await fill(user, "새 비밀번호", "New-Pass1!x");

    await user.click(screen.getByRole("button", { name: "비밀번호 바꾸기" }));

    const notice = await screen.findByRole("status");
    expect(notice.textContent).toContain("비밀번호를 바꿨다");
    expect(notice.textContent).toContain("다른 곳의 로그인은 길어야 5분 안에 끊긴다");
    expect(sent).toEqual({ current_password: "old-Pass1!", new_password: "New-Pass1!x" });
    expect(screen.getByLabelText("지금 비밀번호")).toHaveProperty("value", "");
    expect(screen.getByLabelText("새 비밀번호")).toHaveProperty("value", "");
  });

  test("지금 비밀번호가 맞지 않다는 422 는 그 칸 아래에, 새 비밀번호의 422 는 새 칸 아래에 알린다", async () => {
    network.use(
      http.post(api("/auth/password"), () =>
        HttpResponse.json(
          {
            ...envelope("invalid_request", "요청의 형식이 올바르지 않다", "req-pw1"),
            violations: [
              { field: "body.current_password", message: "지금 비밀번호가 맞지 않는다" },
              { field: "body.new_password", message: "지금 비밀번호와 같다" },
            ],
          },
          { status: 422 },
        ),
      ),
    );
    const user = userEvent.setup();
    await open();
    await fill(user, "지금 비밀번호", "old-Pass1!");
    await fill(user, "새 비밀번호", "New-Pass1!x");

    await user.click(screen.getByRole("button", { name: "비밀번호 바꾸기" }));

    expect(await screen.findByText("지금 비밀번호가 맞지 않는다")).toBeTruthy();
    expect(screen.getByText("지금 비밀번호와 같다")).toBeTruthy();
    expect(screen.getByLabelText("지금 비밀번호").getAttribute("aria-invalid")).toBe("true");
    expect(screen.getByLabelText("새 비밀번호").getAttribute("aria-invalid")).toBe("true");
  });

  test("계정이 잠겼으면 잠시 뒤에 다시 하라고 알린다", async () => {
    network.use(
      http.post(api("/auth/password"), () =>
        HttpResponse.json(envelope("conflict", "계정이 잠겼다. 잠시 뒤에 다시 한다"), {
          status: 409,
        }),
      ),
    );
    const user = userEvent.setup();
    await open();
    await fill(user, "지금 비밀번호", "old-Pass1!");
    await fill(user, "새 비밀번호", "New-Pass1!x");

    await user.click(screen.getByRole("button", { name: "비밀번호 바꾸기" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("계정이 잠겼다. 잠시 뒤에 다시 한다");
    expect(screen.queryByText("비밀번호를 바꿨다")).toBeNull();
  });

  test("서버가 오류를 내면 봉투의 메시지와 추적 식별자를 알린다", async () => {
    network.use(
      http.post(api("/auth/password"), () =>
        HttpResponse.json(envelope("internal_error", "서버가 멈췄다", "req-pw9"), { status: 500 }),
      ),
    );
    const user = userEvent.setup();
    await open();
    await fill(user, "지금 비밀번호", "old-Pass1!");
    await fill(user, "새 비밀번호", "New-Pass1!x");

    await user.click(screen.getByRole("button", { name: "비밀번호 바꾸기" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("비밀번호를 바꾸지 못했다");
    expect(alert.textContent).toContain("req-pw9");
    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "비밀번호 바꾸기" }).getAttribute("aria-busy"),
      ).toBeNull();
    });
  });
});
