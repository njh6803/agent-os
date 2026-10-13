// 사진 비교(design-system 명세의 "사진 비교 게이트", ADR 0026). 판정 스토리를 뺀 패키지의 스토리를 기본 테마(녹청)의
// 라이트·다크로 찍어 커밋한 정답 사진과 비교한다(판정 스토리는 storybook.ts 가 뺀다). 새 스토리는 저절로 찍히고, 정답
// 사진이 없으면 실패한다. 정답 사진의 이름은 `<스토리 id>-<모드>.png`, 실제 입력의 상태는 `<스토리 id>-<모드>-<상태>.png`
// 다. 스토리가 globals 로 모드를 정했으면 그 모드만 찍는다(일반 루프와 상호작용 루프 모두).
//
// 누름은 스토리 테스트의 userEvent 가 `:active` 를 걸지 못해(ADR 0026 의 넷째 2026-10-06 이력) 여기서만 잰다. 보조·위험
// 버튼은 실제 마우스로 누른 순간의 계산 바탕이 그 쓰임새 토큰이고, 녹청 다크의 카드 안 위험 버튼은 칠한 픽셀과 글자의
// 명암비가 4.5 이상이다(design-refresh 명세의 "위험 버튼의 누름". 판정의 4.507 은 반올림해 겹친 값이라 실제 픽셀을 본다).
import { inflateSync } from "node:zlib";
import type { Locator, Page } from "@playwright/test";
import { contrastRatio } from "../src/testing/index.ts";
import { DEFAULT_THEME } from "../src/themes.ts";
import {
  MODES,
  expect,
  inDefaultTheme,
  photographedStories,
  test,
  type Mode,
  type Storybook,
} from "./storybook.ts";

async function shoot(page: Page, name: string): Promise<void> {
  await expect(page).toHaveScreenshot(`${name}.png`, { fullPage: true });
}

/**
 * 기본 테마의 그 모드로 스토리를 연다. 스토리가 globals 로 다른 테마를 정했으면 실패한다. 사진은 기본 테마만 찍는다
 * (ADR 0026 의 2026-10-06 이력). 그런 스토리는 `judgment` 태그를 달아 사진에서 뺀다.
 */
async function openInDefault(
  storybook: Storybook,
  page: Page,
  id: string,
  mode: Mode,
): Promise<void> {
  await storybook.open(id, inDefaultTheme(mode));
  expect(
    await page.evaluate(() => document.documentElement.dataset["theme"]),
    "기본 테마가 아닌 테마를 정한 스토리는 judgment 태그를 단다",
  ).toBe(DEFAULT_THEME);
}

/**
 * 그려진 모드. 스토리가 globals 로 모드를 정했으면 그 값이 URL 의 값을 이겨 요청한 모드와 다르다. 그 차례는 같은 그림이라
 * 찍지 않는다.
 */
async function renderedMode(page: Page): Promise<string | undefined> {
  return page.evaluate(() => document.documentElement.dataset["mode"]);
}

for (const story of photographedStories()) {
  test(`${story.id} 를 기본 테마의 그려진 모드마다 찍은 사진이 정답과 같다`, async ({
    page,
    storybook,
  }) => {
    const shot: Mode[] = [];
    for (const mode of MODES) {
      await openInDefault(storybook, page, story.id, mode);
      if ((await renderedMode(page)) !== mode) {
        continue;
      }
      await shoot(page, `${story.id}-${mode}`);
      shot.push(mode);
    }
    expect(shot, "찍은 모드").not.toEqual([]);
  });
}

const STATE_NAMES = { hover: "올림", press: "누름", focus: "키보드 포커스" } as const;
type State = keyof typeof STATE_NAMES;

/** 누름에서 맞대는 쓰임새 토큰. 보조 버튼은 `bg-active`, 위험 버튼은 `bg-selected` 다. */
type PressSurface = "bg-active" | "bg-selected";

