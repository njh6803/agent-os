// 티켓 06(플러그인 하나와 켜고 끄기)의 TS 변이. 이 티켓의 테스트가 무엇을 재는지 본다.
//
// 페이지 테스트는 페이지와 스위치가 서기 전에 빨갰지만(모듈이 없다, 스위치가 없다), 그 빨강은 각 테스트가 지키는 행동의
// 빨강이 아니다. 구현 뒤에 쓴 테스트(실패의 표시, 401, 새로 고침, 다시 확인하는 중, 다시 읽다 실패, 키의 횟수)는 빨강을
// 본 적이 없다. 그래서 행동마다 제품 코드에 변이를 넣어 그 행동을 지키는 테스트가 빨간지 본다. 플러그인 하나(들여 적기,
// 켜짐, 실패, 추적 식별자, 401, 새로 고침, 작은 표시, 키의 횟수, 종류 검사, 목록 링크), 켜고 끄기(먼저 뒤집기, 다시
// 읽을 때까지 막기, 목록과 그 행의 다시 읽기, 401, 방향, 204, 목록 자리의 실패 표시와 걷기, 표지 행), 목록의 링크,
// 그리고 e2e 로만 잡히는 것(라우트가 조각을 넘기는 것, 스위치가 실제 serve 에 쓰는 값)이다.
//
// 규약은 `admin_pages_mutations.mjs` 와 같다. 원문이 파일에 정확히 한 번 있는지 먼저 보고(하나라도 틀리면 아무것도
// 쓰지 않는다), 변이 없이 명령이 초록인지 기준선을 본 뒤, 변이마다 원래 바이트를 쥐고 넣어 돌리고 finally 에서 그
// 바이트를 쓴다. Vitest 는 실패한 테스트가 셀 때만, Playwright 는 실패한 테스트가 셀 때만 빨강이다. 그 밖의
// 비초록(수집 오류, 준비 실패)은 오류다.
//
// 쓰는 법: node .scratch/web-admin/probes/plugin_toggle_mutations.mjs [이름 ...]   (저장소 루트에서. 명령은 web/ 에서 돈다)
// 네트워크를 타지 않는다. e2e 변이는 앱을 빌드하고 serve 를 띄운다(약 30초). 종료 코드: 모두 기대대로면 0, 어긋나거나
// 기준선이 초록이 아니면 1, 원문이 틀리거나 없는 이름을 주면 2.

import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const WEB = join(process.cwd(), "web");
const DETAIL_PAGE =
  "pnpm exec vitest run --project pages apps/admin/components/pages/PluginPage.test.tsx";
const HOME_PAGE =
  "pnpm exec vitest run --project pages apps/admin/components/pages/HomePage.test.tsx";
const E2E = "pnpm -C apps/admin exec playwright test";
const HOOKS = "apps/admin/hooks/queries/plugins/index.ts";
const API = "apps/admin/api/plugins/index.ts";
const LIST = "apps/admin/components/organisms/PluginList.tsx";
const DETAIL = "apps/admin/components/organisms/PluginDetail.tsx";
const PAGE = "apps/admin/components/pages/PluginPage.tsx";
const ROUTE = "apps/admin/app/plugins/[kind]/[name]/page.tsx";
// (2026-09-30, 티켓 07) 새로 고침과 실패의 표시는 읽기 골격으로, 주소의 조각을 푸는 것은 화면 둘이 함께 쓰는 자리로
// 옮겼다. 변이는 옮긴 자리에 넣고 명령은 그대로다.
const SECTION = "apps/admin/components/organisms/ReadSection.tsx";
const SEGMENT = "apps/admin/components/pages/segment.ts";

