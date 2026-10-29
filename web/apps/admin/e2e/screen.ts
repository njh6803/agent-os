// 흐름들이 함께 쓰는 화면의 자리. 운영자가 보는 이름(역할과 글자)으로 찾는다.

import { expect, type Locator, type Page } from "@playwright/test";

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

/** 옆 탐색(좁은 폭에서는 위 막대)의 항목 하나로 간다. 이름은 "플러그인", "실행", "설정"이다. */
export async function openSection(page: Page, name: string): Promise<void> {
  await page.getByRole("navigation").getByRole("link", { name, exact: true }).click();
}

/**
 * 채널 토큰을 넣는다. 넣는 자리는 설정 화면에 있어(admin-style 티켓 04) 탐색으로 설정에 가서 넣고, 넣었다는 줄을 본 뒤
 * 브라우저의 뒤로 가기로 있던 화면에 돌아온다. 관리 토큰이 받아들여진 뒤에 부른다.
 */
export async function enterChannelToken(page: Page, token: string): Promise<void> {
  await openSection(page, "설정");
  await page.getByLabel("채널 토큰", { exact: true }).fill(token);
  await page.getByRole("button", { name: "채널 토큰 넣기", exact: true }).click();
  await expect(page.getByText("채널 토큰을 넣었다", { exact: true })).toBeVisible();
  await page.goBack();
}

/** 설정 화면의 토큰 지우기로 이 탭의 두 토큰을 지운다. 관리 토큰 넣기 화면으로 돌아간다. */
export async function clearTokens(page: Page): Promise<void> {
  await openSection(page, "설정");
  await page.getByRole("button", { name: "토큰 지우기", exact: true }).click();
}

/** 실행 하나의 결정 자리. */
export function decisionPlace(page: Page): Locator {
  return page.getByRole("region", { name: "결정", exact: true });
}
