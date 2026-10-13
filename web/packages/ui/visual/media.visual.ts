// 미디어 특성(prefers-color-scheme, prefers-reduced-motion, 창의 폭)을 바꿔 가며 같은 정적 빌드를 연다. 사진은
// Playwright 가 움직임을 멈춰 찍어 움직임 줄이기를 가르지 못한다(design-system 명세의 사진 비교 게이트). 시스템 모드와
// 속성 없는 문서·호스트는 명세의 스토리 13 이고, 속성 없는 밀도는 design-refresh 명세의 "사진 비교"의 미디어 특성이다.
// 스토리 테스트의 창은 1200×900 으로 고정이라 창의 폭은 여기서 바꾼다. 쓰임새 토큰과 밀도 변수의 기대값은 디자인 파일이
// 아니라 같은 빌드에서 그 `data-theme`·`data-mode`·`data-density` 를 단 요소로 읽는다. 선례는 측정
// tokens/measure.mjs 의 switch 와 motion 이다.
import type { Locator, Page } from "@playwright/test";
import { DEFAULT_THEME, type Density, type ThemeKey } from "../src/themes.ts";
import { MODES, expect, inDefaultTheme, test, type Mode } from "./storybook.ts";

// 속성을 지우는 사례가 그리는 표본. 판정 스토리가 아니고 globals 로 테마·모드를 정하지 않은 스토리다.
const SAMPLE = "atoms-button--primary";

// 속성을 지우기 전에 다는 테마. 기본 테마가 아니면 된다.
const OTHER_THEME: ThemeKey = "guncheong";

const OPPOSITE: Readonly<Record<Mode, Mode>> = { light: "dark", dark: "light" };

// 주 버튼 묶음. 군청·자초는 시스템 모드에서도 `@media (prefers-color-scheme: …)` 안의 덮기로 강조색 갈래가 된다.
const PRIMARY = ["--primary", "--on-primary", "--primary-hover", "--primary-active"] as const;

/** 요소에서 풀린 사용자 정의 속성들의 값. */
function tokens(target: Locator, names: readonly string[]): Promise<string[]> {
  return target.evaluate(
    (element, list) => list.map((name) => getComputedStyle(element).getPropertyValue(name).trim()),
    [...names],
  );
}

async function background(target: Locator): Promise<string> {
  const [value = ""] = await tokens(target, ["--bg"]);
  return value;
}

/** 탐침에 다는 data 속성. 주지 않은 것은 달지 않는다. */
interface ProbeData {
  readonly theme?: ThemeKey;
  readonly mode?: Mode;
  readonly density?: Density;
}

/** 문서에 그 data 속성들을 단 요소를 하나 두고 그 값들을 읽은 뒤 걷는다. */
async function probeTokens(
  page: Page,
  { theme, mode, density }: ProbeData,
  names: readonly string[],
): Promise<string[]> {
  const entries = Object.entries({ theme, mode, density }).flatMap(([name, value]) =>
    value === undefined ? [] : [[name, value] as const],
  );
  await page.evaluate((data) => {
    const probe = document.createElement("div");
    probe.dataset["visualProbe"] = "";
    for (const [name, value] of data) {
      probe.dataset[name] = value;
    }
    document.body.append(probe);
  }, entries);
  const probe = page.locator("[data-visual-probe]");
  const values = await tokens(probe, names);
  await probe.evaluate((element) => {
    element.remove();
  });
  return values;
}

/** 기본 테마의 그 모드로 단 탐침의 `--bg`. */
async function defaultBackground(page: Page, mode: Mode): Promise<string> {
  const [value = ""] = await probeTokens(page, { theme: DEFAULT_THEME, mode }, ["--bg"]);
  return value;
}

/** 미리보기는 디자인 토큰 CSS 를 문서에 전역으로 싣는다. shadow 안의 값이 shadow 의 시트에서만 오는지 보려고 끈다. */
async function disableDocumentSheets(page: Page): Promise<void> {
  await page.evaluate(() => {
    for (const sheet of document.styleSheets) {
      sheet.disabled = true;
    }
  });
}

