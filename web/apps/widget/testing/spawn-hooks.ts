// 시작 래퍼를 실제 프로세스로 띄우는 시험(tools/start.spawn.test.ts)이 `--import` 로 거는 불러오기 가로채기. 셋을 한다.
//
// - `next/dist/bin/next` 를 가짜 실행 파일(stub-next.ts)로 바꾼다. 실제 Next 를 띄우지 않고 래퍼가 그것을 부르는 자리까지만 본다.
// - 임시 앱 폴더에 복사한 래퍼는 `node_modules` 가 없어 `@agent-os/site-file` 을 찾지 못한다. 저장소의 그 패키지로 잇는다.
// - 스크립트를 짓는 도구(Vite, Tailwind 의 Vite 플러그인, TypeScript)와 그것을 부르는 모듈(글꼴 복사, 페이지 안 번들의 빌드)은
//   `WIDGET_TEST_TOOLS` 에 따라 다룬다. `reject`(기본)면 불러오는 순간 오류를 던져 서비스 시작이 빌드 도구를 불러왔다고 말하게
//   하고, `stub` 이면 빈 모듈을 세워 빌드가 그 뒤의 단계까지 가게 한다. 뜬 뒤의 이미지에는 그 도구가 없다(widget-runtime-values
//   명세 "위젯 이미지").

import { registerHooks } from "node:module";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const HERE = import.meta.dirname;
const SITE_FILE = pathToFileURL(
  join(HERE, "..", "..", "..", "packages", "site-file", "src", "index.ts"),
).href;
const NEXT = pathToFileURL(join(HERE, "stub-next.ts")).href;
const TOOLS = pathToFileURL(join(HERE, "stub-tools.ts")).href;
const BUILD_TOOLS: ReadonlySet<string> = new Set(["vite", "@tailwindcss/vite", "typescript"]);

/** 스크립트를 짓는 도구나 그것을 부르는 모듈인가. */
function isBuildTool(specifier: string): boolean {
  return (
    BUILD_TOOLS.has(specifier) ||
    specifier === "@agent-os/ui/fonts" ||
    /(^|\/)element\.ts$/.test(specifier)
  );
}

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === "@agent-os/site-file") {
      return { url: SITE_FILE, shortCircuit: true };
    }
    if (specifier === "next/dist/bin/next") {
      return { url: NEXT, shortCircuit: true };
    }
    if (isBuildTool(specifier)) {
      if (process.env["WIDGET_TEST_TOOLS"] === "stub") {
        return { url: TOOLS, shortCircuit: true };
      }
      throw new Error(`서비스 시작이 빌드 도구를 불러왔다: ${specifier}`);
    }
    return nextResolve(specifier, context);
  },
});
