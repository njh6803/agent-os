// 시작 래퍼가 받는 인자. 판정의 표는 loopback.test.ts 가 재고, 여기서는 래퍼가 그 판정을 거쳐 next 에 넘길 인자를
// 다시 짓는지를 본다. 프로세스를 띄우지 않는다(띄우는 것은 start.spawn.test.ts).

import { describe, expect, test } from "vitest";
import { CASES, expectSignals, nameOf } from "../testing/container-network.ts";
import type { ContainerNetwork } from "./loopback.ts";
import { nextCommand } from "./start.ts";

// 예외가 꺼진 입력. 표지 파일도 환경 변수도 없다.
const OUTSIDE: ContainerNetwork = { imageMarker: false, env: undefined };

function refusal(argv: readonly string[]): string {
  const command = nextCommand(argv, "3000", OUTSIDE);
  if (!("problem" in command)) {
    throw new Error(`${argv.join(" ")} 가 거부되지 않았다`);
  }
  return command.problem;
}

describe("래퍼가 받는 인자", () => {
  test("루프백 호스트는 그대로 next 의 --hostname 으로 넘어간다", () => {
    expect(nextCommand(["start", "--hostname", "::1"], "3000", OUTSIDE)).toEqual({
      args: ["start", "--hostname", "::1"],
    });
  });

  test("루프백이 아닌 호스트는 next 에 넘기지 않고 구성 오류다", () => {
    expect(refusal(["dev", "--hostname", "0.0.0.0"])).toContain("ssh -L");
  });

  test("호스트를 주지 않으면 127.0.0.1 에 선다. next 의 기본값은 0.0.0.0 이다", () => {
    expect(nextCommand(["dev"], "3000", OUTSIDE)).toEqual({
      args: ["dev", "--hostname", "127.0.0.1"],
    });
  });

  test("포트는 받은 그대로 넘어간다", () => {
    expect(nextCommand(["start", "-p", "3100", "-H", "::1"], "3000", OUTSIDE)).toEqual({
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

// 사례 표(tests/fixtures/container_network/cases.json)의 듣는 주소. 판정 함수만이 아니라 래퍼가 그 판정을 거쳐 next 에
// 넘기는지를 본다. 표를 읽는 쪽이 loopback.test.ts 와 둘인 것은 래퍼가 판정을 부르는 자리가 따로이기 때문이다.
describe("래퍼가 읽는 컨테이너 네트워크 예외의 사례 표", () => {
  for (const item of CASES.binding) {
    test(nameOf(item), () => {
      const command = nextCommand(["start", "--hostname", item.host], "3000", {
        imageMarker: item.marker,
        env: item.env,
      });

      if (item.verdict === "ok") {
        expect(command).toEqual({ args: ["start", "--hostname", item.host] });
      } else if ("problem" in command) {
        expectSignals(command.problem, CASES.bindingSignals, item);
      } else {
        throw new Error("거부되지 않았다");
      }
    });
  }
});
