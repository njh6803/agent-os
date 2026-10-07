/**
 * 사진 비교의 로컬 명령(design-system 명세의 "사진 비교 게이트", ADR 0026). Storybook 정적 빌드를 호스트에서 짓고,
 * 판을 고정한 Playwright 이미지의 컨테이너에서 네트워크 없이 그 패키지의 `visual/` 을 돌린다. CI 는 이 스크립트를 쓰지
 * 않는다. 같은 이미지를 잡의 컨테이너로 쓰고 그 안에서 설치하고 짓고 비교한다(.github/workflows/ci.yml 의 visual 잡).
 *
 * - 컨테이너에 Playwright 패키지를 넣는 길: 그 패키지에 깔린 @playwright/test·playwright·playwright-core 를 pnpm
 *   링크를 풀어 임시 폴더로 복사하고 그 패키지의 node_modules 자리에 bind 한다. pnpm 의 링크(윈도우는 junction)는
 *   컨테이너 안에서 풀리지 않는다. 셋은 순수 JS 라(네이티브 파일 0개, 측정 visual_docker) 운영체제를 가리지 않는다.
 * - web/ 은 읽기 전용으로, 그 패키지의 visual/ 만 쓰기로 bind 한다. 비교의 산출물(test-results/)과 다시 만든 정답
 *   사진이 거기 쓰인다.
 * - 이미지는 태그에 digest 를 붙인다. 같은 태그가 다시 빌드되면 글꼴과 라이브러리가 바뀌어 코드 변경 없이 정답이
 *   깨질 수 있다. digest 는 잰 이미지의 linux/amd64 매니페스트다(이미지 ID `sha256:2c1f4e0fd645…`). index 의
 *   digest 는 호스트의 CPU 에 따라 다른 이미지로 풀린다. Playwright 판을 올리면 태그와 digest 를 함께 바꾼다.
 *   ci.yml 의 이미지와 설치된 Playwright 판이 이것과 맞는지는 visual.test.ts 가 본다.
 *
 * 사용: node tools/visual.ts <Storybook 패키지> [--update] [Playwright 인자 ...]. 패키지는 web/ 기준 경로이고
 * (`packages/ui`) 그 아래에 `build-storybook` 스크립트와 `visual/playwright.config.ts` 가 있어야 한다. --update 는
 * 정답과 다른 사진과 정답이 없는 사진을 컨테이너 안에서 다시 쓴다. 나머지 인자는 `playwright test` 에 그대로 간다
 * (`pnpm -C web visual -g atoms-button` 이 그 스토리들만 본다). Docker 가 없거나 비교가 실패하면 0 이 아닌 코드로
 * 끝난다(건너뛰지 않는다).
 */

import { spawnSync, type SpawnSyncReturns } from "node:child_process";
import { cpSync, mkdtempSync, realpathSync, rmSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join, relative, sep } from "node:path";

export const IMAGE =
  "mcr.microsoft.com/playwright:v1.63.0-noble@sha256:bc6ab0d6d44ff4826e4cb8c1e6d801e185bfc42bb0753f8e2a30efc70db054c7";

const WEB = dirname(import.meta.dirname);

/** `from` 에서 풀리는 패키지 `name` 의 실제 폴더(pnpm 링크를 푼 것). */
export function locatePackage(from: string, name: string): string {
  return realpathSync(
    dirname(createRequire(join(from, "package.json")).resolve(`${name}/package.json`)),
  );
}

/** 패키지에 깔린 Playwright 패키지 셋의 실제 폴더. 이름은 `@playwright/test`, `playwright`, `playwright-core` 다. */
export function playwrightPackages(packageDir: string): Record<string, string> {
  const test = locatePackage(packageDir, "@playwright/test");
  const playwright = locatePackage(test, "playwright");
  return {
    "@playwright/test": test,
    playwright,
    "playwright-core": locatePackage(playwright, "playwright-core"),
  };
}

/** Playwright 패키지 셋을 링크를 풀어 임시 폴더의 `node_modules` 로 복사하고 그 임시 폴더를 돌려준다. */
function copyPlaywright(packageDir: string): string {
  const staged = mkdtempSync(join(tmpdir(), "agent-os-visual-"));
  for (const [name, from] of Object.entries(playwrightPackages(packageDir))) {
    cpSync(from, join(staged, "node_modules", ...name.split("/")), {
      recursive: true,
      dereference: true,
      filter: (source) => !relative(from, source).split(sep).includes("node_modules"),
    });
  }
  return staged;
}

/** 컨테이너를 띄우는 `docker` 인자. `target` 은 web/ 기준 패키지 경로, `staged` 는 Playwright 를 복사한 폴더다. */
function containerArgs(
  target: string,
  staged: string,
  playwrightArgs: readonly string[],
): string[] {
  const inside = `/web/${target.split(/[\\/]/).join("/")}`;
  return [
    "run",
    "--rm",
    "--init",
    "--ipc=host",
    "--network",
    "none",
    "--mount",
    `type=bind,source=${WEB},target=/web,readonly`,
    "--mount",
    `type=bind,source=${join(staged, "node_modules")},target=${inside}/node_modules,readonly`,
    "--mount",
    `type=bind,source=${join(WEB, target, "visual")},target=${inside}/visual`,
    "--workdir",
    inside,
    IMAGE,
    "node",
    "node_modules/@playwright/test/cli.js",
    "test",
    "-c",
    "visual/playwright.config.ts",
    ...playwrightArgs,
  ];
}

/** 띄운 프로세스의 종료 코드. 띄우지 못했으면 그 이유를 쓰고 1 이다. */
function exitCode(result: SpawnSyncReturns<Buffer>, command: string): number {
  if (result.error !== undefined) {
    console.error(`${command} 를 띄우지 못했다: ${result.error.message}`);
    return 1;
  }
  return result.status ?? 1;
}

function buildStorybook(packageDir: string): number {
  // 윈도우의 pnpm 은 .cmd 라 셸로 띄운다. 인자는 고정이다.
  const build = spawnSync("pnpm run build-storybook", {
    cwd: packageDir,
    shell: true,
    stdio: "inherit",
  });
  return exitCode(build, "pnpm");
}

/** 정적 빌드를 짓고 컨테이너에서 `playwright test` 를 그 인자로 돌린다. 종료 코드를 돌려준다. */
function main(target: string, playwrightArgs: readonly string[]): number {
  const packageDir = join(WEB, target);
  console.log(`정적 빌드: ${target}`);
  const built = buildStorybook(packageDir);
  if (built !== 0) {
    console.error(`정적 빌드가 실패했다(${String(built)})`);
    return built;
  }
  console.log(`사진 비교: ${IMAGE} 에서 ${target} ${playwrightArgs.join(" ")}`);
  const staged = copyPlaywright(packageDir);
  try {
    const args = containerArgs(target, staged, playwrightArgs);
    return exitCode(spawnSync("docker", args, { cwd: packageDir, stdio: "inherit" }), "docker");
  } finally {
    rmSync(staged, { recursive: true, force: true });
  }
}

if (import.meta.main) {
  const [target, ...rest] = process.argv.slice(2);
  if (target === undefined || target.startsWith("-")) {
    console.error("사용: node tools/visual.ts <Storybook 패키지> [--update] [Playwright 인자 ...]");
    process.exit(2);
  }
  // --update 는 정답과 다른 사진과 없는 사진만 다시 쓴다. 나머지는 playwright test 의 인자다.
  const update = rest.includes("--update") ? ["--update-snapshots=changed"] : [];
  process.exit(main(target, [...update, ...rest.filter((arg) => arg !== "--update")]));
}
