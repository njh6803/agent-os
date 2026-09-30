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
  await page.getByRole("button", { name: "넣기", exact: true }).click();
}

/** 채널 토큰을 넣는다. 넣는 자리는 관리 토큰이 받아들여진 뒤 머리에 선다. */
export async function enterChannelToken(page: Page, token: string): Promise<void> {
  await page.getByLabel("채널 토큰", { exact: true }).fill(token);
  await page.getByRole("button", { name: "채널 토큰 넣기", exact: true }).click();
}

/** 실행 하나의 결정 자리. */
export function decisionPlace(page: Page): Locator {
  return page.getByRole("region", { name: "결정", exact: true });
}
