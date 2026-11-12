// 브라우저가 하는 몫을 `node:http`·`node:https` 의 `request` 로 대신한다. 인가 요청 주소에서 시작해 넘김을 따라가다
// 돌아갈 주소(`redirectUri`)로 가는 넘김을 만나면 그 주소를 돌려준다. 그 주소로는 요청하지 않는다.
//
// 후보 ㄱ(직접 만든 서버)은 한 번에 돌려보낸다. 후보 ㄴ(`oidc-provider`)은 개발용 로그인 화면과 동의 화면을 거치므로,
// 200 으로 온 HTML 의 폼을 대신 내고 쿠키를 경로 범위대로 들고 다닌다. 프로브의 것이고 제품 코드가 아니다.

import { request as httpRequest } from "node:http";
import { request as httpsRequest } from "node:https";

export interface SignInOptions {
  readonly redirectUri: string;
  /** 로그인 화면에 적을 계정. ㄴ 에서는 이것이 `sub` 가 된다. */
  readonly accountId: string;
}

interface Page {
  readonly status: number;
  readonly location: string | undefined;
  readonly setCookies: readonly string[];
  readonly text: string;
}

interface StoredCookie {
  readonly value: string;
  readonly path: string;
}

const MAX_HOPS = 20;

function visit(
  url: URL,
  cookies: string,
  form: string | undefined,
): Promise<Page> {
  const request = url.protocol === "https:" ? httpsRequest : httpRequest;
  const headers: Record<string, string> = {};
  if (cookies !== "") {
    headers["Cookie"] = cookies;
  }
  if (form !== undefined) {
    headers["Content-Type"] = "application/x-www-form-urlencoded";
  }
  return new Promise((resolve, reject) => {
    const outgoing = request(
      url,
      { method: form === undefined ? "GET" : "POST", headers },
      (incoming) => {
        const chunks: Buffer[] = [];
        incoming.on("data", (chunk: Buffer) => {
          chunks.push(chunk);
        });
        incoming.on("error", reject);
        incoming.on("end", () => {
          resolve({
            status: incoming.statusCode ?? 0,
            location: incoming.headers.location,
            setCookies: incoming.headers["set-cookie"] ?? [],
            text: Buffer.concat(chunks).toString("utf8"),
          });
        });
      },
    );
    outgoing.on("error", reject);
    outgoing.end(form);
  });
}

function store(jar: Map<string, StoredCookie>, setCookies: readonly string[]): void {
  for (const line of setCookies) {
    const [pair, ...attributes] = line.split(";").map((piece) => piece.trim());
    const mark = pair?.indexOf("=") ?? -1;
    if (pair === undefined || mark < 0) {
      continue;
    }
    const name = pair.slice(0, mark);
    const value = pair.slice(mark + 1);
    const path =
      attributes.find((piece) => piece.toLowerCase().startsWith("path="))?.slice("path=".length) ??
      "/";
    const expires = attributes
      .find((piece) => piece.toLowerCase().startsWith("expires="))
      ?.slice("expires=".length);
    const expired = expires !== undefined && Date.parse(expires) <= Date.now();
    if (value === "" || expired) {
      jar.delete(`${name} ${path}`);
    } else {
      jar.set(`${name} ${path}`, { value, path });
    }
  }
}

function cookieHeader(jar: Map<string, StoredCookie>, url: URL): string {
  return [...jar.entries()]
    .filter(([, cookie]) => url.pathname.startsWith(cookie.path))
    .map(([key, cookie]) => `${key.split(" ")[0] ?? ""}=${cookie.value}`)
    .join("; ");
}

/** 개발용 화면의 폼 하나를 대신 낸다. 로그인 화면이면 계정을, 동의 화면이면 동의를 보낸다. */
function formFor(page: Page, options: SignInOptions): { action: string; body: string } {
  const action = /<form[^>]*action="([^"]+)"/u.exec(page.text)?.[1];
  if (action === undefined) {
    throw new Error(`폼이 없는 화면에서 멈췄다(상태 ${String(page.status)})`);
  }
  const login = page.text.includes('name="login"');
  const body = login
    ? new URLSearchParams({ prompt: "login", login: options.accountId, password: "probe" })
    : new URLSearchParams({ prompt: "consent" });
  return { action, body: body.toString() };
}

export async function signIn(authorizationUrl: string, options: SignInOptions): Promise<string> {
  const jar = new Map<string, StoredCookie>();
  let url = new URL(authorizationUrl);
  let form: string | undefined;
  for (let hop = 0; hop < MAX_HOPS; hop += 1) {
    const page = await visit(url, cookieHeader(jar, url), form);
    store(jar, page.setCookies);
    form = undefined;
    if (page.status >= 300 && page.status < 400 && page.location !== undefined) {
      const next = new URL(page.location, url);
      if (next.href.startsWith(options.redirectUri)) {
        return next.href;
      }
      url = next;
      continue;
    }
    if (page.status !== 200) {
      throw new Error(
        `로그인 서버가 ${String(page.status)} 로 답했다: ${page.text.slice(0, 300)}`,
      );
    }
    const filled = formFor(page, options);
    url = new URL(filled.action.replaceAll("&amp;", "&"), url);
    form = filled.body;
  }
  throw new Error("넘김이 너무 많다");
}
