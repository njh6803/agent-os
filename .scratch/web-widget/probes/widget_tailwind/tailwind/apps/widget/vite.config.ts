// 위젯의 Vite 빌드. `--mode element` 는 script 하나로 커스텀 요소를 정의하는 IIFE 번들, 그 밖은 iframe 용 정적
// 페이지(Next 를 쓰지 않을 때의 견줌)다. Tailwind 는 @tailwindcss/vite 로 돈다. 같은 폴더의 postcss.config.mjs(Next 가
// 읽는다)도 Vite 가 찾아 읽는다. 아래 견줌 모드 둘은 측정 전용이다(measure.mjs 가 셋의 CSS 를 견준다).
//   element-viteonly  인라인 PostCSS 설정을 비워 postcss.config.mjs 를 읽지 않는다
//   element-postcss   Vite 플러그인 없이 postcss.config.mjs 만으로 돈다(Next 와 같은 길)
// element 빌드에만 `process.env.NODE_ENV` 를 박는다(widget_stack 의 react 후보와 같다).

import { resolve } from "node:path";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig, type UserConfig } from "vite";

const here = import.meta.dirname;
const ELEMENT_MODES = ["element", "element-viteonly", "element-postcss"];

export default defineConfig(({ mode }): UserConfig => {
  const plugins = mode === "element-postcss" ? [react()] : [react(), tailwindcss()];
  if (!ELEMENT_MODES.includes(mode)) {
    return { plugins, build: { outDir: resolve(here, "dist/page"), emptyOutDir: true } };
  }
  return {
    plugins,
    css: mode === "element-viteonly" ? { postcss: {} } : {},
    define: { "process.env.NODE_ENV": JSON.stringify("production") },
    build: {
      outDir: resolve(here, `dist/${mode}`),
      emptyOutDir: true,
      minify: true,
      lib: {
        entry: resolve(here, "element.tsx"),
        formats: ["iife"],
        name: "AgentOsWidget",
        fileName: () => "widget.js",
      },
    },
  };
});
