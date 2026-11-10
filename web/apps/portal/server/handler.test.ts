// HTTP 요청 처리기. 순수 함수라 요청을 값으로 만들어 부른다. 시계와 UUID 만들기는 시험이 고정한다. 실제 소켓은 e2e 가 지난다.

import { createHash, createPrivateKey, createPublicKey, verify } from "node:crypto";
import { expect, test } from "vitest";
import { rsaKey, testAssets } from "../testing/fixtures.ts";
import type { Cookie } from "./cookies.ts";
import { handle, type PortalRequest, type PortalResponse } from "./handler.ts";
import type { PortalContext } from "./context.ts";

const ORIGIN = "http://portal.localhost:8080";
const ID = "3f2b8c1e-5d4a-4e7b-9a6c-0d1e2f3a4b5c";
const OTHER_ID = "9c1d7e22-0b3f-4a58-8d2e-6f4a1b9c3d70";
const FRESH_ID = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee";
const NOW_MS = 1_800_000_000_000;
const LOGIN_NOTICE = "이 사이트는 로그인이 필요합니다. 로그인은 아직 제공하지 않습니다.";

function context(overrides: Partial<PortalContext> = {}): PortalContext {
  return {
    publicOrigin: ORIGIN,
    kid: "portal-1",
    privateKey: createPrivateKey(rsaKey().pkcs8),
    sites: [
      {
        name: "demo",
        issuer: "https://demo.example",
        audience: "agent-os",
        assurance: "anonymous",
      },
      { name: "wide", issuer: "https://wide.example", audience: "wide-aud", assurance: "both" },
      { name: "gate", issuer: "https://gate.example", audience: "agent-os", assurance: "login" },
    ],
    assets: testAssets(),
    now: () => NOW_MS,
    newAnonymousId: () => FRESH_ID,
    ...overrides,
  };
}

interface Extras {
  readonly headers?: Record<string, string>;
  readonly cookies?: readonly Cookie[];
  /** 물음표를 포함한 질의. 주지 않으면 비어 있다. */
  readonly query?: string;
}

function request(method: string, path: string, extras: Extras = {}): PortalRequest {
  return {
    method,
    path,
    query: extras.query ?? "",
    headers: extras.headers ?? {},
    cookies: extras.cookies ?? [],
  };
}

function call(method: string, path: string, extras: Extras = {}, ctx = context()): PortalResponse {
  return handle(request(method, path, extras), ctx);
}

const anon = (value: string): Cookie => ({ name: "portal_anon", value });
const fromOrigin = (origin = ORIGIN): Record<string, string> => ({ origin });

function setCookieOf(response: PortalResponse): string[] {
  return (response.headers["Set-Cookie"] ?? "").split("; ").filter((piece) => piece !== "");
}

test("health 는 살아 있다고 JSON 으로 답하고 캐시하지 않는다", () => {
  const response = call("GET", "/portal/health");

  expect(response.status).toBe(200);
  expect(response.headers["Content-Type"]).toBe("application/json");
  expect(response.headers["Cache-Control"]).toBe("no-store");
  expect(JSON.parse(response.body)).toEqual({ status: "ok" });
});

test("모르는 경로는 404 다", () => {
  expect(call("GET", "/nothing").status).toBe(404);
  // 끝 슬래시가 없는 /portal 은 넘기지 않고 404 다(운영의 프록시가 그 경로를 404 로 답한다).
  expect(call("GET", "/portal").status).toBe(404);
  expect(call("GET", "/portal/nothing").status).toBe(404);
  expect(call("GET", "/portal/portal.js/extra").status).toBe(404);
});

const CSP =
  "default-src 'none'; script-src 'self'; connect-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'";

test("페이지는 질의와 쿠키를 보지 않고 같은 HTML 을 낸다", () => {
  const plain = call("GET", "/portal/");
  const withQuery = call("GET", "/portal/", {
    query: "?site=other",
    cookies: [anon(ID)],
    headers: { cookie: `portal_anon=${ID}` },
  });

  expect(plain.status).toBe(200);
  expect(plain.headers["Content-Type"]).toBe("text/html; charset=utf-8");
  expect(plain.body).toBe(testAssets().page.body);
  expect(withQuery.body).toBe(plain.body);
});

