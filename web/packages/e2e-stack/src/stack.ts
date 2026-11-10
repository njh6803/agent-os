// 준비 하나가 띄운 것을 모았다가 거두는 묶음. 준비(globalSetup)는 `createStack` 으로 묶음을 만들고 띄운 프로세스와 서버를
// 여기에 맡긴다. 준비가 던지거나 시험이 끝나면 `teardown` 이 서버를 닫고 프로세스를 거두고, 프로세스의 출력을 `logs` 에
// 남기고, 임시 작업 폴더를 지운다. 토큰과 개인 키는 출력에 싣지 않는 것이 띄우는 쪽의 몫이다.

import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import type { Server } from "node:http";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { type Launched, launch, stop } from "./process.ts";

export interface Stack {
  /** 준비가 쓰는 임시 작업 폴더. `teardown` 이 지운다. */
  readonly work: string;
  /** 프로세스를 띄워 묶음에 맡긴다. */
  launch(
    name: string,
    command: string,
    args: readonly string[],
    cwd: string,
    env: NodeJS.ProcessEnv,
  ): Launched;
  /** 서버를 묶음에 맡기고 그대로 돌려준다. */
  own(server: Server): Server;
  teardown(): Promise<void>;
}

export interface StackOptions {
  /** 임시 작업 폴더 이름의 머리. 앱마다 다르게 준다. */
  readonly prefix: string;
  /** 프로세스의 출력을 `<이름>.log` 로 남길 폴더. */
  readonly logs: string;
}

export function createStack(options: StackOptions): Stack {
  const work = mkdtempSync(join(tmpdir(), options.prefix));
  const launched: Launched[] = [];
  const servers: Server[] = [];
  return {
    work,
    launch(name, command, args, cwd, env) {
      const started = launch(name, command, args, cwd, env);
      launched.push(started);
      return started;
    },
    own(server) {
      servers.push(server);
      return server;
    },
    async teardown() {
      // 앞 단계가 던져도 임시 작업 폴더는 지워야 해서 `finally` 로 묶는다. 던진 오류는 그대로 올라간다.
      try {
        for (const server of servers.toReversed()) {
          await new Promise<void>((resolve) => {
            server.close(() => {
              resolve();
            });
            server.closeAllConnections();
          });
        }
        try {
          for (const { child } of launched.toReversed()) {
            await stop(child);
          }
        } finally {
          mkdirSync(options.logs, { recursive: true });
          for (const { name, output } of launched) {
            writeFileSync(join(options.logs, `${name}.log`), output());
          }
        }
      } finally {
        rmSync(work, { recursive: true, force: true, maxRetries: 5 });
      }
    },
  };
}
