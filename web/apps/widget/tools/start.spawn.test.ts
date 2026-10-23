// 위젯의 시작 래퍼를 실제 프로세스로 띄운다. 인자의 판정은 start.test.ts 가 잰다. 여기서는 거부가 next 를 띄우기 전에
// 끝나는지만 본다. 운영체제별 명령에 기대지 않는다. 윈도우와 CI 의 ubuntu 에서 같이 돈다.

import { spawnSync } from "node:child_process";
import { join } from "node:path";
import { expect, test } from "vitest";

const START = join(import.meta.dirname, "start.ts");

test("루프백이 아닌 호스트로 띄우면 next 를 부르지 않고 실패 종료 코드로 끝난다", () => {
  // next 가 떴다면 이 프로세스는 스스로 끝나지 않는다. 시간 제한에 걸리면 status 가 null 이다.
  const run = spawnSync(process.execPath, [START, "dev", "--hostname", "0.0.0.0"], {
    encoding: "utf-8",
    timeout: 30_000,
    env: { ...process.env, PORT: "3456" },
  });

  expect(run.status).toBe(1);
  expect(run.stderr).toContain("ssh -L 3456:127.0.0.1:3456");
  // next 의 첫 줄(판과 주소)이 없다. next 를 부르기 전에 끝났다.
  expect(run.stdout).toBe("");
});
