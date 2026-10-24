// 위젯 페이지 시험(widget-pages)이 함께 쓰는 조작. 질의를 준 iframe 페이지를 그리고, 요청을 적어 보내고, 최종 사용자
// 경로에 응답을 건다. 가짜는 HTTP(testing/network)와 부모 창(testing/site)뿐이다.

import { render, screen } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { http } from "msw";
import { WidgetPage } from "../components/pages/WidgetPage";
import { api, items, network } from "./network";

export const QUERY = new URLSearchParams({
  agent: "order-helper",
  heading: "주문 도우미",
}).toString();

export function openWidget(query = QUERY): UserEvent {
  window.history.replaceState(null, "", `/widget?${query}`);
  const user = userEvent.setup();
  render(<WidgetPage />);
  return user;
}

export function requestBox(): HTMLElement {
  return screen.getByRole("textbox", { name: "요청" });
}

export function sendButton(): HTMLElement {
  return screen.getByRole("button", { name: "보내기" });
}

/** 대화 목록에 선 출력. 읽기 영역의 같은 글과 가른다. */
export function findOutput(text: string): Promise<HTMLElement> {
  return screen.findByText(text, { selector: "ol p" });
}

export async function ask(user: UserEvent, text: string): Promise<void> {
  await user.type(requestBox(), text);
  await user.keyboard("{Enter}");
}

export interface Seen {
  readonly url: string;
  readonly authorization: string | null;
  readonly body: unknown;
}

/** 시작 경로에 응답을 걸고, 받은 요청을 차례로 적어 돌려준다. */
export function onStart(respond: () => Response): Seen[] {
  return onPost("/runs", respond);
}

/** 이어 가기 경로에 응답을 걸고, 받은 요청을 차례로 적어 돌려준다. */
export function onContinue(respond: () => Response): Seen[] {
  return onPost("/runs/:runId/continuation", respond);
}

/** 결정 경로에 응답을 걸고, 받은 요청을 차례로 적어 돌려준다. */
export function onDecide(respond: () => Response): Seen[] {
  return onPost("/runs/:runId/approval", respond);
}

export interface Subscribed {
  readonly url: string;
  readonly lastEventId: string | null;
}

/** 구독 경로에 응답을 걸고, 받은 요청의 주소와 `Last-Event-ID` 를 차례로 적어 돌려준다. */
export function onSubscribe(respond: () => Response): Subscribed[] {
  const seen: Subscribed[] = [];
  network.use(
    http.get(api("/runs/:runId/subscription"), ({ request }) => {
      seen.push({ url: request.url, lastEventId: request.headers.get("Last-Event-ID") });
      return respond();
    }),
  );
  return seen;
}

function onPost(path: string, respond: () => Response): Seen[] {
  const seen: Seen[] = [];
  network.use(
    http.post(api(path), async ({ request }) => {
      seen.push({
        url: request.url,
        authorization: request.headers.get("Authorization"),
        body: await request.json(),
      });
      return respond();
    }),
  );
  return seen;
}

export const FINISHED = () =>
  items({ type: "started", run_id: "run_1" }, { type: "finished", output: "도착 예정입니다." });
