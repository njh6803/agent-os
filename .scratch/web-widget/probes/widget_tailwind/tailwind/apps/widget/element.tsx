// (1) 사이트 페이지에 script 하나로 넣는 커스텀 요소. Tailwind 로 빌드한 CSS 를 `?inline` 으로 글자로 받아 구성한
// 시트로 만들고 shadow root 의 adoptedStyleSheets 에 넣는다. 그 안에 React 뿌리를 둔다.

import { createRoot, type Root } from "react-dom/client";
import { ChatWidget } from "./components/organisms/ChatWidget";
import { shadowSheets } from "./lib/shadow-styles";
import { targetFromElement } from "./lib/target";
import css from "./styles/widget.css?inline";

// 같은 문서의 위젯 인스턴스가 시트를 함께 든다. 구성한 시트는 여러 shadow root 에 나눠 넣을 수 있다.
const sheets = shadowSheets(css);

export class AgentOsWidget extends HTMLElement {
  #root: Root | null = null;

  connectedCallback(): void {
    const shadow = this.shadowRoot ?? this.attachShadow({ mode: "open" });
    shadow.adoptedStyleSheets = sheets;
    const mount = document.createElement("div");
    shadow.replaceChildren(mount);
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
