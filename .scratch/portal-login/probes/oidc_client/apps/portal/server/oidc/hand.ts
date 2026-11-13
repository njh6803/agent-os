// 후보 다: 라이브러리 없이 `node:crypto` 와 `node:http`·`node:https` 의 `request` 로 직접 짠 OIDC 인가 코드 흐름.
// 프로브의 것이고 제품 코드가 아니다. `signature` 는 `verify` 하나만 받는다(서명을 늘 본다).
//
// ID 토큰 검증에서 한 것(번호는 OpenID Connect Core 1.0 의 3.1.3.7 "ID Token Validation"):
//   2  `iss` 가 설정 문서의 발급자와 글자 그대로 같다
//   3  `aud` 에 클라이언트 id 가 있다
//   4·5  `aud` 가 여럿이면 `azp` 가 있어야 하고, `azp` 가 있으면 클라이언트 id 와 같다
//   6  JWS 서명(RS256)을 공개 키 끝점의 키로 본다. 키는 `kid` 로 고른다
//   7  `alg` 가 RS256 이 아니면 거부한다(`none`, HS256 포함)
//   9  `exp` 가 지금보다 뒤다(허용 오차 30초)
//   11 `nonce` 가 보낸 값과 같다
//   그 밖: `sub` 가 빈 글이 아닌 글이다, `iat` 가 수다, 토큰이 점으로 나뉜 세 토막이다
// 흐름에서 한 것: 설정 문서의 `issuer` 가 물은 발급자와 같은지, PKCE(S256), `state` 견주기, 돌아온 요청의 `error`,
//   돌아온 요청의 `iss`(RFC 9207, 있을 때만), `client_secret_basic`, 토큰 응답의 `token_type`.
// 하지 않은 것:
//   1  암호화된 ID 토큰(JWE)
//   8  HS256 같은 MAC 알고리즘(거부만 한다)
//   10 `iat` 가 지금에서 너무 먼지
//   12·13 `acr`, `auth_time`(`max_age`)
//   `at_hash`, RS256 밖의 서명 알고리즘(PS256, ES256, EdDSA), RSA 키 길이의 아래 한계,
//   공개 키의 캐시와 키가 바뀌었을 때 다시 받기(로그인마다 새로 받는다), 응답 크기 상한, 요청 다시 보내기,
//   돌아온 요청에 같은 매개변수가 둘일 때 거부, 설정 문서가 `iss` 매개변수를 낸다고 알릴 때 그것을 요구하기,
//   `client_secret_post`·`private_key_jwt`, UserInfo, 로그아웃, 토큰 갱신.

import {
  createHash,
  createPublicKey,
  type KeyObject,
  randomBytes,
  timingSafeEqual,
  verify,
} from "node:crypto";
import { request as httpRequest } from "node:http";
import { request as httpsRequest } from "node:https";
import type { Begun, LoginConfig, OidcClient, Pending } from "./contract.ts";

const CLOCK_TOLERANCE_SECONDS = 30;
const REQUEST_TIMEOUT_MS = 10_000;

interface HttpResult {
  readonly status: number;
  readonly text: string;
}

interface Outgoing {
  readonly method: "GET" | "POST";
  readonly headers: Readonly<Record<string, string>>;
  readonly body?: string;
}

interface Provider {
  readonly issuer: string;
  readonly authorizationEndpoint: URL;
  readonly tokenEndpoint: URL;
  readonly jwksUri: URL;
}

