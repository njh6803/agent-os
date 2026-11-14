// 다른 출처의 작은 페이지(pilot-portal 명세 "Playwright e2e"). 폼 하나가 위젯 미리보기 페이지의 고지 확인 끝점으로 POST 를 보낸다. 다른
// 출처에서 일으킨 확인 요청이 쿠키를 받지 못하는 것을 보는 사례(`acknowledge.e2e.ts`)가 쓴다.

import { createServer, type Server } from "node:http";

export interface OtherPageTarget {
  /** 위젯 미리보기 페이지의 공개 출처(중계의 주소). 폼이 여기로 POST 한다. */
  readonly portalOrigin: string;
  /** 확인을 보낼 사이트의 이름. */
  readonly siteName: string;
}

function html({ portalOrigin, siteName }: OtherPageTarget): string {
  const action = `${portalOrigin}/portal/sites/${siteName}/acknowledgement`;
  return [
    "<!doctype html>",
    '<html lang="ko">',
    '<meta charset="utf-8">',
    "<title>다른 출처의 페이지</title>",
    `<form id="acknowledge" method="post" action="${action}">`,
    '<button type="submit">고지를 확인했다고 보낸다</button>',
    "</form>",
    "",
  ].join("\n");
}

/** 그 포트의 루프백에 선 다른 출처의 페이지. */
export async function startOtherPage(port: number, target: OtherPageTarget): Promise<Server> {
  const body = html(target);
  const server = createServer((_incoming, outgoing) => {
    outgoing.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    outgoing.end(body);
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", resolve);
  });
  return server;
}
