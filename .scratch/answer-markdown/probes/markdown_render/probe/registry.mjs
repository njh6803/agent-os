// 레지스트리 프로브(B1 의 보탬). 설치한 판이 언제 나왔고 그 뒤로 얼마나 자주 새 판이 나오는지 본다. 공급망 유예
// (pnpm 의 minimumReleaseAge, 예외를 두지 않는다는 ADR 0024)와 잠금 파일이 얼마나 자주 흔들릴지의 근거다.
//
// 돌리기: node probe/registry.mjs      (레지스트리 https://registry.npmjs.org/ 에 패키지마다 읽기 요청 하나를 보낸다)
// 산출물: out/registry/summary.json, 표준 출력의 마지막 줄(JSON 한 줄)
//
// 조회 대상은 둘로 가른다.
// - INSTALLED: 프로브에 직접 설치한 패키지다. 설치한 판(node_modules/<이름>/package.json)의 나온 시각을 잰다.
// - LOOKUP_ONLY: 설치하지 않고 이름만 견주는 패키지다(remark-cjk-friendly 와 이름이 비슷한 것). latest 의 시각을 잰다.
//
// 측정이 아닌 회차(.claude/rules/probes.md): 패키지마다 한 회차다. 아래 가운데 하나면 그 패키지는 잰 것이 아니다.
// - 요청이 던졌다(연결 실패, 제한 시간). 요청마다 `AbortSignal.timeout` 을 걸어 응답이 멈춰도 끝없이 기다리지 않는다.
//   신호는 본문을 읽는 동안에도 걸린다(머리만 보내고 멈춘 서버는 registry-selftest.mjs 의 body-stall 갈래가 본다).
// - 응답이 2xx 가 아니다, 본문이 JSON 이 아니다, 재려는 판의 시각이 문서에 없다.
// 측정이 아닌 회차가 있어도 그때까지 모은 회차는 summary.json 에 쓰고, 하나라도 있으면 종료 코드 1 이다.
// 이 길(던짐, 제한 시간, 모은 회차를 쓰는 것)이 실제로 도는지는 registry-selftest.mjs 가 가짜 레지스트리로 본다.
//
// 환경 변수(자가 시험이 쓴다. 보통은 주지 않는다)
// - MD_PROBE_REGISTRY: 레지스트리 주소(기본 https://registry.npmjs.org)
// - MD_PROBE_REGISTRY_TIMEOUT_MS: 요청마다의 제한 시간(기본 15000)
// - MD_PROBE_REGISTRY_OUT: 산출물 폴더(기본 out/registry)
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const OUT = process.env.MD_PROBE_REGISTRY_OUT ?? join(ROOT, "out", "registry");
const REGISTRY = (process.env.MD_PROBE_REGISTRY ?? "https://registry.npmjs.org").replace(/\/+$/, "");
const TIMEOUT_MS = Number(process.env.MD_PROBE_REGISTRY_TIMEOUT_MS ?? "15000");
const INSTALLED = ["react-markdown", "remark-gfm", "markdown-to-jsx", "marked", "remark-breaks", "remark-cjk-friendly"];
const LOOKUP_ONLY = [
  "remark-cjk-friendly-gfm-strikethrough",
  "micromark-extension-cjk-friendly",
  "markdown-it-cjk-friendly",
];
const DAY = 24 * 60 * 60 * 1000;

/** 던진 까닭을 한 줄로 낸다. undici 는 연결 실패의 까닭을 `cause` 에 둔다. */
function reasonOf(error) {
  if (error instanceof Error) {
    if (error.name === "TimeoutError") return `제한 시간(${TIMEOUT_MS}ms)을 넘겼다`;
    const cause = error.cause instanceof Error ? ` (${error.cause.code ?? error.cause.name}: ${error.cause.message})` : "";
    return `요청이 던졌다: ${error.name}: ${error.message}${cause}`;
  }
  return `요청이 던졌다: ${String(error)}`;
}

/** 패키지 하나를 조회한다. 잰 것이면 `{ row }`, 아니면 `{ notMeasured }` 다. 던지지 않는다. */
async function lookup(name, installed, now) {
  let doc;
  try {
    const response = await fetch(`${REGISTRY}/${name}`, { signal: AbortSignal.timeout(TIMEOUT_MS) });
    if (!response.ok) {
      await response.body?.cancel();
      return { notMeasured: { name, reason: `응답이 ${response.status} 이다` } };
    }
    doc = await response.json();
  } catch (error) {
    return { notMeasured: { name, reason: reasonOf(error) } };
  }
  const latest = doc?.["dist-tags"]?.latest;
  const measuredVersion = installed ?? latest;
  const releasedAt = doc?.time?.[measuredVersion];
  if (typeof measuredVersion !== "string" || typeof releasedAt !== "string") {
    return { notMeasured: { name, reason: installed === null ? "latest 의 시각이 없다" : "설치한 판의 시각이 없다" } };
  }
  const stable = Object.entries(doc.time)
    .filter(([version]) => /^\d+\.\d+\.\d+$/.test(version))
    .map(([version, at]) => ({ version, at }))
    .sort((a, b) => a.at.localeCompare(b.at));
  const within = (days) => stable.filter((r) => now - Date.parse(r.at) <= days * DAY).length;
  const manifest = doc.versions?.[measuredVersion] ?? {};
  return {
    row: {
      name,
      installed,
      measuredVersion,
      installedReleasedAt: releasedAt,
      installedAgeDays: Math.floor((now - Date.parse(releasedAt)) / DAY),
      latest,
      latestReleasedAt: doc.time?.[latest],
      distTags: doc["dist-tags"],
      stableReleasesLast90Days: within(90),
      stableReleasesLast365Days: within(365),
      license: manifest.license ?? null,
      dependencies: manifest.dependencies ?? {},
      peerDependencies: manifest.peerDependencies ?? {},
      lastFive: stable.slice(-5),
    },
  };
}

async function main() {
  mkdirSync(OUT, { recursive: true });
  const now = Date.now();
  const rows = [];
  const notMeasured = [];
  const targets = [
    ...INSTALLED.map((name) => ({ name, lookupOnly: false })),
    ...LOOKUP_ONLY.map((name) => ({ name, lookupOnly: true })),
  ];
  for (const { name, lookupOnly } of targets) {
    let installed = null;
    if (!lookupOnly) {
      try {
        installed = JSON.parse(readFileSync(join(ROOT, "node_modules", name, "package.json"), "utf8")).version;
      } catch (error) {
        notMeasured.push({ name, reason: `설치한 판을 읽지 못했다: ${String(error)}` });
        continue;
      }
    }
    const result = await lookup(name, installed, now);
    if (result.row === undefined) notMeasured.push(result.notMeasured);
    else rows.push(result.row);
  }
  const at = new Date(now).toISOString();
  writeFileSync(
    join(OUT, "summary.json"),
    JSON.stringify({ at, registry: REGISTRY, timeoutMs: TIMEOUT_MS, expected: targets.length, notMeasured, rows }, null, 2),
  );
  console.log(
    JSON.stringify({
      probe: "registry",
      at,
      registry: REGISTRY,
      expected: targets.length,
      measured: rows.length,
      notMeasured,
      rows: rows.map(({ lastFive, distTags, dependencies, peerDependencies, ...row }) => ({
        ...row,
        dependencies: Object.keys(dependencies).length,
      })),
    }),
  );
  if (notMeasured.length > 0) process.exitCode = 1;
}

await main();
