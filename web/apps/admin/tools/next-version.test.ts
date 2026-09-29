// 관리 화면의 중계는 Next 16.3.6 에서 쟀다. rewrites 가 빌드에 박히는지, IPv6 목적지를 컴파일하는지, 압축이 꺼지는지가
// 판마다 다를 수 있다(ADR 0011 의 2026-09-30 이력). 판을 바꾸는 쪽이 측정을 다시 돌게 하는 계기다. 문서의 한 줄은
// 강제력이 없어서 테스트로 둔다(CLAUDE.md 로드 시점 표).

import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
import { expect, test } from "vitest";

const MEASURED = "16.3.6";

test("설치된 Next 는 중계를 잰 판이다. 올리면 .scratch/web-admin/probes/admin_relay.mjs 를 다시 돌고 이 값을 고친다", () => {
  const path = createRequire(import.meta.url).resolve("next/package.json");
  const manifest: unknown = JSON.parse(readFileSync(path, "utf-8"));

  expect(
    typeof manifest === "object" && manifest !== null && "version" in manifest
      ? manifest.version
      : undefined,
  ).toBe(MEASURED);
});
