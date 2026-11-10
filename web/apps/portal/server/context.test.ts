// 시작 검사를 지난 결과를 요청 처리기가 쓰는 값으로 잇는 일. 설정의 사이트와 사이트 파일의 audience 를 발급자로 맞댄다.

import { expect, test } from "vitest";
import { portalContext } from "./context.ts";
import { loadPortal } from "./load.ts";
import { rsaKey, siteSpec, writeSetup } from "../testing/fixtures.ts";

function loaded(edits: Parameters<typeof writeSetup>[0] = {}) {
  const setup = writeSetup(edits);
  const result = loadPortal(setup.configPath, setup.siteFilePath);
  if ("problems" in result) {
    throw new Error(result.problems.join("\n"));
  }
  return result;
}

const CLOCK = { now: () => 1_800_000_000_000, newAnonymousId: () => "id" };

test("설정의 사이트마다 이름과 발급자와 보증 모드에 사이트 파일의 audience 를 붙인다", () => {
  const context = portalContext(loaded(), CLOCK);

  expect(context.sites).toEqual([
    { name: "demo", issuer: "https://demo.example", audience: "agent-os", assurance: "anonymous" },
  ]);
});

test("공개 출처와 kid 와 시작 때 읽은 개인 키를 그대로 든다", () => {
  const result = loaded();

  const context = portalContext(result, CLOCK);

  expect(context.publicOrigin).toBe(result.config.publicOrigin);
  expect(context.kid).toBe(result.config.kid);
  expect(context.privateKey).toBe(result.privateKey);
});

test("시계와 식별자 만들기는 받은 것을 그대로 든다", () => {
  const context = portalContext(loaded(), CLOCK);

  expect(context.now()).toBe(1_800_000_000_000);
  expect(context.newAnonymousId()).toBe("id");
});

test("발급자마다 audience 가 다른 사이트 파일에서 사이트마다 제 발급자의 audience 를 붙인다", () => {
  const result = loaded({
    config: (doc) => {
      doc.sites.push({
        name: "second",
        issuer: "https://second.example",
        agent: "calc",
        heading: "둘째",
        assurance: "both",
      });
    },
    sites: (sites) => {
      // 사이트 파일에는 설정과 거꾸로 적어 차례가 아니라 발급자로 맞대는지 본다.
      sites.unshift({
        ...siteSpec(),
        issuer: "https://second.example",
        audience: "second-aud",
        keys: [{ kid: "portal-1", pem: rsaKey().spki }],
      });
    },
  });

  const context = portalContext(result, CLOCK);

  expect(context.sites.map(({ name, issuer, audience }) => [name, issuer, audience])).toEqual([
    ["demo", "https://demo.example", "agent-os"],
    ["second", "https://second.example", "second-aud"],
  ]);
  expect(context.sites[1]?.assurance).toBe("both");
});

test("발급자가 사이트 파일에 없으면 서버가 뜨기 전에 오류로 멈춘다", () => {
  const result = loaded();

  expect(() => portalContext({ ...result, siteFile: { sites: [] } }, CLOCK)).toThrow(/demo/u);
});