function send(url: URL, outgoing: Outgoing): Promise<HttpResult> {
  const request = url.protocol === "https:" ? httpsRequest : httpRequest;
  return new Promise((resolve, reject) => {
    const sent = request(
      url,
      { method: outgoing.method, headers: outgoing.headers, timeout: REQUEST_TIMEOUT_MS },
      (incoming) => {
        const chunks: Buffer[] = [];
        incoming.on("data", (chunk: Buffer) => {
          chunks.push(chunk);
        });
        incoming.on("error", reject);
        incoming.on("end", () => {
          resolve({
            status: incoming.statusCode ?? 0,
            text: Buffer.concat(chunks).toString("utf8"),
          });
        });
      },
    );
    sent.on("timeout", () => {
      sent.destroy(new Error("로그인 서버가 제때 답하지 않았다"));
    });
    sent.on("error", reject);
    sent.end(outgoing.body);
  });
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseObject(text: string, what: string): Record<string, unknown> {
  const value: unknown = JSON.parse(text);
  if (!isRecord(value)) {
    throw new Error(`${what} 이 JSON 객체가 아니다`);
  }
  return value;
}

function textOf(source: Record<string, unknown>, key: string, what: string): string {
  const value = source[key];
  if (typeof value !== "string" || value === "") {
    throw new Error(`${what} 의 ${key} 가 글이 아니다`);
  }
  return value;
}

function stringsOf(value: unknown): readonly string[] {
  if (typeof value === "string") {
    return [value];
  }
  if (!Array.isArray(value)) {
    return [];
  }
  const items: unknown[] = value;
  return items.filter((item) => typeof item === "string");
}

function sameText(left: string, right: string): boolean {
  const a = Buffer.from(left);
  const b = Buffer.from(right);
  return a.length === b.length && timingSafeEqual(a, b);
}

function endpoint(config: LoginConfig, value: string): URL {
  const url = new URL(value);
  if (url.protocol !== "https:" && !(url.protocol === "http:" && config.insecure === "allow")) {
    throw new Error(`https 가 아닌 주소로는 요청하지 않는다: ${url.protocol}`);
  }
  return url;
}

async function discover(config: LoginConfig): Promise<Provider> {
  if (config.signature !== "verify") {
    throw new Error(`직접 구현 후보가 모르는 signature: ${config.signature}`);
  }
  const base = config.issuer.replace(/\/$/u, "");
  const result = await send(endpoint(config, `${base}/.well-known/openid-configuration`), {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  if (result.status !== 200) {
    throw new Error(`설정 문서 응답이 ${String(result.status)} 이다`);
  }
  const metadata = parseObject(result.text, "설정 문서");
  const issuer = textOf(metadata, "issuer", "설정 문서");
  if (issuer !== config.issuer) {
    throw new Error("설정 문서의 issuer 가 물은 발급자와 다르다");
  }
  return {
    issuer,
    authorizationEndpoint: endpoint(
      config,
      textOf(metadata, "authorization_endpoint", "설정 문서"),
    ),
    tokenEndpoint: endpoint(config, textOf(metadata, "token_endpoint", "설정 문서")),
    jwksUri: endpoint(config, textOf(metadata, "jwks_uri", "설정 문서")),
  };
}

async function begin(config: LoginConfig): Promise<Begun> {
  const provider = await discover(config);
  const codeVerifier = randomBytes(32).toString("base64url");
  const state = randomBytes(32).toString("base64url");
  const nonce = randomBytes(32).toString("base64url");
  const url = new URL(provider.authorizationEndpoint);
  url.searchParams.set("client_id", config.clientId);
  url.searchParams.set("redirect_uri", config.redirectUri);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", "openid");
  url.searchParams.set(
    "code_challenge",
    createHash("sha256").update(codeVerifier).digest("base64url"),
  );
  url.searchParams.set("code_challenge_method", "S256");
  url.searchParams.set("state", state);
  url.searchParams.set("nonce", nonce);
  return { authorizationUrl: url.href, pending: { state, nonce, codeVerifier } };
}

/** 돌아온 요청에서 인가 코드를 꺼낸다. `state` 를 먼저 본다. */
function codeFrom(callbackUrl: string, provider: Provider, pending: Pending): string {
  const parameters = new URL(callbackUrl).searchParams;
  const state = parameters.get("state");
  if (state === null || !sameText(state, pending.state)) {
    throw new Error("돌아온 요청의 state 가 보낸 값과 다르다");
  }
  const issuer = parameters.get("iss");
  if (issuer !== null && issuer !== provider.issuer) {
    throw new Error("돌아온 요청의 iss 가 발급자와 다르다");
  }
  const error = parameters.get("error");
  if (error !== null) {
    throw new Error(`로그인 서버가 오류를 돌려줬다: ${error}`);
  }
  const code = parameters.get("code");
  if (code === null || code === "") {
    throw new Error("돌아온 요청에 인가 코드가 없다");
  }
  return code;
}

/** RFC 6749 의 2.3.1: id 와 비밀 값을 폼 인코딩한 뒤 Basic 으로 싣는다. */
function basicAuthorization(config: LoginConfig): string {
  const encode = (value: string): string =>
    new URLSearchParams({ v: value }).toString().slice("v=".length);
  const pair = `${encode(config.clientId)}:${encode(config.clientSecret)}`;
  return `Basic ${Buffer.from(pair).toString("base64")}`;
}

async function exchange(
  config: LoginConfig,
  provider: Provider,
  code: string,
  pending: Pending,
): Promise<string> {
  const result = await send(provider.tokenEndpoint, {
    method: "POST",
    headers: {
      Accept: "application/json",
      Authorization: basicAuthorization(config),
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      code,
      redirect_uri: config.redirectUri,
      code_verifier: pending.codeVerifier,
    }).toString(),
  });
  if (result.status !== 200) {
    throw new Error(`토큰 끝점 응답이 ${String(result.status)} 이다`);
  }
  const body = parseObject(result.text, "토큰 응답");
  if (textOf(body, "token_type", "토큰 응답").toLowerCase() !== "bearer") {
    throw new Error("토큰 응답의 token_type 이 bearer 가 아니다");
  }
  return textOf(body, "id_token", "토큰 응답");
}

async function signingKey(provider: Provider, kid: unknown): Promise<KeyObject> {
  const result = await send(provider.jwksUri, {
    method: "GET",
    headers: { Accept: "application/json" },
  });
  if (result.status !== 200) {
    throw new Error(`공개 키 끝점 응답이 ${String(result.status)} 이다`);
  }
  const listed: unknown = parseObject(result.text, "공개 키 문서")["keys"];
  const keys: unknown[] = Array.isArray(listed) ? listed : [];
  const candidates = keys
    .filter(isRecord)
    .filter((key) => key["kty"] === "RSA" && (key["use"] === undefined || key["use"] === "sig"))
    .filter((key) => kid === undefined || key["kid"] === kid);
  const [jwk, ...rest] = candidates;
  if (jwk === undefined || rest.length > 0) {
    throw new Error("서명 키를 하나로 고르지 못했다");
  }
  return createPublicKey({
    key: { kty: "RSA", n: textOf(jwk, "n", "공개 키"), e: textOf(jwk, "e", "공개 키") },
    format: "jwk",
  });
}

async function subjectOf(
  config: LoginConfig,
  provider: Provider,
  idToken: string,
  pending: Pending,
): Promise<string> {
  const [head, body, signature, ...extra] = idToken.split(".");
  if (head === undefined || body === undefined || signature === undefined || extra.length > 0) {
    throw new Error("ID 토큰이 세 토막이 아니다");
  }
  const header = parseObject(Buffer.from(head, "base64url").toString("utf8"), "ID 토큰 머리");
  if (header["alg"] !== "RS256") {
    throw new Error("ID 토큰의 alg 가 RS256 이 아니다");
  }
  const key = await signingKey(provider, header["kid"]);
  const signed = Buffer.from(`${head}.${body}`);
  if (!verify("RSA-SHA256", signed, key, Buffer.from(signature, "base64url"))) {
    throw new Error("ID 토큰의 서명이 맞지 않는다");
  }
  const claims = parseObject(Buffer.from(body, "base64url").toString("utf8"), "ID 토큰");
  if (claims["iss"] !== provider.issuer) {
    throw new Error("ID 토큰의 iss 가 발급자와 다르다");
  }
  const audiences = stringsOf(claims["aud"]);
  if (!audiences.includes(config.clientId)) {
    throw new Error("ID 토큰의 aud 에 이 클라이언트가 없다");
  }
  const authorizedParty = claims["azp"];
  if (audiences.length > 1 && authorizedParty === undefined) {
    throw new Error("aud 가 여럿인데 azp 가 없다");
  }
  if (authorizedParty !== undefined && authorizedParty !== config.clientId) {
    throw new Error("ID 토큰의 azp 가 이 클라이언트가 아니다");
  }
  const expires = claims["exp"];
  const nowSeconds = Math.floor(Date.now() / 1000);
  if (typeof expires !== "number" || expires <= nowSeconds - CLOCK_TOLERANCE_SECONDS) {
    throw new Error("ID 토큰이 만료됐다");
  }
  if (typeof claims["iat"] !== "number") {
    throw new Error("ID 토큰에 iat 가 없다");
  }
  const nonce = claims["nonce"];
  if (typeof nonce !== "string" || !sameText(nonce, pending.nonce)) {
    throw new Error("ID 토큰의 nonce 가 보낸 값과 다르다");
  }
  return textOf(claims, "sub", "ID 토큰");
}

async function finish(config: LoginConfig, callbackUrl: string, pending: Pending): Promise<string> {
  const provider = await discover(config);
  const code = codeFrom(callbackUrl, provider, pending);
  const idToken = await exchange(config, provider, code, pending);
  return subjectOf(config, provider, idToken, pending);
}

export const hand: OidcClient = { begin, finish };
