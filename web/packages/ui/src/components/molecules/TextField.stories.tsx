import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn } from "storybook/test";
import {
  colorsOf,
  expectedFocusRing,
  focusRingOf,
  hoverAwareColor,
  iconShape,
  semanticColor,
} from "../../storybook/expect";
import { TextField } from "./TextField";

const meta = {
  title: "molecules/TextField",
  component: TextField,
  args: { label: "플러그인 이름", placeholder: "예: 주문 조회", onChange: fn() },
} satisfies Meta<typeof TextField>;

export default meta;
type Story = StoryObj<typeof meta>;

type Control = HTMLInputElement | HTMLTextAreaElement;

/** 이어진 라벨의 글자로 칸을 찾는다. 접근 이름은 스토리가 getByRole 로 따로 본다. */
function fieldNamed(canvasElement: HTMLElement, name: string): Control {
  for (const field of canvasElement.querySelectorAll("input, textarea")) {
    if (
      (field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement) &&
      field.labels?.[0]?.textContent === name
    ) {
      return field;
    }
  }
  throw new Error(`라벨이 "${name}" 인 칸이 없다`);
}

/** 칸의 `aria-describedby` 가 가리키는 요소(도움말이나 오류). 없으면 null. */
function noteOf(field: Control): HTMLElement | null {
  const id = field.getAttribute("aria-describedby");
  return id === null ? null : document.getElementById(id);
}

// 기본 그림의 스토리(Single, Multi)는 글을 넣지 않는다. 글 칸은 어떻게 포커스되든 :focus-visible 이라 글을 넣고
// 끝나는 play 는 칸에 링을 남긴다. 글을 넣는 확인은 Typing 이 한다.
export const Single: Story = {
  name: "한 줄 글 입력은 라벨로 찾히는 높이 40px 의 칸이고 자리 글자는 라벨을 대신하지 않는다",
  play: async ({ canvas, canvasElement }) => {
    const input = canvas.getByLabelText("플러그인 이름");
    await expect(input).toBe(fieldNamed(canvasElement, "플러그인 이름"));
    await expect(input).toBe(canvas.getByRole("textbox", { name: "플러그인 이름" }));
    await expect({
      tag: input.tagName,
      type: input.getAttribute("type"),
      height: getComputedStyle(input).height,
      placeholder: input.getAttribute("placeholder"),
      invalid: input.getAttribute("aria-invalid"),
      note: input.getAttribute("aria-describedby"),
    }).toEqual({
      tag: "INPUT",
      type: "text",
      height: "40px",
      placeholder: "예: 주문 조회",
      invalid: null,
      note: null,
    });
    await expect(colorsOf(input)).toEqual({
      background: semanticColor(input, "raised"),
      text: semanticColor(input, "text"),
      border: hoverAwareColor(input, "border", "border-hover"),
    });
    await expect(getComputedStyle(input, "::placeholder").color).toBe(
      semanticColor(input, "muted"),
    );
    // 라벨은 칸 밖에 늘 보이는 글자이고 이름은 자리 글자가 아니라 라벨에서 온다.
    const label = canvas.getByText("플러그인 이름");
    await expect(label.tagName).toBe("LABEL");
    await expect(label.checkVisibility()).toBe(true);
    await expect(getComputedStyle(label).color).toBe(semanticColor(label, "text"));
  },
};

export const Multi: Story = {
  name: "여러 줄 글 입력은 textarea 이고 높이가 88px 이상이며 세로로만 늘어난다",
  args: { variant: "multi", label: "거부 사유", placeholder: "예: 금액을 먼저 확인해 주세요" },
  play: async ({ canvas, canvasElement }) => {
    const textarea = fieldNamed(canvasElement, "거부 사유");
    await expect(textarea).toBe(canvas.getByRole("textbox", { name: "거부 사유" }));
    const style = getComputedStyle(textarea);
    await expect({
      tag: textarea.tagName,
      rows: textarea.getAttribute("rows"),
      resize: style.resize,
    }).toEqual({ tag: "TEXTAREA", rows: "3", resize: "vertical" });
    await expect(Number.parseFloat(style.height)).toBeGreaterThanOrEqual(88);
    await expect(colorsOf(textarea)).toEqual({
      background: semanticColor(textarea, "raised"),
      text: semanticColor(textarea, "text"),
      border: hoverAwareColor(textarea, "border", "border-hover"),
    });
  },
};

