// 읽기 흐름의 첫 조각. 관리 토큰을 넣고 플러그인 목록을 본다(web-admin 티켓 05). 실행 목록과 실행 하나는 runs.e2e.ts 가 잇는다.
// 실제 serve, 시작 래퍼로 띄운 실제 next start, 실제 중계(rewrites)를 지난다. 준비는 stack.ts 다.

import { expect, type Page, test } from "@playwright/test";
import { stack } from "./env";
import { enterAdminToken, row } from "./screen";

const TOKEN_FIELD_SEEN = "e2e: 관리 토큰 칸이 문서에 붙었다";

/** 그 탭의 브라우저 저장소 둘에 든 값 전부. */
function storedValues(page: Page): Promise<{ local: string[]; session: string[] }> {
  return page.evaluate(() => {
    const values = (storage: Storage): string[] => {
      const found: string[] = [];
      for (let index = 0; index < storage.length; index += 1) {
        const key = storage.key(index);
        found.push(key === null ? "" : (storage.getItem(key) ?? ""));
      }
      return found;
    };
    return { local: values(localStorage), session: values(sessionStorage) };
  });
}

test("관리 토큰을 넣으면 종류별로 묶인 플러그인 목록이 보이고 새로 고쳐도 남는다", async ({
  page,
}) => {
  const { adminUrl, adminToken } = stack();
  const printed: string[] = [];
  const crashes: string[] = [];
  page.on("console", (message) => printed.push(`${message.type()} ${message.text()}`));
  page.on("pageerror", (error) => crashes.push(error.message));
  // 문서가 읽히는 동안 관리 토큰 넣는 칸이 한 번이라도 붙으면 콘솔에 남긴다. 페이지를 읽을 때마다 새로 건다. 칸은
  // 운영자가 보는 이름(라벨)으로 찾는다. 채널 토큰의 칸도 가린 입력이고, 관리 토큰이 있으면 머리에 선다(티켓 08).
  await page.addInitScript((marker) => {
    let seen = false;
    const adminTokenField = (): boolean =>
      Array.from(document.querySelectorAll("label")).some(
        (label) =>
          label.textContent.startsWith("관리 토큰") &&
          label.querySelector('input[type="password"]') !== null,
      );
    new MutationObserver(() => {
      if (!seen && adminTokenField()) {
        seen = true;
        console.debug(marker);
      }
    }).observe(document, { childList: true, subtree: true });
  }, TOKEN_FIELD_SEEN);

  await page.goto(adminUrl);
  await enterAdminToken(page, "e2e-a-token-the-server-refuses");
  // Next 가 두는 경로 알림도 alert 라 글자로 거른다.
  await expect(page.getByRole("alert").filter({ hasText: "관리 토큰이 거부됐다" })).toBeVisible();

  await enterAdminToken(page, adminToken);

  await expect(row(page, "에이전트", "echo")).toContainText("켜짐");
  await expect(row(page, "에이전트", "broken")).toContainText("읽을 수 없는 매니페스트");
  await expect(row(page, "MCP", "fixture")).toContainText("켜짐");
  await expect(row(page, "스킬", "summarize")).toContainText("꺼짐");
  await expect(row(page, "스킬", "summarize")).toContainText("로더가 생기기 전에는 효과가 없다");
  await expect(row(page, "모델", "sonnet")).toContainText("로더가 생기기 전에는 효과가 없다");

  const beforeReload = printed.length;
  await page.reload();
  await expect(row(page, "에이전트", "echo")).toBeVisible();
  await expect(page.getByLabel("관리 토큰", { exact: true })).toHaveCount(0);
  // 토큰을 가진 운영자가 새로 고칠 때 넣는 칸이 번쩍이지 않는다. 서버가 미리 그린 HTML 에도 없다.
  expect(printed.slice(beforeReload).filter((line) => line.includes(TOKEN_FIELD_SEEN))).toEqual([]);

  const stored = await storedValues(page);
  expect(stored.local).toEqual([]);
  expect(stored.session.filter((value) => value.includes(adminToken))).toHaveLength(1);
  expect(page.url()).not.toContain(adminToken);
  expect(await page.content()).not.toContain(adminToken);
  expect(printed.join("\n")).not.toContain(adminToken);
  expect(printed.slice(0, beforeReload).some((line) => line.includes(TOKEN_FIELD_SEEN))).toBe(true);
  // 서버가 그린 첫 그림과 브라우저의 첫 그림이 어긋나면(hydration) 여기에 잡힌다.
  expect(crashes).toEqual([]);
  expect(printed.filter((line) => line.startsWith("error") && !line.includes("401"))).toEqual([]);

  await page.getByRole("button", { name: "토큰 지우기" }).click();
  await expect(page.getByLabel("관리 토큰", { exact: true })).toBeVisible();
  const cleared = await storedValues(page);
  expect(cleared.session.filter((value) => value.includes(adminToken))).toEqual([]);
});
