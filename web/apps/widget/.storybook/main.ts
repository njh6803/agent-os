// 위젯의 Storybook(ADR 0026 의 2026-10-07 이력). 스토리 한 벌이 미리보기, 스토리 테스트(뿌리 vitest.config.ts 의
// widget-storybook 프로젝트), 사진 비교(visual/)의 원천이다. 미리보기의 본체는 디자인 시스템 패키지의 것을 나눠 쓴다.
//
// Tailwind 는 viteFinal 로 단다(패키지의 .storybook/main.ts 와 같은 까닭). 그리고 PostCSS 설정을 빈 인라인 값으로 둔다.
// 앱 폴더의 postcss.config.mjs 는 Next 의 길이다. Vite 는 인라인 값이 있으면 설정 파일을 찾지 않는데, 찾으면 앱
// 폴더에서 띄운 build-storybook 이 Tailwind 를 두 번 돌린다.
import tailwindcss from "@tailwindcss/vite";
import type { StorybookConfig } from "@storybook/react-vite";

const config = {
  framework: "@storybook/react-vite",
  stories: ["../components/**/*.stories.tsx"],
  addons: ["@storybook/addon-a11y", "@storybook/addon-vitest"],
  core: { disableTelemetry: true },
  viteFinal: (viteConfig) => ({
    ...viteConfig,
    css: { ...viteConfig.css, postcss: { plugins: [] } },
    plugins: [...(viteConfig.plugins ?? []), tailwindcss()],
  }),
} satisfies StorybookConfig;

export default config;
