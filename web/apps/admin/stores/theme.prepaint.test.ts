// 그리기 전 스크립트(public/theme.js)의 단위 시험(admin-style 명세 "첫 그림의 테마"). 그 파일은 브라우저가 그대로 받는
// 평범한 JS 라 패키지의 THEMES 와 설정 화면의 저장 키를 import 하지 못하고 따로 적는다. 그래서 파일을 읽어 node `vm` 의
// 맥락에서 실제로 돌리고, 테마 키와 저장 키는 앱이 쓰는 상수에서 읽어 맞댄다. THEMES 에 테마를 더하거나 저장 키를 바꾸고
// 스크립트를 고치지 않으면 여기서 빨갛다. 이 파일은 `public/` 밖에 둔다. `public/` 의 파일은 그대로 공개된다.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { runInNewContext } from "node:vm";
import { THEMES } from "@agent-os/ui";
import { describe, expect, test } from "vitest";
import { THEME_STORAGE_KEY } from "./theme";

const SCRIPT = readFileSync(join(import.meta.dirname, "..", "public", "theme.js"), "utf8");

/** 시험이 만든 문서 뿌리의 `dataset` 과 `localStorage` 접근자로 스크립트를 돌리고, 돌린 뒤의 `dataset` 을 돌려준다. */
function runWith(storage: () => Pick<Storage, "getItem">): Record<string, string> {
  const dataset: Record<string, string> = {};
  const context = { document: { documentElement: { dataset } } };
  Object.defineProperty(context, "localStorage", { get: storage, enumerable: true });
  runInNewContext(SCRIPT, context);
  return dataset;
}

/** 저장 키에만 그 값을 돌려주는 저장소. 다른 키를 읽는 스크립트는 값을 받지 못한다. */
function storing(value: string | null): () => Pick<Storage, "getItem"> {
  return () => ({ getItem: (key) => (key === THEME_STORAGE_KEY ? value : null) });
}

describe("그리기 전 스크립트", () => {
  test.each(THEMES.map(({ key }) => key))(
    "저장 값이 테마 키 %s 면 문서 뿌리의 data-theme 에 그 키를 단다",
    (key) => {
      expect(runWith(storing(key))).toEqual({ theme: key });
    },
  );

  test.each(["purple", "", "JJOKBIT", '"jjokbit"'])(
    "저장 값이 목록에 없는 %j 면 아무것도 달지 않는다",
    (value) => {
      expect(runWith(storing(value))).toEqual({});
    },
  );

  test("저장소가 비었으면 아무것도 달지 않는다", () => {
    expect(runWith(storing(null))).toEqual({});
  });

  test("getItem 이 던지면 예외 없이 아무것도 달지 않는다", () => {
    const throwing = () => ({
      getItem: (): string | null => {
        throw new Error("저장소를 막았다");
      },
    });

    expect(runWith(throwing)).toEqual({});
  });

  test("localStorage 접근자가 던지면 예외 없이 아무것도 달지 않는다", () => {
    const denied = (): Pick<Storage, "getItem"> => {
      throw new Error("저장소를 막았다");
    };

    expect(runWith(denied)).toEqual({});
  });
});
