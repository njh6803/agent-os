// 위젯의 시작 래퍼를 실제 프로세스로 띄운다. 인자의 판정은 start.test.ts 가 잰다. 여기서는 거부가 next 를 띄우기 전에
// 끝나는지와, 래퍼가 푼 사이트 파일을 읽는지, 서비스 시작이 빌드 도구 없이 값 파일과 응답 머리 사본을 쓰고 next 를 부르는지,
// 빌드가 사이트 파일을 읽지 않고 원본을 남기는지를 본다. start 는 값 파일을 쓰려고 그 파일을 먼저 읽고(runtime.ts), 읽지
// 못하면 next 를 부르기 전에 끝난다.
//
// 저장소의 앱 폴더에 쓰지 않으려고 쓰는 사례는 래퍼 사본을 임시 앱 폴더에 두고 돌린다(testing/spawn-app.ts). 실제 Next 와 빌드
// 도구 대신 가짜를 세우는 불러오기 가로채기(testing/spawn-hooks.ts)를 건다. 이 이음매에서는 실제 `next build` 를 돌리지 않는다.
// 실제 빌드가 낸 목록과 실제 Next 가 사본을 읽는 것은 위젯 e2e 의 준비가 지난다. 운영체제별 명령에 기대지 않는다. 윈도우와 CI
// 의 ubuntu 에서 같이 돈다.

import { spawnSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, test } from "vitest";
import { CASES, expectSignals, nameOf } from "../testing/container-network.ts";
import { builtManifest } from "../testing/manifest.ts";
import { expectedSiteFile, SITE_FILE_FIXTURES } from "../testing/site-file.ts";
import { HOOKS, type SpawnedApp, spawnedApp } from "../testing/spawn-app.ts";

const START = join(import.meta.dirname, "start.ts");

/** 사이트 하나의 사이트 파일. 공개 키는 서버만 읽는 값이라 뜻을 보지 않는다. */
function siteText(origin: string): string {
  return [
    'schema_version = "1"',
    "[[sites]]",
    'issuer = "https://issuer.example"',
    'audience = "agent-os"',
    `allowed_origins = ["${origin}"]`,
    'agents = ["echo"]',
    "[[sites.public_keys]]",
    'pem = "서버만 읽는다"',
    "",
  ].join("\n");
}

const SITE_A = siteText("https://a.example");
const SITE_B = siteText("https://b.example");

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

// 사례 표(tests/fixtures/container_network/cases.json)의 거부 사례 가운데 표지 파일이 없는 것. 환경에서 온 값이 진입점까지
// 닿는지를 본다. 표지 파일은 `/etc` 에 있어 시험이 만들지 못하므로 있는 쪽은 start.test.ts 의 순수 판정이 본다. 받는 사례는
// next 가 떠서 스스로 끝나지 않으므로 띄우지 않는다.
for (const item of CASES.binding.filter(
  ({ marker, env, verdict }) => !marker && env !== undefined && verdict !== "ok",
)) {
  test(`환경에서 온 값이 진입점에서 거부된다: ${nameOf(item)}`, () => {
    const run = spawnSync(process.execPath, [START, "dev", "--hostname", item.host], {
      encoding: "utf-8",
      timeout: 30_000,
      env: { ...process.env, [CASES.envName]: item.env },
    });

    expect(run.status).toBe(1);
    expectSignals(run.stderr, CASES.bindingSignals, item);
    expect(run.stdout).toBe("");
  });
}

const BROKEN_SITE_FILE = 'schema_version = "1"\n[[sites]\n';

const created: string[] = [];

afterEach(() => {
  for (const folder of created.splice(0)) {
    rmSync(folder, { recursive: true, force: true, maxRetries: 5 });
  }
});

/** 부른 자리로 쓸 임시 폴더와 그 안의 사이트 파일. */
function operatorWith(siteFile: string, text: string): string {
  const operator = mkdtempSync(join(tmpdir(), "widget-start-"));
  created.push(operator);
  writeFileSync(join(operator, siteFile), text, "utf-8");
  return operator;
}

/** 가로채기를 건 임시 앱 폴더. 지우는 것은 시험이 끝난 뒤의 `afterEach` 다. */
function appUnderTest(): SpawnedApp {
  const spawned = spawnedApp();
  created.push(spawned.app);
  return spawned;
}

/** 빌드를 마친 산출물의 원본을 앱 폴더에 둔다. 서비스 시작이 읽는 것이다. */
function seedOriginal(app: string, frameAncestors?: string): void {
  mkdirSync(join(app, ".next"), { recursive: true });
  writeFileSync(
    join(app, ".next", "routes-manifest.original.json"),
    JSON.stringify(frameAncestors === undefined ? builtManifest() : builtManifest(frameAncestors)),
  );
}

