// design-system 디자인 토큰 프로브의 입력: 내보낸 디자인 파일(Claude Design 의 .dc.html)이 그리는 값을 뽑는다.
//   node .scratch/design-system/probes/tokens/design.mjs [--out <파일>]
//   node .scratch/design-system/probes/tokens/design.mjs --refresh [--out <파일>]
//
// 디자인 파일은 hex 를 글자로 들지 않는다. 파일 끝의 `<script type="text/x-dc" data-dc-script>` 가 테마마다 (색상각, 채도)
// 짝과 고정된 밝기 단계로 OKLCH 에서 hex 를 계산하고(sRGB 밖이면 채도를 줄인다), 같은 스크립트가 디자인 토큰 JSON 과
// 대응표·명암비 표를 만든다. 그래서 그 스크립트를 그대로 돌려 값을 받는다. 스크립트는 저장소에 커밋한 디자인 파일의
// 것이고(계산과 객체 생성뿐이다), `DCLogic` 은 props 와 setState 만 흉내 낸다.
// 디자인 파일은 둘이다. 첫 탐색의 v3(`readDesign`, 디자인 토큰 JSON 의 키가 `tokJson`)와 2026-10-12 재탐색의
// `Agent OS Design System.dc.html`(`readRefresh`, 키가 `tokensJson`)이다. 둘은 테마 이름과 JSON 의 모양이 달라 함수를
// 나눴다. 앞의 것은 setup.mjs·measure.mjs 가 그대로 읽는다.
// stdout 은 v3 이면 열 벌(테마 다섯 × 모드 둘)의 쓰임새 토큰 열둘과 상태용 토큰의 명암비 요약이고, `--refresh` 면 여덟 벌
// (테마 넷 × 모드 둘)의 쓰임새 토큰 수, 원색 계열과 단계, 밀도 두 벌, 대응표의 판정 요약이다.

