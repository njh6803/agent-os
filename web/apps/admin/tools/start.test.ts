// 시작 래퍼가 받는 인자. 판정의 표는 loopback.test.ts 가 재고, 여기서는 래퍼가 그 판정을 거쳐 next 에 넘길 인자를
// 다시 짓는지를 본다. 프로세스를 띄우지 않는다(띄우는 것은 start.spawn.test.ts).

import { describe, expect, test } from "vitest";
import { nextCommand } from "./start.ts";

function refusal(argv: readonly string[]): string {
  const command = nextCommand(argv, "3000");
  if (!("problem" in command)) {
    throw new Error(`${argv.join(" ")} 가 거부되지 않았다`);
  }
  return command.problem;
}

describe("래퍼가 받는 인자", () => {
  test("루프백 호스트는 그대로 next 의 --hostname 으로 넘어간다", () => {
    expect(nextCommand(["start", "--hostname", "::1"], "3000")).toEqual({
      args: ["start", "--hostname", "::1"],
    });
  });

  test("루프백이 아닌 호스트는 next 에 넘기지 않고 구성 오류다", () => {
    expect(refusal(["dev", "--hostname", "0.0.0.0"])).toContain("ssh -L");
  });

  test("호스트를 주지 않으면 127.0.0.1 에 선다. next 의 기본값은 0.0.0.0 이다", () => {
    expect(nextCommand(["dev"], "3000")).toEqual({ args: ["dev", "--hostname", "127.0.0.1"] });
  });

  test("포트는 받은 그대로 넘어간다", () => {
    expect(nextCommand(["start", "-p", "3100", "-H", "::1"], "3000")).toEqual({
      args: ["start", "--hostname", "::1", "--port", "3100"],
    });
  });

  test("= 로 붙여 준 호스트도 판정을 지난다", () => {
    expect(refusal(["dev", "--hostname=0.0.0.0"])).toContain("0.0.0.0");
  });

  test("SSH 포트 포워딩 안내는 준 포트, 없으면 next 가 쓸 포트를 싣는다", () => {
    expect(refusal(["dev", "--hostname", "0.0.0.0", "--port", "3100"])).toContain(
      "ssh -L 3100:127.0.0.1:3100",
    );
    expect(refusal(["dev", "--hostname", "0.0.0.0"])).toContain("ssh -L 3000:127.0.0.1:3000");
  });

  test("바인딩을 바꿀 수 있는 다른 인자는 넘기지 않고 구성 오류다", () => {
    // next 의 --inspect 는 [[host:]port] 를 받아 디버거를 LAN 에 열 수 있다.
    const problem = refusal(["dev", "--inspect", "0.0.0.0:9229"]);

    expect(problem).toContain("--inspect");
    expect(problem).toContain("--hostname");
  });

  test("dev 나 start 가 아닌 명령은 구성 오류다", () => {
    expect(refusal(["build"])).toContain("build");
    expect(refusal([])).toContain("dev");
    expect(refusal(["dev", "start"])).toContain("start");
  });
});
