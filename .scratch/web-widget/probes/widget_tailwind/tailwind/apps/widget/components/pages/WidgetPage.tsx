"use client";

// (2) iframe 안의 Next 페이지. (1) 의 커스텀 요소와 같은 ChatWidget 을 문서에 바로 그린다. 격리는 iframe 이 한다.
// CSS 원본은 element 와 같은 styles/widget.css 이고 Next 가 postcss.config.mjs 로 빌드한다. 전역 CSS 를 app/ 이 아니라
// 여기서 import 하는 것은 app/ 의 파일이 pages·templates 밖을 import 하지 못해서다(cases.mjs 가 잰다).
// 부를 곳은 자기 주소에서 읽으므로 서버가 그릴 때는 비워 두고 브라우저에서 채운다.

import { useEffect, useState } from "react";
import type { RunTarget } from "../../api/runs";
import { targetFromLocation } from "../../lib/target";
import "../../styles/widget.css";
import { ChatWidget } from "../organisms/ChatWidget";

export function WidgetPage() {
  const [target, setTarget] = useState<RunTarget | null>(null);

  useEffect(() => {
    setTarget(targetFromLocation(location));
  }, []);

  return target === null ? null : <ChatWidget target={target} />;
}
