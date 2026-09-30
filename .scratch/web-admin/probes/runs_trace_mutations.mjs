// 티켓 07(실행 목록과 실행 하나)의 TS 변이. 이 티켓의 테스트가 무엇을 재는지 본다.
//
// 페이지 테스트는 화면이 서기 전에 빨갰지만(모듈이 없다), 그 빨강은 각 테스트가 지키는 행동의 빨강이 아니다. 구현 뒤에
// 모두 초록으로 섰으므로 어느 것도 행동의 빨강을 본 적이 없다. 그래서 행동마다 제품 코드에 변이를 넣어 그 행동을 지키는
// 테스트가 빨간지 본다. 실행 목록(서버의 차례, 거르기, 상태의 이름, 커서, 더 보기, 멈춘 실행, 읽을 수 없는 트레이스,
// 링크, 요약 행, 빈 목록, 새로 고침이 본 쪽을 모두 읽는 것, 401, 키의 횟수, 읽기 골격의 실패·작은 표시·거르기 자리,
// 화면 사이 링크), 실행 하나(쓴 차례, 글자 그대로, 들여 적기, 모르는 종류, 형식 1, 글자로만, 401, 키의 횟수, 새로
// 고침, 다시 읽다 실패, 주소의 조각, 목록으로 가는 링크), 그리고 e2e 로만 잡히는 것(라우트가 조각을 넘기는 것, 실제
// 브라우저의 HTML, 실제 serve 의 거르기, 실제 트레이스의 모르는 줄과 형식 1)이다.
//
// 규약은 `plugin_toggle_mutations.mjs` 와 같다. 원문이 파일에 정확히 한 번 있는지 먼저 보고(하나라도 틀리면 아무것도
// 쓰지 않는다), 변이 없이 명령이 초록인지 기준선을 본 뒤, 변이마다 원래 바이트를 쥐고 넣어 돌리고 finally 에서 그
// 바이트를 쓴다. Vitest 는 실패한 테스트가 셀 때만, Playwright 는 실패한 테스트가 셀 때만 빨강이다. 그 밖의 비초록(수집
// 오류, 준비 실패)은 오류다.
//
// 쓰는 법: node .scratch/web-admin/probes/runs_trace_mutations.mjs [이름 ...]   (저장소 루트에서. 명령은 web/ 에서 돈다)
// 네트워크를 타지 않는다. e2e 변이는 앱을 빌드하고 serve 를 띄운다(하나에 약 40초). 모두 약 13분이라 에이전트의 명령
// 상한(10분)을 넘는다. 백그라운드로 돌리거나 이름으로 나눈다. 종료 코드: 모두 기대대로면 0, 어긋나거나 기준선이 초록이
// 아니면 1, 원문이 틀리거나 없는 이름을 주면 2.

import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const WEB = join(process.cwd(), "web");
const RUNS_PAGE =
  "pnpm exec vitest run --project pages apps/admin/components/pages/RunsPage.test.tsx";
const RUN_PAGE =
  "pnpm exec vitest run --project pages apps/admin/components/pages/RunPage.test.tsx";
const E2E = "pnpm -C apps/admin exec playwright test";
const HOOKS = "apps/admin/hooks/queries/traces/index.ts";
const LIST = "apps/admin/components/organisms/RunList.tsx";
const DETAIL = "apps/admin/components/organisms/RunDetail.tsx";
// 티켓 08 이 이벤트 하나를 그리는 코드를 RunDetail 에서 옮겼다. 재개 스트림도 같은 것을 지난다.
const EVENT = "apps/admin/components/organisms/EventItem.tsx";
const SECTION = "apps/admin/components/organisms/ReadSection.tsx";
const SCREEN = "apps/admin/components/pages/AdminScreen.tsx";
const PAGE = "apps/admin/components/pages/RunPage.tsx";
const SEGMENT = "apps/admin/components/pages/segment.ts";
const ROUTE = "apps/admin/app/runs/[runId]/page.tsx";