export const Typing: Story = {
  name: "두 변형 모두 글을 넣으면 onChange 가 넣은 글을 받고 라벨은 그대로 보인다",
  render: (args) => (
    <div className="flex flex-col gap-4">
      <TextField {...args} />
      <TextField variant="multi" label="거부 사유" onChange={args.onChange} />
    </div>
  ),
  play: async ({ args, canvasElement, userEvent }) => {
    for (const [name, text] of [
      ["플러그인 이름", "주문 조회"],
      ["거부 사유", "금액을 먼저 확인해 주세요"],
    ] as const) {
      const field = fieldNamed(canvasElement, name);
      await userEvent.type(field, text);
      await expect(args.onChange).toHaveBeenLastCalledWith(text);
      await expect(field.value).toBe(text);
      await expect(field.labels?.[0]?.checkVisibility()).toBe(true);
    }
  },
};

export const WithHelp: Story = {
  name: "도움말은 칸 아래에 muted 글자로 보이고 aria-describedby 로 이어진다",
  render: (args) => (
    <div className="flex flex-col gap-4">
      <TextField {...args} help="목록에 보이는 이름입니다." />
      <TextField
        variant="multi"
        label="거부 사유"
        help="사유는 에이전트에게 그대로 전해집니다."
        onChange={args.onChange}
      />
    </div>
  ),
  play: async ({ canvasElement }) => {
    for (const [name, help] of [
      ["플러그인 이름", "목록에 보이는 이름입니다."],
      ["거부 사유", "사유는 에이전트에게 그대로 전해집니다."],
    ] as const) {
      const field = fieldNamed(canvasElement, name);
      const note = noteOf(field);
      await expect(note?.textContent).toBe(help);
      await expect(note === null ? null : getComputedStyle(note).color).toBe(
        semanticColor(field, "muted"),
      );
      await expect(note?.querySelector("svg")).toBeNull();
      await expect(field.getAttribute("aria-invalid")).toBeNull();
    }
  },
};

export const WithError: Story = {
  name: "오류이면 aria-invalid 이고 테두리와 도움말이 danger 이며 도움말 앞에 circle-x 아이콘이 있다",
  render: (args) => (
    <div className="flex flex-col gap-4">
      <TextField {...args} help="목록에 보이는 이름입니다." error="이미 있는 이름입니다." />
      <TextField
        variant="multi"
        label="거부 사유"
        value="금액을 먼저 확인해 주세요. 지난번 환불과 겹치는지도 봐 주세요."
        error="500자 안으로 적어 주세요."
        onChange={args.onChange}
      />
    </div>
  ),
  play: async ({ canvasElement }) => {
    for (const [name, error] of [
      ["플러그인 이름", "이미 있는 이름입니다."],
      ["거부 사유", "500자 안으로 적어 주세요."],
    ] as const) {
      const field = fieldNamed(canvasElement, name);
      const danger = semanticColor(field, "danger");
      await expect(field.getAttribute("aria-invalid")).toBe("true");
      await expect(colorsOf(field).border).toBe(danger);
      // 오류가 도움말의 자리를 차지한다. 이어 읽는 것은 오류 하나다.
      const note = noteOf(field);
      await expect(note?.textContent).toBe(error);
      await expect(note === null ? null : getComputedStyle(note).color).toBe(danger);
      // 아이콘은 글 앞에 있고 꾸밈이라 숨는다. 모양은 circle-x 이고 색은 도움말의 색(danger)이다.
      const icon = note?.firstElementChild;
      await expect(icon instanceof SVGElement).toBe(true);
      await expect({
        hidden: icon?.getAttribute("aria-hidden"),
        shape: icon?.innerHTML,
        color: icon === null || icon === undefined ? null : getComputedStyle(icon).color,
      }).toEqual({ hidden: "true", shape: iconShape("circle-x"), color: danger });
    }
  },
};

export const Optional: Story = {
  name: "선택이면 라벨 옆에 muted 글자로 '선택'이 보이고 이름에도 든다",
  render: (args) => (
    <div className="flex flex-col gap-4">
      <TextField {...args} optional />
      <TextField variant="multi" label="거부 사유" optional onChange={args.onChange} />
    </div>
  ),
  play: async ({ canvas, canvasElement }) => {
    for (const name of ["플러그인 이름 선택", "거부 사유 선택"]) {
      const field = fieldNamed(canvasElement, name);
      await expect(canvas.getByRole("textbox", { name })).toBe(field);
      const mark = Array.from(field.labels?.[0]?.querySelectorAll("span") ?? []).find(
        (span) => span.textContent.trim() === "선택",
      );
      await expect(mark?.checkVisibility()).toBe(true);
      await expect(mark === undefined ? null : getComputedStyle(mark).color).toBe(
        semanticColor(field, "muted"),
      );
    }
  },
};

