// 시작 래퍼가 받는 인자. 인자 둘은 필수이고 듣는 호스트와 포트는 설정에서 읽어 인자로 받지 않는다.

import { expect, test } from "vitest";
import { parseStartArgs } from "./start.ts";

test("설정과 사이트 파일의 경로를 받는다", () => {
  expect(parseStartArgs(["--config", "portal.toml", "--site-file", "sites.toml"])).toEqual({
    config: "portal.toml",
    siteFile: "sites.toml",
  });
});

test("pnpm 이 앞에 붙여 넘기는 구분자 두 줄표는 건너뛴다", () => {
  expect(parseStartArgs(["--", "--config", "portal.toml", "--site-file", "sites.toml"])).toEqual({
    config: "portal.toml",
    siteFile: "sites.toml",
  });
});

test("인자 둘 가운데 하나라도 빠지면 쓰는 법과 함께 거부한다", () => {
  for (const argv of [[], ["--config", "portal.toml"], ["--site-file", "sites.toml"]]) {
    const result = parseStartArgs(argv);

    expect("problem" in result && result.problem).toContain("--config");
    expect("problem" in result && result.problem).toContain("--site-file");
  }
});

test("호스트와 포트와 모르는 인자는 받지 않는다", () => {
  for (const extra of [
    ["--host", "127.0.0.1"],
    ["--port", "8080"],
    ["--hostname", "x"],
    ["extra"],
  ]) {
    const result = parseStartArgs(["--config", "a", "--site-file", "b", ...extra]);

    // 쓰는 법과 함께, 받지 않은 그 인자 이름이 까닭에 든다.
    expect("problem" in result && result.problem, JSON.stringify(extra)).toContain("--config");
    expect("problem" in result && result.problem, JSON.stringify(extra)).toContain(extra[0]);
  }
});

test("빈 경로는 받지 않고 쓰는 법을 알린다", () => {
  const result = parseStartArgs(["--config", "", "--site-file", "sites.toml"]);

  expect("problem" in result && result.problem).toContain("--site-file");
});