test("시스템 모드에서 문서 뿌리의 --bg 가 시스템의 라이트·다크를 따라 기본 테마의 그 모드 값이다", async ({
  page,
  storybook,
}) => {
  const seen: string[] = [];
  for (const scheme of MODES) {
    await page.emulateMedia({ colorScheme: scheme });
    await storybook.open(SAMPLE, {
      theme: DEFAULT_THEME,
      mode: "system",
      density: "auto",
      shadow: "off",
    });
    const expected = await defaultBackground(page, scheme);
    expect(await background(page.locator("html")), scheme).toBe(expected);
    seen.push(expected);
  }
  expect(new Set(seen).size, "라이트와 다크의 --bg 가 다르다").toBe(2);
});

test("문서 뿌리에서 데코레이터가 단 data-theme·data-mode 를 지우면 시스템 라이트·다크 모두 기본 테마의 값이다", async ({
  page,
  storybook,
}) => {
  const root = page.locator("html");
  for (const scheme of MODES) {
    await page.emulateMedia({ colorScheme: scheme });
    // 지우기 전의 값이 기대값과 달라야 지운 효과를 본다. 다른 테마에 시스템과 반대 모드를 단다.
    await storybook.open(SAMPLE, {
      theme: OTHER_THEME,
      mode: OPPOSITE[scheme],
      density: "auto",
      shadow: "off",
    });
    const expected = await defaultBackground(page, scheme);
    expect(await background(root), `${scheme} 지우기 전`).not.toBe(expected);
    await root.evaluate((element) => {
      element.removeAttribute("data-theme");
      element.removeAttribute("data-mode");
    });
    expect(await background(root), `${scheme} 지운 뒤`).toBe(expected);
  }
});

test("shadow 호스트에서 data-theme·data-mode 를 지우면 문서의 시트 없이도 시스템 라이트·다크 모두 기본 테마의 값이다", async ({
  page,
  storybook,
}) => {
  // 틀과 감싼 요소는 ShadowFrame 의 표시다. Playwright 의 CSS 위치 지정은 열린 shadow root 안까지 들어간다.
  const host = page.locator("[data-shadow-frame]");
  const wrapper = host.locator("[data-ui-root]");
  for (const scheme of MODES) {
    await page.emulateMedia({ colorScheme: scheme });
    await storybook.open(SAMPLE, {
      theme: OTHER_THEME,
      mode: OPPOSITE[scheme],
      density: "auto",
      shadow: "on",
    });
    // 기대값은 문서의 시트를 끄기 전에 읽는다. 끈 뒤에는 문서의 요소에 쓰임새 토큰이 없다.
    const expected = await defaultBackground(page, scheme);
    // ADR 0026, 측정 tokens/measure.mjs 의 switch.
    await disableDocumentSheets(page);
    expect(await background(wrapper), `${scheme} 지우기 전`).not.toBe(expected);
    await host.evaluate((element) => {
      element.removeAttribute("data-theme");
      element.removeAttribute("data-mode");
    });
    expect(await background(wrapper), `${scheme} 지운 뒤`).toBe(expected);
  }
});

// 스토리 테스트는 시스템 모드를 바꾸지 못해(판정 스토리 Matrix 는 라이트에서만 본다) 시스템 다크의 덮기와 shadow 호스트의
// 시스템 모드 짝은 여기서 본다. 기대값은 같은 빌드에서 그 모드를 명시한 탐침이다.
test("시스템 모드의 군청은 문서 뿌리와 shadow 호스트 모두 시스템 라이트·다크마다 주 버튼 묶음이 그 모드를 명시한 군청과 같다", async ({
  page,
  storybook,
}) => {
  const wrapper = page.locator("[data-shadow-frame]").locator("[data-ui-root]");
  const seen: string[] = [];
  for (const scheme of MODES) {
    await page.emulateMedia({ colorScheme: scheme });
    await storybook.open(SAMPLE, {
      theme: OTHER_THEME,
      mode: "system",
      density: "auto",
      shadow: "on",
    });
    const expected = await probeTokens(page, { theme: OTHER_THEME, mode: scheme }, PRIMARY);
    expect(await tokens(page.locator("html"), PRIMARY), `${scheme} 문서 뿌리`).toEqual(expected);
    await disableDocumentSheets(page);
    expect(await tokens(wrapper, PRIMARY), `${scheme} shadow 호스트`).toEqual(expected);
    seen.push(expected.join(" "));
  }
  expect(new Set(seen).size, "라이트와 다크의 주 버튼 묶음이 다르다").toBe(2);
});