function servedOf(app: string): unknown {
  return JSON.parse(readFileSync(join(app, ".next", "routes-manifest.json"), "utf-8"));
}

function valuesOf(app: string): unknown {
  return JSON.parse(readFileSync(join(app, "public", "runtime.json"), "utf-8"));
}

test("상대 경로로 준 사이트 파일을 서비스 시작이 래퍼를 부른 자리에서 찾고, 읽지 못하면 빌드 도구를 불러오기 전에 그 진단으로 끝난다", () => {
  // 값 파일을 쓰려고 사이트 파일을 읽다 멈추므로 next 를 띄우지 않는다. 저장소의 앱 폴더에서 돌므로 아무것도 쓰기 전에 끝나는
  // 사례여야 한다. 가로채기가 빌드 도구(Vite, Tailwind, TypeScript)와 그것을 부르는 모듈의 불러오기를 거절하는데, 래퍼가 처음
  // 불러오는 모듈이 그것을 정적으로 불러오면 사이트 파일의 진단이 아니라 그 거절로 끝난다.
  const operator = operatorWith("sites.toml", BROKEN_SITE_FILE);

  const run = spawnSync(process.execPath, ["--import", HOOKS, START, "start"], {
    cwd: operator,
    encoding: "utf-8",
    timeout: 30_000,
    env: { ...process.env, AGENT_OS_SITE_FILE: "sites.toml", WIDGET_TEST_TOOLS: "reject" },
  });

  expect(run.status).toBe(1);
  expect(run.stderr).toContain(`사이트 파일 ${join(operator, "sites.toml")} 을 받아들일 수 없다`);
  // 앱 폴더에서 풀었다면 "파일이 없다" 다.
  expect(run.stderr).toContain("TOML 이 아니다");
  expect(run.stderr).not.toContain("빌드 도구를 불러왔다");
  expect(run.stdout).toBe("");
});

