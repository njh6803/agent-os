// 위젯이 열릴 때 값 파일(`/widget/runtime.json`)을 받는 길(widget-runtime-values 티켓 01). 받기 전에는 틀만 그리고 입력을
// 막으며 토큰을 묻지 않는다. 받은 뒤에는 입력창이 받은 상한을 따르고 토큰을 받은 허용 출처로 묻는다. 다시 받으면 풀릴 수 있는
// 실패에는 "받아 오지 못했습니다"와 "다시 시도"가, 404 에는 "올바르지 않습니다"가 선다. 다른 시험은 값을 받은 상태로 시작한다
// (testing/setup.ts). 여기서는 그 값을 걷고 값 파일의 응답을 흉내 낸다. 가짜는 HTTP(MSW)와 부모 창(testing/site.ts)뿐이다.

import { cleanup, screen, waitFor } from "@testing-library/react";
import { http, HttpResponse, type JsonBodyType } from "msw";
import { beforeEach, describe, expect, test, vi } from "vitest";
import { RUNTIME_PATH, RUNTIME_TIMEOUT_MS, clearRuntimeValues } from "../../lib/runtime";
import { gate, network } from "../../testing/network";
import { serveTokens } from "../../testing/site";
import {
  advance,
  ask,
  FINISHED,
  onStart,
  openWidget,
  requestBox,
  sendButton,
} from "../../testing/widget";

const VALUES_URL = new URL(RUNTIME_PATH, window.location.origin).href;

beforeEach(() => {
  // setup.ts 가 둔 받은 값을 걷는다. 값은 아래 응답으로 받는다.
  clearRuntimeValues();
});

/** 값 파일에 응답을 걸고, 받은 요청의 수를 세어 돌려준다. */
function serveValues(respond: () => Response | Promise<Response>): { count: number } {
  const asked = { count: 0 };
  network.use(
    http.get(VALUES_URL, () => {
      asked.count += 1;
      return respond();
    }),
  );
  return asked;
}

const GOOD = (
  body: JsonBodyType = { allowedOrigins: ["https://shop.example"], requestChars: 20_000 },
) => HttpResponse.json(body);

/** `fetch` 의 첫 인자가 글자든 주소 객체든 요청 객체든 가리키는 주소를 글자로 돌려준다. */
function addressOf(input: Parameters<typeof fetch>[0]): string {
  if (typeof input === "string") {
    return input;
  }
  return input instanceof URL ? input.href : input.url;
}

function isDisabled(element: HTMLElement): boolean {
  return "disabled" in element && element.disabled === true;
}

async function opened(): Promise<void> {
  await waitFor(() => {
    expect(isDisabled(requestBox())).toBe(false);
  });
}

describe("받는 동안", () => {
  test("틀만 그리고 입력을 막으며, 받으면 열린다", async () => {
    const release = gate();
    serveValues(async () => {
      await release.wait;
      return GOOD();
    });

    openWidget();

    // 위쪽 띠는 서고 대화 자리는 비어 있다. 첫 화면의 안내도 값을 받은 뒤에 선다.
    expect(screen.getByRole("heading", { name: "주문 도우미" })).toBeTruthy();
    expect(isDisabled(requestBox())).toBe(true);
    expect(isDisabled(sendButton())).toBe(true);
    expect(screen.queryByText("위젯 설정을 받아 오지 못했습니다.")).toBeNull();
    expect(screen.queryByText("위젯 설정이 올바르지 않습니다.")).toBeNull();

    release.open();
    await opened();
  });

  test("값을 받기 전에는 부모 창에 토큰을 묻지 않고, 받은 뒤에 저장한 대화를 되살린다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    // 먼저 값을 받은 상태로 대화하고 새로 고친다. 저장이 남는다.
    serveValues(() => GOOD());
    const tokens = serveTokens();
    onStart(() => FINISHED());
    const first = openWidget();
    await opened();
    await ask(first, "배송은 언제 오나요?");
    await screen.findByText("도착 예정입니다.", { selector: "ol p" });
    cleanup();
    clearRuntimeValues();
    const askedBefore = tokens.length;

    const release = gate();
    serveValues(async () => {
      await release.wait;
      return GOOD();
    });
    openWidget();
    // 받는 동안은 토큰을 묻지 않아 저장한 대화도 되살리지 않는다.
    await advance(50);
    expect(tokens).toHaveLength(askedBefore);
    expect(screen.queryByText("도착 예정입니다.", { selector: "ol p" })).toBeNull();

    release.open();
    await screen.findByText("도착 예정입니다.", { selector: "ol p" });
    expect(tokens.length).toBeGreaterThan(askedBefore);
  });
});

