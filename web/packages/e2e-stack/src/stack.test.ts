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

test("맡긴 정리 동작은 맡긴 순서의 거꾸로 부르고, 하나가 던져도 나머지를 부른 뒤 첫 오류를 알린다", async () => {
  const stack = createStack({ prefix: "e2e-stack-stack-work-", logs: join(folder, "logs") });
  const called: string[] = [];
  stack.cleanup(() => {
    called.push("첫째");
  });
  stack.cleanup(() => {
    called.push("둘째");
    throw new Error("둘째가 던졌다");
  });
  stack.cleanup(() => {
    called.push("셋째");
  });
  try {
    await expect(stack.teardown()).rejects.toThrow("둘째가 던졌다");
    expect(called).toEqual(["셋째", "둘째", "첫째"]);
    expect(existsSync(stack.work)).toBe(false);
  } finally {
    rmSync(stack.work, { recursive: true, force: true, maxRetries: 5 });
  }
});

test("로그를 쓰지 못해도 정리 동작은 부르고 임시 작업 폴더는 지운다", async () => {
  const blocked = join(folder, "not-a-folder");
  writeFileSync(blocked, "");
  const stack = createStack({ prefix: "e2e-stack-stack-work-", logs: blocked });
  let called = false;
  stack.cleanup(() => {
    called = true;
  });
  try {
    await expect(stack.teardown()).rejects.toThrow();
    expect(called).toBe(true);
    expect(existsSync(stack.work)).toBe(false);
  } finally {
    rmSync(stack.work, { recursive: true, force: true, maxRetries: 5 });
  }
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
