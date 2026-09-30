// 티켓 05(관리 토큰과 플러그인 목록, 첫 e2e)의 TS 변이 28. 이 티켓의 테스트가 무엇을 재는지 본다.
//
// 페이지 테스트는 페이지가 서기 전에 빨갰지만(입력칸이 없다), 그 빨강은 각 테스트가 지키는 행동의 빨강이 아니다.
// 그래서 행동마다 제품 코드에 변이를 넣어 그 행동을 지키는 테스트가 빨간지 본다. 토큰(저장소, partialize, 되살림,
// 확인의 판정 셋, 거부, 지운 토큰의 늦은 401, 키의 횟수, 지우기, 가린 입력, 칸 비우기, 실은 헤더), 목록(묶음, 표지,
// 효과 없음, 실패가 옛 행을 지움, 추적 식별자, 봉투가 아닌 실패), 새로 고침(포커스, 주기, 재연결, 실패 뒤 재시도, 작은 표시, 자리표시), 격리(처리하지 않은 요청), 판정자의
// 생성 클라이언트 패키지 예외, 그리고 e2e 로만 잡히는 hydration 가드(서버가 미리 그린 HTML 에 넣는 칸이 박혀 새로 고칠
// 때 번쩍이는 것)다. 두 그림의 어긋남은 zustand 가 막아서 가드를 빼도 어긋나지 않는다. 처음에는 e2e 의 콘솔 단언이
// 그것을 잡으리라 보고 변이를 뒀는데 초록이었다(2026-09-30). 그래서 e2e 가 칸이 문서에 붙는지를 보게 고쳤다.
//
// 규약은 `tools/mutate.py`·`api_client_mutations.mjs`·`admin_app_mutations.mjs` 와 같다. 원문이 파일에 정확히 한 번
// 있는지 먼저 보고(하나라도 틀리면 아무것도 쓰지 않는다), 변이 없이 명령이 초록인지 기준선을 본 뒤, 변이마다 원래
// 바이트를 쥐고 넣어 돌리고 finally 에서 그 바이트를 쓴다. Vitest 는 실패한 테스트가 셀 때만, Playwright 는 실패한
// 테스트가 셀 때만 빨강이다. 그 밖의 비초록(수집 오류, 준비 실패)은 오류다.
//
// 쓰는 법: node .scratch/web-admin/probes/admin_pages_mutations.mjs [이름 ...]   (저장소 루트에서. 명령은 web/ 에서 돈다)
// 네트워크를 타지 않는다. e2e 변이는 앱을 빌드하고 serve 를 띄운다(약 20초). 모두 약 5분. 종료 코드: 모두 기대대로면 0,
// 어긋나거나 기준선이 초록이 아니면 1, 원문이 틀리거나 없는 이름을 주면 2.

import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const WEB = join(process.cwd(), "web");
const PAGES = "pnpm exec vitest run --project pages";
const JUDGE = "pnpm exec vitest run eslint.config.test.ts";
const E2E = "pnpm -C apps/admin exec playwright test";
const STORE = "apps/admin/stores/tokens.ts";
const HOOKS = "apps/admin/hooks/queries/plugins/index.ts";
const API = "apps/admin/api/plugins/index.ts";
const FAILURE = "apps/admin/api/failure/index.ts";
const FORM = "apps/admin/components/organisms/AdminTokenForm.tsx";
const LIST = "apps/admin/components/organisms/PluginList.tsx";
const NOTICE = "apps/admin/components/molecules/FailureNotice.tsx";
const HYDRATED = "apps/admin/hooks/useHydrated.ts";

