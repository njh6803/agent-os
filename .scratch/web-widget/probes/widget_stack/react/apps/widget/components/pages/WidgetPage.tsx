"use client";

// (2) iframe 안의 Next 페이지. (1) 의 커스텀 요소와 같은 ChatWidget 을 문서에 바로 그린다. 격리는 iframe 이 한다.
// 부를 곳은 자기 주소에서 읽으므로 서버가 그릴 때는 비워 두고 브라우저에서 채운다.

import { useEffect, useState } from "react";
import type { RunTarget } from "../../api/runs";
import { STYLES } from "../../lib/styles";
import { targetFromLocation } from "../../lib/target";
import { ChatWidget } from "../organisms/ChatWidget";

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
