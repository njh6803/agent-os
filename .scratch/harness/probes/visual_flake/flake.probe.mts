// 사진 비교 흔들림 프로브(harness 티켓 016)의 컨테이너 쪽 시험. run.mjs 가 띄운다. 흔들린 세 사진의 스토리를 사진
// 비교(web/packages/ui/visual/stories.visual.ts)와 같은 차례로 열고 상태를 걸어 찍은 뒤, 찍은 바이트를 정답 사진
// (/baseline, run.mjs 가 --baseline 커밋에서 꺼낸 것)과 맞대어 같으면 A, 다르면 B 로 가른다. 사진은 모두 /out/shots/ 에
// 남기고(same_bytes.mjs 가 CI 의 그림과 맞댄다) B 는 갈린 픽셀을 센다. 시험 하나가 한 줄을 /out/results.jsonl 에
// 덧붙인다.
//
// 환경 변수: FLAKE_REPS(되풀이 수), FLAKE_CASES(alert,textfield,switch 가운데), FLAKE_CONDITIONS(갈래, 아래 CONDITIONS),
// FLAKE_WAIT_MS(wait 갈래가 찍기 전에 기다리는 밀리초).
import { appendFileSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { createHash } from "node:crypto";
// 타입만 들이고 실행 때는 지워진다(/probe 에는 node_modules 가 없다).
import type { Locator, Page } from "@playwright/test";
import { DENSITIES, type Density } from "/web/packages/ui/src/themes.ts";
import { MODES, expect, inDefaultTheme, test, type Mode } from "/web/packages/ui/visual/storybook.ts";
import { differingPixels, readPng } from "./png.mjs";

const OUT = "/out";
const SNAPSHOTS = "/baseline";
const REPS = Number(process.env["FLAKE_REPS"] ?? "10");
const WAIT_MS = Number(process.env["FLAKE_WAIT_MS"] ?? "1500");

type State = "hover" | "focus";
interface Case {
  readonly story: string;
  /** 없으면 상태 없이 스토리만 찍는다(stories.visual.ts 의 첫 루프). */
  readonly target?: (page: Page) => Locator;
  readonly states: readonly State[];
}

const CASES: Record<string, Case> = {
  alert: { story: "molecules-alert--showcase-run-failed", states: [] },
  textfield: {
    story: "molecules-textfield--multi",
    target: (page) => page.getByRole("textbox", { name: "거부 사유" }),
    states: ["hover", "focus"],
  },
  switch: {
    story: "molecules-switch--off",
    target: (page) => page.getByRole("switch", { name: "결제 환불" }),
    states: ["hover", "focus"],
  },
};

interface Condition {
  /** 스토리를 열기 전에 한 번. */
  readonly setup?: (page: Page) => Promise<void>;
  /** 사진마다 찍기 바로 전에. */
  readonly before?: (page: Page) => Promise<void>;
  /** 있으면 상태를 건 때부터 이 밀리초마다 한 장씩 찍는다(한 페이지에서 차례로). 없으면 한 장이다. */
  readonly offsets?: readonly number[];
}

/**
 * 갈래. now 는 사진 비교와 같이 곧바로 찍는다. wait 는 찍기 전에 FLAKE_WAIT_MS 를 기다린다(찍는 때의 가설). wide 는
 * 창을 처음부터 정답 사진의 폭(알림 496px)으로 열어, 전체 페이지 사진이 창 밖의 띠를 찍는 순간에 처음 그리게 되는
 * 일을 없앤다(창 밖 띠의 가설). wide 는 폭이 창을 따르지 않는 알림에만 뜻이 있다. wide-wait 은 둘을 겹친다.
 * timeline 은 한 페이지에서 차례로 찍어, 앞의 찍기가 뒤의 그림을 바꾸는지와 A 에서 B 로 넘어가는 때를 본다.
 * wide-timeline 은 wide 의 창으로 timeline 을 찍어, 창 밖 띠를 없앤 채로도 시간이 지나면 B 로 넘어가는지 본다.
 * raf2 는 찍기 전에 애니메이션 프레임 둘을 기다린다. 그리기 한 바퀴가 끝나기를 기다리는 흔한 처방이 A·B 를 가르는지 본다.
 */
const CONDITIONS: Record<string, Condition> = {
  now: {},
  wait: {
    before: async (page) => {
      await page.waitForTimeout(WAIT_MS);
    },
  },
  wide: {
    setup: async (page) => {
      await page.setViewportSize({ width: 496, height: 320 });
    },
  },
  "wide-wait": {
    setup: async (page) => {
      await page.setViewportSize({ width: 496, height: 320 });
    },
    before: async (page) => {
      await page.waitForTimeout(WAIT_MS);
    },
  },
  timeline: { offsets: [0, 100, 200, 400, 800, 1600, 3200] },
  "wide-timeline": {
    setup: async (page) => {
      await page.setViewportSize({ width: 496, height: 320 });
    },
    offsets: [0, 50, 100, 200, 400, 800],
  },
  raf2: {
    before: async (page) => {
      await page.evaluate(
        () =>
          new Promise<void>((resolve) => {
            requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
          }),
      );
    },
  },
};

const pick = <T,>(name: string, all: Record<string, T>): string[] => {
  const wanted = (process.env[name] ?? Object.keys(all).join(",")).split(",").filter(Boolean);
  for (const key of wanted) {
    if (!(key in all)) throw new Error(`${name} 에 모르는 값: ${key}`);
  }
  return wanted;
};
const caseNames = pick("FLAKE_CASES", CASES);
const conditionNames = pick("FLAKE_CONDITIONS", CONDITIONS);

const TURNS = MODES.flatMap((mode) =>
  DENSITIES.map((density) => ({ mode, density, name: `${mode}-${density}` })),
);

async function renderedAs(page: Page, mode: Mode, density: Density): Promise<boolean> {
  const rendered = await page.evaluate(() => ({
    mode: document.documentElement.dataset["mode"],
    density: document.documentElement.dataset["density"],
  }));
  return rendered.mode === mode && rendered.density === density;
}

interface Shot {
  readonly name: string;
  /** offsets 갈래에서 상태를 건 때부터 찍기를 시작한 때까지의 밀리초(재었다). 한 장 갈래는 없다. */
  readonly at?: number;
  /** offsets 갈래에서 이 사진의 예정 밀리초(offsets 의 값). 한 장 갈래는 없다. */
  readonly step?: number;
  readonly verdict: "A" | "B";
  readonly sha256: string;
  readonly pixels: number;
  readonly spots: readonly string[];
}

async function capture(page: Page, name: string, tag: string, at?: number): Promise<Shot> {
  // toHaveScreenshot 의 기본값과 같다(움직임 끄기, 캐럿 숨기기). 배율은 창이 1 이라 갈리지 않는다.
  const buffer = await page.screenshot({ fullPage: true, animations: "disabled", caret: "hide" });
  const expected = readFileSync(`${SNAPSHOTS}/${name}.png`);
  const sha256 = createHash("sha256").update(buffer).digest("hex");
  mkdirSync(`${OUT}/shots`, { recursive: true });
  const path = `${OUT}/shots/${tag}-${name}${at === undefined ? "" : `-at${at}`}.png`;
  writeFileSync(path, buffer);
  if (buffer.equals(expected)) {
    return { name, at, verdict: "A", sha256, pixels: 0, spots: [] };
  }
  const found = differingPixels(readPng(`${SNAPSHOTS}/${name}.png`), readPng(path));
  return {
    name,
    at,
    verdict: "B",
    sha256,
    pixels: found.length,
    spots: found.slice(0, 40).map(({ x, y }) => `${x},${y}`),
  };
}

async function shoot(page: Page, name: string, condition: string, tag: string): Promise<Shot[]> {
  const chosen = CONDITIONS[condition];
  await chosen?.before?.(page);
  if (chosen?.offsets === undefined) {
    return [await capture(page, name, tag)];
  }
  const start = Date.now();
  const shots: Shot[] = [];
  for (const offset of chosen.offsets) {
    const left = start + offset - Date.now();
    if (left > 0) await page.waitForTimeout(left);
    shots.push({ ...(await capture(page, name, tag, Date.now() - start)), step: offset });
  }
  return shots;
}

test("메타: 브라우저 판과 GPU 상태", async ({ browser }) => {
  const session = await browser.newBrowserCDPSession();
  const info = await session.send("SystemInfo.getInfo");
  writeFileSync(
    `${OUT}/meta.json`,
    JSON.stringify(
      {
        version: browser.version(),
        featureStatus: info.gpu.featureStatus,
        devices: info.gpu.devices,
        driverBugWorkarounds: info.gpu.driverBugWorkarounds,
        commandLine: info.commandLine,
      },
      null,
      2,
    ),
  );
});

for (let rep = 1; rep <= REPS; rep += 1) {
  for (const caseName of caseNames) {
    for (const condition of conditionNames) {
      const chosen = CASES[caseName];
      if (chosen === undefined) throw new Error(`모르는 사례: ${caseName}`);
      const { story, target, states } = chosen;
      test(`${caseName} ${condition} ${rep}`, async ({ page, storybook }) => {
        const tag = `${caseName}-${condition}-${rep}`;
        const shots: Shot[] = [];
        await CONDITIONS[condition]?.setup?.(page);
        for (const { mode, density, name } of TURNS) {
          await storybook.open(story, inDefaultTheme(mode, density));
          if (!(await renderedAs(page, mode, density))) continue;
          if (target === undefined) {
            shots.push(...(await shoot(page, `${story}-${name}`, condition, tag)));
            continue;
          }
          const element = target(page);
          if (states.includes("hover")) {
            await element.hover();
            expect(await element.evaluate((e) => e.matches(":hover")), "올림").toBe(true);
            shots.push(...(await shoot(page, `${story}-${name}-hover`, condition, tag)));
          }
          if (states.includes("focus")) {
            await page.mouse.click(1, 1);
            await page.keyboard.press("Tab");
            await expect(element).toBeFocused();
            expect(await element.evaluate((e) => e.matches(":focus-visible")), "포커스").toBe(true);
            shots.push(...(await shoot(page, `${story}-${name}-focus`, condition, tag)));
          }
        }
        // 측정의 표지: 이 줄은 상태를 확인하고 찍은 사진이 하나 이상일 때만 쓰인다. 줄이 없는 시험은 측정 아님이다.
        expect(shots.length, "찍은 사진").toBeGreaterThan(0);
        appendFileSync(
          `${OUT}/results.jsonl`,
          `${JSON.stringify({ case: caseName, condition, rep, shots })}\n`,
        );
      });
    }
  }
}
