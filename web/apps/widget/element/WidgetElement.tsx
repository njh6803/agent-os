// 페이지 안 방식의 커스텀 요소 `<agent-os-widget>`(web-widget 명세 "임베드"의 페이지 안 방식, ADR 0024). 사이트는 번들
// script 한 줄과 이 요소 하나를 넣고, 요소의 속성(property) `tokenProvider` 에 토큰 함수를 준다. 화면은 iframe 방식과
// 같은 위젯 한 벌(components/pages/ConnectedWidget)이다. 번들 입구(index.ts)가 이 클래스를 정의한다.
//
// - 속성(attribute)은 다섯이고 이름과 뜻은 iframe 의 질의와 같다(lib/embed.ts). 바뀌면 다시 그린다. 잘못 준 속성은
//   하나마다 그 이름을 든 console.error 로 남는다. `agent` 가 바뀌면 위젯 한 벌을 새로 띄운다. 화면의 대화와 이어 갈
//   실행은 위젯 한 벌(useConversation)이 들어, 그대로 두면 새 에이전트 아래에 앞 에이전트와 나눈 대화가 보이고 다음
//   요청이 앞 에이전트의 실행을 이어 간다. 서버의 이어 가기는 앞 실행의 에이전트가 같은지 보지 않고 지금 에이전트의
//   교환만 모아(core/continuation.py), 새 에이전트는 화면에 보인 그 대화를 받지 못한다. iframe 방식은 질의가 바뀌면
//   문서가 새로 뜬다.
// - `open` 모드의 shadow root 에 그린다. 페이지 스크립트는 이미 위젯과 같은 출처의 권한으로 돌아 `closed` 가 막는 것이
//   없다(명세 "Shadow DOM"). 그 안의 감싼 요소(`data-ui-root`) 하나가 React 의 뿌리이고, 상속 속성은 디자인 토큰 CSS 가
//   거기서 다시 정한다(ADR 0026).
// - 테마와 모드는 호스트의 `data-theme`·`data-mode` 로 옮겨 디자인 토큰 CSS 의 `:host(...)` 가 받는다. 호스트에는
//   `data-density="regular"` 를 단다. shadow 호스트는 바깥의 밀도를 물려받지 않아, 빠뜨리면 넓은 창에서 촘촘해진다.
//   속성은 붙을 때부터 단다. 생성자에서 속성을 더하면 `createElement` 가 실패한다(Custom Elements 의 생성자 규칙).
// - 번들의 기준 주소가 없으면(element/base.ts) 토큰 함수를 부르지도 요청을 보내지도 않고, 잘못 준 속성과 같은 위험
//   알림과 console.error 를 남긴다.
// - 사이트가 요소가 정의되기 전에 `tokenProvider` 를 대입하면 그 값은 인스턴스의 자기 속성으로 남아 이 클래스의
//   접근자를 가린다. 업그레이드되는 생성자에서 그 값을 옮겨 담고 자기 속성을 지운다.
// - 떼면 React 뿌리를 걷어 열린 스트림이 끊기고(useConversation), 다시 붙이면 새로 그린다.

import { UI_ROOT_ATTRIBUTE } from "@agent-os/ui";
import { createRoot, type Root } from "react-dom/client";
import { ConnectedWidget } from "../components/pages/ConnectedWidget";
import type { Connection } from "../lib/connection";
import { EMBED_NAMES, readEmbed } from "../lib/embed";
import { providerToken } from "./token";

export const ELEMENT_NAME = "agent-os-widget";

const PROVIDER = "tokenProvider";

/** 번들의 기준 주소를 읽지 못했을 때 남기는 글. */
export const BASE_URL_PROBLEM =
  "위젯 번들의 기준 주소: document.currentScript 가 이 번들의 script 요소가 아니다(사이트 페이지의 이름 있는 요소가 그 자리를 가렸을 수 있다). 토큰 함수를 부르지 않고 요청을 보내지 않는다";

export interface ElementSetup {
  /** shadow root 의 `adoptedStyleSheets`. 같은 문서의 위젯이 함께 든다. */
  readonly sheets: readonly CSSStyleSheet[];
  /** 번들의 기준 주소. null 이면 요청을 보낼 수 없는 설정이다. */
  readonly baseUrl: URL | null;
}

/** 위젯 요소의 클래스. 이름을 붙여 정의하는 것은 부르는 쪽이다. */
export function widgetElement(setup: ElementSetup): CustomElementConstructor {
  return class AgentOsWidget extends HTMLElement {
    static readonly observedAttributes: readonly string[] = EMBED_NAMES;

    #provider: unknown = undefined;
    #root: Root | null = null;
    readonly #connection: Connection | null;

    constructor() {
      super();
      if (Object.hasOwn(this, PROVIDER)) {
        const provider: unknown = Reflect.get(this, PROVIDER);
        Reflect.deleteProperty(this, PROVIDER);
        this.#provider = provider;
      }
      const { baseUrl } = setup;
      this.#connection =
        baseUrl === null ? null : { baseUrl, token: () => providerToken(this.#provider) };
    }

    /** 사이트가 주는 토큰 함수(`() => Promise<string>`). 요청을 보낼 때마다 부른다. */
    get tokenProvider(): unknown {
      return this.#provider;
    }

    set tokenProvider(provider: unknown) {
      this.#provider = provider;
    }

    connectedCallback(): void {
      const shadow = this.shadowRoot ?? this.attachShadow({ mode: "open" });
      shadow.adoptedStyleSheets = [...setup.sheets];
      const wrapper = document.createElement("div");
      wrapper.setAttribute(UI_ROOT_ATTRIBUTE, "");
      shadow.replaceChildren(wrapper);
      this.#root = createRoot(wrapper);
      this.#render();
    }

    disconnectedCallback(): void {
      this.#root?.unmount();
      this.#root = null;
    }

    attributeChangedCallback(): void {
      this.#render();
    }

    #render(): void {
      const root = this.#root;
      if (root === null) {
        return;
      }
      const { embed, problems } = readEmbed((name) => this.getAttribute(name));
      this.dataset["theme"] = embed.theme;
      if (embed.mode === null) {
        delete this.dataset["mode"];
      } else {
        this.dataset["mode"] = embed.mode;
      }
      this.dataset["density"] = "regular";
      const messages = problems.map((problem) => `위젯 속성 ${problem.name}: ${problem.reason}`);
      if (this.#connection === null) {
        messages.push(BASE_URL_PROBLEM);
      }
      root.render(
        <ConnectedWidget
          key={embed.agent ?? ""}
          embed={embed}
          problems={messages}
          connection={this.#connection}
        />,
      );
    }
  };
}
