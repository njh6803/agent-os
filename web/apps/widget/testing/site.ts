// 위젯을 품은 사이트의 흉내. iframe 의 부모 창이 토큰 요청에 답한다. jsdom 의 창은 맨 위 창이라 `window.parent` 가
// 자기 자신이다. 그래서 위젯이 부모에 보낸 토큰 요청은 같은 창의 message 사건으로 오고, 사이트의 답도 같은 창에
// 출처와 보낸 창을 정해 사건으로 넣는다.

export const SITE_ORIGIN = "https://shop.example";

export interface TokenRequest {
  readonly id: string;
}

const listeners: ((event: MessageEvent<unknown>) => void)[] = [];

/** 위젯의 토큰 요청마다 부른다. setup.ts 가 시험마다 걷는다. */
export function onTokenRequest(handle: (request: TokenRequest) => void): void {
  const listener = (event: MessageEvent<unknown>) => {
    const data = event.data;
    if (
      typeof data === "object" &&
      data !== null &&
      "type" in data &&
      data.type === "agent-os/token-request" &&
      "id" in data &&
      typeof data.id === "string"
    ) {
      handle({ id: data.id });
    }
  };
  listeners.push(listener);
  window.addEventListener("message", listener);
}

/** 위젯 창에 메시지 하나를 넣는다. 처음 값은 허용 출처의 부모 창이 보낸 것이다. */
export function post(
  data: unknown,
  from: { readonly origin?: string; readonly source?: Window | null } = {},
): void {
  window.dispatchEvent(
    new MessageEvent("message", {
      data,
      origin: from.origin ?? SITE_ORIGIN,
      source: from.source === undefined ? window : from.source,
    }),
  );
}

/** 토큰 요청마다 이 토큰으로 답한다. 받은 요청의 id 를 차례로 적어 돌려준다. */
export function serveTokens(token = "signed-token"): string[] {
  const ids: string[] = [];
  onTokenRequest(({ id }) => {
    ids.push(id);
    post({ type: "agent-os/token", id, token });
  });
  return ids;
}

export function removeTokenListeners(): void {
  for (const listener of listeners.splice(0)) {
    window.removeEventListener("message", listener);
  }
}
