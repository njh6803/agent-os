// 계정 화면(admin-login 티켓 12). 시스템 관리자만 열고, 줄 끝의 메뉴는 계정의 단계와 상태에 따라 갈리며, 만들기와 링크와
// 비활성으로 바꾸기는 창을 지난다. 주 이음매다. 화면을 그려 보고 HTTP 만 MSW 가 받는다.
//
// 본문 칸이 `split` 이상이면 표, 미만이면 카드를 보이는 두 갈래를 함께 그리고 CSS 로 하나를 숨기는데(실행 목록과 같다), jsdom 은
// CSS 를 싣지 않아 둘이 다 있다. 그래서 줄과 메뉴는 표 안에서 찾는다.

import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, test } from "vitest";
import type { AccountRow } from "../../api/accounts";
import { api, envelope, network } from "../../testing/network";
import { renderPage } from "../../testing/render";
import { signedIn } from "../../testing/session";
import { AccountsPage } from "./AccountsPage";

type Account = AccountRow;

const minutesFromNow = (minutes: number): string =>
  new Date(Date.now() + minutes * 60_000).toISOString();

function accounts(): Account[] {
  return [
    {
      name: "ops-lead",
      tier: "system_admin",
      state: "active",
      locked_until: null,
      created_at: "2026-11-01T09:12:00Z",
    },
    {
      name: "root.two",
      tier: "system_admin",
      state: "active",
      locked_until: minutesFromNow(15),
      created_at: "2026-11-02T09:12:00Z",
    },
    {
      name: "kim.dev",
      tier: "admin",
      state: "active",
      locked_until: null,
      created_at: "2026-11-03T14:20:00Z",
    },
    {
      name: "park.sre",
      tier: "admin",
      state: "active",
      locked_until: minutesFromNow(20),
      created_at: "2026-11-04T10:05:00Z",
    },
    {
      name: "lee.qa",
      tier: "admin",
      state: "password_unset",
      locked_until: null,
      created_at: "2026-11-15T15:18:00Z",
    },
    {
      name: "choi.ml",
      tier: "admin",
      state: "disabled",
      locked_until: null,
      created_at: "2026-11-08T11:30:00Z",
    },
  ];
}

interface Server {
  readonly reads: () => number;
  readonly writes: string[];
}

/** 계정 목록을 돌려주고 쓰기를 `writes` 에 적는 가짜 서버. 쓰기는 모두 성공한다. */
function serve(list: Account[] = accounts()): Server {
  let reads = 0;
  const writes: string[] = [];
  network.use(
    http.get(api("/accounts"), () => {
      reads += 1;
      return HttpResponse.json({ accounts: list });
    }),
    http.post(api("/accounts/:name/link"), ({ params }) => {
      writes.push(`link ${String(params["name"])}`);
      return HttpResponse.json(
        { link_token: "tok-link_1", link_expires_at: "2026-11-28T09:00:00Z" },
        { status: 201 },
      );
    }),
    http.post(api("/accounts/:name/unlock"), ({ params }) => {
      writes.push(`unlock ${String(params["name"])}`);
      return new Response(null, { status: 204 });
    }),
    http.put(api("/accounts/:name/active"), async ({ params, request }) => {
      const body: unknown = await request.json();
      const active =
        typeof body === "object" && body !== null && "active" in body ? body.active : null;
      writes.push(`active ${String(params["name"])} ${String(active)}`);
      return new Response(null, { status: 204 });
    }),
  );
  return { reads: () => reads, writes };
}

async function open(
  me: Parameters<typeof signedIn>[0] = { tier: "system_admin", name: "ops-lead" },
) {
  signedIn(me);
  renderPage(<AccountsPage />);
  await screen.findByRole("heading", { level: 1, name: "운영자 계정" });
  return screen.findByRole("table");
}

async function openMenuOf(
  user: ReturnType<typeof userEvent.setup>,
  table: HTMLElement,
  name: string,
): Promise<string[]> {
  await user.click(within(table).getByRole("button", { name: `${name}의 동작` }));
  const menu = screen.getByRole("menu", { name: `${name}의 동작` });
  return within(menu)
    .getAllByRole("menuitem")
    .map((item) => item.textContent);
}

