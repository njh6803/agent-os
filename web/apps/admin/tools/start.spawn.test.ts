// 시작 래퍼를 실제 프로세스로 띄운다. 판정은 loopback.test.ts 가, 인자는 start.test.ts 가 잰다. 여기서는 거부가 next 를
// 띄우기 전에 끝나는지와, 진입점이 환경의 PORT 를 SSH 안내에 싣는지를 본다. 운영체제별 명령(taskkill, netstat)에
// 기대지 않는다. 윈도우와 CI 의 ubuntu 에서 같이 돈다.

import { spawnSync } from "node:child_process";
import { connect, createServer } from "node:net";
import { join } from "node:path";
import { expect, test } from "vitest";

const START = join(import.meta.dirname, "start.ts");

/** 지금 비어 있는 루프백 포트. 잡았다 놓는다. */
function freePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const server = createServer();
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const address = server.address();
      server.close(() => {
        if (address === null || typeof address === "string") {
          reject(new Error("포트를 받지 못했다"));
        } else {
          resolve(address.port);
        }
      });
    });
  });
}

/** 그 포트에서 듣는 것이 있는가. 연결을 시도만 한다. */
function listening(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = connect({ port, host: "127.0.0.1" });
    socket.once("connect", () => {
      socket.destroy();
      resolve(true);
    });
    socket.once("error", () => {
      resolve(false);
    });
  });
}

test("루프백이 아닌 호스트로 띄우면 포트를 열지 않고 실패 종료 코드로 끝난다", async () => {
  const port = await freePort();

  // next 가 떴다면 이 프로세스는 스스로 끝나지 않는다. 시간 제한에 걸리면 status 가 null 이다.
  const run = spawnSync(
    process.execPath,
    [START, "dev", "--hostname", "0.0.0.0", "--port", String(port)],
    { encoding: "utf-8", timeout: 30_000 },
  );

  expect(run.status).toBe(1);
  expect(run.stderr).toContain("0.0.0.0");
  expect(run.stderr).toContain(`ssh -L ${String(port)}:127.0.0.1:${String(port)}`);
  // next 의 첫 줄(판과 주소)이 없다. next 를 부르기 전에 끝났다.
  expect(run.stdout).toBe("");
  expect(await listening(port)).toBe(false);
});

test("포트를 주지 않으면 SSH 포트 포워딩 안내는 next 가 쓸 PORT 를 싣는다", () => {
  const run = spawnSync(process.execPath, [START, "dev", "--hostname", "0.0.0.0"], {
    encoding: "utf-8",
    timeout: 30_000,
    env: { ...process.env, PORT: "3456" },
  });

  expect(run.status).toBe(1);
  expect(run.stderr).toContain("ssh -L 3456:127.0.0.1:3456");
});
