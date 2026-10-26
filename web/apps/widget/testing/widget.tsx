// 위젯 페이지 시험(widget-pages)이 함께 쓰는 조작. 질의를 준 iframe 페이지를 그리고, 요청을 적어 보내고, 최종 사용자
// 경로에 응답을 건다. 가짜는 HTTP(testing/network)와 부모 창(testing/site)뿐이다.

import { act, cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import { http } from "msw";
import { vi } from "vitest";
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

/** 입력창 위 띠의 자리. 대화 뒤, 입력창 앞의 status 다. */
export function band(): HTMLElement {
  const statuses = screen.getAllByRole("status");
  const last = statuses.at(-1);
  if (
    last === undefined ||
    last.compareDocumentPosition(requestBox()) !== Node.DOCUMENT_POSITION_FOLLOWING
  ) {
    throw new Error("입력창 앞의 status 가 없다");
  }
  return last;
}

/** 화면 읽기 프로그램이 읽는 글. aria-hidden 인 것을 뺀다. */
export function spoken(element: Element): string {
  const copy = element.cloneNode(true);
  if (!(copy instanceof Element)) {
    throw new Error("요소가 아니다");
  }
  for (const hidden of copy.querySelectorAll('[aria-hidden="true"]')) {
    hidden.remove();
  }
  return copy.textContent;
}

/** 띠의 줄어드는 숫자. 화면 읽기 프로그램에서 숨는다. 같이 숨는 아이콘은 글이 없어 거른다. */
export function countdown(): string | null {
  const hidden = Array.from(
    band().querySelectorAll('[aria-hidden="true"]'),
    (element) => element.textContent,
  );
  return hidden.find((text) => text !== "") ?? null;
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
  readonly authorization: string | null;
  readonly lastEventId: string | null;
  /** 받은 시각(`Date.now()`). 가짜 시계에서 간격을 잰다. */
  readonly at: number;
}

/** 구독 경로에 응답을 걸고, 받은 요청의 주소와 토큰과 `Last-Event-ID` 를 차례로 적어 돌려준다. */
export function onSubscribe(respond: () => Response): Subscribed[] {
  const seen: Subscribed[] = [];
  network.use(
    http.get(api("/runs/:runId/subscription"), ({ request }) => {
      seen.push({
        url: request.url,
        authorization: request.headers.get("Authorization"),
        lastEventId: request.headers.get("Last-Event-ID"),
        at: Date.now(),
      });
      return respond();
    }),
  );
  return seen;
}

/** 위젯의 저장 키. 에이전트는 `QUERY` 의 것이다. */
export const STORAGE_KEY = "agent-os-widget:order-helper";

/**
 * 저장한 값이 `check` 를 지날 때까지 기다린다. 저장은 그린 뒤의 효과(`useEffect`)가 쓴다. 스트림이나 토큰 응답이 그린 글을
 * `findBy` 로 찾은 직후에는 그 커밋의 저장이 아직 밀려 있을 수 있어, 곧바로 읽으면 앞 판을 본다. 밀린 채 `reload` 하면
 * 걷기(`cleanup`)가 그 효과를 비워 시험이 고친 값을 덮는다. 부하를 건 탐침에서 기다리지 않으면 400회 가운데 7회 그랬고
 * 기다리면 400회 모두 지났다(일지 2026-10-26-01).
 */
export async function untilSaved(check: (saved: string | null) => void): Promise<void> {
  await waitFor(() => {
    check(sessionStorage.getItem(STORAGE_KEY));
  });
}

/** 같은 탭에서 새로 고친다. 그린 것을 걷고(열린 스트림도 끊긴다) 같은 질의로 다시 그린다. 저장은 남는다. */
export function reload(query = QUERY): UserEvent {
  cleanup();
  return openWidget(query);
}

/** 응답을 차례로 하나씩 낸다. 여러 경로가 함께 쓸 수 있다. */
export function inTurn(...responses: readonly (() => Response)[]): () => Response {
  let next = 0;
  return () => {
    const respond = responses[next];
    next += 1;
    if (respond === undefined) {
      throw new Error("준비한 응답보다 요청이 많다");
    }
    return respond();
  };
}

/** 가짜 시계를 `ms` 만큼 돌리고 그동안 생긴 일을 그린다. */
export async function advance(ms: number): Promise<void> {
  await act(async () => {
    await vi.advanceTimersByTimeAsync(ms);
  });
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