export const Disabled: Story = {
  name: "쓸 수 없으면 글을 넣지 못하고 disabled-surface 바탕, divider 테두리, disabled-text 글자와 라벨이며 도움말은 muted 로 남는다",
  render: (args) => (
    <div className="flex flex-col gap-4">
      <TextField {...args} value="주문 조회" help="목록에 보이는 이름입니다." disabled />
      <TextField
        variant="multi"
        label="거부 사유"
        placeholder="예: 금액을 먼저 확인해 주세요"
        disabled
        onChange={args.onChange}
      />
    </div>
  ),
  play: async ({ args, canvasElement, userEvent }) => {
    for (const name of ["플러그인 이름", "거부 사유"]) {
      const field = fieldNamed(canvasElement, name);
      const disabledText = semanticColor(field, "disabled-text");
      await expect(field.disabled).toBe(true);
      await expect(colorsOf(field)).toEqual({
        background: semanticColor(field, "disabled-surface"),
        text: disabledText,
        border: semanticColor(field, "divider"),
      });
      const label = field.labels?.[0];
      await expect(label === undefined ? null : getComputedStyle(label).color).toBe(disabledText);
      // 자리 글자도 쓸 수 없음의 색이다. 넣은 글보다 밝으면 쓸 수 있는 칸처럼 보인다.
      await expect(getComputedStyle(field, "::placeholder").color).toBe(disabledText);
      await userEvent.type(field, "가");
    }
    // 도움말은 쓸 수 없는 조작 요소가 아니라 명암비의 예외가 아니다. 그대로 muted 로 읽힌다.
    const help = noteOf(fieldNamed(canvasElement, "플러그인 이름"));
    await expect(help === null ? null : getComputedStyle(help).color).toBe(
      semanticColor(canvasElement, "muted"),
    );
    await expect(fieldNamed(canvasElement, "플러그인 이름").value).toBe("주문 조회");
    await expect(args.onChange).not.toHaveBeenCalled();
  },
};

export const SingleDark: Story = {
  name: "다크 모드의 글 입력도 raised 바탕에 border 테두리, text 글자다",
  globals: { mode: "dark" },
  play: async ({ canvasElement }) => {
    const input = fieldNamed(canvasElement, "플러그인 이름");
    await expect(getComputedStyle(document.documentElement).colorScheme).toBe("dark");
    await expect(colorsOf(input)).toEqual({
      background: semanticColor(input, "raised"),
      text: semanticColor(input, "text"),
      border: hoverAwareColor(input, "border", "border-hover"),
    });
  },
};

// 공문에서 잰다. 먹은 focus 와 accent 가 같은 색이다. 기본 테마가 아닌 테마에서 값을 재는 판정 스토리라 사진에서
// 뺀다(사진은 기본 테마만 찍는다, ADR 0026 의 2026-10-06 이력).
export const Focus: Story = {
  name: "Tab 으로 포커스하면 focus 색의 실선 테두리가 바깥에 그려지고 글을 넣는 동안 남는다",
  tags: ["judgment"],
  globals: { theme: "gongmun" },
  play: async ({ canvasElement, userEvent }) => {
    const input = fieldNamed(canvasElement, "플러그인 이름");
    await userEvent.tab();
    await expect(document.activeElement).toBe(input);
    await expect(focusRingOf(input)).toEqual(expectedFocusRing(input));
    await userEvent.keyboard("주문");
    await expect(focusRingOf(input)).toEqual(expectedFocusRing(input));
  },
};

export const NarrowColumn: Story = {
  name: "두 변형을 폭 320px 자리에 그려도 가로로 넘치지 않는다",
  render: (args) => (
    <div data-sample="column" className="flex flex-col gap-4" style={{ width: 320 }}>
      <TextField
        {...args}
        help="목록에 보이는 이름입니다. 운영자 화면과 위젯에 같은 이름으로 보입니다."
      />
      <TextField
        variant="multi"
        label="거부 사유"
        optional
        error="500자 안으로 적어 주세요. 지금 글은 512자입니다."
        onChange={args.onChange}
      />
    </div>
  ),
  play: async ({ canvasElement }) => {
    const column = canvasElement.querySelector("[data-sample=column]");
    await expect(column instanceof HTMLElement && column.scrollWidth <= column.clientWidth).toBe(
      true,
    );
  },
};
