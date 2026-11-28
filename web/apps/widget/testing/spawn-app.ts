// 시작 래퍼를 임시 앱 폴더에서 실제 프로세스로 돌리는 도구(tools/start.spawn.test.ts). 래퍼는 자기 위치의 위 폴더를 앱 폴더(`APP`)로
// 삼아 거기에 값 파일과 응답 머리 목록의 사본을 쓴다. 저장소의 앱 폴더에 쓰지 않으려고 래퍼와 그것이 부르는 두 파일을 임시 폴더에
// 복사해 돌린다. 불러오기 가로채기(spawn-hooks.ts)가 Next 와 빌드 도구를 가짜로 바꾼다.

import { type SpawnSyncReturns, spawnSync } from "node:child_process";
import { copyFileSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { builtManifest } from "./manifest.ts";

const TOOLS = join(import.meta.dirname, "..", "tools");
/** 불러오기 가로채기의 주소. `node --import <주소>` 로 건다. */
export const HOOKS = pathToFileURL(join(import.meta.dirname, "spawn-hooks.ts")).href;
const COPIED = ["start.ts", "manifest.ts", "runtime.ts"] as const;

export interface SpawnedApp {
  /** 임시 앱 폴더. */
  readonly app: string;
  /**
   * 래퍼를 띄운다. `env` 의 값이 undefined 이면 그 변수를 뺀다. 사이트 파일의 변수는 따로 주지 않으면 빠진다(바깥 환경의 값이
   * 시험에 새지 않는다). 가로챈 Next 가 빌드의 끝에 남길 목록은 `WIDGET_TEST_BUILT_MANIFEST` 로 바꿔 줄 수 있고 빈 값이면 남기지
   * 않는다.
   */
  readonly run: (
    args: readonly string[],
    options?: {
      readonly env?: Readonly<Record<string, string | undefined>>;
      readonly cwd?: string;
      readonly tools?: "reject" | "stub";
    },
  ) => SpawnSyncReturns<string>;
}

/** 래퍼 사본이 선 임시 앱 폴더. 지우는 것은 부른 시험이다. */
export function spawnedApp(): SpawnedApp {
  const app = mkdtempSync(join(tmpdir(), "widget-spawn-app-"));
  mkdirSync(join(app, "tools"));
  for (const name of COPIED) {
    copyFileSync(join(TOOLS, name), join(app, "tools", name));
  }
  const built = join(app, "built-manifest.json");
  writeFileSync(built, JSON.stringify(builtManifest()));
  return {
    app,
    run: (args, { env = {}, cwd = app, tools = "reject" } = {}) =>
      spawnSync(process.execPath, ["--import", HOOKS, join(app, "tools", "start.ts"), ...args], {
        cwd,
        encoding: "utf-8",
        timeout: 60_000,
        env: {
          ...process.env,
          AGENT_OS_SITE_FILE: undefined,
          WIDGET_TEST_TOOLS: tools,
          WIDGET_TEST_BUILT_MANIFEST: built,
          ...env,
        },
      }),
  };
}
