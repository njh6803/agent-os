// 가짜 로그인 서버 후보 ㄱ: `node:http`(TLS 회차는 `node:https`)와 `node:crypto` 로 직접 짠 최소 구현. 프로브의 것이고
// 제품 코드가 아니다. 끝점은 넷이다. 설정 문서, 인가 끝점, 토큰 끝점, 공개 키 끝점.
//
// 인가 끝점은 화면 없이 바로 돌려보낸다. 요청마다 무엇을 받았고 무엇을 판정했는지 `log` 에 세어, 회차가 재려는 상황이
// 실제로 났는지(PKCE 를 서버가 맞춰 봤다, 공개 키를 받아 갔다, 고장을 심은 토큰을 내줬다)를 읽는 쪽이 본다.
// `fault` 는 ID 토큰에 고장 하나를 심는다. 클라이언트가 그 토큰을 받고도 `sub` 를 내면 그 검사를 하지 않는 것이다.

import {
  createHash,
  createHmac,
  generateKeyPairSync,
  type KeyObject,
  randomBytes,
  sign,
} from "node:crypto";
import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import { createServer as createTlsServer } from "node:https";

export const FAULTS = [
  "none",
  "bad_signature",
  "wrong_issuer",
  "wrong_audience",
  "expired",
  "wrong_nonce",
  "missing_nonce",
  "alg_none",
  "alg_hs256",
] as const;
export type Fault = (typeof FAULTS)[number];

export interface IdpLog {
  discovery: number;
  jwks: number;
  authorize: number;
  /** 인가 요청이 PKCE(S256), `state`, `nonce`, `scope=openid`, `response_type=code` 를 모두 들었던 횟수. */
  authorizeComplete: number;
  token: number;
  /** 토큰 요청의 `code_verifier` 가 인가 요청의 `code_challenge` 와 맞았던 횟수. */
  pkceVerified: number;
  /** 토큰 요청이 클라이언트를 어떻게 증명했는지(`basic`, `post`). */
  clientAuthentication: string[];
  /** 고장을 심은 ID 토큰을 내준 횟수. */
  faultyTokens: number;
  /** 토큰 끝점이 거절한 까닭. */
  tokenErrors: string[];
}

export interface FakeIdpOptions {
  readonly clientId: string;
  readonly clientSecret: string;
  readonly redirectUri: string;
  readonly subject: string;
  readonly fault: Fault;
  /** 주면 `https` 로 듣는다. PEM 글이다. */
  readonly tls?: { readonly key: string; readonly cert: string };
}

export interface FakeIdp {
  readonly issuer: string;
  readonly log: IdpLog;
  close(): Promise<void>;
}

interface Grant {
  readonly codeChallenge: string;
  readonly nonce: string;
}

const KID = "probe-key-1";

function encode(value: object): string {
  return Buffer.from(JSON.stringify(value)).toString("base64url");
}

function idToken(
  issuer: string,
  options: FakeIdpOptions,
  nonce: string,
  keys: { readonly good: KeyObject; readonly other: KeyObject },
): string {
  const { fault } = options;
  const now = Math.floor(Date.now() / 1000);
  const issuedAt = fault === "expired" ? now - 7200 : now;
  const claims: Record<string, unknown> = {
    iss: fault === "wrong_issuer" ? `${issuer}/other` : issuer,
    sub: options.subject,
    aud: fault === "wrong_audience" ? "someone-else" : options.clientId,
    iat: issuedAt,
    exp: issuedAt + (fault === "expired" ? 3600 : 300),
  };
  if (fault !== "missing_nonce") {
    claims["nonce"] = fault === "wrong_nonce" ? "tampered-nonce" : nonce;
  }
  const body = encode(claims);
  if (fault === "alg_none") {
    return `${encode({ alg: "none", typ: "JWT" })}.${body}.`;
  }
  if (fault === "alg_hs256") {
    const head = encode({ alg: "HS256", typ: "JWT", kid: KID });
    const mac = createHmac("sha256", options.clientSecret).update(`${head}.${body}`).digest();
    return `${head}.${body}.${mac.toString("base64url")}`;
  }
  const head = encode({ alg: "RS256", typ: "JWT", kid: KID });
  const key = fault === "bad_signature" ? keys.other : keys.good;
  const signature = sign("RSA-SHA256", Buffer.from(`${head}.${body}`), key);
  return `${head}.${body}.${signature.toString("base64url")}`;
}

function readBody(incoming: IncomingMessage): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    incoming.on("data", (chunk: Buffer) => {
      chunks.push(chunk);
    });
    incoming.on("error", reject);
    incoming.on("end", () => {
      resolve(Buffer.concat(chunks).toString("utf8"));
    });
  });
}

function json(outgoing: ServerResponse, status: number, body: object): void {
  outgoing.writeHead(status, { "Content-Type": "application/json", "Cache-Control": "no-store" });
  outgoing.end(JSON.stringify(body));
}

