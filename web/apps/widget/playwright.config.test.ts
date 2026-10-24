// 위젯 e2e 의 Playwright 설정(web-widget 티켓 11). 실제 모델을 부르는 프로젝트 `llm` 은 환경 변수가 있을 때만 프로젝트
// 목록에 든다. 그 변수는 감싸는 파이썬 시험(tests/test_widget_llm.py)만 준다. 그래서 프로젝트를 지정하지 않은 로컬
// 명령과 CI 의 e2e-widget 이 실제 모델을 부르지 않는다. 설정 파일을 변수마다 새로 읽어 목록을 본다.

import type { PlaywrightTestConfig } from "@playwright/test";
import { afterEach, expect, test, vi } from "vitest";
import { LLM_ENV } from "./e2e/env.ts";

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

async function projectNames(flag: string | undefined): Promise<readonly (string | undefined)[]> {
  vi.stubEnv(LLM_ENV, flag);
  vi.resetModules();
  const module: { default: PlaywrightTestConfig } = await import("./playwright.config.ts");
  return (module.default.projects ?? []).map((project) => project.name);
}

test("실제 모델 변수가 없으면 프로젝트 목록에 llm 이 없다", async () => {
  expect(await projectNames(undefined)).toEqual(["chromium"]);
});

test("실제 모델 변수가 1 이면 프로젝트 목록에 llm 이 든다", async () => {
  expect(await projectNames("1")).toEqual(["chromium", "llm"]);
});

test("실제 모델 변수가 1 이 아닌 값이면 llm 이 없다", async () => {
  expect(await projectNames("0")).toEqual(["chromium"]);
});
