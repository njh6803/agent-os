// 시작 검사. 설정, 사이트 파일, 개인 키를 실제 파일로 읽어 서로 맞는지 본다. 파일은 임시 폴더에 짓는다.

import { writeFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "vitest";
import {
  type ConfigDoc,
  ecPrivateKeyPem,
  ISSUER,
  KID,
  PUBLIC_ORIGIN,
  rsaKey,
  type SetupEdits,
  type SiteSpec,
  writeSetup,
} from "../testing/fixtures.ts";
import { COOKIE_LIFETIME_DAYS } from "./cookie-policy.ts";
import { loadPortal } from "./load.ts";

// 어긋난 파일의 글이 진단에 실리지 않는 것을 보려고 파일에 넣는 글자.
const SECRET = "SECRET-KEY-TEXT";

function load(edits: SetupEdits = {}) {
  const setup = writeSetup(edits);
  return loadPortal(setup.configPath, setup.siteFilePath);
}

function problemsOf(edits: SetupEdits): readonly string[] {
  const result = load(edits);
  if (!("problems" in result)) {
    throw new Error("어긋난 파일이 받아들여졌다");
  }
  return result.problems;
}

function configSite(doc: ConfigDoc, index = 0) {
  const site = doc.sites[index];
  if (site === undefined) {
    throw new Error("시험의 설정에 그 사이트가 없다");
  }
  return site;
}

function fileSite(sites: SiteSpec[], index = 0): SiteSpec {
  const site = sites[index];
  if (site === undefined) {
    throw new Error("시험의 사이트 파일에 그 사이트가 없다");
  }
  return site;
}

test("서로 맞는 설정과 사이트 파일과 개인 키면 설정을 낸다", () => {
  const result = load();

  expect("problems" in result).toBe(false);
  expect("config" in result && result.config).toMatchObject({
    publicOrigin: PUBLIC_ORIGIN,
    kid: KID,
    sites: [{ name: "demo", issuer: ISSUER, agent: "calc" }],
  });
});

test("읽어 둔 개인 키와 사이트 파일을 함께 낸다(토큰을 지을 때 서명 키와 audience 를 쓴다)", () => {
  const result = load();

  expect("privateKey" in result && result.privateKey.asymmetricKeyType).toBe("rsa");
  expect("siteFile" in result && result.siteFile.sites).toMatchObject([
    { issuer: ISSUER, audience: "agent-os", agents: ["calc"] },
  ]);
});

test("개인 키가 PKCS#1 PEM 이어도 받는다", () => {
  expect("problems" in load({ privateKey: rsaKey().pkcs1 })).toBe(false);
});

test("읽어 낸 고지 전문에 쿠키 수명 상수의 일수가 선다", () => {
  const result = load();

  expect("config" in result && result.config.sites[0]?.notice).toContain(
    `${String(COOKIE_LIFETIME_DAYS)}일 동안 남습니다.`,
  );
});

test("사이트 파일이 없으면 사이트 파일 자리로 알린다", () => {
  const setup = writeSetup();

  const result = loadPortal(setup.configPath, join(setup.dir, "missing.toml"));

  expect("problems" in result && result.problems).toEqual(["사이트 파일: 파일이 없다"]);
});

test("사이트 파일이 site-file 패키지의 판정을 지나지 못하면 그 진단이 사이트 파일 자리로 선다", () => {
  const setup = writeSetup();
  writeFileSync(setup.siteFilePath, 'schema_version = "2"\n', "utf-8");

  const result = loadPortal(setup.configPath, setup.siteFilePath);

  expect("problems" in result && result.problems).toEqual([
    '사이트 파일: schema_version: 글자 "1" 이어야 한다',
  ]);
});

test("사이트 파일이 TOML 이 아니면 줄과 열만 싣고 파일 내용은 싣지 않는다", () => {
  const setup = writeSetup();
  writeFileSync(setup.siteFilePath, `schema_version = "1"\n[[sites]\n${SECRET}`, "utf-8");

  const result = loadPortal(setup.configPath, setup.siteFilePath);

  expect("problems" in result && result.problems).toEqual([
    expect.stringMatching(/^사이트 파일: TOML 이 아니다: .*\(\d+행 \d+열\)$/u),
  ]);
  expect(JSON.stringify(result)).not.toContain(SECRET);
});

test("설정의 발급자가 사이트 파일에 없으면 그 사이트의 발급자 자리에 진단이 선다", () => {
  const problems = problemsOf({
    config: (doc) => void (configSite(doc)["issuer"] = "https://other.example"),
  });

  expect(problems).toEqual(["sites[0].issuer: 사이트 파일에 없다"]);
});

test("설정의 에이전트가 사이트의 열 에이전트 밖이면 에이전트 자리에 진단이 선다", () => {
  const problems = problemsOf({ config: (doc) => void (configSite(doc)["agent"] = "other") });

  expect(problems).toEqual(["sites[0].agent: 사이트 파일이 그 사이트에 연 에이전트 밖이다"]);
});

test("공개 출처가 사이트의 허용 출처 밖이면 공개 출처 자리에 그 사이트와 함께 진단이 선다", () => {
  const problems = problemsOf({
    sites: (sites) => void (fileSite(sites).allowedOrigins = ["https://elsewhere.example"]),
  });

  expect(problems).toEqual(["portal.public_origin: sites[0]의 허용 출처에 들지 않는다"]);
});

test("kid 가 사이트의 공개 키에 없으면 kid 자리에 진단이 선다", () => {
  const problems = problemsOf({ config: (doc) => void (doc.portal["kid"] = "no-such-kid") });

  expect(problems).toEqual(["portal.kid: sites[0]의 공개 키에 그 kid 가 없다"]);
});

test("kid 로 고른 공개 키가 개인 키에서 난 공개 키와 다르면 kid 자리에 진단이 선다", () => {
  const problems = problemsOf({ privateKey: rsaKey(1).pkcs8 });

  expect(problems).toEqual([
    "portal.kid: sites[0]에서 그 kid 로 고른 공개 키가 개인 키에서 난 공개 키와 다르다",
  ]);
});

test("사이트 파일의 pem 에 개인 키가 들어 있으면 공개 키로 읽지 못한다고 알린다", () => {
  const problems = problemsOf({
    sites: (sites) => {
      const [site] = sites;
      const [key] = site?.keys ?? [];
      if (key !== undefined) {
        key.pem = rsaKey().pkcs8;
      }
    },
  });

  expect(problems).toEqual(["portal.kid: sites[0]에서 그 kid 로 고른 공개 키를 읽지 못한다"]);
});

test("개인 키 파일이 없으면 읽지 못한다고 알린다", () => {
  expect(problemsOf({ privateKey: null })).toEqual(["portal.private_key: 읽지 못한다"]);
});

test("개인 키 파일이 키가 아니면 읽지 못한다고 알리되 파일의 글은 싣지 않는다", () => {
  const text = `-----BEGIN PRIVATE KEY-----\n${SECRET}\n-----END PRIVATE KEY-----\n`;

  const problems = problemsOf({ privateKey: text });

  expect(problems).toEqual(["portal.private_key: 개인 키로 읽지 못한다"]);
  expect(problems.join("\n")).not.toContain(SECRET);
});

test("개인 키가 RSA 가 아니면 RSA 개인 키가 아니라고 알린다", () => {
  expect(problemsOf({ privateKey: ecPrivateKeyPem() })).toEqual([
    "portal.private_key: RSA 개인 키가 아니다",
  ]);
});

test("개인 키를 읽지 못해도 사이트 파일 대조는 계속해 어긋난 곳을 함께 알린다", () => {
  const problems = problemsOf({
    privateKey: null,
    config: (doc) => void (configSite(doc)["agent"] = "other"),
  });

  expect(problems).toEqual([
    "portal.private_key: 읽지 못한다",
    "sites[0].agent: 사이트 파일이 그 사이트에 연 에이전트 밖이다",
  ]);
});

test("설정의 어긋남은 사이트 파일의 어긋남과 함께 모두 알린다", () => {
  const setup = writeSetup({ config: (doc) => void (doc.portal["port"] = 0) });

  const result = loadPortal(setup.configPath, join(setup.dir, "missing.toml"));

  expect("problems" in result && result.problems).toEqual([
    "portal.port: 1 이상 65535 이하의 정수여야 한다",
    "사이트 파일: 파일이 없다",
  ]);
});

test("사이트마다 어긋난 곳을 모두 모아 알린다", () => {
  const problems = problemsOf({
    config: (doc) => {
      doc.sites.push({
        ...configSite(doc),
        name: "second",
        issuer: "https://second.example",
        agent: "other",
      });
      configSite(doc)["agent"] = "wrong";
    },
    sites: (sites) => void sites.push({ ...fileSite(sites), issuer: "https://second.example" }),
  });

  expect(problems).toEqual([
    "sites[0].agent: 사이트 파일이 그 사이트에 연 에이전트 밖이다",
    "sites[1].agent: 사이트 파일이 그 사이트에 연 에이전트 밖이다",
  ]);
});

test("설정 파일이 없으면 설정 파일 자리로 알린다", () => {
  const setup = writeSetup();

  const result = loadPortal(join(setup.dir, "missing.toml"), setup.siteFilePath);

  expect("problems" in result && result.problems).toEqual(["설정 파일: 파일이 없다"]);
});
