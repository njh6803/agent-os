// 디자인 시스템 패키지의 사진 비교가 쓰는 픽스처. 사진(stories.visual.ts), 미디어 특성(media.visual.ts), 정적 빌드의
// 성질(storybook.visual.ts)이 함께 쓴다. 정적 빌드를 여는 길은 위젯과 나눠 쓰는 `./index.ts`(`@agent-os/ui/visual`)이고,
// 여기서는 이 패키지의 정적 빌드(`../storybook-static`)와 이 패키지에 깔린 Playwright 의 `test` 를 넘긴다.
import { join } from "node:path";
import { test as base, expect } from "@playwright/test";
import { photographedStories as storiesIn, storybookTest, type StoryEntry } from "./index.ts";

const SITE = join(import.meta.dirname, "..", "storybook-static");

export const test = storybookTest(base, SITE);

/** 이 패키지의 정적 빌드에서 판정 스토리가 아닌 스토리. 정적 빌드가 없으면 던진다. */
export function photographedStories(): StoryEntry[] {
  return storiesIn(SITE);
}

export {
  MODES,
  ORIGIN,
  inDefaultTheme,
  type Globals,
  type Mode,
  type StoryEntry,
  type Storybook,
} from "./index.ts";
export { expect };
