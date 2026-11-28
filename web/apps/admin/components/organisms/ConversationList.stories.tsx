// 대화 목록(admin-login 티켓 10, 화면 디자인 ch-list, ch-list-m). 틀 없이 그리고, 미리보기의 데코레이터가 본문 칸과 같은
// 컨테이너를 두른다. 넓은 폭(admin-storybook-wide)에서는 표, 좁은 폭(admin-storybook-narrow)에서는 대화마다 카드다. 그
// 갈래는 사진만이 아니라 위치와 역할로 본다.
//
// 표본 값은 그림의 것이다. 첫 요청이 열 폭보다 긴 줄, 앞부분을 읽지 못한 줄, 요청한 계정이 빈 줄 둘(운영자 채널의 실행과
// 최종 사용자의 대화), 읽을 수 없는 트레이스의 표지 줄을 한 목록에 둔다. 시각은 사진을 찍는 Asia/Seoul 로 적히고
// (visual/playwright.config.ts) play 는 시각 글자를 단언하지 않는다. 거르기와 더 보기를 누르는 행동은 페이지 시험
// (pages/ConversationsPage.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, waitFor, within } from "storybook/test";
import type { Conversation, ConversationPage, ConversationRow } from "../../api/conversations";
import { ConversationList } from "./ConversationList";

/** 문서 뿌리에 선언된 디자인 토큰의 값. */
function rootToken(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/** 넓은 폭의 프로젝트인가. 두 프로젝트의 창은 1280 과 320 이라 화면 중단점 `wide` 로 가른다. */
function isWideProject(): boolean {
  return window.matchMedia(`(min-width: ${rootToken("--breakpoint-wide")})`).matches;
}

function conversation(lastRun: string, extra: Partial<Conversation>): Conversation {
  return {
    agent: "support-bot",
    complete: true,
    first_request: "",
    last_at: "2026-10-12T05:03:25+00:00",
    last_run: lastRun,
    last_started_at: "2026-10-12T05:03:22+00:00",
    principal: "operator",
    requesting_account: "kim.dev",
    run_count: 1,
    status: "finished",
    ...extra,
  };
}

const ROWS: readonly ConversationRow[] = [
  conversation("7f3a2c91-4b8e-4d1a-9c2f-0e6b5a8d3f12", {
    first_request: "지난주 환불 요청 가운데 아직 처리하지 않은 것을 찾아 줘",
    run_count: 3,
    status: "paused",
  }),
  conversation("0b9e5d14-2a7c-4f3e-8d61-c4a2b9e07f5d", {
    first_request:
      "ORD-2026-11-08-000184 환불을 진행해 줘. 배송이 열흘 넘게 늦어서 고객이 취소를 원하고, 결제 수단은 카드이며 부분 환불은 원하지 않는다고 했다",
    agent: "calc",
    last_at: "2026-10-12T04:58:11+00:00",
    last_started_at: "2026-10-12T04:58:07+00:00",
    requesting_account: "lee.ops",
    run_count: 2,
  }),
  conversation("c51f8a07-9d3b-4e2a-b6f4-17e8d0c3a92b", {
    first_request: "이번 달 환불 내역을 정리해 줘",
    complete: false,
    last_at: "2026-10-12T04:42:31+00:00",
    last_started_at: "2026-10-12T04:41:50+00:00",
    run_count: 4,
    status: "failed",
  }),
  conversation("5d27e3b0-6c1f-4a8d-93e5-b8f0a4c6d211", {
    first_request: "서버 점검 공지를 써 줘",
    agent: "calc",
    last_at: "2026-10-12T02:20:04+00:00",
    last_started_at: "2026-10-12T02:20:03+00:00",
    principal: "deploy-user",
    requesting_account: null,
    status: "unfinished",
  }),
  conversation("e8a4b2f6-1d9c-4b7e-a053-6f2c8e1d4b90", {
    first_request: "배송은 언제 오나요?",
    last_at: "2026-10-11T09:12:52+00:00",
    last_started_at: "2026-10-11T09:12:45+00:00",
    principal: "https://shop.example|user-17",
    requesting_account: null,
  }),
  {
    run_id: "9a0c6e12-7b3d-4f1a-8e25-c6d4b0a9f371",
    reason: "traces/9a0c6e12-7b3d-4f1a-8e25-c6d4b0a9f371.jsonl: 첫 줄의 형식 버전이 없다",
  },
];

const NEXT_PAGE: readonly ConversationPage[] = [{ conversations: [...ROWS], next_cursor: "cur-2" }];

const meta = {
  title: "organisms/ConversationList",
  component: ConversationList,
  args: {
    data: NEXT_PAGE,
    error: undefined,
    isValidating: false,
    onRefresh: fn(),
    status: null,
    onStatusChange: fn(),
    onMore: fn(),
  },
} satisfies Meta<typeof ConversationList>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * 다음 쪽이 있는 목록. 넓은 폭에서는 표이고 열 머리는 `<th scope="col">`, 행 높이는 `h-row` 다. 좁은 폭에서는 대화마다
 * 카드다. 첫 요청의 링크는 끝 실행의 대화 주소로 가고 포인터 목표는 24px 이상이다. 긴 첫 요청은 열 폭에서 줄고, 앞부분을
 * 읽지 못한 줄에는 그 말이 서며, 요청한 계정이 빈 줄은 주체를 흐린 글자로 보인다(최종 사용자는 그 앞에 "최종 사용자").
 */
export const List: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const region = within(canvas.getByRole("region", { name: "대화" }));
    await expect(canvas.getByRole("heading", { level: 1 })).toHaveTextContent(/^대화$/);
    let shown: HTMLElement;
    if (isWideProject()) {
      shown = region.getByRole("table");
      await expect(region.queryByRole("list")).toBeNull();
      const headers = within(shown).getAllByRole("columnheader");
      await expect(headers.map((header) => header.textContent)).toEqual([
        "첫 요청",
        "요청한 계정",
        "에이전트",
        "상태",
        "실행",
        "마지막",
      ]);
      const [, first] = within(shown).getAllByRole("row");
      await expect(first?.getBoundingClientRect().height).toBe(
        Number.parseFloat(rootToken("--row-h")),
      );
      // 긴 첫 요청은 칸에서 한 줄로 줄어 줄 높이를 늘리지 않는다.
      for (const row of within(shown).getAllByRole("row").slice(1)) {
        await expect(row.getBoundingClientRect().height).toBe(
          Number.parseFloat(rootToken("--row-h")),
        );
      }
    } else {
      shown = region.getByRole("list");
      await expect(region.queryByRole("table")).toBeNull();
      await expect(within(shown).getAllByRole("listitem")).toHaveLength(ROWS.length);
    }
    await expect(shown).toBeVisible();
    const links = region.getAllByRole("link");
    await expect(links).toHaveLength(ROWS.length);
    for (const link of links) {
      await expect(link.getBoundingClientRect().height).toBeGreaterThanOrEqual(24);
    }
    await expect(within(shown).getByText("앞부분을 읽지 못함")).toBeVisible();
    await expect(within(shown).getByText("deploy-user")).toBeVisible();
    await expect(within(shown).getByText("최종 사용자 https://shop.example|user-17")).toBeVisible();
    await expect(
      within(shown).getByText(
        "읽을 수 없는 트레이스: traces/9a0c6e12-7b3d-4f1a-8e25-c6d4b0a9f371.jsonl: 첫 줄의 형식 버전이 없다",
      ),
    ).toBeVisible();
    await expect(canvas.getByRole("button", { name: "더 보기" })).toBeVisible();
  },
};

