// 결정 흐름(web-admin 티켓 08). 채널 토큰을 넣고 멈춘 실행에 결정을 낸다. 실제 serve, 실제 중계, 실제 MCP 픽스처
// 서버를 지난다. 모델은 부르지 않는다. 픽스처 에이전트가 승인 대상 도구를 `ctx.tool()` 로 직접 부른다(stack.ts). 멈춘
// 실행과 오래된 화면의 "다른 곳"은 흐름이 채널 토큰으로 보내는 화면 밖의 요청이다(channel.ts).
//
// 흐름들은 serve 하나를 파일 이름 차례로 함께 쓴다. 여기서 만든 실행은 뒤의 읽기 흐름(runs.e2e.ts)의 목록에도 선다.

import { expect, test } from "@playwright/test";
import { approve, startPausedRun } from "./channel";
import { stack } from "./env";
import { decisionPlace, enterAdminToken, enterChannelToken, row } from "./screen";

test("멈춘 실행을 허가하면 재개 스트림이 조각으로 붙고 실행이 끝나며 도구가 실제로 불렸다", async ({
  page,
  request,
}) => {
  const { adminUrl, adminToken, channelToken } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  const paused = await startPausedRun(request, "gated");
  await page.goto(`${adminUrl}/runs/${paused.runId}`);
  await enterAdminToken(page, adminToken);
  await expect(page.getByRole("region", { name: "이벤트" })).toContainText("run_paused");
  await expect(decisionPlace(page)).toHaveCount(0);

  await enterChannelToken(page, channelToken);
  const place = decisionPlace(page);
  await expect(place).toContainText("add");
  await expect(place).toContainText('"a": 2');
  await place.getByRole("button", { name: "허가", exact: true }).click();

  // 재개 스트림이 조각으로 온다. 첫 이벤트가 결말보다 먼저 화면에 있다. 픽스처는 도구를 부른 뒤 2초 뒤에 끝난다.
  // 중계의 압축이 켜지면(`compress: false` 가 빠지면) 스트림이 끝에 몰려 와 여기서 빨개진다(web-admin 티켓 04).
  const resumed = page.getByRole("region", { name: "재개 스트림" });
  await expect(resumed).toContainText("approval_granted");
  await expect(page.getByRole("main")).not.toContainText("run_finished");

  // 스트림이 결말로 끝나면 트레이스를 다시 읽는다. 도구가 실제로 불린 것은 트레이스의 tool_called 로 본다.
  const events = page.getByRole("region", { name: "이벤트" });
  await expect(events).toContainText("run_finished");
  await expect(events.getByRole("listitem").filter({ hasText: "tool_called" })).toContainText(
    /content\s*5/,
  );
  await expect(resumed).toHaveCount(0);
  await expect(place).toHaveCount(0);

  // 실행이 끝남으로 바뀐다. 상태의 이름은 목록의 요약이 말한다.
  await page.getByRole("link", { name: "실행 목록으로" }).click();
  await expect(row(page, "실행", paused.runId)).toContainText("끝남");
  expect(crashes).toEqual([]);
});

test("재개 스트림 도중에 떠나면 화면은 연결을 끊고 실행은 서버에서 끝까지 간다", async ({
  page,
  request,
}) => {
  // 페이지 테스트의 가짜 네트워크는 끊김을 핸들러에 잇지 않아(`.scratch/web-admin/probes/msw_abort.mjs`) 끊는 것을 실제
  // 브라우저에서 본다. 끊긴 fetch 는 requestfailed 다. 실행은 연결에 묶이지 않는다(ADR 0014, 스토리 45).
  const { adminUrl, adminToken, channelToken } = stack();
  const crashes: string[] = [];
  const cut: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  page.on("requestfailed", (failed) => {
    if (failed.url().endsWith("/approval")) {
      cut.push(failed.failure()?.errorText ?? "(이유 없음)");
    }
  });
  const paused = await startPausedRun(request, "gated");
  await page.goto(`${adminUrl}/runs/${paused.runId}`);
  await enterAdminToken(page, adminToken);
  await enterChannelToken(page, channelToken);
  await decisionPlace(page).getByRole("button", { name: "허가", exact: true }).click();
  await expect(page.getByRole("region", { name: "재개 스트림" })).toContainText("approval_granted");

  // 픽스처가 끝나기(2초) 전에 실행 목록으로 떠난다.
  await page.getByRole("link", { name: "실행 목록으로" }).click();

  await expect.poll(() => cut).toEqual(["net::ERR_ABORTED"]);
  const summary = row(page, "실행", paused.runId);
  await expect(async () => {
    await page.getByRole("button", { name: "새로 고침" }).click();
    await expect(summary).toContainText("끝남", { timeout: 1_000 });
  }).toPass({ timeout: 15_000 });
  expect(crashes).toEqual([]);
});

test("오래된 화면에서 옛 일시정지를 허가하면 409 메시지와 새 일시정지가 보이고 둘째 도구는 불리지 않았다", async ({
  page,
  request,
}) => {
  const { adminUrl, adminToken, channelToken } = stack();
  const printed: string[] = [];
  const crashes: string[] = [];
  page.on("console", (message) => printed.push(`${message.type()} ${message.text()}`));
  page.on("pageerror", (error) => crashes.push(error.message));
  const first = await startPausedRun(request, "twice");
  await page.goto(`${adminUrl}/runs/${first.runId}`);
  await enterAdminToken(page, adminToken);
  await enterChannelToken(page, channelToken);
  const place = decisionPlace(page);
  await expect(place).toContainText('"a": 2');

  // 다른 곳(흐름의 요청)이 화면이 보는 일시정지를 먼저 허가한다. 실행은 둘째 승인 대상에서 다시 멈춘다.
  const second = await approve(request, first);
  await place.getByRole("button", { name: "허가", exact: true }).click();

  // Next 가 페이지에 두는 경로 알림도 alert 라 글자로 거른다.
  await expect(
    page.getByRole("alert").filter({
      hasText: `결정이 가리킨 자리 ${String(first.pauseIndex)} 는 지금의 일시정지(자리 ${String(second.pauseIndex)})가 아니라`,
    }),
  ).toBeVisible();
  await expect(place).toContainText('"a": 4');
  const events = page.getByRole("region", { name: "이벤트" });
  await expect(events.getByRole("heading", { level: 4, name: "run_paused" })).toHaveCount(2);
  await expect(events.getByRole("heading", { level: 4, name: "tool_called" })).toHaveCount(1);
  expect(crashes).toEqual([]);
  // 브라우저는 실패한 응답을 콘솔 에러(Failed to load resource)로 찍는다. 409 는 이 흐름이 받는 것이다.
  expect(printed.filter((line) => line.startsWith("error") && !line.includes("409"))).toEqual([]);
});