describe("서비스 시작은 빌드 도구 없이 값 파일과 사본을 쓰고 next 를 부른다", () => {
  test("합친 허용 출처가 값 파일과 응답 머리 사본에 들고, 사본을 쓴 뒤에 next 를 부른다", () => {
    const { app, run } = appUnderTest();
    seedOriginal(app);
    const expected = expectedSiteFile();

    const result = run(["start"], {
      env: { AGENT_OS_SITE_FILE: join(SITE_FILE_FIXTURES, "sites.toml") },
    });

    expect(result.status).toBe(0);
    // 가로챈 next 가 받은 인자. 값 파일과 사본이 모두 쓰인 뒤에 불렸다.
    expect(result.stdout).toContain('NEXT-STUB ["start","--hostname","127.0.0.1"]');
    expect(result.stdout).toContain("위젯이 받은 값");
    expect(valuesOf(app)).toEqual({
      allowedOrigins: expected.allowedOrigins,
      requestChars: expected.requestChars,
    });
    expect(servedOf(app)).toEqual(
      builtManifest(`frame-ancestors ${expected.allowedOrigins.join(" ")}`),
    );
  });

  test("상대 경로로 준 사이트 파일도 래퍼를 부른 자리에서 찾는다", () => {
    const { app, run } = appUnderTest();
    seedOriginal(app);
    const operator = operatorWith(
      "sites.toml",
      readFileSync(join(SITE_FILE_FIXTURES, "sites.toml"), "utf-8"),
    );

    const result = run(["start"], { cwd: operator, env: { AGENT_OS_SITE_FILE: "sites.toml" } });

    expect(result.status).toBe(0);
    expect(servedOf(app)).toEqual(
      builtManifest(`frame-ancestors ${expectedSiteFile().allowedOrigins.join(" ")}`),
    );
  });

  test("사이트 파일을 바꿔 다시 띄우면 같은 원본에서 새 값을 쓴다. 다시 빌드하지 않는다", () => {
    const { app, run } = appUnderTest();
    seedOriginal(app);
    const first = operatorWith("a.toml", SITE_A);
    const second = operatorWith("b.toml", SITE_B);

    run(["start"], { env: { AGENT_OS_SITE_FILE: join(first, "a.toml") } });
    expect(servedOf(app)).toEqual(builtManifest("frame-ancestors https://a.example"));
    expect(valuesOf(app)).toEqual({ allowedOrigins: ["https://a.example"], requestChars: 20_000 });

    const again = run(["start"], { env: { AGENT_OS_SITE_FILE: join(second, "b.toml") } });

    expect(again.status).toBe(0);
    expect(servedOf(app)).toEqual(builtManifest("frame-ancestors https://b.example"));
    expect(valuesOf(app)).toEqual({ allowedOrigins: ["https://b.example"], requestChars: 20_000 });
  });

  test("사이트 파일의 변수를 주지 않으면 값 파일은 빈 값이고 사본은 아무도 품지 못하는 값이다", () => {
    const { app, run } = appUnderTest();
    seedOriginal(app);

    const result = run(["start"]);

    expect(result.status).toBe(0);
    expect(valuesOf(app)).toEqual({ allowedOrigins: [], requestChars: 20_000 });
    expect(servedOf(app)).toEqual(builtManifest());
  });

  test("변수가 비었으면 진단과 함께 끝나고 아무것도 쓰지 않는다", () => {
    const { app, run } = appUnderTest();
    seedOriginal(app);

    const result = run(["start"], { env: { AGENT_OS_SITE_FILE: "" } });

    expect(result.status).toBe(1);
    expect(result.stderr).toContain("AGENT_OS_SITE_FILE 가 비었다");
    expect(result.stdout).not.toContain("NEXT-STUB");
    expect(existsSync(join(app, "public", "runtime.json"))).toBe(false);
    expect(existsSync(join(app, ".next", "routes-manifest.json"))).toBe(false);
  });

  test("바꿀 자리가 기대와 다르면 사본을 쓰지 않고 next 를 부르지 않은 채 사이트 파일이 아닌 까닭으로 끝난다", () => {
    const { app, run } = appUnderTest();
    seedOriginal(app, "frame-ancestors https://decoy.example");

    const result = run(["start"], {
      env: { AGENT_OS_SITE_FILE: join(SITE_FILE_FIXTURES, "sites.toml") },
    });

    expect(result.status).toBe(1);
    expect(result.stderr).toContain("frame-ancestors https://decoy.example");
    expect(result.stderr).toContain("사이트 파일의 문제가 아니다");
    expect(result.stdout).not.toContain("NEXT-STUB");
    expect(existsSync(join(app, ".next", "routes-manifest.json"))).toBe(false);
  });

  test("원본이 없는 산출물이면 사본을 쓰지 않고 끝난다", () => {
    const { app, run } = appUnderTest();

    const result = run(["start"], {
      env: { AGENT_OS_SITE_FILE: join(SITE_FILE_FIXTURES, "sites.toml") },
    });

    expect(result.status).toBe(1);
    expect(result.stderr).toContain("원본");
    expect(result.stdout).not.toContain("NEXT-STUB");
    expect(existsSync(join(app, ".next", "routes-manifest.json"))).toBe(false);
  });
});

describe("빌드는 사이트 파일을 읽지 않고 원본을 남긴다", () => {
  test("읽지 못하는 사이트 파일을 주어도 그 진단 없이 끝나고, 빌드가 낸 목록을 원본으로 남긴다", () => {
    // 지금까지는 next 의 설정 파일이 사이트 파일을 읽다 이 진단으로 멈췄다. 이제 빌드는 그 파일을 읽지 않는다.
    const { app, run } = appUnderTest();
    const operator = operatorWith("sites.toml", BROKEN_SITE_FILE);

    const result = run(["build"], {
      cwd: operator,
      tools: "stub",
      env: { AGENT_OS_SITE_FILE: "sites.toml" },
    });

    expect(result.status).toBe(0);
    expect(result.stderr).not.toContain("사이트 파일");
    expect(result.stdout).toContain('NEXT-STUB ["build"]');
    // 가로챈 next 가 부른 줄이 돌아온 뒤에 목록을 남기고 `process.exit(0)` 으로 끝났다. 원본은 그 목록이다.
    expect(
      JSON.parse(readFileSync(join(app, ".next", "routes-manifest.original.json"), "utf-8")),
    ).toEqual(builtManifest());
    // 빌드는 값 파일을 쓰지 않는다.
    expect(existsSync(join(app, "public", "runtime.json"))).toBe(false);
  });

  test("빌드가 목록을 남기지 않았으면 종료 코드 1 로 끝난다", () => {
    const { app, run } = appUnderTest();

    const result = run(["build"], { tools: "stub", env: { WIDGET_TEST_BUILT_MANIFEST: "" } });

    expect(result.status).toBe(1);
    expect(result.stderr).toContain("응답 머리 목록을 남기지 않았다");
    expect(existsSync(join(app, ".next", "routes-manifest.original.json"))).toBe(false);
  });
});
