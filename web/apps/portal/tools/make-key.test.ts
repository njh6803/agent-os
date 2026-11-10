// 키 만들기 명령. 함수가 짓는 출력과 파일을 먼저 보고, 실제 프로세스로 종료 코드와 stdout 을 본다.

import { createPrivateKey, createPublicKey } from "node:crypto";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { parse } from "smol-toml";
import { expect, test } from "vitest";
import { makeKey } from "./make-key.ts";

const MAKE_KEY = join(import.meta.dirname, "make-key.ts");

function freshPath(): string {
  return join(mkdtempSync(join(tmpdir(), "portal-key-")), "portal.pem");
}

/** 출력을 TOML 로 읽어 `[[sites.public_keys]]` 하나를 꺼낸다. */
function publicKeyOf(toml: string): { kid: unknown; pem: unknown } {
  const document = parse(toml);
  const sites = document["sites"];
  if (typeof sites !== "object" || Array.isArray(sites) || sites instanceof Date) {
    throw new Error("출력에 sites 표가 없다");
  }
  const keys = sites["public_keys"];
  if (!Array.isArray(keys) || keys.length !== 1) {
    throw new Error("출력에 공개 키 하나가 아니다");
  }
  const [key] = keys;
  if (typeof key !== "object" || Array.isArray(key) || key instanceof Date) {
    throw new Error("공개 키 표가 아니다");
  }
  return { kid: key["kid"], pem: key["pem"] };
}

test("개인 키를 PKCS#8 PEM 으로 쓰고 사이트 파일에 붙일 공개 키 조각을 TOML 로 낸다", () => {
  const path = freshPath();

  const result = makeKey(path, "portal-1");

  expect("toml" in result).toBe(true);
  const pem = readFileSync(path, "utf-8");
  expect(pem.startsWith("-----BEGIN PRIVATE KEY-----")).toBe(true);
  const privateKey = createPrivateKey(pem);
  expect(privateKey.asymmetricKeyType).toBe("rsa");
  expect(privateKey.asymmetricKeyDetails?.modulusLength).toBe(2048);
  const toml = "toml" in result ? result.toml : "";
  expect(toml.startsWith("[[sites.public_keys]]\n")).toBe(true);
  // 설정 파일에 붙일 [portal] 조각은 내지 않는다.
  expect(toml).not.toContain("[portal]");
  const { kid, pem: publicPem } = publicKeyOf(toml);
  expect(kid).toBe("portal-1");
  expect(publicPem).toBe(
    createPublicKey(privateKey).export({ type: "spki", format: "pem" }).toString(),
  );
});

test("출력의 공개 키 조각은 SPKI PEM 이다", () => {
  const result = makeKey(freshPath(), "k");

  expect("toml" in result && result.toml).toContain("-----BEGIN PUBLIC KEY-----");
});

test("kid 에 따옴표와 역슬래시와 제어 문자가 있어도 TOML 로 읽으면 같은 글이 나온다", () => {
  const tricky = 'a"b\\c\td\ne\u007ff';

  const result = makeKey(freshPath(), tricky);

  expect(publicKeyOf("toml" in result ? result.toml : "").kid).toBe(tricky);
});

test("이미 있는 파일은 덮어쓰지 않고 그 파일을 그대로 둔다", () => {
  const path = freshPath();
  writeFileSync(path, "원래 있던 글", "utf-8");

  const result = makeKey(path, "portal-1");

  expect("problem" in result && result.problem).toContain("덮어쓰지 않는다");
  expect(readFileSync(path, "utf-8")).toBe("원래 있던 글");
});

test("빈 kid 와 공백뿐인 kid 는 받지 않고 파일도 쓰지 않는다", () => {
  for (const kid of ["", "  "]) {
    const path = freshPath();

    const result = makeKey(path, kid);

    expect("problem" in result && result.problem, JSON.stringify(kid)).toContain("kid 가 비었다");
    expect(existsSync(path), JSON.stringify(kid)).toBe(false);
  }
});

// 윈도우는 모드 비트를 따르지 않아 그 판에서는 건너뛴 것으로 드러낸다.
test.skipIf(process.platform === "win32")("POSIX 에서는 개인 키 파일의 모드가 0600 이다", () => {
  const path = freshPath();
  makeKey(path, "portal-1");

  expect(statSync(path).mode & 0o777).toBe(0o600);
});

test("명령을 실제로 치면 키 파일을 쓰고 stdout 에 조각을 찍고 종료 코드 0 으로 끝난다", () => {
  const path = freshPath();

  const run = spawnSync(process.execPath, [MAKE_KEY, "--private-key", path, "--kid", "portal-1"], {
    encoding: "utf-8",
    timeout: 30_000,
  });

  expect(run.status).toBe(0);
  expect(publicKeyOf(run.stdout).kid).toBe("portal-1");
  expect(existsSync(path)).toBe(true);
  // 개인 키는 출력에 실리지 않는다.
  expect(run.stdout).not.toContain("PRIVATE KEY");
  expect(run.stderr).toBe("");
});

test("이미 파일이 있는 경로로 명령을 치면 덮어쓰지 않고 종료 코드 1 로 끝난다", () => {
  const path = freshPath();
  writeFileSync(path, "원래 있던 글", "utf-8");

  const run = spawnSync(process.execPath, [MAKE_KEY, "--private-key", path, "--kid", "portal-1"], {
    encoding: "utf-8",
    timeout: 30_000,
  });

  expect(run.status).toBe(1);
  expect(run.stdout).toBe("");
  expect(run.stderr).toContain("덮어쓰지 않는다");
  expect(readFileSync(path, "utf-8")).toBe("원래 있던 글");
});

test("인자를 빠뜨리면 쓰는 법을 알리고 종료 코드 1 로 끝난다", () => {
  const run = spawnSync(process.execPath, [MAKE_KEY, "--kid", "portal-1"], {
    encoding: "utf-8",
    timeout: 30_000,
  });

  expect(run.status).toBe(1);
  expect(run.stderr).toContain("--private-key");
});
