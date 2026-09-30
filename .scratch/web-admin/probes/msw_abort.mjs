// 페이지 테스트의 가짜 네트워크(MSW 3.0.0)가 응답 뒤의 끊김을 어떻게 다루는지 잰다(web-admin 티켓 08).
//
// 03 의 메모: "브라우저의 fetch가 본문 스트림을 끝내는 것은 03이 손으로 만든 스트림으로만 쟀다. MSW를 지나는 페이지
// 테스트에서 끊김이 실제로 그 모양인지 본다." 재는 것은 셋이다. 응답 본문을 한 조각 읽은 뒤 요청의 signal 을 끊으면
//   1. 핸들러가 받은 request.signal 이 끊기는가
//   2. 핸들러가 낸 ReadableStream 의 cancel 이 불리는가
//   3. 다음 조각을 기다리던 읽기가 에러로 끝나는가, 계속 기다리는가
// 그리고 반대쪽 하나. 핸들러의 스트림이 한 조각 뒤 에러로 끝나면(`controller.error`) 읽는 쪽의 다음 읽기가 무엇으로
// 끝나는가. 페이지 테스트의 "도중에 끊김"이 그 모양이다.
//
// 앱의 페이지 테스트 설정(testing/setup.ts 의 MSW 서버)을 그대로 쓰려고 테스트 파일을 components/ 아래에 잠시 쓰고
// finally 에서 지운다. 쓰는 법: node .scratch/web-admin/probes/msw_abort.mjs   (저장소 루트에서. 네트워크를 타지 않는다)

import { spawnSync } from "node:child_process";
import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const WEB = join(process.cwd(), "web");
const DIR = join(WEB, "apps", "admin", "components", "probe-msw-abort");
const FILE = join(DIR, "abort.test.tsx");

const SOURCE = `
import { http } from "msw";
import { expect, test } from "vitest";
import { api, network } from "../../testing/network";

test("응답 뒤의 끊김", async () => {
  let handlerSignal = "끊기지 않았다";
  let cancelled = "불리지 않았다";
  network.use(
    http.post(api("/probe"), ({ request }) => {
      request.signal.addEventListener("abort", () => {
        handlerSignal = "끊겼다";
      });
      const body = new ReadableStream({
        start(controller) {
          controller.enqueue(new TextEncoder().encode("data: 1\\n\\n"));
        },
        cancel() {
          cancelled = "불렸다";
        },
      });
      return new Response(body, { headers: { "Content-Type": "text/event-stream" } });
    }),
  );
  const controller = new AbortController();
  const response = await fetch(api("/probe"), { method: "POST", signal: controller.signal });
  const reader = response.body?.getReader();
  expect(reader).toBeDefined();
  await reader?.read();
  const pending = reader?.read().then(
    () => "풀렸다",
    (error: unknown) => \`에러로 끝났다: \${String(error)}\`,
  );
  controller.abort();
  const outcome = await Promise.race([
    pending,
    new Promise((resolve) => setTimeout(() => resolve("500ms 뒤에도 기다린다"), 500)),
  ]);
  console.log("PROBE 핸들러의 request.signal:", handlerSignal);
  console.log("PROBE 핸들러 스트림의 cancel:", cancelled);
  console.log("PROBE 기다리던 읽기:", outcome);
});

test("핸들러 스트림의 에러", async () => {
  network.use(
    http.post(api("/probe"), () => {
      const body = new ReadableStream({
        async start(controller) {
          controller.enqueue(new TextEncoder().encode("data: 1\\n\\n"));
          await new Promise((resolve) => setTimeout(resolve, 50));
          controller.error(new Error("끊겼다"));
        },
      });
      return new Response(body, { headers: { "Content-Type": "text/event-stream" } });
    }),
  );
  const response = await fetch(api("/probe"), { method: "POST" });
  const reader = response.body?.getReader();
  await reader?.read();
  const outcome = await Promise.race([
    reader?.read().then(
      ({ done }) => (done ? "done 으로 끝났다" : "조각이 더 왔다"),
      (error: unknown) => \`에러로 끝났다: \${String(error)}\`,
    ),
    new Promise((resolve) => setTimeout(() => resolve("500ms 뒤에도 기다린다"), 500)),
  ]);
  console.log("PROBE 핸들러 스트림이 에러로 끝난 뒤의 읽기:", outcome);
});
`;

mkdirSync(DIR, { recursive: true });
try {
  writeFileSync(FILE, SOURCE);
  // 초록인 테스트의 콘솔도 보이게 한다(`--silent=false`).
  const run = spawnSync(
    "pnpm exec vitest run --silent=false --project pages apps/admin/components/probe-msw-abort",
    { cwd: WEB, encoding: "utf-8", shell: true },
  );
  const lines = `${run.stdout}\n${run.stderr}`
    .split("\n")
    .filter((line) => /PROBE|✓|×|FAIL|Tests /.test(line));
  console.log(lines.join("\n"));
  const version = spawnSync(
    "node",
    ["-p", "require('msw/package.json').version"],
    {
      cwd: join(WEB, "apps", "admin"),
      encoding: "utf-8",
    },
  );
  console.log(`msw ${version.stdout.trim()}`);
  process.exitCode = run.status ?? 1;
} finally {
  rmSync(DIR, { recursive: true, force: true });
}
