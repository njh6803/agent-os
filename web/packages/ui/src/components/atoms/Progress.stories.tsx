import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
import { semanticColor } from "../../storybook/expect";
import { Progress } from "./Progress";

const meta = {
  title: "atoms/Progress",
  component: Progress,
  args: { label: "3단계 중 2단계" },
} satisfies Meta<typeof Progress>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 진행 표시의 트랙과 막대. 트랙은 progressbar 의 마지막 자식이고 막대는 그 안의 하나다. */
function partsOf(progressbar: HTMLElement): { track: Element; bar: Element } {
  const track = progressbar.lastElementChild;
  const bar = track?.firstElementChild;
  if (track === null || bar === null || bar === undefined) {
    throw new Error("진행 표시에 트랙과 막대가 없다");
  }
  return { track, bar };
}

export const Determinate: Story = {
  name: "값이 있으면 label 이 이름이고 aria-valuenow·aria-valuemax 가 있으며 막대가 그 비율만큼 accent 로 찬다",
  args: { value: 2, max: 3 },
  play: async ({ canvas }) => {
    const progressbar = canvas.getByRole("progressbar", { name: "3단계 중 2단계" });
    await expect(canvas.getByText("3단계 중 2단계")).toBeVisible();
    await expect({
      now: progressbar.getAttribute("aria-valuenow"),
      max: progressbar.getAttribute("aria-valuemax"),
    }).toEqual({ now: "2", max: "3" });
    const { track, bar } = partsOf(progressbar);
    const trackStyle = getComputedStyle(track);
    await expect({ height: trackStyle.height, background: trackStyle.backgroundColor }).toEqual({
      height: "6px",
      background: semanticColor(track, "tint"),
    });
    await expect(getComputedStyle(bar).backgroundColor).toBe(semanticColor(bar, "accent"));
    const ratio = bar.getBoundingClientRect().width / track.getBoundingClientRect().width;
    await expect(Math.abs(ratio - 2 / 3)).toBeLessThan(0.01);
    await expect(getComputedStyle(bar).animationName).toBe("none");
  },
};

export const DeterminateDanger: Story = {
  name: "실패 톤의 막대는 danger 로 차고 max 가 없으면 끝 값이 1 이다",
  args: { value: 0.5, label: "2단계에서 실패", tone: "danger" },
  play: async ({ canvas }) => {
    const progressbar = canvas.getByRole("progressbar", { name: "2단계에서 실패" });
    await expect({
      now: progressbar.getAttribute("aria-valuenow"),
      max: progressbar.getAttribute("aria-valuemax"),
    }).toEqual({ now: "0.5", max: "1" });
    const { track, bar } = partsOf(progressbar);
    await expect(getComputedStyle(bar).backgroundColor).toBe(semanticColor(bar, "danger"));
    const ratio = bar.getBoundingClientRect().width / track.getBoundingClientRect().width;
    await expect(Math.abs(ratio - 0.5)).toBeLessThan(0.01);
  },
};

export const Indeterminate: Story = {
  name: "값을 모르면 aria-valuenow 가 없고 막대가 progress 움직임으로 옮겨 다닌다",
  // value 를 넘기지 않는다. 기본값이 null(값 모름)이다(디자인 파일 05절의 props 표).
  args: { label: "단계를 세는 중" },
  play: async ({ canvas }) => {
    const progressbar = canvas.getByRole("progressbar", { name: "단계를 세는 중" });
    await expect({
      hasNow: progressbar.hasAttribute("aria-valuenow"),
      max: progressbar.getAttribute("aria-valuemax"),
    }).toEqual({ hasNow: false, max: "1" });
    const { bar } = partsOf(progressbar);
    const style = getComputedStyle(bar);
    await expect({ animation: style.animationName, background: style.backgroundColor }).toEqual({
      animation: "progress",
      background: semanticColor(bar, "accent"),
    });
  },
};

export const IndeterminateDanger: Story = {
  name: "값을 모르는 실패 톤의 막대도 danger 로 옮겨 다닌다",
  args: { value: null, label: "멈춘 단계를 찾는 중", tone: "danger" },
  play: async ({ canvas }) => {
    const progressbar = canvas.getByRole("progressbar", { name: "멈춘 단계를 찾는 중" });
    await expect(progressbar.hasAttribute("aria-valuenow")).toBe(false);
    const { bar } = partsOf(progressbar);
    const style = getComputedStyle(bar);
    await expect({ animation: style.animationName, background: style.backgroundColor }).toEqual({
      animation: "progress",
      background: semanticColor(bar, "danger"),
    });
  },
};

export const OutOfRange: Story = {
  name: "끝 값을 넘는 값은 끝 값으로, 음수 값과 max 가 0 이하인 값은 0 으로 잘라 aria 값과 막대가 같은 범위를 보인다",
  render: (args) => (
    <div className="flex flex-col gap-4">
      <Progress {...args} label="넘친 값" value={5} max={3} />
      <Progress {...args} label="음수 값" value={-1} max={3} />
      <Progress {...args} label="끝 값 0" value={1} max={0} />
      <Progress {...args} label="끝 값 음수" value={1} max={-2} />
    </div>
  ),
  play: async ({ canvas }) => {
    const over = canvas.getByRole("progressbar", { name: "넘친 값" });
    const below = canvas.getByRole("progressbar", { name: "음수 값" });
    const zero = canvas.getByRole("progressbar", { name: "끝 값 0" });
    const negative = canvas.getByRole("progressbar", { name: "끝 값 음수" });
    const ratio = (progressbar: HTMLElement): number => {
      const { track, bar } = partsOf(progressbar);
      return bar.getBoundingClientRect().width / track.getBoundingClientRect().width;
    };
    await expect({
      overNow: over.getAttribute("aria-valuenow"),
      overRatio: ratio(over),
      belowNow: below.getAttribute("aria-valuenow"),
      belowRatio: ratio(below),
      zeroNow: zero.getAttribute("aria-valuenow"),
      zeroRatio: ratio(zero),
      negativeNow: negative.getAttribute("aria-valuenow"),
      negativeMax: negative.getAttribute("aria-valuemax"),
      negativeRatio: ratio(negative),
    }).toEqual({
      overNow: "3",
      overRatio: 1,
      belowNow: "0",
      belowRatio: 0,
      zeroNow: "0",
      zeroRatio: 0,
      // max 가 0 이하이면 범위는 0 부터 0 까지다. 최대가 최소(0)보다 작게 나가지 않는다.
      negativeNow: "0",
      negativeMax: "0",
      negativeRatio: 0,
    });
  },
};

export const DeterminateDark: Story = {
  name: "다크 모드에서도 트랙은 tint, 막대는 accent 다",
  args: { value: 2, max: 3 },
  globals: { mode: "dark" },
  play: async ({ canvas }) => {
    await expect(getComputedStyle(document.documentElement).colorScheme).toBe("dark");
    const { track, bar } = partsOf(canvas.getByRole("progressbar", { name: "3단계 중 2단계" }));
    await expect({
      track: getComputedStyle(track).backgroundColor,
      bar: getComputedStyle(bar).backgroundColor,
    }).toEqual({ track: semanticColor(track, "tint"), bar: semanticColor(bar, "accent") });
  },
};
