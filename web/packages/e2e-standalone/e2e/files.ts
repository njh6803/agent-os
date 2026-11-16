// 풀어 놓은 배포 파일 묶음에서 운영자가 채우는 파일을 시험 값으로 짓는 순수 함수. 파일에 쓰는 것은 준비(stack.ts)가 한다.
// 사이트 파일과 위젯 미리보기 페이지 설정의 모양은 e2e-stack 과 위젯 미리보기 페이지 e2e(`apps/portal/e2e/stack.ts`)가 쓰는
// 것과 같다.

import { stringify } from "smol-toml";

export interface E2eSite {
  readonly name: string;
  readonly issuer: string;
  readonly agent: string;
  readonly heading: string;
  readonly theme: string;
}

export interface SiteFileInput {
  readonly origin: string;
  readonly audience: string;
  readonly kid: string;
  readonly publicPem: string;
  readonly sites: readonly E2eSite[];
}

export function siteFileToml(input: SiteFileInput): string {
  return stringify({
    schema_version: "1",
    sites: input.sites.map((site) => ({
      issuer: site.issuer,
      audience: input.audience,
      allowed_origins: [input.origin],
      agents: [site.agent],
      public_keys: [{ kid: input.kid, pem: input.publicPem }],
    })),
  });
}

export interface PortalConfigInput {
  readonly origin: string;
  readonly kid: string;
  readonly sites: readonly E2eSite[];
}

/** 위젯 미리보기 페이지 설정. 듣는 주소와 포트는 틀의 값(`0.0.0.0`, 3000)이고 개인 키는 설정 폴더의 `keys/portal.pem` 이다. */
export function portalConfigToml(input: PortalConfigInput): string {
  return stringify({
    schema_version: "1",
    portal: {
      public_origin: input.origin,
      private_key: "keys/portal.pem",
      kid: input.kid,
      host: "0.0.0.0",
      port: 3000,
    },
    sites: input.sites.map((site) => ({
      name: site.name,
      issuer: site.issuer,
      agent: site.agent,
      heading: site.heading,
      theme: site.theme,
      assurance: "anonymous",
    })),
  });
}

/**
 * 환경 변수 틀(`.env.example`)의 `이름=` 줄에 값을 채운다. 틀에 없는 이름을 채우려 하면 던진다. 틀의 이름이 바뀌었는데 시험이
 * 옛 이름을 채워 서버가 값을 못 받는 일을 막는다.
 */
export function fillEnv(template: string, values: Readonly<Record<string, string>>): string {
  const wanted = new Set(Object.keys(values));
  const lines = template.split("\n").map((line) => {
    const match = /^([A-Z][A-Z0-9_]*)=/u.exec(line);
    const name = match?.[1];
    if (name === undefined || !(name in values)) {
      return line;
    }
    wanted.delete(name);
    return `${name}=${values[name] ?? ""}`;
  });
  if (wanted.size > 0) {
    throw new Error(`환경 변수 틀에 없는 이름을 채우려 했다: ${[...wanted].join(", ")}`);
  }
  return lines.join("\n");
}
