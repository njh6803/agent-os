// 플러그인 목록의 접속 확인이 실제 `serve` 와 실제 중계를 지나 행에 닿는다(connection-check 티켓 04). 이 e2e 의 `serve` 는
// 모델 제공사의 키를 받지 않는다(`stack.ts` 의 `serveEnv`). 그래서 켜 둔 모델 행은 제공사에 요청을 보내지 않고 키가 없다는
// 까닭을 보인다. 키가 있는 셸에서 돌려도 같은 글이 보여야 한다. 다른 장면이 플러그인 화면을 열 때마다 같은 확인이 나가므로,
// 이 장면이 그 확인이 제공사에 닿지 않는다는 것을 지킨다. 실제로 붙는 서버와 닿지 않는 서버를 보는 장면은 티켓 05 가 더한다.

import { expect, test } from "@playwright/test";
import { stack } from "./env";
import { enterAdminToken, row } from "./screen";

test("켜 둔 모델 행은 제공사에 요청을 보내지 않고 키가 없다는 까닭과 붙지 못함을 보이며 켜 둔 stdio 서버 행에는 접속 확인 버튼이 있다", async ({
  page,
}) => {
  const { adminUrl, adminToken } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  await page.goto(adminUrl);

  await enterAdminToken(page, adminToken);

  const sonnet = row(page, "모델", "sonnet");
  await expect(sonnet).toContainText("붙지 못함");
  await expect(sonnet).toContainText("키가 없다(환경 변수 ANTHROPIC_API_KEY)");
  // 기본 모델도 같다. 두 행 모두 실제 제공사에 닿지 않았다는 것이 이 글로 보인다.
  await expect(row(page, "모델", "claude-opus-5")).toContainText("키가 없다");
  // 서버를 띄우는 확인이라 stdio 서버 행은 누르기 전에는 아무것도 하지 않는다.
  const fixture = row(page, "MCP", "fixture");
  await expect(fixture.getByRole("button", { name: "접속 확인" })).toBeEnabled();
  await expect(fixture.getByRole("status")).toHaveCount(0);
  expect(crashes).toEqual([]);
});
