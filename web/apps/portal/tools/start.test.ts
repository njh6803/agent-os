// 시작 래퍼가 받는 인자. 인자 둘은 필수이고 듣는 호스트와 포트는 설정에서 읽어 인자로 받지 않는다.

import { expect, test } from "vitest";
import { failureCode, parseStartArgs } from "./start.ts";

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

test("시작 실패의 진단은 오류의 코드를 낸다", () => {
  expect(failureCode(Object.assign(new Error("포트가 쓰인다"), { code: "EADDRINUSE" }))).toBe(
    "EADDRINUSE",
  );
});

test("코드가 원인(cause)에만 있으면 원인을 따라가 코드를 낸다", () => {
  const cause = Object.assign(new Error("벗길 수 없다"), {
    code: "ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX",
  });

  expect(failureCode(new Error("페이지 스크립트를 벗기지 못했다", { cause }))).toBe(
    "ERR_UNSUPPORTED_TYPESCRIPT_SYNTAX",
  );
});

test("코드가 null 이면 건너뛰고 원인의 코드를 낸다", () => {
  const cause = Object.assign(new Error("시간 초과"), { code: "ETIMEDOUT" });
  const error = Object.assign(new Error("자식 프로세스가 죽었다", { cause }), { code: null });

  expect(failureCode(error)).toBe("ETIMEDOUT");
});

test("어디에도 코드가 없으면 알 수 없는 오류라고 낸다", () => {
  expect(failureCode(new Error("코드 없음", { cause: new Error("이것도 없음") }))).toBe(
    "알 수 없는 오류",
  );
  expect(failureCode("문자열이 던져졌다")).toBe("알 수 없는 오류");
});
