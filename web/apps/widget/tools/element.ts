/**
 * 페이지 안 번들의 빌드(web-widget 티켓 10, ADR 0024 의 배치). 시작 래퍼(`start.ts`)가 `dev` 와 `build` 전에 Vite 의
 * 라이브러리 빌드로 `element/index.ts` 를 묶어 Next 의 `public/element.js` 에 낸다. Next 가 그것을 `/widget/element.js`
 * 로 낸다. 설정 파일을 두지 않고 이 함수가 설정을 짓는다. 앱 폴더에 `vite.config.ts` 가 있으면 위젯의 Storybook 빌더가
 * 그것을 찾아 읽는다(`@storybook/builder-vite` 가 `.storybook` 의 부모를 뿌리로 Vite 의 `loadConfigFromFile` 을 부른다.
 * 코드를 읽어 봤다).
 *
 * - 번들의 꼴은 즉시 실행되는 classic 스크립트 하나(IIFE)다. 다른 출처의 `<script type="module">` 은 CORS 로 받고,
 *   classic 스크립트는 청크로 나뉘지 않아 사이트가 넣을 것이 한 줄로 남는다(명세 "번들의 꼴"). 입구가 아무것도 내보내지
 *   않아 사이트 페이지의 전역 이름을 짓지 않는다.
 * - 빌드의 입력은 iframe 페이지와 같은 사이트 파일이다(`site-file.ts` 의 `buildInput`). 가장 작은 요청 글자 수 상한을
 *   `process.env.AGENT_OS_WIDGET_REQUEST_CHARS` 의 자리에 글자로 박는다. lib/build.ts 가 Next 의 env 와 같은 자리를 읽기
 *   때문이다. 변수가 준 파일을 읽지 못하면 던져 빌드가 멈춘다(fail-closed, ADR 0024). 페이지 안 방식은 postMessage 를
 *   쓰지 않아 허용 출처는 싣지 않는다. 상대 경로의 `AGENT_OS_SITE_FILE` 은 시작 래퍼가 푼다.
 * - 라이브러리 빌드는 `process.env.*` 를 바꾸지 않는다(https://vite.dev/guide/build#library-mode 의 원문, "`process.env.*`
 *   usage are not"). React 의 개발판이 실리지 않게 박는다.
 * - CSS 는 위젯의 CSS(디자인 토큰 CSS 를 들이고 위젯 소스를 덮은 것)만 `?inline` 글자로 싣는다. 글꼴 CSS 는 싣지 않는다.
 *   라이브러리 모드는 `url()` 의 자산까지 data URL 로 박는다(디자인 토큰 CSS 의 머리 주석). 글꼴은 face 의 목록만
 *   가상 모듈(`virtual:agent-os-widget/fonts`, element/virtual.d.ts)로 싣고 파일은 위젯 출처에서 받는다.
 * - Tailwind 는 Vite 플러그인으로 돌고 PostCSS 설정은 빈 인라인 값이다. 앱 폴더의 `postcss.config.mjs` 는 Next 의 길이고,
 *   Vite 가 그것까지 찾으면 Tailwind 가 두 번 돈다(위젯의 .storybook/main.ts 와 같다).
 * - 내는 자리에는 글꼴 파일이 함께 있어 비우지 않고, Vite 의 public 복사도 끈다. 산출물은 저장소가 무시한다(뿌리
 *   `.gitignore`).
 */

import { join } from "node:path";
import tailwindcss from "@tailwindcss/vite";
import { build, type InlineConfig, type Plugin } from "vite";
import type { FontFaceSource } from "../element/fonts.ts";
import { fontFaces } from "./fonts.ts";
import { buildInput, WIDGET_REQUEST_CHARS_ENV } from "./site-file.ts";

const APP = join(import.meta.dirname, "..");
export const ELEMENT_FILE = "element.js";
const FONTS_MODULE = "virtual:agent-os-widget/fonts";

