// design-refresh 같은 값 프로브: 한 벌(테마·모드) 안에서 같은 원색을 가리키는 쓰임새 토큰의 짝을 여덟 벌 모두에서 센다.
//   node .scratch/design-refresh/probes/same-values.mjs
//
// 스토리 테스트는 컴포넌트의 색을 쓰임새 토큰이 풀린 계산값과 맞댄다(`web-design.md`). 두 토큰이 그 벌에서 같은 값이면
// 계산값으로 둘을 가를 수 없어, 한쪽을 다른 쪽으로 바꾼 실수가 그 벌에서는 초록으로 지난다. 그래서 짝마다 값이 다른 벌을
// 함께 낸다. 그 벌에서 재면 가를 수 있다.
// 값은 `design.mjs` 의 `readRefresh()` 가 돌려주는 디자인 토큰 JSON 에서 읽는다(디자인 파일의 이름이다. 코드에서
// `shadow` 는 `shadow-color` 다).
// stdout 은 같은 값을 가진 짝마다 같은 벌의 목록과 다른 벌의 수다. 여덟 벌 모두 같은 짝은 "가를 수 없음"이다.

import { readRefresh } from "../../design-system/probes/tokens/design.mjs";

const { tokens } = readRefresh();
const THEMES = Object.keys(tokens.theme);
const MODES = ["light", "dark"];
const SETS = THEMES.flatMap((theme) => MODES.map((mode) => ({ theme, mode })));
const NAMES = Object.keys(tokens.theme[THEMES[0]].semantic.light);

function value(theme, mode, name) {
  const t = tokens.theme[theme];
  const ref = t.semantic[mode][name];
  const dot = ref.indexOf(".");
  return t.primitive[ref.slice(0, dot)][ref.slice(dot + 1)].toUpperCase();
}

const rows = [];
for (let i = 0; i < NAMES.length; i += 1) {
  for (let j = i + 1; j < NAMES.length; j += 1) {
    const [a, b] = [NAMES[i], NAMES[j]];
    const same = SETS.filter(({ theme, mode }) => value(theme, mode, a) === value(theme, mode, b));
    if (same.length > 0) {
      rows.push({ a, b, same, differ: SETS.length - same.length });
    }
  }
}

for (const { a, b, same, differ } of rows) {
  const where = same.map(({ theme, mode }) => `${theme}/${mode}`).join(", ");
  const verdict = differ === 0 ? "가를 수 없음" : `다른 벌 ${String(differ)}`;
  console.log(`${a} = ${b} :: 같은 벌 ${String(same.length)} (${where}) :: ${verdict}`);
}
console.log(`같은 값을 가진 짝 ${String(rows.length)}개, 쓰임새 토큰 ${String(NAMES.length)}개, 벌 ${String(SETS.length)}개`);
