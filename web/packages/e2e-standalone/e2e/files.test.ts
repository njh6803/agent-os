import { parse } from "smol-toml";
import { expect, test } from "vitest";
import { fillEnv, portalConfigToml, siteFileToml, type E2eSite } from "./files.ts";

const SITE: E2eSite = {
  name: "preview",
  issuer: "https://preview.example",
  agent: "echo",
  heading: "미리보기",
  theme: "jacho",
};

test("환경 변수 틀의 이름 줄에만 값을 채우고 나머지 줄은 그대로 둔다", () => {
  const template = "# 주석\nAGENT_OS_VERSION=1.0.0\nAGENT_OS_DATABASE_PASSWORD=\n";
  const filled = fillEnv(template, { AGENT_OS_DATABASE_PASSWORD: "비밀번호" });
  expect(filled).toBe("# 주석\nAGENT_OS_VERSION=1.0.0\nAGENT_OS_DATABASE_PASSWORD=비밀번호\n");
});

test("환경 변수 틀에 없는 이름을 채우려 하면 던진다", () => {
  expect(() => fillEnv("A=\n", { B: "1" })).toThrow(/B/u);
});

test("사이트 파일은 사이트마다 항목 하나이고 허용 출처와 에이전트를 든다", () => {
  const text = siteFileToml({
    origin: "https://localhost",
    audience: "agent-os",
    kid: "k1",
    publicPem: "PEM",
    sites: [SITE],
  });
  expect(parse(text)).toEqual({
    schema_version: "1",
    sites: [
      {
        issuer: SITE.issuer,
        audience: "agent-os",
        allowed_origins: ["https://localhost"],
        agents: ["echo"],
        public_keys: [{ kid: "k1", pem: "PEM" }],
      },
    ],
  });
});

test("위젯 미리보기 페이지 설정은 0.0.0.0 의 3000 에 서고 개인 키를 설정 폴더의 keys 에서 읽는다", () => {
  const parsed = parse(portalConfigToml({ origin: "https://localhost", kid: "k1", sites: [SITE] }));
  expect(parsed).toMatchObject({
    portal: {
      public_origin: "https://localhost",
      private_key: "keys/portal.pem",
      host: "0.0.0.0",
      port: 3000,
    },
  });
});
