// 시험이 쓰는 설정과 사이트 파일, 키의 도우미. 질문 페이지의 시험은 파일을 임시 폴더에 짓고 키 파일은 커밋하지 않는다.
// 키는 `node:crypto` 가 짓고 같은 시험 프로세스 안에서는 두 벌만 만든다(2048 비트 RSA 키 생성은 느려서 시험마다 새로 만들지 않는다).

import { createPrivateKey, generateKeyPairSync } from "node:crypto";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { stringify, type TomlValue } from "smol-toml";

export const PUBLIC_ORIGIN = "http://portal.localhost:8080";
export const ISSUER = "https://demo.example";
export const KID = "portal-1";

export interface KeyMaterial {
  /** PKCS#8 PEM. 키 만들기 명령이 쓰는 꼴이다. */
  readonly pkcs8: string;
  /** PKCS#1 PEM(`BEGIN RSA PRIVATE KEY`). */
  readonly pkcs1: string;
  /** 사이트 파일의 `pem` 에 싣는 SPKI PEM. */
  readonly spki: string;
}

const KEYS = new Map<number, KeyMaterial>();

/** `slot` 마다 다른 RSA 키 한 벌. 같은 `slot` 은 같은 키다. */
export function rsaKey(slot = 0): KeyMaterial {
  const known = KEYS.get(slot);
  if (known !== undefined) {
    return known;
  }
  const { privateKey, publicKey } = generateKeyPairSync("rsa", {
    modulusLength: 2048,
    publicKeyEncoding: { type: "spki", format: "pem" },
    privateKeyEncoding: { type: "pkcs8", format: "pem" },
  });
  const pkcs1 = createPrivateKey(privateKey).export({ type: "pkcs1", format: "pem" });
  const made = { pkcs8: privateKey, pkcs1: pkcs1.toString(), spki: publicKey };
  KEYS.set(slot, made);
  return made;
}

/** RSA 가 아닌 개인 키(타원 곡선)의 PKCS#8 PEM. */
export function ecPrivateKeyPem(): string {
  return generateKeyPairSync("ec", {
    namedCurve: "prime256v1",
    privateKeyEncoding: { type: "pkcs8", format: "pem" },
    publicKeyEncoding: { type: "spki", format: "pem" },
  }).privateKey;
}

export interface SiteSpec {
  issuer: string;
  /** 주지 않으면 `agent-os` 다. */
  audience?: string;
  agents: string[];
  allowedOrigins: string[];
  keys: { kid?: string; pem: string }[];
}

/** 사이트 파일의 글. 발급자마다 한 사이트다. */
export function siteFileToml(sites: readonly SiteSpec[]): string {
  return stringify({
    schema_version: "1",
    sites: sites.map(({ issuer, audience, agents, allowedOrigins, keys }) => ({
      issuer,
      audience: audience ?? "agent-os",
      agents,
      allowed_origins: allowedOrigins,
      public_keys: keys,
    })),
  });
}

export interface ConfigDoc {
  schema_version: TomlValue;
  portal: Record<string, TomlValue>;
  sites: Record<string, TomlValue>[];
}

/** 맞는 질문 페이지 설정. 시험이 한 칸씩 고쳐 stringify 한다. 부를 때마다 새 객체다. */
export function configDoc(): ConfigDoc {
  return {
    schema_version: "1",
    portal: {
      public_origin: PUBLIC_ORIGIN,
      private_key: "keys/portal.pem",
      kid: KID,
      port: 8080,
    },
    sites: [
      {
        name: "demo",
        issuer: ISSUER,
        agent: "calc",
        heading: "계산기",
        assurance: "anonymous",
      },
    ],
  };
}

export function configToml(doc: ConfigDoc): string {
  return stringify(doc);
}

/** 맞는 사이트 파일의 사이트. 설정의 `configDoc()` 이 가리키는 것이다. */
export function siteSpec(): SiteSpec {
  return {
    issuer: ISSUER,
    agents: ["calc"],
    allowedOrigins: [PUBLIC_ORIGIN],
    keys: [{ kid: KID, pem: rsaKey().spki }],
  };
}

export interface Setup {
  readonly dir: string;
  readonly configPath: string;
  readonly siteFilePath: string;
  readonly privateKeyPath: string;
}

export interface SetupEdits {
  config?: (doc: ConfigDoc) => void;
  sites?: (sites: SiteSpec[]) => void;
  /** 개인 키 파일의 글. 주지 않으면 `rsaKey()` 의 PKCS#8 이다. `null` 이면 파일을 쓰지 않는다. */
  privateKey?: string | null;
}

/** 임시 폴더에 설정, 사이트 파일, 개인 키를 쓴다. 기본은 서로 맞는 셋이다. */
export function writeSetup(edits: SetupEdits = {}): Setup {
  const dir = mkdtempSync(join(tmpdir(), "portal-"));
  const doc = configDoc();
  edits.config?.(doc);
  const sites = [siteSpec()];
  edits.sites?.(sites);
  const configPath = join(dir, "portal.toml");
  const siteFilePath = join(dir, "sites.toml");
  const privateKeyPath = join(dir, "keys", "portal.pem");
  writeFileSync(configPath, configToml(doc), "utf-8");
  writeFileSync(siteFilePath, siteFileToml(sites), "utf-8");
  if (edits.privateKey !== null) {
    writeKeyFile(privateKeyPath, edits.privateKey ?? rsaKey().pkcs8);
  }
  return { dir, configPath, siteFilePath, privateKeyPath };
}

function writeKeyFile(path: string, text: string): void {
  // `keys/` 폴더는 설정의 상대 경로(`keys/portal.pem`)가 가리키는 자리다.
  mkdirSync(join(path, ".."), { recursive: true });
  writeFileSync(path, text, "utf-8");
}