test("페이지 응답의 Content-Security-Policy 는 글자 그대로다", () => {
  const response = call("GET", "/portal/");

  expect(response.headers["Content-Security-Policy"]).toBe(CSP);
});

test("페이지와 정적 파일은 no-cache 와 ETag 와 nosniff 를 단다", () => {
  for (const path of ["/portal/", "/portal/portal.js", "/portal/portal.css", "/portal/theme.css"]) {
    const response = call("GET", path);

    expect(response.status, path).toBe(200);
    expect(response.headers["Cache-Control"], path).toBe("no-cache");
    expect(response.headers["ETag"], path).toMatch(/^"[0-9a-f]{32}"$/u);
    expect(response.headers["X-Content-Type-Options"], path).toBe("nosniff");
  }
});

test("정적 파일의 콘텐츠 타입은 명세 표대로다", () => {
  const types = (path: string): string | undefined => call("GET", path).headers["Content-Type"];

  expect(types("/portal/portal.js")).toBe("text/javascript; charset=utf-8");
  expect(types("/portal/portal.css")).toBe("text/css; charset=utf-8");
  expect(types("/portal/theme.css")).toBe("text/css; charset=utf-8");
  expect(types("/portal/fonts.css")).toBe("text/css; charset=utf-8");
  expect(types("/portal/fonts/font-a.woff2")).toBe("font/woff2");
});

test("조건부 요청이 같은 ETag 를 보내면 304 와 빈 본문으로 답한다", () => {
  for (const path of ["/portal/", "/portal/portal.js", "/portal/fonts/font-a.woff2"]) {
    const first = call("GET", path);
    const etag = first.headers["ETag"] ?? "";

    const second = call("GET", path, { headers: { "if-none-match": etag } });

    expect(second.status, path).toBe(304);
    expect(second.body, path).toBe("");
    expect(second.headers["ETag"], path).toBe(etag);
    expect(second.headers["Cache-Control"], path).toBe("no-cache");
    expect(second.file, path).toBeUndefined();
  }
});

const PAGE_ETAG = call("GET", "/portal/").headers["ETag"] ?? "";

function conditional(value: string): number {
  return call("GET", "/portal/", { headers: { "if-none-match": value } }).status;
}

test("다른 ETag 를 보내면 304 가 아니라 200 이다", () => {
  expect(conditional('"other"')).toBe(200);
});

test("쉼표로 이은 목록의 가운데에 같은 ETag 가 있으면 304 다", () => {
  expect(conditional(`"x", ${PAGE_ETAG}`)).toBe(304);
});

test("약한 표시(W/)가 붙은 같은 ETag 도 304 다", () => {
  expect(conditional(`W/${PAGE_ETAG}`)).toBe(304);
});

test("별표는 어느 ETag 와도 맞아 304 다", () => {
  expect(conditional("*")).toBe(304);
});

test("글꼴 파일은 목록의 이름만 파일 경로로 내고 본문은 비운다", () => {
  const response = call("GET", "/portal/fonts/font-a.woff2");

  expect(response.status).toBe(200);
  expect(response.body).toBe("");
  expect(response.file).toBe(testAssets().fonts.get("font-a.woff2")?.path);
  expect(response.headers["Content-Length"]).toBe("3");
});

test("글꼴 목록 밖 이름은 404 다", () => {
  expect(call("GET", "/portal/fonts/not-in-list.woff2").status).toBe(404);
  expect(call("GET", "/portal/fonts/").status).toBe(404);
  // 경로를 거슬러 오르는 이름도 목록에 없어 404 다.
  expect(call("GET", "/portal/fonts/../portal.js").status).toBe(404);
  expect(call("GET", "/portal/fonts/%2e%2e%2fportal.js").status).toBe(404);
});

