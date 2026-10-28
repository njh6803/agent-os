// 관리 화면의 Storybook(ADR 0026 의 2026-10-07 이력, admin-style 명세 "Storybook과 사진 비교"). 스토리 한 벌이 미리보기,
// 스토리 테스트(뿌리 vitest.config.ts 의 admin-storybook-wide·admin-storybook-narrow 프로젝트), 사진 비교(visual/)의
// 원천이다. 미리보기의 본체는 디자인 시스템 패키지의 것을 나눠 쓴다.
//
// Tailwind 와 빈 PostCSS 설정은 위젯의 .storybook/main.ts 와 같은 까닭이다. 앱 폴더의 postcss.config.mjs 는 Next 의
// 길이다.
//
// `next/link` 는 평범한 `<a>` 를 그리는 대역(next-link.tsx)으로 별칭한다. Next 밖의 Vite 에서 진짜 `Link` 는 정적
// 빌드에서는 그려지지만 스토리 테스트에서는 `ReferenceError: process is not defined` 로 불러오다 실패했고, 별칭을 두면
// 두 길 모두 `<a href>` 로 그려졌다(.scratch/admin-style/probes/storybook_next_link.mjs). 별칭은 Vite 의 `mergeConfig`
// 로 더해 Storybook 이 이미 둔 별칭(배열이든 객체든) 앞에 선다.
import { join } from "node:path";
import tailwindcss from "@tailwindcss/vite";
import type { StorybookConfig } from "@storybook/react-vite";
import { mergeConfig } from "vite";

const NEXT_LINK = { find: /^next\/link$/, replacement: join(import.meta.dirname, "next-link.tsx") };

const config = {
  framework: "@storybook/react-vite",
  stories: ["../components/**/*.stories.tsx", "./*.stories.tsx"],
  addons: ["@storybook/addon-a11y", "@storybook/addon-vitest"],
  core: { disableTelemetry: true },
  viteFinal: (viteConfig) =>
    mergeConfig(
      {
        ...viteConfig,
        css: { ...viteConfig.css, postcss: { plugins: [] } },
        plugins: [...(viteConfig.plugins ?? []), tailwindcss()],
      },
      { resolve: { alias: [NEXT_LINK] } },
    ),
} satisfies StorybookConfig;

export default config;
