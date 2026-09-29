// 관리 화면의 루프백 판정. 시작 래퍼의 바인딩 호스트와 설정의 상류 호스트가 같은 거부 표를 지난다.
// 규칙은 `serve` 와 같다(src/agent_os/main.py 의 LOOPBACK_HOSTS, tests/test_main.py 의 두 선례). 상류는 하나를 더
// 좁혀 127.0.0.1 만 받는다. Next 가 IPv6 리터럴 목적지를 컴파일하지 못한다(ADR 0011 의 2026-09-30 이력).

import { afterEach, describe, expect, test, vi } from "vitest";
import { nextCommand } from "./start.ts";

// 허용되는 것과 거부되는 것. 기댓값을 리터럴로 적는다. 허용 목록을 도는 단언은 그 목록이 비는 날 조용히 통과한다.
const ALLOWED = ["127.0.0.1", "::1"];
const REFUSED = [
  "0.0.0.0",
  "::",
  // 이름은 ::1 로도 풀릴 수 있어 루프백이라는 보장이 없다(tests/test_main.py 의 선례)
  "localhost",
  "192.168.0.10",
  "admin.example",
];

/** URL 에 호스트를 넣는다. IPv6 는 대괄호로 싼다. */
function origin(host: string): string {
  return host.includes(":") ? `http://[${host}]:8000` : `http://${host}:8000`;
}

function refusal(argv: readonly string[]): string {
  const command = nextCommand(argv, "3000");
  if (!("problem" in command)) {
    throw new Error(`${argv.join(" ")} 가 거부되지 않았다`);
  }
  return command.problem;
}

describe("시작 래퍼의 바인딩 호스트", () => {
  for (const host of ALLOWED) {
    test(`${host} 는 그대로 next 의 --hostname 으로 넘어간다`, () => {
      expect(nextCommand(["start", "--hostname", host], "3000")).toEqual({
        args: ["start", "--hostname", host],
      });
    });
  }

  for (const host of REFUSED) {
    test(`${host} 는 구성 오류이고 진단이 허용되는 두 주소와 SSH 포트 포워딩을 말한다`, () => {
      const problem = refusal(["dev", "--hostname", host]);

      expect(problem).toContain(host);
      expect(problem).toContain("127.0.0.1");
      expect(problem).toContain("::1");
      expect(problem.toLowerCase()).toContain("ssh -l");
    });
  }

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

  test("SSH 포트 포워딩 안내는 관리 화면이 설 포트를 싣는다", () => {
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

describe("설정의 상류 호스트", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  /** 상류 입력을 환경에 두고 설정 파일을 새로 읽는다. next dev·build·start 가 읽는 그 파일이다. */
  async function loadConfig(upstream: string | undefined) {
    vi.stubEnv("AGENT_OS_UPSTREAM", upstream);
    vi.resetModules();
    const module = await import("../next.config.ts");
    return module.default;
  }

  async function destinations(upstream: string | undefined): Promise<string[]> {
    const config = await loadConfig(upstream);
    if (config.rewrites === undefined) {
      throw new Error("설정에 rewrites 가 없다");
    }
    const rewrites = await config.rewrites();
    if (!Array.isArray(rewrites)) {
      throw new Error("rewrites 가 배열이 아니다");
    }
    return rewrites.map((rewrite) => `${rewrite.source} -> ${rewrite.destination}`);
  }

  test("127.0.0.1 상류로 같은 출처의 /api/* 를 넘긴다", async () => {
    expect(await destinations("http://127.0.0.1:8100")).toEqual([
      "/api/:path* -> http://127.0.0.1:8100/:path*",
    ]);
  });

  for (const host of REFUSED) {
    test(`${host} 상류는 설정을 읽을 때 구성 오류이고 진단이 127.0.0.1 과 SSH 포트 포워딩을 말한다`, async () => {
      const failure = loadConfig(origin(host));

      await expect(failure).rejects.toThrow(host);
      await expect(failure).rejects.toThrow("127.0.0.1");
      await expect(failure).rejects.toThrow(/ssh -L/i);
    });
  }

  test("::1 상류는 루프백이어도 구성 오류이고 serve 를 127.0.0.1 에 세우라고 안내한다", async () => {
    // Next 16.3.6 의 rewrites 는 목적지 호스트를 경로 틀로 컴파일해 [::1] 에서 요청마다 500 이다(ADR 0011 의
    // 2026-09-30 이력). 요청 때 드러날 것을 설정을 읽을 때 막는다.
    const failure = loadConfig("http://[::1]:8000");

    await expect(failure).rejects.toThrow("::1");
    await expect(failure).rejects.toThrow("--host 127.0.0.1");
  });

  test("상류를 주지 않으면 serve 의 기본 주소 http://127.0.0.1:8000 이다", async () => {
    expect(await destinations(undefined)).toEqual(["/api/:path* -> http://127.0.0.1:8000/:path*"]);
    expect(await destinations("")).toEqual(["/api/:path* -> http://127.0.0.1:8000/:path*"]);
  });

  test("줄여 쓴 IPv4 는 URL 이 127.0.0.1 로 정규화해 받는다", async () => {
    // 판정은 URL 파서가 정규화한 호스트를 본다. 127.1 은 127.0.0.1 과 같은 주소다.
    expect(await destinations("http://127.1:8100")).toEqual([
      "/api/:path* -> http://127.0.0.1:8100/:path*",
    ]);
  });

  test("끝의 빗금은 출처의 일부로 읽는다", async () => {
    expect(await destinations("http://127.0.0.1:8100/")).toEqual([
      "/api/:path* -> http://127.0.0.1:8100/:path*",
    ]);
  });

  for (const value of [
    "127.0.0.1:8000",
    "https://127.0.0.1:8000",
    "http://127.0.0.1:8000/api",
    "http://127.0.0.1:8000/?a=1",
    "http://user:secret@127.0.0.1:8000",
    "http://127.0.0.1:8000#x",
  ]) {
    test(`http 출처 하나가 아닌 ${value} 는 구성 오류다`, async () => {
      await expect(loadConfig(value)).rejects.toThrow("AGENT_OS_UPSTREAM");
    });
  }

  test("계정을 실은 상류의 진단은 그 비밀번호를 싣지 않는다", async () => {
    // 원칙 V: 로그에 비밀번호를 싣지 않는다. 구성 오류는 터미널과 CI 로그에 남는다.
    await expect(loadConfig("http://user:secret@127.0.0.1:8000")).rejects.not.toThrow("secret");
  });
});
