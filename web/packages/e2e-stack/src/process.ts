// e2e 의 준비가 프로세스를 띄우고 기다리고 거두는 도우미. 위젯 e2e 의 준비(`apps/widget/e2e/stack.ts`)에서 옮겼다.
// 출력은 파이프에 쌓지 않고 받는 대로 모은다. 비우는 쪽이 없는 파이프는 차면 서버를 쓰기에서 세운다.

import { type ChildProcess, spawn } from "node:child_process";
import { connect, createServer } from "node:net";

const STARTUP_MS = 60_000;
const POLL_MS = 100;
const KILL_AFTER_MS = 10_000;

export interface Launched {
  readonly name: string;
  readonly child: ChildProcess;
  readonly output: () => string;
}

export function launch(
  name: string,
  command: string,
  args: readonly string[],
  cwd: string,
  env: NodeJS.ProcessEnv,
): Launched {
  const child = spawn(command, args, {
    cwd,
    env,
    stdio: ["ignore", "pipe", "pipe"],
    windowsHide: true,
  });
  let output = "";
  child.stdout.on("data", (chunk: Buffer) => (output += chunk.toString("utf-8")));
  child.stderr.on("data", (chunk: Buffer) => (output += chunk.toString("utf-8")));
  // 명령이 없으면 처리기가 없는 `error` 가 러너를 죽인다. 이유를 출력에 남겨 `until` 이 그것으로 실패하게 한다.
  child.on("error", (error: Error) => {
    output += `\n[spawn 오류] ${error.message}\n`;
  });
  return { name, child, output: () => output };
}

/** `check` 가 값을 줄 때까지 기다린다. 그 전에 프로세스가 끝나거나 상한을 넘기면 그 출력과 함께 실패한다. */
export async function until<T>(
  launched: Launched,
  failure: string,
  check: () => T | null | Promise<T | null>,
): Promise<T> {
  const deadline = Date.now() + STARTUP_MS;
  while (Date.now() < deadline) {
    const found = await check();
    if (found !== null) {
      return found;
    }
    // 신호로 죽으면 exitCode 는 null 이고 signalCode 만 찬다.
    if (launched.child.exitCode !== null || launched.child.signalCode !== null) {
      break;
    }
    await sleep(POLL_MS);
  }
  throw new Error(`${failure}:\n${launched.output()}`);
}

/** 비어 있는 루프백 포트. 닫은 뒤 곧바로 가져간다. */
export async function freePort(): Promise<number> {
  const server = createServer();
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const bound = server.address();
  await new Promise<void>((resolve) =>
    server.close(() => {
      resolve();
    }),
  );
  if (bound === null || typeof bound === "string") {
    throw new Error("빈 포트를 얻지 못했다");
  }
  return bound.port;
}

/** 그 루프백 포트가 연결을 받는지. */
export function accepts(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const socket = connect({ host: "127.0.0.1", port });
    socket.once("connect", () => {
      socket.destroy();
      resolve(true);
    });
    socket.once("error", () => {
      resolve(false);
    });
  });
}

/** 거두고 끝날 때까지 기다린다. 제때 끝나지 않으면 죽인다. */
export async function stop(child: ChildProcess): Promise<void> {
  if (child.exitCode !== null || child.signalCode !== null) {
    return;
  }
  const exited = new Promise<void>((resolve) =>
    child.once("exit", () => {
      resolve();
    }),
  );
  child.kill();
  const timer = setTimeout(() => child.kill("SIGKILL"), KILL_AFTER_MS);
  await exited;
  clearTimeout(timer);
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
