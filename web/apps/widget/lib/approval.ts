// 승인 묻기의 글 규칙(web-widget 명세 "승인 묻기"). 인자를 보이는 글과, 거부 사유가 비었는지를 서버와 같이 가르는 것이다.
//
// - 인자는 `JSON.stringify(args, null, 2)` 의 글이다. 받은 키 차례를 지키고, 두 칸 들여쓰고, 한글을 이스케이프하지
//   않는다. 고치거나 줄이지 않는다.
// - 서버는 거부 사유를 파이썬 `str.strip()` 으로 다듬어 비면 422 를 낸다. JS 의 `trim()` 은 U+001C~U+001F 와 U+0085 를
//   지우지 않고 U+FEFF 를 지워 서버와 갈리므로 쓰지 않는다. 아래 글자는 `str.isspace()` 가 참인 글자 전부다
//   (`uv run python` 으로 0~U+10FFFF 를 훑어 찍었다).

/** 파이썬 `str.isspace()` 가 참인 글자. */
const PYTHON_SPACE = new Set(
  [
    0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x85, 0xa0, 0x1680, 0x2000, 0x2001,
    0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008, 0x2009, 0x200a, 0x2028, 0x2029, 0x202f,
    0x205f, 0x3000,
  ].map((code) => String.fromCodePoint(code)),
);

/** 서버가 다듬으면 비는 사유인가. 파이썬 `str.strip()` 이 지우는 글자만 들었으면 참이다. */
export function blankReason(reason: string): boolean {
  return Array.from(reason).every((char) => PYTHON_SPACE.has(char));
}

/** 인자를 보이는 글. */
export function argsText(args: unknown): string {
  return JSON.stringify(args, null, 2);
}
