// 스토리를 shadow root 안에 그리는 틀. 위젯의 페이지 안 번들(Shadow DOM 커스텀 요소, ADR 0024)과 같은 자리를 미리 본다.
// 시트는 패키지의 CSS 원본을 `?inline` 글자로 받아 만든다. on 은 보정 시트(shadowSheets)까지, raw 는 Tailwind 시트만이다.
// 테마는 호스트의 data-theme 으로 준다(shadow 안의 CSS 는 `:host([data-theme=dark])` 로 읽는다).
import { useCallback, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import css from "../src/styles/theme.css?inline";
import { shadowSheets } from "../src/styles/shadow";

export const SHADOW_MODES = ["on", "raw"] as const;
export type ShadowMode = (typeof SHADOW_MODES)[number];

function sheetsFor(mode: ShadowMode): CSSStyleSheet[] {
  if (mode === "on") {
    return shadowSheets(css);
  }
  const sheet = new CSSStyleSheet();
  sheet.replaceSync(css);
  return [sheet];
}

interface ShadowFrameProps {
  mode: ShadowMode;
  theme: "light" | "dark";
  children: ReactNode;
}

export function ShadowFrame({ mode, theme, children }: ShadowFrameProps) {
  const [root, setRoot] = useState<ShadowRoot | null>(null);
  const attach = useCallback(
    (host: HTMLDivElement | null) => {
      if (host === null) {
        return;
      }
      const shadow = host.shadowRoot ?? host.attachShadow({ mode: "open" });
      shadow.adoptedStyleSheets = sheetsFor(mode);
      setRoot(shadow);
    },
    [mode],
  );
  return (
    <div ref={attach} data-theme={theme} data-shadow-frame={mode}>
      {root === null ? null : createPortal(children, root)}
    </div>
  );
}
