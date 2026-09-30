// 페이지를 그린다. SWR 캐시를 그릴 때마다 새로 두어 앞 테스트가 읽은 값이 다음 테스트에 남지 않는다(`provider`).

import { render, type RenderResult } from "@testing-library/react";
import type { ReactElement } from "react";
import { SWRConfig } from "swr";

export function renderPage(page: ReactElement): RenderResult {
  return render(<SWRConfig value={{ provider: () => new Map() }}>{page}</SWRConfig>);
}
