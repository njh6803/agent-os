// 채팅 위젯 하나(프레임워크 없이, HTMLElement 와 DOM API 만). 입력창, 메시지 목록, 보내기 버튼. 보내면 실행을 일으키고
// 프레임을 받는 대로 목록에 붙인다. 요소가 스스로 shadow root 에 그리므로 커스텀 요소가 곧 UI 다. 정의는 입구
// (element.ts)가 한다. 부를 곳은 속성에서 읽는다. 글자는 textContent 로만 넣는다(HTML 로 그리지 않는다).

import { startRun } from "../../api/runs";
import { describeFrame, type Role } from "../../lib/frames";
import { STYLES } from "../../lib/styles";
import { targetFromElement } from "../../lib/target";

export class AgentOsWidget extends HTMLElement {
  #list: HTMLUListElement | null = null;
  #button: HTMLButtonElement | null = null;
  #running: AbortController | null = null;

  connectedCallback(): void {
    if (this.shadowRoot !== null) {
      return;
    }
    const shadow = this.attachShadow({ mode: "open" });
    const style = document.createElement("style");
    style.textContent = STYLES;

    const section = document.createElement("section");
    section.className = "widget";
    section.setAttribute("aria-label", "채팅");
    const list = document.createElement("ul");
    list.className = "messages";
    list.setAttribute("aria-label", "메시지");
    const form = document.createElement("form");
    const input = document.createElement("input");
    input.setAttribute("aria-label", "메시지 입력");
    const button = document.createElement("button");
    button.type = "submit";
    button.textContent = "보내기";

    form.append(input, button);
    section.append(list, form);
    shadow.append(style, section);
    this.#list = list;
    this.#button = button;

    form.addEventListener("submit", (event) => {
      event.preventDefault();
      const request = input.value.trim();
      if (request === "" || button.disabled) {
        return;
      }
      input.value = "";
      void this.#send(request);
    });
  }

  disconnectedCallback(): void {
    this.#running?.abort();
  }

  #append(role: Role, text: string): void {
    const item = document.createElement("li");
    item.dataset["role"] = role;
    item.textContent = text;
    this.#list?.append(item);
  }

  async #send(request: string): Promise<void> {
    const controller = new AbortController();
    this.#running = controller;
    this.#setBusy(true);
    this.#append("user", request);
    try {
      for await (const frame of await startRun(
        targetFromElement(this),
        request,
        controller.signal,
      )) {
        const { role, text } = describeFrame(frame);
        this.#append(role, text);
      }
    } catch (error: unknown) {
      this.#append("event", error instanceof Error ? error.message : String(error));
    } finally {
      this.#setBusy(false);
    }
  }

  #setBusy(busy: boolean): void {
    if (this.#button !== null) {
      this.#button.disabled = busy;
    }
  }
}
