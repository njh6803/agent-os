// 페이지 안 방식의 커스텀 요소가 shadow root 에 마운트되는지 본다(web-widget 명세 Testing Decisions 1, ADR 0024 의
// 테스트 항목). 화면 동작은 위젯 페이지 시험이 light DOM 에서 이미 본다. jsdom 의 shadow root 안에서는 user-event 로 친
// 글자가 React 의 onChange 에 닿지 않아(ADR 0024), 실제 shadow 동작은 위젯 e2e 가 본다.
//
// 요소의 이름은 문서마다 한 번만 정의되므로 사례마다 다른 이름으로 정의한다.

import { UI_ROOT_ATTRIBUTE } from "@agent-os/ui";
import { act, screen, within } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { widgetElement, type ElementSetup } from "./WidgetElement";

const BASE = new URL("https://widget.example");
let defined = 0;

function define(setup: Partial<ElementSetup> = {}): string {
  const name = `agent-os-widget-test-${String(++defined)}`;
  customElements.define(name, widgetElement({ sheets: [], baseUrl: BASE, ...setup }));
  return name;
}

function mount(name: string, attributes: Record<string, string>): HTMLElement {
  const host = document.createElement(name);
  for (const [attribute, value] of Object.entries(attributes)) {
    host.setAttribute(attribute, value);
  }
  act(() => {
    document.body.append(host);
  });
  return host;
}

function wrapper(host: HTMLElement): HTMLElement {
  const found = host.shadowRoot?.querySelector<HTMLElement>(`[${UI_ROOT_ATTRIBUTE}]`);
  if (found === null || found === undefined) {
    throw new Error("shadow root 안에 감싼 요소가 없다");
  }
  return found;
}

afterEach(() => {
  act(() => {
    document.body.replaceChildren();
  });
});

test("붙이면 open 모드의 shadow root 안 감싼 요소에 위젯이 그려지고 시트가 실린다", () => {
  const sheet = new CSSStyleSheet();
  const host = mount(define({ sheets: [sheet] }), {
    agent: "order-helper",
    heading: "주문 도우미",
    intro: "주문을 찾아 드립니다.",
  });

  expect(host.shadowRoot?.mode).toBe("open");
  expect(host.shadowRoot?.adoptedStyleSheets).toEqual([sheet]);
  const root = wrapper(host);
  expect(root.parentNode).toBe(host.shadowRoot);
  expect(within(root).getByRole("heading", { name: "주문 도우미" })).toBeTruthy();
  expect(within(root).getByText("주문을 찾아 드립니다.")).toBeTruthy();
  expect(within(root).getByRole("textbox", { name: "요청" })).toBeTruthy();
  // 위젯은 light DOM 에 아무것도 그리지 않는다.
  expect(screen.queryByRole("heading")).toBeNull();
});

test("호스트에 테마와 모드와 보통 밀도가 달리고, 속성을 바꾸면 따라간다", () => {
  const host = mount(define(), { agent: "order-helper", theme: "guncheong", mode: "dark" });
  expect(host.dataset).toMatchObject({ theme: "guncheong", mode: "dark", density: "regular" });

  act(() => {
    host.setAttribute("heading", "주문 도우미");
    host.removeAttribute("mode");
    host.setAttribute("theme", "jacho");
  });
  expect(host.dataset["theme"]).toBe("jacho");
  expect(host.dataset["mode"]).toBeUndefined();
  expect(host.dataset["density"]).toBe("regular");
  expect(within(wrapper(host)).getByRole("heading", { name: "주문 도우미" })).toBeTruthy();
});

test("잘못 준 agent 는 위험 알림과 막힌 입력창, 그 속성 이름을 든 console.error 를 남긴다", () => {
  const errors = vi.spyOn(console, "error").mockImplementation(() => undefined);
  const host = mount(define(), { agent: "Order Helper", mode: "sepia" });

  const root = wrapper(host);
  expect(within(root).getByText("위젯 설정이 올바르지 않습니다.")).toBeTruthy();
  expect(within(root).getByRole("textbox", { name: "요청" })).toHaveProperty("disabled", true);
  const logged = errors.mock.calls.map((call) => String(call[0]));
  expect(logged.filter((line) => line.startsWith("위젯 속성 agent: "))).toHaveLength(1);
  expect(logged.filter((line) => line.startsWith("위젯 속성 mode: "))).toHaveLength(1);
  // 목록 밖의 모드는 기본값으로 그린다.
  expect(host.dataset["mode"]).toBeUndefined();
});

test("번들의 기준 주소가 없으면 위험 알림과 console.error 를 남기고 입력창을 막는다", () => {
  const errors = vi.spyOn(console, "error").mockImplementation(() => undefined);
  const host = mount(define({ baseUrl: null }), { agent: "order-helper" });

  const root = wrapper(host);
  expect(within(root).getByText("위젯 설정이 올바르지 않습니다.")).toBeTruthy();
  expect(within(root).getByRole("textbox", { name: "요청" })).toHaveProperty("disabled", true);
  const logged = errors.mock.calls.map((call) => String(call[0]));
  expect(logged.filter((line) => line.includes("document.currentScript"))).toHaveLength(1);
});

test("정의되기 전에 사이트가 단 tokenProvider 를 정의된 뒤에도 든다", () => {
  const name = `agent-os-widget-test-${String(++defined)}`;
  const host = document.createElement(name);
  const provider = () => Promise.resolve("signed.token.value");
  Reflect.set(host, "tokenProvider", provider);
  document.body.append(host);

  act(() => {
    customElements.define(name, widgetElement({ sheets: [], baseUrl: BASE }));
  });

  expect(Object.hasOwn(host, "tokenProvider")).toBe(false);
  expect(Reflect.get(host, "tokenProvider")).toBe(provider);
});

test("떼면 그림을 걷고, 다시 붙이면 다시 그린다", () => {
  const host = mount(define(), { agent: "order-helper" });
  act(() => {
    host.remove();
  });
  expect(host.shadowRoot?.querySelector("[role=textbox], textarea")).toBeNull();

  act(() => {
    document.body.append(host);
  });
  expect(within(wrapper(host)).getByRole("textbox", { name: "요청" })).toBeTruthy();
});
