// 채팅 위젯 하나(Lit 3, 데코레이터 없이). 입력창, 메시지 목록, 보내기 버튼. 보내면 실행을 일으키고 프레임을 받는 대로
// 목록에 붙인다. Lit 요소는 스스로 shadow root 에 그리므로 커스텀 요소가 곧 UI 다. 정의(customElements.define)는
// 입구(element.ts)가 한다. 부를 곳은 속성에서 온다(api-base 는 속성 이름만 다르다).
//
// 반응 속성은 `static properties` 와 `declare` 필드로 둔다. 표준 데코레이터(lit-std/ 의 같은 파일)는 tsc 와 판정자를
// 지나지만 Vite 8 의 변환이 데코레이터를 그대로 내보내고 Next 16 의 SWC 가 accessor 에서 멈췄다(lit-std 후보를
// verify.mjs·measure.mjs·shadow.mjs 로 돌린 결과). 실험 데코레이터(lit-legacy/)는 Next 빌드에서 반응 속성이 가려졌다.
// `declare` 는 필드를 내보내지 않아 Lit 의 접근자를 가리지 않는다. 초깃값은 생성자에서 넣는다.

import { html, LitElement, unsafeCSS, type TemplateResult } from "lit";
import { startRun, type RunTarget } from "../../api/runs";
import { describeFrame, type Line, type Role } from "../../lib/frames";
import { STYLES } from "../../lib/styles";

export class AgentOsWidget extends LitElement {
  static override styles = unsafeCSS(STYLES);

  static override properties = {
    apiBase: { attribute: "api-base" },
    agent: {},
    token: {},
    lines: { state: true },
    draft: { state: true },
    busy: { state: true },
  };

  declare apiBase: string;
  declare agent: string;
  declare token: string;
  declare lines: readonly Line[];
  declare draft: string;
  declare busy: boolean;

  #nextId = 0;
  #running: AbortController | null = null;

  constructor() {
    super();
    this.apiBase = "";
    this.agent = "";
    this.token = "";
    this.lines = [];
    this.draft = "";
    this.busy = false;
  }

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