describe("누가 여는가", () => {
  test("시스템 관리자의 탐색에는 계정이 있고 지금 화면으로 표시된다", async () => {
    serve();
    await open();

    const link = screen.getByRole("link", { name: "계정" });
    expect(link.getAttribute("href")).toBe("/accounts");
    expect(link.getAttribute("aria-current")).toBe("page");
  });

  test("관리자의 탐색에는 계정이 없고 주소로 열면 한 줄만 보이며 계정 목록을 묻지 않는다", async () => {
    const server = serve();
    signedIn({ tier: "admin" });

    renderPage(<AccountsPage />);

    expect(await screen.findByText("이 계정으로는 볼 수 없다")).toBeTruthy();
    expect(screen.queryByRole("link", { name: "계정" })).toBeNull();
    expect(screen.queryByRole("heading", { level: 1, name: "운영자 계정" })).toBeNull();
    expect(server.reads()).toBe(0);
  });
});

describe("목록", () => {
  test("열은 계정 이름, 단계, 상태, 만든 시각, 동작이고 로그인한 계정의 줄에 지금 계정이 붙는다", async () => {
    serve();
    const table = await open();

    const heads = within(table)
      .getAllByRole("columnheader")
      .map((head) => head.textContent);
    expect(heads).toEqual(["계정 이름", "단계", "상태", "만든 시각", "동작"]);
    const ops = within(table).getByRole("row", { name: /ops-lead/ });
    expect(ops.textContent).toContain("지금 계정");
    expect(ops.textContent).toContain("시스템 관리자");
    const kim = within(table).getByRole("row", { name: /kim\.dev/ });
    expect(kim.textContent).not.toContain("지금 계정");
    expect(kim.textContent).toContain("관리자");
  });

  test("상태는 배지이고 잠긴 계정은 잠김 배지와 풀리는 시각이 함께 선다", async () => {
    serve();
    const table = await open();

    expect(
      within(within(table).getByRole("row", { name: /kim\.dev/ })).getByText("활성"),
    ).toBeTruthy();
    expect(
      within(within(table).getByRole("row", { name: /lee\.qa/ })).getByText("비밀번호 미설정"),
    ).toBeTruthy();
    const locked = within(table).getByRole("row", { name: /park\.sre/ });
    expect(within(locked).getByText("활성")).toBeTruthy();
    expect(within(locked).getByText("잠김")).toBeTruthy();
    expect(within(locked).getByText(/^\d\d:\d\d까지$/)).toBeTruthy();
  });

  test("비활성 계정은 기본으로 숨기고 비활성 계정도 보기를 켜면 보인다", async () => {
    serve();
    const user = userEvent.setup();
    const table = await open();
    expect(within(table).queryByText("choi.ml")).toBeNull();

    await user.click(screen.getByRole("switch", { name: "비활성 계정도 보기" }));

    const row = within(screen.getByRole("table")).getByRole("row", { name: /choi\.ml/ });
    expect(within(row).getByText("비활성")).toBeTruthy();
  });

  test("목록을 읽지 못하면 이미 보인 것 없이 실패만 보인다", async () => {
    network.use(
      http.get(api("/accounts"), () =>
        HttpResponse.json(envelope("internal_error", "서버가 멈췄다", "req-acc1"), { status: 500 }),
      ),
    );
    signedIn({ tier: "system_admin", name: "ops-lead" });

    renderPage(<AccountsPage />);

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("계정 목록을 읽지 못했다");
    expect(alert.textContent).toContain("req-acc1");
    expect(screen.queryByRole("table")).toBeNull();
  });
});

