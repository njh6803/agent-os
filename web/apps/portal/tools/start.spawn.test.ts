// 질문 페이지의 시작 래퍼를 실제 프로세스로 띄운다. 인자의 판정은 start.test.ts 가, 설정과 사이트 파일을 대 보는 판정은
// server/load.test.ts 가 잰다. 여기서는 맞는 파일로 서버가 서서 시작 로그 한 줄을 찍고 `/portal/health` 에 답하는 것과,
// 어긋난 파일로는 서지 않고 stderr 의 진단과 종료 코드 1로 끝나는 것을 본다. 서버를 부르는 쪽도 `fetch` 가 아니라
// `node:http` 다(전역 `fetch` 금지). 운영체제별 명령에 기대지 않아 윈도우와 CI 의 ubuntu 에서 같이 돈다.

import { type ChildProcess, spawn, spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { request } from "node:http";
import { createServer, type Server } from "node:net";
import { join } from "node:path";
import { expect, test } from "vitest";
import { type ConfigDoc, writeSetup } from "../testing/fixtures.ts";

const START = join(import.meta.dirname, "start.ts");
// 프로세스가 뜨고 로그를 찍기까지의 상한. 다른 검사와 함께 돌아 느려질 때를 생각해 넉넉히 둔다.
const BOOT_TIMEOUT_MS = 30_000;

function close(server: Server): Promise<void> {
  return new Promise((resolve) => {
    server.close(() => {
      resolve();
    });
  });
}

/** 지금 비어 있는 루프백 포트 하나. 닫은 뒤 서버가 쓰므로 그 사이에 다른 프로세스가 가져갈 수 있다. */
async function freePort(): Promise<number> {
  const probe = createServer();
  await new Promise<void>((resolve) => probe.listen(0, "127.0.0.1", resolve));
  const address = probe.address();
  await close(probe);
  if (address === null || typeof address === "string") {
    throw new Error("빈 포트를 얻지 못했다");
  }
  return address.port;
}

function get(port: number, path: string): Promise<{ status: number; body: string }> {
  return new Promise((resolve, reject) => {
    const call = request({ host: "127.0.0.1", port, path, method: "GET" }, (response) => {
      let body = "";
      response.setEncoding("utf-8");
      response.on("data", (chunk: string) => (body += chunk));
      response.on("end", () => {
        resolve({ status: response.statusCode ?? 0, body });
      });
    });
    call.on("error", reject);
    call.end();
  });
}

/** 첫 stdout 줄까지 기다린다. 줄 전에 프로세스가 끝나면 거부한다. */
function firstLine(child: ChildProcess): Promise<string> {
  return new Promise((resolve, reject) => {
    let text = "";
    const timer = setTimeout(() => {
      reject(new Error(`시작 로그가 없다: ${text}`));
    }, BOOT_TIMEOUT_MS);
    child.stdout?.setEncoding("utf-8");
    child.stdout?.on("data", (chunk: string) => {
      text += chunk;
      const end = text.indexOf("\n");
      if (end >= 0) {
        clearTimeout(timer);
        resolve(text.slice(0, end));
      }
    });
    child.on("exit", (code) => {
      clearTimeout(timer);
      reject(new Error(`로그 전에 끝났다(코드 ${String(code)}): ${text}`));
    });
  });
}

function withPort(port: number): (doc: ConfigDoc) => void {
  return (doc) => void (doc.portal["port"] = port);
}

test("맞는 설정과 사이트 파일이면 시작 로그 한 줄을 찍고 health 에 답한다", async () => {
  const port = await freePort();
  const setup = writeSetup({ config: withPort(port) });
  const child = spawn(
    process.execPath,
    [START, "--config", setup.configPath, "--site-file", setup.siteFilePath],
    { stdio: ["ignore", "pipe", "pipe"] },
  );
  try {
    const line = await firstLine(child);

    expect(line).toBe(
      `질문 페이지가 http://127.0.0.1:${String(port)}/portal/ 에 섰다. 사이트 1개.`,
    );
    const health = await get(port, "/portal/health");
    expect(health.status).toBe(200);
    expect(JSON.parse(health.body)).toEqual({ status: "ok" });
    // 페이지와 정적 파일은 시작 때 지어 두었으므로 첫 요청부터 답한다.
    const page = await get(port, "/portal/");
    expect(page.status).toBe(200);
    expect(page.body).toContain("<agent-os-widget hidden>");
    expect((await get(port, "/portal/portal.js")).status).toBe(200);
    expect((await get(port, "/portal/theme.css")).body).toContain("--bg-raised");
    expect((await get(port, "/portal/nothing")).status).toBe(404);
  } finally {
    child.kill();
  }
});

/** 출력을 모아 서서 첫 줄을 찍은 뒤 끝낸다. `nodeFlags` 는 `package.json` 의 `start` 가 node 에 주는 인자다. */
async function runUntilListening(
  nodeFlags: readonly string[],
): Promise<{ stdout: string; stderr: string; port: number }> {
  const port = await freePort();
  const setup = writeSetup({ config: withPort(port) });
  const child = spawn(
    process.execPath,
    [...nodeFlags, START, "--config", setup.configPath, "--site-file", setup.siteFilePath],
    { stdio: ["ignore", "pipe", "pipe"] },
  );
  let stderr = "";
  child.stderr.setEncoding("utf-8");
  child.stderr.on("data", (chunk: string) => (stderr += chunk));
  try {
    const line = await firstLine(child);
    await get(port, "/portal/");
    await get(port, "/portal/theme.css");
    return { stdout: `${line}\n`, stderr, port };
  } finally {
    child.kill();
  }
}

test("실험 기능 경고만 끄고 시작하면 stderr 는 비고 stdout 은 시작 로그 한 줄이다", async () => {
  const run = await runUntilListening(["--disable-warning=ExperimentalWarning"]);

  expect(run.stderr).toBe("");
  expect(run.stdout.split("\n")).toEqual([
    `질문 페이지가 http://127.0.0.1:${String(run.port)}/portal/ 에 섰다. 사이트 1개.`,
    "",
  ]);
  // 키 파일의 글과 쿠키 이름이 출력에 실리지 않는다.
  expect(run.stdout + run.stderr).not.toMatch(/PRIVATE KEY|portal_anon/u);
});

test("package.json 의 start 가 실험 기능 경고를 끄는 인자를 node 에 준다", () => {
  const manifest = readFileSync(join(import.meta.dirname, "..", "package.json"), "utf-8");

  expect(manifest).toContain(
    '"start": "node --disable-warning=ExperimentalWarning tools/start.ts"',
  );
});

test("경고를 끄지 않으면 stderr 에 실험 기능 경고가 찍힌다(끄는 인자가 필요한 까닭)", async () => {
  const run = await runUntilListening([]);

  expect(run.stderr).toContain("ExperimentalWarning");
});

test("상대 경로로 준 파일을 래퍼를 부른 자리에서 찾는다", async () => {
  const port = await freePort();
  const setup = writeSetup({ config: withPort(port) });
  const child = spawn(
    process.execPath,
    [START, "--config", "portal.toml", "--site-file", "sites.toml"],
    {
      cwd: setup.dir,
      stdio: ["ignore", "pipe", "pipe"],
    },
  );
  try {
    expect(await firstLine(child)).toContain("에 섰다. 사이트 1개.");
  } finally {
    child.kill();
  }
});

test("에이전트가 틀리면 서지 않고 어긋난 자리를 stderr 에 찍고 종료 코드 1로 끝난다", () => {
  const setup = writeSetup({
    config: (doc) => {
      const [site] = doc.sites;
      if (site !== undefined) {
        site["agent"] = "wrong-agent";
      }
    },
  });

  const run = spawnSync(
    process.execPath,
    [START, "--config", setup.configPath, "--site-file", setup.siteFilePath],
    { encoding: "utf-8", timeout: BOOT_TIMEOUT_MS },
  );

  expect(run.status).toBe(1);
  expect(run.stdout).toBe("");
  expect(run.stderr.split("\n")).toEqual([
    "구성 오류:",
    "sites[0].agent: 사이트 파일이 그 사이트에 연 에이전트 밖이다",
    "",
  ]);
});

test("포트를 이미 다른 프로세스가 쥐고 있으면 서지 못한다고 알리고 종료 코드 1로 끝난다", async () => {
  const taken = createServer();
  await new Promise<void>((resolve) => taken.listen(0, "127.0.0.1", resolve));
  const address = taken.address();
  if (address === null || typeof address === "string") {
    throw new Error("포트를 얻지 못했다");
  }
  try {
    const setup = writeSetup({ config: withPort(address.port) });

    const run = spawnSync(
      process.execPath,
      [START, "--config", setup.configPath, "--site-file", setup.siteFilePath],
      { encoding: "utf-8", timeout: BOOT_TIMEOUT_MS },
    );

    expect(run.status).toBe(1);
    expect(run.stdout).toBe("");
    expect(run.stderr).toContain("질문 페이지를 열지 못했다");
  } finally {
    await close(taken);
  }
});

test("인자를 빠뜨리면 쓰는 법을 알리고 서지 않는다", () => {
  const run = spawnSync(process.execPath, [START], { encoding: "utf-8", timeout: BOOT_TIMEOUT_MS });

  expect(run.status).toBe(1);
  expect(run.stdout).toBe("");
  expect(run.stderr).toContain("--config");
});
