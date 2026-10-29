// 위젯을 품는 사이트(web-widget 명세 "임베드"의 두 방식). 위젯과 다른 출처에 선다. 같은 서버가 두 호스트 이름으로
// 불리며 출처 둘을 낸다. `site.localhost` 는 사이트 파일의 허용 출처이고 `other.localhost` 는 아니다.
//
// - `/` 는 iframe 위젯을 품은 페이지다. 질의 `agent` 가 위젯의 에이전트다. 위젯이 토큰을 물으면 이 서버의 `/token` 에서
//   받아 그 iframe 의 창에만 위젯 출처를 대상으로 답한다.
// - 질의 `intruders=1` 이면 페이지가 답하기 전에 끼어드는 iframe 둘(같은 허용 출처의 형제, 허용 밖 출처)이 같은 `id`
//   로 가짜 토큰을 위젯에 먼저 보낸다. 둘이 보냈다고 알린 뒤 0.5초를 더 기다려 페이지가 진짜 토큰을 보낸다. 위젯이
//   가짜를 받으면 401 이 되고, 버리면 진짜로 실행이 끝난다.
// - 질의 `sub` 가 있으면 페이지가 토큰마다 그 주체를 청한다. 없으면 토큰마다 새 주체다(token.ts). 위젯은 저장한 대화의
//   묶음(발급자와 주체)을 새로 받은 토큰과 견줘, 주체가 바뀌면 앞 사람의 대화로 보고 지운다. 그래서 새로 고친 뒤 다시
//   붙는 사례는 주체를 고정한다.
// - `/token` 은 사이트의 키로 서명한 새 토큰이다. 질의 `sub` 가 그 주체다. 시험이 서버에 직접 보내는 요청도 이것을 쓴다.
// - `/element` 와 그 아래는 페이지 안 방식의 페이지다(element-site.ts).
//
// iframe 페이지의 스크립트는 인라인이고 CSP 를 두지 않는다. CSP 를 다는 페이지는 페이지 안 방식의 한 판뿐이다.

import { createServer, type Server } from "node:http";
import { elementAnswer } from "./element-site";
import { signToken, type SiteKey } from "./token";

export const INTRUDER_TOKEN = "intruder-token";

/** 끼어드는 iframe 둘. 같은 허용 출처의 형제와 허용 밖 출처(`otherOrigin`)다. */
function intruderFrames(otherOrigin: string): string {
  return `<iframe class="intruder" title="형제" src="/intruder"></iframe>
<iframe class="intruder" title="남" src="${otherOrigin}/intruder"></iframe>`;
}

/** iframe 위젯을 품은 페이지. `nested` 는 위젯 iframe 뒤에 둘 끼어드는 iframe 의 마크업이고 없으면 빈 글이다. */
function page(widgetOrigin: string, agent: string, sub: string | null, nested: string): string {
  const widget = `${widgetOrigin}/widget?agent=${encodeURIComponent(agent)}`;
  const tokenPath = sub === null ? "/token" : `/token?sub=${encodeURIComponent(sub)}`;
  // 위젯 iframe 이 첫 프레임이어야 끼어드는 iframe 이 `parent.frames[0]` 으로 찾는다.
  return `<!doctype html>
<html lang="ko">
<head><meta charset="utf-8"><title>사이트</title></head>
<body>
<h1>사이트</h1>
<iframe id="widget" title="위젯" src="${widget}" style="width: 400px; height: 600px; border: 0"></iframe>
${nested}
<script>
const WIDGET = ${JSON.stringify(widgetOrigin)};
const frame = document.getElementById("widget");
const intruders = Array.from(document.querySelectorAll("iframe.intruder"));
function intrude(id) {
  return new Promise((resolve) => {
    let sent = 0;
    const onSent = (event) => {
      if (event.data && event.data.type === "e2e/intruded" && ++sent === intruders.length) {
        window.removeEventListener("message", onSent);
        resolve();
      }
    };
    window.addEventListener("message", onSent);
    for (const nested of intruders) {
      nested.contentWindow.postMessage({ type: "e2e/intrude", id }, "*");
    }
  });
}
window.addEventListener("message", async (event) => {
  const data = event.data;
  if (event.source !== frame.contentWindow || !data || data.type !== "agent-os/token-request") {
    return;
  }
  if (intruders.length > 0) {
    await intrude(data.id);
    // 끼어들기가 그 회차에 실제로 났다는 표지. 시험이 이것을 본다.
    document.body.dataset.intruded = String(intruders.length);
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  const token = await (await fetch(${JSON.stringify(tokenPath)})).text();
  frame.contentWindow.postMessage({ type: "agent-os/token", id: data.id, token }, WIDGET);
});
</script>
</body>
</html>
`;
}

function intruder(widgetOrigin: string): string {
  return `<!doctype html>
<html lang="ko">
<head><meta charset="utf-8"><title>끼어드는 프레임</title></head>
<body>
<script>
window.addEventListener("message", (event) => {
  const data = event.data;
  if (event.source !== window.parent || !data || data.type !== "e2e/intrude") {
    return;
  }
  window.parent.frames[0].postMessage(
    { type: "agent-os/token", id: data.id, token: ${JSON.stringify(INTRUDER_TOKEN)} },
    ${JSON.stringify(widgetOrigin)},
  );
  window.parent.postMessage({ type: "e2e/intruded" }, "*");
});
</script>
</body>
</html>
`;
}

export interface SiteOrigins {
  readonly widget: string;
  readonly other: string;
}

/** 그 포트의 루프백에 선 사이트 서버. */
export async function startSite(port: number, origins: SiteOrigins, key: SiteKey): Promise<Server> {
  const server = createServer((incoming, outgoing) => {
    const url = new URL(incoming.url ?? "/", "http://site.localhost");
    if (url.pathname === "/token") {
      outgoing.writeHead(200, {
        "Content-Type": "text/plain; charset=utf-8",
        "Cache-Control": "no-store",
      });
      outgoing.end(signToken(key, url.searchParams.get("sub") ?? undefined));
      return;
    }
    if (url.pathname === "/intruder") {
      outgoing.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      outgoing.end(intruder(origins.widget));
      return;
    }
    if (url.pathname === "/") {
      const agent = url.searchParams.get("agent") ?? "tools";
      const nested = url.searchParams.get("intruders") === "1" ? intruderFrames(origins.other) : "";
      outgoing.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      outgoing.end(page(origins.widget, agent, url.searchParams.get("sub"), nested));
      return;
    }
    const answer = elementAnswer(url, origins);
    if (answer !== null) {
      outgoing.writeHead(answer.status, answer.headers);
      outgoing.end(answer.body);
      return;
    }
    outgoing.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    outgoing.end("site: not found\n");
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(port, "127.0.0.1", resolve);
  });
  return server;
}
