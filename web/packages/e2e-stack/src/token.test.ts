import { createPublicKey, verify } from "node:crypto";
import { expect, test } from "vitest";
import { AUDIENCE, ISSUER, KEY_ID, principalOf, signToken, siteKey } from "./token.ts";

function claims(token: string): Record<string, unknown> {
  const [, body] = token.split(".");
  const parsed: unknown = JSON.parse(Buffer.from(body ?? "", "base64url").toString("utf-8"));
  if (typeof parsed !== "object" || parsed === null) {
    throw new Error("토큰 본문이 객체가 아니다");
  }
  return Object.fromEntries(Object.entries(parsed));
}

test("실행 주체는 발급자와 sub 를 세로 막대로 잇는다", () => {
  expect(principalOf("alice")).toBe(`${ISSUER}|alice`);
});

test("토큰의 발급자와 sub 클레임을 세로 막대로 이은 값이 실행 주체와 같고 대상은 사이트 파일의 audience 다", () => {
  const token = signToken(siteKey(), "alice");
  const body = claims(token);

  expect(`${String(body["iss"])}|${String(body["sub"])}`).toBe(principalOf("alice"));
  expect(body["aud"]).toBe(AUDIENCE);
});

test("토큰은 사이트 파일에 실리는 공개 키로 검증된다", () => {
  const key = siteKey();
  const [head, body, signature] = signToken(key, "alice").split(".");

  expect(JSON.parse(Buffer.from(head ?? "", "base64url").toString("utf-8"))).toMatchObject({
    alg: "RS256",
    kid: KEY_ID,
  });
  expect(
    verify(
      "RSA-SHA256",
      Buffer.from(`${head ?? ""}.${body ?? ""}`),
      createPublicKey(key.publicPem),
      Buffer.from(signature ?? "", "base64url"),
    ),
  ).toBe(true);
});

test("sub 를 주지 않으면 토큰마다 새 주체다", () => {
  const key = siteKey();

  expect(claims(signToken(key))["sub"]).not.toBe(claims(signToken(key))["sub"]);
});
