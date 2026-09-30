// 페이지를 그린다. SWR 캐시를 그릴 때마다 새로 두어 앞 테스트가 읽은 값이 다음 테스트에 남지 않는다(`provider`).
// 한 테스트 안에서 화면을 옮겨 다니는 운영자를 재려면 캐시 하나를 여러 번의 그리기에 넘긴다. 실제 앱에서 화면을
// 옮겨도 SWR 의 캐시는 하나로 남는다.

import { render, type RenderResult } from "@testing-library/react";
import type { ReactElement } from "react";
import { type Cache, SWRConfig } from "swr";

export function renderPage(page: ReactElement, cache: Cache = new Map()): RenderResult {
  return render(<SWRConfig value={{ provider: () => cache }}>{page}</SWRConfig>);
}
