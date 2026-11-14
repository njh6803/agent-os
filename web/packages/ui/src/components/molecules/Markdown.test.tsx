// 마크다운 부품의 단위 시험(answer-markdown 명세 "부품의 단위 시험", 티켓 01). 입력마다 무엇이 그려지는지를 말해 준다. 바깥
// 행동만 본다. 그린 DOM 을 요소의 종류와 차례, 글, 링크의 주소와 속성만 남긴 뼈대(`markdown/cases/skeleton.ts`)로 바꾸어 목표와
// 견주고, 모든 입력에는 규칙 하나(`markdown/cases/rules.ts`)를 건다. 모양(간격, 색, 글자 크기)은 스토리 테스트와 사진 비교가
// 본다. 클래스 이름의 글자와 안쪽 함수의 이름은 단언하지 않는다(라이브러리가 붙이는 클래스가 요소에 넘어가지 않았다는
// 음성 단언은 예외다). 걸린 시간도 단언하지 않는다.
//
// 티켓 02(출력을 다듬는 변환)의 사례도 여기 건다. 닫히지 않은 굵게, 숫자 사이의 기호, 문장 끝 번호, 출처 덩이, 그 넷을
// 합친 것이다. 변환은 모든 입력에 함께 걸리므로 01 의 사례(위험한 입력, 병적인 입력 포함)도 그 변환을 지난 결과를 본다.
import { render, within } from "@testing-library/react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BREAKS, type ShapeCase } from "../../markdown/cases/breaks";
import { CITE, CITE_EDGES } from "../../markdown/cases/cite";
import { COMBINED, SCREEN_INPUTS } from "../../markdown/cases/combined";
import { DANGER_CASES } from "../../markdown/cases/danger";
import { CJK, INTERPLAY, LITERAL } from "../../markdown/cases/emphasis";
import { SOURCE_EDGES, SOURCES } from "../../markdown/cases/sources";
import { analyze, violations } from "../../markdown/cases/rules";
import { ALIGNED_TABLE, LINKS, SHAPE } from "../../markdown/cases/shape";
import { skeletonOf } from "../../markdown/cases/skeleton";
import { STRESS_FALLBACK_NAMES, STRESS_INPUTS } from "../../markdown/cases/stress";
import { allowElement } from "../../markdown/options";
import { Markdown, MarkdownText } from "./Markdown";

afterEach(() => {
  vi.restoreAllMocks();
});

/** 콘솔의 오류와 경고를 가로채 세는 탐침. 가로챈 호출은 화면에 찍히지 않는다. */
function listenToConsole() {
  return {
    errors: vi.spyOn(console, "error").mockImplementation(() => undefined),
    warnings: vi.spyOn(console, "warn").mockImplementation(() => undefined),
  };
}

const HIDDEN_NEW_TAB = "(새 탭에서 열림)";
const SEPARATORS = new Set([
  "p",
  "div",
  "blockquote",
  "ul",
  "ol",
  "li",
  "table",
  "thead",
  "tbody",
  "tr",
  "th",
  "td",
  "pre",
  "hr",
  "br",
  "h1",
  "h2",
  "h3",
  "h4",
  "h5",
  "h6",
]);

/**
 * 화면의 갈래가 그린 글의 낱말. 블록과 표 칸의 경계는 공백으로 보고, 링크에 숨긴 문구는 뺀다. 위첨자 번호는 화면에서 작은
 * 글자로 앞말과 갈리므로 그 앞만 공백으로 본다(글자만 내는 갈래는 번호 앞에 공백을 두고 뒤에는 두지 않는다).
 */
function screenWords(root: Element): string[] {
  let out = "";
  const walk = (node: Node): void => {
    if (node instanceof Text) {
      out += node.data;
      return;
    }
    if (!(node instanceof Element)) return;
    if (node.localName === "span" && node.textContent === HIDDEN_NEW_TAB) return;
    const separate = SEPARATORS.has(node.localName);
    if (separate || node.localName === "sup") out += " ";
    for (const child of Array.from(node.childNodes)) walk(child);
    if (separate) out += " ";
  };
  for (const child of Array.from(root.childNodes)) walk(child);
  return out.split(/\s+/).filter((word) => word !== "");
}

const wordsOf = (text: string): string[] => text.split(/\s+/).filter((word) => word !== "");

