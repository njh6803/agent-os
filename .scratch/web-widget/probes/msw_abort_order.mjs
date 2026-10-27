// 위젯 페이지 시험의 가짜 네트워크(MSW 3.0.0, @mswjs/interceptors 0.45.5, Node 의 fetch 인 undici)에서, 응답 본문을
// 읽던 fetch 를 끊는 자리가 뒤의 테스트에 무엇을 남기는지 잰다(web-widget 티켓 09).
//
// 계기. 재접속 시험의 45초 무응답 테스트(위젯의 무응답 타이머가 콜백 안에서 fetch 를 끊었다) 뒤에 undici 의
// `assert(!this.aborted)` 가 처리되지 않은 에러로 찍히고, 그 뒤 테스트의 구독이 응답 전에 실패했다. 그 테스트만 돌리면
// 초록이었다. 진단(diagnosing-bugs)이 줄인 재현이 아래 둘째 테스트다. 그 가운데 "스트림을 읽다 마이크로태스크에서
// 끊기"와 "한 틱 기다리기"는 하나라도 빼면 초록이었고, 구독의 `signal` 은 빼도 빨갰다. 이 줄임은 임시 테스트 파일로 손으로
// 본 것이다(README 의 "2026-10-25 결과 — 끊는 자리").
//
// 갈래 셋. 파일마다 다른 워커에서 돌아 한 갈래가 망가뜨린 연결이 다른 갈래에 닿지 않는다. 파일마다 테스트가 둘이다.
//   첫째 테스트: 응답 본문을 한 조각 읽은 fetch 를 끊는다. 끊는 자리가 갈래마다 다르다.
//   둘째 테스트: 스트림 하나를 한 조각 읽고 마이크로태스크에서 끊은 뒤, 한 틱 기다려 같은 출처에 fetch 를 하나 더 보내
//     본문의 첫 조각을 읽는다.
//   1. timer: 첫째가 실제 `setTimeout` 콜백 안에서 끊는다. 위젯의 옛 무응답 타이머가 끊던 자리다.
//   2. microtask: 첫째가 `Promise.resolve().then` 안에서 끊는다. 1의 대조다. 끊기 자체가 탈이면 이것도 빨갛다.
//   3. fresh: 1과 같이 끊고, 둘째가 처음에 Node 의 전역 디스패처(undici 의 연결 풀)를 새것으로 바꾼다. 망가진 것이 MSW
//      가 아니라 undici 의 연결이라는 해석의 갈래다. MSW 쪽이 망가졌으면 이것도 빨갛다.
//
// 회차의 표지. 끊은 fetch 마다 끊기 전에 첫 조각을 읽었고 끊은 뒤 신호가 끊겼어야 측정이다. 테스트가 그것과 둘째의 결과를
// 파일에 적고, 표지가 없는 회차가 하나라도 있으면 종료 코드는 1이다. 단언은 처리되지 않은 에러 블록에 그 글과 그 파일
// 이름이 함께 있을 때 그 갈래의 것으로 센다.
//
// 재지 않은 것. 왜 타이머 콜백에서만 나는지는 인터셉터의 소스(`lib/node/source-BU2cVRgr.js` 의 `socket._destroy`)를 읽은
// 어림이다. 가짜 소켓은 끊길 때 error 를 `queueMicrotask` 로, close 를 `process.nextTick` 으로 낸다. 마이크로태스크
// 안에서 끊으면 error 가 같은 비움에서 먼저 돌고, 매크로태스크에서 끊으면 nextTick 이 먼저 돌아 close 가 앞선다. undici
// 는 에러 없는 close 를 응답의 끝으로 읽어 끊긴 요청을 끝내려다 단언에 걸리고, 그 close 처리를 마치지 못한 클라이언트가
// 죽은 소켓을 든 채 남는다.
//
// 앱의 시험 설정(testing/setup.ts 의 MSW 서버)을 그대로 쓰려고 테스트 파일을 components/ 아래에 잠시 쓰고 finally 에서
// 지운다. 쓰는 법: node .scratch/web-widget/probes/msw_abort_order.mjs   (저장소 루트에서. 네트워크를 타지 않는다)

import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const WEB = join(process.cwd(), "web");
const DIR = join(WEB, "apps", "widget", "components", "probe-msw-abort-order");

const ABORT = {
  timer: "await new Promise((resolve) => setTimeout(() => { controller.abort(); resolve(undefined); }, 0));",
  microtask: "await Promise.resolve().then(() => { controller.abort(); });",
};

