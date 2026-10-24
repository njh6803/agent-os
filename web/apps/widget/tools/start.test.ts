// 위젯의 시작 래퍼가 받는 인자. 래퍼가 루프백 판정을 거쳐 next 에 넘길 인자를 다시 짓는지, 어느 명령 앞에서 글꼴을
// 준비하는지, 판정을 지난 명령을 그 차례로 따르는지를 본다. 프로세스를 띄우지 않는다(띄우는 것은 start.spawn.test.ts).

import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { describe, expect, test } from "vitest";
import { absoluteSiteFile, launch, nextCommand } from "./start.ts";

function refusal(argv: readonly string[]): string {
  const command = nextCommand(argv, "3000");
  if (!("problem" in command)) {
    throw new Error(`${argv.join(" ")} 가 거부되지 않았다`);
  }
  return command.problem;
}

describe("래퍼가 받는 인자", () => {
  test("호스트를 주지 않으면 127.0.0.1 에 선다. next 의 기본값은 0.0.0.0 이다", () => {
    expect(nextCommand(["dev"], "3000")).toEqual({
      args: ["dev", "--hostname", "127.0.0.1"],
      prepare: true,
    });
    expect(nextCommand(["start"], "3000")).toEqual({
      args: ["start", "--hostname", "127.0.0.1"],
      prepare: false,
    });
  });

  test("루프백 호스트와 포트는 판정을 지나 그대로 next 에 넘어간다", () => {
    expect(nextCommand(["start", "-H", "::1", "-p", "3100"], "3000")).toEqual({
      args: ["start", "--hostname", "::1", "--port", "3100"],
      prepare: false,
    });
  });

  for (const argv of [
    ["dev", "--hostname", "0.0.0.0"],
    ["start", "--hostname=192.168.0.10"],
    ["dev", "-H", "localhost"],
  ]) {
    test(`${argv.join(" ")} 는 루프백이 아니라 next 에 넘기지 않고 SSH 포트 포워딩을 안내한다`, () => {
      expect(refusal(argv)).toContain("ssh -L 3000:127.0.0.1:3000");
    });
  }

  test("빌드는 글꼴을 준비한 뒤 next build 를 부르고, 서지 않으므로 호스트와 포트를 받지 않는다", () => {
    expect(nextCommand(["build"], "3000")).toEqual({ args: ["build"], prepare: true });
    expect(refusal(["build", "--port", "3100"])).toContain("build");
  });

  test("바인딩을 바꿀 수 있는 다른 인자와 모르는 명령은 구성 오류다", () => {
    expect(refusal(["dev", "--inspect", "0.0.0.0:9229"])).toContain("--inspect");
    expect(refusal(["export"])).toContain("export");
    expect(refusal([])).toContain("dev");
    expect(refusal(["dev", "start"])).toContain("start");
  });
});

describe("판정을 지난 명령을 따르기", () => {
  for (const [command, expected] of [
    ["dev", ["준비", "next dev"]],
    ["build", ["준비", "next build"]],
    ["start", ["next start"]],
  ] as const) {
    test(`${command} 는 ${expected.join(" 뒤에 ")} 를 부른다`, () => {
      const judged = nextCommand([command], "3000");
      if ("problem" in judged) {
        throw new Error(`${command} 가 거부됐다: ${judged.problem}`);
      }
      const calls: string[] = [];
      launch(judged, {
        prepare: () => calls.push("준비"),
        run: (args) => calls.push(`next ${args[0] ?? ""}`),
      });
      expect(calls).toEqual(expected);
    });
  }
});

describe("사이트 파일의 경로", () => {
  test("상대 경로는 래퍼를 부른 자리에서 푼다. next 를 부르기 전에 작업 폴더를 앱으로 옮기기 때문이다", () => {
    const operator = join(tmpdir(), "operator");

    expect(absoluteSiteFile("conf/sites.toml", operator)).toBe(
      resolve(operator, "conf", "sites.toml"),
    );
  });

  test("절대 경로와 빈 값과 없는 값은 그대로 넘긴다. 판정은 설정 파일이 한다", () => {
    const absolute = resolve(tmpdir(), "sites.toml");

    expect(absoluteSiteFile(absolute, join(tmpdir(), "operator"))).toBe(absolute);
    expect(absoluteSiteFile("", join(tmpdir(), "operator"))).toBe("");
    expect(absoluteSiteFile(undefined, join(tmpdir(), "operator"))).toBeUndefined();
  });
});
