import { existsSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, beforeEach, expect, test } from "vitest";
import { createStack } from "./stack.ts";

let folder = "";

beforeEach(() => {
  folder = mkdtempSync(join(tmpdir(), "e2e-stack-stack-test-"));
});

afterEach(() => {
  rmSync(folder, { recursive: true, force: true, maxRetries: 5 });
});

test("로그를 쓰지 못해도 임시 작업 폴더는 지우고 그 오류는 그대로 알린다", async () => {
  // 로그 폴더 자리에 파일이 있어 폴더를 만들 수 없다.
  const blocked = join(folder, "not-a-folder");
  writeFileSync(blocked, "");
  const stack = createStack({ prefix: "e2e-stack-stack-work-", logs: blocked });
  const work = stack.work;
  try {
    await expect(stack.teardown()).rejects.toThrow();
    expect(existsSync(work)).toBe(false);
  } finally {
    rmSync(work, { recursive: true, force: true, maxRetries: 5 });
  }
});
