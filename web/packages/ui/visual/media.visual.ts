// 미디어 특성(prefers-color-scheme, prefers-reduced-motion)을 바꿔 가며 같은 정적 빌드를 연다. 사진은 Playwright 가
// 움직임을 멈춰 찍어 움직임 줄이기를 가르지 못한다(design-system 명세의 사진 비교 게이트). 시스템 모드와 속성 없는 문서·
// 호스트는 명세의 스토리 13 이다. 쓰임새 토큰의 기대값은 디자인 파일이 아니라 같은 빌드에서 `data-theme="muk"` 과
// `data-mode` 를 단 요소로 읽는다. 선례는 측정 tokens/measure.mjs 의 switch 와 motion 이다.
import type { Locator, Page } from "@playwright/test";
import { MODES, expect, muk, test, type Mode } from "./storybook.ts";

// 속성을 지우는 사례가 그리는 표본. 판정 스토리가 아니고 globals 로 테마·모드를 정하지 않은 스토리다.
const SAMPLE = "atoms-button--primary";

const OPPOSITE: Readonly<Record<Mode, Mode>> = { light: "dark", dark: "light" };

function background(target: Locator): Promise<string> {
  return target.evaluate((element) => getComputedStyle(element).getPropertyValue("--bg").trim());
}

/** 문서에 `data-theme="muk"` 과 `data-mode` 를 단 요소를 하나 두고 그 `--bg` 를 읽은 뒤 걷는다. */
async function mukBackground(page: Page, mode: Mode): Promise<string> {
  await page.evaluate((value) => {
    const probe = document.createElement("div");
    probe.dataset["visualProbe"] = "";
    probe.dataset["theme"] = "muk";
    probe.dataset["mode"] = value;
    document.body.append(probe);
  }, mode);
  const probe = page.locator("[data-visual-probe]");
  const value = await background(probe);
  await probe.evaluate((element) => {
    element.remove();
  });
  return value;
}

test("시스템 모드에서 문서 뿌리의 --bg 가 시스템의 라이트·다크를 따라 먹의 그 모드 값이다", async ({
  page,
  storybook,
}) => {
  const seen: string[] = [];
  for (const scheme of MODES) {
    await page.emulateMedia({ colorScheme: scheme });
    await storybook.open(SAMPLE, { ...muk(scheme), mode: "system" });
    const expected = await mukBackground(page, scheme);
    expect(await background(page.locator("html")), scheme).toBe(expected);
    seen.push(expected);
  }
  expect(new Set(seen).size, "라이트와 다크의 --bg 가 다르다").toBe(2);
});

test("문서 뿌리에서 데코레이터가 단 data-theme·data-mode 를 지우면 시스템 라이트·다크 모두 먹의 값이다", async ({
  page,
  storybook,
}) => {
  const root = page.locator("html");
  for (const scheme of MODES) {
    await page.emulateMedia({ colorScheme: scheme });
    // 지우기 전의 값이 기대값과 달라야 지운 효과를 본다. 청록에 시스템과 반대 모드를 단다.
    await storybook.open(SAMPLE, { theme: "cheongnok", mode: OPPOSITE[scheme], shadow: "off" });
    const expected = await mukBackground(page, scheme);
    expect(await background(root), `${scheme} 지우기 전`).not.toBe(expected);
    await root.evaluate((element) => {
      element.removeAttribute("data-theme");
      element.removeAttribute("data-mode");
    });
    expect(await background(root), `${scheme} 지운 뒤`).toBe(expected);
  }
});

test("shadow 호스트에서 data-theme·data-mode 를 지우면 문서의 시트 없이도 시스템 라이트·다크 모두 먹의 값이다", async ({
  page,
  storybook,
}) => {
  // 틀과 감싼 요소는 ShadowFrame 의 표시다. Playwright 의 CSS 위치 지정은 열린 shadow root 안까지 들어간다.
  const host = page.locator("[data-shadow-frame]");
  const wrapper = host.locator("[data-ui-root]");
  for (const scheme of MODES) {
    await page.emulateMedia({ colorScheme: scheme });
    await storybook.open(SAMPLE, { theme: "cheongnok", mode: OPPOSITE[scheme], shadow: "on" });
    // 기대값은 문서의 시트를 끄기 전에 읽는다. 끈 뒤에는 문서의 요소에 쓰임새 토큰이 없다.
    const expected = await mukBackground(page, scheme);
    // 미리보기는 디자인 토큰 CSS 를 문서에 전역으로 싣는다. shadow 안의 값이 shadow 의 시트에서만 오는지 보려고 문서의
    // 시트를 모두 끈다(ADR 0026, 측정 tokens/measure.mjs 의 switch).
    await page.evaluate(() => {
      for (const sheet of document.styleSheets) {
        sheet.disabled = true;
      }
    });
    expect(await background(wrapper), `${scheme} 지우기 전`).not.toBe(expected);
    await host.evaluate((element) => {
      element.removeAttribute("data-theme");
      element.removeAttribute("data-mode");
    });
    expect(await background(wrapper), `${scheme} 지운 뒤`).toBe(expected);
  }
});

// 불러오는 중인 컴포넌트의 스토리와 그 도는 표시. 값 모름 진행 막대는 그것을 들이는 티켓이 여기 더한다.
const SPINNERS = ["atoms-button--loading", "atoms-iconbutton--loading"] as const;

for (const story of SPINNERS) {
  test(`${story} 의 도는 표시가 움직임 줄이기에서 멈추고 줄이기가 없으면 돈다`, async ({
    page,
    storybook,
  }) => {
    for (const [reducedMotion, name] of [
      ["no-preference", "spin"],
      ["reduce", "none"],
    ] as const) {
      await page.emulateMedia({ reducedMotion });
      await storybook.open(story, muk("light"));
      const spinner = page.locator("[aria-busy=true] svg");
      await expect(spinner, reducedMotion).toHaveCount(1);
      expect(
        await spinner.evaluate((element) => getComputedStyle(element).animationName),
        reducedMotion,
      ).toBe(name);
    }
  });
}
