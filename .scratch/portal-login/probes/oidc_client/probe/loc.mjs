// 코드 분량 프로브. 프로브의 `.ts` 파일마다 줄 수를 센다.
//
// 돌리기: node probe/loc.mjs
// 산출물: 표준 출력의 마지막 줄(JSON 한 줄)
//
// 세는 법: 전체 줄, 빈 줄, 주석만 있는 줄(`//` 로 시작하거나 `/**`·`*`·`*/` 로 시작하는 줄), 그 둘을 뺀 코드 줄.
// 코드 뒤에 붙은 주석은 코드 줄로 센다. 후보의 "코드 줄"은 그 후보의 파일 하나의 것이고, 세 후보가 함께 쓰는
// `contract.ts` 와 `node-fetch.ts`(전역 fetch 를 바꿔 끼울 때만 든다)는 따로 적는다.
// 측정이 아닌 회차: 파일을 읽지 못하면 예외로 끝난다(종료 코드 1).
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const FILES = {
  "가 openid-client": "server/oidc/openid-client.ts",
  "나 oauth4webapi + jose": "server/oidc/oauth4webapi.ts",
  "다 직접 구현": "server/oidc/hand.ts",
  "함께 쓰는 모양": "server/oidc/contract.ts",
  "node:http 로 낸 fetch 모양 함수": "server/oidc/node-fetch.ts",
  "ㄱ 직접 만든 가짜 서버": "testing/fake-idp.ts",
  "ㄴ oidc-provider 를 띄우는 코드": "testing/fake-idp-provider.ts",
  "브라우저 몫(두 가짜 서버가 함께 쓴다)": "testing/browser.ts",
  "회차 진입점": "testing/round.ts",
};

const rows = Object.entries(FILES).map(([name, path]) => {
  const lines = readFileSync(join(ROOT, "apps", "portal", ...path.split("/")), "utf8").replaceAll("\r\n", "\n").replace(/\n$/, "").split("\n");
  const blank = lines.filter((line) => line.trim() === "").length;
  const comment = lines.filter((line) => /^(\/\/|\/\*\*|\*\/|\*( |$))/.test(line.trim())).length;
  return { name, path, total: lines.length, blank, comment, code: lines.length - blank - comment };
});
for (const row of rows) console.log(`${row.name}\t${row.path}\t전체 ${String(row.total)}\t코드 ${String(row.code)}`);
console.log(JSON.stringify({ probe: "loc", rows }));
