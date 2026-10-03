// (1) 사이트 페이지에 script 하나로 넣는 커스텀 요소의 입구. Lit 요소를 정의만 한다.

import { AgentOsWidget } from "./components/organisms/AgentOsWidget";

declare global {
  interface HTMLElementTagNameMap {
    "agent-os-widget": AgentOsWidget;
  }
}

if (customElements.get("agent-os-widget") === undefined) {
  customElements.define("agent-os-widget", AgentOsWidget);
}

export { AgentOsWidget };
