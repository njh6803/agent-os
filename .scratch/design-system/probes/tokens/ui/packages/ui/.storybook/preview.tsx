// 미리보기 설정(프로브 표본). 패키지의 CSS 원본을 전역으로 싣고, 툴바의 globals 셋으로 테마(data-theme), 모드
// (data-mode, system 이면 속성을 두지 않는다), 그리는 자리(light DOM, shadow root)를 바꾼다. axe 의 위반은 스토리
// 테스트를 실패시킨다.
import type { Decorator, Preview } from "@storybook/react-vite";
import "../src/styles/theme.css";
import { THEMES, type Theme } from "../src/styles/design-tokens";
import { SHADOW_MODES, ShadowFrame, type Mode, type ShadowMode } from "./shadow";

const MODE_ITEMS = ["system", "light", "dark"] as const;

function themeOf(globals: Record<string, unknown>): Theme {
  return THEMES.find((theme) => theme === globals["theme"]) ?? "muk";
}

function modeOf(globals: Record<string, unknown>): Mode | null {
  const value = globals["mode"];
  return value === "light" || value === "dark" ? value : null;
}

function shadowOf(globals: Record<string, unknown>): ShadowMode | null {
  const value = globals["shadow"];
  return SHADOW_MODES.find((mode) => mode === value) ?? null;
}

const withTheme: Decorator = (Story, context) => {
  const root = document.documentElement;
  root.dataset["theme"] = themeOf(context.globals);
  const mode = modeOf(context.globals);
  if (mode === null) {
    delete root.dataset["mode"];
  } else {
    root.dataset["mode"] = mode;
  }
  return <Story />;
};

const withShadowRoot: Decorator = (Story, context) => {
  const shadow = shadowOf(context.globals);
  if (shadow === null) {
    return <Story />;
  }
  return (
    <ShadowFrame
      shadow={shadow}
      theme={themeOf(context.globals)}
      mode={modeOf(context.globals)}
    >
      <Story />
    </ShadowFrame>
  );
};

const preview = {
  parameters: { a11y: { test: "error" } },
  initialGlobals: { theme: "muk", mode: "system", shadow: "off" },
  globalTypes: {
    theme: {
      description: "테마(data-theme)",
      toolbar: { title: "테마", items: [...THEMES], dynamicTitle: true },
    },
    mode: {
      description: "모드(data-mode). system 이면 속성을 두지 않는다",
      toolbar: { title: "모드", items: [...MODE_ITEMS], dynamicTitle: true },
    },
    shadow: {
      description: "그리는 자리. on 은 보정 시트까지, raw 는 Tailwind 시트만 shadow root 에 넣는다",
      toolbar: { title: "shadow", items: ["off", ...SHADOW_MODES], dynamicTitle: true },
    },
  },
  decorators: [withShadowRoot, withTheme],
} satisfies Preview;

export default preview;
