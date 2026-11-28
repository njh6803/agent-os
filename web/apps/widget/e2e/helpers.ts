// 위젯 e2e 의 사례 파일들이 함께 쓰는 도우미. iframe 사례(widget.e2e.ts)와 페이지 안 사례(element.e2e.ts)가 쓴다.

import {
  expect,
  type APIRequestContext,
  type FrameLocator,
  type Page,
  type Request,
} from "@playwright/test";
import { control } from "./env";

/**
 * 위젯만 다시 띄운다(`control.ts`). `site` 를 주면 그 허용 출처와 글자 수 상한을 적은 사이트 파일로, 주지 않으면 준비가 처음 준
 * 사이트 파일로 띄운다. 위젯이 다시 서고 값 파일과 응답 머리 사본을 새로 쓴 뒤에야 돌아온다.
 */
export async function restartWidget(
  request: APIRequestContext,
  site?: { readonly origin: string; readonly requestChars: number },
): Promise<void> {
  const response = await request.post(`${control()}/restart`, {
    data: site ?? {},
    timeout: 90_000,
  });
  expect(response.status(), await response.text()).toBe(204);
}

/** 위젯의 입력창에 요청을 넣고 보낸다. iframe 위젯이면 그 프레임을, 페이지 안 위젯이면 페이지를 준다. */
export async function send(scope: Page | FrameLocator, request: string): Promise<void> {
  await scope.getByRole("textbox", { name: "질문" }).fill(request);
  await scope.getByRole("button", { name: "보내기" }).click();
}

/** 그 페이지(iframe 포함)가 보낸 요청을 모은다. */
export function recordRequests(page: Page): Request[] {
  const requests: Request[] = [];
  page.on("request", (request) => {
    requests.push(request);
  });
  return requests;
}

/**
 * 시험 프로세스가 직접 부를 주소. `*.localhost` 를 루프백으로 푸는 것은 브라우저의 규칙이라(playwright.config.ts) node 의
 * 요청은 같은 포트의 127.0.0.1 로 보낸다.
 */
export function loopback(origin: string): string {
  const url = new URL(origin);
  url.hostname = "127.0.0.1";
  return url.origin;
}
