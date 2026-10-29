// 실행 목록(admin-style 티켓 06, 화면 디자인 mk-runs, mk-runs-dark, mk-runs-m, mk-runs-empty, mk-runs-loading). 틀 없이
// 그리고, 미리보기의 데코레이터가 본문 칸과 같은 컨테이너를 두른다. 넓은 폭(admin-storybook-wide)에서는 표, 좁은 폭
// (admin-storybook-narrow)에서는 실행마다 카드다. 그 갈래는 사진만이 아니라 위치와 역할로 본다. 사진만 보면 처음 정답을
// 만들 때 넓은 폭에서 좁은 갈래가 그려져도 그대로 정답이 된다.
//
// 표본 값은 그림의 것이고 첫 행의 주체는 실행 하나 화면과 같은 operator 다. 읽을 수 없는 행만 그림과 다르다. 그림은 그
// 행에 실행 식별자 링크를 그리지 않아(명세는 링크를 둔다) 식별자를 지어 넣었고, 이유도 그 식별자의 파일 경로로 적었다.
// 시각은 그림의 Asia/Seoul 글자가 나오는 UTC 값이다. 스토리 테스트의 브라우저 시간대는 고정되지 않아 play 는 시각 글자를 단언하지 않는다. 사진은 Asia/Seoul 로
// 찍힌다(visual/playwright.config.ts). 거르기와 더 보기를 누르는 행동, 시각을 바꾸는 규칙은 페이지 시험
// (pages/RunsPage.test)이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, waitFor, within } from "storybook/test";
import type { RunRow, RunSummary, TracePage } from "../../api/traces";
import { RunList } from "./RunList";

/** 문서 뿌리에 선언된 디자인 토큰의 값. */
function rootToken(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/**
 * 넓은 폭의 프로젝트인가. 두 프로젝트의 창은 1280 과 320 이라 화면 중단점 `wide` 로 가른다. 기대는 프로젝트에서 고르고
 * 보이는 갈래는 그림에서 읽어, 컨테이너가 빠지거나 기준 폭이 어긋나면 둘이 갈린다.
 */
function isWideProject(): boolean {
  return window.matchMedia(`(min-width: ${rootToken("--breakpoint-wide")})`).matches;
}

function summary(
  runId: string,
  status: RunSummary["status"],
  agent: string,
  principal: string,
  startedAt: string,
  lastAt: string,
): RunSummary {
  return {
    run_id: runId,
    status,
    schema_version: "3",
    started_at: startedAt,
    last_at: lastAt,
    agent,
    principal,
  };
}

/** 그림 mk-runs 의 행. 다섯째가 읽을 수 없는 트레이스다. */
const ROWS: readonly RunRow[] = [
  summary(
    "7f3a2c91-4b8e-4d1a-9c2f-0e6b5a8d3f12",
    "paused",
    "support-bot",
    "operator",
    "2026-10-12T05:03:22+00:00",
    "2026-10-12T05:03:25+00:00",
  ),
  summary(
    "0b9e5d14-2a7c-4f3e-8d61-c4a2b9e07f5d",
    "finished",
    "calc",
    "operator",
    "2026-10-12T04:58:07+00:00",
    "2026-10-12T04:58:11+00:00",
  ),
  summary(
    "c51f8a07-9d3b-4e2a-b6f4-17e8d0c3a92b",
    "failed",
    "support-bot",
    "operator",
    "2026-10-12T04:41:50+00:00",
    "2026-10-12T04:42:31+00:00",
  ),
  summary(
    "5d27e3b0-6c1f-4a8d-93e5-b8f0a4c6d211",
    "unfinished",
    "calc",
    "operator",
    "2026-10-12T02:20:03+00:00",
    "2026-10-12T02:20:04+00:00",
  ),
  {
    run_id: "9a0c6e12-7b3d-4f1a-8e25-c6d4b0a9f371",
    reason: "traces/9a0c6e12-7b3d-4f1a-8e25-c6d4b0a9f371.jsonl: 첫 줄의 형식 버전이 없다",
  },
  summary(
    "e8a4b2f6-1d9c-4b7e-a053-6f2c8e1d4b90",
    "finished",
    "support-bot",
    "https://shop.example|user-17",
    "2026-10-11T09:12:45+00:00",
    "2026-10-11T09:12:52+00:00",
  ),
  summary(
    "2f6d9b13-8e4a-4c5f-b712-d3a9e6f0c845",
    "paused",
    "calc",
    "operator",
    "2026-10-11T00:30:16+00:00",
    "2026-10-11T00:30:19+00:00",
  ),
];

const NEXT_PAGE: readonly TracePage[] = [{ runs: [...ROWS], next_cursor: "cur-2" }];

const meta = {
  title: "organisms/RunList",
  component: RunList,
  args: {
    data: NEXT_PAGE,
    error: undefined,
    isValidating: false,
    onRefresh: fn(),
    status: null,
    onStatusChange: fn(),
    onMore: fn(),
  },
} satisfies Meta<typeof RunList>;

export default meta;
type Story = StoryObj<typeof meta>;

/**
 * 다음 쪽이 있는 목록. 다섯째 행은 읽을 수 없는 트레이스다. 넓은 폭에서는 표이고 열 머리는 `<th scope="col">`, 행 높이는
 * `h-row` 다. 좁은 폭에서는 실행마다 카드다. 실행 식별자 링크의 포인터 목표는 24px 이상이다.
 */
export const List: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const region = within(canvas.getByRole("region", { name: "실행" }));
    await expect(canvas.getByRole("heading", { level: 1 })).toHaveTextContent(/^실행$/);
    // 역할 조회는 숨은 갈래를 넘는다. 글자 조회는 넘지 않아 보이는 갈래 안에서 한다.
    let shown: HTMLElement;
    if (isWideProject()) {
      shown = region.getByRole("table");
      await expect(region.queryByRole("list")).toBeNull();
      const headers = within(shown).getAllByRole("columnheader");
      await expect(headers.map((header) => header.textContent)).toEqual([
        "상태",
        "실행",
        "에이전트",
        "주체",
        "시작",
        "마지막",
      ]);
      const [, first] = within(shown).getAllByRole("row");
      await expect(first?.getBoundingClientRect().height).toBe(
        Number.parseFloat(rootToken("--row-h")),
      );
    } else {
      shown = region.getByRole("list");
      await expect(region.queryByRole("table")).toBeNull();
      await expect(within(shown).getAllByRole("listitem")).toHaveLength(ROWS.length);
      // 라벨 칸은 가장 긴 라벨의 폭이라, 긴 주체가 든 카드에서도 값이 다른 카드와 같은 자리에서 시작한다.
      const valueStarts = within(shown)
        .getAllByRole("definition")
        .map((value) => value.getBoundingClientRect().left);
      await expect(new Set(valueStarts).size).toBe(1);
    }
    await expect(shown).toBeVisible();
    const links = region.getAllByRole("link");
    await expect(links.map((link) => link.textContent)).toEqual(ROWS.map((row) => row.run_id));
    for (const link of links) {
      await expect(link.getBoundingClientRect().height).toBeGreaterThanOrEqual(24);
    }
    await expect(
      within(shown).getByText(
        "읽을 수 없는 트레이스: traces/9a0c6e12-7b3d-4f1a-8e25-c6d4b0a9f371.jsonl: 첫 줄의 형식 버전이 없다",
      ),
    ).toBeVisible();
    await expect(canvas.getByRole("button", { name: "더 보기" })).toBeVisible();
  },
};