test("루트는 질의를 그대로 붙여 /portal/ 로 302 한다", () => {
  const plain = call("GET", "/");
  const withQuery = call("GET", "/", { query: "?site=other&x=1" });

  expect(plain.status).toBe(302);
  expect(plain.headers["Location"]).toBe("/portal/");
  expect(withQuery.status).toBe(302);
  expect(withQuery.headers["Location"]).toBe("/portal/?site=other&x=1");
});

test("정적 경로와 루트의 다른 메서드는 405 와 Allow 로 답한다", () => {
  for (const path of ["/", "/portal/", "/portal/portal.js", "/portal/fonts/font-a.woff2"]) {
    const response = call("POST", path);

    expect(response.status, path).toBe(405);
    expect(response.headers["Allow"], path).toBe("GET");
  }
});

test("아는 경로의 다른 메서드는 405 와 Allow 로 답한다", () => {
  for (const method of ["POST", "PUT", "DELETE", "HEAD"]) {
    const response = call(method, "/portal/health");

    expect(response.status, method).toBe(405);
    expect(response.headers["Allow"], method).toBe("GET");
  }
});

test("모든 응답에 nosniff 를 단다", () => {
  const responses = [
    call("GET", "/portal/health"),
    call("GET", "/nothing"),
    call("POST", "/portal/health"),
    call("GET", "/portal/sites/demo/acknowledgement"),
    call("POST", "/portal/sites/demo/acknowledgement", { headers: fromOrigin() }),
    call("POST", "/portal/sites/demo/acknowledgement"),
    call("POST", "/portal/sites/demo/token"),
    call("POST", "/portal/sites/demo/token", { cookies: [anon(ID)] }),
    call("GET", "/portal/sites/gate/acknowledgement"),
    call("GET", "/portal/sites/missing/acknowledgement"),
    call("GET", "/portal/sites/demo/token"),
  ];

  for (const response of responses) {
    expect(response.headers["X-Content-Type-Options"]).toBe("nosniff");
  }
});

test("고지 확인 상태는 쿠키가 없으면 거짓이다", () => {
  const response = call("GET", "/portal/sites/demo/acknowledgement");

  expect(response.status).toBe(200);
  expect(response.headers["Content-Type"]).toBe("application/json");
  expect(JSON.parse(response.body)).toEqual({ acknowledged: false });
  expect(response.headers["Set-Cookie"]).toBeUndefined();
});

test("고지 확인 상태는 꼴이 맞는 쿠키가 있으면 참이다", () => {
  const response = call("GET", "/portal/sites/demo/acknowledgement", { cookies: [anon(ID)] });

  expect(response.status).toBe(200);
  expect(JSON.parse(response.body)).toEqual({ acknowledged: true });
  expect(response.headers["Set-Cookie"]).toBeUndefined();
});

test("고지 확인 상태는 꼴이 틀린 쿠키를 없는 것으로 본다", () => {
  const response = call("GET", "/portal/sites/demo/acknowledgement", {
    cookies: [anon("not-a-uuid")],
  });

  expect(JSON.parse(response.body)).toEqual({ acknowledged: false });
});

test("고지 확인은 Origin 이 공개 출처와 같으면 204 와 새 식별자 쿠키를 낸다", () => {
  const response = call("POST", "/portal/sites/demo/acknowledgement", { headers: fromOrigin() });

  expect(response.status).toBe(204);
  expect(response.body).toBe("");
  expect(setCookieOf(response)).toEqual([
    `portal_anon=${FRESH_ID}`,
    "HttpOnly",
    "SameSite=Strict",
    "Path=/portal/sites/demo",
    "Max-Age=2592000",
  ]);
});

test("고지 확인은 꼴이 맞는 쿠키가 있으면 같은 값으로 만료만 다시 적는다", () => {
  const response = call("POST", "/portal/sites/demo/acknowledgement", {
    headers: fromOrigin(),
    cookies: [anon(ID)],
  });

  expect(response.status).toBe(204);
  expect(setCookieOf(response)[0]).toBe(`portal_anon=${ID}`);
  expect(setCookieOf(response)).toContain("Max-Age=2592000");
});

