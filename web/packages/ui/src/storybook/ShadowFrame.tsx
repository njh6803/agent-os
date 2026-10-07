// 스토리를 shadow root 안에 그리는 틀. 위젯의 페이지 안 번들(Shadow DOM 커스텀 요소, ADR 0024)과 같은 자리를 미리
// 본다. 테마와 모드는 호스트의 data-theme·data-mode 로 주고, 그림은 감싼 요소(`data-ui-root`) 안에 둔다.
// on 은 보정 시트(shadowSheets)까지, raw 는 디자인 토큰 CSS 의 시트만 넣는다.
import { useCallback, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { UI_ROOT_ATTRIBUTE, shadowSheets } from "../styles/shadow";
import type { Mode, ThemeKey } from "../themes";

export const SHADOW_MODES = ["on", "raw"] as const;
export type ShadowMode = (typeof SHADOW_MODES)[number];

function sheetsFor(shadow: ShadowMode, css: string): CSSStyleSheet[] {
  if (shadow === "on") {
    return shadowSheets(css);
  }
  const sheet = new CSSStyleSheet();
  sheet.replaceSync(css);
  return [sheet];
}

function appendWrapper(root: ShadowRoot): HTMLElement {
  const wrapper = document.createElement("div");
  wrapper.setAttribute(UI_ROOT_ATTRIBUTE, "");
  root.append(wrapper);
  return wrapper;
}

export interface ShadowFrameProps {
  shadow: ShadowMode;
  /** 빌드한 디자인 토큰 CSS(`?inline` 글자). */
  css: string;
  theme: ThemeKey;
  /** null 이면 data-mode 를 두지 않아 시스템 설정을 따른다. */
  mode: Mode | null;
  children: ReactNode;
}

export function ShadowFrame({ shadow, css, theme, mode, children }: ShadowFrameProps) {
  const [wrapper, setWrapper] = useState<HTMLElement | null>(null);
  const attach = useCallback(
    (host: HTMLDivElement | null) => {
      if (host === null) {
        return;
      }
      const root = host.shadowRoot ?? host.attachShadow({ mode: "open" });
      root.adoptedStyleSheets = sheetsFor(shadow, css);
      const existing = root.firstElementChild;
      setWrapper(existing instanceof HTMLElement ? existing : appendWrapper(root));
    },
    [shadow, css],
  );
  return (
    <div ref={attach} data-theme={theme} data-mode={mode ?? undefined} data-shadow-frame={shadow}>
      {wrapper === null ? null : createPortal(children, wrapper)}
    </div>
  );
}
