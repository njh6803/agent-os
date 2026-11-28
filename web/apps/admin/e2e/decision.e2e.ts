// 결정 흐름(web-admin 티켓 08, admin-login 티켓 11). 로그인한 계정이 대화 화면의 승인 묻기에서 멈춘 실행에 결정을 낸다.
// 실제 serve, 실제 중계, 실제 MCP 픽스처 서버를 지난다. 모델은 부르지 않는다. 픽스처 에이전트가 승인 대상 도구를
// `ctx.tool()` 로 직접 부른다(stack.ts). 멈춘 실행과 오래된 화면의 "다른 곳"은 흐름이 채널 토큰으로 보내는 화면 밖의
// 요청이다(channel.ts).
//
// 흐름들은 serve 하나를 파일 이름 차례로 함께 쓴다. 여기서 만든 대화는 뒤의 읽기 흐름(reading.e2e.ts)의 목록에도 선다.

import { expect, test } from "@playwright/test";
import { approve, startPausedRun } from "./channel";
import { stack } from "./env";
import { approvalAsk, signInTo } from "./screen";

test("멈춘 실행을 승인하면 재개 스트림이 조각으로 붙고 실행이 끝나며 도구가 실제로 불렸다", async ({
  page,
  request,
}) => {
  const { adminUrl } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  const paused = await startPausedRun(request, "gated");
  // 로그인하지 않은 채 대화 하나의 주소를 열면 로그인 화면으로 쫓겨나고, 로그인하면 그 대화로 돌아온다.
  await signInTo(page, `${adminUrl}/chat/${paused.runId}`);
  const turn = page.getByRole("region", { name: "실행 1", exact: true });
  const ask = approvalAsk(page);
  await expect(ask).toContainText("add");
  await expect(ask).toContainText('"a": 2');
  await ask.getByRole("button", { name: "승인", exact: true }).click();

  // 재개 스트림이 조각으로 온다. 승인했다는 줄이 결말보다 먼저 화면에 있다. 픽스처는 도구를 부른 뒤 2초 뒤에 끝난다.
  // 중계의 압축이 켜지면(`compress: false` 가 빠지면) 스트림이 끝에 몰려 와 여기서 빨개진다(web-admin 티켓 04).
  await expect(turn).toContainText("승인했다");
  await expect(turn).not.toContainText("끝남");
  await expect(ask).toHaveCount(0);

  // 스트림이 결말로 끝나면 실행이 끝남이 되고, 도구가 실제로 불린 것은 실행 패널의 tool_called 로 본다.
  await expect(turn).toContainText("끝남");
  await expect(turn).toContainText("도구 1개를 불렀다");
  await turn.getByRole("button", { name: "자세히" }).click();
  const panel = page.getByRole("complementary", { name: "실행 패널" });
  await expect(panel.getByRole("listitem").filter({ hasText: "tool_called" })).toContainText(
    /content\s*5/,
  );
  await expect(panel).toContainText("run_finished");
  expect(crashes).toEqual([]);
});

test("재개 스트림 도중에 떠나면 화면은 연결을 끊고 실행은 서버에서 끝까지 간다", async ({
  page,
  request,
}) => {
  // 페이지 테스트의 가짜 네트워크는 끊김을 핸들러에 잇지 않아(`.scratch/web-admin/probes/msw_abort.mjs`) 끊는 것을 실제
  // 브라우저에서 본다. 끊긴 fetch 는 requestfailed 다. 실행은 연결에 묶이지 않는다(ADR 0014, 스토리 45).
  const { adminUrl } = stack();
  const crashes: string[] = [];
  const cut: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  page.on("requestfailed", (failed) => {
    if (failed.url().endsWith("/approval")) {
      cut.push(failed.failure()?.errorText ?? "(이유 없음)");
    }
  });
  const paused = await startPausedRun(request, "gated");
  await signInTo(page, `${adminUrl}/chat/${paused.runId}`);
  await approvalAsk(page).getByRole("button", { name: "승인", exact: true }).click();
  const turn = page.getByRole("region", { name: "실행 1", exact: true });
  await expect(turn).toContainText("승인했다");

  // 픽스처가 끝나기(2초) 전에 대화 목록으로 떠난다.
  await page.getByRole("link", { name: "대화 목록", exact: true }).click();
  await expect(page).toHaveURL(`${adminUrl}/chat`);

  await expect.poll(() => cut).toEqual(["net::ERR_ABORTED"]);
  // 같은 대화를 다시 열면 서버에서 끝까지 간 실행이 끝남으로 읽힌다.
  await page.goto(`${adminUrl}/chat/${paused.runId}`);
  await expect(page.getByRole("region", { name: "실행 1", exact: true })).toContainText("끝남", {
    timeout: 15_000,
  });
  expect(crashes).toEqual([]);
});