test("고지 확인은 꼴이 틀린 쿠키가 있으면 새 값을 낸다", () => {
  const response = call("POST", "/portal/sites/demo/acknowledgement", {
    headers: fromOrigin(),
    cookies: [anon("broken")],
  });

  expect(setCookieOf(response)[0]).toBe(`portal_anon=${FRESH_ID}`);
});

test("고지 확인은 같은 이름의 쿠키가 둘이면 첫 것의 값을 다시 적는다", () => {
  const response = call("POST", "/portal/sites/demo/acknowledgement", {
    headers: fromOrigin(),
    cookies: [anon(ID), anon(OTHER_ID)],
  });

  expect(setCookieOf(response)[0]).toBe(`portal_anon=${ID}`);
});

test("고지 확인은 Origin 이 없으면 쿠키 없이 403 이다", () => {
  const response = call("POST", "/portal/sites/demo/acknowledgement");

  expect(response.status).toBe(403);
  expect(response.headers["Content-Type"]).toBe("text/plain; charset=utf-8");
  expect(response.headers["Set-Cookie"]).toBeUndefined();
});

test("고지 확인은 Origin 이 공개 출처와 다르면 쿠키 없이 403 이다", () => {
  const different = [
    "http://evil.example",
    "https://portal.localhost:8080",
    "http://portal.localhost:8081",
    // 글자 그대로 견준다. 끝 슬래시와 대문자는 다른 출처로 본다.
    `${ORIGIN}/`,
    ORIGIN.toUpperCase(),
    "null",
    "",
  ];

  for (const origin of different) {
    const response = call("POST", "/portal/sites/demo/acknowledgement", {
      headers: fromOrigin(origin),
      cookies: [anon(ID)],
    });

    expect(response.status, JSON.stringify(origin)).toBe(403);
    expect(response.headers["Set-Cookie"], JSON.stringify(origin)).toBeUndefined();
  }
});

test("Secure 는 공개 출처가 https 일 때만 붙는다", () => {
  const secure = call(
    "POST",
    "/portal/sites/demo/acknowledgement",
    { headers: fromOrigin("https://portal.example") },
    context({ publicOrigin: "https://portal.example" }),
  );
  const plain = call("POST", "/portal/sites/demo/acknowledgement", { headers: fromOrigin() });

  expect(setCookieOf(secure)).toContain("Secure");
  expect(setCookieOf(plain)).not.toContain("Secure");
});

test("토큰은 쿠키가 없으면 401 과 고지 확인 안내다", () => {
  const response = call("POST", "/portal/sites/demo/token");

  expect(response.status).toBe(401);
  expect(response.headers["Content-Type"]).toBe("text/plain; charset=utf-8");
  expect(response.body).toBe("고지 확인이 필요합니다.");
  expect(response.headers["Set-Cookie"]).toBeUndefined();
});

test("토큰은 꼴이 틀린 쿠키를 없는 것으로 보고 401 이다", () => {
  const response = call("POST", "/portal/sites/demo/token", { cookies: [anon("broken")] });

  expect(response.status).toBe(401);
  expect(response.body).toBe("고지 확인이 필요합니다.");
});

function parseToken(body: string) {
  const [head, claimsPart, signature] = body.split(".");
  if (head === undefined || claimsPart === undefined || signature === undefined) {
    throw new Error("토큰이 아니다");
  }
  const header: unknown = JSON.parse(Buffer.from(head, "base64url").toString("utf-8"));
  const claims: unknown = JSON.parse(Buffer.from(claimsPart, "base64url").toString("utf-8"));
  return { head, claimsPart, signature, header, claims };
}

test("토큰은 꼴이 맞는 쿠키가 있으면 200 과 토큰 글 하나를 text/plain 으로 낸다", () => {
  const response = call("POST", "/portal/sites/demo/token", { cookies: [anon(ID)] });

  expect(response.status).toBe(200);
  expect(response.headers["Content-Type"]).toBe("text/plain; charset=utf-8");
  expect(response.body).toMatch(/^[\w-]+\.[\w-]+\.[\w-]+$/u);
});