/** 실패로 거른 목록이 비었다. 그 상태의 배지 아이콘(20)과 한 줄이고, "전부 보기"는 없으며 거르기는 남는다. */
export const FilteredEmpty: Story = {
  args: { status: "failed", data: [{ runs: [], next_cursor: null }] },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const line = canvas.getByText("실패한 실행이 없다");
    await expect(line).toBeVisible();
    const icon = line.querySelector("svg");
    await expect(icon?.getBoundingClientRect().width).toBe(
      Number.parseFloat(rootToken("--spacing-icon-m")),
    );
    await expect(canvas.queryByRole("button", { name: "전부 보기" })).toBeNull();
    await expect(canvas.getByRole("radio", { name: "실패" })).toBeChecked();
    await expect(canvas.queryByRole("table")).toBeNull();
  },
};

/**
 * 처음 불러오는 중. 0.3초가 지나면 넓은 폭에서는 표 머리와 뼈대 행 넷(진짜 행과 같은 높이)이, 좁은 폭에서는 진행 표시
 * 하나가 선다. 뼈대는 화면 읽기 프로그램에서 숨는다. play 가 그것이 서기를 기다려 사진에 담긴다.
 */
export const Loading: Story = {
  args: { data: undefined, isValidating: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const live = within(canvas.getByRole("region", { name: "실행" })).getByRole("status");
    await waitFor(async () => {
      await expect(live).toHaveTextContent("실행 목록을 불러오는 중");
    });
    const bones = await canvas.findByRole("table", { hidden: true });
    await expect(bones).toHaveAttribute("aria-hidden", "true");
    if (isWideProject()) {
      await expect(bones).toBeVisible();
      await expect(canvas.queryByRole("progressbar")).toBeNull();
      const rows = within(bones).getAllByRole("row", { hidden: true }).slice(1);
      await expect(rows).toHaveLength(4);
      for (const bone of rows) {
        await expect(bone.getBoundingClientRect().height).toBe(
          Number.parseFloat(rootToken("--row-h")),
        );
      }
    } else {
      await expect(
        canvas.getByRole("progressbar", { name: "실행 목록을 불러오는 중" }),
      ).toBeVisible();
      await expect(bones).not.toBeVisible();
    }
  },
};
