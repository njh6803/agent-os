import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
import { SCREEN_STROKE, semanticColor, strokesOf } from "../../storybook/expect";
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
  name: "값이 있으면 label 이 text-muted 의 이름이고 aria-valuenow·aria-valuemax 가 있으며 높이 4px 의 둥근 bg-active 트랙에 막대가 그 비율만큼 text-muted 로 찬다",
  args: { value: 2, max: 3 },
  play: async ({ canvas }) => {
    const progressbar = canvas.getByRole("progressbar", { name: "3단계 중 2단계" });
    const name = canvas.getByText("3단계 중 2단계");
    await expect(name).toBeVisible();
    await expect(getComputedStyle(name).color).toBe(semanticColor(name, "text-muted"));
    await expect({
      now: progressbar.getAttribute("aria-valuenow"),
      max: progressbar.getAttribute("aria-valuemax"),
    }).toEqual({ now: "2", max: "3" });
    const { track, bar } = partsOf(progressbar);
    const trackStyle = getComputedStyle(track);
    await expect({
      height: trackStyle.height,
      radius: trackStyle.borderTopLeftRadius,
      background: trackStyle.backgroundColor,
    }).toEqual({
      height: "4px",
      radius: "999px",
      background: semanticColor(track, "bg-active"),
    });
    await expect(getComputedStyle(bar).backgroundColor).toBe(semanticColor(bar, "text-muted"));
    const ratio = bar.getBoundingClientRect().width / track.getBoundingClientRect().width;
    await expect(Math.abs(ratio - 2 / 3)).toBeLessThan(0.01);
    await expect(getComputedStyle(bar).animationName).toBe("none");
  },
};

export const Indeterminate: Story = {
  name: "값을 모르면 aria-valuenow 가 없고 트랙 대신 한 바퀴 0.8초로 도는 text-muted 의 16px 표시와 이름을 8px 사이로 보인다",
  // value 를 넘기지 않는다. 기본값이 null(값 모름)이다.
  args: { label: "단계를 세는 중" },
  play: async ({ canvas }) => {
    const progressbar = canvas.getByRole("progressbar", { name: "단계를 세는 중" });
    await expect({
      hasNow: progressbar.hasAttribute("aria-valuenow"),
      max: progressbar.getAttribute("aria-valuemax"),
    }).toEqual({ hasNow: false, max: "1" });
    // 도는 표시가 먼저, 이름이 나중이고 트랙은 없다.
    await expect(Array.from(progressbar.children, (child) => child.tagName.toLowerCase())).toEqual([
      "svg",
      "span",
    ]);
    const [spinner, name] = progressbar.children;
    if (spinner === undefined || name === undefined) {
      throw new Error("도는 표시와 이름이 없다");
    }
    await expect(name.textContent).toBe("단계를 세는 중");
    await expect(canvas.getByText("단계를 세는 중")).toBeVisible();
    await expect(getComputedStyle(name).color).toBe(semanticColor(name, "text-muted"));
    const style = getComputedStyle(spinner);
    await expect({
      width: style.width,
      color: style.color,
      animation: style.animationName,
      duration: style.animationDuration,
    }).toEqual({
      width: "16px",
      color: semanticColor(spinner, "text-muted"),
      animation: "spin",
      duration: "0.8s",
    });
    const strokes = strokesOf(spinner);
    await expect(strokes).toEqual(strokes.map(() => SCREEN_STROKE));
    // 도는 표시의 getBoundingClientRect 는 회전한 상자의 외접 사각형이라 각도마다 달라진다. 회전과 무관한 이름의 자리로
    // 잰다. 이름은 progressbar 의 왼쪽에서 도는 표시(16px)와 사이(8px)만큼 떨어진다.
    const offset = name.getBoundingClientRect().left - progressbar.getBoundingClientRect().left;
    await expect(offset).toBe(16 + 8);
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

// `bg-active` 는 라이트에서 `shadow-color` 와 같은 값이라 다크에서도 잰다.
export const DeterminateDark: Story = {
  name: "다크 모드에서도 트랙은 bg-active, 막대는 text-muted 다",
  args: { value: 2, max: 3 },
  globals: { mode: "dark" },
  play: async ({ canvas }) => {
    await expect(getComputedStyle(document.documentElement).colorScheme).toBe("dark");
    const { track, bar } = partsOf(canvas.getByRole("progressbar", { name: "3단계 중 2단계" }));
    await expect({
      track: getComputedStyle(track).backgroundColor,
      bar: getComputedStyle(bar).backgroundColor,
    }).toEqual({ track: semanticColor(track, "bg-active"), bar: semanticColor(bar, "text-muted") });
  },
};

/** 보여 주기용(`showcase`). 끝을 알면 막대이고, 모델의 응답처럼 끝을 모르면 도는 표시다. */
export const ShowcaseRunSteps: Story = {
  name: "쓰임: 단계를 아는 진행과 응답 기다리기",
  tags: ["showcase"],
  render: () => (
    <div className="flex flex-col gap-4" style={{ width: 320 }}>
      <Progress value={2} max={3} label="3단계 중 2단계" />
      <Progress value={null} label="모델의 응답을 기다립니다" />
    </div>
  ),
};
