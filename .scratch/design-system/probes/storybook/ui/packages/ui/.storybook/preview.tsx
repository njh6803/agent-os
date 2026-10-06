// 미리보기 설정. 패키지의 CSS 원본을 전역으로 싣고, 툴바의 globals 둘로 테마(data-theme)와 그리는 자리(light DOM,
// shadow root)를 바꾼다. axe(addon-a11y)의 위반은 스토리 테스트를 실패시킨다.
import type { Decorator, Preview } from "@storybook/react-vite";
import "../src/styles/theme.css";
import { SHADOW_MODES, ShadowFrame, type ShadowMode } from "./shadow";

type Theme = "light" | "dark";

function themeOf(globals: Record<string, unknown>): Theme {
  return globals["theme"] === "dark" ? "dark" : "light";
}

function shadowOf(globals: Record<string, unknown>): ShadowMode | null {
  const value = globals["shadow"];
  return SHADOW_MODES.find((mode) => mode === value) ?? null;
}

const withTheme: Decorator = (Story, context) => {
  document.documentElement.dataset["theme"] = themeOf(context.globals);
  return <Story />;
};

const withShadowRoot: Decorator = (Story, context) => {
  const mode = shadowOf(context.globals);
  if (mode === null) {
    return <Story />;
  }
  return (
    <ShadowFrame mode={mode} theme={themeOf(context.globals)}>
      <Story />
    </ShadowFrame>
  );
};

const preview = {
  parameters: { a11y: { test: "error" } },
  initialGlobals: { theme: "light", shadow: "off" },
  globalTypes: {
    theme: {
      description: "색 테마(data-theme)",
      toolbar: { title: "테마", items: ["light", "dark"], dynamicTitle: true },
    },
    shadow: {
      description: "그리는 자리. on 은 보정 시트까지, raw 는 Tailwind 시트만 shadow root 에 넣는다",
      toolbar: { title: "shadow", items: ["off", ...SHADOW_MODES], dynamicTitle: true },
    },
  },
  decorators: [withShadowRoot, withTheme],
} satisfies Preview;

export default preview;
