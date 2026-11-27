// 위젯의 시작 래퍼가 받는 인자. 래퍼가 루프백 판정을 거쳐 next 에 넘길 인자를 다시 짓는지, 어느 명령 앞에서 값 파일을
// 쓰고 빌드의 입력(글꼴 파일과 페이지 안 번들)을 준비하는지, 판정을 지난 명령을 그 차례로 따르는지를 본다. 프로세스를
// 띄우지 않는다(띄우는 것은 start.spawn.test.ts). 값 파일의 내용은 runtime.test.ts 가 본다.

import { existsSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { SITE_FILE_ENV } from "@agent-os/site-file";
import { afterEach, describe, expect, test } from "vitest";
import { CASES, expectSignals, nameOf } from "../testing/container-network.ts";
import { expectedSiteFile, SITE_FILE_FIXTURES } from "../testing/site-file.ts";
import { RUNTIME_FILE, writeRuntimeValues } from "./runtime.ts";
import {
  absoluteSiteFile,
  type ContainerNetwork,
  launch,
  type NextCommand,
  nextCommand,
} from "./start.ts";

// 예외가 꺼진 입력. 표지 파일도 환경 변수도 없다.
const OUTSIDE: ContainerNetwork = { imageMarker: false, env: undefined };

function refusal(argv: readonly string[]): string {
  const command = nextCommand(argv, "3000", OUTSIDE);
  if (!("problem" in command)) {
    throw new Error(`${argv.join(" ")} 가 거부되지 않았다`);
  }
  return command.problem;
}

/** 거부되지 않은 명령. 거부됐으면 시험이 멈춘다. */
function accepted(argv: readonly string[]): Exclude<NextCommand, { readonly problem: string }> {
  const command = nextCommand(argv, "3000", OUTSIDE);
  if ("problem" in command) {
    throw new Error(`${argv.join(" ")} 가 거부됐다: ${command.problem}`);
  }
  return command;
}

describe("래퍼가 받는 인자", () => {
  test("호스트를 주지 않으면 127.0.0.1 에 선다. next 의 기본값은 0.0.0.0 이다", () => {
    expect(nextCommand(["dev"], "3000", OUTSIDE)).toEqual({
      args: ["dev", "--hostname", "127.0.0.1"],
      prepare: true,
      runtime: true,
    });
    expect(nextCommand(["start"], "3000", OUTSIDE)).toEqual({
      args: ["start", "--hostname", "127.0.0.1"],
      prepare: false,
      runtime: true,
    });
  });

  test("루프백 호스트와 포트는 판정을 지나 그대로 next 에 넘어간다", () => {
    expect(nextCommand(["start", "-H", "::1", "-p", "3100"], "3000", OUTSIDE)).toEqual({
      args: ["start", "--hostname", "::1", "--port", "3100"],
      prepare: false,
      runtime: true,
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

  test("빌드는 입력을 준비한 뒤 next build 를 부르고, 서지 않으므로 값 파일을 쓰지 않고 호스트와 포트를 받지 않는다", () => {
    expect(nextCommand(["build"], "3000", OUTSIDE)).toEqual({
      args: ["build"],
      prepare: true,
      runtime: false,
    });
    expect(refusal(["build", "--port", "3100"])).toContain("build");
  });

  test("바인딩을 바꿀 수 있는 다른 인자와 모르는 명령은 구성 오류다", () => {
    expect(refusal(["dev", "--inspect", "0.0.0.0:9229"])).toContain("--inspect");
    expect(refusal(["export"])).toContain("export");
    expect(refusal([])).toContain("dev");
    expect(refusal(["dev", "start"])).toContain("start");
  });
});

const created: string[] = [];

afterEach(() => {
  for (const folder of created.splice(0)) {
    rmSync(folder, { recursive: true, force: true, maxRetries: 5 });
  }
});

/** 앱 폴더에 쓴 값 파일을 읽은 값. */
function valuesIn(app: string): unknown {
  return JSON.parse(readFileSync(join(app, "public", RUNTIME_FILE), "utf-8"));
}

/** 값 파일을 쓸 앱 폴더. 래퍼의 `APP` 대신 시험이 주는 임시 폴더라 저장소의 앱 폴더에 쓰지 않는다. */
function appFolder(): string {
  const folder = mkdtempSync(join(tmpdir(), "widget-start-"));
  created.push(folder);
  return folder;
}

describe("판정을 지난 명령을 따르기", () => {
  for (const [command, expected] of [
    ["dev", ["값 파일", "준비", "next dev"]],
    ["build", ["준비", "next build"]],
    ["start", ["값 파일", "next start"]],
  ] as const) {
    test(`${command} 는 ${expected.join(" 뒤에 ")} 를 부른다`, async () => {
      const calls: string[] = [];
      await launch(accepted([command]), {
        runtime: () => calls.push("값 파일"),
        // 페이지 안 번들의 빌드는 비동기다. 준비가 끝난 뒤에야 next 를 부른다.
        prepare: async () => {
          await new Promise((resolve) => setTimeout(resolve, 10));
          calls.push("준비");
        },
        run: (args) => calls.push(`next ${args[0] ?? ""}`),
      });
      expect(calls).toEqual(expected);
    });
  }

  test("준비가 실패하면 next 를 부르지 않는다", async () => {
    const calls: string[] = [];
    await expect(
      launch(accepted(["build"]), {
        runtime: () => calls.push("값 파일"),
        prepare: () => Promise.reject(new Error("글꼴을 복사하지 못했다")),
        run: (args) => calls.push(`next ${args[0] ?? ""}`),
      }),
    ).rejects.toThrow("글꼴을 복사하지 못했다");
    expect(calls).toEqual([]);
  });

  test("값 파일을 쓰지 못하면 준비도 next 도 부르지 않는다", async () => {
    for (const name of ["dev", "start"]) {
      const calls: string[] = [];
      await expect(
        launch(accepted([name]), {
          runtime: () => {
            throw new Error("사이트 파일을 받아들일 수 없다");
          },
          prepare: () => Promise.resolve(void calls.push("준비")),
          run: (args) => calls.push(`next ${args[0] ?? ""}`),
        }),
      ).rejects.toThrow("사이트 파일을 받아들일 수 없다");
      expect(calls).toEqual([]);
    }
  });
});

// 값 파일을 쓰는 실제 코드를 시험이 준 앱 폴더로 걸어, 서비스 시작과 개발 서버가 사이트 파일을 읽어 쓴 뒤에 next 를 부르는지
// 본다. 쓰는 코드의 내용은 runtime.test.ts 가 본다.
describe("서비스 시작과 개발 서버가 값 파일을 쓴다", () => {
  /** 래퍼의 값 파일 단계와 같은 모양의 단계. 환경 변수와 앱 폴더와 알림 자리만 시험이 준다. */
  function steps(env: Record<string, string>, app: string, lines: string[], calls: string[]) {
    return {
      runtime: () => {
        writeRuntimeValues(env, app, (line) => lines.push(line));
        calls.push("값 파일");
      },
      prepare: () => Promise.resolve(void calls.push("준비")),
      run: () =>
        calls.push(`next ${existsSync(join(app, "public", RUNTIME_FILE)) ? "있음" : "없음"}`),
    };
  }

  for (const name of ["dev", "start"]) {
    test(`${name} 는 사이트 파일의 합친 값을 값 파일로 쓰고 한 줄로 알린 뒤에 next 를 부른다`, async () => {
      const app = appFolder();
      const lines: string[] = [];
      const calls: string[] = [];
      const expected = expectedSiteFile();

      await launch(
        accepted([name]),
        steps({ [SITE_FILE_ENV]: join(SITE_FILE_FIXTURES, "sites.toml") }, app, lines, calls),
      );

      // next 를 부를 때 값 파일이 이미 있다. dev 는 그 사이에 준비가 든다.
      expect(calls.at(-1)).toBe("next 있음");
      expect(valuesIn(app)).toEqual({
        allowedOrigins: expected.allowedOrigins,
        requestChars: expected.requestChars,
      });
      expect(lines).toHaveLength(1);
      expect(lines[0]).toContain(String(expected.requestChars));
    });
  }

  test("사이트 파일의 환경 변수가 없으면 멈추지 않고 빈 허용 출처와 기본 상한 20000 으로 쓴다", async () => {
    const app = appFolder();

    await launch(accepted(["start"]), steps({}, app, [], []));

    expect(valuesIn(app)).toEqual({
      allowedOrigins: [],
      requestChars: 20_000,
    });
  });

  test("서 있지 않은 build 는 값 파일을 쓰지 않는다", async () => {
    const app = appFolder();
    const calls: string[] = [];

    await launch(accepted(["build"]), steps({}, app, [], calls));

    expect(calls).toEqual(["준비", "next 없음"]);
  });

  describe("읽지 못하는 사이트 파일이면 진단을 찍고 next 를 부르지 않고, 값 파일도 쓰지 않는다", () => {
    const missing = join(tmpdir(), "widget-start-none", "sites.toml");
    for (const [name, value, diagnosis] of [
      ["파일이 없다", missing, `사이트 파일 ${missing} 을 받아들일 수 없다`],
      ["변수가 비었다", "", `${SITE_FILE_ENV} 가 비었다`],
    ] as const) {
      test(name, async () => {
        const app = appFolder();
        const calls: string[] = [];

        await expect(
          launch(accepted(["start"]), steps({ [SITE_FILE_ENV]: value }, app, [], calls)),
        ).rejects.toThrow(diagnosis);

        expect(calls).toEqual([]);
        expect(existsSync(join(app, "public", RUNTIME_FILE))).toBe(false);
      });
    }
  });
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

// 사례 표(tests/fixtures/container_network/cases.json)의 듣는 주소. 파이썬의 tests/test_main.py 와 관리 화면, 위젯 미리보기
// 페이지의 시험이 같은 표를 읽는다. 표지 파일을 실제로 읽는 길은 이미지를 띄우는 시험(release-image 07·08·09)이 본다.
describe("컨테이너 네트워크 예외의 사례 표", () => {
  test("표가 판정의 종류를 모두 갖고 있다", () => {
    expect(new Set(CASES.binding.map(({ verdict }) => verdict))).toEqual(
      new Set(["ok", ...Object.keys(CASES.bindingSignals)]),
    );
  });

  for (const item of CASES.binding) {
    test(nameOf(item), () => {
      const command = nextCommand(["start", "--hostname", item.host], "3000", {
        imageMarker: item.marker,
        env: item.env,
      });

      if (item.verdict === "ok") {
        expect(command).toEqual({
          args: ["start", "--hostname", item.host],
          prepare: false,
          runtime: true,
        });
      } else if ("problem" in command) {
        expectSignals(command.problem, CASES.bindingSignals, item);
      } else {
        throw new Error("거부되지 않았다");
      }
    });
  }

  test("빌드는 서지 않아 환경 변수의 오타도 보지 않는다", () => {
    const command = nextCommand(["build"], "3000", { imageMarker: false, env: "true" });

    expect(command).toEqual({ args: ["build"], prepare: true, runtime: false });
  });
});