// 속성이 없을 때의 밀도는 창의 폭을 따른다. 768px(`wide:` 와 같은 중단점) 이상에서 촘촘, 미만에서 보통이다. 관리 화면
// (데스크톱과 휴대폰)과 `regular` 를 빠뜨린 위젯 호스트의 자리다. 기대값은 같은 빌드에서 그 밀도를 단 탐침이다. 미디어
// 규칙은 촘촘의 값 일곱을 다시 적은 블록이라 일곱을 모두 맞댄다.
const VIEWPORTS = [
  { width: 1280, height: 800, density: "compact" },
  { width: 375, height: 812, density: "regular" },
] as const satisfies readonly { width: number; height: number; density: Density }[];

const DENSITY_VARIABLES = [
  "--body-size",
  "--body-lh",
  "--table-size",
  "--table-lh",
  "--mono-size",
  "--row-h",
  "--control-h",
] as const;

test("data-density 가 없는 문서 뿌리와 shadow 호스트는 창의 폭 1280px 에서 촘촘, 375px 에서 보통의 밀도 변수를 받는다", async ({
  page,
  storybook,
}) => {
  const host = page.locator("[data-shadow-frame]");
  const wrapper = host.locator("[data-ui-root]");
  const seen: string[] = [];
  for (const { width, height, density } of VIEWPORTS) {
    await page.setViewportSize({ width, height });
    await storybook.open(SAMPLE, {
      theme: DEFAULT_THEME,
      mode: "light",
      density: "auto",
      shadow: "on",
    });
    expect(
      [
        await page.locator("html").getAttribute("data-density"),
        await host.getAttribute("data-density"),
      ],
      "밀도 속성이 없다",
    ).toEqual([null, null]);
    const expected = await probeTokens(page, { density }, DENSITY_VARIABLES);
    expect(
      await tokens(page.locator("html"), DENSITY_VARIABLES),
      `${String(width)}px 문서 뿌리`,
    ).toEqual(expected);
    await disableDocumentSheets(page);
    expect(await tokens(wrapper, DENSITY_VARIABLES), `${String(width)}px shadow 호스트`).toEqual(
      expected,
    );
    seen.push(expected.join(" "));
  }
  expect(new Set(seen).size, "촘촘과 보통의 밀도 변수가 다르다").toBe(2);
});

interface Motion {
  readonly story: string;
  /** 테스트 이름에 드는 표시의 이름. */
  readonly what: string;
  readonly target: (page: Page) => Locator;
  /** 줄이기가 없을 때의 animation-name. 줄이기에서는 `none` 이다. */
  readonly animation: string;
}

const SPINNER = (page: Page): Locator => page.locator("[aria-busy=true] svg");

// 움직이는 표시를 그리는 컴포넌트마다 그 상태의 스토리 하나. 불러오는 중인 버튼과 아이콘 버튼의 도는 표시, 값을
// 모르는 진행 표시의 도는 표시(progressbar 의 첫 자식)다. 같은 컴포넌트의 다른 스토리(제출 버튼)는 같은 클래스라 더
// 보지 않는다.
const SPINNERS: readonly Motion[] = [
  { story: "atoms-button--loading", what: "도는 표시", target: SPINNER, animation: "spin" },
  { story: "atoms-iconbutton--loading", what: "도는 표시", target: SPINNER, animation: "spin" },
  {
    story: "atoms-progress--indeterminate",
    what: "값 모름 진행 표시의 도는 표시",
    target: (page) => page.locator("[role=progressbar]:not([aria-valuenow]) > svg"),
    animation: "spin",
  },
];

for (const { story, what, target, animation } of SPINNERS) {
  test(`${story} 의 ${what}가 움직임 줄이기에서 멈추고 줄이기가 없으면 움직인다`, async ({
    page,
    storybook,
  }) => {
    for (const [reducedMotion, name] of [
      ["no-preference", animation],
      ["reduce", "none"],
    ] as const) {
      await page.emulateMedia({ reducedMotion });
      await storybook.open(story, inDefaultTheme("light", "regular"));
      const moving = target(page);
      await expect(moving, reducedMotion).toHaveCount(1);
      expect(
        await moving.evaluate((element) => getComputedStyle(element).animationName),
        reducedMotion,
      ).toBe(name);
    }
  });
}
