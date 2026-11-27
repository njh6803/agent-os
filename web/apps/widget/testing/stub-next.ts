// 실제 Next 대신 래퍼가 부르는 자리에 서는 가짜 실행 파일(tools/start.spawn.test.ts 가 쓴다). 래퍼는 `process.argv` 를 짓고 이
// 파일을 `require` 로 불러 Next 를 부른다(`start.ts` 의 `runNext`). 받은 인자를 한 줄로 찍는다. 빌드면 실제 Next 16.3.6 처럼
// 부른 줄이 돌아온 뒤에야 응답 머리 목록을 남기고 `process.exit(0)` 으로 끝난다(`tools/manifest.ts` 머리 주석). 남길 목록의 글은
// 환경 변수 `WIDGET_TEST_BUILT_MANIFEST` 가 가리키는 파일에서 읽는다.

import { copyFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";

const args = process.argv.slice(2);
console.log(`NEXT-STUB ${JSON.stringify(args)}`);

// 목록을 주지 않거나 비워 주면 빌드가 목록을 남기지 않은 길이다. 아무것도 쓰지 않고 그대로 끝난다.
const built = process.env["WIDGET_TEST_BUILT_MANIFEST"];
if (args[0] === "build" && built !== undefined && built !== "") {
  setTimeout(() => {
    mkdirSync(join(process.cwd(), ".next"), { recursive: true });
    copyFileSync(built, join(process.cwd(), ".next", "routes-manifest.json"));
    process.exit(0);
  }, 20);
}