/** 페이지 안 번들의 Vite 설정. `outDir` 을 주지 않으면 Next 의 `public/` 이다. 사이트 파일을 읽지 못하면 던진다. */
export function elementBuildConfig(
  env: Readonly<Record<string, string | undefined>>,
  outDir: string = join(APP, "public"),
): InlineConfig {
  const input = buildInput(env);
  return {
    configFile: false,
    root: APP,
    publicDir: false,
    logLevel: "warn",
    css: { postcss: { plugins: [] } },
    plugins: [tailwindcss(), fontsModule(fontFaces())],
    define: {
      "process.env.NODE_ENV": JSON.stringify("production"),
      // String(n) 은 10^21 부터 지수 꼴이라 BigInt 로 십진수 글을 짓는다(next.config.ts 와 같다).
      [`process.env.${WIDGET_REQUEST_CHARS_ENV}`]: JSON.stringify(
        BigInt(input.requestChars).toString(),
      ),
    },
    build: {
      outDir,
      emptyOutDir: false,
      copyPublicDir: false,
      reportCompressedSize: false,
      lib: {
        entry: join(APP, "element", "index.ts"),
        formats: ["iife"],
        // Vite 가 iife 에 이름을 요구한다. 입구가 아무것도 내보내지 않아 전역에 이 이름이 서지 않는다.
        name: "AgentOsWidget",
        fileName: () => ELEMENT_FILE,
      },
    },
  };
}

/**
 * 페이지 안 번들을 짓는다. Vite 의 `build` 는 `NODE_ENV` 가 비었으면 production 으로 채우고 되돌리지 않는다(vite 8.3.1 의
 * `resolveConfig`). 시작 래퍼가 같은 프로세스에서 이어 부르는 `next dev` 가 그 값을 받지 않게 빌드 전의 값으로 되돌린다.
 */
export async function buildElement(
  env: Readonly<Record<string, string | undefined>>,
  outDir?: string,
): Promise<void> {
  // Next 의 타입은 NODE_ENV 를 늘 있는 값으로 적는다. 시작 래퍼가 부를 때는 비어 있을 수 있어 넓은 타입으로 받는다.
  const processEnv: Record<string, string | undefined> = process.env;
  const nodeEnv = processEnv["NODE_ENV"];
  try {
    await build(elementBuildConfig(env, outDir));
  } finally {
    if (nodeEnv === undefined) {
      delete processEnv["NODE_ENV"];
    } else {
      processEnv["NODE_ENV"] = nodeEnv;
    }
  }
}

/**
 * 글꼴 face 의 목록을 내는 가상 모듈. 번들 입구가 그 목록으로 사이트 문서에 글꼴을 등록한다. 한글 글꼴의 세 굵기는 같은
 * 글자 범위를 쓰므로 범위는 한 번씩만 싣고 face 가 그것을 가리킨다. 굵기마다 실으면 목록 모듈의 글이 gzip 으로 약 71KB,
 * 한 번씩 실으면 약 25KB 였다(`.scratch/web-widget/probes/font_list_size.mjs`, 2026-10-24). 같은 범위가 gzip 의 창(32KB)
 * 보다 멀리 떨어져 되풀이가 줄지 않은 것으로 어림한다.
 */
function fontsModule(faces: readonly FontFaceSource[]): Plugin {
  const resolved = `\0${FONTS_MODULE}`;
  return {
    name: "agent-os-widget-fonts",
    resolveId: (id) => (id === FONTS_MODULE ? resolved : null),
    load: (id) => (id === resolved ? fontsSource(faces) : null),
  };
}

function fontsSource(faces: readonly FontFaceSource[]): string {
  const ranges = new Map<string, number>();
  for (const { unicodeRange } of faces) {
    if (!ranges.has(unicodeRange)) {
      ranges.set(unicodeRange, ranges.size);
    }
  }
  const entries = faces.map(({ unicodeRange, ...rest }) => {
    const fields = Object.entries(rest).map(([key, value]) => `${key}:${JSON.stringify(value)}`);
    return `{${fields.join(",")},unicodeRange:ranges[${String(ranges.get(unicodeRange))}]}`;
  });
  return [
    `const ranges = ${JSON.stringify([...ranges.keys()])};`,
    `export const FONT_FACES = [${entries.join(",")}];`,
  ].join("\n");
}