interface Interaction {
  readonly story: string;
  readonly target: (page: Page) => Locator;
  /** 찍을 상태. 디자인 파일의 상태 표가 그 컴포넌트에 두지 않은 상태는 뺀다. */
  readonly states: readonly State[];
  /** 누름에서 대상의 계산 바탕이 같아야 할 쓰임새 토큰. */
  readonly pressSurface?: PressSurface;
  /** 누름 사진에서 대상의 칠한 픽셀과 글자색의 명암비가 넘어야 할 기준. */
  readonly pressContrast?: number;
}

const BUTTON: readonly State[] = ["hover", "press", "focus"];
// 글 입력과 스위치는 디자인 파일의 상태 표에 누름이 없다(스위치는 재탐색에서 빠졌다).
const NO_PRESS: readonly State[] = ["hover", "focus"];

// 실제 입력의 상태를 더 찍는 스토리. 스토리 테스트의 userEvent 는 합성 이벤트라 :hover·:active 가 걸리지 않는다
// (ADR 0026 의 2026-10-06 이력). 변형마다 올림·누름의 클래스가 달라 변형마다 하나다. 상호작용 컴포넌트를 더하는 티켓은
// 자기 변형의 스토리와 상태를 여기 더한다.
const INTERACTIONS: readonly Interaction[] = [
  {
    story: "atoms-button--primary",
    target: (page) => page.getByRole("button", { name: "승인" }),
    states: BUTTON,
  },
  {
    story: "atoms-button--secondary",
    target: (page) => page.getByRole("button", { name: "거부" }),
    states: BUTTON,
    pressSurface: "bg-active",
  },
  {
    story: "atoms-button--danger",
    target: (page) => page.getByRole("button", { name: "실행 지우기" }),
    states: BUTTON,
    pressSurface: "bg-selected",
  },
  // 위험 버튼의 누름이 기준과 가장 가까운 자리(녹청 다크의 카드 안 4.507). 스토리가 globals 로 다크를 정해 다크만 찍는다.
  {
    story: "atoms-button--danger-in-card-dark",
    target: (page) => page.getByRole("button", { name: "실행 지우기" }),
    states: ["press"],
    pressSurface: "bg-selected",
    pressContrast: 4.5,
  },
  {
    story: "atoms-iconbutton--ghost",
    target: (page) => page.getByRole("button", { name: "보내기" }),
    states: BUTTON,
  },
  {
    story: "atoms-iconbutton--primary",
    target: (page) => page.getByRole("button", { name: "보내기" }),
    states: BUTTON,
  },
  {
    story: "atoms-iconbutton--secondary",
    target: (page) => page.getByRole("button", { name: "더 보기" }),
    states: BUTTON,
  },
  {
    story: "molecules-textfield--single",
    target: (page) => page.getByRole("textbox", { name: "플러그인 이름" }),
    states: NO_PRESS,
  },
  {
    story: "molecules-textfield--multi",
    target: (page) => page.getByRole("textbox", { name: "거부 사유" }),
    states: NO_PRESS,
  },
  // 스위치는 켜짐과 꺼짐의 트랙이 달라 올림의 그림도 다르다. 두 스토리 모두 checked 를 넘겨, 포커스 사진 전에 출발점을
  // 돌리는 빈 자리 click 이 아니더라도 그림이 바뀌지 않는다.
  {
    story: "molecules-switch--off",
    target: (page) => page.getByRole("switch", { name: "결제 환불" }),
    states: NO_PRESS,
  },
  {
    story: "molecules-switch--on",
    target: (page) => page.getByRole("switch", { name: "주문 조회" }),
    states: NO_PRESS,
  },
  // 알림 자체는 상태가 없고 닫기 버튼(투명·작은 아이콘 버튼)이 상태를 따른다. 알림의 면 위에서 찍는다.
  {
    story: "molecules-alert--with-close",
    target: (page) => page.getByRole("button", { name: "닫기" }),
    states: BUTTON,
  },
];

async function matches(target: Locator, selector: string): Promise<boolean> {
  return target.evaluate((element, pseudo) => element.matches(pseudo), selector);
}