// ── 깊이 가드의 입력 ────────────────────────────────────────────────────────────────────────────────────────────
const quote = (depth: number): string => `${">".repeat(depth)} a`;
const listInline = (depth: number): string => `${"- ".repeat(depth)}a`;
const listIndent = (depth: number): string =>
  Array.from({ length: depth }, (_, i) => `${" ".repeat(2 * i)}- a`).join("\n");
/** 인용과 목록이 번갈아 겹친 입력. 쌍마다 인용 하나와 목록 하나(깊이 둘)이다. */
const mixedPairs = (pairs: number): string => `${"> - ".repeat(pairs)}a`;
const MIXED_ELEVEN = `${"> - ".repeat(5)}> a`;

const GUARD_TEN = {
  "인용 10겹": quote(10),
  "한 줄 목록 10겹": listInline(10),
  "들여쓴 목록 10겹": listIndent(10),
  "인용과 목록이 섞인 10겹": mixedPairs(5),
};
const GUARD_ELEVEN = {
  "인용 11겹": quote(11),
  "한 줄 목록 11겹": listInline(11),
  "들여쓴 목록 11겹": listIndent(11),
  "인용과 목록이 섞인 11겹": MIXED_ELEVEN,
};

// ── 위험한 입력 ─────────────────────────────────────────────────────────────────────────────────────────────────
describe("위험한 입력 52가지", () => {
  it("입력이 52가지다", () => {
    expect(DANGER_CASES).toHaveLength(52);
    expect(new Set(DANGER_CASES.map((item) => item.id)).size).toBe(52);
  });

  it.each(DANGER_CASES)(
    "$id 입력은 허용 목록 밖의 요소와 위험한 속성과 위험한 주소 없이 그려진다",
    ({ input, must }) => {
      const { container } = render(<Markdown text={input} />);
      expect(violations(container)).toEqual([]);
      expect(must?.(analyze(container)) ?? []).toEqual([]);
    },
  );

  it.each(DANGER_CASES.filter((item) => item.shown !== undefined))(
    "$id 입력의 원시 HTML 은 쓴 글자 그대로 보인다",
    ({ input, shown }) => {
      const { container } = render(<Markdown text={input} />);
      expect(container.textContent).toContain(shown);
    },
  );

  it("글자만 내는 갈래는 52가지 어디에도 요소를 그리지 않는다", () => {
    for (const { id, input } of DANGER_CASES) {
      const { container, unmount } = render(<MarkdownText text={input} />);
      expect({ id, elements: container.childElementCount }).toEqual({ id, elements: 0 });
      unmount();
    }
  });

  it("양성 대조: 라이브러리의 기본 설정으로 그린 이미지는 규칙에 걸린다", () => {
    const { container } = render(
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {"![추적](https://evil.example/p.png?q=secret)"}
      </ReactMarkdown>,
    );
    expect(violations(container)).toContain("금지한 요소 <img>가 그려졌다");
  });

  it("양성 대조: 라이브러리의 기본 설정으로 그린 사용자 정보 주소와 제목 단계도 규칙에 걸린다", () => {
    const { container } = render(
      <ReactMarkdown remarkPlugins={[remarkGfm]}>
        {"# 제목\n\n[은행](https://www.law.go.kr@evil.example/login)\n\n- [x] 한 일"}
      </ReactMarkdown>,
    );
    const found = violations(container);
    expect(found).toContain("허용 목록 밖의 요소 <h1>가 그려졌다");
    expect(found).toContain(
      'href에 사용자 정보가 있다: "https://www.law.go.kr@evil.example/login"',
    );
    expect(found).toContain("금지한 요소 <input>가 그려졌다");
  });

  it("같은 입력을 부품으로 그리면 같은 규칙에 걸리지 않는다", () => {
    const { container } = render(
      <Markdown
        text={
          "![추적](https://evil.example/p.png?q=secret)\n\n[은행](https://www.law.go.kr@evil.example/login)\n\n- [x] 한 일"
        }
      />,
    );
    expect(violations(container)).toEqual([]);
  });
});

