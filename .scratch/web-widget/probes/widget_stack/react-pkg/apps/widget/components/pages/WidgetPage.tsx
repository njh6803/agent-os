"use client";

// (2) iframe 안의 Next 페이지(모양 B). 공유 컴포넌트는 packages/widget-ui 에서 온다. app/ 은 이 파일만 import 한다.

import { ChatWidget, STYLES, targetFromLocation, type RunTarget } from "@agent-os/widget-ui";
import { useEffect, useState } from "react";

export function WidgetPage() {
  const [target, setTarget] = useState<RunTarget | null>(null);

  useEffect(() => {
    setTarget(targetFromLocation(location));
  }, []);

  return (
    <>
      <style>{STYLES}</style>
      {target === null ? null : <ChatWidget target={target} />}
    </>
  );
}
