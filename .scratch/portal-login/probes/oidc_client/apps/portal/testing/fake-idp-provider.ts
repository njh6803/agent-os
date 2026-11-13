// 가짜 로그인 서버 후보 ㄴ: `oidc-provider` 패키지. 프로브의 것이고 제품 코드가 아니다.
//
// 설정은 클라이언트 하나와 계정 찾기뿐이고 나머지는 패키지의 기본값이다. 로그인과 동의 화면은 패키지의 개발용 화면
// (`devInteractions`)을 그대로 두고 `browser.ts` 가 그 폼을 대신 낸다. 서명 키와 쿠키 키도 패키지의 개발용 기본값이다.
// 요청 수는 패키지 앞에 둔 `node:http` 서버가 경로로 센다. 고장을 심는 길은 두지 않았다(`fault` 는 `none` 만 받는다).

import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import Provider from "oidc-provider";
import type { FakeIdp, FakeIdpOptions, IdpLog } from "./fake-idp.ts";

type Listener = (incoming: IncomingMessage, outgoing: ServerResponse) => Promise<void>;

export function startProviderIdp(options: FakeIdpOptions): Promise<FakeIdp> {
  if (options.fault !== "none" || options.tls !== undefined) {
    throw new Error("oidc-provider 후보는 고장과 TLS 회차를 돌지 않는다");
  }
  const log: IdpLog = {
    discovery: 0,
    jwks: 0,
    authorize: 0,
    authorizeComplete: 0,
    token: 0,
    pkceVerified: 0,
    clientAuthentication: [],
    faultyTokens: 0,
    tokenErrors: [],
  };
  let listener: Listener | undefined;
  const server = createServer((incoming, outgoing) => {
    const path = new URL(incoming.url ?? "/", "http://127.0.0.1").pathname;
    if (path === "/.well-known/openid-configuration") {
      log.discovery += 1;
    } else if (path === "/jwks") {
      log.jwks += 1;
    } else if (path === "/auth") {
      log.authorize += 1;
    } else if (path === "/token") {
      log.token += 1;
    }
    if (listener === undefined) {
      outgoing.writeHead(503);
      outgoing.end();
      return;
    }
    listener(incoming, outgoing).catch((error: unknown) => {
      outgoing.destroy(error instanceof Error ? error : undefined);
    });
  });

  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen({ host: "127.0.0.1", port: 0 }, () => {
      const address = server.address();
      if (address === null || typeof address === "string") {
        reject(new Error("포트를 알 수 없다"));
        return;
      }
      const issuer = `http://127.0.0.1:${String(address.port)}`;
      const provider = new Provider(issuer, {
        clients: [
          {
            client_id: options.clientId,
            client_secret: options.clientSecret,
            redirect_uris: [options.redirectUri],
            response_types: ["code"],
            grant_types: ["authorization_code"],
            token_endpoint_auth_method: "client_secret_basic",
          },
        ],
        findAccount: (_context, id) => ({ accountId: id, claims: () => ({ sub: id }) }),
      });
      // 인가 코드를 내줄 때와 토큰을 내줄 때 패키지가 내는 이벤트로 PKCE 와 인가 요청의 모양을 센다.
      provider.on("authorization.success", (context) => {
        const parameters = context.oidc.params;
        if (
          parameters?.["code_challenge_method"] === "S256" &&
          typeof parameters["state"] === "string" &&
          typeof parameters["nonce"] === "string"
        ) {
          log.authorizeComplete += 1;
        }
      });
      provider.on("grant.success", (context) => {
        if (typeof context.oidc.params?.["code_verifier"] === "string") {
          log.pkceVerified += 1;
        }
        log.clientAuthentication.push(
          context.headers.authorization?.startsWith("Basic ") === true ? "basic" : "post",
        );
      });
      provider.on("grant.error", (_context, error) => {
        log.tokenErrors.push(error.message);
      });
      listener = provider.callback();
      resolve({
        issuer,
        log,
        close: () =>
          new Promise((done) => {
            server.close(() => {
              done();
            });
            server.closeAllConnections();
          }),
      });
    });
  });
}
