// 후보 가: openid-client(6.x). 프로브의 것이고 제품 코드가 아니다.
//
// `signature` 는 `default`(라이브러리 기본 그대로)와 `verify`(`enableNonRepudiationChecks` 를 켠다) 둘을 받는다.

import * as client from "openid-client";
import type { Begun, LoginConfig, OidcClient, Pending } from "./contract.ts";
import { nodeFetch } from "./node-fetch.ts";

function configure(config: LoginConfig): Promise<client.Configuration> {
  if (config.signature !== "default" && config.signature !== "verify") {
    throw new Error(`openid-client 후보가 모르는 signature: ${config.signature}`);
  }
  const execute: ((configuration: client.Configuration) => void)[] = [];
  if (config.insecure === "allow") {
    execute.push(client.allowInsecureRequests);
  }
  if (config.signature === "verify") {
    execute.push(client.enableNonRepudiationChecks);
  }
  const options: client.DiscoveryRequestOptions = { execute };
  if (config.transport === "node-http") {
    options[client.customFetch] = nodeFetch;
  }
  return client.discovery(
    new URL(config.issuer),
    config.clientId,
    config.clientSecret,
    client.ClientSecretBasic(config.clientSecret),
    options,
  );
}

async function begin(config: LoginConfig): Promise<Begun> {
  const configuration = await configure(config);
  const codeVerifier = client.randomPKCECodeVerifier();
  const state = client.randomState();
  const nonce = client.randomNonce();
  const url = client.buildAuthorizationUrl(configuration, {
    redirect_uri: config.redirectUri,
    scope: "openid",
    code_challenge: await client.calculatePKCECodeChallenge(codeVerifier),
    code_challenge_method: "S256",
    state,
    nonce,
  });
  return { authorizationUrl: url.href, pending: { state, nonce, codeVerifier } };
}

async function finish(config: LoginConfig, callbackUrl: string, pending: Pending): Promise<string> {
  const configuration = await configure(config);
  const tokens = await client.authorizationCodeGrant(configuration, new URL(callbackUrl), {
    pkceCodeVerifier: pending.codeVerifier,
    expectedState: pending.state,
    expectedNonce: pending.nonce,
    idTokenExpected: true,
  });
  const claims = tokens.claims();
  if (claims === undefined) {
    throw new Error("토큰 응답에 ID 토큰이 없다");
  }
  return claims.sub;
}

export const openidClient: OidcClient = { begin, finish };
