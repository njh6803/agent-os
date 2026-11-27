// 파일 링크를 만들 수 있는 기계인지. 윈도는 권한이 없으면 만들지 못한다. 쓸 자리가 링크일 때의 쓰기를 보는 시험들
// (tools/runtime.test.ts, tools/manifest.test.ts)이 `test.skipIf` 에 쓴다.

import { mkdtempSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

/** 이 기계에서 파일 링크를 만들 수 있는가. */
export function canSymlink(): boolean {
  const dir = mkdtempSync(join(tmpdir(), "widget-symlink-probe-"));
  try {
    writeFileSync(join(dir, "a"), "");
    symlinkSync(join(dir, "a"), join(dir, "b"), "file");
    return true;
  } catch {
    return false;
  } finally {
    rmSync(dir, { recursive: true, force: true, maxRetries: 5 });
  }
}
