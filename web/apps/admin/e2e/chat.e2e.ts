// 대화를 읽는 흐름(admin-login 티켓 10). 채널 토큰으로 끝난 실행 하나를 만들고 거기서 이어 가기를 한 번 해 두 실행이 이어진
// 대화를 만든 뒤, 로그인한 운영자가 목록에서 그 대화를 찾아 열고 두 실행의 요청과 출력이 차례로 서는 것과 실행 패널이 열리고
// 닫히는 것을 본다. 모델은 부르지 않는다(픽스처 에이전트 echo 가 요청을 그대로 되돌려 끝낸다. stack.ts). 실행은 채널
// 요청이라 요청한 계정이 비고 목록은 그 자리에 주체를 보인다.

import { expect, test } from "@playwright/test";
import { continueRun, startFinishedRun } from "./channel";
import { stack } from "./env";
import { group, openSection, row, signInTo } from "./screen";

test("이어 가기를 한 두 실행이 대화 한 줄로 서고 열면 두 실행의 요청과 출력이 차례로 서며 패널이 열리고 닫힌다", async ({
  page,
  request,
}) => {
  const { adminUrl } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  const firstText = "대화 흐름의 첫 요청";
  const secondText = "대화 흐름의 둘째 요청";
  const first = await startFinishedRun(request, "echo", firstText);
  const second = await continueRun(request, first, "echo", secondText);

  await signInTo(page, adminUrl);
  await openSection(page, "대화");
  await expect(page).toHaveURL(`${adminUrl}/chat`);

  // 두 실행이 대화 한 줄이다. 줄은 대화의 첫 요청으로 서고 끝 실행의 대화 주소로 간다.
  const line = row(page, "대화", firstText);
  await expect(line).toHaveCount(1);
  await expect(line).toContainText("echo");
  await expect(line).toContainText("끝남");
  await expect(group(page, "대화")).not.toContainText(secondText);
  await line.getByRole("link", { name: firstText }).click();
  await expect(page).toHaveURL(`${adminUrl}/chat/${second}`);

  // 대화 화면에는 두 실행의 요청과 출력이 차례로 선다.
  const firstTurn = page.getByRole("region", { name: "실행 1", exact: true });
  const secondTurn = page.getByRole("region", { name: "실행 2", exact: true });
  await expect(firstTurn).toContainText(firstText);
  await expect(firstTurn).toContainText(`echo:${firstText}`);
  await expect(secondTurn).toContainText(secondText);
  await expect(secondTurn).toContainText(`echo:${secondText}`);

  // 실행 패널은 질의로 열리고 그 실행의 이벤트를 보이며, 닫으면 질의가 지워진다.
  await firstTurn.getByRole("button", { name: "자세히" }).click();
  await expect(page).toHaveURL(`${adminUrl}/chat/${second}?run=${first}`);
  const panel = page.getByRole("complementary", { name: "실행 패널" });
  await expect(panel).toBeVisible();
  await expect(panel).toContainText(first);
  await expect(panel).toContainText("run_finished");
  await panel.getByRole("button", { name: "닫기" }).click();
  await expect(panel).toHaveCount(0);
  await expect(page).toHaveURL(`${adminUrl}/chat/${second}`);
  expect(crashes).toEqual([]);
});
