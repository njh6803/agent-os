// HTTP 요청 처리기. 요청 값(메서드, 경로, 질의, 헤더, 쿠키)과 처리 값(`PortalContext`)을 받아 응답 값(상태, 헤더, 본문)을 내는
// 순수 함수 하나다. 소켓에 거는 일은 `serve.ts` 가 하고, 여기는 `node:http` 를 모른다. 그래서 시험이 요청을 값으로 만들어
// 부르고 시계와 UUID 만들기를 고정한다(pilot-portal 명세 "HTTP 요청 처리기와 서버"). 서버 코드와 시험은 전역 `fetch` 를 쓰지
// 않는다.
//
// 경로는 `GET /` 의 302, 페이지 `GET /portal/`, 메모리의 정적 파일 넷, 글꼴 `GET /portal/fonts/<이름>`, `GET /portal/health`,
// 사이트마다의 `/portal/sites/<이름>/acknowledgement` 와 `/portal/sites/<이름>/token` 이다. 경로의 글자는 `paths.ts` 가
// 한 곳에서 정한다. 쿠키 값과 토큰은 응답에만 싣고 어디에도 기록하지 않는다(ADR 0050 결정 "기록").
//
// 페이지와 정적 파일은 `Cache-Control: no-cache` 와 내용 해시의 `ETag` 를 달고 조건부 요청에 304 로 답한다. 글꼴 파일은
// 본문 대신 `file` 에 경로를 돌려주고 `serve.ts` 가 흘려보낸다.

import { anonymousCookie, anonymousIdOf } from "./anonymous-cookie.ts";
import type { StaticText } from "./assets.ts";
import type { PortalContext, SiteContext } from "./context.ts";
import type { Cookie } from "./cookies.ts";
import {
  FONTS_CSS,
  FONTS_PREFIX,
  HEALTH,
  PAGE,
  PAGE_CSS,
  PAGE_SCRIPT,
  ROOT,
  SITE_ENDPOINT,
  SITES_PREFIX,
  THEME_CSS,
} from "./paths.ts";
import { anonymousSubject, signSiteToken } from "./token.ts";

export interface PortalRequest {
  readonly method: string;
  /** 질의를 뗀 경로. 퍼센트 인코딩은 풀지 않는다. */
  readonly path: string;
  /** 물음표를 포함한 질의. 질의가 없으면 빈 글이다. 퍼센트 인코딩은 풀지 않는다. */
  readonly query: string;
  /** 소문자 이름의 요청 헤더. 같은 이름이 여럿이면 `node:http` 가 이은 한 글이다(`cookie` 는 `; ` 로 잇는다). */
  readonly headers: Readonly<Record<string, string>>;
  readonly cookies: readonly Cookie[];
}

export interface PortalResponse {
  readonly status: number;
  readonly headers: Readonly<Record<string, string>>;
  readonly body: string;
  /** 주면 본문 대신 이 파일을 흘려보낸다. 이때 `body` 는 비어 있다. */
  readonly file?: string;
}

/** 모든 응답에 단다. 브라우저가 내용을 추측해 다른 형식으로 읽지 못하게 한다. */
const SECURITY_HEADERS = { "X-Content-Type-Options": "nosniff" } as const;
const TEXT = "text/plain; charset=utf-8";
const NO_CACHE = "no-cache";

/** 페이지 응답의 CSP. 같은 출처의 파일만 싣고 다른 문서가 이 페이지를 틀에 넣지 못한다. */
const PAGE_CSP =
  "default-src 'none'; script-src 'self'; connect-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'";

function respond(
  status: number,
  contentType: string,
  body: string,
  extra: Readonly<Record<string, string>> = {},
): PortalResponse {
  return {
    status,
    headers: { ...SECURITY_HEADERS, "Content-Type": contentType, ...extra },
    body,
  };
}

function noContent(extra: Readonly<Record<string, string>>): PortalResponse {
  return { status: 204, headers: { ...SECURITY_HEADERS, ...extra }, body: "" };
}

function notFound(): PortalResponse {
  return respond(404, TEXT, "찾을 수 없습니다.");
}

function methodNotAllowed(allow: string): PortalResponse {
  return respond(405, TEXT, "허용하지 않는 메서드입니다.", { Allow: allow });
}

/** 처리기가 던졌을 때 `serve.ts` 가 내는 응답. 까닭은 싣지 않는다. */
export const SERVER_ERROR: PortalResponse = respond(500, TEXT, "서버 오류입니다.", {
  "Cache-Control": "no-store",
});

export function handle(request: PortalRequest, context: PortalContext): PortalResponse {
  const { path } = request;
  if (path === ROOT) {
    return request.method === "GET" ? redirectToPage(request) : methodNotAllowed("GET");
  }
  if (path === HEALTH) {
    return request.method === "GET"
      ? respond(200, "application/json", JSON.stringify({ status: "ok" }), {
          "Cache-Control": "no-store",
        })
      : methodNotAllowed("GET");
  }
  if (path.startsWith(SITES_PREFIX)) {
    const response = siteEndpoint(request, context);
    return { ...response, headers: { ...response.headers, "Cache-Control": "no-store" } };
  }
  if (path.startsWith(FONTS_PREFIX)) {
    return fontFile(request, context, path.slice(FONTS_PREFIX.length));
  }
  const { assets } = context;
  switch (path) {
    case PAGE:
      return staticFile(request, assets.page, { "Content-Security-Policy": PAGE_CSP });
    case PAGE_SCRIPT:
      return staticFile(request, assets.pageScript);
    case PAGE_CSS:
      return staticFile(request, assets.pageCss);
    case THEME_CSS:
      return staticFile(request, assets.themeCss);
    case FONTS_CSS:
      return staticFile(request, assets.fontsCss);
    default:
      return notFound();
  }
}

