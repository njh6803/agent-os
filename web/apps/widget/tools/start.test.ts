// 위젯의 시작 래퍼가 받는 인자. 래퍼가 루프백 판정을 거쳐 next 에 넘길 인자를 다시 짓는지, 어느 명령 앞에서 값 파일과 사본을
// 쓰고 빌드 준비물(글꼴 파일과 페이지 안 번들)을 준비하며 빌드가 원본을 남기게 하는지, 판정을 지난 명령을 그 차례로 따르는지를
// 본다. 프로세스를 띄우지 않는다(띄우는 것은 start.spawn.test.ts). 값 파일의 내용은 runtime.test.ts, 응답 머리 목록의 원본과
// 사본은 manifest.test.ts 가 본다.

import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { SITE_FILE_ENV } from "@agent-os/site-file";
import { afterEach, describe, expect, test } from "vitest";
import { CASES, expectSignals, nameOf } from "../testing/container-network.ts";
import { builtManifest } from "../testing/manifest.ts";
import { expectedSiteFile, SITE_FILE_FIXTURES } from "../testing/site-file.ts";
import { manifestPaths, writeServedManifest } from "./manifest.ts";
import { RUNTIME_FILE, type RuntimeValuesFile, writeRuntimeValues } from "./runtime.ts";
import {
  absoluteSiteFile,
  type ContainerNetwork,
  type LaunchSteps,
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
      manifest: null,
    });
    expect(nextCommand(["start"], "3000", OUTSIDE)).toEqual({
      args: ["start", "--hostname", "127.0.0.1"],
      prepare: false,
      runtime: true,
      manifest: "fill",
    });
  });

  test("루프백 호스트와 포트는 판정을 지나 그대로 next 에 넘어간다", () => {
    expect(nextCommand(["start", "-H", "::1", "-p", "3100"], "3000", OUTSIDE)).toEqual({
      args: ["start", "--hostname", "::1", "--port", "3100"],
      prepare: false,
      runtime: true,
      manifest: "fill",
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

  test("빌드는 입력을 준비한 뒤 next build 를 부르고 응답 머리 목록의 원본을 남긴다. 서지 않으므로 값 파일을 쓰지 않고 호스트와 포트를 받지 않는다", () => {
    expect(nextCommand(["build"], "3000", OUTSIDE)).toEqual({
      args: ["build"],
      prepare: true,
      runtime: false,
      manifest: "keep",
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

const NO_VALUES: RuntimeValuesFile = { allowedOrigins: [], requestChars: 20_000 };

/** 단계를 부른 차례를 `calls` 에 적는 가짜 단계. 바꿀 단계만 `override` 로 준다. */
function recording(calls: string[], override: Partial<LaunchSteps> = {}): LaunchSteps {
  return {
    runtime: () => {
      calls.push("값 파일");
      return NO_VALUES;
    },
    manifest: () => {
      calls.push("사본");
    },
    keep: () => {
      calls.push("원본 처리기");
    },
    // 페이지 안 번들의 빌드는 비동기다. 준비가 끝난 뒤에야 next 를 부른다.
    prepare: async () => {
      await new Promise((resolve) => setTimeout(resolve, 10));
      calls.push("준비");
    },
    run: (args) => {
      calls.push(`next ${args[0] ?? ""}`);
    },
    ...override,
  };
}

describe("판정을 지난 명령을 따르기", () => {
  for (const [command, expected] of [
    ["dev", ["값 파일", "준비", "next dev"]],
    ["build", ["준비", "원본 처리기", "next build"]],
    ["start", ["값 파일", "사본", "next start"]],
  ] as const) {
    test(`${command} 는 ${expected.join(" 뒤에 ")} 를 부른다`, async () => {
      const calls: string[] = [];

      await launch(accepted([command]), recording(calls));

      expect(calls).toEqual(expected);
    });
  }

  test("준비가 실패하면 원본 처리기도 next 도 부르지 않는다", async () => {
    const calls: string[] = [];

    await expect(
      launch(
        accepted(["build"]),
        recording(calls, { prepare: () => Promise.reject(new Error("글꼴을 복사하지 못했다")) }),
      ),
    ).rejects.toThrow("글꼴을 복사하지 못했다");

    expect(calls).toEqual([]);
  });

  test("값 파일을 쓰지 못하면 사본도 준비도 next 도 부르지 않는다", async () => {
    for (const name of ["dev", "start"]) {
      const calls: string[] = [];

      await expect(
        launch(
          accepted([name]),
          recording(calls, {
            runtime: () => {
              throw new Error("사이트 파일을 받아들일 수 없다");
            },
          }),
        ),
      ).rejects.toThrow("사이트 파일을 받아들일 수 없다");

      expect(calls).toEqual([]);
    }
  });

  test("사본을 쓰지 못하면 next 를 부르지 않는다", async () => {
    const calls: string[] = [];

    await expect(
      launch(
        accepted(["start"]),
        recording(calls, {
          manifest: () => {
            throw new Error("바꿀 자리가 기대와 다르다");
          },
        }),
      ),
    ).rejects.toThrow("바꿀 자리가 기대와 다르다");

    // 값 파일은 사본보다 앞서 이미 썼다. 사본이 틀렸으면 next 는 부르지 않는다.
    expect(calls).toEqual(["값 파일"]);
  });

  test("사본은 값 파일을 쓴 단계가 돌려준 값으로 바꾼다", async () => {
    const values: RuntimeValuesFile = {
      allowedOrigins: ["https://a.example"],
      requestChars: 4000,
    };
    const received: RuntimeValuesFile[] = [];

    await launch(
      accepted(["start"]),
      recording([], {
        runtime: () => values,
        manifest: (given) => {
          received.push(given);
        },
      }),
    );

    expect(received).toEqual([values]);
  });
});

// 값 파일과 사본을 쓰는 실제 코드를 시험이 준 앱 폴더로 걸어, 서비스 시작이 사이트 파일을 읽어 두 파일을 쓴 뒤에 next 를
// 부르는지, 개발 서버는 값 파일만 쓰는지 본다. 쓰는 코드의 내용은 runtime.test.ts 와 manifest.test.ts 가 본다.
describe("서비스 시작과 개발 서버가 값 파일과 사본을 쓴다", () => {
  const SERVED = (app: string) => manifestPaths(app).served;

  /** 앱 폴더에 빌드가 남긴 원본을 둔다. 서비스 시작이 읽는 것이다. */
  function seedOriginal(app: string, text = JSON.stringify(builtManifest())): void {
    mkdirSync(join(app, ".next"));
    writeFileSync(manifestPaths(app).original, text);
  }

  /** next 를 부른 때 값 파일과 사본이 이미 있었는지 적는 말. */
  function seen(app: string): string {
    const values = existsSync(join(app, "public", RUNTIME_FILE)) ? "값 파일" : "값 파일 없음";
    const served = existsSync(SERVED(app)) ? "사본" : "사본 없음";
    return `next 때 ${values} ${served}`;
  }

  /** 래퍼의 실제 단계와 같은 모양의 단계. 환경 변수와 앱 폴더와 알림 자리만 시험이 준다. */
  function steps(
    env: Record<string, string>,
    app: string,
    lines: string[],
    calls: string[],
  ): LaunchSteps {
    return {
      runtime: () => {
        const values = writeRuntimeValues(env, app, (line) => lines.push(line));
        calls.push("값 파일");
        return values;
      },
      manifest: (values) => {
        writeServedManifest(app, values);
        calls.push("사본");
      },
      keep: () => {
        calls.push("원본 처리기");
      },
      prepare: () => Promise.resolve(void calls.push("준비")),
      run: () => {
        calls.push(seen(app));
      },
    };
  }

  function servedAncestors(app: string): unknown {
    return JSON.parse(readFileSync(SERVED(app), "utf-8"));
  }

  test("start 는 사이트 파일의 합친 값을 값 파일로, 합친 허용 출처를 사본으로 쓴 뒤에 next 를 부른다", async () => {
    const app = appFolder();
    seedOriginal(app);
    const lines: string[] = [];
    const calls: string[] = [];
    const expected = expectedSiteFile();

    await launch(
      accepted(["start"]),
      steps({ [SITE_FILE_ENV]: join(SITE_FILE_FIXTURES, "sites.toml") }, app, lines, calls),
    );

    // next 를 부를 때 값 파일과 사본이 이미 있다.
    expect(calls).toEqual(["값 파일", "사본", "next 때 값 파일 사본"]);
    expect(valuesIn(app)).toEqual({
      allowedOrigins: expected.allowedOrigins,
      requestChars: expected.requestChars,
    });
    expect(servedAncestors(app)).toEqual(
      builtManifest(`frame-ancestors ${expected.allowedOrigins.join(" ")}`),
    );
    expect(lines).toHaveLength(1);
    expect(lines[0]).toContain(String(expected.requestChars));
  });

  test("dev 는 값 파일만 쓰고 사본은 쓰지 않는다. 개발 서버의 설정이 응답 머리를 낸다", async () => {
    const app = appFolder();
    const calls: string[] = [];

    await launch(
      accepted(["dev"]),
      steps({ [SITE_FILE_ENV]: join(SITE_FILE_FIXTURES, "sites.toml") }, app, [], calls),
    );

    expect(calls).toEqual(["값 파일", "준비", "next 때 값 파일 사본 없음"]);
  });

  test("사이트 파일의 환경 변수가 없으면 멈추지 않고 빈 허용 출처, 기본 상한 20000, 'none' 사본으로 쓴다", async () => {
    const app = appFolder();
    seedOriginal(app);

    await launch(accepted(["start"]), steps({}, app, [], []));

    expect(valuesIn(app)).toEqual({ allowedOrigins: [], requestChars: 20_000 });
    expect(servedAncestors(app)).toEqual(builtManifest());
  });

  test("서 있지 않은 build 는 값 파일도 사본도 쓰지 않고 원본 처리기를 등록한다", async () => {
    const app = appFolder();
    const calls: string[] = [];

    await launch(accepted(["build"]), steps({}, app, [], calls));

    expect(calls).toEqual(["준비", "원본 처리기", "next 때 값 파일 없음 사본 없음"]);
  });

  describe("읽지 못하는 사이트 파일이면 진단을 찍고 next 를 부르지 않고, 두 파일도 쓰지 않는다", () => {
    const missing = join(tmpdir(), "widget-start-none", "sites.toml");
    for (const [name, value, diagnosis] of [
      ["파일이 없다", missing, `사이트 파일 ${missing} 을 받아들일 수 없다`],
      ["변수가 비었다", "", `${SITE_FILE_ENV} 가 비었다`],
    ] as const) {
      test(name, async () => {
        const app = appFolder();
        seedOriginal(app);
        const calls: string[] = [];

        await expect(
          launch(accepted(["start"]), steps({ [SITE_FILE_ENV]: value }, app, [], calls)),
        ).rejects.toThrow(diagnosis);

        expect(calls).toEqual([]);
        expect(existsSync(join(app, "public", RUNTIME_FILE))).toBe(false);
        expect(existsSync(SERVED(app))).toBe(false);
      });
    }
  });

  describe("바꿀 자리를 찾지 못하면 사본을 쓰지 않고 next 를 부르지 않는다", () => {
    test("빌드가 사이트 파일을 읽어 값을 굳힌 산출물이다", async () => {
      const app = appFolder();
      seedOriginal(app, JSON.stringify(builtManifest("frame-ancestors https://decoy.example")));
      const calls: string[] = [];

      await expect(
        launch(
          accepted(["start"]),
          steps({ [SITE_FILE_ENV]: join(SITE_FILE_FIXTURES, "sites.toml") }, app, [], calls),
        ),
      ).rejects.toThrow("frame-ancestors https://decoy.example");

      expect(calls).toEqual(["값 파일"]);
      expect(existsSync(SERVED(app))).toBe(false);
    });

    test("원본이 없다", async () => {
      const app = appFolder();
      const calls: string[] = [];

      await expect(launch(accepted(["start"]), steps({}, app, [], calls))).rejects.toThrow(
        "routes-manifest.original.json 이 없다",
      );

      expect(calls).toEqual(["값 파일"]);
    });
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
          manifest: "fill",
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

    expect(command).toEqual({
      args: ["build"],
      prepare: true,
      runtime: false,
      manifest: "keep",
    });
  });
});
