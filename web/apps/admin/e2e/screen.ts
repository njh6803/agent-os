// 흐름들이 함께 쓰는 화면의 자리. 운영자가 보는 이름(역할과 글자)으로 찾는다.

import type { Locator, Page } from "@playwright/test";

export function group(page: Page, heading: string): Locator {
  return page.getByRole("region", { name: heading });
}

export function row(page: Page, heading: string, name: string): Locator {
  return group(page, heading).getByRole("listitem").filter({ hasText: name });
}

export async function enterAdminToken(page: Page, token: string): Promise<void> {
  await page.getByLabel("관리 토큰", { exact: true }).fill(token);
  await page.getByRole("button", { name: "넣기" }).click();
}
