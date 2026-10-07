import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn } from "storybook/test";
import {
  colorsOf,
  expectedFocusRing,
  focusRingOf,
  hoverAwareColor,
  semanticColor,
} from "../../storybook/expect";
import { Switch } from "./Switch";

const meta = {
  title: "molecules/Switch",
  component: Switch,
  args: { label: "결제 환불", onChange: fn() },
} satisfies Meta<typeof Switch>;

export default meta;
type Story = StoryObj<typeof meta>;

interface Parts {
  /** `role="switch"` 인 입력 요소. 트랙으로 그린다. */
  track: HTMLInputElement;
  /** 트랙 위의 손잡이. */
  knob: HTMLElement;
  /** 라벨 아래의 상태 글(켜짐·꺼짐). */
  stateText: HTMLElement;
  /** 누르는 곳인 라벨 전체. */
  row: HTMLLabelElement;
}

function partsOf(track: HTMLElement): Parts {
  const knob = track.nextElementSibling;
  const row = track.closest("label");
  const stateText = row === null ? null : stateTextOf(row);
  if (
    !(track instanceof HTMLInputElement) ||
    !(knob instanceof HTMLElement) ||
    row === null ||
    stateText === null
  ) {
    throw new Error("스위치의 트랙, 손잡이, 라벨, 상태 글이 없다");
  }
  return { track, knob, stateText, row };
}

function stateTextOf(row: HTMLLabelElement): HTMLElement | null {
  return (
    Array.from(row.querySelectorAll("span")).find(
      (span) => span.textContent === "켜짐" || span.textContent === "꺼짐",
    ) ?? null
  );
}

/** 상태마다 맞댈 계산값. 트랙의 바탕과 테두리, 손잡이의 바탕, 라벨과 상태 글의 색이다. */
function switchColors({ track, knob, stateText, row }: Parts) {
  return {
    track: colorsOf(track).background,
    border: colorsOf(track).border,
    knob: getComputedStyle(knob).backgroundColor,
    label: getComputedStyle(row).color,
    state: getComputedStyle(stateText).color,
  };
}

export const Off: Story = {
  name: "꺼진 스위치는 raised 트랙에 border 테두리와 muted 손잡이이고 상태 글이 꺼짐이며 누르면 onChange 가 true 를 받고 넘긴 꺼짐에 남는다",
  args: { checked: false },
  play: async ({ args, canvas, userEvent }) => {
    const parts = partsOf(canvas.getByRole("switch", { name: "결제 환불" }));
    const { track, knob, stateText, row } = parts;
    await expect({
      type: track.type,
      checked: track.checked,
      state: stateText.textContent,
    }).toEqual({
      type: "checkbox",
      checked: false,
      state: "꺼짐",
    });
    await expect(switchColors(parts)).toEqual({
      track: semanticColor(track, "raised"),
      border: hoverAwareColor(row, "border", "border-hover"),
      knob: semanticColor(track, "muted"),
      label: semanticColor(track, "text"),
      state: semanticColor(track, "muted"),
    });
    // 트랙 36×20px, 손잡이 12px 이 왼쪽에서 4px, 누르는 곳(라벨 전체)은 높이 48px 이상이다.
    const trackBox = track.getBoundingClientRect();
    const knobBox = knob.getBoundingClientRect();
    await expect({
      track: [trackBox.width, trackBox.height],
      knob: [knobBox.width, knobBox.height],
      left: knobBox.left - trackBox.left,
      top: knobBox.top - trackBox.top,
    }).toEqual({ track: [36, 20], knob: [12, 12], left: 4, top: 4 });
    await expect(row.getBoundingClientRect().height).toBeGreaterThanOrEqual(48);
    // 상태 글은 checked 와 같은 뜻이라 화면 읽기 프로그램에서 숨는다. 이름은 라벨 하나다.
    await expect(stateText.closest("[aria-hidden=true]")).not.toBeNull();
    await userEvent.click(track);
    await expect(args.onChange).toHaveBeenCalledOnce();
    await expect(args.onChange).toHaveBeenCalledWith(true);
    // checked 를 넘겼으면 넘긴 값에 남는다. 바꾸는 것도, 바꾸지 못해 되돌리는 것도 쓰는 쪽이다.
    await expect({ checked: track.checked, state: stateText.textContent }).toEqual({
      checked: false,
      state: "꺼짐",
    });
  },
};

