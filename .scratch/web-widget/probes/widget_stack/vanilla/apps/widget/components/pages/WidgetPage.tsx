"use client";

// (2) iframe 안의 Next 페이지. React 19 가 (1) 과 같은 커스텀 요소를 그린다. 요소의 정의는 브라우저에서만 불러온다
// (서버에는 HTMLElement 가 없다). JSX 에서 요소 이름을 쓰는 타입은 react-intrinsic.d.ts 의 보강이다.

import { useEffect, useState } from "react";
import type { RunTarget } from "../../api/runs";
import { targetFromLocation } from "../../lib/target";

export function WidgetPage() {
  const [target, setTarget] = useState<RunTarget | null>(null);

  useEffect(() => {
    void import("../../element").then(() => {
      setTarget(targetFromLocation(location));
    });
  }, []);

  return target === null ? null : (
    <agent-os-widget api-base={target.baseUrl} agent={target.agent} token={target.token} />
  );
}
