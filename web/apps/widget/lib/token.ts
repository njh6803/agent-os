// iframe 방식의 토큰 손잡이(web-widget 명세 "임베드"의 iframe 방식). 위젯은 요청마다 부모 창에 토큰을 묻고, 사이트는
// 그 iframe 의 창에만 위젯 출처를 대상으로 답한다.
//
// - 묻는 메시지 `{type: "agent-os/token-request", id}` 에는 비밀이 없어 대상 출처를 "*" 로 둔다. iframe 이 부모의
//   출처를 모든 브라우저에서 미리 알 길이 없다. `id` 는 요청마다 새 무작위 문자열이다.
// - 받는 메시지는 보낸 창이 부모이고, 출처가 빌드에 든 허용 출처이며, `id` 가 기다리는 요청과 같은
//   `{type: "agent-os/token", id, token}` 뿐이다. 나머지는 버리고 계속 기다린다.
// - `token` 이 문자열이 아니면(거부를 뜻하는 null 따위) 받지 못한 것이다. 10초 안에 답이 없어도 같다.
// - `crypto.randomUUID` 는 보안 맥락(https, localhost)에만 있다. 그 밖에서 `id` 를 만들지 못하면 묻지 않고 받지 못한
//   것으로 끝낸다. 던지게 두면 부르는 쪽의 교환이 결말 없이 남는다.

export const TOKEN_TIMEOUT_MS = 10_000;

/** 받은 토큰. 받지 못했으면 null 이다. */
export type TokenResult = string | null;

export function requestToken(allowedOrigins: readonly string[]): Promise<TokenResult> {
  let id: string;
  try {
    id = crypto.randomUUID();
  } catch {
    return Promise.resolve(null);
  }
  const parent = window.parent;
  return new Promise((resolve) => {
    const finish = (token: TokenResult) => {
      window.clearTimeout(timer);
      window.removeEventListener("message", onMessage);
      resolve(token);
    };
    const onMessage = (event: MessageEvent<unknown>) => {
      if (event.source !== parent || !allowedOrigins.includes(event.origin)) {
        return;
      }
      const data = event.data;
      if (
        typeof data !== "object" ||
        data === null ||
        !("type" in data) ||
        data.type !== "agent-os/token" ||
        !("id" in data) ||
        data.id !== id
      ) {
        return;
      }
      finish("token" in data && typeof data.token === "string" ? data.token : null);
    };
    const timer = window.setTimeout(() => {
      finish(null);
    }, TOKEN_TIMEOUT_MS);
    window.addEventListener("message", onMessage);
    parent.postMessage({ type: "agent-os/token-request", id }, "*");
  });
}