// ── 목표 모양과 지금의 결과 ─────────────────────────────────────────────────────────────────────────────────────
function shapeTests(cases: readonly ShapeCase[], count: number): void {
  it(`입력이 ${String(count)}가지이고 목표를 적지 않은 입력에는 지금의 결과가 적혀 있다`, () => {
    expect(cases).toHaveLength(count);
    expect(new Set(cases.map((item) => item.id)).size).toBe(count);
    expect(cases.filter((item) => item.want === null && item.pinned === undefined)).toEqual([]);
  });

  it.each(cases.filter((item) => item.want !== null))(
    "$id 입력은 목표 모양으로 그려진다",
    ({ input, want }) => {
      const { container } = render(<Markdown text={input} />);
      expect(skeletonOf(container)).toBe(want);
      expect(violations(container)).toEqual([]);
    },
  );

  it.each(cases.filter((item) => item.want === null))(
    "$id 입력은 지금 정한 모양으로 그려진다",
    ({ input, pinned }) => {
      const { container } = render(<Markdown text={input} />);
      expect(skeletonOf(container)).toBe(pinned);
      expect(violations(container)).toEqual([]);
    },
  );
}

describe("한 줄 바꿈 30가지", () => {
  shapeTests(BREAKS, 30);
});

describe("제목·이미지·표·코드·각주·할 일 목록 21가지", () => {
  shapeTests(SHAPE, 21);
});

describe("링크 17가지", () => {
  shapeTests(LINKS, 17);
});

// ── 출력을 다듬는 변환(티켓 02) ─────────────────────────────────────────────────────────────────────────────────
describe("닫히지 않는 굵게 34가지", () => {
  shapeTests(CJK, 34);
});

describe("글자로 두는 기호 60가지", () => {
  shapeTests(LITERAL, 60);
});

describe("변환의 차례 11가지", () => {
  shapeTests(INTERPLAY, 11);
});

describe("문장 끝 번호 48가지", () => {
  shapeTests(CITE, 48);
});

describe("문장 끝 번호의 경계 입력 13가지", () => {
  shapeTests(CITE_EDGES, 13);
});

describe("출처 덩이 32가지", () => {
  shapeTests(SOURCES, 32);
});

describe("출처 덩이의 경계 입력 3가지", () => {
  shapeTests(SOURCE_EDGES, 3);
});

describe("합친 사례 17가지", () => {
  shapeTests(COMBINED, 17);
});

describe("문장 끝 번호와 출처 덩이의 그림", () => {
  it("번호는 링크가 아니고 누를 수 없다", () => {
    const { container } = render(<Markdown text={"그렇다 [1]"} />);
    const cite = container.querySelector("sup");
    expect(cite?.textContent).toBe("1");
    expect(cite?.closest("a")).toBeNull();
    expect(cite?.querySelector("a, button")).toBeNull();
    expect(cite?.hasAttribute("tabindex")).toBe(false);
  });

  it("번호와 출처 덩이의 표지는 DOM 에 남지 않는다", () => {
    const { container } = render(<Markdown text={SCREEN_INPUTS["mk-cite"]} />);
    for (const element of container.querySelectorAll("sup, div")) {
      const names = Array.from(element.attributes, (attr) => attr.name);
      expect(names.filter((name) => name.startsWith("data-"))).toEqual([]);
    }
  });

  it("출처 덩이는 최상위의 마지막 요소 하나로 감싸이고 본문은 그 밖에 남는다", () => {
    const { container } = render(<Markdown text={SCREEN_INPUTS["mk-cite"]} />);
    const root = container.firstElementChild;
    const block = root?.lastElementChild;
    expect(block?.localName).toBe("div");
    expect(block?.querySelector("ol")).not.toBeNull();
    expect(block?.textContent).toContain("출처");
    expect(root?.firstElementChild?.querySelectorAll("sup")).toHaveLength(2);
    expect(block?.querySelectorAll("sup")).toHaveLength(0);
  });

  it("마크다운 문법이 쓰지 않는 sup 과 div 는 원시 HTML 로 써도 그려지지 않는다", () => {
    const { container } = render(
      <Markdown text={'본문<sup>1</sup>\n\n<div class="sources">출처</div>'} />,
    );
    expect(container.querySelectorAll("sup")).toHaveLength(0);
    expect(container.firstElementChild?.querySelectorAll("div")).toHaveLength(0);
    expect(container.textContent).toContain("<sup>1</sup>");
  });

  it("각주 문법의 위첨자는 그려지지 않고 쓴 글자로 남는다", () => {
    const { container } = render(<Markdown text={"본문입니다[^1].\n\n[^1]: 각주 글"} />);
    expect(container.querySelectorAll("sup")).toHaveLength(0);
    expect(container.textContent).toContain("[^1]");
  });

  // 위의 두 시험은 원시 HTML 과 각주가 다른 층에서 먼저 글자가 되어 허용 판정이 없어도 지난다. 그래서 판정을 직접 부른다.
  it("허용 판정은 표지가 없는 sup 과 div 를 벗기고 표지가 있는 것과 다른 요소는 들인다", () => {
    const element = (tagName: string, properties: Record<string, string>) => ({
      type: "element" as const,
      tagName,
      properties,
      children: [],
    });
    expect(allowElement(element("sup", {}), 0, undefined)).toBe(false);
    expect(allowElement(element("sup", { dataCite: "first" }), 0, undefined)).toBe(true);
    expect(allowElement(element("div", {}), 0, undefined)).toBe(false);
    expect(allowElement(element("div", { dataSources: "true" }), 0, undefined)).toBe(true);
    expect(allowElement(element("p", {}), 0, undefined)).toBe(true);
  });
});

