// 사진 비교의 이미지 고정(visual.ts)의 테스트. 저장소 상태를 web/ 과 .github/ 에서 잰다. 이미지의 판은 Playwright
// 판과 함께 올리고(ADR 0026), 로컬 명령과 CI 잡이 같은 이미지를 쓴다.

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, expect, test } from "vitest";
import { IMAGE, locatePackage, playwrightPackages, workspaceLinks } from "./visual.ts";

const WEB = dirname(import.meta.dirname);
const CI = join(dirname(WEB), ".github", "workflows", "ci.yml");
const PINNED = /^mcr\.microsoft\.com\/playwright:v(\d+\.\d+\.\d+)-noble@sha256:[0-9a-f]{64}$/;

function versionOf(packageDir: string): string {
  const data: unknown = JSON.parse(readFileSync(join(packageDir, "package.json"), "utf-8"));
  if (
    typeof data !== "object" ||
    data === null ||
    !("version" in data) ||
    typeof data.version !== "string"
  ) {
    throw new Error(`${packageDir} 의 package.json 에 version 이 없다`);
  }
  return data.version;
}

describe("사진 비교의 이미지", () => {
  test("태그에 sha256 digest 를 붙여 고정한다", () => {
    expect(IMAGE).toMatch(PINNED);
  });

  test("태그의 판이 web 에 깔린 Playwright 패키지의 판과 모두 같다", () => {
    const installed = [
      ...Object.values(playwrightPackages(join(WEB, "packages", "ui"))),
      ...Object.values(playwrightPackages(join(WEB, "apps", "admin"))),
      ...Object.values(playwrightPackages(join(WEB, "apps", "widget"))),
      locatePackage(WEB, "playwright"),
    ];

    expect(new Set(installed.map(versionOf))).toEqual(new Set([PINNED.exec(IMAGE)?.[1]]));
  });

  test("CI 의 visual 잡이 같은 이미지를 잡의 컨테이너로 쓴다", () => {
    // 잡은 두 칸 들여쓴 `visual:` 줄부터 네 칸 이상 들여쓴 줄과 빈 줄이 이어지는 데까지다.
    const job = /^ {2}visual:\n((?: {4}.*\n|\n)*)/m.exec(readFileSync(CI, "utf-8"))?.[1] ?? "";

    expect(job).toContain(`    container:\n      image: ${IMAGE}\n`);
  });
});

describe("컨테이너 안의 워크스페이스 패키지", () => {
  test("위젯이 기대는 워크스페이스 패키지(생성 클라이언트, 디자인 시스템)를 컨테이너 안의 web/ 자리로 잇는다", () => {
    expect(workspaceLinks(join(WEB, "apps", "widget"))).toEqual({
      "@agent-os/api-client": "/web/packages/api-client",
      "@agent-os/ui": "/web/packages/ui",
    });
  });

  test("관리 화면이 기대는 워크스페이스 패키지(생성 클라이언트, 디자인 시스템)를 컨테이너 안의 web/ 자리로 잇는다", () => {
    expect(workspaceLinks(join(WEB, "apps", "admin"))).toEqual({
      "@agent-os/api-client": "/web/packages/api-client",
      "@agent-os/ui": "/web/packages/ui",
    });
  });

  test("워크스페이스 패키지에 기대지 않는 디자인 시스템 패키지는 이을 것이 없다", () => {
    expect(workspaceLinks(join(WEB, "packages", "ui"))).toEqual({});
  });
});
