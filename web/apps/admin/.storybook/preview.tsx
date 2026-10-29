// 관리 화면의 미리보기. 앱의 전역 CSS(디자인 토큰 CSS 를 들인 것)와 글꼴 CSS 를 싣고, 패키지의 미리보기 본체에 그 전역
// CSS 를 넘긴다(위젯의 .storybook/preview.tsx 와 같은 모양). 밀도 globals 는 본체의 기본 "auto" 그대로라 문서 뿌리에
// 밀도를 달지 않는다. 관리 화면은 폭이 밀도를 고른다(admin-style 명세 "디자인 시스템 들이기").
//
// 본체에 더하는 것은 다섯이다.
// - viewport 항목 둘(viewports.ts). 스토리 테스트 프로젝트가 `initialGlobals` 로 고른다. 프로젝트의 `test.browser.viewport`
//   는 스토리마다 1200×900 으로 덮였다(.scratch/admin-style/probes/storybook_viewport.mjs).
// - 스토리를 이름 없는 컨테이너(`@container`)로 두른다. 틀(AdminFrame)의 본문 칸과 같은 선언이라, 틀 없이 그리는
//   organisms 의 스토리에서도 컨테이너 기준 폭(`@split:`)의 갈래가 선다(admin-style 티켓 04). 클래스는 틀이 써서
//   앱 CSS 에 이미 있다.
// - 스토리마다 그리기 전에 localStorage 를 비운다. 비우지 않으면 앞 스토리가 쓴 값을 다음 스토리가 봤다(같은 프로브).
// - afterEach 가 문서의 가로 스크롤을 본다. 두 폭 모두 보지만 걸리는 것은 좁은 폭이다.
// - axe 의 target-size(포인터 목표 24px)를 켠다. axe-core 4.14.0 은 그 규칙을 기본으로 끈다(설치본 axe.min.js 의 규칙
//   정의가 `enabled:!1`).
import "../styles/admin.css";
import "@agent-os/ui/fonts.css";
import { A11Y_PARAMETERS, storyPreview } from "@agent-os/ui/storybook";
import type { Decorator, Preview } from "@storybook/react-vite";
import css from "../styles/admin.css?inline";
import { VIEWPORTS, type ViewportKey } from "./viewports";

const base = storyPreview(css);

/** Storybook 의 viewport 항목 하나. */
function viewportOption(key: ViewportKey, name: string, type: "desktop" | "mobile") {
  const { width, height } = VIEWPORTS[key];
  return {
    name: `${name} ${String(width)}`,
    styles: { width: `${String(width)}px`, height: `${String(height)}px` },
    type,
  };
}

/** 본체의 훅(하나, 여럿, 없음) 뒤에 하나를 더한다. */
function appended<T extends (...args: never[]) => unknown>(
  inherited: T | T[] | undefined,
  added: T,
): T[] {
  if (inherited === undefined) {
    return [added];
  }
  return typeof inherited === "function" ? [inherited, added] : [...inherited, added];
}

const withContainer: Decorator = (Story) => (
  <div className="@container">
    <Story />
  </div>
);

function clearLocalStorage(): void {
  localStorage.clear();
}

/** 문서가 창 폭을 넘어 가로로 밀리면 던진다. */
function noHorizontalScroll(): void {
  const { scrollWidth, clientWidth } = document.documentElement;
  if (scrollWidth > clientWidth) {
    throw new Error(
      `문서가 창 폭 ${String(clientWidth)}px 을 넘어 가로로 밀린다(${String(scrollWidth)}px)`,
    );
  }
}

const preview = {
  ...base,
  parameters: {
    ...base.parameters,
    // 본체의 a11y 를 펼치고 규칙 하나를 더 켠다. 본체의 parameters 는 Storybook 의 `Parameters`(값이 any)라 읽어 펼치지
    // 않고, 본체가 내보내는 상수를 쓴다.
    a11y: { ...A11Y_PARAMETERS, config: { rules: [{ id: "target-size", enabled: true }] } },
    viewport: {
      options: {
        wide: viewportOption("wide", "넓은 폭", "desktop"),
        narrow: viewportOption("narrow", "좁은 폭", "mobile"),
      },
    },
  },
  decorators: appended(base.decorators, withContainer),
  beforeEach: appended(base.beforeEach, clearLocalStorage),
  afterEach: appended(base.afterEach, noHorizontalScroll),
} satisfies Preview;

export default preview;