/** Basic 머리나 폼의 `client_id`·`client_secret` 으로 클라이언트를 알아본다. 맞으면 방법의 이름을 낸다. */
function authenticate(
  incoming: IncomingMessage,
  form: URLSearchParams,
  options: FakeIdpOptions,
): string | undefined {
  const header = incoming.headers.authorization;
  if (header?.startsWith("Basic ") === true) {
    const [id, secret] = Buffer.from(header.slice("Basic ".length), "base64")
      .toString("utf8")
      .split(":");
    const matches =
      decodeURIComponent(id ?? "") === options.clientId &&
      decodeURIComponent(secret ?? "") === options.clientSecret;
    return matches ? "basic" : undefined;
  }
  const matches =
    form.get("client_id") === options.clientId && form.get("client_secret") === options.clientSecret;
  return matches ? "post" : undefined;
}

export function startFakeIdp(options: FakeIdpOptions): Promise<FakeIdp> {
  const good = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const other = generateKeyPairSync("rsa", { modulusLength: 2048 });
  const grants = new Map<string, Grant>();
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
  let issuer = "";

  function authorize(url: URL, outgoing: ServerResponse): void {
    log.authorize += 1;
    const query = url.searchParams;
    const state = query.get("state");
    const nonce = query.get("nonce");
    const codeChallenge = query.get("code_challenge");
    const complete =
      query.get("client_id") === options.clientId &&
      query.get("redirect_uri") === options.redirectUri &&
      query.get("response_type") === "code" &&
      (query.get("scope") ?? "").split(" ").includes("openid") &&
      query.get("code_challenge_method") === "S256";
    if (!complete || state === null || nonce === null || codeChallenge === null) {
      outgoing.writeHead(400, { "Content-Type": "text/plain; charset=utf-8" });
      outgoing.end("인가 요청이 모자라다");
      return;
    }
    log.authorizeComplete += 1;
    const code = randomBytes(16).toString("base64url");
    grants.set(code, { codeChallenge, nonce });
    const back = new URL(options.redirectUri);
    back.searchParams.set("code", code);
    back.searchParams.set("state", state);
    back.searchParams.set("iss", issuer);
    outgoing.writeHead(302, { Location: back.href });
    outgoing.end();
  }

  async function token(incoming: IncomingMessage, outgoing: ServerResponse): Promise<void> {
    log.token += 1;
    const form = new URLSearchParams(await readBody(incoming));
    const refuse = (error: string): void => {
      log.tokenErrors.push(error);
      json(outgoing, 400, { error });
    };
    const method = authenticate(incoming, form, options);
    if (method === undefined) {
      refuse("invalid_client");
      return;
    }
    log.clientAuthentication.push(method);
    const code = form.get("code") ?? "";
    const grant = grants.get(code);
    grants.delete(code);
    if (
      grant === undefined ||
      form.get("grant_type") !== "authorization_code" ||
      form.get("redirect_uri") !== options.redirectUri
    ) {
      refuse("invalid_grant");
      return;
    }
    const verifier = form.get("code_verifier") ?? "";
    if (createHash("sha256").update(verifier).digest("base64url") !== grant.codeChallenge) {
      refuse("invalid_grant_pkce");
      return;
    }
    log.pkceVerified += 1;
    if (options.fault !== "none") {
      log.faultyTokens += 1;
    }
    json(outgoing, 200, {
      access_token: randomBytes(16).toString("base64url"),
      token_type: "Bearer",
      expires_in: 60,
      id_token: idToken(issuer, options, grant.nonce, {
        good: good.privateKey,
        other: other.privateKey,
      }),
    });
  }

  async function route(incoming: IncomingMessage, outgoing: ServerResponse): Promise<void> {
    const url = new URL(incoming.url ?? "/", issuer);
    if (incoming.method === "GET" && url.pathname === "/.well-known/openid-configuration") {
      log.discovery += 1;
      json(outgoing, 200, {
        issuer,
        authorization_endpoint: `${issuer}/authorize`,
        token_endpoint: `${issuer}/token`,
        jwks_uri: `${issuer}/jwks`,
        response_types_supported: ["code"],
        subject_types_supported: ["public"],
        id_token_signing_alg_values_supported: ["RS256"],
        code_challenge_methods_supported: ["S256"],
        token_endpoint_auth_methods_supported: ["client_secret_basic", "client_secret_post"],
        authorization_response_iss_parameter_supported: true,
      });
      return;
    }
    if (incoming.method === "GET" && url.pathname === "/jwks") {
      log.jwks += 1;
      const jwk = good.publicKey.export({ format: "jwk" });
      json(outgoing, 200, { keys: [{ ...jwk, kid: KID, use: "sig", alg: "RS256" }] });
      return;
    }
    if (incoming.method === "GET" && url.pathname === "/authorize") {
      authorize(url, outgoing);
      return;
    }
    if (incoming.method === "POST" && url.pathname === "/token") {
      await token(incoming, outgoing);
      return;
    }
    outgoing.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    outgoing.end("없는 경로");
  }

  const listener = (incoming: IncomingMessage, outgoing: ServerResponse): void => {
    route(incoming, outgoing).catch((error: unknown) => {
      outgoing.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
      outgoing.end(error instanceof Error ? error.message : "알 수 없는 오류");
    });
  };
  const server: Server =
    options.tls === undefined ? createServer(listener) : createTlsServer(options.tls, listener);

  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen({ host: "127.0.0.1", port: 0 }, () => {
      const address = server.address();
      if (address === null || typeof address === "string") {
        reject(new Error("포트를 알 수 없다"));
        return;
      }
      issuer = `${options.tls === undefined ? "http" : "https"}://127.0.0.1:${String(address.port)}`;
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
