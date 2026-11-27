// 시제품(측정용) 위젯 진입 단계. 미리 지어 둔 이미지의 컨테이너가 뜰 때 사이트 파일을 읽어 두 가지만 하고 next start 를
// 부른다. 최종 코드가 아니다. 실제 구현은 위젯의 시작 래퍼(tools/start.ts)가 맡을 일이고, 이 파일은 그 래퍼의 루프백 검사를
// 거치지 않는다. 줄 머리가 WRV_PROBE 인 줄은 프로브(run.py)가 읽는 표지다.
//
// 하는 일 둘
//   1. 지어 둔 routes-manifest 원본(.next/routes-manifest.build.json)에서 frame-ancestors 값이 든 응답 머리를 찾아 사이트
//      파일의 허용 출처로 바꾸고 .next/routes-manifest.json 에 쓴다. 그 자리가 정확히 하나이고 값이 지을 때의
//      frame-ancestors 'none' 이 아니면 쓰지 않고 종료 1 로 끝난다(Next 의 판이 올라 모양이 바뀐 것을 조용히 지나지 않는다).
//   2. 위젯의 스크립트가 받아 갈 값 파일(public/runtime.json)에 합친 허용 출처와 가장 작은 요청 글자 수 상한을 쓴다.
// 사이트 파일은 @agent-os/site-file 의 widgetValues 로 읽는다(재던 때는 buildInput 이었고 widget-runtime-values 티켓 02가 이름을 바꿨다. 같은 함수, 같은 진단).
//
// 사용: node tools/entry.mjs [--hostname <호스트>] [--port <포트>]   (앱 폴더의 tools/ 에 복사해 부른다)
// 환경 변수(측정용): WRV_PROBE_WAIT_URL 을 주면 next 를 부르기 전에 wait.mjs 를 뒤에서 띄워 첫 200 의 시각을 찍는다.

import { spawn } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { widgetValues } from "@agent-os/site-file";

const APP = dirname(import.meta.dirname);
const BUILT = join(APP, ".next", "routes-manifest.build.json");
const SERVED = join(APP, ".next", "routes-manifest.json");
const VALUES = join(APP, "public", "runtime.json");
const PLACEHOLDER = "frame-ancestors 'none'";

const now = () => (Date.now() / 1000).toFixed(3);
const mark = (text) => {
  console.log(`WRV_PROBE ${text}`);
};

mark(
  `entry t=${now()} uid=${process.getuid()} pid=${process.pid} site_file=${process.env.AGENT_OS_SITE_FILE ?? "<unset>"}`,
);

let input;
try {
  input = widgetValues(process.env);
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  mark("site-file-rejected");
  process.exit(1);
}

const manifest = JSON.parse(readFileSync(BUILT, "utf-8"));
const slots = [];
for (const rule of manifest.headers ?? []) {
  for (const header of rule.headers ?? []) {
    if (
      String(header.key).toLowerCase() === "content-security-policy" &&
      String(header.value).startsWith("frame-ancestors")
    ) {
      slots.push(header);
    }
  }
}
if (slots.length !== 1 || slots[0].value !== PLACEHOLDER) {
  console.error(
    `지어 둔 routes-manifest 의 frame-ancestors 자리가 기대와 다르다. 찾은 값: ${JSON.stringify(slots.map((slot) => slot.value))}`,
  );
  mark("manifest-shape-rejected");
  process.exit(1);
}
const ancestors = input.allowedOrigins.length === 0 ? "'none'" : input.allowedOrigins.join(" ");
slots[0].value = `frame-ancestors ${ancestors}`;
writeFileSync(SERVED, JSON.stringify(manifest));
writeFileSync(
  VALUES,
  JSON.stringify({ allowedOrigins: input.allowedOrigins, requestChars: input.requestChars }),
);
mark(`wrote t=${now()} ancestors=${JSON.stringify(ancestors)} request_chars=${String(input.requestChars)}`);

if (process.env.WRV_PROBE_WAIT_URL) {
  spawn(process.execPath, ["/probe/wait.mjs", process.env.WRV_PROBE_WAIT_URL], { stdio: "inherit" });
}

// 시작 래퍼의 runNext 와 같은 길이다. next CLI 를 이 프로세스에서 부른다(신호와 종료 코드가 next 의 것 그대로다).
const load = createRequire(import.meta.url);
const bin = load.resolve("next/dist/bin/next");
process.chdir(APP);
process.argv = [process.execPath, bin, "start", ...process.argv.slice(2)];
mark(`next-start t=${now()}`);
load(bin);