test("토큰은 공개 키로 검증되고 클레임이 그 사이트의 것이다", () => {
  const response = call("POST", "/portal/sites/demo/token", { cookies: [anon(ID)] });
  const { head, claimsPart, signature, header, claims } = parseToken(response.body);

  expect(
    verify(
      "RSA-SHA256",
      Buffer.from(`${head}.${claimsPart}`),
      createPublicKey(rsaKey().spki),
      Buffer.from(signature, "base64url"),
    ),
  ).toBe(true);
  expect(header).toEqual({ alg: "RS256", typ: "JWT", kid: "portal-1" });
  const expectedSubject = `anon-${createHash("sha256").update(ID, "utf8").digest("hex").slice(0, 32)}`;
  expect(claims).toEqual({
    iss: "https://demo.example",
    sub: expectedSubject,
    aud: "agent-os",
    iat: NOW_MS / 1000,
    exp: NOW_MS / 1000 + 120,
  });
});

test("토큰의 발급자와 audience 는 사이트마다 그 사이트의 것이다", () => {
  const response = call("POST", "/portal/sites/wide/token", { cookies: [anon(ID)] });

  expect(parseToken(response.body).claims).toMatchObject({
    iss: "https://wide.example",
    aud: "wide-aud",
  });
});

test("토큰과 토큰 응답의 어느 곳에도 쿠키 값 원문이 없다", () => {
  const response = call("POST", "/portal/sites/demo/token", { cookies: [anon(ID)] });

  expect(response.body).not.toContain(ID);
  expect(
    Buffer.from(response.body.split(".")[1] ?? "", "base64url").toString("utf-8"),
  ).not.toContain(ID);
});

test("토큰 200 은 받은 쿠키와 같은 값으로 만료를 다시 적는다", () => {
  const response = call("POST", "/portal/sites/demo/token", { cookies: [anon(ID)] });

  expect(setCookieOf(response)).toEqual([
    `portal_anon=${ID}`,
    "HttpOnly",
    "SameSite=Strict",
    "Path=/portal/sites/demo",
    "Max-Age=2592000",
  ]);
});

test("토큰은 같은 이름의 쿠키가 둘이면 첫 것의 주체로 낸다", () => {
  const response = call("POST", "/portal/sites/demo/token", {
    cookies: [anon(ID), anon(OTHER_ID)],
  });

  expect(parseToken(response.body).claims).toMatchObject({
    sub: `anon-${createHash("sha256").update(ID, "utf8").digest("hex").slice(0, 32)}`,
  });
});

test("토큰 끝점은 Origin 을 보지 않는다", () => {
  for (const headers of [{}, fromOrigin(), fromOrigin("http://evil.example")]) {
    const response = call("POST", "/portal/sites/demo/token", { headers, cookies: [anon(ID)] });

    expect(response.status, JSON.stringify(headers)).toBe(200);
  }
});

test("토큰 끝점의 Secure 도 공개 출처가 https 일 때만 붙는다", () => {
  const secure = call(
    "POST",
    "/portal/sites/demo/token",
    { cookies: [anon(ID)] },
    context({ publicOrigin: "https://portal.example" }),
  );

  expect(setCookieOf(secure)).toContain("Secure");
  expect(
    setCookieOf(call("POST", "/portal/sites/demo/token", { cookies: [anon(ID)] })),
  ).not.toContain("Secure");
});