const MUTATIONS = [
  // ---- 플러그인 하나 ----
  {
    name: "매니페스트를 들여 적지 않는다",
    file: DETAIL,
    old: "JSON.stringify(plugin.manifest, null, 2)",
    new: "JSON.stringify(plugin.manifest)",
    command: DETAIL_PAGE,
  },
  {
    name: "플러그인 하나의 켜짐을 거꾸로 보인다",
    file: DETAIL,
    old: '<p>{plugin.enabled ? "켜짐" : "꺼짐"}</p>',
    new: '<p>{plugin.enabled ? "꺼짐" : "켜짐"}</p>',
    command: DETAIL_PAGE,
  },
  {
    name: "플러그인 하나의 실패에 추적 식별자를 싣지 않는다",
    file: SECTION,
    old: "<FailureNotice {...describeFailure(error)} />",
    new: "<FailureNotice message={describeFailure(error).message} requestId={null} />",
    command: DETAIL_PAGE,
  },
  {
    name: "다시 읽다 실패해도 보인 매니페스트를 둔다",
    file: SECTION,
    old: "{error !== undefined ? (",
    new: "{error !== undefined && data === undefined ? (",
    command: DETAIL_PAGE,
  },
  {
    name: "플러그인 하나의 401 에 관리 토큰을 내려놓지 않는다",
    file: HOOKS,
    old: ": () => orRejectAdminToken(adminToken, (token) => readPlugin(token, kind, name)),",
    new: ": () => readPlugin(adminToken, kind, name),",
    command: DETAIL_PAGE,
  },
  {
    name: "플러그인 하나의 새로 고침 버튼이 다시 읽지 않는다",
    file: DETAIL,
    old: "        void mutate();",
    new: "        void 0;",
    command: DETAIL_PAGE,
  },
  {
    name: "플러그인 하나를 다시 확인하는 중을 보이지 않는다",
    file: SECTION,
    old: '{shown && isValidating ? <span role="status">다시 확인하는 중</span> : null}',
    new: "{null}",
    command: DETAIL_PAGE,
  },
  {
    name: "플러그인 하나의 키에 토큰을 받아들인 횟수를 싣지 않는다",
    file: HOOKS,
    old: '    ["plugins", generation, kind, name] as const,',
    new: '    ["plugins", kind, name] as const,',
    command: DETAIL_PAGE,
  },
  {
    name: "주소의 종류를 가리지 않는다",
    file: API,
    old: "  return Object.hasOwn(KINDS, value);",
    new: "  return true;",
    command: DETAIL_PAGE,
  },
  {
    name: "목록으로 가는 링크가 첫 화면이 아니다",
    file: PAGE,
    old: '<Link href="/">플러그인 목록으로</Link>',
    new: '<Link href="/plugins">플러그인 목록으로</Link>',
    command: DETAIL_PAGE,
  },
  {
    name: "주소의 조각을 풀지 않는다",
    file: SEGMENT,
    old: "    return decodeURIComponent(segment);",
    new: "    return segment;",
    command: DETAIL_PAGE,
  },
  {
    name: "풀 수 없는 조각에도 요청을 보낸다",
    file: SEGMENT,
    old: "  } catch {\n    return null;\n  }",
    new: "  } catch {\n    return segment;\n  }",
    command: DETAIL_PAGE,
  },
  // ---- 목록의 링크 ----
  {
    name: "링크가 이름을 조각으로 적지 않는다",
    file: LIST,
    old: "encodeURIComponent(row.name)",
    new: "row.name",
    command: HOME_PAGE,
  },
  // ---- 켜고 끄기 ----
  {
    name: "스위치를 먼저 뒤집어 둔다",
    file: LIST,
    old: "        checked={row.enabled}",
    new: "        checked={pending ? !row.enabled : row.enabled}",
    command: HOME_PAGE,
  },
  {
    name: "응답까지 스위치를 막지 않는다",
    file: LIST,
    old: "        disabled={pending}",
    new: "        disabled={false}",
    command: HOME_PAGE,
  },
  {
    name: "표지 행의 스위치를 막는다",
    file: LIST,
    old: "        disabled={pending}",
    new: '        disabled={pending || "reason" in row}',
    command: HOME_PAGE,
  },
  {
    name: "누른 행의 켜짐을 그대로 보낸다",
    file: LIST,
    old: "await setEnabled(row.kind, row.name, !row.enabled);",
    new: "await setEnabled(row.kind, row.name, row.enabled);",
    command: HOME_PAGE,
  },
  {
    name: "끄기만 보낸다",
    file: LIST,
    old: "await setEnabled(row.kind, row.name, !row.enabled);",
    new: "await setEnabled(row.kind, row.name, false);",
    command: HOME_PAGE,
  },
  {
    name: "켜고 끄기의 실패를 보이지 않는다",
    file: LIST,
    old: "{switchFailure === null ? null : <FailureNotice {...switchFailure} />}",
    new: "{null}",
    command: HOME_PAGE,
  },
  {
    name: "켜고 끈 뒤 목록을 다시 읽지 않는다",
    file: HOOKS,
    old: "          mutate(pluginKeys.list(generation)),\n",
    new: "",
    command: HOME_PAGE,
  },
  {
    name: "성공 뒤에만 목록과 그 행을 다시 읽는다",
    file: HOOKS,
    old: "      } finally {\n        // mutate 는",
    new: "      } catch (error: unknown) {\n        throw error;\n      }\n      {\n        // mutate 는",
    command: HOME_PAGE,
  },
  {
    name: "다시 읽기를 기다리지 않고 스위치를 푼다",
    file: HOOKS,
    old: "        await Promise.all([",
    new: "        void Promise.all([",
    command: HOME_PAGE,
  },
  {
    name: "켜고 끈 뒤 그 행의 캐시를 둔다",
    file: HOOKS,
    old: "          mutate(pluginKeys.one(generation, kind, name), undefined, { revalidate: true }),\n",
    new: "",
    command: HOME_PAGE,
  },
  {
    name: "그 행을 다시 읽기만 하고 캐시의 값을 버리지 않는다",
    file: HOOKS,
    old: "mutate(pluginKeys.one(generation, kind, name), undefined, { revalidate: true })",
    new: "mutate(pluginKeys.one(generation, kind, name))",
    command: HOME_PAGE,
  },
  {
    name: "다음 켜고 끄기에 앞의 실패를 걷지 않는다",
    file: LIST,
    old: "    onSwitchFailure(null);\n",
    new: "",
    command: HOME_PAGE,
  },
  {
    name: "켜고 끄기의 401 에 관리 토큰을 내려놓지 않는다",
    file: HOOKS,
    old: "        await orRejectAdminToken(adminToken, (token) =>\n          setPluginEnabled(token, kind, name, enabled),\n        );",
    new: "        await setPluginEnabled(adminToken, kind, name, enabled);",
    command: HOME_PAGE,
  },
  {
    name: "본문 없는 204 를 실패로 읽는다",
    file: API,
    old: "  if (!response.ok) {",
    new: "  if (response.status !== 200) {",
    command: HOME_PAGE,
  },
  // ---- e2e 로만 잡히는 것 ----
  {
    name: "라우트가 종류와 이름을 바꿔 넘긴다",
    file: ROUTE,
    old: "<PluginPage kind={kind} name={name} />",
    new: "<PluginPage kind={name} name={kind} />",
    command: E2E,
  },
  {
    // Next 16.3.6 이 동적 조각을 인코딩된 채로 넘기는 것은 실제 Next 에서만 드러난다.
    name: "e2e: 주소의 조각을 풀지 않는다",
    file: SEGMENT,
    old: "    return decodeURIComponent(segment);",
    new: "    return segment;",
    command: E2E,
  },
  {
    // next build 가 타입까지 보므로 쓰지 않는 인자가 생기는 변이는 빨강이 아니라 오류가 된다. 값만 뒤집는다.
    name: "스위치가 반대 값을 쓴다",
    file: API,
    old: "      body: { enabled },",
    new: "      body: { enabled: !enabled },",
    command: E2E,
  },
];

