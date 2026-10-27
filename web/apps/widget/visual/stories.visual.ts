// 위젯의 사진 비교. 판정 스토리를 뺀 위젯의 스토리를 기본 테마(녹청)의 라이트·다크로 찍어 커밋한 정답 사진과 비교한다.
// 밀도는 위젯이 문서 뿌리에 다는 보통 하나다. 정답 사진의 이름은 `<스토리 id>-<모드>.png` 다. 스토리가 globals 로
// 모드를 정했으면 그 모드만 찍는다. 정적 빌드를 여는 길은 디자인 시스템 패키지와 나눠 쓴다(`@agent-os/ui/visual`).
//
// 컴포넌트의 올림·누름·포커스는 디자인 시스템 패키지의 사진 비교가 찍는다. 여기서는 위젯이 그것들을 엮은 화면을 찍는다.
import { join } from "node:path";
import { test as base, expect, type Page } from "@playwright/test";
import {
  MODES,
  inDefaultTheme,
  missingBrowserArgs,
  photographedStories,
  storybookTest,
  type Globals,
} from "@agent-os/ui/visual";

const SITE = join(import.meta.dirname, "..", "storybook-static");
const test = storybookTest(base, SITE);

/** 요청한 globals 로 그려졌는지. 스토리가 globals 로 모드를 정했으면 그 값이 URL 의 값을 이긴다. */
async function renderedAs(page: Page, globals: Globals): Promise<boolean> {
  const rendered = await page.evaluate(() => {
    const { theme, mode, density } = document.documentElement.dataset;
    return { theme, mode, density };
  });
  expect(rendered.theme, "기본 테마가 아닌 테마를 정한 스토리는 judgment 태그를 단다").toBe(
    globals.theme,
  );
  return rendered.mode === globals.mode && rendered.density === globals.density;
}

for (const story of photographedStories(SITE)) {
  test(`${story.id} 를 기본 테마의 그려진 모드마다 찍은 사진이 정답과 같다`, async ({
    page,
    storybook,
  }) => {
    const shot: string[] = [];
    for (const mode of MODES) {
      const globals = inDefaultTheme(mode, "regular");
      await storybook.open(story.id, globals);
      if (!(await renderedAs(page, globals))) {
        continue;
      }
      await expect(page).toHaveScreenshot(`${story.id}-${mode}.png`, { fullPage: true });
      shot.push(mode);
    }
    expect(shot, "찍은 모드").not.toEqual([]);
  });
}

// 화면의 사진은 이 PC 에서 인자를 빼도 정답과 맞아, 설정이 `BROWSER_ARGS` 를 넘기는지는 이 시험이 본다(`@agent-os/ui/visual`
// 의 주석).
test("브라우저가 사진 비교의 실행 인자를 모두 받고 떠 있다", async ({ browser }) => {
  expect(await missingBrowserArgs(browser)).toEqual([]);
});

// 대화의 진행 표시(값 모름)는 디자인 시스템의 도는 표시다. 움직임 줄이기는 그 패키지의 미디어 특성 테스트가 부품
// 하나로 재고, 여기서는 위젯이 엮은 자리에서도 그 설정이 닿는지 본다(web-widget 티켓 05 의 접근성).
test("대화의 진행 표시가 움직임 줄이기에서 멈추고 줄이기가 없으면 돈다", async ({
  page,
  storybook,
}) => {
  for (const [reducedMotion, name] of [
    ["no-preference", "spin"],
    ["reduce", "none"],
  ] as const) {
    await page.emulateMedia({ reducedMotion });
    await storybook.open("organisms-conversation--running", inDefaultTheme("light", "regular"));
    const spinner = page.locator("[role=progressbar]:not([aria-valuenow]) > svg");
    await expect(spinner, reducedMotion).toHaveCount(1);
    expect(
      await spinner.evaluate((element) => getComputedStyle(element).animationName),
      reducedMotion,
    ).toBe(name);
  }
});