// ── 깊이 가드 ───────────────────────────────────────────────────────────────────────────────────────────────────
describe("깊이 가드", () => {
  it.each(Object.entries(GUARD_TEN))("%s 는 그린다", (_name, input) => {
    const { container } = render(<Markdown text={input} />);
    expect(container.querySelectorAll("blockquote, ul")).not.toHaveLength(0);
    // 안쪽 목록은 항목마다 a 를 낸다. 겹마다 줄바꿈 글자가 낀다.
    expect(container.textContent.replace(/\s+/g, "")).toMatch(/^a+$/);
    expect(violations(container)).toEqual([]);
  });

  it("그리는 깊이는 인용과 목록을 합쳐 센 겹의 수와 같다", () => {
    const quoted = render(<Markdown text={quote(10)} />);
    expect(quoted.container.querySelectorAll("blockquote")).toHaveLength(10);
    const listed = render(<Markdown text={listIndent(10)} />);
    expect(listed.container.querySelectorAll("ul")).toHaveLength(10);
    const mixed = render(<Markdown text={mixedPairs(5)} />);
    expect(mixed.container.querySelectorAll("blockquote")).toHaveLength(5);
    expect(mixed.container.querySelectorAll("ul")).toHaveLength(5);
  });

  it.each(Object.entries(GUARD_ELEVEN))(
    "%s 는 그리지 않고 넣은 글자 그대로 보인다",
    (_name, input) => {
      const { container } = render(<Markdown text={input} />);
      expect(container.textContent).toBe(input);
      expect(container.querySelector("blockquote, ul, ol, li")).toBeNull();
    },
  );

  it.each(Object.entries(GUARD_TEN))("%s 는 글자만 내는 갈래도 그린다", (_name, input) => {
    const { container } = render(<MarkdownText text={input} />);
    expect(container.childElementCount).toBe(0);
    expect(container.textContent).not.toBe(input);
    expect(container.textContent).toContain("a");
  });

  it.each(Object.entries(GUARD_ELEVEN))(
    "%s 는 글자만 내는 갈래도 넣은 글자 그대로 보인다",
    (_name, input) => {
      const { container } = render(<MarkdownText text={input} />);
      expect(container.childElementCount).toBe(0);
      expect(container.textContent).toBe(input);
    },
  );
});

// ── 실패하면 원문 ───────────────────────────────────────────────────────────────────────────────────────────────
describe("실패하면 원문", () => {
  it("가드에 걸린 입력은 콘솔에 오류와 경고를 남기지 않는다", () => {
    const { errors, warnings } = listenToConsole();
    render(<Markdown text={quote(11)} />);
    render(<MarkdownText text={quote(11)} />);
    expect(errors).not.toHaveBeenCalled();
    expect(warnings).not.toHaveBeenCalled();
  });

  it("같은 부품에 보통 글, 물러서는 글, 보통 글을 차례로 넣어 다시 그리면 마지막 그림이 그려진다", () => {
    const { errors, warnings } = listenToConsole();
    const { container, rerender } = render(<Markdown text="보통 글" />);
    expect(container.textContent).toBe("보통 글");
    rerender(<Markdown text={quote(11)} />);
    expect(container.textContent).toBe(quote(11));
    rerender(<Markdown text="**다시** 보통 글" />);
    expect(container.querySelector("strong")?.textContent).toBe("다시");
    expect(container.textContent).toBe("다시 보통 글");
    expect(errors).not.toHaveBeenCalled();
    expect(warnings).not.toHaveBeenCalled();
  });

  it("글자만 내는 갈래도 보통 글, 물러서는 글, 보통 글을 차례로 넣어 다시 그리면 마지막 그림이 그려진다", () => {
    const { errors, warnings } = listenToConsole();
    const { container, rerender } = render(<MarkdownText text="보통 글" />);
    rerender(<MarkdownText text={listInline(11)} />);
    expect(container.textContent).toBe(listInline(11));
    rerender(<MarkdownText text="**다시** 보통 글" />);
    expect(container.textContent).toBe("다시 보통 글");
    expect(errors).not.toHaveBeenCalled();
    expect(warnings).not.toHaveBeenCalled();
  });

  it("물러선 원문의 줄바꿈과 공백이 그대로다", () => {
    const input = `${quote(11)}\n  들여쓴 줄\n\n\n끝`;
    const { container } = render(<Markdown text={input} />);
    expect(container.textContent).toBe(input);
  });

  it("두 갈래는 따로 물러선다", () => {
    const screen = render(<Markdown text={quote(11)} />);
    const plain = render(<MarkdownText text="**굵게**" />);
    expect(screen.container.textContent).toBe(quote(11));
    expect(plain.container.textContent).toBe("굵게");
  });
});