const FRESH = `
  const key = Symbol.for("undici.globalDispatcher.1");
  const current = Reflect.get(globalThis, key);
  Reflect.set(globalThis, key, Reflect.construct(current.constructor, []));`;

function source(abort, fresh, resultPath) {
  return `
import { readFileSync, writeFileSync } from "node:fs";
import { http } from "msw";
import { test } from "vitest";
import { api, network } from "../../testing/network";

const RESULT = ${JSON.stringify(resultPath)};

function body(text: string, close: boolean): Response {
  const stream = new ReadableStream({
    async start(controller) {
      await new Promise((resolve) => setTimeout(resolve, 10));
      controller.enqueue(new TextEncoder().encode(text));
      if (close) controller.close();
    },
  });
  return new Response(stream, { headers: { "Content-Type": "text/event-stream" } });
}

/** 본문을 한 조각 읽은 뒤 끊는다. 읽은 것과 끊김을 돌려준다. */
async function readThenAbort(path: string, abort: (controller: AbortController) => Promise<void>) {
  const controller = new AbortController();
  const response = await fetch(api(path), { signal: controller.signal });
  const reader = response.body?.getReader();
  const first = await reader?.read();
  void reader?.read().catch(() => undefined);
  await abort(controller);
  return { read: new TextDecoder().decode(first?.value), aborted: controller.signal.aborted };
}

test("첫째", async () => {
  network.use(http.get(api("/probe"), () => body("data: 1\\n\\n", false)));
  const first = await readThenAbort("/probe", async (controller) => { ${abort} });
  await new Promise((resolve) => setTimeout(resolve, 50));
  writeFileSync(RESULT, JSON.stringify({ first }));
});

test("둘째", async () => {
  ${fresh ? FRESH : ""}
  network.use(
    http.get(api("/start"), () => body("data: 1\\n\\n", false)),
    http.get(api("/next"), () => body("data: 2\\n\\n", true)),
  );
  const second = await readThenAbort("/start", async (controller) => { ${ABORT.microtask} });
  await new Promise((resolve) => setTimeout(resolve, 0));
  const next = await fetch(api("/next")).then(
    async (response) => {
      const chunk = await response.body?.getReader().read();
      return chunk === undefined || chunk.done ? "본문이 조각 없이 끝났다" : "첫 조각을 읽었다";
    },
    (error: unknown) => \`fetch 실패(\${error instanceof Error ? String(error.cause) : String(error)})\`,
  );
  const saved = JSON.parse(readFileSync(RESULT, "utf8"));
  writeFileSync(RESULT, JSON.stringify({ ...saved, second, next }));
});
`;
}

const CASES = [
  ["timer", "타이머 콜백에서 끊기", ABORT.timer, false],
  ["microtask", "마이크로태스크에서 끊기(대조)", ABORT.microtask, false],
  ["fresh", "타이머 콜백에서 끊고 둘째가 디스패처를 새로", ABORT.timer, true],
];

function marked(entry) {
  return entry !== undefined && entry.read === "data: 1\n\n" && entry.aborted === true;
}

let unmeasured = 0;
mkdirSync(DIR, { recursive: true });
try {
  for (const [file, , abort, fresh] of CASES) {
    writeFileSync(join(DIR, `${file}.test.tsx`), source(abort, fresh, join(DIR, `${file}.json`)));
  }
  const run = spawnSync(
    "pnpm exec vitest run --project widget-pages apps/widget/components/probe-msw-abort-order",
    { cwd: WEB, encoding: "utf8", shell: true },
  );
  const output = `${run.stdout}\n${run.stderr}`.replace(/\x1b\[[0-9;]*m/g, "");
  const blocks = output.split("Uncaught Exception").slice(1);
  for (const [file, name] of CASES) {
    let result;
    try {
      result = JSON.parse(readFileSync(join(DIR, `${file}.json`), "utf8"));
    } catch {
      console.log(`${name}: 측정 아님(결과 파일이 없다)`);
      unmeasured += 1;
      continue;
    }
    if (!marked(result.first) || !marked(result.second) || typeof result.next !== "string") {
      console.log(`${name}: 측정 아님(${JSON.stringify(result)})`);
      unmeasured += 1;
      continue;
    }
    const asserted = blocks.some(
      (block) =>
        block.includes("assert(!this.aborted)") && block.includes(`probe-msw-abort-order/${file}.test.tsx`),
    );
    console.log(`${name}: undici 단언 ${asserted ? "났다" : "나지 않았다"}, 둘째의 다음 요청 ${result.next}`);
  }
} finally {
  rmSync(DIR, { recursive: true, force: true });
}
process.exitCode = unmeasured === 0 ? 0 : 1;
