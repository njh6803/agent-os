// 전역 `fetch` 를 쓰지 않고 `node:http`·`node:https` 의 `request` 로 Fetch 모양의 함수를 낸다. 가(openid-client)와
// 나(oauth4webapi, jose)의 `customFetch` 자리에 넘겨, 라이브러리의 HTTP 가 전역 `fetch` 를 거치지 않게 할 수 있는지 잰다.
// 프로브의 것이고 제품 코드가 아니다. 응답 크기 상한과 재전송은 두지 않았다.

import { request as httpRequest } from "node:http";
import { request as httpsRequest } from "node:https";

export interface NodeFetchOptions {
  readonly method: string;
  readonly headers: Readonly<Record<string, string>> | Headers;
  readonly body?: ArrayBuffer | ReadableStream | Uint8Array | URLSearchParams | string | null;
  readonly signal?: AbortSignal;
}

let calls = 0;

/** 이 함수로 낸 요청 수. 회차가 "전역 `fetch` 가 아니라 이 길로 나갔다"는 표지로 읽는다. */
export function nodeFetchCalls(): number {
  return calls;
}

function plainHeaders(headers: NodeFetchOptions["headers"]): Record<string, string> {
  if (!(headers instanceof Headers)) {
    return { ...headers };
  }
  const plain: Record<string, string> = {};
  headers.forEach((value, name) => {
    plain[name] = value;
  });
  return plain;
}

function bodyBytes(body: NodeFetchOptions["body"]): Uint8Array | string | undefined {
  if (body === undefined || body === null) {
    return undefined;
  }
  if (typeof body === "string" || body instanceof Uint8Array) {
    return body;
  }
  if (body instanceof URLSearchParams) {
    return body.toString();
  }
  if (body instanceof ArrayBuffer) {
    return new Uint8Array(body);
  }
  throw new TypeError("스트림 본문은 보내지 않는다");
}

export function nodeFetch(url: string, options: NodeFetchOptions): Promise<Response> {
  calls += 1;
  const target = new URL(url);
  const request = target.protocol === "https:" ? httpsRequest : httpRequest;
  const headers = plainHeaders(options.headers);
  // URLSearchParams 본문은 fetch 가 붙여 주던 콘텐츠 타입을 손으로 붙인다.
  if (options.body instanceof URLSearchParams && headers["content-type"] === undefined) {
    headers["content-type"] = "application/x-www-form-urlencoded;charset=UTF-8";
  }
  const body = bodyBytes(options.body);
  return new Promise((resolve, reject) => {
    const outgoing = request(
      target,
      { method: options.method, headers, signal: options.signal },
      (incoming) => {
        const chunks: Buffer[] = [];
        incoming.on("data", (chunk: Buffer) => {
          chunks.push(chunk);
        });
        incoming.on("error", reject);
        incoming.on("end", () => {
          const responseHeaders = new Headers();
          for (const [name, value] of Object.entries(incoming.headers)) {
            for (const item of Array.isArray(value) ? value : [value]) {
              if (item !== undefined) {
                responseHeaders.append(name, item);
              }
            }
          }
          const status = incoming.statusCode ?? 0;
          const empty = status === 204 || status === 304;
          resolve(
            new Response(empty ? null : Buffer.concat(chunks), {
              status,
              headers: responseHeaders,
            }),
          );
        });
      },
    );
    outgoing.on("error", reject);
    outgoing.end(body);
  });
}