// ── 병적인 입력 ─────────────────────────────────────────────────────────────────────────────────────────────────
describe("병적인 입력 14가지", () => {
  const entries = Object.entries(STRESS_INPUTS);

  it("입력이 14가지이고 원문으로 물러서야 하는 둘이 그 안에 있다", () => {
    expect(entries).toHaveLength(14);
    for (const name of STRESS_FALLBACK_NAMES) expect(Object.keys(STRESS_INPUTS)).toContain(name);
  });

  it.each(entries)(
    "%s 는 화면의 갈래가 던지지 않고 그리거나 원문으로 물러서며 규칙에 걸리지 않는다",
    (name, make) => {
      const input = make();
      const { container } = render(<Markdown text={input} />);
      expect(violations(container)).toEqual([]);
      // 별표·밑줄만 늘어선 입력은 가로줄, 따옴표 기호만 늘어선 입력은 빈 코드 블록이라 글이 없어도 요소는 그려진다.
      expect(container.childElementCount).toBe(1);
      if (STRESS_FALLBACK_NAMES.includes(name)) expect(container.textContent).toBe(input);
    },
  );

  it.each(entries)(
    "%s 는 글자만 내는 갈래가 던지지 않고 요소 없이 그리거나 원문으로 물러선다",
    (name, make) => {
      const input = make();
      const { container } = render(<MarkdownText text={input} />);
      expect(container.childElementCount).toBe(0);
      if (STRESS_FALLBACK_NAMES.includes(name)) expect(container.textContent).toBe(input);
    },
  );
});

