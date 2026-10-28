// 관리 화면 미리보기의 판정 스토리. 스토리 테스트 프로젝트가 고른 창 폭이 닿았는지와, 미리보기가 스토리마다 localStorage
// 를 비우는지 본다(preview.tsx). 사진 비교는 판정 스토리를 찍지 않는다.
//
// 저장소의 두 스토리는 한 파일 안의 차례(쓰기 → 보기)에 기댄다. 차례가 바뀌면 보기가 비었다고 초록이 되지 않게, 쓰기가
// 먼저 돌았다는 표지를 sessionStorage(미리보기가 비우지 않는다)에 남기고 보기가 그것부터 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
import type { ViewportKey } from "./viewports";

const KEY = "admin-storybook-preview-probe";

/**
 * 항목마다 서야 하는 창(admin-style 명세 "Storybook과 사진 비교"의 1280×900 과 320×640). 창을 세우는 viewports.ts 의 값과
 * 따로 적어, 그 값이 명세와 달라지면 이 판정이 빨개진다. 스토리 테스트 프로젝트의 이름과 그 프로젝트가 고르는 항목의
 * 키는 뿌리 vitest.config.ts 가 같은 변수로 정하고, 항목 자체는 preview.tsx 가 짓는다.
 */
const EXPECTED = {
  wide: { width: 1280, height: 900 },
  narrow: { width: 320, height: 640 },
} as const satisfies Record<ViewportKey, { width: number; height: number }>;

function isViewportKey(value: unknown): value is ViewportKey {
  return Object.keys(EXPECTED).some((key) => key === value);
}

/** globals 의 viewport 항목. 고르지 않았으면 null 이다. */
function selectedViewport(globals: Record<string, unknown>): ViewportKey | null {
  const selected = globals["viewport"];
  if (typeof selected !== "object" || selected === null || !("value" in selected)) {
    return null;
  }
  return isViewportKey(selected.value) ? selected.value : null;
}

const meta = {
  title: "판정/미리보기",
  tags: ["judgment"],
  render: () => <p className="text-body">미리보기 판정</p>,
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

/** 프로젝트가 고른 viewport 항목의 크기로 창이 섰다. */
export const Viewport: Story = {
  play: async ({ globals }) => {
    const selected = selectedViewport(globals);
    await expect(selected, "viewport 항목을 고르지 않았다").not.toBeNull();
    if (selected !== null) {
      await expect({ width: window.innerWidth, height: window.innerHeight }).toEqual(
        EXPECTED[selected],
      );
    }
  },
};

/** 다음 스토리가 볼 값을 localStorage 에 쓴다. */
export const StorageWrite: Story = {
  play: () => {
    localStorage.setItem(KEY, "written");
    sessionStorage.setItem(KEY, "written");
  },
};

/** 앞 스토리가 쓴 localStorage 값이 남지 않았다. */
export const StorageCleared: Story = {
  play: async () => {
    await expect(sessionStorage.getItem(KEY), "앞의 쓰기 스토리가 먼저 돌지 않았다").toBe(
      "written",
    );
    sessionStorage.removeItem(KEY);
    await expect(localStorage.getItem(KEY)).toBeNull();
  },
};
