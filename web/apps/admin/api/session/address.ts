// 로그인 화면의 주소를 짓고 읽는 규칙(admin-login 명세 "관리 화면의 페이지와 주소"). 화면의 스크립트는 HttpOnly 쿠키를
// 읽지 못하므로, 어느 화면에서 쫓겨났는지는 `next` 질의가 들고 간다.

/** 로그인 화면의 알림 값 셋. 모르는 값은 무시한다. */
export type LoginNotice = "logged-out" | "expired" | "password-set";

const NOTICES = {
  "logged-out": true,
  expired: true,
  "password-set": true,
} as const satisfies Record<LoginNotice, true>;

function isNotice(value: string): value is LoginNotice {
  return Object.hasOwn(NOTICES, value);
}

/** 주소의 질의로 온 글자가 알림 값인가. 모르는 값이면 null 이다. */
export function noticeOf(value: string | null): LoginNotice | null {
  return value !== null && isNotice(value) ? value : null;
}

/** 로그인 없이 열리는 화면의 경로. 여기서는 로그인을 요구해 쫓아내지 않고, `next` 로도 받지 않는다. */
const PUBLIC_PATHS: readonly string[] = ["/login", "/set-password"];

function withoutTrailingSlash(path: string): string {
  return path.length > 1 ? path.replace(/\/+$/, "") : path;
}

/** 퍼센트로 쓴 글자를 푼다. `/%6cogin` 도 라우터에는 `/login` 이다. 풀리지 않는 글이면 그대로 둔다. */
function decodedPath(pathname: string): string {
  try {
    return decodeURIComponent(pathname);
  } catch {
    return pathname;
  }
}

/** 이 경로의 화면이 로그인 없이 열리는 화면인가. */
export function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.includes(withoutTrailingSlash(decodedPath(pathname)));
}

/**
 * 로그인 뒤에 돌아갈 곳. 값을 지금 화면의 출처를 기준으로 URL 로 풀어, 풀린 주소의 출처가 같을 때만 받고 그 `href`
 * (출처까지 든 절대 주소)를 돌려준다. 경로만 떼어 쓰지 않는다. `https://admin.example:8443//evil.test/x` 는 출처가
 * 같지만 경로만 떼면 `//evil.test/x` 라 브라우저가 다른 사이트로 읽는다. 앞 글자만 보는 검사로는 `/<탭>/evil.test` 를
 * 막지 못한다. URL 로 풀면 탭과 줄바꿈이 지워져 다른 출처로 풀리므로 여기서 걸린다. 풀리지 않거나 출처가 다르거나
 * 로그인 화면과 비밀번호 정하기 화면의 주소면 null 이다.
 */
export function nextTarget(raw: string | null, origin: string): string | null {
  if (raw === null || raw === "") {
    return null;
  }
  let target: URL;
  try {
    target = new URL(raw, origin);
  } catch {
    return null;
  }
  if (target.origin !== origin || isPublicPath(target.pathname)) {
    return null;
  }
  return target.href;
}

/** 서버 자신의 주소(루프백). https 가 아니어도 브라우저가 `Secure` 쿠키를 받는다. */
const LOOPBACK_HOSTS: readonly string[] = ["localhost", "127.0.0.1", "[::1]"];

/**
 * 이 주소에서 로그인할 수 있는가. 쿠키는 `Secure` 라서 브라우저가 https 주소와 서버 자신의 주소(루프백)의 http 에서만
 * 받아 준다. 그 밖의 http 주소에서는 로그인해도 쿠키가 남지 않는다. 화면이 열린 주소는 http 나 https 뿐이라 `http:` 가
 * 아니면 https 로 본다. 링크로 비밀번호 정하기 화면도 같은 판정으로 막는다. 쿠키가 아니라 새 비밀번호가 평문으로 오가기 때문이다.
 */
export function canSignInAt(url: URL): boolean {
  return url.protocol !== "http:" || LOOPBACK_HOSTS.includes(url.hostname);
}

/** 로그인 화면의 주소. `next` 는 지금 화면의 경로와 질의다. */
export function loginAddress({
  next,
  notice,
}: {
  readonly next?: string;
  readonly notice?: LoginNotice;
}): string {
  const query = new URLSearchParams();
  if (next !== undefined) {
    query.set("next", next);
  }
  if (notice !== undefined) {
    query.set("notice", notice);
  }
  const text = query.toString();
  return text === "" ? "/login" : `/login?${text}`;
}

/**
 * 비밀번호 링크의 주소. 서버는 토큰만 주고 주소를 짓지 않는다. 관리 화면의 출처에 `/set-password#<토큰>` 이다. `#` 뒤는
 * 브라우저가 서버에도 `Referer` 에도 보내지 않는다.
 */
export function setPasswordAddress(token: string): string {
  const address = new URL("/set-password", location.origin);
  address.hash = token;
  return address.href;
}

/** 지금 화면의 경로와 질의(조각은 뺀다). 로그인 뒤에 돌아올 곳으로 `next` 에 싣는다. */
export function currentPlace(): string {
  return `${location.pathname}${location.search}`;
}
