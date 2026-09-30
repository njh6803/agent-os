// 켜고 끄기의 401 뒤에 목록을 다시 읽지 않는 까닭을 잰다(티켓 06). 훅(`useSetPluginEnabled`)은 성공이든 실패든
// `finally` 에서 목록의 다시 읽기를 청한다. 401 이면 관리 토큰을 내려놓으므로, 그 `finally` 에 닿을 때 목록이 이미
// 화면에서 걷혔다면 SWR 의 mutate 는 걷힌 키를 읽지 않는다. 그 순간 문서에 스위치가 몇 개인지 찍어 본다.
//
// 훅의 `finally` 첫 줄에 표준 에러로 찍는 줄을 넣고, 켜고 끄기 절의 페이지 테스트를 돌린 뒤, 원래 바이트를 그대로
// 쓴다. `console` 로 찍은 줄은 Vitest 의 출력에 나오지 않아(까닭은 재지 않았다) `process.stderr.write` 를 쓴다.
//
// 쓰는 법: node .scratch/web-admin/probes/switch_after_rejection.mjs   (저장소 루트에서. 명령은 web/ 에서 돈다)
// 네트워크를 타지 않는다. 약 20초. 켜고 끄기 한 번마다 `PROBE switches-at-finally=<수> token-field=<true|false>` 를
// 찍는다. 관리 토큰을 넣는 칸이 선 줄(401 을 받아 토큰을 내려놓은 경우)은 스위치가 0 이고, 나머지 줄은 0 이 아니면
// 종료 0 이다. 결과는 README 의 이 행에 적는다.

import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const WEB = join(process.cwd(), "web");
const HOOKS = join(WEB, "apps/admin/hooks/queries/plugins/index.ts");
const ANCHOR = "      } finally {\n        await Promise.all([";
const MEASURE = [
  "const switches = String(document.querySelectorAll('[role=switch]').length);",
  "const field = String(document.querySelector('input[type=password]') !== null);",
  "process.stderr.write('PROBE switches-at-finally=' + switches + ' token-field=' + field + '\\n');",
].join(" ");
const PROBED = `      } finally {\n        { ${MEASURE} }\n        await Promise.all([`;

const original = readFileSync(HOOKS);
const text = original.toString("utf-8");
if (text.split(ANCHOR).length !== 2) {
  console.log(`원문이 ${HOOKS} 에 정확히 한 번 있지 않다`);
  process.exit(2);
}

let output = "";
try {
  writeFileSync(HOOKS, text.replace(ANCHOR, PROBED));
  const result = spawnSync(
    "pnpm exec vitest run --project pages apps/admin/components/pages/HomePage.test.tsx -t 켜고",
    { cwd: WEB, shell: true, encoding: "utf-8" },
  );
  output = `${result.stdout}${result.stderr}`;
} finally {
  writeFileSync(HOOKS, original);
}

const lines = output.split("\n").filter((line) => line.startsWith("PROBE "));
for (const line of lines) {
  console.log(line);
}
const rejected = lines.filter((line) => line.includes("token-field=true"));
const others = lines.filter((line) => line.includes("token-field=false"));
const ok =
  rejected.length === 1 &&
  rejected.every((line) => line.includes("switches-at-finally=0 ")) &&
  others.length > 0 &&
  others.every((line) => !line.includes("switches-at-finally=0 "));
console.log(ok ? "401 뒤에만 목록이 걷혀 있었다" : "기대와 다르다");
process.exit(ok ? 0 : 1);
