// 사이트 토큰. 서명과 클레임을 공개 키로 검증하고, 익명 주체의 이름이 쿠키 값의 해시임을 시험이 스스로 계산해 대조한다.

import { createHash, createPrivateKey, createPublicKey, randomUUID, verify } from "node:crypto";
import { expect, test } from "vitest";
import { rsaKey } from "../testing/fixtures.ts";
import { anonymousSubject, signSiteToken } from "./token.ts";

const NOW_SECONDS = 1_800_000_000;

function sign(subject: string, nowSeconds = NOW_SECONDS): string {
  return signSiteToken({
    privateKey: createPrivateKey(rsaKey().pkcs8),
    kid: "portal-1",
    issuer: "https://demo.example",
    audience: "agent-os",
    subject,
    nowSeconds,
  });
}

function parts(token: string) {
  const [head, body, signature, ...rest] = token.split(".");
  if (head === undefined || body === undefined || signature === undefined || rest.length > 0) {
    throw new Error("토큰이 세 토막이 아니다");
  }
  const header: unknown = JSON.parse(Buffer.from(head, "base64url").toString("utf-8"));
  const claims: unknown = JSON.parse(Buffer.from(body, "base64url").toString("utf-8"));
  return { head, body, signature, header, claims };
}

test("토큰은 서명 키의 공개 키로 검증된다", () => {
  const { head, body, signature } = parts(sign("anon-x"));

  const valid = verify(
    "RSA-SHA256",
    Buffer.from(`${head}.${body}`),
    createPublicKey(rsaKey().spki),
    Buffer.from(signature, "base64url"),
  );

  expect(valid).toBe(true);
});

test("다른 키의 공개 키로는 검증되지 않는다", () => {
  const { head, body, signature } = parts(sign("anon-x"));

  const valid = verify(
    "RSA-SHA256",
    Buffer.from(`${head}.${body}`),
    createPublicKey(rsaKey(1).spki),
    Buffer.from(signature, "base64url"),
  );

  expect(valid).toBe(false);
});

test("헤더는 RS256 JWT 이고 설정의 kid 를 싣는다", () => {
  expect(parts(sign("anon-x")).header).toEqual({ alg: "RS256", typ: "JWT", kid: "portal-1" });
});

test("본문은 iss, sub, aud, iat, exp 다섯이고 nbf 는 없다", () => {
  const { claims } = parts(sign("anon-x"));

  expect(claims).toEqual({
    iss: "https://demo.example",
    sub: "anon-x",
    aud: "agent-os",
    iat: NOW_SECONDS,
    exp: NOW_SECONDS + 120,
  });
});

test("만료는 발급 시각에서 120초 뒤다", () => {
  for (const now of [0, 1, 1_700_000_000]) {
    const { claims } = parts(sign("anon-x", now));

    expect(claims).toMatchObject({ iat: now, exp: now + 120 });
  }
});

test("익명 주체는 쿠키 값 글자 36자의 SHA-256 을 소문자 16진으로 쓴 앞 32자에 anon- 을 붙인 것이다", () => {
  const id = randomUUID();
  const expected = `anon-${createHash("sha256").update(id, "utf8").digest("hex").slice(0, 32)}`;

  expect(anonymousSubject(id)).toBe(expected);
  expect(anonymousSubject(id)).toMatch(/^anon-[0-9a-f]{32}$/u);
});

test("같은 쿠키 값은 같은 주체이고 다른 값은 다른 주체다", () => {
  const first = randomUUID();
  const second = randomUUID();

  expect(anonymousSubject(first)).toBe(anonymousSubject(first));
  expect(anonymousSubject(first)).not.toBe(anonymousSubject(second));
});

test("주체를 해시로 지은 토큰의 본문에는 쿠키 값 원문이 없다", () => {
  const id = randomUUID();

  const token = sign(anonymousSubject(id));
  const { body } = parts(token);

  expect(token).not.toContain(id);
  expect(Buffer.from(body, "base64url").toString("utf-8")).not.toContain(id);
});
