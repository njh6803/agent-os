// 플러그인 목록의 접속 확인이 실제 `serve` 와 실제 중계를 지나 행에 닿는다(connection-check 티켓 04). 이 e2e 의 `serve` 는
// 모델 제공사의 키를 받지 않는다(`stack.ts` 의 `serveEnv`). 그래서 켜 둔 모델 행은 제공사에 요청을 보내지 않고 키가 없다는
// 까닭을 보인다. 키가 있는 셸에서 돌려도 같은 글이 보여야 한다. 다른 장면이 플러그인 화면을 열 때마다 같은 확인이 나가므로,
// 이 장면이 그 확인이 제공사에 닿지 않는다는 것을 지킨다. 둘째 장면(티켓 05)은 실제로 붙는 원격 MCP 서버와 닿지 않는
// 모델 서버를 본다. 그 둘은 이 준비(`stack.ts`)가 띄운 가짜 원격 MCP 서버와, 닫힌 포트를 가리키는 `openai-compatible`
// 모델이고 어느 에이전트도 쓰지 않는다. 첫 확인의 결과만 보고 30초 간격의 다시 확인은 기다리지 않는다.

import { expect, test } from "@playwright/test";
import { stack } from "./env";
import { row, signInTo } from "./screen";

// 원격 MCP 서버와 모델의 확인 기한은 각각 10초다(`CHECK_DEADLINE_SECONDS`, `remote_check_seconds`). 그 기한과 중계를 지나는
// 시간을 넘게 넉넉히 두되 30초 간격은 넘지 않는다.
const FIRST_CHECK_MS = 25_000;

test("켜 둔 모델 행은 제공사에 요청을 보내지 않고 키가 없다는 까닭과 붙지 못함을 보이며 켜 둔 stdio 서버 행에는 접속 확인 버튼이 있다", async ({
  page,
}) => {
  const { adminUrl } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));

  await signInTo(page, adminUrl);

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

test("뜬 원격 MCP 서버의 행은 붙음을 보이고 닫힌 포트를 가리키는 모델의 행은 붙지 못함과 서버에 닿지 못했다를 보인다", async ({
  page,
}) => {
  // 기본 상한 30초는 페이지를 열고 로그인하는 시간에 첫 확인의 기다림(25초)을 더하면 빠듯하다. 실패가 시간 초과가 아니라 단언의
  // 글로 보이게 그 시간을 넉넉히 더한다.
  test.setTimeout(FIRST_CHECK_MS + 15_000);
  const { adminUrl } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));

  await signInTo(page, adminUrl);

  // 상태는 색이 아니라 글자로 찾는다. 붙음은 까닭 없이 글자 하나뿐이다. 두 확인은 화면을 열 때 함께 나가므로 두 행을 함께
  // 기다린다. 차례로 기다리면 첫 확인에 쓸 수 있는 시간이 둘로 늘어 30초 간격의 다시 확인 결과가 대신 통과시킬 수 있다.
  const remote = row(page, "MCP", "remote-docs");
  const offline = row(page, "모델", "offline-model");
  await Promise.all([
    expect(remote.getByRole("status")).toHaveText("붙음", { timeout: FIRST_CHECK_MS }),
    expect(offline.getByRole("status")).toContainText("붙지 못함", { timeout: FIRST_CHECK_MS }),
  ]);
  await expect(offline.getByRole("status")).toContainText("서버에 닿지 못했다");
  // 눌러서 하는 확인이 아니라 스스로 하는 확인이라 버튼이 없다.
  await expect(remote.getByRole("button", { name: "접속 확인" })).toHaveCount(0);
  expect(crashes).toEqual([]);
});
