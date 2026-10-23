// 사이트가 준 임베드 설정을 읽는다. iframe 방식은 질의, 페이지 안 방식(티켓 10)은 요소의 속성에서 같은 이름 다섯을
// 받는다(web-widget 명세 "임베드"). 읽는 자리가 달라 값을 꺼내는 함수를 받고, 문제의 글머리("위젯 질의")는 부르는
// 쪽이 붙인다.
//
// - `agent` 는 필수이고 플러그인 이름의 패턴을 지나야 한다. 없거나 밖이면 `agent` 가 null 이라 위젯은 요청을 보내지
//   못한다. 패턴은 계약의 실행 시작 본문과 같다(embed.test.ts 가 openapi.json 과 맞댄다).
// - `theme` 과 `mode` 가 목록 밖이면 기본값으로 그린다. 위젯은 그대로 쓸 수 있기 때문이다. 모드가 null 이면 시스템
//   설정을 따른다.
// - 보일 글인 `heading`·`intro` 의 빈 값과 공백만 든 값은 주지 않은 것으로 읽는다. 보일 것이 없기 때문이다.
//   `agent`·`theme`·`mode` 의 빈 값은 준 값이라 패턴·목록 밖으로 본다(명세의 "없으면"은 주지 않은 것이다).

import { DEFAULT_THEME, MODES, THEMES, type Mode, type ThemeKey } from "@agent-os/ui";

export const AGENT_PATTERN = /^[a-z][a-z0-9-]{1,62}$/;

export const EMBED_NAMES = ["agent", "heading", "intro", "theme", "mode"] as const;
export type EmbedName = (typeof EMBED_NAMES)[number];

export interface Embed {
  /** null 이면 설정이 잘못돼 요청을 보내지 못한다. */
  readonly agent: string | null;
  /** 위쪽 띠의 이름. 주지 않았으면 받은 `agent` 값이다. */
  readonly heading: string;
  /** 첫 화면의 할 수 있는 일 한 줄. null 이면 그 줄을 그리지 않는다. */
  readonly intro: string | null;
  readonly theme: ThemeKey;
  /** null 이면 시스템 설정을 따른다. */
  readonly mode: Mode | null;
}

export interface EmbedProblem {
  readonly name: EmbedName;
  /** 무엇이 틀렸고 위젯이 어떻게 그리는지. 받은 값을 JSON 글자로 싣는다. */
  readonly reason: string;
}

function isTheme(value: string): value is ThemeKey {
  return THEMES.some((theme) => theme.key === value);
}

function isMode(value: string): value is Mode {
  return MODES.some((mode) => mode === value);
}

export function readEmbed(read: (name: EmbedName) => string | null): {
  embed: Embed;
  problems: EmbedProblem[];
} {
  const shown = (name: "heading" | "intro"): string | null => {
    const value = read(name);
    return value?.trim() === "" ? null : value;
  };
  const problems: EmbedProblem[] = [];

  const agentValue = read("agent");
  let agent: string | null = null;
  if (agentValue === null) {
    problems.push({ name: "agent", reason: "에이전트 이름이 없다. 요청을 보내지 않는다" });
  } else if (!AGENT_PATTERN.test(agentValue)) {
    problems.push({
      name: "agent",
      reason: `플러그인 이름(${AGENT_PATTERN.source})이어야 한다. 받은 값: ${JSON.stringify(agentValue)}. 요청을 보내지 않는다`,
    });
  } else {
    agent = agentValue;
  }

  const themeValue = read("theme");
  let theme: ThemeKey = DEFAULT_THEME;
  if (themeValue !== null) {
    if (isTheme(themeValue)) {
      theme = themeValue;
    } else {
      const keys = THEMES.map((entry) => entry.key).join(", ");
      problems.push({
        name: "theme",
        reason: `테마 목록(${keys})의 키여야 한다. 받은 값: ${JSON.stringify(themeValue)}. 기본 테마 ${DEFAULT_THEME} 로 그린다`,
      });
    }
  }

  const modeValue = read("mode");
  let mode: Mode | null = null;
  if (modeValue !== null) {
    if (isMode(modeValue)) {
      mode = modeValue;
    } else {
      problems.push({
        name: "mode",
        reason: `${MODES.join(" 나 ")} 여야 한다. 받은 값: ${JSON.stringify(modeValue)}. 시스템 설정을 따른다`,
      });
    }
  }

  return {
    embed: {
      agent,
      heading: shown("heading") ?? agentValue ?? "",
      intro: shown("intro"),
      theme,
      mode,
    },
    problems,
  };
}
