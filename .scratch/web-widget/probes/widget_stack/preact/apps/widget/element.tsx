// (1) 사이트 페이지에 script 하나로 넣는 커스텀 요소. shadow root 안에 스타일과 Preact 뿌리를 둔다.

import { render } from "preact";
import { ChatWidget } from "./components/organisms/ChatWidget";
import { STYLES } from "./lib/styles";
import { targetFromElement } from "./lib/target";

export class AgentOsWidget extends HTMLElement {
  #mount: HTMLElement | null = null;

  connectedCallback(): void {
    const shadow = this.shadowRoot ?? this.attachShadow({ mode: "open" });
    const style = document.createElement("style");
    style.textContent = STYLES;
    const mount = document.createElement("div");
    shadow.replaceChildren(style, mount);
    this.#mount = mount;
    render(<ChatWidget target={targetFromElement(this)} />, mount);
  }

  disconnectedCallback(): void {
    if (this.#mount !== null) {
      render(null, this.#mount);
      this.#mount = null;
    }
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