describe("받은 뒤", () => {
  test("입력창이 받은 상한을 따른다", async () => {
    serveValues(() => GOOD({ allowedOrigins: ["https://shop.example"], requestChars: 10 }));
    const user = openWidget();
    await opened();

    await user.type(requestBox(), "가나다라마바사아자");

    // 상한의 90% 이상이면 센 수가 입력창에 묶여 보인다.
    const count = document.getElementById(requestBox().getAttribute("aria-describedby") ?? "");
    expect(count?.textContent).toBe("9 / 10");
  });

  test("토큰은 받은 허용 출처의 부모 창이 보낸 것만 받는다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    serveValues(() => GOOD({ allowedOrigins: ["https://other.example"], requestChars: 20_000 }));
    // 기본 흉내는 shop.example 이 답한다. 받은 허용 출처에는 없어 위젯이 그 답을 버린다.
    const started = onStart(() => FINISHED());
    serveTokens();
    const user = openWidget();
    await opened();

    await ask(user, "요청");
    await advance(500);

    expect(started).toEqual([]);
  });

  test("두 키만 보고 모르는 키는 무시하며, 2^53 을 넘는 상한도 받는다", async () => {
    serveValues(() =>
      GOOD({
        allowedOrigins: ["https://shop.example"],
        requestChars: Number.MAX_VALUE,
        schema_version: 3,
        extra: "무시한다",
      }),
    );
    openWidget();

    await opened();
    expect(screen.queryByText("위젯 설정을 받아 오지 못했습니다.")).toBeNull();
  });

  test("쿠키와 자격 증명을 싣지 않고 한 번만 받는다", async () => {
    // MSW 가 요청을 다시 지어 `credentials` 가 가려져, 전역 fetch 에 준 인자를 본다.
    const fetched = vi.spyOn(globalThis, "fetch");
    const asked = serveValues(() => GOOD());
    openWidget();
    await opened();
    // 다시 그려도 같은 문서에서는 다시 받지 않는다.
    cleanup();
    openWidget();
    await opened();

    expect(asked.count).toBe(1);
    const own = fetched.mock.calls.filter(([input]) => addressOf(input) === VALUES_URL);
    expect(own.map(([, init]) => init?.credentials)).toEqual(["omit"]);
  });
});

describe("다시 받으면 풀릴 수 있는 실패", () => {
  const FAILURES: readonly (readonly [string, () => Response])[] = [
    ["요청이 실패했다", () => HttpResponse.error()],
    ["500 이다", () => new HttpResponse(null, { status: 500 })],
    ["503 이다", () => new HttpResponse(null, { status: 503 })],
    ["404 가 아닌 다른 200 밖의 답이다", () => new HttpResponse(null, { status: 403 })],
    ["JSON 이 아니다", () => HttpResponse.text("<html>")],
    [
      "허용 출처가 글자의 목록이 아니다",
      () => GOOD({ allowedOrigins: "https://shop.example", requestChars: 5 }),
    ],
    ["허용 출처의 항목이 글자가 아니다", () => GOOD({ allowedOrigins: [1], requestChars: 5 })],
    ["상한이 없다", () => GOOD({ allowedOrigins: [] })],
    ["상한이 0 이다", () => GOOD({ allowedOrigins: [], requestChars: 0 })],
    ["상한이 정수가 아니다", () => GOOD({ allowedOrigins: [], requestChars: 1.5 })],
    ["상한이 글자다", () => GOOD({ allowedOrigins: [], requestChars: "20000" })],
    ["상한이 null 이다", () => GOOD({ allowedOrigins: [], requestChars: null })],
    ["답이 목록이다", () => GOOD([])],
  ];

  for (const [name, respond] of FAILURES) {
    test(`${name}. 알림과 "다시 시도"가 서고 입력이 막히며 스스로 다시 받지 않는다`, async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      const asked = serveValues(respond);
      openWidget();

      expect(await screen.findByText("위젯 설정을 받아 오지 못했습니다.")).toBeTruthy();
      expect(screen.getByRole("button", { name: "다시 시도" })).toBeTruthy();
      expect(isDisabled(requestBox())).toBe(true);
      expect(isDisabled(sendButton())).toBe(true);
      await advance(60_000);
      expect(asked.count).toBe(1);
    });
  }

  test("10초 안에 답이 없으면 받지 못한 것이다", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    serveValues(() => new Promise<Response>(() => {}));
    openWidget();

    await advance(RUNTIME_TIMEOUT_MS - 1_000);
    expect(screen.queryByText("위젯 설정을 받아 오지 못했습니다.")).toBeNull();
    expect(isDisabled(requestBox())).toBe(true);

    await advance(1_000);
    expect(await screen.findByText("위젯 설정을 받아 오지 못했습니다.")).toBeTruthy();
  });

  test('"다시 시도"를 누르면 받는 동안의 화면으로 돌아가 다시 받고, 받으면 열린다', async () => {
    const release = gate();
    let calls = 0;
    const asked = serveValues(async () => {
      calls += 1;
      if (calls === 1) {
        return new HttpResponse(null, { status: 503 });
      }
      await release.wait;
      return GOOD();
    });
    const user = openWidget();
    await user.click(await screen.findByRole("button", { name: "다시 시도" }));

    // 받는 동안: 알림과 단추가 없고 입력은 막혀 있다.
    await waitFor(() => {
      expect(screen.queryByRole("button", { name: "다시 시도" })).toBeNull();
    });
    expect(screen.queryByText("위젯 설정을 받아 오지 못했습니다.")).toBeNull();
    expect(isDisabled(requestBox())).toBe(true);

    release.open();
    await opened();
    expect(asked.count).toBe(2);
  });

  test("다시 시도도 실패하면 다시 알림과 단추가 선다", async () => {
    serveValues(() => new HttpResponse(null, { status: 503 }));
    const user = openWidget();

    await user.click(await screen.findByRole("button", { name: "다시 시도" }));

    expect(await screen.findByRole("button", { name: "다시 시도" })).toBeTruthy();
    expect(screen.getByText("위젯 설정을 받아 오지 못했습니다.")).toBeTruthy();
  });
});

describe("값 파일이 없다(404)", () => {
  test('"올바르지 않습니다" 알림이 서고 "다시 시도"는 없으며 입력이 막힌다', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const asked = serveValues(() => new HttpResponse(null, { status: 404 }));
    openWidget();

    expect(await screen.findByText("위젯 설정이 올바르지 않습니다.")).toBeTruthy();
    expect(screen.getByText("사이트 관리자에게 알려 주세요.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "다시 시도" })).toBeNull();
    expect(screen.queryByText("위젯 설정을 받아 오지 못했습니다.")).toBeNull();
    expect(isDisabled(requestBox())).toBe(true);
    await advance(60_000);
    expect(asked.count).toBe(1);
  });
});
