// 스토리를 shadow root 안에 그리는 틀(프로브 표본). 위젯의 페이지 안 번들(Shadow DOM 커스텀 요소, ADR 0024)과 같은
// 자리를 미리 본다. 테마와 모드는 호스트의 data-theme·data-mode 로 준다(ADR 0026 의 둘째 2026-10-06 이력).
import { useCallback, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import css from "../src/styles/theme.css?inline";
import { shadowSheets } from "../src/styles/shadow";

export const SHADOW_MODES = ["on", "raw"] as const;
export type ShadowMode = (typeof SHADOW_MODES)[number];
export type Mode = "light" | "dark";

function sheetsFor(shadow: ShadowMode): CSSStyleSheet[] {
  if (shadow === "on") {
    return shadowSheets(css);
  }
  const sheet = new CSSStyleSheet();
  sheet.replaceSync(css);
  return [sheet];
}

interface ShadowFrameProps {
  shadow: ShadowMode;
  theme: string;
  mode: Mode | null;
  children: ReactNode;
}

export function ShadowFrame({ shadow, theme, mode, children }: ShadowFrameProps) {
  const [root, setRoot] = useState<ShadowRoot | null>(null);
  const attach = useCallback(
    (host: HTMLDivElement | null) => {
      if (host === null) {
        return;
      }
      const shadowRoot = host.shadowRoot ?? host.attachShadow({ mode: "open" });
      shadowRoot.adoptedStyleSheets = sheetsFor(shadow);
      setRoot(shadowRoot);
    },
    [shadow],
  );
  return (
    <div ref={attach} data-theme={theme} data-mode={mode ?? undefined} data-shadow-frame={shadow}>
      {root === null ? null : createPortal(children, root)}
    </div>
  );
}
