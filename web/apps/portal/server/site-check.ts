/**
 * 시작 검사 가운데 사이트 파일과 개인 키를 대 보는 갈래(pilot-portal 명세 "시작 검사와 진단"). 설정의 모양은
 * `config.ts` 가 보고, 여기서는 이미 모양이 맞은 설정을 읽은 사이트 파일과 개인 키에 댄다. 파일을 읽지 않는 순수 함수다.
 *
 * 설정의 사이트마다 사이트 파일을 대 보는 여섯 갈래 가운데 다섯이 이 파일에 있다(사이트 파일이 `site-file` 패키지의
 * 판정을 지나지 못하는 것은 읽는 `load.ts` 가 본다).
 *
 * - `issuer` 가 사이트 파일에 없다.
 * - `agent` 가 그 사이트의 열 에이전트 밖이다.
 * - `public_origin` 이 그 사이트의 허용 출처 밖이다.
 * - `kid` 가 그 사이트의 공개 키에 없다.
 * - `kid` 로 고른 공개 키가 개인 키에서 난 공개 키와 다르다(SPKI DER 바이트로 견준다).
 *
 * 진단은 `<자리>: <까닭>` 이고 까닭에 값(키의 글, 에이전트와 출처의 이름)을 싣지 않는다.
 */

import { createPrivateKey, createPublicKey, type KeyObject } from "node:crypto";
import type { Site, SiteFile } from "@agent-os/site-file";
import type { PortalConfig } from "./config.ts";

export type PrivateKeyRead = { readonly key: KeyObject } | { readonly problem: string };

/** 개인 키 PEM 의 글에서 RSA 개인 키를 읽는다. PKCS#8 과 PKCS#1 둘 다 받는다. 까닭에 글은 싣지 않는다. */
export function readPrivateKey(text: string): PrivateKeyRead {
  let key: KeyObject;
  try {
    key = createPrivateKey(text);
  } catch {
    return { problem: "portal.private_key: 개인 키로 읽지 못한다" };
  }
  if (key.asymmetricKeyType !== "rsa") {
    return { problem: "portal.private_key: RSA 개인 키가 아니다" };
  }
  return { key };
}

/** 설정의 사이트마다 사이트 파일과 개인 키를 대 본 어긋남들. `privateKey` 가 없으면 키가 맞는지는 보지 않는다. */
export function siteProblems(
  config: PortalConfig,
  siteFile: SiteFile,
  privateKey: KeyObject | undefined,
): readonly string[] {
  return config.sites.flatMap((entry, index) => {
    const site = siteFile.sites.find(({ issuer }) => issuer === entry.issuer);
    if (site === undefined) {
      return [`sites[${String(index)}].issuer: 사이트 파일에 없다`];
    }
    return [
      ...(site.agents.includes(entry.agent)
        ? []
        : [`sites[${String(index)}].agent: 사이트 파일이 그 사이트에 연 에이전트 밖이다`]),
      ...(site.allowedOrigins.includes(config.publicOrigin)
        ? []
        : [`portal.public_origin: sites[${String(index)}]의 허용 출처에 들지 않는다`]),
      ...keyProblems(config.kid, site, privateKey, index),
    ];
  });
}

function keyProblems(
  kid: string,
  site: Site,
  privateKey: KeyObject | undefined,
  index: number,
): readonly string[] {
  const where = `sites[${String(index)}]`;
  const chosen = site.publicKeys.find((key) => key.kid === kid);
  if (chosen === undefined) {
    return [`portal.kid: ${where}의 공개 키에 그 kid 가 없다`];
  }
  if (privateKey === undefined) {
    return [];
  }
  const published = spkiOf(chosen.pem);
  if (published === undefined) {
    return [`portal.kid: ${where}에서 그 kid 로 고른 공개 키를 읽지 못한다`];
  }
  const own = spkiOf(privateKey);
  return own !== undefined && published.equals(own)
    ? []
    : [`portal.kid: ${where}에서 그 kid 로 고른 공개 키가 개인 키에서 난 공개 키와 다르다`];
}

/**
 * 공개 키의 SPKI DER 바이트. 공개 키 PEM 이나 개인 키 객체(그 키에서 난 공개 키)를 받는다. 읽히지 않으면 undefined.
 * `createPublicKey` 는 공개 키 객체를 받지 않는다.
 */
function spkiOf(source: string | KeyObject): Buffer | undefined {
  try {
    return createPublicKey(source).export({ type: "spki", format: "der" });
  } catch {
    return undefined;
  }
}
