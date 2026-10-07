// 미리보기 설정의 본체(`@agent-os/ui/storybook`). 패키지의 `.storybook/preview.tsx` 가 디자인 토큰 CSS 와 글꼴 CSS 를
// 실은 뒤 이것을 부른다. 앱의 Storybook 도 자기 CSS 를 실은 뒤 같은 것을 부른다(ADR 0026 의 2026-10-07 이력).
// - globals 셋: theme(테마 목록, 기본 먹), mode(system 기본 | light | dark. system 이면 속성을 두지 않는다),
//   shadow(off | on | raw). 데코레이터가 문서 뿌리나 shadow 호스트에 단다. globals 는 `Record<string, unknown>` 으로
//   받아 비교로 좁힌다(원칙 III. Storybook 의 Globals 는 값이 any 다).
// - axe(addon-a11y)의 위반은 스토리 테스트를 실패시킨다.
// - afterEach 가 모든 스토리의 그림에서 규칙 없는 클래스와 임의값을 찾아 있으면 실패시킨다. 그래서 컴포넌트를 더하는
//   티켓은 판정 스토리를 고치지 않아도 판정된다. 판정하는 것은 문서에 그린 그림이다(shadow 가 off 인 기본 globals).
// - 태그 둘. `judgment` 는 판정 스토리(디자인 토큰의 판정과 그 음성 사례, 기본 테마가 아닌 테마에서 값을 재는 스토리)이고
//   사진 비교(`visual/`)가 찍지 않는다. 사진은 기본 테마만 찍는다(ADR 0026 의 2026-10-06 이력).
//   `planted` 는 일부러 규칙 없는 클래스나 기준 미달 짝을 그리는 음성 사례이고 afterEach 의 판정에서 빠진다(axe 는 그
//   스토리가 끈다). 스토리 파일의 `tags` 에는 글자 그대로 적는다. Storybook 의 색인이 정적으로 읽어 상수를 받지 않는다.
import type { Decorator, Preview } from "@storybook/react-vite";
import { arbitraryClasses, classesWithoutRules, sheetsDefining } from "../testing";
import { DEFAULT_THEME, THEMES, type Mode, type ThemeKey } from "../themes";
import { SHADOW_MODES, ShadowFrame, type ShadowMode } from "./ShadowFrame";

export const PLANTED_TAG = "planted";

const MODE_ITEMS = [
  { value: "system", title: "시스템" },
  { value: "light", title: "라이트" },
  { value: "dark", title: "다크" },
] as const;

function themeOf(globals: Record<string, unknown>): ThemeKey {
  return THEMES.find((theme) => theme.key === globals["theme"])?.key ?? DEFAULT_THEME;
}

function modeOf(globals: Record<string, unknown>): Mode | null {
  const value = globals["mode"];
  return value === "light" || value === "dark" ? value : null;
}

function shadowOf(globals: Record<string, unknown>): ShadowMode | null {
  const value = globals["shadow"];
  return SHADOW_MODES.find((mode) => mode === value) ?? null;
}

// lucide-react 가 svg 에 스스로 붙이는 클래스(`lucide`, `lucide-<아이콘 이름>`). React 판은 그것을 끄는 길이 없고
// 규칙도 없다(1.51.0 의 Icon.mjs·buildLucideIconNode.mjs 를 읽었다). 우리가 쓴 클래스가 아니라 판정에서 뺀다.
const LIBRARY_CLASS = /^lucide(?:-[a-z0-9-]+)?$/;

/** 디자인 토큰 CSS 의 시트에서 그린 요소의 class 낱말을 판정한다. 문제가 있으면 그 낱말을 든 오류를 던진다. */
export function judgeClasses(canvas: Element): void {
  const sheets = sheetsDefining("--gray-50", document.styleSheets);
  const problems = [
    ...classesWithoutRules(canvas, sheets)
      .filter((name) => !LIBRARY_CLASS.test(name))
      .map((name) => `규칙 없는 클래스 ${name}`),
    ...arbitraryClasses(canvas).map((name) => `임의값 클래스 ${name}`),
  ];
  if (problems.length > 0) {
    throw new Error(`디자인 토큰에 없는 클래스를 그렸다: ${problems.join(", ")}`);
  }
}

/**
 * 미리보기 주해. `shadowCss` 는 shadow 틀에 넣을 빌드한 CSS(`?inline` 글자)다. 패키지는 디자인 토큰 CSS 를, 앱은
 * 디자인 토큰 CSS 를 `@import` 하고 자기 소스를 `@source` 로 덮은 자기 CSS 를 넘긴다. 디자인 토큰 CSS 만 넘기면 shadow 틀
 * 안에서 앱의 클래스가 규칙을 잃는다.
 */
export function storyPreview(shadowCss: string): Preview {
  const withTheme: Decorator = (Story, context) => {
    const root = document.documentElement;
    root.dataset["theme"] = themeOf(context.globals);
    const mode = modeOf(context.globals);
    if (mode === null) {
      delete root.dataset["mode"];
    } else {
      root.dataset["mode"] = mode;
    }
    return <Story />;
  };

  const withShadowRoot: Decorator = (Story, context) => {
    const shadow = shadowOf(context.globals);
    if (shadow === null) {
      return <Story />;
    }
    return (
      <ShadowFrame
        shadow={shadow}
        css={shadowCss}
        theme={themeOf(context.globals)}
        mode={modeOf(context.globals)}
      >
        <Story />
      </ShadowFrame>
    );
  };

  return {
    parameters: { a11y: { test: "error" } },
    initialGlobals: { theme: DEFAULT_THEME, mode: "system", shadow: "off" },
    globalTypes: {
      theme: {
        description: "테마(data-theme)",
        toolbar: {
          title: "테마",
          items: THEMES.map(({ key, name }) => ({ value: key, title: name })),
          dynamicTitle: true,
        },
      },
      mode: {
        description: "모드(data-mode). 시스템이면 속성을 두지 않는다",
        toolbar: { title: "모드", items: [...MODE_ITEMS], dynamicTitle: true },
      },
      shadow: {
        description:
          "그리는 자리. on 은 보정 시트까지, raw 는 디자인 토큰 CSS 만 shadow root 에 넣는다",
        toolbar: { title: "shadow", items: ["off", ...SHADOW_MODES], dynamicTitle: true },
      },
    },
    decorators: [withShadowRoot, withTheme],
    afterEach: ({ canvasElement, tags }) => {
      if (!tags.includes(PLANTED_TAG)) {
        judgeClasses(canvasElement);
      }
    },
  } satisfies Preview;
}
