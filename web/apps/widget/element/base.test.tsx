// 페이지 안 방식의 API 기준 주소. 번들이 처음 실행될 때의 `document.currentScript` 가 `HTMLScriptElement` 의
// 인스턴스일 때만 그 `src` 의 출처를 쓴다(web-widget 명세 "API의 기준 주소"). 이름 있는 요소가 그 자리를 가리는
// DOM clobbering 의 갈래(다른 요소, 컬렉션)는 기준 주소가 없다.

import { afterEach, describe, expect, test } from "vitest";
import { scriptBaseUrl } from "./base";

afterEach(() => {
  document.body.replaceChildren();
});

function element<K extends keyof HTMLElementTagNameMap>(
  tag: K,
  attributes: Record<string, string>,
): HTMLElementTagNameMap[K] {
  const created = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes)) {
    created.setAttribute(name, value);
  }
  document.body.append(created);
  return created;
}

test("번들의 script 요소면 그 src 의 출처가 기준 주소다", () => {
  const script = element("script", { src: "https://widget.example:8443/widget/element.js?v=1" });
  expect(scriptBaseUrl(script)?.href).toBe("https://widget.example:8443/");
});

test("src 를 상대 경로로 적어도 문서 기준으로 푼 출처다", () => {
  const script = element("script", { src: "/widget/element.js" });
  expect(scriptBaseUrl(script)?.origin).toBe(window.location.origin);
});

describe("기준 주소가 없다", () => {
  test("currentScript 가 없다", () => {
    expect(scriptBaseUrl(null)).toBeNull();
  });

  test("이름이 currentScript 인 img 가 그 자리를 가렸다", () => {
    const image = element("img", { name: "currentScript", src: "https://attacker.example/" });
    expect(scriptBaseUrl(image)).toBeNull();
  });

  test("이름 있는 요소 둘이 컬렉션으로 그 자리를 가렸다", () => {
    element("img", { name: "currentScript", src: "https://attacker.example/a" });
    element("img", { name: "currentScript", src: "https://attacker.example/b" });
    expect(scriptBaseUrl(document.getElementsByName("currentScript"))).toBeNull();
  });

  test("src 가 있는 다른 요소다", () => {
    const frame = element("iframe", { src: "https://attacker.example/" });
    expect(scriptBaseUrl(frame)).toBeNull();
  });

  test("src 없이 인라인으로 든 script 다", () => {
    expect(scriptBaseUrl(element("script", {}))).toBeNull();
  });

  test("출처가 불투명한 src 다", () => {
    expect(scriptBaseUrl(element("script", { src: "data:text/javascript,0" }))).toBeNull();
  });
});
