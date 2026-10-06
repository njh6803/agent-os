// 디자인 토큰의 판정을 스토리 테스트로 돈다(프로브 표본). 명세가 고른 이음매(스토리 테스트 하나)에서 판정 함수가
// 타입 검사와 실행을 지나는지, 그리고 무엇을 잡는지 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect } from "storybook/test";
import { BUTTON_SIZES, BUTTON_VARIANTS, Button } from "../components/atoms/Button";
import { Planted } from "../components/atoms/Planted";
import {
  arbitraryClasses,
  classesWithoutRules,
  contrastRatio,
  sheetsDefining,
  undefinedCustomProperties,
} from "../testing/checks";
import { CONTRAST_PAIRS, EXPECTED, FONT_FACES, MODES, SEMANTIC, THEMES } from "./design-tokens";

const meta = { title: "probe/Tokens" } satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

function designSheets(): CSSStyleSheet[] {
  return sheetsDefining("--gray-50", document.styleSheets);
}

/** 열 벌(테마 다섯 × 모드 둘)마다 쓰임새 토큰의 계산값이 디자인 파일의 값과 같고, 짝의 명암비가 기준을 넘는다. */
export const Matrix: Story = {
  render: () => (
    <div data-probe="matrix" className="bg-bg p-4 text-text">
      테마 표
    </div>
  ),
  play: async ({ canvasElement }) => {
    const target = canvasElement.querySelector("[data-probe=matrix]");
    if (!(target instanceof HTMLElement)) {
      throw new Error("표본이 없다");
    }
    const mismatches: string[] = [];
    const failures: string[] = [];
    for (const theme of THEMES) {
      for (const mode of MODES) {
        target.dataset["theme"] = theme;
        target.dataset["mode"] = mode;
        const style = getComputedStyle(target);
        const value = (name: string): string =>
          style.getPropertyValue(`--${name}`).trim().toUpperCase();
        for (const name of SEMANTIC) {
          const expected = EXPECTED[theme][mode][name];
          if (value(name) !== expected) {
            mismatches.push(`${theme}/${mode} --${name} ${value(name)} != ${expected}`);
          }
        }
        for (const [foreground, background, minimum] of CONTRAST_PAIRS) {
          const ratio = contrastRatio(value(foreground), value(background));
          if (ratio < minimum) {
            failures.push(`${theme}/${mode} ${foreground}/${background} ${ratio.toFixed(2)}`);
          }
        }
      }
    }
    await expect(mismatches).toEqual([]);
    await expect(failures).toEqual([]);
  },
};

/** 표본 컴포넌트가 쓴 클래스는 모두 규칙이 있다. */
export const Classes: Story = {
  render: () => (
    <div className="flex flex-col gap-2">
      {BUTTON_VARIANTS.map((variant) =>
        BUTTON_SIZES.map((size) => (
          <Button key={`${variant}-${size}`} variant={variant} size={size}>
            {`${variant} ${size}`}
          </Button>
        )),
      )}
      <Button disabled>쓸 수 없음</Button>
    </div>
  ),
  play: async ({ canvasElement }) => {
    await expect(classesWithoutRules(canvasElement, designSheets())).toEqual([]);
    await expect(arbitraryClasses(canvasElement)).toEqual([]);
  },
};

/** 심은 클래스를 판정 함수가 잡는다. 기대값이 이 프로브의 측정 결과다. */
export const PlantedIsCaught: Story = {
  render: () => <Planted />,
  parameters: { a11y: { test: "off" } },
  play: async ({ canvasElement }) => {
    await expect(classesWithoutRules(canvasElement, designSheets())).toEqual([
      "animate-pulse",
      "bg-gray-500",
      "font-bold",
      "p-5",
      "rounded",
      "shadow",
      "text-base",
      "text-red-500",
      "w-64",
    ]);
    await expect(arbitraryClasses(canvasElement)).toEqual(["bg-[var(--nope)]", "p-[13px]"]);
    await expect(undefinedCustomProperties(designSheets())).toEqual(["--nope"]);
  },
};

