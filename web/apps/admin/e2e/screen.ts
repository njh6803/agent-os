// 흐름들이 함께 쓰는 화면의 자리. 운영자가 보는 이름(역할과 글자)으로 찾는다.

import { expect, type Locator, type Page } from "@playwright/test";
import { stack } from "./env";

export function group(page: Page, heading: string): Locator {
  return page.getByRole("region", { name: heading });
}

/**
 * 구역 안에서 그 글자가 든 줄. 플러그인 목록의 줄은 목록의 항목이고, 실행 목록의 줄은 넓은 본문 칸에서 표의 행, 좁은
 * 칸에서 카드(목록의 항목)다(admin-style 티켓 06). 숨은 갈래는 역할 조회에서 빠져 보이는 갈래의 줄만 걸린다.
 */
export function row(page: Page, heading: string, name: string): Locator {
  const place = group(page, heading);
  return place.getByRole("listitem").or(place.getByRole("row")).filter({ hasText: name });
}

/**
 * 로그인 화면의 입력 칸에 계정 이름과 비밀번호를 넣고 로그인을 누른다. 입력 칸이 선 화면에서 부른다. 로그인하지 않은 채
 * 어느 화면을 열면 로그인 화면(`/login?next=…`)으로 쫓겨나므로, 부르는 쪽은 `page.goto(주소)` 뒤에 이것을 부르면 된다.
 * 서버가 로그인을 받으면 화면은 쫓겨난 화면으로 돌아가고(전체 이동), 그 화면의 단언이 도착을 기다린다.
 */
export async function logIn(page: Page, name?: string, password?: string): Promise<void> {
  const account = stack();
  await page.getByLabel("계정 이름", { exact: true }).fill(name ?? account.accountName);
  await page.getByLabel("비밀번호", { exact: true }).fill(password ?? account.accountPassword);
  await page.getByRole("button", { name: "로그인", exact: true }).click();
}

/** 주소 하나를 열고 그 화면으로 로그인해 들어간다. 로그인한 뒤의 본문은 부르는 쪽이 단언으로 기다린다. */
export async function signInTo(page: Page, address: string): Promise<void> {
  await page.goto(address);
  await logIn(page);
  await expect(page.getByLabel("계정 이름", { exact: true })).toHaveCount(0);
}

/** 옆 탐색(좁은 폭에서는 위 막대)의 항목 하나로 간다. 이름은 "플러그인", "대화", "실행", "설정"이다. */
export async function openSection(page: Page, name: string): Promise<void> {
  await page.getByRole("navigation").getByRole("link", { name, exact: true }).click();
}

/** 실행 하나의 결정 자리. */
export function decisionPlace(page: Page): Locator {
  return page.getByRole("region", { name: "결정", exact: true });
}
