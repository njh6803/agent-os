// 위젯의 빌드 둘. `--mode element` 는 script 하나로 커스텀 요소를 정의하는 IIFE 번들, 그 밖은 iframe 용 정적 페이지다.
// element 빌드에만 `process.env.NODE_ENV` 를 박는다. Vite 문서가 라이브러리 모드는 이 값을 바꾸지 않는다고 해서
// 넣었고, 빼고 빌드해 재지는 않았다.

import { resolve } from "node:path";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const here = import.meta.dirname;

export default defineConfig(({ mode }) =>
  mode === "element"
    ? {
        plugins: [react()],
        define: { "process.env.NODE_ENV": JSON.stringify("production") },
        build: {
          outDir: resolve(here, "dist/element"),
          emptyOutDir: true,
          minify: true,
          lib: {
            entry: resolve(here, "element.tsx"),
            formats: ["iife"],
            name: "AgentOsWidget",
            fileName: () => "widget.js",
          },
        },
      }
    : {
        plugins: [react()],
        build: { outDir: resolve(here, "dist/page"), emptyOutDir: true },
      },
);
