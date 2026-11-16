// 시험이 docker 와 compose 를 부르는 길. 명령의 출력은 받는 대로 모으고, 제한 시간을 넘기면 죽인다. 실패하면 명령과 출력을
// 오류에 싣는다. 인자에는 비밀 값을 싣지 않는다(토큰은 .env 로만 가고 시험이 HTTP 머리로 쓴다).

import { spawn } from "node:child_process";
import { join } from "node:path";
import { interpreter, REPO } from "@agent-os/e2e-stack";

export interface Outcome {
  readonly code: number | null;
  readonly stdout: string;
  readonly stderr: string;
  readonly timedOut: boolean;
}

export interface RunOptions {
  readonly cwd?: string;
  readonly env?: NodeJS.ProcessEnv;
  readonly timeoutMs: number;
}

// 제한 시간에 죽이고 나서 `close` 를 더 기다리는 상한.
const KILL_GRACE_MS = 10_000;

export function run(
  command: string,
  args: readonly string[],
  options: RunOptions,
): Promise<Outcome> {
  return new Promise((resolve) => {
    const child = spawn(command, args, {
      cwd: options.cwd,
      env: options.env ?? process.env,
      stdio: ["ignore", "pipe", "pipe"],
      windowsHide: true,
    });
    let stdout = "";
    let stderr = "";
    let timedOut = false;
    child.stdout.on("data", (chunk: Buffer) => (stdout += chunk.toString("utf-8")));
    child.stderr.on("data", (chunk: Buffer) => (stderr += chunk.toString("utf-8")));
    let hardStop: NodeJS.Timeout | undefined;
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill();
      // docker CLI 가 띄운 하위 프로세스가 파이프를 쥔 채 남으면 `close` 가 오지 않는다. 죽인 뒤 얼마 기다려도 안 오면
      // 강제로 죽이고 그 시점의 출력으로 끝낸다.
      hardStop = setTimeout(() => {
        child.kill("SIGKILL");
        // 하위 프로세스가 파이프를 쥔 채면 열린 파이프가 이 프로세스의 이벤트 루프를 붙잡으므로 부모 쪽 끝을 닫는다.
        child.stdout.destroy();
        child.stderr.destroy();
        resolve({ code: null, stdout, stderr, timedOut });
      }, KILL_GRACE_MS);
    }, options.timeoutMs);
    child.on("error", (error: Error) => {
      clearTimeout(timer);
      clearTimeout(hardStop);
      resolve({ code: null, stdout, stderr: `${stderr}\n[spawn 오류] ${error.message}`, timedOut });
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      clearTimeout(hardStop);
      resolve({ code, stdout, stderr, timedOut });
    });
  });
}

/** 종료 코드가 0 이 아니면 던진다. 성공하면 표준 출력을 준다. */
export async function succeed(
  command: string,
  args: readonly string[],
  options: RunOptions,
): Promise<string> {
  const outcome = await run(command, args, options);
  if (outcome.code !== 0) {
    const why = outcome.timedOut ? "제한 시간을 넘겨 죽였다" : `종료 ${String(outcome.code)}`;
    throw new Error(
      `${command} ${args.join(" ")} 이(가) ${why}:\n${outcome.stdout}\n${outcome.stderr}`,
    );
  }
  return outcome.stdout;
}

/**
 * 짓기 대상 이름(`serve` 등)에 대응하는 Docker Hub 저장소 이름을 읽는다. 대응은 `deploy/images/docker-bake.hcl` 한 곳이
 * 정하고 판 내기 워크플로도 같은 도구(`tools/release_ci.py repository`)로 읽는다.
 */
export async function repositoryName(target: string): Promise<string> {
  const printed = await succeed(interpreter(), ["tools/release_ci.py", "repository", target], {
    cwd: REPO,
    timeoutMs: 60_000,
  });
  return printed.trim();
}

/** 한 번 띄운 배치를 가리키는 compose 명령 묶음. 프로젝트 이름이 그 실행의 것이라 다른 실행의 것을 건드리지 않는다. */
export class Compose {
  readonly project: string;
  readonly dir: string;
  /** 모든 명령에 더하는 덧씌움 파일. 한 번만 쓰는 파일은 `call` 과 `ensure` 의 `files` 로 따로 준다. */
  readonly overlays: readonly string[];

  constructor(project: string, dir: string, overlays: readonly string[] = []) {
    this.project = project;
    this.dir = dir;
    this.overlays = overlays;
  }

  private args(files: readonly string[], rest: readonly string[]): string[] {
    return [
      "compose",
      "--project-name",
      this.project,
      "--project-directory",
      this.dir,
      "--file",
      join(this.dir, "compose.yaml"),
      ...[...this.overlays, ...files].flatMap((file) => ["--file", file]),
      ...rest,
    ];
  }

  /** 서비스 안에서 명령을 치고 표준 출력을 준다. 실패하면 던진다. */
  inService(service: string, command: readonly string[], timeoutMs = 60_000): Promise<string> {
    return succeed("docker", this.args([], ["exec", "-T", service, ...command]), {
      cwd: this.dir,
      timeoutMs,
    });
  }

  call(
    rest: readonly string[],
    timeoutMs: number,
    files: readonly string[] = [],
  ): Promise<Outcome> {
    return run("docker", this.args(files, rest), { cwd: this.dir, timeoutMs });
  }

  async ensure(
    rest: readonly string[],
    timeoutMs: number,
    files: readonly string[] = [],
  ): Promise<string> {
    return succeed("docker", this.args(files, rest), { cwd: this.dir, timeoutMs });
  }
}