/** 기준 폭 둘: 위젯은 자리의 폭(@wide: 컨테이너 360px), 관리 화면은 창의 폭(wide: 미디어 768px). */
export const Responsive: Story = {
  render: () => (
    <div data-probe="container" className="@container" style={{ width: 320 }}>
      <div data-probe="row" className="flex flex-col gap-2 @wide:flex-row wide:gap-4">
        <span>거부</span>
        <span>승인</span>
      </div>
    </div>
  ),
  play: async ({ canvasElement }) => {
    const container = canvasElement.querySelector("[data-probe=container]");
    const row = canvasElement.querySelector("[data-probe=row]");
    if (!(container instanceof HTMLElement) || !(row instanceof HTMLElement)) {
      throw new Error("표본이 없다");
    }
    const directions: string[] = [];
    for (const width of [359, 360, 400]) {
      container.style.width = `${String(width)}px`;
      directions.push(`${String(width)} ${getComputedStyle(row).flexDirection}`);
    }
    await expect(directions).toEqual(["359 column", "360 row", "400 row"]);
    const conditions = new Set<string>();
    const visit = (list: CSSRuleList): void => {
      for (const rule of list) {
        if (rule instanceof CSSMediaRule || rule instanceof CSSContainerRule) {
          conditions.add(rule.conditionText);
        }
        if (rule instanceof CSSGroupingRule || rule instanceof CSSStyleRule) {
          visit(rule.cssRules);
        }
      }
    };
    for (const sheet of designSheets()) {
      visit(sheet.cssRules);
    }
    await expect([...conditions].filter((text) => text.includes("px")).sort()).toEqual([
      "(width >= 360px)",
      "(width >= 768px)",
    ]);
  },
};

/** 움직임 디자인 토큰 둘. measure.mjs 가 움직임 줄이기 있고 없을 때의 animation-name 을 잰다. */
export const Motion: Story = {
  render: () => (
    <div className="flex flex-col gap-4 bg-bg p-4 text-text">
      <span
        data-probe="spinner"
        className="inline-block size-icon-m animate-spin rounded-full border-2 border-accent motion-reduce:animate-none"
      />
      <div className="relative h-progress overflow-hidden rounded-full bg-tint">
        <span
          data-probe="bar"
          className="absolute inset-y-0 w-1/3 animate-progress rounded-full bg-accent motion-reduce:animate-none"
        />
      </div>
    </div>
  ),
  play: async ({ canvasElement }) => {
    await expect(classesWithoutRules(canvasElement, designSheets())).toEqual([]);
  },
};

/** measure.mjs 가 정적 빌드에서 계산값을 읽는 표본. 테마와 모드는 globals 가 문서 뿌리나 shadow 호스트에 단다. */
export const Sample: Story = {
  render: () => (
    <div data-probe="sample" className="bg-bg p-4 text-text">
      표본
    </div>
  ),
};

/** measure.mjs 가 테마마다 받는 글꼴 파일과 바이트를 재는 표본. 위젯 대화의 문장 둘과 도구 이름. */
export const KoreanSample: Story = {
  render: () => (
    <div className="bg-bg p-4 text-text">
      <p className="font-sans text-body">승인을 기다리고 있습니다. 허가하거나 거부해 주세요.</p>
      <p className="font-sans text-body font-strong">실행이 실패했습니다.</p>
      <p className="font-mono text-code font-mid">payments.refund</p>
    </div>
  ),
};

/** 테마의 글꼴이 패키지에서 실제로 받아진다(url() 이 풀린다). */
export const Fonts: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      {THEMES.map((theme) => (
        <div key={theme} data-theme={theme} className="bg-bg p-4 text-text">
          <p className="font-sans text-body">승인을 기다리고 있습니다.</p>
          <p className="font-sans text-body font-mid">허가하거나 거부해 주세요.</p>
          <p className="font-sans text-body font-strong">실행이 실패했습니다.</p>
          <p className="font-mono text-code">payments.refund {"{ count: 52 }"}</p>
        </div>
      ))}
    </div>
  ),
  play: async () => {
    const results: string[] = [];
    for (const [family, weight, sample] of FONT_FACES) {
      const faces = await document.fonts.load(`${String(weight)} 16px "${family}"`, sample);
      const statuses = [...new Set(faces.map((face) => face.status))].sort().join(",");
      results.push(`${family} ${String(weight)} ${String(faces.length)} ${statuses}`);
    }
    await expect(results.filter((line) => !line.endsWith(" loaded"))).toEqual([]);
  },
};