const AS_TEXT = 'return typeof value === "string" ? value : JSON.stringify(value, null, 2);';
const FIELDS = '.filter(([name]) => name !== "type" && name !== "run_id")';
const AS_HTML =
  '<dd style={{ whiteSpace: "pre-wrap" }} dangerouslySetInnerHTML={{ __html: asText(value) }} />';

const MUTATIONS = [
  // ---- 실행 목록 ----
  {
    name: "목록을 다시 정렬한다",
    file: LIST,
    old: "const rows = pages.flatMap((page) => page.runs);",
    new: "const rows = pages.flatMap((page) => page.runs).toSorted((a, b) => a.run_id.localeCompare(b.run_id));",
    command: RUNS_PAGE,
  },
  {
    name: "거르기가 상태를 싣지 않는다",
    file: HOOKS,
    old: "listTraces(token, pageStatus, after)",
    new: "listTraces(token, null, after)",
    command: RUNS_PAGE,
  },
  {
    name: "끝남과 실패의 이름이 뒤바뀐다",
    file: LIST,
    old: '  finished: "끝남",\n  failed: "실패",',
    new: '  finished: "실패",\n  failed: "끝남",',
    command: RUNS_PAGE,
  },
  {
    name: "결말 없음을 실행 중으로 부른다",
    file: LIST,
    old: '  unfinished: "결말 없음",',
    new: '  unfinished: "실행 중",',
    command: RUNS_PAGE,
  },
  {
    name: "더 보기가 커서를 싣지 않는다",
    file: HOOKS,
    old: ": traceKeys.page(generation, status, previous.next_cursor);",
    new: ": traceKeys.page(generation, status, null);",
    command: RUNS_PAGE,
  },
  {
    name: "더 보기가 없다",
    file: LIST,
    old: "{nextCursor === null ? null : (",
    new: "{true ? null : (",
    command: RUNS_PAGE,
  },
  {
    name: "마지막 쪽에도 더 보기가 남는다",
    file: LIST,
    old: "const nextCursor = pages.at(-1)?.next_cursor ?? null;",
    new: "const nextCursor = pages.at(0)?.next_cursor ?? null;",
    command: RUNS_PAGE,
  },
  {
    name: "읽는 동안에도 더 보기가 눌린다",
    file: LIST,
    old: "                disabled={isValidating}\n",
    new: "",
    command: RUNS_PAGE,
  },
  {
    name: "쪽을 나란히 읽는다",
    file: HOOKS,
    old: "    { ...READ, revalidateAll: true },\n  );\n}\n\n/** 실행 하나의 트레이스.",
    new: "    { ...READ, revalidateAll: true, parallel: true },\n  );\n}\n\n/** 실행 하나의 트레이스.",
    command: RUNS_PAGE,
  },
  {
    // 셀프 리뷰의 명세 축이 짚었다. 기본값이면 포커스가 첫 쪽과 커서가 바뀐 쪽만 읽는다(스토리 33).
    name: "포커스가 본 쪽을 모두 다시 읽지 않는다",
    file: HOOKS,
    old: "    { ...READ, revalidateAll: true },\n",
    new: "    READ,\n",
    command: RUNS_PAGE,
  },
  {
    name: "멈춘 실행을 두드러지게 하지 않는다",
    file: LIST,
    old: "<strong>{STATUS_NAMES.paused}</strong>",
    new: "<span>{STATUS_NAMES.paused}</span>",
    command: RUNS_PAGE,
  },
  {
    name: "읽을 수 없는 트레이스의 이유를 보이지 않는다",
    file: LIST,
    old: "<span>읽을 수 없는 트레이스: {row.reason}</span>",
    new: "<span>읽을 수 없는 트레이스</span>",
    command: RUNS_PAGE,
  },
  {
    name: "행의 링크가 그 실행을 가리키지 않는다",
    file: LIST,
    old: "<Link href={`/runs/${encodeURIComponent(row.run_id)}`}>",
    new: '<Link href="/runs">',
    command: RUNS_PAGE,
  },
  {
    name: "요약 행이 주체를 보이지 않는다",
    file: LIST,
    old: "에이전트 {row.agent} · 주체 {row.principal} · 시작",
    new: "에이전트 {row.agent} · 시작",
    command: RUNS_PAGE,
  },
  {
    name: "실행이 없다를 말하지 않는다",
    file: LIST,
    old: "<p>실행이 없다</p>",
    new: "<ol />",
    command: RUNS_PAGE,
  },
  {
    name: "목록의 새로 고침 버튼이 다시 읽지 않는다",
    file: LIST,
    old: "        void mutate();",
    new: "        void 0;",
    command: RUNS_PAGE,
  },
  {
    name: "목록의 401 에 관리 토큰을 내려놓지 않는다",
    file: HOOKS,
    old: "orRejectAdminToken(adminToken, (token) => listTraces(token, pageStatus, after))",
    new: "listTraces(adminToken, pageStatus, after)",
    command: RUNS_PAGE,
  },
  {
    name: "목록의 키가 토큰을 받아들인 횟수를 싣지 않는다",
    file: HOOKS,
    old: '["traces", generation, status, after] as const',
    new: '["traces", 0, status, after] as const',
    command: RUNS_PAGE,
  },
  {
    name: "거르기가 실패 중에 사라진다",
    file: SECTION,
    old: "      {above}\n",
    new: "      {error === undefined ? above : null}\n",
    command: RUNS_PAGE,
  },
  {
    name: "다시 읽다 실패해도 보인 행을 둔다",
    file: SECTION,
    old: "{error !== undefined ? (",
    new: "{error !== undefined && data === undefined ? (",
    command: RUNS_PAGE,
  },
  {
    name: "다시 확인하는 동안 행을 지운다",
    file: SECTION,
    old: ") : data === undefined ? (",
    new: ") : data === undefined || isValidating ? (",
    command: RUNS_PAGE,
  },
  {
    name: "실행 목록의 실패에 추적 식별자를 싣지 않는다",
    file: SECTION,
    old: "<FailureNotice {...describeFailure(error)} />",
    new: "<FailureNotice message={describeFailure(error).message} requestId={null} />",
    command: RUNS_PAGE,
  },
  {
    name: "머리의 실행 목록 링크가 실행 목록을 가리키지 않는다",
    file: SCREEN,
    old: '<Link href="/runs">실행 목록</Link>',
    new: '<Link href="/">실행 목록</Link>',
    command: RUNS_PAGE,
  },
  // ---- 실행 하나 ----
  {
    name: "이벤트를 거꾸로 보인다",
    file: DETAIL,
    old: "{trace.events.map((event, index) => (",
    new: "{trace.events.toReversed().map((event, index) => (",
    command: RUN_PAGE,
  },
  {
    name: "문자열 필드를 JSON 으로 적는다",
    file: EVENT,
    old: AS_TEXT,
    new: "return JSON.stringify(value, null, 2);",
    command: RUN_PAGE,
  },
  {
    name: "JSON 값을 들여 적지 않는다",
    file: EVENT,
    old: AS_TEXT,
    new: 'return typeof value === "string" ? value : JSON.stringify(value);',
    command: RUN_PAGE,
  },
  {
    name: "모르는 종류의 원문을 보이지 않는다",
    file: EVENT,
    old: FIELDS,
    new: '.filter(([name]) => name !== "type" && name !== "run_id" && name !== "raw")',
    command: RUN_PAGE,
  },
  {
    // 셀프 리뷰의 명세 축이 짚었다. 화면 문구는 용어집의 말이다.
    name: "필드에 용어집의 말을 붙이지 않는다",
    file: EVENT,
    old: "{isEventField(name) ? `${FIELD_NAMES[name]} ` : null}",
    new: "{null}",
    command: RUN_PAGE,
  },
  {
    name: "모르는 종류를 판별자 이름으로 부른다",
    file: EVENT,
    old: '{event.type === "unknown" ? "모르는 종류" : event.type}',
    new: "{event.type}",
    command: RUN_PAGE,
  },
  {
    name: "형식을 거꾸로 가린다",
    file: DETAIL,
    old: 'trace.schema_version === "1" ? (',
    new: 'trace.schema_version !== "1" ? (',
    command: RUN_PAGE,
  },
  {
    name: "트레이스를 HTML 로 그린다",
    file: EVENT,
    old: '<dd style={{ whiteSpace: "pre-wrap" }}>{asText(value)}</dd>',
    new: AS_HTML,
    command: RUN_PAGE,
  },
  {
    name: "상세의 401 에 관리 토큰을 내려놓지 않는다",
    file: HOOKS,
    old: "orRejectAdminToken(adminToken, (token) => readTrace(token, runId))",
    new: "readTrace(adminToken, runId)",
    command: RUN_PAGE,
  },
  {
    name: "상세의 키가 토큰을 받아들인 횟수를 싣지 않는다",
    file: HOOKS,
    old: '["trace", generation, runId] as const',
    new: '["trace", 0, runId] as const',
    command: RUN_PAGE,
  },
  {
    name: "상세의 새로 고침 버튼이 다시 읽지 않는다",
    file: DETAIL,
    old: "        void mutate();",
    new: "        void 0;",
    command: RUN_PAGE,
  },
  {
    name: "다시 읽다 실패해도 보인 이벤트를 둔다",
    file: SECTION,
    old: "{error !== undefined ? (",
    new: "{error !== undefined && data === undefined ? (",
    command: RUN_PAGE,
  },
  {
    name: "실행 하나의 주소 조각을 풀지 않는다",
    file: SEGMENT,
    old: "    return decodeURIComponent(segment);",
    new: "    return segment;",
    command: RUN_PAGE,
  },
  {
    name: "풀 수 없는 실행 식별자에도 요청을 보낸다",
    file: SEGMENT,
    old: "  } catch {\n    return null;\n  }",
    new: "  } catch {\n    return segment;\n  }",
    command: RUN_PAGE,
  },
  {
    name: "실행 목록으로 가는 링크가 목록을 가리키지 않는다",
    file: PAGE,
    old: '<Link href="/runs">실행 목록으로</Link>',
    new: '<Link href="/">실행 목록으로</Link>',
    command: RUN_PAGE,
  },
  // ---- e2e 로만 잡히는 것 ----
  {
    // next build 가 타입까지 보므로 쓰지 않는 인자가 생기는 변이는 빨강이 아니라 오류가 된다. 값만 바꾼다.
    name: "e2e: 라우트가 실행 식별자를 넘기지 않는다",
    file: ROUTE,
    old: "<RunPage runId={runId} />",
    new: "<RunPage runId={`${runId}-x`} />",
    command: E2E,
  },
  {
    name: "e2e: 트레이스를 HTML 로 그린다",
    file: EVENT,
    old: '<dd style={{ whiteSpace: "pre-wrap" }}>{asText(value)}</dd>',
    new: AS_HTML,
    command: E2E,
  },
  {
    name: "e2e: 거르기가 상태를 싣지 않는다",
    file: HOOKS,
    old: "listTraces(token, pageStatus, after)",
    new: "listTraces(token, pageStatus === null ? null : null, after)",
    command: E2E,
  },
  {
    name: "e2e: 모르는 종류의 원문을 보이지 않는다",
    file: EVENT,
    old: FIELDS,
    new: '.filter(([name]) => name !== "type" && name !== "run_id" && name !== "raw")',
    command: E2E,
  },
  {
    name: "e2e: 형식 1 을 말하지 않는다",
    file: DETAIL,
    old: 'trace.schema_version === "1" ? (',
    new: 'trace.schema_version === "2" ? (',
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
      original.toString("utf-8").replace(mutation.old, () => mutation.new),
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
