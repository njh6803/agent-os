// 레지스트리 프로브. 설치한 판이 나온 날짜와, 재는 날의 최신 판과 그 날짜를 npm 공식 레지스트리에서 읽는다.
//
// 돌리기: node probe/registry.mjs
// 산출물: out/registry/summary.json, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 바깥에 보내는 것은 `https://registry.npmjs.org/<패키지 이름>` 읽기 요청 다섯이다. 패키지 이름 말고는 싣지 않는다.
// 설치한 판은 node_modules 의 package.json 에서 읽는다(package.json 에 적은 판과 같은지도 본다).
//
// 측정이 아닌 회차: 응답이 200 이 아니거나, 문서의 `time` 에 설치한 판의 날짜가 없거나, 최신 판(`dist-tags.latest`)이나
// 그 날짜가 없거나, 설치된 판이 package.json 에 적은 판과 다르면 그 패키지는 센 것이 아니다. 종료 코드 1.
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = join(ROOT, "out", "registry");
const PACKAGES = ["openid-client", "oauth4webapi", "jose", "oidc-provider", "@types/oidc-provider"];
const readJson = (path) => JSON.parse(readFileSync(path, "utf8"));

async function main() {
  mkdirSync(OUT, { recursive: true });
  const declared = readJson(join(ROOT, "package.json"));
  const pinned = { ...declared.dependencies, ...declared.devDependencies };
  const rows = [];
  const notMeasured = [];
  for (const name of PACKAGES) {
    const installed = readJson(join(ROOT, "node_modules", ...name.split("/"), "package.json")).version;
    const response = await fetch(`https://registry.npmjs.org/${name.replace("/", "%2F")}`);
    if (response.status !== 200) {
      notMeasured.push({ name, problem: `레지스트리 응답이 ${String(response.status)} 이다` });
      continue;
    }
    const document = await response.json();
    const published = document.time?.[installed];
    const latest = document["dist-tags"]?.latest;
    const latestPublished = typeof latest === "string" ? document.time?.[latest] : undefined;
    if (typeof published !== "string") notMeasured.push({ name, problem: `time 에 ${installed} 가 없다` });
    if (typeof latestPublished !== "string") notMeasured.push({ name, problem: `최신 판(${String(latest)})이나 그 날짜가 문서에 없다` });
    if (pinned[name] !== installed) notMeasured.push({ name, problem: `설치된 ${installed} 가 적은 ${String(pinned[name])} 와 다르다` });
    rows.push({
      name,
      installed,
      published: published ?? null,
      license: document.versions?.[installed]?.license ?? null,
      unpackedSize: document.versions?.[installed]?.dist?.unpackedSize ?? null,
      latest,
      latestPublished: latestPublished ?? null,
      isLatest: latest === installed,
    });
  }
  const summary = { probe: "registry", readAt: new Date().toISOString(), notMeasured, rows };
  writeFileSync(join(OUT, "summary.json"), JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary));
  if (notMeasured.length > 0) process.exit(1);
}

await main();
