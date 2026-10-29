// 빌드한 관리 화면이 디자인 시스템의 글꼴을 싣는다(admin-style 티켓 03). 플래그 없는 `next build`(Turbopack)가 글꼴 CSS 의
// `@font-face` 를 내고 woff2 를 풀었다는 것은 측정(.scratch/admin-style/probes/next_fonts.mjs)뿐이었다. 그것을 남는 시험으로
// 둔다. 실제 next start 를 지나고, 준비는 stack.ts 다. 글꼴이 그려지는지(모양)는 사진 비교가 Storybook 에서 본다.

import { expect, test } from "@playwright/test";
import { stack } from "./env";

const FAMILIES = ["Noto Sans KR", "Noto Sans Mono"];

test("빌드한 문서에 두 글꼴의 @font-face 가 있고 가족마다 woff2 하나를 200 으로 받는다", async ({
  page,
}) => {
  await page.goto(stack().adminUrl);
  await expect(page.getByLabel("관리 토큰", { exact: true })).toBeVisible();

  // 문서의 시트에서 가족마다 처음 만난 woff2 주소(시트 기준으로 푼 것)와 `@font-face` 수를 읽는다.
  const found = await page.evaluate((families) => {
    const faces: Record<string, { count: number; woff2: string | null }> = {};
    for (const family of families) {
      faces[family] = { count: 0, woff2: null };
    }
    for (const sheet of Array.from(document.styleSheets)) {
      for (const rule of Array.from(sheet.cssRules)) {
        if (!(rule instanceof CSSFontFaceRule)) {
          continue;
        }
        const family = rule.style.getPropertyValue("font-family").replace(/^["']|["']$/g, "");
        const face = faces[family];
        if (face === undefined) {
          continue;
        }
        face.count += 1;
        const url = /url\(["']?([^"')]+\.woff2)["']?\)/.exec(rule.style.getPropertyValue("src"));
        if (face.woff2 === null && url?.[1] !== undefined) {
          face.woff2 = new URL(url[1], sheet.href ?? location.href).href;
        }
      }
    }
    return faces;
  }, FAMILIES);

  for (const family of FAMILIES) {
    const face = found[family];
    expect(face?.count, `${family} 의 @font-face`).toBeGreaterThan(0);
    const woff2 = face?.woff2 ?? null;
    expect(woff2, `${family} 의 woff2 주소`).not.toBeNull();
    if (woff2 !== null) {
      const response = await page.request.get(woff2);
      expect(response.status(), `${family} 의 ${woff2}`).toBe(200);
    }
  }
});
