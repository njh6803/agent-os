// browser.mjs 가 회차마다 띄우는 Node 자식. 표지를 끼운 `Markdown` 호출과 서버 렌더를 해 보고 JSON 한 줄을 낸다.
//
// 인자
//   <묶음 경로> stages <입력 이름>             입력 하나에서 어디까지 갔고 무엇을 던졌는지. 이름은 inputs.mjs 의 `inputOf` 꼴이다.
//   <묶음 경로> threshold <꼴> <lo> <hi>       `Markdown` 이 던지기 시작하는 깊이를 lo(던지지 않는다)와 hi(던진다) 사이에서 좁힌다.
// 던진 것은 측정 결과라 종료 코드 0 이다. 스택은 글 그대로 내고, 모듈로 옮기는 일은 부모가 한다.
import { createRequire } from "node:module";
import { DEPTH_KINDS, inputOf } from "./inputs.mjs";

const [bundlePath, command, ...rest] = process.argv.slice(2);
const entry = createRequire(import.meta.url)(bundlePath);
const print = (value) => console.log(JSON.stringify(value));
const count = (html, piece) => html.split(piece).length - 1;

if (command === "stages") {
  const name = rest[0];
  const text = inputOf(name);
  if (text === null) {
    print({ ok: false, reason: `없는 입력이다: ${name}` });
    process.exit(2);
  }
  const result = entry.stages(text);
  const html = result.render?.html ?? null;
  print({
    ok: true,
    name,
    inputChars: text.length,
    reached: result.reached,
    filterCalls: result.filterCalls,
    thrown: result.thrown,
    markdownMs: Math.round(result.markdownMs * 10) / 10,
    render:
      result.render === null
        ? null
        : {
            thrown: result.render.thrown,
            ms: Math.round(result.render.ms * 10) / 10,
            htmlBytes: html === null ? null : Buffer.byteLength(html),
            counts: html === null ? null : { blockquote: count(html, "<blockquote"), ul: count(html, "<ul") },
          },
  });
} else if (command === "threshold") {
  const [kind, loText, hiText] = rest;
  const make = DEPTH_KINDS[kind];
  const lo = Number(loText);
  const hi = Number(hiText);
  if (make === undefined || !Number.isInteger(lo) || !Number.isInteger(hi) || lo >= hi) {
    print({ ok: false, reason: `인자가 틀렸다: ${rest.join(" ")}` });
    process.exit(2);
  }
  // 양 끝이 기대와 같아야 좁히기가 뜻이 있다(lo 는 던지지 않고 hi 는 던진다).
  const loThrows = entry.markdownThrows(make(lo));
  const hiThrows = entry.markdownThrows(make(hi));
  if (loThrows || !hiThrows) {
    print({ ok: true, kind, bracketed: false, lo, hi, loThrows, hiThrows });
  } else {
    let pass = lo;
    let fail = hi;
    let checks = 2;
    while (fail - pass > 1) {
      const mid = Math.floor((pass + fail) / 2);
      if (entry.markdownThrows(make(mid))) fail = mid;
      else pass = mid;
      checks += 1;
    }
    // 같은 프로세스에서 두 끝을 한 번씩 더 본다. 스택이 넘치는 깊이는 JIT 상태에 따라 조금 움직일 수 있다.
    const again = { lastPassThrows: entry.markdownThrows(make(pass)), firstThrowThrows: entry.markdownThrows(make(fail)) };
    print({ ok: true, kind, bracketed: true, lastPass: pass, firstThrow: fail, checks, again });
  }
} else {
  print({ ok: false, reason: `없는 명령이다: ${command}` });
  process.exit(2);
}
