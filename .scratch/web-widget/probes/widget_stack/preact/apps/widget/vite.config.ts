// 위젯의 빌드 둘. `--mode element` 는 script 하나로 커스텀 요소를 정의하는 IIFE 번들, 그 밖은 iframe 용 정적 페이지다.
// JSX 는 플러그인 없이 Vite 의 변환이 tsconfig 의 jsxImportSource 로 낸다(이 설정으로 빌드한 번들이 shadow.mjs 에서
// 돌았다). @preact/preset-vite 2.10.6 은 들이지 않았다. 레지스트리의 의존성 목록을 읽으면 Babel 플러그인과 prefresh 를
// 끌고 온다.

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
            entry: resolve(here, "element.tsx"),
            formats: ["iife"],
            name: "AgentOsWidget",
            fileName: () => "widget.js",
          },
        },
      }
    : { build: { outDir: resolve(here, "dist/page"), emptyOutDir: true } },
);