describe("줄 끝의 메뉴", () => {
  test("시스템 관리자의 줄에는 메뉴가 없고 잠겼을 때만 잠금 풀기 하나가 선다", async () => {
    serve();
    const user = userEvent.setup();
    const table = await open();

    expect(within(table).queryByRole("button", { name: "ops-lead의 동작" })).toBeNull();
    expect(await openMenuOf(user, table, "root.two")).toEqual(["잠금 풀기"]);
  });

  test("활성 계정의 메뉴는 링크 만들기와 비활성으로 바꾸기이고 잠겼으면 그 사이에 잠금 풀기가 든다", async () => {
    serve();
    const user = userEvent.setup();
    const table = await open();

    expect(await openMenuOf(user, table, "kim.dev")).toEqual([
      "비밀번호 링크 만들기",
      "비활성으로 바꾸기",
    ]);
    await user.keyboard("{Escape}");
    expect(await openMenuOf(user, table, "park.sre")).toEqual([
      "비밀번호 링크 만들기",
      "잠금 풀기",
      "비활성으로 바꾸기",
    ]);
  });

  test("비밀번호를 정하기 전의 계정에도 링크 만들기가 있다", async () => {
    serve();
    const user = userEvent.setup();
    const table = await open();

    expect(await openMenuOf(user, table, "lee.qa")).toContain("비밀번호 링크 만들기");
  });

  test("비활성 계정의 메뉴에는 활성으로 바꾸기만 있고 누르면 창 없이 바로 바꾼다", async () => {
    const server = serve();
    const user = userEvent.setup();
    await open();
    await user.click(screen.getByRole("switch", { name: "비활성 계정도 보기" }));
    const table = screen.getByRole("table");

    expect(await openMenuOf(user, table, "choi.ml")).toEqual(["활성으로 바꾸기"]);
    await user.click(screen.getByRole("menuitem", { name: "활성으로 바꾸기" }));

    await waitFor(() => {
      expect(server.writes).toEqual(["active choi.ml true"]);
    });
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  test("메뉴는 눌러 열면 첫 항목에 포커스가 가고 Esc 로 닫으면 단추로 돌아온다", async () => {
    serve();
    const user = userEvent.setup();
    const table = await open();
    const trigger = within(table).getByRole("button", { name: "kim.dev의 동작" });

    await user.click(trigger);
    expect(document.activeElement).toBe(
      screen.getByRole("menuitem", { name: "비밀번호 링크 만들기" }),
    );
    await user.keyboard("{Escape}");

    expect(screen.queryByRole("menu")).toBeNull();
    expect(document.activeElement).toBe(trigger);
  });

  test("잠금 풀기를 누르면 그 계정의 잠금을 풀고 목록을 다시 읽는다", async () => {
    const server = serve();
    const user = userEvent.setup();
    const table = await open();
    await openMenuOf(user, table, "park.sre");

    await user.click(screen.getByRole("menuitem", { name: "잠금 풀기" }));

    await waitFor(() => {
      expect(server.writes).toEqual(["unlock park.sre"]);
    });
    await waitFor(() => {
      expect(server.reads()).toBe(2);
    });
  });

  test("메뉴의 쓰기가 실패하면 목록 위에 알린다", async () => {
    serve();
    network.use(
      http.post(api("/accounts/:name/unlock"), () =>
        HttpResponse.json(envelope("internal_error", "서버가 멈췄다", "req-unl1"), { status: 500 }),
      ),
    );
    const user = userEvent.setup();
    const table = await open();
    await openMenuOf(user, table, "park.sre");

    await user.click(screen.getByRole("menuitem", { name: "잠금 풀기" }));

    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("계정을 바꾸지 못했다");
    expect(alert.textContent).toContain("req-unl1");
  });
});

describe("비밀번호 링크 창", () => {
  const ADDRESS = (token: string): string =>
    `${new URL("/set-password", location.origin).href}#${token}`;

  test("메뉴에서 링크를 만들면 주소와 복사 단추와 네 줄이 선다", async () => {
    const server = serve();
    const user = userEvent.setup();
    const table = await open();
    await openMenuOf(user, table, "lee.qa");

    await user.click(screen.getByRole("menuitem", { name: "비밀번호 링크 만들기" }));

    const dialog = await screen.findByRole("dialog", { name: "lee.qa의 비밀번호 링크" });
    expect(server.writes).toEqual(["link lee.qa"]);
    expect(within(dialog).getByText(ADDRESS("tok-link_1"))).toBeTruthy();
    expect(within(dialog).getByRole("button", { name: "복사" })).toBeTruthy();
    expect(dialog.textContent).toContain("이 링크를 lee.qa에게 직접 전한다. 메일은 보내지 않는다.");
    expect(dialog.textContent).toMatch(/한 번만 쓰인다\. .+에 끝난다\(만든 뒤 24시간\)\./);
    expect(dialog.textContent).toContain("다시 만들면 이 링크는 쓸 수 없다.");
    expect(dialog.textContent).toContain(
      "서버는 링크를 다시 보여 주지 못한다. 잃으면 새로 만든다.",
    );
  });

  test("복사를 누르면 주소를 클립보드에 넣고 복사했다고 알린다", async () => {
    serve();
    const user = userEvent.setup();
    const table = await open();
    await openMenuOf(user, table, "lee.qa");
    await user.click(screen.getByRole("menuitem", { name: "비밀번호 링크 만들기" }));
    const dialog = await screen.findByRole("dialog", { name: "lee.qa의 비밀번호 링크" });

    await user.click(within(dialog).getByRole("button", { name: "복사" }));

    expect(await within(dialog).findByRole("button", { name: "복사했다" })).toBeTruthy();
    expect(await navigator.clipboard.readText()).toBe(ADDRESS("tok-link_1"));
  });

  test("창을 닫으면 링크가 화면에서도 사라지고 포커스가 단추로 돌아온다", async () => {
    serve();
    const user = userEvent.setup();
    const table = await open();
    await openMenuOf(user, table, "lee.qa");
    await user.click(screen.getByRole("menuitem", { name: "비밀번호 링크 만들기" }));
    const dialog = await screen.findByRole("dialog", { name: "lee.qa의 비밀번호 링크" });

    await user.click(within(dialog).getByRole("button", { name: "닫기" }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(screen.queryByText(ADDRESS("tok-link_1"))).toBeNull();
    expect(document.activeElement).toBe(
      within(table).getByRole("button", { name: "lee.qa의 동작" }),
    );
  });

  test("Esc 로도 닫힌다", async () => {
    serve();
    const user = userEvent.setup();
    const table = await open();
    await openMenuOf(user, table, "lee.qa");
    await user.click(screen.getByRole("menuitem", { name: "비밀번호 링크 만들기" }));
    await screen.findByRole("dialog", { name: "lee.qa의 비밀번호 링크" });

    await user.keyboard("{Escape}");

    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

describe("계정 만들기 창", () => {
  async function openCreate(user: ReturnType<typeof userEvent.setup>): Promise<HTMLElement> {
    await open();
    await user.click(screen.getByRole("button", { name: "계정 만들기" }));
    return screen.getByRole("dialog", { name: "계정 만들기" });
  }

  test("이름을 넣고 만들면 곧바로 비밀번호 링크 창이 열린다", async () => {
    serve();
    let sent: unknown = null;
    network.use(
      http.post(api("/accounts"), async ({ request }) => {
        sent = await request.json();
        return HttpResponse.json(
          {
            name: "new.ops",
            tier: "admin",
            link_token: "tok-new_1",
            link_expires_at: "2026-11-28T09:00:00Z",
          },
          { status: 201 },
        );
      }),
    );
    const user = userEvent.setup();
    const dialog = await openCreate(user);
    expect(dialog.textContent).toContain("단계: 관리자");

    await user.type(within(dialog).getByLabelText("계정 이름"), "new.ops");
    await user.click(within(dialog).getByRole("button", { name: "만들기" }));

    const link = await screen.findByRole("dialog", { name: "new.ops의 비밀번호 링크" });
    expect(sent).toEqual({ name: "new.ops" });
    expect(
      within(link).getByText(`${new URL("/set-password", location.origin).href}#tok-new_1`),
    ).toBeTruthy();
    expect(screen.queryByRole("dialog", { name: "계정 만들기" })).toBeNull();
  });

  test("이름이 규칙을 어기면 칸을 떠날 때 알리고 보내지 않는다", async () => {
    serve();
    const user = userEvent.setup();
    const dialog = await openCreate(user);

    await user.type(within(dialog).getByLabelText("계정 이름"), "ab");
    await user.tab();

    expect(within(dialog).getByText(/^규칙에 맞지 않는 이름이다/)).toBeTruthy();

    await user.click(within(dialog).getByRole("button", { name: "만들기" }));
    expect(screen.getByRole("dialog", { name: "계정 만들기" })).toBeTruthy();
  });

  test("이미 있는 이름이면 칸 아래에 비활성 계정을 포함한다고 알리고 창을 닫지 않는다", async () => {
    serve();
    network.use(
      http.post(api("/accounts"), () =>
        HttpResponse.json(envelope("conflict", "이미 있다", "req-409"), { status: 409 }),
      ),
    );
    const user = userEvent.setup();
    const dialog = await openCreate(user);

    await user.type(within(dialog).getByLabelText("계정 이름"), "kim.dev");
    await user.click(within(dialog).getByRole("button", { name: "만들기" }));

    expect(await within(dialog).findByText("이 이름의 계정이 있다(비활성 계정 포함)")).toBeTruthy();
    expect(screen.getByRole("dialog", { name: "계정 만들기" })).toBeTruthy();
  });

  test("서버가 이름을 규칙 위반으로 보면 그 문구를 칸 아래에 보인다", async () => {
    serve();
    network.use(
      http.post(api("/accounts"), () =>
        HttpResponse.json(
          {
            ...envelope("invalid_request", "요청의 형식이 올바르지 않다", "req-422"),
            violations: [{ field: "body.name", message: "서버가 본 이름 규칙 위반" }],
          },
          { status: 422 },
        ),
      ),
    );
    const user = userEvent.setup();
    const dialog = await openCreate(user);

    await user.type(within(dialog).getByLabelText("계정 이름"), "abc");
    await user.click(within(dialog).getByRole("button", { name: "만들기" }));

    expect(await within(dialog).findByText("서버가 본 이름 규칙 위반")).toBeTruthy();
  });
});

describe("비활성으로 바꾸기 창", () => {
  async function openDisable(user: ReturnType<typeof userEvent.setup>): Promise<HTMLElement> {
    const table = await open();
    await openMenuOf(user, table, "kim.dev");
    await user.click(screen.getByRole("menuitem", { name: "비활성으로 바꾸기" }));
    return screen.getByRole("dialog", { name: "kim.dev을 비활성으로 바꾼다" });
  }

  test("제목과 네 줄이 서고 첫 줄은 로그인이 끊기는 분을 알린다", async () => {
    serve();
    const user = userEvent.setup();
    const dialog = await openDisable(user);

    const lines = within(dialog)
      .getAllByRole("listitem")
      .map((item) => item.textContent);
    expect(lines).toEqual([
      "이 계정의 로그인은 길어야 5분 안에 모두 끊긴다. 도는 실행은 끝까지 간다.",
      "이 이름으로 새 계정을 만들 수 없다.",
      "실행 기록에 남은 이름은 그대로다.",
      "언제든 활성으로 되돌릴 수 있다.",
    ]);
  });

  test("로그인이 끊기는 분은 서버가 알려 준 값이다", async () => {
    serve();
    signedIn({ tier: "system_admin", name: "ops-lead", token_minutes: 15 });
    const user = userEvent.setup();
    renderPage(<AccountsPage />);
    const table = await screen.findByRole("table");
    await openMenuOf(user, table, "kim.dev");
    await user.click(screen.getByRole("menuitem", { name: "비활성으로 바꾸기" }));

    const dialog = screen.getByRole("dialog", { name: "kim.dev을 비활성으로 바꾼다" });
    expect(dialog.textContent).toContain("길어야 15분 안에");
  });

  test("바꾸기를 누르면 비활성으로 바꾸고 목록을 다시 읽으며 창이 닫힌다", async () => {
    const server = serve();
    const user = userEvent.setup();
    const dialog = await openDisable(user);

    await user.click(within(dialog).getByRole("button", { name: "비활성으로 바꾸기" }));

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).toBeNull();
    });
    expect(server.writes).toEqual(["active kim.dev false"]);
    expect(server.reads()).toBe(2);
  });

  test("취소하면 아무것도 바꾸지 않고 창이 닫힌다", async () => {
    const server = serve();
    const user = userEvent.setup();
    const dialog = await openDisable(user);

    await user.click(within(dialog).getByRole("button", { name: "취소" }));

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(server.writes).toEqual([]);
  });

  test("바꾸지 못하면 창 안에서 알리고 창을 닫지 않는다", async () => {
    serve();
    network.use(
      http.put(api("/accounts/:name/active"), () =>
        HttpResponse.json(envelope("internal_error", "서버가 멈췄다", "req-dis1"), { status: 500 }),
      ),
    );
    const user = userEvent.setup();
    const dialog = await openDisable(user);

    await user.click(within(dialog).getByRole("button", { name: "비활성으로 바꾸기" }));

    const alert = await within(dialog).findByRole("alert");
    expect(alert.textContent).toContain("req-dis1");
    expect(screen.getByRole("dialog", { name: "kim.dev을 비활성으로 바꾼다" })).toBeTruthy();
  });
});
