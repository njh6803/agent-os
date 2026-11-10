import { expect, test } from "vitest";
import { launch, until } from "./process.ts";

test("없는 명령을 띄워도 러너가 죽지 않고 실패 이유가 출력에 남는다", async () => {
  const launched = launch("missing", "agent-os-e2e-no-such-command", [], process.cwd(), {});
  const waited = until(launched, "띄우지 못했다", () => null);
  await expect(waited).rejects.toThrow(/띄우지 못했다:\n[\s\S]*spawn 오류[\s\S]*ENOENT/);
});