/**
 * 대상의 계산 바탕과, 대상 바로 앞에 `background-color: var(--<token>)` 을 둔 숨은 탐침의 계산 바탕. 탐침을 같은 부모에
 * 두는 까닭은 스토리 도우미 `semanticColor`(src/storybook/expect.ts)와 같다. 토큰이 hex 로 풀리지 않으면 던진다. 없는
 * 토큰의 탐침은 투명이라 투명한 대상과 조용히 맞기 때문이다.
 */
async function backgrounds(
  target: Locator,
  token: PressSurface,
): Promise<{ actual: string; expected: string }> {
  const measured = await target.evaluate((element, name) => {
    const probe = document.createElement("span");
    probe.hidden = true;
    probe.style.backgroundColor = `var(--${name})`;
    element.before(probe);
    try {
      const style = getComputedStyle(probe);
      return {
        hex: style.getPropertyValue(`--${name}`).trim(),
        expected: style.backgroundColor,
        actual: getComputedStyle(element).backgroundColor,
      };
    } finally {
      probe.remove();
    }
  }, token);
  if (!/^#[0-9a-f]{6}(?:[0-9a-f]{2})?$/i.test(measured.hex)) {
    throw new Error(`--${token} 이 #RRGGBB 나 #RRGGBBAA 로 풀리지 않았다: "${measured.hex}"`);
  }
  return { actual: measured.actual, expected: measured.expected };
}

type Rgb = readonly [number, number, number];

/** `rgb(r, g, b)` 계산값을 수 셋으로. 그 꼴이 아니면 던진다. */
function rgbOf(text: string): Rgb {
  const match = /^rgb\((\d+), (\d+), (\d+)\)$/.exec(text);
  if (match === null) {
    throw new Error(`불투명한 rgb() 가 아니다: ${text}`);
  }
  const [, red = "", green = "", blue = ""] = match;
  return [Number(red), Number(green), Number(blue)];
}

function hexOf(rgb: Rgb): string {
  return `#${rgb.map((channel) => channel.toString(16).padStart(2, "0")).join("")}`;
}

/**
 * 1×1 PNG 의 화소 RGB. 화소가 하나라 어느 필터든 원래 바이트가 그대로다(왼쪽과 위가 0). 그 읽기는 폭·높이 1, 깊이 8,
 * 색 유형 2(RGB)나 6(RGBA), 인터레이스 없음일 때만 맞아, 머리(IHDR)가 그렇지 않으면 던진다. 선례는
 * .scratch/design-refresh/probes/chromium.mjs 의 firstPixel 이다.
 */
function onlyPixel(png: Buffer): Rgb {
  const idat: Buffer[] = [];
  let header: Buffer | null = null;
  for (let at = 8; at < png.length; at += 12 + png.readUInt32BE(at)) {
    const size = png.readUInt32BE(at);
    const type = png.toString("ascii", at + 4, at + 8);
    if (type === "IHDR") {
      header = png.subarray(at + 8, at + 8 + size);
    } else if (type === "IDAT") {
      idat.push(png.subarray(at + 8, at + 8 + size));
    }
  }
  const plain =
    header !== null &&
    header.readUInt32BE(0) === 1 &&
    header.readUInt32BE(4) === 1 &&
    header[8] === 8 &&
    (header[9] === 2 || header[9] === 6) &&
    header[12] === 0;
  const raw = inflateSync(Buffer.concat(idat));
  const [, red, green, blue] = raw;
  if (!plain || red === undefined || green === undefined || blue === undefined) {
    throw new Error("스크린샷이 1×1·깊이 8·RGB(A)·인터레이스 없음의 PNG 가 아니다");
  }
  return [red, green, blue];
}

/**
 * 누른 대상의 칠한 화소 하나와, 그 아래 바탕(부모 요소들 가운데 처음 칠해진 바탕)과 글자색. 읽는 자리는 대상의 왼쪽
 * 테두리 안 4px, 세로 가운데라 글자(안쪽 여백 뒤)와 둥근 모서리(위아래 끝) 밖이다.
 */
