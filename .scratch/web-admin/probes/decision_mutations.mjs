// 티켓 08(채널 토큰과 결정)의 TS 변이. 이 티켓의 테스트가 무엇을 재는지 본다.
//
// 페이지 테스트는 채널 토큰을 넣는 자리가 서기 전에 모두 빨갰지만(그 칸이 없다), 그 빨강은 각 테스트가 지키는 행동의
// 빨강이 아니다. 그래서 행동마다 제품 코드에 변이를 넣어 그 행동을 지키는 테스트가 빨간지 본다. 채널 토큰(저장, 지우기,
// 관리 토큰이 거부된 뒤의 지우기, 한 토큰의 거부가 다른 토큰을 두는 것, 가린 입력), 결정(자리, 채널 토큰만 싣기, 거부의
// 사유와 다듬기, 422 를 사유 옆에, 새 일시정지의 새 폼), 재개 스트림(받는 대로, 다시 읽기, 받은 것 걷기, 끊김의 판정 셋,
// 다시 보내지 않기, 떠나면 끊기, 읽지 못한 프레임, 트레이스 아래), 결정 자리의 조건(채널 토큰, 형식, 일시정지, 에이전트),
// 409 와 꺼짐(트레이스와 목록 다시 읽기, 에이전트와 MCP 의 미리 알림, 표지, 실패한 목록을 믿지 않기, 버튼 막기), 채널
// 토큰의 거부, e2e 로만 잡히는 것(중계의 압축, 꺼짐이 막는 버튼, 409 뒤의 다시 읽기, 스트림 뒤의 다시 읽기, 떠나면 끊기,
// 끊긴 읽기를 잡기)이다.
//
// 티켓은 압축의 되돌림을 `tools/mutate.py` 로 보라고 적었지만 그 도구는 pytest 만 돈다. 그래서 web 티켓들의 하네스인 이
// 파일에 넣는다. 규약은 `runs_trace_mutations.mjs` 와 같다. 원문이 파일에 정확히 한 번 있는지 먼저 보고(하나라도 틀리면
// 아무것도 쓰지 않는다), 변이 없이 명령이 초록인지 기준선을 본 뒤, 변이마다 원래 바이트를 쥐고 넣어 돌리고 finally 에서
// 그 바이트를 쓴다. Vitest 는 실패한 테스트가 셀 때만, Playwright 는 실패한 테스트가 셀 때만 빨강이다. 그 밖의 비초록(수집
// 오류, 준비 실패)은 오류다.
//
// 쓰는 법: node .scratch/web-admin/probes/decision_mutations.mjs [이름 ...]   (저장소 루트에서. 명령은 web/ 에서 돈다)
// 네트워크를 타지 않는다. e2e 변이는 앱을 빌드하고 serve 를 띄운다(하나에 약 40초). 페이지 테스트의 변이도 하나에
// 30초~1분이라 모두 약 45분(2026-09-30)이다. 에이전트의 명령 상한(10분)을 넘으니 백그라운드로 돌리거나 이름으로 나눈다.
// 도는 동안 러너가 소스를 잠깐씩 고치므로 web/ 을 고치거나 소스를 읽는 리뷰를 띄우지 않는다. 종료 코드: 모두 기대대로면 0, 어긋나거나 기준선이 초록이
// 아니면 1, 원문이 틀리거나 없는 이름을 주면 2.

import { spawnSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const WEB = join(process.cwd(), "web");
const HOME = "pnpm exec vitest run --project pages apps/admin/components/pages/HomePage.test.tsx";
const DECISION =
  "pnpm exec vitest run --project pages apps/admin/components/pages/RunPage.decision.test.tsx";
const E2E = "pnpm -C apps/admin exec playwright test";
const STORE = "apps/admin/stores/tokens.ts";
const FORM = "apps/admin/components/organisms/ChannelTokenForm.tsx";
const HOOK = "apps/admin/hooks/queries/approval/index.ts";
const PLACE = "apps/admin/components/organisms/RunDecision.tsx";
const DETAIL = "apps/admin/components/organisms/RunDetail.tsx";
const SCREEN = "apps/admin/components/pages/AdminScreen.tsx";
const CONFIG = "apps/admin/next.config.ts";

const SEND = "received = await sendDecision(token, runId, decision, controller.signal);";
const CUT = "setCut(!endsStream(last));";
const REREAD = "        await rereadTrace();\n        setFrames([]);\n";
const CONFLICT = "await Promise.all([rereadTrace(), mutate(pluginKeys.list(generation))]);";
const BLOCKED = "const blocked = busy || disabled.length > 0;";
const APPROVE = 'onDecide({ decision: "approve", pause_index: pause.index });';
const DENY = 'onDecide({ decision: "deny", pause_index: pauseIndex, reason: trimmed });';
const DENY_DISABLED = 'disabled={blocked || trimmed === ""}';
const EVENTS_THEN_DECISION = `          <section aria-labelledby={eventsId}>
            <h3 id={eventsId}>이벤트</h3>
            <ol>
              {trace.events.map((event, index) => (
                // 이벤트는 트레이스에 쓴 차례로만 갈린다. 같은 트레이스 안에서 그 차례는 바뀌지 않는다.
                <EventItem key={index} event={event} />
              ))}
            </ol>
          </section>
          <RunDecision runId={runId} trace={trace} />
`;

const MUTATIONS = [
  // ---- 채널 토큰 ----
  {
    name: "채널 토큰을 저장하지 않는다",
    file: STORE,
    old: "partialize: ({ adminToken, channelToken }) => ({ adminToken, channelToken }),",
    new: "partialize: ({ adminToken }) => ({ adminToken }),",
    command: HOME,
  },
  {
    name: "토큰 지우기가 채널 토큰을 남긴다",
    file: STORE,
    old: "set({ adminToken: null, adminTokenNotice: null, channelToken: null });",
    new: "set({ adminToken: null, adminTokenNotice: null });",
    command: HOME,
  },
  {
    name: "관리 토큰의 거부가 채널 토큰도 지운다",
    file: STORE,
    old: 'set({ adminToken: null, adminTokenNotice: "rejected" });',
    new: 'set({ adminToken: null, adminTokenNotice: "rejected", channelToken: null });',
    command: HOME,
  },
  {
    name: "채널 토큰의 거부가 관리 토큰도 지운다",
    file: STORE,
    old: "set({ channelToken: null });",
    new: "set({ channelToken: null, adminToken: null });",
    command: DECISION,
  },
  {
    name: "관리 토큰이 거부되면 남은 채널 토큰을 지울 길이 없다",
    file: SCREEN,
    old: "<AdminFrame actions={channelToken === null ? undefined : clearButton}>",
    new: "<AdminFrame>",
    command: HOME,
  },
  {
    name: "지울 토큰이 없어도 넣는 자리에 토큰 지우기를 둔다",
    file: SCREEN,
    old: "<AdminFrame actions={channelToken === null ? undefined : clearButton}>",
    new: "<AdminFrame actions={clearButton}>",
    command: HOME,
  },
  {
    name: "채널 토큰 칸이 가린 입력이 아니다",
    file: FORM,
    old: 'type="password"',
    new: 'type="text"',
    command: HOME,
  },
  {
    name: "결정에 관리 토큰을 싣는다",
    file: HOOK,
    old: SEND,
    new: "received = await sendDecision(useTokens.getState().adminToken ?? token, runId, decision, controller.signal);",
    command: DECISION,
  },
  {
    name: "401 이 채널 토큰을 내려놓지 않는다",
    file: HOOK,
    old: "          rejectChannelTokenIfStillHeld(token);\n",
    new: "",
    command: DECISION,
  },
  {
    name: "채널 토큰이 거부됐다고 말하지 않는다",
    file: PLACE,
    old: 'return channelToken === null ? { message: "채널 토큰이 거부됐다", requestId: null } : null;',
    new: "return describeFailure(failure);",
    command: DECISION,
  },
  // ---- 결정 자리 ----
  {
    name: "채널 토큰 없이도 결정 자리를 둔다",
    file: PLACE,
    old: "{channelToken !== null && pause !== null ? (",
    new: "{pause !== null ? (",
    command: DECISION,
  },
  {
    name: "형식 1 에도 결정 자리를 둔다",
    file: PLACE,
    old: 'const pause = trace.schema_version === "2" ? pauseOf(trace) : null;',
    new: "const pause = pauseOf(trace);",
    command: DECISION,
  },
  {
    name: "끝난 실행에도 결정 자리를 둔다",
    file: PLACE,
    old: 'if (last?.type !== "run_paused") {',
    new: "if (last === undefined) {",
    command: DECISION,
  },
  {
    name: "인자를 보이지 않는다",
    file: PLACE,
    old: '<dd style={{ whiteSpace: "pre-wrap" }}>{asText(pause.args)}</dd>',
    new: "<dd />",
    command: DECISION,
  },
  {
    name: "승인자가 누구로 기록되는지 말하지 않는다",
    file: PLACE,
    old: "        결정의 승인자는 이 화면이 고르지 않는다. <code>agent-os serve</code> 를 띄운 OS 사용자로\n        기록된다.\n",
    new: "",
    command: DECISION,
  },
  {
    name: "허가가 트레이스에서 읽은 자리를 싣지 않는다",
    file: PLACE,
    old: APPROVE,
    new: 'onDecide({ decision: "approve", pause_index: 0 });',
    command: DECISION,
  },
  {
    name: "거부가 트레이스에서 읽은 자리를 싣지 않는다",
    file: PLACE,
    old: DENY,
    new: 'onDecide({ decision: "deny", pause_index: 0, reason: trimmed });',
    command: DECISION,
  },
  {
    name: "거부가 사유를 다듬지 않는다",
    file: PLACE,
    old: DENY,
    new: 'onDecide({ decision: "deny", pause_index: pauseIndex, reason });',
    command: DECISION,
  },
  {
    name: "사유 없이도 거부를 보낼 수 있다",
    file: PLACE,
    old: DENY_DISABLED,
    new: "disabled={blocked}",
    command: DECISION,
  },
  {
    name: "공백뿐인 사유로도 거부를 보낼 수 있다",
    file: PLACE,
    old: DENY_DISABLED,
    new: 'disabled={blocked || reason === ""}',
    command: DECISION,
  },
  {
    name: "새 일시정지에 앞의 거부 사유가 남는다",
    file: PLACE,
    old: "        key={pause.index}\n",
    new: "",
    command: DECISION,
  },
  {
    name: "422 를 사유 옆에 두지 않는다",
    file: PLACE,
    old: "aria-describedby={invalid === null ? undefined : invalidId}",
    new: "aria-describedby={undefined}",
    command: DECISION,
  },
  {
    name: "422 의 violations 를 보이지 않는다",
    file: PLACE,
    old: "{invalid.envelope?.violations.map(",
    new: "{[].map(",
    command: DECISION,
  },
  // ---- 재개 스트림 ----
  {
    name: "재개 스트림을 다 받은 뒤에야 보인다",
    file: HOOK,
    old: "          for await (const frame of received) {\n            last = frame;\n            setFrames((shown) => [...shown, frame]);\n          }\n",
    new: "          const all = [];\n          for await (const frame of received) {\n            last = frame;\n            all.push(frame);\n          }\n          setFrames(all);\n",
    command: DECISION,
  },
  {
    name: "스트림이 끝나도 트레이스를 다시 읽지 않는다",
    file: HOOK,
    old: REREAD,
    new: "        setFrames([]);\n",
    command: DECISION,
  },
  {
    name: "다시 읽은 뒤에도 스트림으로 받은 것을 남긴다",
    file: HOOK,
    old: REREAD,
    new: "        await rereadTrace();\n",
    command: DECISION,
  },
  {
    name: "결말 없이 끝난 스트림을 끊김으로 보지 않는다",
    file: HOOK,
    old: CUT,
    new: "setCut(false);",
    command: DECISION,
  },
  {
    name: "다시 멈춘 스트림을 끊김으로 본다",
    file: HOOK,
    old: "  run_paused: true,",
    new: "  run_paused: false,",
    command: DECISION,
  },
  {
    name: "결말로 끝난 스트림도 끊김으로 본다",
    file: HOOK,
    old: CUT,
    new: "setCut(true);",
    command: DECISION,
  },
  {
    // 처음에는 읽기의 에러(`catch`)에서 다시 보냈다. MSW 3.0.0 은 핸들러 스트림의 에러를 읽는 쪽에 끝으로 넘겨
    // (`msw_abort.mjs`) 그 길을 페이지 테스트가 만들 수 없어 초록이었다. 결말 없이 끝난 모든 스트림에서 다시 보낸다.
    name: "결말 없이 끝난 스트림에 결정을 다시 보낸다",
    file: HOOK,
    old: CUT,
    new: "const cutNow = !endsStream(last);\n        setCut(cutNow);\n        if (cutNow) {\n          await sendDecision(token, runId, decision, controller.signal).catch(() => undefined);\n        }",
    command: DECISION,
  },
  {
    // 처음에는 떠난 화면만 봐 초록이었다(error). SWR 의 mutate 는 그 키를 보는 화면이 없으면 요청을 내지 않는다. 돌아온
    // 화면이 캐시를 이어 쓰게 테스트를 고쳤다.
    name: "화면이 떠나도 연결을 끊지 않는다",
    file: HOOK,
    old: "      inFlight.current?.abort();\n",
    new: "",
    command: DECISION,
  },
  // "떠난 뒤에도 트레이스를 다시 읽는다"(스트림 뒤의 끊김 가드를 걷는 변이)는 걷었다. 끊김은 언마운트와 같은 순간이라
  // 가드가 없어도 늦은 mutate 는 돌아온 화면이 서기 전에 돌아 요청을 내지 않는다(SWR 은 그 키를 보는 훅이 없으면 요청을
  // 내지 않는다). 가드가 막는 것은 화면과 함께 걷힌 캐시에 부르는 mutate 의 처리하지 않은 에러뿐이고, 러너는 그것을
  // 빨강(실패한 테스트)이 아니라 오류로 센다. 두 번 돌려 두 번 다 오류(error(1))였다.
  {
    name: "읽지 못한 프레임의 원문을 버린다",
    file: PLACE,
    old: '<p style={{ whiteSpace: "pre-wrap" }}>{frame.raw}</p>',
    new: '<p style={{ whiteSpace: "pre-wrap" }} />',
    command: DECISION,
  },
  {
    name: "결정과 재개 스트림을 트레이스 위에 둔다",
    file: DETAIL,
    old: EVENTS_THEN_DECISION,
    new: `          <RunDecision runId={runId} trace={trace} />\n${EVENTS_THEN_DECISION.replace("          <RunDecision runId={runId} trace={trace} />\n", "")}`,
    command: DECISION,
  },
  // ---- 409 와 꺼짐 ----
  {
    name: "409 뒤에 트레이스를 다시 읽지 않는다",
    file: HOOK,
    old: CONFLICT,
    new: "await mutate(pluginKeys.list(generation));",
    command: DECISION,
  },
  {
    name: "409 뒤에 플러그인 목록을 다시 읽지 않는다",
    file: HOOK,
    old: CONFLICT,
    new: "await rereadTrace();",
    command: DECISION,
  },
  {
    name: "목록을 다시 읽다 실패해도 옛 꺼짐으로 막는다",
    file: PLACE,
    old: "disabledFor(pause.agent, unknown ? undefined : plugins.data)",
    new: "disabledFor(pause.agent, plugins.data)",
    command: DECISION,
  },
  {
    name: "목록을 읽지 못해 미리 알 수 없다고 말하지 않는다",
    file: PLACE,
    old: "{unknown ? <p>플러그인 목록을 읽지 못해 꺼진 플러그인을 미리 알 수 없다.</p> : null}",
    new: "",
    command: DECISION,
  },
  {
    name: "꺼진 에이전트를 미리 알리지 않는다",
    file: PLACE,
    old: "const found = row.enabled ? [] : [`에이전트 ${row.name}`];",
    new: "const found: string[] = [];",
    command: DECISION,
  },
  {
    name: "꺼진 MCP 를 미리 알리지 않는다",
    file: PLACE,
    old: "      found.push(`MCP ${mcp}`);\n",
    new: "",
    command: DECISION,
  },
  {
    name: "표지 행이어도 꺼짐을 미리 알린다",
    file: PLACE,
    old: 'if (row === undefined || !("manifest" in row)) {\n    return [];',
    new: 'if (row === undefined || !("manifest" in row)) {\n    return row?.enabled === false ? [`에이전트 ${agent}`] : [];',
    command: DECISION,
  },
  {
    name: "에이전트를 첫 이벤트에서 읽지 않는다",
    file: PLACE,
    old: 'agent: first?.type === "run_started" ? first.agent : null,',
    new: "agent: null,",
    command: DECISION,
  },
  {
    name: "꺼짐이 결정 버튼을 막지 않는다",
    file: PLACE,
    old: BLOCKED,
    new: "const blocked = busy;",
    command: DECISION,
  },
  {
    name: "보내는 동안 결정 버튼을 막지 않는다",
    file: PLACE,
    old: BLOCKED,
    new: "const blocked = disabled.length > 0;",
    command: DECISION,
  },
  // ---- e2e 로만 잡히는 것 ----
  {
    // 티켓 04 의 `compress: false` 가 빠진 것. 재개 스트림이 끝에 몰려 와 첫 이벤트가 결말과 함께 선다.
    name: "e2e: 중계가 응답을 압축한다",
    file: CONFIG,
    old: "  compress: false,",
    new: "  compress: true,",
    command: E2E,
  },
  {
    name: "e2e: 꺼짐이 결정 버튼을 막지 않는다",
    file: PLACE,
    old: BLOCKED,
    new: "const blocked = busy;",
    command: E2E,
  },
  {
    name: "e2e: 409 뒤에 트레이스를 다시 읽지 않는다",
    file: HOOK,
    old: CONFLICT,
    new: "await mutate(pluginKeys.list(generation));",
    command: E2E,
  },
  {
    name: "e2e: 스트림이 끝나도 트레이스를 다시 읽지 않는다",
    file: HOOK,
    old: REREAD,
    new: "        setFrames([]);\n",
    command: E2E,
  },
  {
    name: "e2e: 화면이 떠나도 연결을 끊지 않는다",
    file: HOOK,
    old: "      inFlight.current?.abort();\n",
    new: "",
    command: E2E,
  },
  {
    // 떠나며 끊으면 기다리던 읽기가 AbortError 로 끝난다. 잡지 않으면 처리하지 않은 거부로 페이지에 남는다.
    name: "e2e: 끊긴 읽기를 잡지 않는다",
    file: HOOK,
    old: "        try {\n          for await (const frame of received) {\n            last = frame;\n            setFrames((shown) => [...shown, frame]);\n          }\n        } catch {\n          // 끊겼다. 결말을 받았는지는 마지막 프레임이 말한다. 결말 뒤의 끊김은 끊김이 아니다.\n        }\n",
    new: "        for await (const frame of received) {\n          last = frame;\n          setFrames((shown) => [...shown, frame]);\n        }\n",
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
