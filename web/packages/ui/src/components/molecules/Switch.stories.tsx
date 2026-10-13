import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn } from "storybook/test";
import {
  TRANSPARENT,
  colorsOf,
  expectedFocusRing,
  focusRingOf,
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
  /** 올림에서 트랙 위에 겹치는 면. 트랙 바로 뒤에 있다. */
  overlay: HTMLElement;
  /** 트랙과 겹치는 면 위의 손잡이. 트랙을 감싼 요소의 마지막 자식이다. */
  knob: HTMLElement;
  /** 라벨 아래의 상태 글(켜짐·꺼짐). */
  stateText: HTMLElement;
  /** 누르는 곳인 라벨 전체. */
  row: HTMLLabelElement;
}

function partsOf(track: HTMLElement): Parts {
  const overlay = track.nextElementSibling;
  const knob = track.parentElement?.lastElementChild;
  const row = track.closest("label");
  const stateText = row === null ? null : stateTextOf(row);
  if (
    !(track instanceof HTMLInputElement) ||
    !(overlay instanceof HTMLElement) ||
    !(knob instanceof HTMLElement) ||
    overlay === knob ||
    row === null ||
    stateText === null
  ) {
    throw new Error("스위치의 트랙, 겹치는 면, 손잡이, 라벨, 상태 글이 없다");
  }
  return { track, overlay, knob, stateText, row };
}

function stateTextOf(row: HTMLLabelElement): HTMLElement | null {
  return (
    Array.from(row.querySelectorAll("span")).find(
      (span) => span.textContent === "켜짐" || span.textContent === "꺼짐",
    ) ?? null
  );
}

/**
 * 상태마다 맞댈 계산값. 트랙의 바탕, 겹치는 면의 바탕, 손잡이의 바탕, 라벨과 상태 글의 색이다. 겹치는 면은 라벨이
 * `:hover` 일 때만 칠해진다(`hoverAwareColor` 의 까닭과 같이, 스토리 테스트의 포인터가 라벨 위에 머물 수 있다).
 */
function switchColors({ track, overlay, knob, stateText, row }: Parts) {
  return {
    track: colorsOf(track).background,
    overlay: colorsOf(overlay).background,
    knob: getComputedStyle(knob).backgroundColor,
    label: getComputedStyle(row).color,
    state: getComputedStyle(stateText).color,
  };
}

/** 겹치는 면의 기대 색. 라벨이 `:hover` 면 `bg-active`, 아니면 투명이다. */
function expectedOverlay({ overlay, row }: Parts): string {
  return row.matches(":hover") ? semanticColor(overlay, "bg-active") : TRANSPARENT;
}

export const Off: Story = {
  name: "꺼진 스위치는 border-control 트랙에 bg-raised 손잡이이고 상태 글이 꺼짐이며 누르면 onChange 가 true 를 받고 넘긴 꺼짐에 남는다",
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
      track: semanticColor(track, "border-control"),
      overlay: expectedOverlay(parts),
      knob: semanticColor(track, "bg-raised"),
      label: semanticColor(track, "text"),
      state: semanticColor(track, "text-muted"),
    });
    // 트랙 40×24px 의 둥근 면에 손잡이 20px 이 왼쪽 위에서 2px 띄워 놓이고, 글자와 트랙 사이는 8px 이다.
    const trackBox = track.getBoundingClientRect();
    const knobBox = knob.getBoundingClientRect();
    await expect({
      track: [trackBox.width, trackBox.height],
      knob: [knobBox.width, knobBox.height],
      left: knobBox.left - trackBox.left,
      top: knobBox.top - trackBox.top,
      radius: getComputedStyle(track).borderTopLeftRadius,
      gap: getComputedStyle(row).columnGap,
    }).toEqual({ track: [40, 24], knob: [20, 20], left: 2, top: 2, radius: "999px", gap: "8px" });
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
      track: semanticColor(track, "accent"),
      overlay: expectedOverlay(parts),
      knob: semanticColor(track, "on-accent"),
    });
    // 손잡이는 오른쪽에서 2px 이다.
    await expect(track.getBoundingClientRect().right - knob.getBoundingClientRect().right).toBe(2);
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
    await expect(colorsOf(track).background).toBe(semanticColor(track, "accent"));
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
  name: "쓸 수 없는 스위치는 눌러도 바뀌지 않고 bg-disabled 트랙, text-disabled 손잡이와 글자이며 겹치는 면이 투명하다",
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
      const disabledText = semanticColor(track, "text-disabled");
      await expect(track.disabled).toBe(true);
      await expect(switchColors(parts)).toEqual({
        track: semanticColor(track, "bg-disabled"),
        overlay: TRANSPARENT,
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

// `text-disabled` 는 라이트에서 `border-control` 과 같은 값이라 다크에서도 잰다.
export const DisabledDark: Story = {
  ...Disabled,
  name: "다크 모드의 쓸 수 없는 스위치도 bg-disabled 트랙, text-disabled 손잡이와 글자다",
  globals: { mode: "dark" },
};

// 꺼짐의 손잡이(`bg-raised`)와 켜짐의 손잡이(`on-accent`)는 라이트 넷에서 같은 값이라 다크에서 가른다.
export const BothDark: Story = {
  name: "다크 모드의 꺼진 스위치는 border-control 트랙에 bg-raised 손잡이, 켜진 스위치는 accent 트랙에 on-accent 손잡이다",
  globals: { mode: "dark" },
  render: (args) => (
    <div className="flex flex-col">
      <Switch {...args} checked={false} />
      <Switch {...args} label="주문 조회" checked />
    </div>
  ),
  play: async ({ canvas }) => {
    const off = partsOf(canvas.getByRole("switch", { name: "결제 환불" }));
    const on = partsOf(canvas.getByRole("switch", { name: "주문 조회" }));
    await expect(getComputedStyle(document.documentElement).colorScheme).toBe("dark");
    await expect(switchColors(off)).toMatchObject({
      track: semanticColor(off.track, "border-control"),
      knob: semanticColor(off.track, "bg-raised"),
    });
    await expect(switchColors(on)).toMatchObject({
      track: semanticColor(on.track, "accent"),
      knob: semanticColor(on.track, "on-accent"),
    });
  },
};

// 녹청에서 `focus-ring` 은 `accent`(켜진 트랙)와 같은 값이라 그 둘은 가르지 못하지만 `border-control`·`text` 와는 가른다.
export const Focus: Story = {
  name: "Tab 으로 포커스하면 트랙 바깥에 focus-ring 색의 2px 실선이 2px 떨어져 그려진다",
  args: { checked: true },
  play: async ({ canvas, userEvent }) => {
    const track = canvas.getByRole("switch", { name: "결제 환불" });
    await userEvent.tab();
    await expect(document.activeElement).toBe(track);
    await expect(focusRingOf(track)).toEqual(expectedFocusRing(track));
  },
};

/** 보여 주기용(`showcase`). 플러그인 목록의 줄마다 놓인 스위치다. 줄마다 플러그인 하나를 켜고 끈다. */
export const ShowcasePluginRows: Story = {
  name: "쓰임: 플러그인 줄의 스위치",
  tags: ["showcase"],
  render: () => (
    <div className="flex flex-col gap-3" style={{ width: 320 }}>
      <Switch label="calc" checked onChange={() => {}} />
      <Switch label="support-bot" checked={false} onChange={() => {}} />
      <Switch label="filesystem" checked disabled />
    </div>
  ),
};
