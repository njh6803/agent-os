// 계정을 다루는 흐름(admin-login 티켓 12). 시스템 관리자가 계정을 만들어 비밀번호 링크를 받고, 그 링크로 로그인 없이 비밀번호를
// 정하고, 새 계정으로 로그인해 내 비밀번호를 바꾸고, 시스템 관리자가 그 계정을 비활성으로 바꾸면 로그인이 거절되는 데까지 간다.
// 실제 serve, 시작 래퍼로 띄운 실제 next start, 실제 중계(rewrites)를 지난다. 준비는 stack.ts 이고, 시스템 관리자 계정은 준비가
// `agent-os operator system-admin` 으로 만든 것이다. 새 계정은 흐름마다 이름이 다르다(같은 serve 를 다른 흐름과 함께 쓴다).

import { expect, type Page, test } from "@playwright/test";
import { stack } from "./env";
import { group, logIn, openSection, signInTo } from "./screen";

const FIRST_PASSWORD = "E2e-First1!pass";
const SECOND_PASSWORD = "E2e-Second2!pass";

/** 이 흐름에서만 쓰는 계정 이름. 규칙(소문자와 숫자로 시작, 3~32자)에 맞는다. */
function newAccountName(): string {
  return `e2e-${Date.now().toString(36)}`;
}

/** 계정 목록에서 이름이 든 줄(보이는 갈래의 표 행이나 카드). */
function accountRow(page: Page, name: string) {
  return group(page, "운영자 계정")
    .getByRole("row")
    .or(group(page, "운영자 계정").getByRole("listitem"))
    .filter({
      hasText: name,
    });
}

/** 비밀번호 정하기 화면의 두 칸을 채우고 보낸다. */
async function setPassword(page: Page, password: string): Promise<void> {
  await page.getByLabel("새 비밀번호", { exact: true }).fill(password);
  await page.getByLabel("새 비밀번호 다시", { exact: true }).fill(password);
  await page.getByRole("button", { name: "비밀번호 정하기", exact: true }).click();
}