async function pressedPixel(
  page: Page,
  target: Locator,
): Promise<{ painted: Rgb; below: Rgb; text: Rgb }> {
  const box = await target.boundingBox();
  if (box === null) {
    throw new Error("대상이 그려지지 않았다");
  }
  const png = await page.screenshot({
    clip: { x: Math.round(box.x) + 4, y: Math.round(box.y + box.height / 2), width: 1, height: 1 },
  });
  const colors = await target.evaluate((element) => {
    let parent = element.parentElement;
    while (parent !== null && getComputedStyle(parent).backgroundColor === "rgba(0, 0, 0, 0)") {
      parent = parent.parentElement;
    }
    return {
      below: parent === null ? "" : getComputedStyle(parent).backgroundColor,
      text: getComputedStyle(element).color,
    };
  });
  return { painted: onlyPixel(png), below: rgbOf(colors.below), text: rgbOf(colors.text) };
}

for (const { story, target, states, pressSurface, pressContrast } of INTERACTIONS) {
  const names = states.map((state) => STATE_NAMES[state]).join("·");
  test(`${story} 를 실제 입력의 ${names}로 찍은 사진이 기본 테마의 그려진 모드마다 정답과 같다`, async ({
    page,
    storybook,
  }) => {
    const shot: Mode[] = [];
    for (const mode of MODES) {
      // 스토리가 globals 로 모드를 정했으면 다른 모드를 요청한 차례는 같은 그림이라 찍지 않는다. 가드가 없으면 같은 다크
      // 그림이 `-light-` 이름으로도 찍혀 정답이 겹친다.
      await openInDefault(storybook, page, story, mode);
      if ((await renderedMode(page)) !== mode) {
        continue;
      }
      shot.push(mode);
      const element = target(page);
      // 실제 입력이 그 상태를 걸었는지 먼저 본다. 걸리지 않은 채 찍으면 상태 없는 사진이 조용히 정답이 된다.
      if (states.includes("hover")) {
        await element.hover();
        expect(await matches(element, ":hover"), "올림").toBe(true);
        await shoot(page, `${story}-${mode}-hover`);
      }
      if (states.includes("press")) {
        await element.hover();
        await page.mouse.down();
        expect(await matches(element, ":active"), "누름").toBe(true);
        if (pressSurface !== undefined) {
          const { actual, expected } = await backgrounds(element, pressSurface);
          expect(actual, `누름의 계산 바탕이 ${pressSurface} 다`).toBe(expected);
        }
        if (pressContrast !== undefined) {
          const { painted, below, text } = await pressedPixel(page, element);
          // 측정의 표지: 반투명 누름 바탕이 실제로 칠해져 아래 바탕과 다르다.
          expect(painted, "칠한 화소가 아래 바탕과 다르다").not.toEqual(below);
          const ratio = contrastRatio(hexOf(text), hexOf(painted));
          expect(ratio, `칠한 ${hexOf(painted)} 위 글자 ${hexOf(text)}`).toBeGreaterThanOrEqual(
            pressContrast,
          );
        }
        await shoot(page, `${story}-${mode}-press`);
        await page.mouse.up();
      }
      if (states.includes("focus")) {
        // 누르면 버튼이 포커스를 받아, 그대로 Tab 을 누르면 순차 탐색이 버튼 다음에서 시작해 버튼에 오지 않았다(측정
        // tokens/measure.mjs 의 states). 빈 자리를 눌러 출발점을 문서 처음으로 돌린다.
        await page.mouse.click(1, 1);
        await page.keyboard.press("Tab");
        await expect(element).toBeFocused();
        expect(await matches(element, ":focus-visible"), "키보드 포커스").toBe(true);
        await shoot(page, `${story}-${mode}-focus`);
      }
    }
    expect(shot, "찍은 모드").not.toEqual([]);
  });
}