const MUTATIONS = [
  // ---- 토큰 ----
  {
    name: "토큰을 localStorage 에 둔다",
    file: STORE,
    old: "createJSONStorage(() => sessionStorage)",
    new: "createJSONStorage(() => localStorage)",
    command: PAGES,
  },
  {
    name: "partialize 없이 상태 전부를 저장한다",
    file: STORE,
    old: "      partialize: ({ adminToken }) => ({ adminToken }),\n",
    new: "",
    command: PAGES,
  },
  {
    name: "새로 고침 뒤 저장소에서 되살리지 않는다",
    file: STORE,
    old: '      name: "agent-os-admin-tokens",\n',
    new: '      name: "agent-os-admin-tokens",\n      skipHydration: true,\n',
    command: PAGES,
  },
  {
    name: "확인 요청이 401 이어도 토큰을 저장한다",
    file: HOOKS,
    old: '    return "rejected";',
    new: '    return "accepted";',
    command: PAGES,
  },
  {
    name: "확인 중 서버에 닿지 못해도 토큰을 저장한다",
    file: HOOKS,
    old: '  return error.envelope === null ? "unjudged" : "accepted";',
    new: '  return "accepted";',
    command: PAGES,
  },
  {
    name: "봉투가 온 실패에도 토큰을 저장하지 않는다",
    file: HOOKS,
    old: '  return error.envelope === null ? "unjudged" : "accepted";',
    new: '  return "unjudged";',
    command: PAGES,
  },
  {
    name: "관리 요청의 401 에 토큰을 내려놓지 않는다",
    file: HOOKS,
    old: "    tokens.rejectAdminToken();\n",
    new: "",
    command: PAGES,
  },
  {
    name: "지운 토큰의 늦은 401 이 새 토큰을 내려놓는다",
    file: HOOKS,
    old: "isRejection(error) && tokens.adminToken === adminToken",
    new: "isRejection(error)",
    command: PAGES,
  },
  {
    name: "SWR 키에 토큰을 받아들인 횟수를 싣지 않는다",
    file: HOOKS,
    old: 'list: (generation: number) => ["plugins", generation] as const,',
    new: 'list: (generation: number) => ["plugins"] as const,',
    command: PAGES,
  },
  {
    name: "토큰 지우기가 토큰을 남긴다",
    file: STORE,
    old: "      clearTokens: () => {\n        set({ adminToken: null, adminTokenNotice: null });",
    new: "      clearTokens: () => {\n        set({ adminTokenNotice: null });",
    command: PAGES,
  },
  {
    name: "입력칸을 가리지 않는다",
    file: FORM,
    old: 'type="password"',
    new: 'type="text"',
    command: PAGES,
  },
  {
    name: "거부된 토큰을 칸에 둔다",
    file: FORM,
    old: "    form.reset();\n",
    new: "",
    command: PAGES,
  },
  {
    name: "관리 요청에 다른 토큰을 싣는다",
    file: API,
    old: "await createAdminClient(adminToken)",
    new: 'await createAdminClient(`${adminToken}-x`)',
    command: PAGES,
  },
  // ---- 목록 ----
  {
    name: "종류로 묶지 않는다",
    file: LIST,
    old: "rows={data.filter((row) => row.kind === kind)}",
    new: "rows={data}",
    command: PAGES,
  },
  {
    name: "표지 행의 이유를 싣지 않는다",
    file: LIST,
    old: "<p>읽을 수 없는 매니페스트: {row.reason}</p>",
    new: "<p>읽을 수 없는 매니페스트</p>",
    command: PAGES,
  },
  {
    name: "에이전트 행에도 효과 없음을 싣는다",
    file: LIST,
    old: 'new Set<PluginKind>(["skill", "model"])',
    new: 'new Set<PluginKind>(["skill", "model", "agent"])',
    command: PAGES,
  },
  {
    name: "실패해도 옛 행을 둔다",
    file: LIST,
    old: "{error !== undefined ? (",
    new: "{error !== undefined && data === undefined ? (",
    command: PAGES,
  },
  {
    name: "추적 식별자를 보이지 않는다",
    file: NOTICE,
    old: "{requestId === null ? null : (",
    new: "{requestId !== undefined ? null : (",
    command: PAGES,
  },
  {
    name: "봉투가 아닌 500 을 그 본문으로 보인다",
    file: FAILURE,
    old: "isEnvelope(body) ? body : null",
    new: 'isEnvelope(body) ? body : { code: "internal_error", message: String(body), request_id: "", violations: [] }',
    command: PAGES,
  },
  // ---- 새로 고침과 상태 ----
  {
    name: "포커스 재검증을 끈다",
    file: HOOKS,
    old: "  revalidateOnFocus: true,",
    new: "  revalidateOnFocus: false,",
    command: PAGES,
  },
  {
    name: "주기 재검증을 둔다",
    file: HOOKS,
    old: "  refreshInterval: 0,",
    new: "  refreshInterval: 60_000,",
    command: PAGES,
  },
  {
    name: "재연결 재검증을 켠다",
    file: HOOKS,
    old: "  revalidateOnReconnect: false,",
    new: "  revalidateOnReconnect: true,",
    command: PAGES,
  },
  {
    name: "실패 뒤 스스로 다시 시도한다",
    file: HOOKS,
    old: "  shouldRetryOnError: false,",
    new: "  shouldRetryOnError: true,",
    command: PAGES,
  },
  {
    name: "다시 확인하는 중을 보이지 않는다",
    file: LIST,
    old: '{shown && isValidating ? <span role="status">다시 확인하는 중</span> : null}',
    new: "",
    command: PAGES,
  },
  {
    name: "다시 확인하는 동안 행을 지운다",
    file: LIST,
    old: ") : data === undefined ? (",
    new: ") : data === undefined || isValidating ? (",
    command: PAGES,
  },
  // ---- 격리 ----
  {
    name: "화면이 부르지 않을 경로를 부른다",
    file: API,
    old: "export async function listPlugins(adminToken: string): Promise<PluginRow[]> {\n",
    new: 'export async function listPlugins(adminToken: string): Promise<PluginRow[]> {\n  await createAdminClient(adminToken).GET("/health").catch(() => undefined);\n',
    command: PAGES,
  },
  // ---- 판정자 ----
  {
    name: "생성 클라이언트 패키지의 openapi-fetch 예외를 거둔다",
    file: "eslint.config.mjs",
    old: 'files: ["**/packages/api-client/**"],',
    new: 'files: ["**/packages/api-client-nowhere/**"],',
    command: JUDGE,
  },
  // ---- e2e ----
  {
    name: "서버가 미리 그린 HTML 에 넣는 칸을 박는다",
    file: HYDRATED,
    old: "    () => false,\n",
    new: "    () => true,\n",
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
