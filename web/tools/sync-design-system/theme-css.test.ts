// 디자인 토큰 CSS 를 푸는 공용 모듈의 캐스케이드 테스트. 실제 디자인 토큰 CSS 에서는 차례만으로 이기는 쪽이 갈려(짓기의
// 테스트가 본다) 특정성과 레이어가 차례를 거스르는 자리가 없으므로, 그 규칙은 지어낸 CSS 로 본다.

import { describe, expect, test } from "vitest";
import { CommandError } from "./command.ts";
import { parseThemeCss, type Mode } from "./theme-css.ts";

function values(css: string, theme: string, mode: Mode): Record<string, string> {
  const winners = parseThemeCss(css).winners(theme, mode);
  return Object.fromEntries(
    [...winners].map(([property, declaration]) => [property, declaration.value]),
  );
}

describe("캐스케이드", () => {
  test("특정성이 높은 선언은 뒤에 온 낮은 선언을 이긴다", () => {
    const css = `@layer theme {
  [data-theme="a"][data-mode="dark"] {
    --primary: #222222;
  }
  :root,
  [data-theme="a"] {
    --primary: #111111;
  }
}
`;

    expect(values(css, "a", "dark")).toEqual({ "--primary": "#222222" });
    expect(values(css, "a", "light")).toEqual({ "--primary": "#111111" });
  });

  test("특정성이 같으면 뒤에 온 선언이 이긴다", () => {
    const css = `:root {
  --bg: #111111;
}
[data-mode="dark"] {
  --bg: #222222;
}
`;

    expect(values(css, "a", "dark")).toEqual({ "--bg": "#222222" });
  });

  test("레이어 밖 선언은 레이어 안 선언을 이기고, 뒤에 처음 나온 레이어는 앞 레이어를 이긴다", () => {
    const css = `:root {
  --outside: #111111;
}
@layer one {
  [data-theme="a"][data-mode="light"] {
    --outside: #222222;
    --later: #333333;
  }
}
@layer two {
  :root {
    --later: #444444;
  }
}
`;

    expect(values(css, "a", "light")).toEqual({ "--outside": "#111111", "--later": "#444444" });
  });

  test("레이어의 차례는 사용자 정의 속성이 없는 규칙까지 세어 처음 나온 차례다", () => {
    const css = `@layer one {
  :root {
    color: red;
  }
}
@layer two {
  :root {
    --x: #111111;
  }
}
@layer one {
  :root {
    --x: #222222;
  }
}
`;

    expect(values(css, "a", "light")).toEqual({ "--x": "#111111" });
  });

  test("뿌리에 맞지 않는 선택자(:host, :not 이 거르는 것, 결합자)와 @media 안의 선언은 읽지 않는다", () => {
    const css = `@layer theme {
  [data-theme="a"]:not([data-mode="dark"]) {
    --not-dark: #111111;
  }
  :host,
  :host([data-theme="a"]) {
    --host: #222222;
  }
  :root [data-theme="a"] {
    --descendant: #333333;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --media: #444444;
    }
  }
}
`;

    expect(values(css, "a", "light")).toEqual({ "--not-dark": "#111111" });
    expect(values(css, "a", "dark")).toEqual({});
  });

  test("풀 수 없는 선택자가 사용자 정의 속성을 선언하면 입력 오류다", () => {
    const css = `[data-theme="a"]:hover {
  --hover: #111111;
}
`;
    let caught: unknown;
    try {
      values(css, "a", "light");
    } catch (error) {
      caught = error;
    }

    expect(caught).toBeInstanceOf(CommandError);
    expect(caught instanceof CommandError ? caught.kind : undefined).toBe("input");
    expect(caught instanceof Error ? caught.message : "").toContain(
      '선택자를 풀 수 없다: [data-theme="a"]:hover',
    );
  });
});
