// 사이트가 준 임베드 설정(iframe 의 질의)을 읽는 규칙. 화면에 무엇이 서는지와 console.error 는 페이지 시험
// (components/pages/WidgetPage.test.tsx)이 본다.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "vitest";
import { AGENT_PATTERN, readEmbed, type EmbedName } from "./embed.ts";

function fromQuery(query: string) {
  const params = new URLSearchParams(query);
  return readEmbed((name: EmbedName) => params.get(name));
}

test("다섯 값을 모두 주면 그대로 읽고 문제가 없다", () => {
  expect(
    fromQuery(
      "agent=order-helper&heading=주문 도우미&intro=주문을 물어보세요&theme=jacho&mode=dark",
    ),
  ).toEqual({
    embed: {
      agent: "order-helper",
      heading: "주문 도우미",
      intro: "주문을 물어보세요",
      theme: "jacho",
      mode: "dark",
    },
    problems: [],
  });
});

test("이름이 없으면 에이전트 이름을 보이고, 할 수 있는 일과 테마와 모드는 주지 않은 것이다", () => {
  expect(fromQuery("agent=order-helper")).toEqual({
    embed: {
      agent: "order-helper",
      heading: "order-helper",
      intro: null,
      theme: "nokcheong",
      mode: null,
    },
    problems: [],
  });
});

test("보일 글인 이름과 할 수 있는 일의 빈 값은 주지 않은 것으로 읽는다", () => {
  expect(fromQuery("agent=order-helper&heading=&intro=")).toEqual({
    embed: {
      agent: "order-helper",
      heading: "order-helper",
      intro: null,
      theme: "nokcheong",
      mode: null,
    },
    problems: [],
  });
});

test("공백만 든 이름과 할 수 있는 일도 보일 것이 없어 주지 않은 것으로 읽는다", () => {
  expect(fromQuery("agent=order-helper&heading=+&intro=%20%09")).toEqual({
    embed: {
      agent: "order-helper",
      heading: "order-helper",
      intro: null,
      theme: "nokcheong",
      mode: null,
    },
    problems: [],
  });
});

test("빈 테마와 빈 모드는 목록 밖이라 기본값으로 그리고 문제가 둘을 든다", () => {
  const { embed, problems } = fromQuery("agent=order-helper&theme=&mode=");
  expect(embed.theme).toBe("nokcheong");
  expect(embed.mode).toBeNull();
  expect(problems.map((problem) => problem.name)).toEqual(["theme", "mode"]);
  expect(problems.map((problem) => problem.reason.includes('받은 값: ""'))).toEqual([true, true]);
});

test("에이전트가 없으면 쓸 수 없는 설정이고 문제가 agent 를 든다", () => {
  const { embed, problems } = fromQuery("heading=주문 도우미");
  expect(embed.agent).toBeNull();
  expect(embed.heading).toBe("주문 도우미");
  expect(problems.map((problem) => problem.name)).toEqual(["agent"]);
});

for (const agent of ["", "Order", "1order", "a", "order_helper", "order helper", "a".repeat(64)]) {
  test(`플러그인 이름의 패턴 밖인 에이전트 ${JSON.stringify(agent)} 는 쓸 수 없는 설정이고 이름으로도 보이지 않는다`, () => {
    const { embed, problems } = fromQuery(new URLSearchParams({ agent }).toString());
    expect(embed.agent).toBeNull();
    expect(embed.heading).toBe("");
    expect(problems.map((problem) => problem.name)).toEqual(["agent"]);
    expect(problems[0]?.reason).toContain(JSON.stringify(agent));
  });
}

test("패턴의 경계 안인 에이전트(두 글자, 예순세 글자, 숫자와 붙임표)는 지난다", () => {
  for (const agent of ["ab", "a".repeat(63), "a1-b2"]) {
    expect(fromQuery(new URLSearchParams({ agent }).toString()).embed.agent).toBe(agent);
  }
});

test("테마 목록 밖의 테마는 기본 테마로 그리고 문제가 theme 을 든다", () => {
  const { embed, problems } = fromQuery("agent=order-helper&theme=purple");
  expect(embed.agent).toBe("order-helper");
  expect(embed.theme).toBe("nokcheong");
  expect(problems.map((problem) => problem.name)).toEqual(["theme"]);
  expect(problems[0]?.reason).toContain('"purple"');
});

test("light 나 dark 가 아닌 모드는 시스템 설정을 따르고 문제가 mode 를 든다", () => {
  const { embed, problems } = fromQuery("agent=order-helper&mode=system");
  expect(embed.mode).toBeNull();
  expect(problems.map((problem) => problem.name)).toEqual(["mode"]);
});

test("문제는 질의의 차례대로 모두 든다", () => {
  const { problems } = fromQuery("theme=purple&mode=sepia");
  expect(problems.map((problem) => problem.name)).toEqual(["agent", "theme", "mode"]);
});

test("에이전트 이름의 패턴은 계약(openapi.json 의 실행 시작 본문)과 같다", () => {
  const contract: unknown = JSON.parse(
    readFileSync(join(import.meta.dirname, "..", "..", "..", "..", "openapi.json"), "utf-8"),
  );
  expect(startRunAgentPattern(contract)).toBe(AGENT_PATTERN.source);
});

/** openapi.json 에서 StartRun.agent 의 pattern. 모양이 다르면 던진다. */
function startRunAgentPattern(contract: unknown): unknown {
  const path = ["components", "schemas", "StartRun", "properties", "agent", "pattern"];
  let node: unknown = contract;
  for (const key of path) {
    if (typeof node !== "object" || node === null || !(key in node)) {
      throw new Error(`openapi.json 에 ${path.join(".")} 가 없다`);
    }
    node = Object.getOwnPropertyDescriptor(node, key)?.value;
  }
  return node;
}
