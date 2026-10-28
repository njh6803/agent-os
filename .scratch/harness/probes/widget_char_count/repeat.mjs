// 위젯 승인 시험의 "사유가 상한의 90% 이상이면 …" 사례가 가끔 빨간 까닭을 가르는 재현 루프(harness 티켓 023, 대기열 486).
//
// 그 사례를 그대로 따라 하는 사례를 원래 시험 파일의 사본 끝에 붙여 Vitest 의 `repeats` 로 되풀이하고, 회차마다
// 붙여 넣기 앞뒤의 포커스 자리(document.activeElement)와 사유 칸의 값(코드 포인트 수, UTF-16 길이), 선택 범위,
// 칸이 같은 요소인지, 센 수가 보이는지를 한 줄 JSON 으로 찍는다. 붙인 사례는 단언하지 않고 찍기만 한다.
//
// 가르는 해석은 셋이다.
// - 포커스: 카드의 첫 그리기 뒤 효과가 포커스를 제목으로 옮기는데, 그 효과가 시험이 칸에 포커스를 준 뒤에 돌아
//   붙여 넣기가 칸이 아닌 제목에 간다. 표지는 붙여 넣는 순간의 포커스가 칸이 아니고 값이 붙인 만큼 늘지 않은 회차다.
// - 선택: 붙여 넣기가 이모지의 두 UTF-16 단위 사이에 들어가 짝이 깨진다. 표지는 포커스가 칸이고 코드 포인트 수가
//   18,000 이 아닌 회차다(짝이 깨지면 하나가 둘로 세여 18,001 이다).
// - 다시 그리기: 카드가 다시 서며 칸의 상태를 잃는다. 표지는 두 번째 붙여 넣기 뒤의 칸이 처음 잡은 칸과 다른 요소다.
// 셋 가운데 어느 것도 아닌 빨간 회차는 "기타"로 따로 센다.
//
// 붙인 사례는 시험 파일의 도우미(`untilPaused` 등)를 그대로 부른다. 그래서 `--source <커밋>` 으로 고치기 전 커밋의
// 시험 파일을 사본의 바탕으로 주면 고치기 전의 도우미를, 주지 않으면 작업 트리의 고친 도우미를 잰다.
// 사본의 `untilPaused` 안에서 카드를 찾은 바로 뒤에 포커스 자리(`afterCard`)를 적는 줄을 끼운다. 고치기 전 도우미는
// 거기서 끝나므로 `afterCard` 와 `afterPaused` 가 같고, 고친 도우미는 그 뒤에 제목의 포커스를 기다린다.
// 요약 줄의 `afterCardOnRed`·`afterCardOnGreen` 은 그 자리를 빨간·초록 회차로 나눠 센다. 포커스 해석이 맞으면 고치기
// 전 판의 빨간 회차는 카드의 효과가 아직 돌지 않아 포커스가 요청 입력창(textarea)에 남은 회차다.
// `lateEffect` 는 `afterCard` 가 카드 제목이 아닌 회차(효과가 늦은 회차) 수이고 `lateEffectGreen` 은 그 가운데 초록인 수다.
// 고친 판에서는 이것이 고친 길(제목의 포커스를 기다림)을 지났다는 표지다. 다만 고치기 전 판이라면 반드시 빨갰을
// 회차는 아니다. 효과가 시험의 포커스·클릭보다 먼저 돌면 고치기 전 판도 초록이고, 빨간 것은 그 뒤에 돈 회차뿐이다.
// 고치기 전 판을 잰 300회차에서는 효과가 늦은 12회차가 모두 빨갰다(이 프로브의 출력). 그래서 측정에 기댄 표지다.
// `redShapes` 는 빨간 회차를 카드 직후 포커스·붙여 넣기 앞뒤 포커스·칸의 코드 포인트 수·같은 요소인지로 묶어 센다.
//
// 돌리는 법: 저장소 루트에서 `node .scratch/harness/probes/widget_char_count/repeat.mjs [회차=200] [--source <커밋>]`.
// web 의존성이 깔려 있어야 한다(`pnpm -C web install`). 사본은 web/apps/widget/components/pages/ 에 잠깐 쓰고
// 끝나면 지운다(Vitest 의 widget-pages 프로젝트가 그 아래만 jsdom 으로 돌린다).
// 찍은 줄이 회차 수보다 적으면 측정이 아닌 회차가 있는 것이라 1 로 끝난다.