test("오래된 화면에서 옛 일시정지를 승인하면 409 메시지와 새 일시정지가 보이고 둘째 도구는 불리지 않았다", async ({
  page,
  request,
}) => {
  const { adminUrl } = stack();
  const printed: string[] = [];
  const crashes: string[] = [];
  page.on("console", (message) => printed.push(`${message.type()} ${message.text()}`));
  page.on("pageerror", (error) => crashes.push(error.message));
  const first = await startPausedRun(request, "twice");
  await signInTo(page, `${adminUrl}/chat/${first.runId}`);
  const ask = approvalAsk(page);
  await expect(ask).toContainText('"a": 2');

  // 다른 곳(흐름의 요청)이 화면이 보는 일시정지를 먼저 승인한다. 실행은 둘째 승인 대상에서 다시 멈춘다.
  const second = await approve(request, first);
  await ask.getByRole("button", { name: "승인", exact: true }).click();

  // Next 가 페이지에 두는 경로 알림도 alert 라 글자로 거른다.
  await expect(
    page.getByRole("alert").filter({
      hasText: `결정이 가리킨 자리 ${String(first.pauseIndex)} 는 지금의 일시정지(자리 ${String(second.pauseIndex)})가 아니라`,
    }),
  ).toBeVisible();
  await expect(ask).toContainText('"a": 4');
  const turn = page.getByRole("region", { name: "실행 1", exact: true });
  await expect(turn).toContainText("도구 1개를 불렀다");
  expect(crashes).toEqual([]);
  // 브라우저는 실패한 응답을 콘솔 에러(Failed to load resource)로 찍는다. 409 는 이 흐름이 받는 것이고, 401 은 로그인하기 전에
  // 지금 누구인지와 갱신이 받는 것이다(로그인 화면으로 쫓겨나는 길).
  expect(
    printed.filter(
      (line) => line.startsWith("error") && !line.includes("409") && !line.includes("401"),
    ),
  ).toEqual([]);
});

test("375px 폭에서 승인 묻기의 버튼 둘이 위아래로 꽉 차고 거부가 먼저이며 승인이 된다", async ({
  page,
  request,
}) => {
  const { adminUrl } = stack();
  const crashes: string[] = [];
  page.on("pageerror", (error) => crashes.push(error.message));
  await page.setViewportSize({ width: 375, height: 812 });
  const paused = await startPausedRun(request, "gated");
  await signInTo(page, `${adminUrl}/chat/${paused.runId}`);
  const ask = approvalAsk(page);
  const deny = ask.getByRole("button", { name: "거부", exact: true });
  const approveButton = ask.getByRole("button", { name: "승인", exact: true });
  await expect(approveButton).toBeVisible();

  // 칸 폭이 360px 미만이라 둘이 위아래로 선다. 거부(보조)가 위, 승인(주)이 아래이고 폭이 같다.
  const denyBox = await deny.boundingBox();
  const approveBox = await approveButton.boundingBox();
  if (denyBox === null || approveBox === null) {
    throw new Error("버튼의 자리를 읽지 못했다");
  }
  expect(denyBox.y + denyBox.height).toBeLessThanOrEqual(approveBox.y);
  expect(denyBox.x).toBeCloseTo(approveBox.x, 0);
  expect(denyBox.width).toBeCloseTo(approveBox.width, 0);
  // 가로 스크롤이 생기지 않는다.
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
    ),
  ).toBe(true);

  await approveButton.click();
  await expect(page.getByRole("region", { name: "실행 1", exact: true })).toContainText("승인했다");
  expect(crashes).toEqual([]);
});
