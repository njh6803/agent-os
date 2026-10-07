// 사진 비교(design-system 명세의 "사진 비교 게이트", ADR 0026). 판정 스토리를 뺀 패키지의 스토리를 기본 테마(먹)의
// 라이트·다크로 찍어 커밋한 정답 사진과 비교한다(판정 스토리는 storybook.ts 가 뺀다). 새 스토리는 저절로 찍히고, 정답
// 사진이 없으면 실패한다. 정답 사진의 이름은 `<스토리 id>-<모드>.png`, 실제 입력의 상태는 `<스토리 id>-<모드>-<상태>.png`
// 다.
import type { Locator, Page } from "@playwright/test";
import { DEFAULT_THEME } from "../src/themes.ts";
import {
  MODES,
  expect,
  muk,
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
async function openInMuk(storybook: Storybook, page: Page, id: string, mode: Mode): Promise<void> {
  await storybook.open(id, muk(mode));
  expect(
    await renderedTheme(page),
    "기본 테마가 아닌 테마를 정한 스토리는 judgment 태그를 단다",
  ).toBe(DEFAULT_THEME);
}

async function renderedTheme(page: Page): Promise<string | undefined> {
  return page.evaluate(() => document.documentElement.dataset["theme"]);
}

async function renderedMode(page: Page): Promise<string | undefined> {
  return page.evaluate(() => document.documentElement.dataset["mode"]);
}

for (const story of photographedStories()) {
  test(`${story.id} 를 먹의 라이트·다크로 찍은 사진이 정답과 같다`, async ({ page, storybook }) => {
    const shot: Mode[] = [];
    for (const mode of MODES) {
      await openInMuk(storybook, page, story.id, mode);
      // 스토리가 globals 로 모드를 정했으면(PrimaryDark 등) 그 값이 URL 의 값을 이겨 그 모드로만 그려진다. 다른 모드를
      // 요청한 차례는 같은 그림이라 찍지 않는다.
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

interface Interaction {
  readonly story: string;
  readonly target: (page: Page) => Locator;
  /** 찍을 상태. 디자인 파일의 상태 표가 그 컴포넌트에 두지 않은 상태는 뺀다. */
  readonly states: readonly State[];
}

const BUTTON: readonly State[] = ["hover", "press", "focus"];
// 글 입력은 디자인 파일의 상태 표에 누름이 없다.
const FIELD: readonly State[] = ["hover", "focus"];

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
  },
  {
    story: "atoms-button--danger",
    target: (page) => page.getByRole("button", { name: "실행 지우기" }),
    states: BUTTON,
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
    states: FIELD,
  },
  {
    story: "molecules-textfield--multi",
    target: (page) => page.getByRole("textbox", { name: "거부 사유" }),
    states: FIELD,
  },
  // 스위치는 켜짐과 꺼짐의 올림·누름이 다르다. 두 스토리 모두 checked 를 넘겨, 누름을 놓아 생긴 click 이 그림을
  // 바꾸지 않는다(그 뒤의 포커스 사진이 같은 상태를 찍는다).
  {
    story: "molecules-switch--off",
    target: (page) => page.getByRole("switch", { name: "결제 환불" }),
    states: BUTTON,
  },
  {
    story: "molecules-switch--on",
    target: (page) => page.getByRole("switch", { name: "주문 조회" }),
    states: BUTTON,
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

for (const { story, target, states } of INTERACTIONS) {
  const names = states.map((state) => STATE_NAMES[state]).join("·");
  test(`${story} 를 실제 입력의 ${names}로 찍은 사진이 먹의 라이트·다크 모두 정답과 같다`, async ({
    page,
    storybook,
  }) => {
    for (const mode of MODES) {
      await openInMuk(storybook, page, story, mode);
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
  });
}
