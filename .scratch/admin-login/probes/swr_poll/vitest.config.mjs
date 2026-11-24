// swr_poll 프로브의 vitest 설정. 앱의 테스트 묶음(web/vitest.config.ts)에 들지 않는다.
//
// 의존성은 이 설정을 읽는 vitest 가 놓인 web/ 의 관리 화면 앱(web/apps/admin)에서 푼다. 그래서 이 파일은
// 맨 이름(bare) import 를 하나도 하지 않는다. 설정을 읽는 쪽은 이 파일 옆에서 이름을 풀어 node_modules 를 찾지
// 못한다(이 폴더 위에 node_modules 가 없을 수 있다. 의존성을 깔지 않은 워크트리가 그렇다).
//
// - web/ 은 돌고 있는 vitest 의 경로(process.argv[1])에서 위로 올라가 apps/admin/package.json 이 든 첫 폴더다.
//   `pnpm -C web/apps/admin exec vitest` 로 띄워도, 다른 체크아웃의 `node <그 체크아웃>/web/node_modules/vitest/vitest.mjs`
//   로 띄워도 그 vitest 가 놓인 web/ 이다.
// - 이 폴더의 파일이 맨 이름으로 가져오는 것(swr, react, @testing-library/react, vitest)은 관리 화면 앱 폴더에서
//   가져온 것처럼 푼다(resolveId). 그 패키지들이 가져오는 것은 제 자리에서 평소대로 풀린다.
// - 캐시는 OS 임시 폴더에 둔다. 이 폴더와 앱의 node_modules 에 아무것도 쓰지 않는다.

import { existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const probeDir = dirname(fileURLToPath(import.meta.url));

function findWebDir() {
  let dir = dirname(resolve(process.argv[1] ?? ""));
  for (;;) {
    if (existsSync(join(dir, "apps", "admin", "package.json"))) {
      return dir;
    }
    const parent = dirname(dir);
    if (parent === dir) {
      throw new Error(
        `swr_poll: 돌고 있는 vitest(${process.argv[1]}) 위에서 apps/admin/package.json 이 든 web/ 을 찾지 못했다`,
      );
    }
    dir = parent;
  }
}

const webDir = findWebDir();
const appDir = join(webDir, "apps", "admin");
// 관리 화면 앱 폴더 안의 있지 않은 파일. 맨 이름을 이 파일이 가져온 것처럼 푼다.
const anchor = join(appDir, "__swr_poll_probe_anchor__.ts");

const norm = (p) => p.replace(/\\/g, "/").toLowerCase();
const probePrefix = `${norm(probeDir)}/`;

function isBare(id) {
  return !(
    id.startsWith(".") ||
    id.startsWith("/") ||
    id.startsWith("\0") ||
    id.startsWith("node:") ||
    id.startsWith("file:") ||
    id.startsWith("virtual:") ||
    /^[A-Za-z]:[\\/]/.test(id)
  );
}

const resolveFromAdmin = {
  name: "swr-poll-resolve-from-admin",
  enforce: "pre",
  async resolveId(source, importer, options) {
    if (importer === undefined || !isBare(source) || !norm(importer).startsWith(probePrefix)) {
      return null;
    }
    const resolved = await this.resolve(source, anchor, { ...options, skipSelf: true });
    if (resolved === null) {
      throw new Error(`swr_poll: ${source} 를 ${appDir} 에서 풀지 못했다`);
    }
    return resolved;
  },
};

export default {
  root: probeDir,
  cacheDir: join(tmpdir(), "agent-os-swr-poll-probe-vite"),
  plugins: [resolveFromAdmin],
  test: {
    include: ["poll.probe.ts"],
    environment: "jsdom",
    globals: false,
    // 통과한 실행에서도 afterAll 의 요약 줄(판, 회차 셈, 스냅샷 대조)을 찍는다. 2026-11-24 의 vitest 5.0.2 는 이것
    // 없이 통과한 파일의 console 출력을 내지 않았다(손으로 봤다).
    silent: false,
    fileParallelism: false,
    testTimeout: 300_000,
    hookTimeout: 60_000,
    env: { SWR_POLL_WEB_DIR: webDir, SWR_POLL_APP_DIR: appDir },
  },
};
