import { expect, test } from "vitest";
import { databaseName } from "./database.ts";

test("주소의 경로에서 데이터베이스 이름을 읽는다", () => {
  const name = "agent_os_e2e_0123456789abcdef0123456789abcdef";
  expect(databaseName(`postgresql://agent_os:agent_os@127.0.0.1:25432/${name}`)).toBe(name);
});

test("이름이 없는 주소는 거부한다", () => {
  expect(() => databaseName("postgresql://agent_os:agent_os@127.0.0.1:25432")).toThrow(
    "이름이 없다",
  );
});
