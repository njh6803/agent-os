// 읽기 골격(ReadSection)의 공통 상태(admin-style 티켓 04, 명세 "화면 머리와 공통 상태"). 이미 보인 것을 다시 확인하는
// 중, 봉투로 실패한 것, 서버에 닿지 못한 것이다. 틀 없이 그리고, 미리보기의 데코레이터가 본문 칸과 같은 컨테이너를
// 두른다. 처음 불러오는 중의 0.3초 지연과 다시 읽다 실패하면 보인 것이 지워지는 행동은 페이지 시험이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import { RequestFailure } from "../../api/failure";
import { EmptyLine } from "../molecules/EmptyLine";
import { ReadSection } from "./ReadSection";

/** 조상 가운데 인라인 크기 컨테이너가 있는가. 없으면 컨테이너 기준 폭(`@split:`)의 갈래가 서지 않는다. */
function insideContainer(element: Element): boolean {
  for (let ancestor = element.parentElement; ancestor !== null; ancestor = ancestor.parentElement) {
    if (getComputedStyle(ancestor).containerType === "inline-size") {
      return true;
    }
  }
  return false;
}

interface RunsReadProps {
  readonly data: readonly string[] | undefined;
  readonly error: unknown;
  readonly isValidating: boolean;
  readonly onRefresh: () => void;
}

/** 실행 목록 자리의 읽기. 값은 이미 보인 빈 목록이다. */
function RunsRead(props: RunsReadProps) {
  return (
    <ReadSection
      {...props}
      title="실행"
      loadingLabel="실행 목록을 불러오는 중"
      failureTitle="실행 목록을 읽지 못했다"
    >
      {() => (
        <EmptyLine icon="list" iconSize="20">
          실행이 없다
        </EmptyLine>
      )}
    </ReadSection>
  );
}

const meta = {
  title: "organisms/ReadSection",
  component: RunsRead,
  args: { data: [], error: undefined, isValidating: false, onRefresh: fn() },
} satisfies Meta<typeof RunsRead>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 이미 보인 것을 다시 확인하는 중. "새로 고침"이 불러오는 중이고 머리 아래 진행 표시가 서며 보인 줄은 남는다. */
export const Refreshing: Story = {
  args: { isValidating: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("button", { name: "새로 고침" })).toHaveAttribute(
      "aria-busy",
      "true",
    );
    await expect(canvas.getByRole("progressbar", { name: "다시 확인하는 중" })).toBeVisible();
    await expect(canvas.getByText("실행이 없다")).toBeVisible();
    // 틀 없이 그려도 미리보기의 데코레이터가 본문 칸과 같은 컨테이너를 두른다.
    await expect(insideContainer(canvas.getByRole("region", { name: "실행" }))).toBe(true);
  },
};

/** 서버가 에러 봉투로 답했다. 위험 알림의 제목이 실패한 일이고 본문이 메시지와 고정폭 추적 식별자다. */
export const Failed: Story = {
  args: {
    data: undefined,
    error: new RequestFailure(500, {
      code: "internal_error",
      message: "운영자 파일이 깨졌다: C:/root/plugins/disabled.toml",
      request_id: "req-9f3c2a7e41b84d0c",
      violations: [],
    }),
  },
  play: async ({ canvasElement }) => {
    const alert = within(canvasElement).getByRole("alert");
    await expect(alert).toHaveTextContent("실행 목록을 읽지 못했다");
    await expect(alert).toHaveTextContent("운영자 파일이 깨졌다: C:/root/plugins/disabled.toml");
    await expect(alert).toHaveTextContent("추적 식별자: req-9f3c2a7e41b84d0c");
    await expect(within(alert).getByText("req-9f3c2a7e41b84d0c").tagName).toBe("CODE");
  },
};

/** 봉투 없이 실패했다. 추적 식별자 줄은 없다. */
export const Unreachable: Story = {
  args: { data: undefined, error: new RequestFailure(null, null) },
  play: async ({ canvasElement }) => {
    const alert = within(canvasElement).getByRole("alert");
    await expect(alert).toHaveTextContent("서버에 닿지 못했다");
    await expect(alert).not.toHaveTextContent("추적 식별자");
  },
};