/** `/` 는 질의를 지킨 채 페이지로 넘긴다. `/portal`(끝 슬래시 없음)은 넘기지 않고 404 다. */
function redirectToPage(request: PortalRequest): PortalResponse {
  return {
    status: 302,
    headers: {
      ...SECURITY_HEADERS,
      Location: `${PAGE}${request.query}`,
      "Cache-Control": "no-store",
    },
    body: "",
  };
}

/** `If-None-Match` 가 이 `ETag` 를 들었는지. 약한 표시(`W/`)는 벗기고 `*` 는 늘 맞는다. */
function matches(request: PortalRequest, etag: string): boolean {
  const header = request.headers["if-none-match"];
  if (header === undefined) {
    return false;
  }
  return header
    .split(",")
    .map((tag) => tag.trim().replace(/^W\//u, ""))
    .some((tag) => tag === "*" || tag === etag);
}

function notModified(etag: string): PortalResponse {
  return {
    status: 304,
    headers: { ...SECURITY_HEADERS, ETag: etag, "Cache-Control": NO_CACHE },
    body: "",
  };
}

function staticFile(
  request: PortalRequest,
  file: StaticText,
  extra: Readonly<Record<string, string>> = {},
): PortalResponse {
  if (request.method !== "GET") {
    return methodNotAllowed("GET");
  }
  if (matches(request, file.etag)) {
    return notModified(file.etag);
  }
  return respond(200, file.contentType, file.body, {
    "Cache-Control": NO_CACHE,
    ETag: file.etag,
    ...extra,
  });
}

/** 목록(시작 때 짓는 표)에 있는 이름만 낸다. 경로를 거슬러 오르는 이름도 표에 없어 404 다. */
function fontFile(request: PortalRequest, context: PortalContext, name: string): PortalResponse {
  const font = context.assets.fonts.get(name);
  if (font === undefined) {
    return notFound();
  }
  if (request.method !== "GET") {
    return methodNotAllowed("GET");
  }
  if (matches(request, font.etag)) {
    return notModified(font.etag);
  }
  return {
    status: 200,
    headers: {
      ...SECURITY_HEADERS,
      "Content-Type": "font/woff2",
      "Content-Length": String(font.size),
      "Cache-Control": NO_CACHE,
      ETag: font.etag,
    },
    body: "",
    file: font.path,
  };
}

function siteEndpoint(request: PortalRequest, context: PortalContext): PortalResponse {
  const match = SITE_ENDPOINT.exec(request.path);
  const name = match?.[1];
  const endpoint = match?.[2];
  const site = context.sites.find((candidate) => candidate.name === name);
  if (site === undefined || endpoint === undefined) {
    return notFound();
  }
  // 로그인 사이트는 메서드와 쿠키와 상관없이 막는다. 로그인은 아직 없다.
  if (site.assurance === "login") {
    return respond(403, TEXT, "이 사이트는 로그인이 필요합니다. 로그인은 아직 제공하지 않습니다.");
  }
  return endpoint === "acknowledgement"
    ? acknowledgement(request, context, site)
    : token(request, context, site);
}

function cookieFor(id: string, site: SiteContext, context: PortalContext): string {
  return anonymousCookie({ id, siteName: site.name, publicOrigin: context.publicOrigin });
}

function acknowledgement(
  request: PortalRequest,
  context: PortalContext,
  site: SiteContext,
): PortalResponse {
  if (request.method === "GET") {
    const acknowledged = anonymousIdOf(request.cookies) !== undefined;
    return respond(200, "application/json", JSON.stringify({ acknowledged }));
  }
  if (request.method !== "POST") {
    return methodNotAllowed("GET, POST");
  }
  // 다른 사이트에서 일으킨 고지 확인에 쿠키를 내지 않는다. `Origin` 을 글자 그대로 공개 출처와 견준다.
  if (request.headers["origin"] !== context.publicOrigin) {
    return respond(403, TEXT, "허용하지 않는 출처입니다.");
  }
  const id = anonymousIdOf(request.cookies) ?? context.newAnonymousId();
  return noContent({ "Set-Cookie": cookieFor(id, site, context) });
}

/** `Origin` 을 보지 않는다. 쿠키가 `SameSite=Strict` 라 다른 사이트에서 일으킨 요청에는 쿠키가 실리지 않는다. */
function token(request: PortalRequest, context: PortalContext, site: SiteContext): PortalResponse {
  if (request.method !== "POST") {
    return methodNotAllowed("POST");
  }
  const id = anonymousIdOf(request.cookies);
  if (id === undefined) {
    return respond(401, TEXT, "고지 확인이 필요합니다.");
  }
  const signed = signSiteToken({
    privateKey: context.privateKey,
    kid: context.kid,
    issuer: site.issuer,
    audience: site.audience,
    subject: anonymousSubject(id),
    nowSeconds: Math.floor(context.now() / 1000),
  });
  return respond(200, TEXT, signed, { "Set-Cookie": cookieFor(id, site, context) });
}
