// 구성 오류 글과 시작 로그 한 줄.

import { expect, test } from "vitest";
import { configErrorText, listenLine } from "./diagnostics.ts";

test("구성 오류는 첫 줄 뒤에 어긋난 자리마다 한 줄씩 낸다", () => {
  expect(configErrorText(["sites[1].agent: 열 에이전트 밖이다", "portal.kid: 없다"])).toBe(
    "구성 오류:\nsites[1].agent: 열 에이전트 밖이다\nportal.kid: 없다",
  );
});

test("시작 로그는 주소와 사이트 수를 한 줄로 낸다", () => {
  expect(listenLine("127.0.0.1", 8080, 2)).toBe(
    "위젯 미리보기 페이지가 http://127.0.0.1:8080/portal/ 에 섰다. 사이트 2개.",
  );
});

test("호스트가 IPv6 루프백이면 주소의 호스트 자리를 대괄호로 감싼다", () => {
  expect(listenLine("::1", 8080, 1)).toBe(
    "위젯 미리보기 페이지가 http://[::1]:8080/portal/ 에 섰다. 사이트 1개.",
  );
});
