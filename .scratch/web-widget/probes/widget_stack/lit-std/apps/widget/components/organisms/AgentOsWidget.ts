// 채팅 위젯 하나(Lit 3, 표준 데코레이터). 입력창, 메시지 목록, 보내기 버튼. 보내면 실행을 일으키고 프레임을 받는 대로
// 목록에 붙인다. Lit 요소는 스스로 shadow root 에 그리므로 커스텀 요소가 곧 UI 다. 정의(customElements.define)는
// 입구(element.ts)가 한다. 부를 곳은 속성에서 온다(api-base 는 속성 이름만 다르다).

import { html, LitElement, unsafeCSS, type TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import { startRun, type RunTarget } from "../../api/runs";
import { describeFrame, type Line, type Role } from "../../lib/frames";
import { STYLES } from "../../lib/styles";

export class AgentOsWidget extends LitElement {
  static override styles = unsafeCSS(STYLES);

  @property({ attribute: "api-base" }) accessor apiBase = "";
  @property() accessor agent = "";
  @property() accessor token = "";
  @state() accessor lines: readonly Line[] = [];
  @state() accessor draft = "";
  @state() accessor busy = false;

  #nextId = 0;
  #running: AbortController | null = null;

  override disconnectedCallback(): void {
    super.disconnectedCallback();
    this.#running?.abort();
  }

  override render(): TemplateResult {
    return html`
      <section class="widget" aria-label="채팅">
        <ul class="messages" aria-label="메시지">
          ${this.lines.map((line) => html`<li data-role=${line.role}>${line.text}</li>`)}
        </ul>
        <form @submit=${this.#submit}>
          <input aria-label="메시지 입력" .value=${this.draft} @input=${this.#input} />
          <button type="submit" ?disabled=${this.busy}>보내기</button>
        </form>
      </section>
    `;
  }

  #target(): RunTarget {
    return { baseUrl: this.apiBase, token: this.token, agent: this.agent };
  }

  #append(role: Role, text: string): void {
    const id = this.#nextId;
    this.#nextId += 1;
    this.lines = [...this.lines, { id, role, text }];
  }

  readonly #input = (event: Event): void => {
    if (event.target instanceof HTMLInputElement) {
      this.draft = event.target.value;
    }
  };

  readonly #submit = (event: SubmitEvent): void => {
    event.preventDefault();
    const request = this.draft.trim();
    if (request === "" || this.busy) {
      return;
    }
    this.draft = "";
    void this.#send(request);
  };

  async #send(request: string): Promise<void> {
    const controller = new AbortController();
    this.#running = controller;
    this.busy = true;
    this.#append("user", request);
    try {
      for await (const frame of await startRun(this.#target(), request, controller.signal)) {
        const { role, text } = describeFrame(frame);
        this.#append(role, text);
      }
    } catch (error: unknown) {
      this.#append("event", error instanceof Error ? error.message : String(error));
    } finally {
      this.busy = false;
    }
  }
}
