// (다) 후보 ③: micromark 확장. 파싱 뒤에 벗기지 않고, 토큰을 자르는 단계에서 밑줄과 숫자 사이의 별표를 글자로 읽는다.
//
// - 밑줄(`_`)은 언제나 글자다. 기본 구문의 강조(attention)보다 먼저 시도되어 밑줄을 하나씩 `data` 로 먹는다.
// - 별표 묶음은 바로 앞 글자와 바로 뒤 글자가 둘 다 ASCII 숫자일 때만 글자로 먹는다. 아니면 물러나고(nok) 기본
//   구문의 강조가 그 자리를 다시 읽는다.
// 묶음마다 따로 판정하므로 literal-marks.ts 의 두 규칙(노드의 여는 묶음과 닫는 묶음을 함께 본다)과 갈리는 입력이 있다.
//
// 확장은 뒤에 등록한 것이 먼저 시도된다(micromark 의 combineExtensions 가 새 구문을 앞에 끼운다). 그래서 강조 구문을
// 바꾸는 다른 플러그인(remark-cjk-friendly)과 함께 쓸 때는 이 플러그인을 그 뒤에 둔다.
import type { Code, Construct, Extension, State } from "micromark-util-types";
// remark-parse 의 타입 선언이 unified 의 `Data` 에 `micromarkExtensions` 칸을 더한다. 그 선언을 싣는 줄이다.
import type {} from "remark-parse";
import type { Processor } from "unified";

const ASTERISK = 42;
const UNDERSCORE = 95;

function isDigit(code: Code): boolean {
  return code !== null && code >= 48 && code <= 57;
}

const literalUnderscore: Construct = {
  name: "literalUnderscore",
  tokenize(effects, ok) {
    return (code) => {
      effects.enter("data");
      effects.consume(code);
      effects.exit("data");
      return ok;
    };
  },
};

const literalAsteriskBetweenDigits: Construct = {
  name: "literalAsteriskBetweenDigits",
  tokenize(effects, ok, nok) {
    const before = this.previous;
    const run: State = (code) => {
      if (code === ASTERISK) {
        effects.consume(code);
        return run;
      }
      effects.exit("data");
      return isDigit(code) ? ok(code) : nok(code);
    };
    return (code) => {
      if (!isDigit(before)) return nok(code);
      effects.enter("data");
      return run(code);
    };
  },
};

export const literalMarksSyntax: Extension = {
  text: { [ASTERISK]: literalAsteriskBetweenDigits, [UNDERSCORE]: literalUnderscore },
};

/** remark 플러그인. 파서(remark-parse)가 읽는 micromark 확장 목록에 위 확장을 더한다. */
export function remarkLiteralMarksSyntax(this: Processor): undefined {
  const data = this.data();
  const extensions = data.micromarkExtensions ?? [];
  extensions.push(literalMarksSyntax);
  data.micromarkExtensions = extensions;
}