import { readFileSync, writeFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
export const DESIGN_FILE = resolve(HERE, "..", "..", "design", "Agent OS 디자인 시스템 v3.dc.html");
export const REFRESH_FILE = resolve(HERE, "..", "..", "design", "Agent OS Design System.dc.html");

/** 디자인 파일의 스크립트를 돌려 `renderVals()` 의 값을 돌려준다. */
function renderVals(path, props) {
  const source = readFileSync(path, "utf-8");
  const match = /<script type="text\/x-dc" data-dc-script[^>]*>([\s\S]*?)<\/script>/.exec(source);
  if (match === null) {
    throw new Error(`디자인 스크립트가 없다: ${path}`);
  }
  class DCLogic {
    constructor(props) {
      this.props = props;
    }
    setState() {}
  }
  // 저장소에 커밋한 디자인 파일의 스크립트다. 바깥 값을 끼워 넣지 않는다.
  const Component = new Function("DCLogic", `${match[1]}\nreturn Component;`)(DCLogic);
  return new Component(props).renderVals();
}

/**
 * 재탐색의 디자인 파일을 읽는다. 디자인 토큰 JSON(공통 크기, 밀도 두 벌, 테마마다 원색 토큰과 모드마다의 쓰임새 대응),
 * 테마 표(쓰임새 토큰 23행의 대응, hex, 디자인 파일이 셈한 명암비와 판정), 컴포넌트 표(상태·치수·쓰는 법), props 표,
 * 패턴, 아이콘 이름을 돌려준다. 보기 설정은 디자인 파일의 기본값(녹청, 라이트, 촘촘)이고 돌려주는 값은 그것과 무관하다.
 */
export function readRefresh(path = REFRESH_FILE) {
  const vals = renderVals(path, { theme: "nokcheong", mode: "light", density: "compact" });
  return {
    tokens: JSON.parse(vals.tokensJson),
    themeTables: vals.themeTables.map((table) => ({
      key: table.key,
      name: table.ko,
      default: table.def,
      primary: table.primaryTxt,
      rows: table.rows.map(({ token, lRef, dRef, lHex, dHex, ratio, pass, basis }) => ({
        token,
        light: lRef,
        dark: dRef,
        lightHex: lHex,
        darkHex: dHex,
        ratio,
        pass,
        basis,
      })),
    })),
    components: vals.comps.map((comp) => ({
      kind: comp.kind,
      name: comp.name,
      states: comp.states.map(({ s, t }) => ({ state: s, tokens: t })),
      dims: comp.dims.map(({ part, step, px }) => ({ part, step, px })),
      when: comp.when,
      pairs: comp.pairs.map(({ yes, no }) => ({ yes, no })),
    })),
    props: vals.props.map(({ name, rows }) => ({ name, rows })),
    patterns: vals.patterns.map(({ kind, title, rules }) => ({
      kind,
      title,
      rules: rules.map(({ r }) => r),
    })),
    icons: vals.icons.map(({ name, ko }) => ({ name, ko })),
  };
}

/** 첫 탐색 v3 의 디자인 파일을 읽는다. 디자인 토큰 JSON, 대응표, 상태용 토큰, 컴포넌트 표를 돌려준다. */
export function readDesign(path = DESIGN_FILE) {
  const vals = renderVals(path, { theme: "먹", mode: "라이트" });
  return {
    tokens: JSON.parse(vals.tokJson),
    tables: vals.themes.map((theme) => ({
      name: theme.name,
      font: theme.fontLine,
      mono: theme.mono,
      modes: theme.modes.map((mode) => ({
        label: mode.label,
        rows: mode.rows.map(({ code, prim, hex, ratio, pass }) => ({ code, prim, hex, ratio, pass })),
      })),
    })),
    stateTokens: vals.stateTokens.map(({ code, use, l, lNote, d, dNote, pairTxt, ratio, pass }) => ({
      code,
      use,
      light: l,
      lightOverride: lNote,
      dark: d,
      darkOverride: dNote,
      pairs: pairTxt,
      ratio,
      pass,
    })),
    components: vals.comps.map((comp) => ({
      code: comp.code,
      name: comp.name,
      element: comp.el,
      variants: comp.variants,
      sizes: comp.sizes,
      states: comp.states.map((row) => ({ state: row.st, none: row.na, tokens: row.tok.map((t) => t.t), note: row.note })),
      parts: comp.parts.map(({ part, tok, val }) => ({ part, tok, val })),
      props: comp.props,
    })),
    icons: vals.icons.map(({ n, code }) => ({ name: n, code })),
  };
}

/** 쓰임새 토큰의 이름(그림자 색 빼고 26개). */
export function semanticNames(tokens) {
  return Object.keys(tokens.themes.muk.semantic.light).filter((name) => name !== "shadow");
}

/** 한 테마·모드에서 쓰임새 토큰마다 가리키는 원색 토큰의 hex(대문자). setup 의 기대값과 measure 의 대조가 함께 쓴다. */
export function expectedSemantic(tokens, theme, mode) {
  const t = tokens.themes[theme];
  return Object.fromEntries(
    semanticNames(tokens).map((name) => {
      const [family, step] = t.semantic[mode][name].split(/-(?=\d+$)/);
      return [name, t.primitive[family][step].toUpperCase()];
    }),
  );
}

function printRefresh(design) {
  const { tokens } = design;
  const themes = Object.keys(tokens.theme);
  console.log(
    `기본 테마 ${tokens.defaultTheme}, 모드 ${tokens.defaultMode}, 밀도 ${tokens.defaultDensity}. 테마 ${themes.join(", ")}`,
  );
  for (const key of themes) {
    const theme = tokens.theme[key];
    const families = Object.entries(theme.primitive)
      .map(([family, steps]) => `${family}(${Object.keys(steps).length})`)
      .join(" ");
    const semantic = Object.keys(theme.semantic.light);
    console.log(
      `${key} ${theme.name} 글꼴 ${theme.font.sans}/${theme.font.mono} 원색 ${families} 쓰임새 ${String(semantic.length)}`,
    );
  }
  for (const [name, density] of Object.entries(tokens.density)) {
    console.log(`밀도 ${name} ${JSON.stringify(density)}`);
  }
  for (const table of design.themeTables) {
    const judged = table.rows.filter((row) => row.pass !== "" && row.pass !== "면제");
    const failed = judged.filter((row) => row.pass === "미달");
    console.log(
      `${table.key} 판정 ${String(judged.length)} 미달 ${String(failed.length)} :: ${judged.map((row) => `${row.token} ${row.ratio}`).join(" | ")}`,
    );
  }
  console.log(`디자인 파일: ${join(REFRESH_FILE)}`);
}

if (process.argv[1] !== undefined && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const refresh = process.argv.includes("--refresh");
  const design = refresh ? readRefresh() : readDesign();
  const outIndex = process.argv.indexOf("--out");
  if (outIndex !== -1) {
    writeFileSync(resolve(process.argv[outIndex + 1]), `${JSON.stringify(design, null, 2)}\n`);
  }
  if (refresh) {
    printRefresh(design);
    process.exit(0);
  }
  for (const table of design.tables) {
    for (const mode of table.modes) {
      const failed = mode.rows.filter((row) => row.pass.startsWith("✕"));
      const lowest = mode.rows
        .filter((row) => row.pass.trim() !== "")
        .map((row) => `${row.code} ${row.ratio}`)
        .join(" | ");
      console.log(`${table.name} ${mode.label} 실패 ${String(failed.length)} :: ${lowest}`);
    }
  }
  for (const state of design.stateTokens) {
    console.log(`${state.code} L ${state.light} D ${state.dark} :: ${state.ratio} ${state.pass}`);
  }
  console.log(`디자인 파일: ${join(DESIGN_FILE)}`);
}
