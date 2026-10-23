// 위젯 페이지 시험(widget-pages)의 격리. 테스트마다 그린 것을 걷고(페이지가 문서 뿌리에 단 속성도 그때 걷힌다),
// 엿본 함수를 되돌리고, 주소를 처음으로 돌린다.

import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  window.history.replaceState(null, "", "/");
});