export const On: Story = {
  name: "켜진 스위치는 accent 트랙에 on-accent 손잡이이고 상태 글이 켜짐이며 누르면 onChange 가 false 를 받고 넘긴 켜짐에 남는다",
  args: { checked: true, label: "주문 조회" },
  play: async ({ args, canvas, userEvent }) => {
    const parts = partsOf(canvas.getByRole("switch", { name: "주문 조회" }));
    const { track, knob, stateText } = parts;
    await expect({ checked: track.checked, state: stateText.textContent }).toEqual({
      checked: true,
      state: "켜짐",
    });
    await expect(switchColors(parts)).toMatchObject({
      track: hoverAwareColor(parts.row, "accent", "accent-hover"),
      border: hoverAwareColor(parts.row, "accent", "accent-hover"),
      knob: semanticColor(track, "on-accent"),
    });
    // 손잡이는 오른쪽에서 4px 이다.
    await expect(track.getBoundingClientRect().right - knob.getBoundingClientRect().right).toBe(4);
    await userEvent.click(track);
    await expect(args.onChange).toHaveBeenCalledOnce();
    await expect(args.onChange).toHaveBeenCalledWith(false);
    await expect({ checked: track.checked, state: stateText.textContent }).toEqual({
      checked: true,
      state: "켜짐",
    });
  },
};

export const Toggle: Story = {
  name: "라벨 글자를 누르면 켜지고 다시 누르면 꺼지며 onChange 가 새 값을 받는다",
  play: async ({ args, canvas, userEvent }) => {
    const track = canvas.getByRole("switch", { name: "결제 환불" });
    const parts = partsOf(track);
    await userEvent.click(canvas.getByText("결제 환불"));
    await expect({
      checked: parts.track.checked,
      state: stateTextOf(parts.row)?.textContent,
    }).toEqual({
      checked: true,
      state: "켜짐",
    });
    await expect(args.onChange).toHaveBeenLastCalledWith(true);
    await expect(colorsOf(track).background).toBe(
      hoverAwareColor(parts.row, "accent", "accent-hover"),
    );
    await userEvent.click(canvas.getByText("켜짐"));
    await expect({
      checked: parts.track.checked,
      state: stateTextOf(parts.row)?.textContent,
    }).toEqual({
      checked: false,
      state: "꺼짐",
    });
    await expect(args.onChange).toHaveBeenLastCalledWith(false);
    await expect(args.onChange).toHaveBeenCalledTimes(2);
  },
};

export const Disabled: Story = {
  name: "쓸 수 없는 스위치는 눌러도 바뀌지 않고 disabled-surface 트랙과 divider 테두리, disabled-text 손잡이와 글자다",
  render: (args) => (
    <div className="flex flex-col">
      <Switch {...args} disabled />
      <Switch {...args} label="주문 조회" checked disabled />
    </div>
  ),
  play: async ({ args, canvas, userEvent }) => {
    for (const [name, checked] of [
      ["결제 환불", false],
      ["주문 조회", true],
    ] as const) {
      const parts = partsOf(canvas.getByRole("switch", { name }));
      const { track } = parts;
      const disabledText = semanticColor(track, "disabled-text");
      await expect(track.disabled).toBe(true);
      await expect(switchColors(parts)).toEqual({
        track: semanticColor(track, "disabled-surface"),
        border: semanticColor(track, "divider"),
        knob: disabledText,
        label: disabledText,
        state: disabledText,
      });
      await userEvent.click(parts.row);
      await expect(track.checked).toBe(checked);
    }
    await expect(args.onChange).not.toHaveBeenCalled();
  },
};

export const OnDark: Story = {
  name: "다크 모드의 켜진 스위치도 accent 트랙에 on-accent 손잡이다",
  args: { checked: true, label: "주문 조회" },
  globals: { mode: "dark" },
  play: async ({ canvas }) => {
    const parts = partsOf(canvas.getByRole("switch", { name: "주문 조회" }));
    await expect(getComputedStyle(document.documentElement).colorScheme).toBe("dark");
    await expect(switchColors(parts)).toMatchObject({
      track: hoverAwareColor(parts.row, "accent", "accent-hover"),
      knob: semanticColor(parts.track, "on-accent"),
    });
  },
};

// 공문에서 잰다. 먹은 focus 와 accent 가 같은 색이다. 기본 테마가 아닌 테마에서 값을 재는 판정 스토리라 사진에서
// 뺀다(사진은 기본 테마만 찍는다, ADR 0026 의 2026-10-06 이력).
export const Focus: Story = {
  name: "Tab 으로 포커스하면 트랙 바깥에 focus 색의 실선 테두리가 그려진다",
  tags: ["judgment"],
  args: { checked: true },
  globals: { theme: "gongmun" },
  play: async ({ canvas, userEvent }) => {
    const track = canvas.getByRole("switch", { name: "결제 환불" });
    await userEvent.tab();
    await expect(document.activeElement).toBe(track);
    await expect(focusRingOf(track)).toEqual(expectedFocusRing(track));
  },
};
