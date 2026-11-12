// 회차 하나. 가짜 로그인 서버를 `127.0.0.1` 의 임의 포트에 띄우고, 후보 하나로 흐름 한 바퀴(설정 문서 조회, 인가 요청
// 주소, 브라우저 왕복, 돌아온 요청 검증, 토큰 교환, ID 토큰 검증, `sub`)를 돈 뒤 표준 출력에 JSON 한 줄을 낸다.
// node 가 타입만 벗겨 바로 돌린다(빌드 없음). 판정은 `probe/flow.mjs` 가 한다. 프로브의 것이고 제품 코드가 아니다.
//
// 돌리기: node apps/portal/testing/round.ts --client <openid-client|oauth4webapi|hand> [--signature <값>]
//   [--idp <hand|oidc-provider>] [--fault <고장>] [--callback <none|state_mismatch|error>]
//   [--insecure <allow|deny>] [--transport <default|node-http>] [--tls <키와 인증서가 든 폴더>]
// 흐름이 거부로 끝나도 종료 코드는 0 이다(거부가 그 회차의 결과다). 인자가 틀렸거나 서버를 띄우지 못하면 1 이다.

import { randomBytes } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import type { LoginConfig, OidcClient } from "../server/oidc/contract.ts";
import { hand } from "../server/oidc/hand.ts";
import { nodeFetchCalls } from "../server/oidc/node-fetch.ts";
import { oauth4webapi } from "../server/oidc/oauth4webapi.ts";
import { openidClient } from "../server/oidc/openid-client.ts";
import { signIn } from "./browser.ts";
import { type FakeIdp, type FakeIdpOptions, FAULTS, type Fault, startFakeIdp } from "./fake-idp.ts";
import { startProviderIdp } from "./fake-idp-provider.ts";

const CLIENTS: Readonly<Record<string, OidcClient>> = {
  "openid-client": openidClient,
  oauth4webapi,
  hand,
};
const REDIRECT_URI = "https://portal.example.test/portal/login/callback";

function argument(name: string, fallback: string): string {
  const at = process.argv.indexOf(`--${name}`);
  return at < 0 ? fallback : (process.argv[at + 1] ?? fallback);
}

function faultOf(value: string): Fault {
  const fault = FAULTS.find((candidate) => candidate === value);
  if (fault === undefined) {
    throw new Error(`모르는 고장: ${value}`);
  }
  return fault;
}

function oneOf<const T extends string>(name: string, allowed: readonly T[], fallback: T): T {
  const value = argument(name, fallback);
  const found = allowed.find((candidate) => candidate === value);
  if (found === undefined) {
    throw new Error(`--${name} 은 ${allowed.join(", ")} 가운데 하나다: ${value}`);
  }
  return found;
}

/** 돌아온 요청의 주소에 고장을 심는다. 브라우저를 거쳐 오는 값이라 공격자가 바꿀 수 있는 자리다. */
function tamper(callbackUrl: string, callback: "none" | "state_mismatch" | "error"): string {
  const url = new URL(callbackUrl);
  if (callback === "state_mismatch") {
    url.searchParams.set("state", "someone-elses-state");
  }
  if (callback === "error") {
    url.searchParams.delete("code");
    url.searchParams.set("error", "access_denied");
  }
  return url.href;
}

/** 오류의 이름·코드·메시지와 원인 사슬. 원인이 Error 가 아니면(라이브러리가 주소나 주장 객체를 원인에 둔다) 따라가지 않는다. */
function describe(error: unknown): Record<string, unknown> {
  if (!(error instanceof Error)) {
    return { name: "Error 가 아닌 값", code: null, message: String(error), cause: null };
  }
  const code: unknown = Reflect.get(error, "code");
  return {
    name: error.name,
    code: typeof code === "string" ? code : null,
    message: error.message,
    cause: error.cause instanceof Error ? describe(error.cause) : null,
  };
}

async function main(): Promise<void> {
  const clientName = argument("client", "");
  const client = CLIENTS[clientName];
  if (client === undefined) {
    throw new Error(`모르는 후보: ${clientName}`);
  }
  const idpName = oneOf("idp", ["hand", "oidc-provider"], "hand");
  const callback = oneOf("callback", ["none", "state_mismatch", "error"], "none");
  const tlsFolder = argument("tls", "");
  const subject = `user-${randomBytes(6).toString("hex")}`;
  const idpOptions: FakeIdpOptions = {
    clientId: "portal",
    clientSecret: randomBytes(24).toString("base64url"),
    redirectUri: REDIRECT_URI,
    subject,
    fault: faultOf(argument("fault", "none")),
    ...(tlsFolder === ""
      ? {}
      : {
          tls: {
            key: readFileSync(join(tlsFolder, "server.key"), "utf8"),
            cert: readFileSync(join(tlsFolder, "server.crt"), "utf8"),
          },
        }),
  };
  const idp: FakeIdp = await (idpName === "hand"
    ? startFakeIdp(idpOptions)
    : startProviderIdp(idpOptions));
  const config: LoginConfig = {
    issuer: idp.issuer,
    clientId: idpOptions.clientId,
    clientSecret: idpOptions.clientSecret,
    redirectUri: REDIRECT_URI,
    insecure: oneOf("insecure", ["allow", "deny"], "allow"),
    signature: argument("signature", "verify"),
    transport: oneOf("transport", ["default", "node-http"], "default"),
  };

  let stage = "begin";
  let outcome: Record<string, unknown>;
  try {
    const begun = await client.begin(config);
    stage = "sign-in";
    const returned = await signIn(begun.authorizationUrl, {
      redirectUri: REDIRECT_URI,
      accountId: subject,
    });
    stage = "finish";
    const sub = await client.finish(config, tamper(returned, callback), begun.pending);
    outcome = { outcome: "accepted", sub, subMatches: sub === subject };
  } catch (error: unknown) {
    outcome = { outcome: "rejected", stage, error: describe(error) };
  }
  await idp.close();
  console.log(
    JSON.stringify({
      client: clientName,
      signature: config.signature,
      idp: idpName,
      issuerScheme: new URL(idp.issuer).protocol,
      fault: idpOptions.fault,
      callback,
      insecure: config.insecure,
      transport: config.transport,
      node: process.version,
      // 회차의 환경이 뜻한 대로였는지 읽는 쪽이 본다. 값은 싣지 않고 있었는지만 싣는다.
      extraCaGiven: process.env["NODE_EXTRA_CA_CERTS"] !== undefined,
      systemCaGiven: process.env["NODE_USE_SYSTEM_CA"] !== undefined,
      ...outcome,
      idpLog: idp.log,
      nodeFetchCalls: nodeFetchCalls(),
    }),
  );
}

main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
