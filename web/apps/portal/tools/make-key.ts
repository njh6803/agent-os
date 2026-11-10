/**
 * 키 만들기 명령(pilot-portal 명세 "키 만들기 명령"). 질문 페이지가 토큰에 서명할 RSA 2048 키 쌍을 만들어 개인 키를 그
 * 경로에 PKCS#8 PEM 으로 쓰고(POSIX 에서는 모드 0600), 사이트 파일에 붙일 `[[sites.public_keys]]` 조각(`kid` 와 SPKI PEM
 * `pem`)을 stdout 에 TOML 그대로 찍는다. 설정 파일의 `[portal]` 조각은 찍지 않는다. 사이트 파일과 설정 두 파일에 붙일 것을
 * 한 출력에 섞지 않기 위해서다.
 *
 * 그 경로에 이미 파일이 있으면 덮어쓰지 않고 종료 코드 1로 끝난다. 덮어쓰면 이미 서명 중인 개인 키를 잃는다. 키 파일은
 * 커밋하지 않는다. 개인 키는 stdout 에 싣지 않는다.
 *
 * 사용: node tools/make-key.ts --private-key <경로> --kid <kid>
 */

import { generateKeyPairSync } from "node:crypto";
import { writeFileSync } from "node:fs";
import { parseArgs } from "node:util";
import { withoutSeparator } from "./args.ts";

const USAGE = "키 만들기 명령은 --private-key <경로> 와 --kid <kid> 둘을 받는다.";
const OWNER_ONLY = 0o600;
const RSA_BITS = 2048;

export type MakeKeyResult = { readonly toml: string } | { readonly problem: string };

/** TOML 기본 문자열. JSON 의 이스케이프가 TOML 과 같고, 지우지 못하는 DEL 만 따로 쓴다. */
function tomlString(text: string): string {
  return JSON.stringify(text).replaceAll("\u007f", "\\u007f");
}

/** 키 쌍을 만들어 개인 키를 `privateKeyPath` 에 쓰고 사이트 파일에 붙일 TOML 조각을 낸다. */
export function makeKey(privateKeyPath: string, kid: string): MakeKeyResult {
  if (kid.trim() === "") {
    return { problem: `kid 가 비었다. ${USAGE}` };
  }
  const { privateKey, publicKey } = generateKeyPairSync("rsa", {
    modulusLength: RSA_BITS,
    privateKeyEncoding: { type: "pkcs8", format: "pem" },
    publicKeyEncoding: { type: "spki", format: "pem" },
  });
  try {
    // `wx` 는 파일이 이미 있으면 쓰지 않고 EEXIST 로 거부한다. 있는지 보고 쓰는 두 걸음이 아니라 한 걸음이다.
    writeFileSync(privateKeyPath, privateKey, { flag: "wx", mode: OWNER_ONLY });
  } catch (error: unknown) {
    const code = error instanceof Error && "code" in error ? String(error.code) : "알 수 없는 오류";
    return {
      problem:
        code === "EEXIST"
          ? "그 경로에 이미 파일이 있어 덮어쓰지 않는다. 다른 경로를 주거나 그 파일을 먼저 치운다"
          : `개인 키를 쓰지 못했다(${code})`,
    };
  }
  return {
    toml: `[[sites.public_keys]]\nkid = ${tomlString(kid)}\npem = """\n${publicKey}"""\n`,
  };
}

function main(argv: readonly string[]): void {
  let values;
  try {
    ({ values } = parseArgs({
      args: [...withoutSeparator(argv)],
      options: { "private-key": { type: "string" }, kid: { type: "string" } },
      allowPositionals: false,
      strict: true,
    }));
  } catch (error: unknown) {
    console.error(`${USAGE}\n  ${error instanceof Error ? error.message : String(error)}`);
    process.exitCode = 1;
    return;
  }
  const { "private-key": privateKeyPath, kid } = values;
  if (privateKeyPath === undefined || privateKeyPath === "" || kid === undefined) {
    console.error(USAGE);
    process.exitCode = 1;
    return;
  }
  const result = makeKey(privateKeyPath, kid);
  if ("problem" in result) {
    console.error(result.problem);
    process.exitCode = 1;
    return;
  }
  process.stdout.write(result.toml);
}

if (import.meta.main) {
  main(process.argv.slice(2));
}