import { execFileSync, spawnSync } from "node:child_process";
import { readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const args = process.argv.slice(2);
const at = args.indexOf("--source");
const rev = at >= 0 ? (args[at + 1] ?? null) : null;
if (at >= 0 && (rev === null || rev.startsWith("--"))) {
  console.log("--source 뒤에 커밋을 준다");
  process.exit(2);
}
const rounds = Number(args.find((a, i) => !a.startsWith("--") && (at < 0 || i !== at + 1)) ?? "200");

const pages = join("web", "apps", "widget", "components", "pages");
const source =
  rev === null
    ? readFileSync(join(pages, "WidgetApproval.test.tsx"), "utf8")
    : execFileSync("git", ["show", `${rev}:web/apps/widget/components/pages/WidgetApproval.test.tsx`], { encoding: "utf8" });
const copy = join(pages, "ProbeCharCount.test.tsx");
const name = "PROBE_CHAR_COUNT";
// 회차마다 붙인 사례가 한 줄씩 덧붙이는 기록. Vitest 가 jsdom 사례의 console 출력을 이 실행의 stdout 에 싣지 않아 파일로 받는다.
const out = join(tmpdir(), `widget-char-count-${process.pid}.jsonl`).replaceAll("\\", "/");

// 카드를 찾는 줄. 사본의 `untilPaused` 에서 이 줄 뒤에 `afterCard` 를 적는다. 바탕 파일에 없으면 잴 수 없어 멈춘다.
const cardWait = 'await screen.findByRole("group", { name: "승인 묻기" });';
const helperAt = source.indexOf("async function untilPaused(");
const cardAt = source.indexOf(cardWait, helperAt);
if (helperAt < 0 || cardAt < 0) {
  console.log("바탕 파일의 untilPaused 에서 카드를 찾는 줄을 찾지 못했다");
  process.exit(2);
}
const patched = source.slice(0, cardAt + cardWait.length) + "\n  probeAfterCard = probeWhere();" + source.slice(cardAt + cardWait.length);

const probeCase = `
let probeAfterCard = "unset";

function probeWhere(): string {
  const el = document.activeElement;
  if (el === null) return "null";
  if (el === reasonBox()) return "reason";
  return el.tagName.toLowerCase() + ":" + (el.textContent ?? "").slice(0, 20);
}

function probeBox() {
  const box = reasonBox();
  if (!(box instanceof HTMLTextAreaElement) && !(box instanceof HTMLInputElement)) {
    return { kind: box.tagName };
  }
  return {
    points: Array.from(box.value).length,
    units: box.value.length,
    selection: [box.selectionStart, box.selectionEnd],
  };
}

test(${JSON.stringify(name)}, { repeats: ${rounds - 1} }, async () => {
  serveTokens();
  onStart(pausedStart());
  const user = openWidget();
  probeAfterCard = "unset";
  await untilPaused(user);
  const afterCard = probeAfterCard;
  const box = reasonBox();
  const afterPaused = probeWhere();
  reasonBox().focus();
  const afterFocus = probeWhere();
  await user.paste("😀".repeat(17_999));
  const first = { where: probeWhere(), ...probeBox() };
  const beforeSecond = probeWhere();
  await user.paste("😀");
  const second = { where: probeWhere(), ...probeBox() };
  const shown = within(card()).queryByText("18,000 / 20,000") !== null;
  const same = reasonBox() === box;
  appendFileSync(${JSON.stringify(out)}, JSON.stringify({ afterCard, afterPaused, afterFocus, first, beforeSecond, second, same, shown }) + "\\n");
});
`;

writeFileSync(out, "");
writeFileSync(copy, `import { appendFileSync } from "node:fs";\n${patched}${probeCase}`);
let result;
try {
  result = spawnSync(
    "pnpm",
    ["-C", "web", "exec", "vitest", "run", "--project", "widget-pages", "apps/widget/components/pages/ProbeCharCount.test.tsx", "-t", name],
    { encoding: "utf8", shell: true, maxBuffer: 256 * 1024 * 1024 },
  );
} finally {
  rmSync(copy, { force: true });
}

const records = readFileSync(out, "utf8")
  .split("\n")
  .filter((line) => line !== "")
  .map((line) => JSON.parse(line));
rmSync(out, { force: true });

const title = "span:승인이 필요합니다";
const tally = { green: 0, focus: 0, selection: 0, remount: 0, other: 0, lateEffect: 0, lateEffectGreen: 0 };
const afterCardOnRed = {};
const afterCardOnGreen = {};
const redShapes = {};
const reds = [];
const bump = (map, key) => {
  map[key] = (map[key] ?? 0) + 1;
};
for (const r of records) {
  bump(r.shown ? afterCardOnGreen : afterCardOnRed, r.afterCard);
  if (r.afterCard !== title) {
    tally.lateEffect += 1;
    if (r.shown) tally.lateEffectGreen += 1;
  }
  if (!r.shown) {
    bump(
      redShapes,
      [r.afterCard, r.afterFocus, r.first.where, r.first.points, r.beforeSecond, r.second.where, r.second.points, r.same].join(" | "),
    );
  }
  if (r.shown) {
    tally.green += 1;
    continue;
  }
  reds.push(r);
  if (!r.same) tally.remount += 1;
  else if (r.first.where !== "reason" || r.beforeSecond !== "reason" || r.second.where !== "reason") tally.focus += 1;
  else if (r.second.points !== 18_000) tally.selection += 1;
  else tally.other += 1;
}

console.log(
  JSON.stringify({ source: rev ?? "작업 트리", rounds, measured: records.length, ...tally, afterCardOnRed, afterCardOnGreen }),
);
console.log("redShapes (afterCard | afterFocus | first.where | first.points | beforeSecond | second.where | second.points | same):");
console.log(JSON.stringify(redShapes, null, 1));
for (const r of reds.slice(0, 5)) console.log(JSON.stringify(r));
if (records.length !== rounds) {
  console.log(`측정이 아닌 회차: ${rounds - records.length}`);
  console.log(result.stdout.slice(-3000));
  process.exit(1);
}
