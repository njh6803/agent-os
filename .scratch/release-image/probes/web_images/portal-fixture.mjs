// 위젯 미리보기 페이지를 띄울 세 파일(설정, 사이트 파일, 개인 키)을 한 폴더에 짓는다. 키는 운영자가 쓸 그 명령
// (tools/make-key.ts)으로 만든다. 키 파일은 커밋하지 않고 회차마다 볼륨 안에 새로 만든다.
//
// 사용: node portal-fixture.mjs <폴더> <포트>   (작업 폴더가 apps/portal)
// 짓는 것: <폴더>/portal.toml, <폴더>/sites.toml, <폴더>/keys/portal.pem
// 끝에 "RI_PROBE fixture ..." 한 줄로 세 파일의 소유자와 모드를 찍는다.

import { execFileSync } from "node:child_process";
import { mkdirSync, statSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const [dir, port] = process.argv.slice(2);
if (dir === undefined || port === undefined) {
  console.error("사용: node portal-fixture.mjs <폴더> <포트>");
  process.exit(2);
}
const ORIGIN = "https://preview.probe-portal.example";
const ISSUER = "https://issuer.probe-portal.example";
const KID = "portal-probe-1";

mkdirSync(join(dir, "keys"), { recursive: true });
const keyPath = join(dir, "keys", "portal.pem");
const fragment = execFileSync(
  process.execPath,
  ["tools/make-key.ts", "--private-key", keyPath, "--kid", KID],
  { encoding: "utf-8" },
);

writeFileSync(
  join(dir, "sites.toml"),
  [
    'schema_version = "1"',
    "",
    "[[sites]]",
    `issuer = "${ISSUER}"`,
    'audience = "agent-os"',
    `allowed_origins = ["${ORIGIN}"]`,
    'agents = ["echo"]',
    "",
    fragment,
  ].join("\n"),
);
writeFileSync(
  join(dir, "portal.toml"),
  [
    'schema_version = "1"',
    "",
    "[portal]",
    `public_origin = "${ORIGIN}"`,
    'private_key = "keys/portal.pem"',
    `kid = "${KID}"`,
    `port = ${port}`,
    "",
    "[[sites]]",
    'name = "probe"',
    `issuer = "${ISSUER}"`,
    'agent = "echo"',
    'heading = "프로브"',
    'assurance = "anonymous"',
    "",
  ].join("\n"),
);

const describe = (path) => {
  const { uid, gid, mode } = statSync(path);
  return `${path}=${uid}:${gid}:${(mode & 0o777).toString(8)}`;
};
console.log(
  `RI_PROBE fixture ${describe(dir)} ${describe(join(dir, "portal.toml"))} ${describe(join(dir, "sites.toml"))} ${describe(keyPath)}`,
);
