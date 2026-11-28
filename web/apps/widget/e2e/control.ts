/**
 * 위젯만 다시 띄우는 손잡이(widget-runtime-values 티켓 02). 위젯 e2e 의 준비(`stack.ts`, globalSetup)는 러너 프로세스에서 돌고
 * 위젯 프로세스를 그 안에서 쥔다. 사례는 그 뒤에 띄워진 워커에서 돌아 위젯을 잡을 길이 없다. 준비가 이 작은 서버를 열고 주소를
 * 환경 변수(`CONTROL_ENV`)로 넘기면, 사례가 요청 하나로 위젯을 새 사이트 파일로 다시 띄운다.
 *
 * - `POST /restart` 의 본문이 `{ "origin": "<출처>", "requestChars": <수> }` 이면 그 허용 출처와 상한을 적은 사이트 파일로,
 *   본문이 `{}` 이면 준비가 처음 준 사이트 파일로 다시 띄운다. 다시 띄우기 전에 앞 위젯을 끈다. 같은 앱 폴더의 값 파일과 사본을
 *   덮어쓰기 때문이다. 같은 포트에 서므로 중계는 그대로 이어진다.
 * - 루프백에만 선다. 사례들이 위젯 하나를 차례로 함께 쓰므로(`workers: 1`) 요청은 하나씩 온다.
 */

import { createServer, type Server } from "node:http";

/** 다시 띄울 사이트 파일에 적을 값. 둘 다 없으면 처음의 사이트 파일이다. */
export type RestartRequest = { readonly origin: string; readonly requestChars: number } | null;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** 요청 본문을 다시 띄울 값으로 읽는다. `{}` 는 처음의 사이트 파일이다. 모양이 맞지 않으면 던진다. */
export function parseRestart(body: string): RestartRequest {
  const parsed: unknown = JSON.parse(body);
  if (!isRecord(parsed)) {
    throw new Error("본문이 객체가 아니다");
  }
  const { origin, requestChars } = parsed;
  if (origin === undefined && requestChars === undefined) {
    return null;
  }
  if (typeof origin !== "string" || typeof requestChars !== "number") {
    throw new Error("origin(글자)과 requestChars(수)를 함께 주거나 둘 다 빼야 한다");
  }
  return { origin, requestChars };
}

/** 손잡이를 연다. `restart` 가 끝나야 요청에 답한다. 닫는 것은 부른 쪽이다. */
export async function startControl(
  restart: (request: RestartRequest) => Promise<void>,
): Promise<{ readonly server: Server; readonly url: string }> {
  const server = createServer((request, response) => {
    if (request.method !== "POST" || request.url !== "/restart") {
      response.writeHead(404).end();
      return;
    }
    const chunks: Buffer[] = [];
    request.on("data", (chunk: Buffer) => chunks.push(chunk));
    request.on("end", () => {
      void (async () => {
        try {
          await restart(parseRestart(Buffer.concat(chunks).toString("utf-8")));
          response.writeHead(204).end();
        } catch (error: unknown) {
          response
            .writeHead(500, { "content-type": "text/plain; charset=utf-8" })
            .end(error instanceof Error ? error.message : String(error));
        }
      })();
    });
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const bound = server.address();
  if (bound === null || typeof bound === "string") {
    throw new Error("손잡이가 설 포트를 얻지 못했다");
  }
  return { server, url: `http://127.0.0.1:${String(bound.port)}` };
}
