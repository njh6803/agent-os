// 켜고 끄기 흐름(web-admin 티켓 06). 스위치로 에이전트를 끄고 다시 켠다. 실제 serve 가 플러그인 루트의 운영자 파일에
// 쓰고, 화면은 다시 읽은 목록을 보인다. 준비는 stack.ts 다. 끄는 에이전트는 승인 대상 도구를 부르는 픽스처이고, 그
// 에이전트의 멈춘 실행에서 결정 버튼이 꺼짐에 막히고 켜짐에 풀린다(티켓 08). 멈춘 실행은 흐름이 채널 토큰으로 만든다.
// 화면은 로그인한 계정으로 들어간다(admin-login 티켓 09).
//
// 흐름들은 serve 하나를 차례로 함께 쓴다(playwright.config.ts). 끈 에이전트는 끝에 다시 켜서 뒤 흐름에 남기지 않는다.

import { expect, type Page, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { startPausedRun } from "./channel";
import { stack } from "./env";
import { approvalAsk, group, openSection, row, signInTo } from "./screen";

/** 운영자 파일이 꺼 둔 에이전트의 이름들. 파일은 종류마다 한 줄이다(준비가 쓴 것도, serve 가 쓰는 정규형도). */
function disabledAgents(pluginsRoot: string): string[] {
  const text = readFileSync(join(pluginsRoot, "disabled.toml"), "utf-8");
  const items = /^agent = \[(.*)\]$/m.exec(text)?.[1];
  if (items === undefined) {
    throw new Error(`운영자 파일에 agent 줄이 없다:\n${text}`);
  }
  return Array.from(items.matchAll(/"([^"]*)"/g), (match) => match[1] ?? "");
}

/**
 * 탐색의 링크로 멈춘 실행의 대화를 연다. 주소를 새로 읽지 않아 SWR 의 캐시(플러그인 목록)가 이어진다. 대화 목록의 줄은
 * 요청 글로 서는데 같은 요청의 대화가 여럿이라, 그 대화의 주소(끝 실행이 멈춘 실행 자신이다)로 찾는다. 목록은 표와 좁은
 * 폭의 줄을 함께 그려 같은 주소의 링크가 둘이라 보이는 쪽만 고른다.
 */
async function openPausedRun(page: Page, runId: string): Promise<void> {
  await openSection(page, "대화");
  await group(page, "대화").locator(`a[href="/chat/${runId}"]:visible`).click();
  await expect(approvalAsk(page)).toBeVisible();
}

test("스위치로 에이전트를 끄면 운영자 파일에 적히고 목록이 꺼짐을 보이며 그 에이전트의 멈춘 실행에서 결정 버튼이 막히고 다시 켜면 풀린다", async ({
  page,
  request,
}) => {
  const { adminUrl, pluginsRoot } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  const paused = await startPausedRun(request, "gated");
  await signInTo(page, adminUrl);
  const gated = row(page, "에이전트", "gated");
  await expect(gated).toContainText("켜짐");
  expect(disabledAgents(pluginsRoot)).toEqual([]);

  await gated.getByRole("switch").click();

  await expect(gated).toContainText("꺼짐");
  await expect(gated.getByRole("switch")).not.toBeChecked();
  expect(disabledAgents(pluginsRoot)).toEqual(["gated"]);

  // 그 에이전트의 멈춘 실행에서는 결정 버튼이 막히고 무엇이 꺼졌는지 보인다. 누르면 어차피 409 다(스토리 50).
  await openPausedRun(page, paused.runId);
  await expect(approvalAsk(page)).toContainText(
    "꺼진 플러그인이 있어 재개할 수 없다: 에이전트 gated",
  );
  await expect(approvalAsk(page).getByRole("button", { name: "승인", exact: true })).toBeDisabled();
  await openSection(page, "플러그인");

  // 열어 보면 서버가 읽은 꺼짐과 매니페스트가 보인다. 목록의 "매니페스트" 링크와 플러그인 하나의 라우트를 실제 Next
  // 로 지난다.
  await gated.getByRole("link", { name: "매니페스트" }).click();
  await expect(page).toHaveURL(`${adminUrl}/plugins/agent/gated`);
  await expect(page.getByRole("region", { name: "매니페스트" })).toContainText(
    '"entrypoint": "agent:Agent"',
  );
  await expect(page.getByRole("main")).toContainText("꺼짐");
  await page.getByRole("link", { name: "플러그인 목록", exact: true }).click();

  await gated.getByRole("switch").click();

  await expect(gated).toContainText("켜짐");
  await expect(gated.getByRole("switch")).toBeChecked();
  expect(disabledAgents(pluginsRoot)).toEqual([]);

  await openPausedRun(page, paused.runId);
  await expect(approvalAsk(page).getByRole("button", { name: "승인", exact: true })).toBeEnabled();
  await expect(approvalAsk(page)).not.toContainText("꺼진 플러그인");
  expect(crashes).toEqual([]);
});

test("이름이 패턴 밖인 표지를 열면 주소의 조각이 풀린 이름과 422 봉투의 메시지가 보인다", async ({
  page,
}) => {
  // 목록의 링크는 이름을 조각으로 적는다. 라우트가 넘기는 조각이 풀린 이름인지는 실제 Next 에서만 잰다.
  const { adminUrl } = stack();
  await signInTo(page, adminUrl);
  const odd = row(page, "에이전트", "Old Calc");
  await expect(odd).toContainText("디렉터리 이름이 플러그인 이름의 패턴을 어긴다");

  await odd.getByRole("link", { name: "매니페스트" }).click();

  await expect(page).toHaveURL(`${adminUrl}/plugins/agent/Old%20Calc`);
  await expect(page.getByRole("heading", { level: 1, name: "Old Calc" })).toBeVisible();
  // Next 가 페이지에 두는 경로 알림도 alert 라 글자로 거른다.
  await expect(
    page.getByRole("alert").filter({ hasText: "요청의 형식이 올바르지 않다" }),
  ).toBeVisible();
});