function run(command) {
  const result = spawnSync(command, { cwd: WEB, shell: true, encoding: "utf-8" });
  if (result.status === 0) {
    return "green";
  }
  const output = `${result.stdout}${result.stderr}`;
  // Vitest 는 "Tests  N failed", Playwright 는 "N failed" 를 요약에 찍는다.
  return /Tests\s+\d+ failed/.test(output) || /^\s+\d+ failed$/m.test(output)
    ? "red"
    : `error(${result.status})`;
}

const selected = process.argv.slice(2);
const unknown = selected.filter((name) => !MUTATIONS.some((m) => m.name === name));
if (unknown.length > 0) {
  console.log(`없는 변이 이름: ${unknown.join(", ")}`);
  process.exit(2);
}
const chosen = selected.length > 0 ? MUTATIONS.filter((m) => selected.includes(m.name)) : MUTATIONS;

for (const mutation of chosen) {
  const text = readFileSync(join(WEB, mutation.file), "utf-8");
  if (text.split(mutation.old).length !== 2) {
    console.log(`원문이 ${mutation.file} 에 정확히 한 번 있지 않다: ${mutation.name}`);
    process.exit(2);
  }
}

for (const command of new Set(chosen.map((m) => m.command))) {
  const status = run(command);
  console.log(`기준선 ${status}: ${command}`);
  if (status !== "green") {
    process.exit(1);
  }
}

let mismatches = 0;
for (const mutation of chosen) {
  const original = readFileSync(join(WEB, mutation.file));
  let status = "";
  try {
    writeFileSync(
      join(WEB, mutation.file),
      original.toString("utf-8").replace(mutation.old, mutation.new),
    );
    status = run(mutation.command);
  } finally {
    writeFileSync(join(WEB, mutation.file), original);
  }
  const ok = status === "red";
  if (!ok) {
    mismatches += 1;
  }
  console.log(`${ok ? "기대대로" : "어긋남"} ${status} (기대 red): ${mutation.name}`);
}
process.exit(mismatches === 0 ? 0 : 1);
