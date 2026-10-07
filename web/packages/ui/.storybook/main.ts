// Storybook 설정. 스토리 한 벌이 미리보기, 스토리 테스트(뿌리 vitest.config.ts 의 storybook 프로젝트), `/design-sync`
// 의 원천이다(ADR 0026). Tailwind 는 viteFinal 로 단다. 패키지 폴더에 vite.config.ts 를 두면 Storybook 은 읽지만, 뿌리의
// vitest.config.ts 가 도는 스토리 테스트(@storybook/addon-vitest)는 그 파일을 읽지 않는다.
import tailwindcss from "@tailwindcss/vite";
import type { StorybookConfig } from "@storybook/react-vite";

const config = {
  framework: "@storybook/react-vite",
  stories: ["../src/**/*.stories.tsx"],
  addons: ["@storybook/addon-a11y", "@storybook/addon-vitest"],
  core: { disableTelemetry: true },
  viteFinal: (viteConfig) => ({
    ...viteConfig,
    plugins: [...(viteConfig.plugins ?? []), tailwindcss()],
  }),
} satisfies StorybookConfig;

export default config;
