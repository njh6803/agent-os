// 관리 화면의 설정 파일. next dev·build·start 가 읽는 그 파일을 새로 읽어, 상류의 판정이 읽는 자리에서 일어나는지와
// 같은 출처의 /api/* 를 어디로 넘기는지를 본다. 판정의 표는 tools/loopback.test.ts 가 잰다.

import { afterEach, expect, test, vi } from "vitest";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

/** 상류 입력을 환경에 두고 설정 파일을 새로 읽는다. */
async function loadConfig(upstream: string | undefined) {
  vi.stubEnv("AGENT_OS_UPSTREAM", upstream);
  vi.resetModules();
  const module = await import("./next.config.ts");
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

test("상류를 주지 않으면 serve 의 기본 주소 http://127.0.0.1:8000 이다", async () => {
  expect(await destinations(undefined)).toEqual(["/api/:path* -> http://127.0.0.1:8000/:path*"]);
  expect(await destinations("")).toEqual(["/api/:path* -> http://127.0.0.1:8000/:path*"]);
});

test("끝의 빗금은 출처의 일부로 읽고, 줄여 쓴 IPv4 는 정규화한 주소로 넘긴다", async () => {
  expect(await destinations("http://127.0.0.1:8100/")).toEqual([
    "/api/:path* -> http://127.0.0.1:8100/:path*",
  ]);
  expect(await destinations("http://127.1:8100")).toEqual([
    "/api/:path* -> http://127.0.0.1:8100/:path*",
  ]);
});

for (const upstream of ["http://0.0.0.0:8000", "http://[::1]:8000"]) {
  test(`${upstream} 상류는 설정을 읽는 자리에서 구성 오류로 끝난다`, async () => {
    await expect(loadConfig(upstream)).rejects.toThrow("AGENT_OS_UPSTREAM");
  });
}