test("로그인 사이트의 세 끝점은 메서드와 쿠키와 Origin 과 상관없이 403 이다", () => {
  const cases: [string, string][] = [
    ["GET", "/portal/sites/gate/acknowledgement"],
    ["POST", "/portal/sites/gate/acknowledgement"],
    ["PUT", "/portal/sites/gate/acknowledgement"],
    ["POST", "/portal/sites/gate/token"],
    ["GET", "/portal/sites/gate/token"],
    ["DELETE", "/portal/sites/gate/token"],
  ];

  for (const [method, path] of cases) {
    for (const extras of [{}, { cookies: [anon(ID)], headers: fromOrigin() }]) {
      const response = call(method, path, extras);

      expect(response.status, `${method} ${path}`).toBe(403);
      expect(response.headers["Content-Type"], `${method} ${path}`).toBe(
        "text/plain; charset=utf-8",
      );
      expect(response.body, `${method} ${path}`).toBe(LOGIN_NOTICE);
      expect(response.headers["Set-Cookie"], `${method} ${path}`).toBeUndefined();
    }
  }
});

test("both 사이트는 anonymous 와 같이 고지 확인과 토큰을 낸다", () => {
  const acknowledged = call("POST", "/portal/sites/wide/acknowledgement", {
    headers: fromOrigin(),
  });
  const token = call("POST", "/portal/sites/wide/token", { cookies: [anon(ID)] });

  expect(acknowledged.status).toBe(204);
  expect(token.status).toBe(200);
});

test("모르는 사이트 이름과 모르는 끝점은 404 다", () => {
  for (const path of [
    "/portal/sites/missing/acknowledgement",
    "/portal/sites/missing/token",
    "/portal/sites/demo/other",
    "/portal/sites/demo",
    "/portal/sites/demo/",
    "/portal/sites//token",
    "/portal/sites/demo/token/",
    "/portal/sites/demo/acknowledgement/extra",
    "/portal/sites/DEMO/token",
    "/portal/sites/de%6Do/token",
  ]) {
    expect(call("POST", path, { cookies: [anon(ID)], headers: fromOrigin() }).status, path).toBe(
      404,
    );
  }
});

test("고지 확인 끝점의 다른 메서드는 405 와 Allow 로 답한다", () => {
  for (const method of ["PUT", "DELETE", "PATCH", "HEAD"]) {
    const response = call(method, "/portal/sites/demo/acknowledgement", { headers: fromOrigin() });

    expect(response.status, method).toBe(405);
    expect(response.headers["Allow"], method).toBe("GET, POST");
  }
});

test("토큰 끝점의 다른 메서드는 405 와 Allow 로 답한다", () => {
  for (const method of ["GET", "PUT", "DELETE", "HEAD"]) {
    const response = call(method, "/portal/sites/demo/token", { cookies: [anon(ID)] });

    expect(response.status, method).toBe(405);
    expect(response.headers["Allow"], method).toBe("POST");
  }
});

test("사이트 끝점의 모든 응답은 캐시하지 않는다", () => {
  const responses = [
    call("GET", "/portal/sites/demo/acknowledgement"),
    call("GET", "/portal/sites/demo/acknowledgement", { cookies: [anon(ID)] }),
    call("POST", "/portal/sites/demo/acknowledgement", { headers: fromOrigin() }),
    call("POST", "/portal/sites/demo/acknowledgement"),
    call("POST", "/portal/sites/demo/token"),
    call("POST", "/portal/sites/demo/token", { cookies: [anon(ID)] }),
    call("GET", "/portal/sites/gate/acknowledgement"),
    call("PUT", "/portal/sites/demo/acknowledgement"),
    call("GET", "/portal/sites/demo/token"),
    call("GET", "/portal/sites/missing/token"),
  ];

  for (const response of responses) {
    expect(response.headers["Cache-Control"], String(response.status)).toBe("no-store");
  }
});

test("401 과 403 의 본문에 쿠키 값이 들지 않는다", () => {
  const refused = call("POST", "/portal/sites/demo/acknowledgement", {
    headers: fromOrigin("http://evil.example"),
    cookies: [anon(ID)],
  });
  const gated = call("POST", "/portal/sites/gate/token", { cookies: [anon(ID)] });
  const unauthorized = call("POST", "/portal/sites/demo/token", {
    cookies: [anon("broken-" + ID)],
  });

  for (const response of [refused, gated, unauthorized]) {
    expect(response.body).not.toContain(ID);
  }
});