// ── 글자만 내는 갈래 ────────────────────────────────────────────────────────────────────────────────────────────
describe("MarkdownText", () => {
  const TABLE = [
    "| 조문 | 내용 |",
    "|---|---|",
    "| 제750조 | 불법행위 |",
    "| 제751조 | 재산 이외의 손해 |",
  ].join("\n");
  const FENCE = "```";
  /** 화면의 갈래와 낱말의 열이 같아야 하는 입력. 번호 목록은 번호를 되살리므로 따로 본다. */
  const SAME_WORDS: Readonly<Record<string, string>> = {
    표: TABLE,
    "글머리 목록": "- 가\n- 나\n  - 다\n    - 라",
    링크: "문서는 [법령](https://www.law.go.kr/)입니다.",
    이미지: "그림: ![영수증 사진](https://tracker.example/r.png?id=184) 끝",
    "한 줄 바꿈": "첫째 줄\n둘째 줄\n\n셋째 줄",
    "코드 블록": `${FENCE}bash\ncurl -X POST https://example.com/\necho 끝\n${FENCE}`,
    "줄 안 코드와 서식": "**굵게** *기울임* ~~취소~~ `코드`",
    "제목과 인용": "# 제목\n\n본문\n\n> 인용 첫 줄\n> 인용 둘째 줄",
    "물러서는 입력": quote(11),
    "원시 HTML": "<b>굵게</b> <script>alert(1)</script>",
    "위첨자 번호": "휴직은 1년입니다. [1]\n신청은 30일 전입니다[2][3].",
    "출처 덩이": "본문입니다. [1]\n\n**출처:**\n\n[1] 편람\n[2] 규정",
    "숫자 사이 기호": "2*3*4 = 24이고 2*x*4 와 __init__.py",
  };

  it.each(Object.entries(SAME_WORDS))("%s 입력은 요소 없이 글자만 낸다", (_name, input) => {
    const { container } = render(<MarkdownText text={input} />);
    expect(container.childElementCount).toBe(0);
  });

  it.each(Object.entries(SAME_WORDS))(
    "%s 입력은 화면의 갈래와 낱말의 열이 같다",
    (_name, input) => {
      const plain = render(<MarkdownText text={input} />);
      const screen = render(<Markdown text={input} />);
      expect(wordsOf(plain.container.textContent)).toEqual(screenWords(screen.container));
    },
  );

  it("번호 목록의 번호를 항목 앞에 되살린다", () => {
    const { container } = render(<MarkdownText text={"1. 첫째\n2. 둘째\n3. 셋째"} />);
    expect(container.textContent).toMatch(/1\.\s*첫째[\s\S]*2\.\s*둘째[\s\S]*3\.\s*셋째/);
  });

  it("번호 목록은 번호를 뺀 낱말의 열이 화면의 갈래와 같다", () => {
    const input = "1. 첫째\n2. 둘째\n3. 셋째";
    const plain = render(<MarkdownText text={input} />);
    const screen = render(<Markdown text={input} />);
    const words = wordsOf(plain.container.textContent).filter((word) => !/^\d+\.$/.test(word));
    expect(words).toEqual(screenWords(screen.container));
  });

  it("다른 수에서 시작하는 번호 목록은 그 수부터 되살린다", () => {
    const { container } = render(<MarkdownText text={"3. 셋째\n4. 넷째"} />);
    expect(container.textContent).toMatch(/3\.\s*셋째[\s\S]*4\.\s*넷째/);
    expect(container.textContent).not.toMatch(/(^|\s)1\./);
  });

  it("안쪽 목록이 있는 번호 목록도 번호를 되살린다", () => {
    const { container } = render(<MarkdownText text={"1. 가\n   - 나\n2. 다"} />);
    expect(container.textContent).toMatch(/1\.\s*가[\s\S]*나[\s\S]*2\.\s*다/);
  });

  it("표의 칸과 줄이 붙지 않는다", () => {
    const { container } = render(<MarkdownText text={TABLE} />);
    expect(wordsOf(container.textContent)).toEqual([
      "조문",
      "내용",
      "제750조",
      "불법행위",
      "제751조",
      "재산",
      "이외의",
      "손해",
    ]);
  });

  it("이미지 자리가 이미지: 대체 글이고 주소는 보이지 않는다", () => {
    const { container } = render(
      <MarkdownText text="![영수증 사진](https://tracker.example/r.png?id=184)" />,
    );
    expect(container.textContent).toContain("이미지: 영수증 사진");
    expect(container.textContent).not.toContain("tracker.example");
  });

  it("대체 글이 빈 이미지는 이미지만 남는다", () => {
    const { container } = render(<MarkdownText text="![](https://tracker.example/r.png)" />);
    expect(container.textContent.trim()).toBe("이미지");
  });

  it("링크 글만 남고 새 탭에서 열린다는 문구는 내지 않는다", () => {
    const { container } = render(<MarkdownText text="[법령](https://www.law.go.kr/)" />);
    expect(container.textContent).toContain("법령");
    expect(container.textContent).not.toContain("새 탭");
  });

  it("한 줄 바꿈한 두 줄이 한 낱말로 붙지 않는다", () => {
    const { container } = render(<MarkdownText text={"첫째 줄\n둘째 줄"} />);
    expect(container.textContent).not.toContain("줄둘째");
    expect(wordsOf(container.textContent)).toEqual(["첫째", "줄", "둘째", "줄"]);
  });

  it("코드 블록의 글을 그대로 낸다", () => {
    const { container } = render(<MarkdownText text={`${FENCE}\n줄 하나\n줄 둘\n${FENCE}`} />);
    expect(container.textContent).toContain("줄 하나");
    expect(container.textContent).toContain("줄 둘");
    expect(container.textContent).not.toContain(FENCE);
  });

  it("물러서는 입력은 넣은 글자 그대로 낸다", () => {
    const { container } = render(<MarkdownText text={quote(11)} />);
    expect(container.textContent).toBe(quote(11));
  });

  it("위첨자 번호 앞에 공백을 두어 앞 낱말과 붙지 않는다", () => {
    const { container } = render(<MarkdownText text={"휴직은 1년입니다. [1]"} />);
    expect(container.childElementCount).toBe(0);
    expect(container.textContent).toBe("휴직은 1년입니다. 1");
  });

  it("이어진 위첨자 번호도 번호마다 공백으로 갈린다", () => {
    const { container } = render(<MarkdownText text={"가능합니다[1][2]."} />);
    expect(wordsOf(container.textContent)).toEqual(["가능합니다", "1", "2."]);
  });

  it("출처 덩이의 표지와 목록의 글이 남고 번호 목록의 번호가 되살아난다", () => {
    const { container } = render(<MarkdownText text={SCREEN_INPUTS["mk-cite"]} />);
    expect(container.childElementCount).toBe(0);
    const text = container.textContent;
    expect(text).toContain("출처");
    expect(text).toContain("1. 육아휴직 업무편람, 12쪽 (갱신일 2026-10-01)");
    expect(text).toContain("2. 인사 규정, 제3장 제14조 (갱신일 2026-08-15)");
  });

  it("숫자 사이의 별표와 밑줄과 되살린 굵게가 화면과 같은 글로 남는다", () => {
    const input = SCREEN_INPUTS["mk-side-2"];
    const plain = render(<MarkdownText text={input} />);
    const screen = render(<Markdown text={input} />);
    expect(wordsOf(plain.container.textContent)).toEqual(screenWords(screen.container));
    expect(plain.container.textContent).toContain("__init__.py");
    expect(plain.container.textContent).not.toContain("**");
  });
});