/** 실패로 거른 목록이 비었다. 그 상태의 배지 아이콘(20)과 한 줄이고, 거르기는 남는다. */
export const FilteredEmpty: Story = {
  args: { status: "failed", data: [{ conversations: [], next_cursor: null }] },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const line = canvas.getByText("실패한 대화가 없다");
    await expect(line).toBeVisible();
    const icon = line.querySelector("svg");
    await expect(icon?.getBoundingClientRect().width).toBe(
      Number.parseFloat(rootToken("--spacing-icon-m")),
    );
    await expect(canvas.getByRole("radio", { name: "실패" })).toBeChecked();
    await expect(canvas.queryByRole("table")).toBeNull();
  },
};

/**
 * 처음 불러오는 중. 0.3초가 지나면 넓은 폭에서는 표 머리와 뼈대 행 넷이, 좁은 폭에서는 진행 표시 하나가 선다. 뼈대는 화면
 * 읽기 프로그램에서 숨는다. play 가 그것이 서기를 기다려 사진에 담긴다.
 */
export const Loading: Story = {
  args: { data: undefined, isValidating: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const live = within(canvas.getByRole("region", { name: "대화" })).getByRole("status");
    await waitFor(async () => {
      await expect(live).toHaveTextContent("대화 목록을 불러오는 중");
    });
    const bones = await canvas.findByRole("table", { hidden: true });
    await expect(bones).toHaveAttribute("aria-hidden", "true");
    if (isWideProject()) {
      await expect(bones).toBeVisible();
      await expect(canvas.queryByRole("progressbar")).toBeNull();
      await expect(within(bones).getAllByRole("row", { hidden: true }).slice(1)).toHaveLength(4);
    } else {
      await expect(
        canvas.getByRole("progressbar", { name: "대화 목록을 불러오는 중" }),
      ).toBeVisible();
      await expect(bones).not.toBeVisible();
    }
  },
};
