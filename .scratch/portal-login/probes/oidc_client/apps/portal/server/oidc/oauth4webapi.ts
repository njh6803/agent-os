// 후보 나: oauth4webapi(3.x)와 jose(6.x). 프로브의 것이고 제품 코드가 아니다.
//
// `signature` 는 셋을 받는다. `default` 는 oauth4webapi 의 기본 그대로(서명 검증을 따로 부르지 않는다), `oauth4webapi` 는
// 그 라이브러리의 `validateApplicationLevelSignature`, `jose` 는 jose 의 `jwtVerify` 와 `createRemoteJWKSet` 이다.

import { createRemoteJWKSet, customFetch as joseCustomFetch, jwtVerify } from "jose";
import * as oauth from "oauth4webapi";
import type { Begun, LoginConfig, OidcClient, Pending } from "./contract.ts";
import { nodeFetch } from "./node-fetch.ts";

const SIGNATURES = ["default", "oauth4webapi", "jose"];

interface HttpOptions {
  [oauth.allowInsecureRequests]?: boolean;
  [oauth.customFetch]?: typeof nodeFetch;
}

function httpOptions(config: LoginConfig): HttpOptions {
  const options: HttpOptions = {};
  if (config.insecure === "allow") {
    options[oauth.allowInsecureRequests] = true;
  }
  if (config.transport === "node-http") {
    options[oauth.customFetch] = nodeFetch;
  }
  return options;
}

async function discover(config: LoginConfig): Promise<oauth.AuthorizationServer> {
  if (!SIGNATURES.includes(config.signature)) {
    throw new Error(`oauth4webapi 후보가 모르는 signature: ${config.signature}`);
  }
  const issuer = new URL(config.issuer);
  const response = await oauth.discoveryRequest(issuer, httpOptions(config));
  return oauth.processDiscoveryResponse(issuer, response);
}

async function begin(config: LoginConfig): Promise<Begun> {
  const server = await discover(config);
  if (server.authorization_endpoint === undefined) {
    throw new Error("설정 문서에 인가 끝점이 없다");
  }
  const codeVerifier = oauth.generateRandomCodeVerifier();
  const state = oauth.generateRandomState();
  const nonce = oauth.generateRandomNonce();
  const url = new URL(server.authorization_endpoint);
  url.searchParams.set("client_id", config.clientId);
  url.searchParams.set("redirect_uri", config.redirectUri);
  url.searchParams.set("response_type", "code");
  url.searchParams.set("scope", "openid");
  url.searchParams.set("code_challenge", await oauth.calculatePKCECodeChallenge(codeVerifier));
  url.searchParams.set("code_challenge_method", "S256");
  url.searchParams.set("state", state);
  url.searchParams.set("nonce", nonce);
  return { authorizationUrl: url.href, pending: { state, nonce, codeVerifier } };
}

async function verifyWithJose(
  config: LoginConfig,
  server: oauth.AuthorizationServer,
  idToken: string | undefined,
): Promise<void> {
  if (idToken === undefined || server.jwks_uri === undefined) {
    throw new Error("ID 토큰이나 공개 키 끝점이 없다");
  }
  const keys = createRemoteJWKSet(
    new URL(server.jwks_uri),
    config.transport === "node-http" ? { [joseCustomFetch]: nodeFetch } : {},
  );
  await jwtVerify(idToken, keys, {
    issuer: server.issuer,
    audience: config.clientId,
    algorithms: ["RS256"],
  });
}

async function finish(config: LoginConfig, callbackUrl: string, pending: Pending): Promise<string> {
  const server = await discover(config);
  const client: oauth.Client = { client_id: config.clientId };
  const parameters = oauth.validateAuthResponse(
    server,
    client,
    new URL(callbackUrl),
    pending.state,
  );
  const response = await oauth.authorizationCodeGrantRequest(
    server,
    client,
    oauth.ClientSecretBasic(config.clientSecret),
    parameters,
    config.redirectUri,
    pending.codeVerifier,
    httpOptions(config),
  );
  const result = await oauth.processAuthorizationCodeResponse(server, client, response, {
    expectedNonce: pending.nonce,
    requireIdToken: true,
  });
  if (config.signature === "oauth4webapi") {
    await oauth.validateApplicationLevelSignature(server, response, httpOptions(config));
  }
  if (config.signature === "jose") {
    await verifyWithJose(config, server, result.id_token);
  }
  const claims = oauth.getValidatedIdTokenClaims(result);
  if (claims === undefined) {
    throw new Error("토큰 응답에 ID 토큰이 없다");
  }
  return claims.sub;
}

export const oauth4webapi: OidcClient = { begin, finish };