test("시스템 관리자가 만든 계정은 링크로 비밀번호를 정해 로그인하고, 내 비밀번호를 바꾸고, 비활성이 되면 로그인하지 못한다", async ({
  page,
  browser,
}) => {
  const { adminUrl } = stack();
  const name = newAccountName();

  // 시스템 관리자가 계정을 만들고 링크를 받는다.
  await signInTo(page, `${adminUrl}/accounts`);
  await expect(page.getByRole("heading", { level: 1, name: "운영자 계정" })).toBeVisible();
  await page.getByRole("button", { name: "계정 만들기", exact: true }).click();
  const create = page.getByRole("dialog", { name: "계정 만들기" });
  await create.getByLabel("계정 이름", { exact: true }).fill(name);
  await create.getByRole("button", { name: "만들기", exact: true }).click();

  const linkDialog = page.getByRole("dialog", { name: `${name}의 비밀번호 링크` });
  await expect(linkDialog).toBeVisible();
  const address = (await linkDialog.locator("code").innerText()).trim();
  expect(address).toContain("/set-password#");
  await linkDialog.getByRole("button", { name: "닫기", exact: true }).click();
  await expect(linkDialog).toHaveCount(0);
  await expect(accountRow(page, name).first()).toContainText("비밀번호 미설정");

  // 링크는 로그인 없이 열린다. 다른 브라우저 창(쿠키가 따로 선다)에서 연다.
  const guest = await browser.newContext({ timezoneId: "Asia/Seoul", locale: "ko-KR" });
  try {
    const link = await guest.newPage();
    await link.goto(address);
    await expect(link.getByRole("heading", { level: 1, name: "비밀번호 정하기" })).toBeVisible();
    // 주소의 # 뒤(토큰)는 읽은 즉시 주소창에서 지워진다.
    await expect.poll(() => new URL(link.url()).hash).toBe("");
    await setPassword(link, FIRST_PASSWORD);
    await expect(link).toHaveURL(`${adminUrl}/login?notice=password-set`);

    // 같은 링크는 한 번만 쓰인다.
    await link.goto(address);
    await setPassword(link, SECOND_PASSWORD);
    await expect(
      link.getByRole("alert").filter({ hasText: "이 링크는 더 쓸 수 없다" }),
    ).toBeVisible();

    // 새 계정으로 로그인한다. 계정 자리에 이름과 단계가 보이고 "계정" 항목은 없다.
    await link.goto(`${adminUrl}/login`);
    await logIn(link, name, FIRST_PASSWORD);
    await expect(link.getByLabel("계정 이름", { exact: true })).toHaveCount(0);
    const account = link.getByRole("button", { name: new RegExp(name) });
    await expect(account).toContainText("관리자");
    await expect(
      link.getByRole("navigation").getByRole("link", { name: "계정", exact: true }),
    ).toHaveCount(0);

    // 관리자는 계정 화면을 열어도 볼 수 없다는 안내만 본다.
    await link.goto(`${adminUrl}/accounts`);
    await expect(link.getByText("이 계정으로는 볼 수 없다")).toBeVisible();

    // 내 비밀번호 바꾸기. 틀린 지금 비밀번호는 그 칸 아래에 알리고, 맞으면 바꿨다는 알림이 선다.
    await account.click();
    await link.getByRole("menuitem", { name: "내 비밀번호 바꾸기", exact: true }).click();
    await expect(link.getByRole("heading", { level: 1, name: "내 비밀번호 바꾸기" })).toBeVisible();
    await link.getByLabel("지금 비밀번호", { exact: true }).fill("E2e-Wrong9!pass");
    await link.getByLabel("새 비밀번호", { exact: true }).fill(SECOND_PASSWORD);
    await link.getByRole("button", { name: "비밀번호 바꾸기", exact: true }).click();
    await expect(link.getByLabel("지금 비밀번호", { exact: true })).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    await link.getByLabel("지금 비밀번호", { exact: true }).fill(FIRST_PASSWORD);
    await link.getByRole("button", { name: "비밀번호 바꾸기", exact: true }).click();
    await expect(link.getByRole("status").filter({ hasText: "비밀번호를 바꿨다" })).toBeVisible();
  } finally {
    await guest.close();
  }

  // 바뀐 비밀번호로만 로그인된다.
  const again = await browser.newContext({ timezoneId: "Asia/Seoul", locale: "ko-KR" });
  try {
    const second = await again.newPage();
    await second.goto(`${adminUrl}/login`);
    await logIn(second, name, FIRST_PASSWORD);
    await expect(second.getByRole("alert").filter({ hasText: "로그인하지 못했다" })).toBeVisible();
    await logIn(second, name, SECOND_PASSWORD);
    await expect(second.getByLabel("계정 이름", { exact: true })).toHaveCount(0);
  } finally {
    await again.close();
  }

  // 시스템 관리자가 그 계정을 비활성으로 바꾸면 목록에서 사라지고, 거르기를 켜면 비활성으로 보인다.
  await openSection(page, "실행");
  await openSection(page, "계정");
  const target = accountRow(page, name).first();
  await target.getByRole("button", { name: `${name}의 동작` }).click();
  await page.getByRole("menuitem", { name: "비활성으로 바꾸기", exact: true }).click();
  const disable = page.getByRole("dialog", { name: `${name}을 비활성으로 바꾼다` });
  await disable.getByRole("button", { name: "비활성으로 바꾸기", exact: true }).click();
  await expect(disable).toHaveCount(0);
  await expect(accountRow(page, name)).toHaveCount(0);
  await page.getByRole("switch", { name: "비활성 계정도 보기" }).check();
  await expect(accountRow(page, name).first()).toContainText("비활성");

  const last = await browser.newContext({ timezoneId: "Asia/Seoul", locale: "ko-KR" });
  try {
    const refused = await last.newPage();
    await refused.goto(`${adminUrl}/login`);
    await logIn(refused, name, SECOND_PASSWORD);
    await expect(refused.getByRole("alert").filter({ hasText: "로그인하지 못했다" })).toBeVisible();
  } finally {
    await last.close();
  }
});
