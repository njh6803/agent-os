// 위젯의 빌드 둘. `--mode element` 는 script 하나로 커스텀 요소를 정의하는 IIFE 번들, 그 밖은 iframe 용 정적 페이지다.
// 플러그인이 없다.

import { resolve } from "node:path";
import { defineConfig } from "vite";

const here = import.meta.dirname;

export default defineConfig(({ mode }) =>
  mode === "element"
    ? {
        build: {
          outDir: resolve(here, "dist/element"),
          emptyOutDir: true,
          minify: true,
          lib: {
            entry: resolve(here, "element.ts"),
            formats: ["iife"],
            name: "AgentOsWidget",
            fileName: () => "widget.js",
          },
        },
      }
    : { build: { outDir: resolve(here, "dist/page"), emptyOutDir: true } },
);
