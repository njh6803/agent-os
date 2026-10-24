"use client";

// iframe 페이지. 사이트가 iframe 의 질의로 준 임베드 설정을 읽고, 문서 뿌리(html)에 테마·모드·보통 밀도를 단 뒤
// 위젯 한 벌(ConnectedWidget)을 그린다(web-widget 명세 "임베드"와 "테마·모드·밀도·글꼴"). 잘못 준 질의는 하나마다 그
// 이름을 든 console.error 로 남는다. 최종 사용자 경로의 기준 주소는 자기 페이지의 출처이고, 토큰은 부모 창에
// postMessage 로 묻는다(lib/token.ts).
//
// 질의는 브라우저의 주소에서 읽는다. 페이지는 빌드 때 미리 그려지고 그때는 주소가 없어(서버 스냅숏 null) 빈 몸으로
// 나가며, 하이드레이션 뒤 그린다. 속성은 그림을 칠하기 전(useLayoutEffect)에 달아 기본 테마로 한 번 칠해지지 않게 한다.
//
// 위젯의 CSS 와 글꼴 CSS 는 여기서 전역으로 싣는다. app/layout.tsx 에서 import 하면 층 경계가 막는다(ADR 0024).
import "@agent-os/ui/fonts.css";
import "../../styles/widget.css";
import { useLayoutEffect, useMemo, useSyncExternalStore } from "react";
import { allowedOrigins } from "../../lib/build";
import type { Connection } from "../../lib/connection";
import { readEmbed } from "../../lib/embed";
import { requestToken } from "../../lib/token";
import { ConnectedWidget } from "./ConnectedWidget";

function subscribe(onChange: () => void): () => void {
  window.addEventListener("popstate", onChange);
  return () => {
    window.removeEventListener("popstate", onChange);
  };
}

export function WidgetPage() {
  const search = useSyncExternalStore(
    subscribe,
    () => window.location.search,
    () => null,
  );
  const read = useMemo(() => {
    if (search === null) {
      return null;
    }
    const params = new URLSearchParams(search);
    const { embed, problems } = readEmbed((name) => params.get(name));
    return {
      embed,
      problems: problems.map((problem) => `위젯 질의 ${problem.name}: ${problem.reason}`),
    };
  }, [search]);
  // 주소가 없는 빌드 때의 그림에서는 짓지 않는다.
  const hydrated = search !== null;
  const connection = useMemo<Connection | null>(
    () =>
      hydrated
        ? {
            baseUrl: new URL(window.location.origin),
            token: () => requestToken(allowedOrigins()),
          }
        : null,
    [hydrated],
  );

  useLayoutEffect(() => {
    if (read === null) {
      return;
    }
    const root = document.documentElement;
    root.dataset["theme"] = read.embed.theme;
    if (read.embed.mode === null) {
      delete root.dataset["mode"];
    } else {
      root.dataset["mode"] = read.embed.mode;
    }
    root.dataset["density"] = "regular";
    return () => {
      delete root.dataset["theme"];
      delete root.dataset["mode"];
      delete root.dataset["density"];
    };
  }, [read]);

  if (read === null) {
    return null;
  }
  return <ConnectedWidget embed={read.embed} problems={read.problems} connection={connection} />;
}