// ── 그 밖 ───────────────────────────────────────────────────────────────────────────────────────────────────────
describe("그 밖", () => {
  it("머리의 BOM 을 그리지 않는다", () => {
    const screen = render(<Markdown text={"\uFEFF안녕"} />);
    expect(screen.container.textContent).not.toContain("\uFEFF");
    expect(screen.container.textContent).toContain("안녕");
    const plain = render(<MarkdownText text={"\uFEFF안녕"} />);
    expect(plain.container.textContent).not.toContain("\uFEFF");
    expect(plain.container.textContent).toContain("안녕");
  });

  it("BOM 으로 시작해도 첫 줄의 제목 표시를 알아본다", () => {
    const { container } = render(<Markdown text={"\uFEFF# 제목\n\n본문"} />);
    expect(skeletonOf(container)).toBe("<h2>제목</h2><p>본문</p>");
  });

  it("BOM 으로 시작해도 각주 표지와 할 일 표시가 쓴 글자 그대로 남는다", () => {
    const bom = String.fromCharCode(0xfeff);
    const note = render(<Markdown text={`${bom}본문[^1]\n\n[^1]: 글`} />);
    expect(skeletonOf(note.container)).toBe("<p>본문[^1]</p><p>[^1]: 글</p>");
    const task = render(<Markdown text={`${bom}- [X] 일`} />);
    expect(task.container.textContent.trim()).toBe("[X] 일");
  });

  it("각주 정의 안에 든 정의도 사라지지 않고 쓴 글자로 남는다", () => {
    const { container } = render(
      <Markdown text={"본문[^1]\n\n[^1]: 가\n\n    [^2]: 나\n\n        [^3]: 다"} />,
    );
    expect(skeletonOf(container)).toBe(
      "<p>본문[^1]</p><p>[^1]: 가</p><p>[^2]: 나</p><p>[^3]: 다</p>",
    );
    expect(violations(container)).toEqual([]);
  });

  it.each([
    ["본문[^a\\*b]\n\n[^a\\*b]: 글", "<p>본문[^a\\*b]</p><p>[^a\\*b]: 글</p>"],
    ["본문[^a&amp;b]\n\n[^a&amp;b]: 글", "<p>본문[^a&amp;amp;b]</p><p>[^a&amp;amp;b]: 글</p>"],
  ])("각주 정의의 표지는 본문의 참조처럼 쓴 글자 그대로 남는다(%j)", (input, want) => {
    const { container } = render(<Markdown text={input} />);
    expect(skeletonOf(container)).toBe(want);
    expect(violations(container)).toEqual([]);
  });

  it.each(["", " ", "\n\n", "   \n  \n"])(
    "빈 글과 공백뿐인 글(%j)은 던지지 않고 아무 글도 그리지 않는다",
    (input) => {
      const screen = render(<Markdown text={input} />);
      expect(violations(screen.container)).toEqual([]);
      expect(screen.container.textContent.trim()).toBe("");
      const plain = render(<MarkdownText text={input} />);
      expect(plain.container.textContent.trim()).toBe("");
    },
  );

  it("링크에 화면 읽기 프로그램만 읽는 문구가 있고 새 탭으로 열린다", () => {
    const { container } = render(<Markdown text="[법령](https://www.law.go.kr/)" />);
    const link = within(container).getByRole("link");
    expect(link.getAttribute("href")).toBe("https://www.law.go.kr/");
    expect(link.getAttribute("target")).toBe("_blank");
    expect(link.getAttribute("rel")?.split(/\s+/).sort()).toEqual(["noopener", "noreferrer"]);
    expect(link.textContent).toBe(`법령${HIDDEN_NEW_TAB}`);
  });

  it("제목이 든 링크에 title 이 없다", () => {
    const { container } = render(
      <Markdown text={'[글](https://example.com/ "제목으로 속인 주소")'} />,
    );
    expect(container.querySelector("[title]")).toBeNull();
    expect(within(container).getByRole("link").getAttribute("title")).toBeNull();
  });

  it("표의 스크롤 칸이 이름 표의 묶음이고 포커스를 받는다", () => {
    const text = "| 가 | 나 |\n|---|---|\n| 1 | 2 |\n\n문단\n\n| 다 | 라 |\n|---|---|\n| 3 | 4 |";
    const { container } = render(<Markdown text={text} />);
    const boxes = within(container).getAllByRole("group", { name: "표" });
    expect(boxes).toHaveLength(2);
    for (const box of boxes) {
      expect(box.tabIndex).toBe(0);
      expect(box.querySelector("table")).not.toBeNull();
    }
  });

  it("넘치지 않는 표와 코드 블록도 같은 속성을 갖는다", () => {
    const { container } = render(<Markdown text={"| 가 |\n|---|\n| 1 |\n\n```\na\n```"} />);
    expect(within(container).getByRole("group", { name: "표" }).tabIndex).toBe(0);
    expect(container.querySelector("pre")?.tabIndex).toBe(0);
  });

  it("코드 블록의 pre 가 포커스를 받고 역할이 없다", () => {
    const { container } = render(
      <Markdown text={"```bash\ncurl -X POST https://example.com/\n```"} />,
    );
    const block = container.querySelector("pre");
    expect(block?.tabIndex).toBe(0);
    expect(block?.getAttribute("role")).toBeNull();
    expect(block?.getAttribute("aria-label")).toBeNull();
  });

  it("제목이 h2 부터 h6 으로 그려지고 h1 이 없다", () => {
    const { container } = render(
      <Markdown text={"# 하나\n\n## 둘\n\n### 셋\n\n#### 넷\n\n##### 다섯\n\n###### 여섯"} />,
    );
    const levels = Array.from(container.querySelectorAll("h1, h2, h3, h4, h5, h6")).map(
      (heading) => heading.localName,
    );
    expect(levels).toEqual(["h2", "h3", "h4", "h5", "h6", "h6"]);
  });

  it("라이브러리가 붙이는 클래스를 요소에 넘기지 않는다", () => {
    const { container } = render(
      <Markdown text={"```bash\necho 1\n```\n\n- [x] 한 일\n- [ ] 할 일"} />,
    );
    const classes = Array.from(container.querySelectorAll("*")).map((element) => element.className);
    for (const library of ["language-", "task-list-item", "contains-task-list"]) {
      expect(classes.filter((value) => value.includes(library))).toEqual([]);
    }
  });

  it("표 칸의 정렬을 인라인 style 이 아니라 정렬을 적은 칸마다 다른 클래스로 낸다", () => {
    const { container } = render(<Markdown text={ALIGNED_TABLE} />);
    expect(container.querySelector("[style]")).toBeNull();
    for (const row of ["thead th", "tbody td"]) {
      const classes = Array.from(container.querySelectorAll(row)).map((cell) => cell.className);
      expect(classes).toHaveLength(4);
      const [none, , center, right] = classes;
      expect(new Set([none, center, right]).size).toBe(3);
    }
  });

  it("뿌리 요소는 하나이고 그 안에 그린다", () => {
    const { container } = render(<Markdown text={"문단\n\n- 항목"} />);
    expect(container.childElementCount).toBe(1);
    expect(container.firstElementChild?.querySelector("p")?.textContent).toBe("문단");
  });
});
