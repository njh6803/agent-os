// (1) 사이트 페이지에 script 하나로 넣는 커스텀 요소(모양 B). 공유 컴포넌트는 packages/widget-ui 에서 온다.

import { ChatWidget, STYLES, targetFromElement } from "@agent-os/widget-ui";
import { createRoot, type Root } from "react-dom/client";

export class AgentOsWidget extends HTMLElement {
  #root: Root | null = null;

  connectedCallback(): void {
    const shadow = this.shadowRoot ?? this.attachShadow({ mode: "open" });
    const style = document.createElement("style");
    style.textContent = STYLES;
    const mount = document.createElement("div");
    shadow.replaceChildren(style, mount);
    this.#root = createRoot(mount);
    this.#root.render(<ChatWidget target={targetFromElement(this)} />);
  }

  disconnectedCallback(): void {
    this.#root?.unmount();
    this.#root = null;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "agent-os-widget": AgentOsWidget;
  }
}

if (customElements.get("agent-os-widget") === undefined) {
  customElements.define("agent-os-widget", AgentOsWidget);
}
