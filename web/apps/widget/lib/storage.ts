// 위젯의 저장(web-widget 명세 "저장", ADR 0024). 같은 탭에서 새로 고쳐도 대화가 남도록 sessionStorage 에 둔다. 새 탭은
// 빈 저장소라 새 대화로 시작한다.
//
// - 키는 `agent-os-widget:<에이전트 이름>` 이다. 페이지 안 방식에서는 사이트 출처의 저장소라 접두사를 둔다.
// - 드는 것은 토큰의 묶음(발급자와 `sub`), 결말이 있는 교환(요청 글, 도구 줄, 결정의 기록, 결말), 다시 붙을 교환의 요청
//   글, 이어 갈 실행과 다시 붙을 실행의 run_id 다. 도는(또는 멈춘) 교환은 새로 고친 뒤 처음부터 받아 다시 짓기 때문에
//   요청 글만 든다. 실행이 서기 전에 거절된 교환과 알림, 입력창의 글은 들지 않는다. 그래서 새로 고친 뒤에는 결말이 있거나
//   다시 붙을 교환만 보인다.
// - 담을 것이 없으면(교환도 이어 갈 실행도 다시 붙을 실행도 없으면) 키를 지운다. "새 대화"와 마지막 404 가 저장을 비우는
//   길이 이것이다.
// - 용량을 넘으면 오래된 교환부터 뺀다. 다 빼도 넘으면 묶음과 run_id 만 둔 것이 되고, 그것도 넘으면 앞서 저장한 것을 지우고
//   메모리로만 이어 간다. 저장소에 닿지 못하는 것(막힌 저장소의 SecurityError 등)도 용량을 넘은 것과 같다.
// - 저장한 값은 판 번호(`version`, 처음은 1)를 든다. 판이 다르거나 모양 검사를 지나지 못하면 묶음이 다를 때처럼 지운다.
//   모양은 타입 단언 없이 실행 중에 본다(원칙 III).
//
// 토큰의 페이로드는 검증하지 않고 base64url 을 풀어 읽기만 한다. 검증은 서버가 한다. 풀지 못한 토큰은 받지 못한 토큰과
// 같다(부르는 쪽이 그렇게 다룬다).

import type {
  Approval,
  ApprovalState,
  Conversation,
  Exchange,
  FailureCause,
  Outcome,
  ToolCall,
} from "./conversation";

/** 토큰의 발급자와 주체. 같은 탭에서 사이트 계정이 바뀐 것을 이것으로 안다. */
export interface Bundle {
  readonly iss: string;
  readonly sub: string;
}

/** 저장의 판. 모양을 바꾸면 올린다. 다른 판의 저장은 지운다. */
const VERSION = 1;

export function storageKey(agent: string): string {
  return `agent-os-widget:${agent}`;
}

/**
 * 토큰 페이로드의 묶음. 점으로 나눈 둘째 조각을 base64url 로 풀어 읽는다. 풀지 못하거나, 둘 중 하나라도 없거나 문자열이
 * 아니거나, `sub` 가 빈 글자면 null 이다.
 */
export function bundleOf(token: string): Bundle | null {
  const payload = token.split(".")[1];
  if (payload === undefined) {
    return null;
  }
  let claims: unknown;
  try {
    const binary = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    const bytes = Uint8Array.from(binary, (char) => char.charCodeAt(0));
    claims = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
  } catch {
    return null;
  }
  if (
    typeof claims !== "object" ||
    claims === null ||
    !("iss" in claims) ||
    !("sub" in claims) ||
    typeof claims.iss !== "string" ||
    typeof claims.sub !== "string" ||
    claims.sub === ""
  ) {
    return null;
  }
  return { iss: claims.iss, sub: claims.sub };
}

export function sameBundle(a: Bundle, b: Bundle): boolean {
  return a.iss === b.iss && a.sub === b.sub;
}

/** 저장에 드는 결정의 기록. 결정을 기다리는 것은 들지 않는다(그 교환은 요청 글만 든다). */
type SavedApprovalState = Exclude<ApprovalState, { readonly kind: "waiting" }>;

interface SavedApproval {
  readonly pauseId: number;
  readonly tool: string;
  readonly args: string;
  readonly after: number;
  readonly state: SavedApprovalState;
}

/** 저장에 드는 결말. 실행이 남긴 것과 결정이 두 번 404 였던 것이다. */
type SavedOutcome = Extract<
  Outcome,
  { readonly kind: "finished" | "failed" | "unfinished" | "expired" }
>;

interface SavedExchange {
  readonly request: string;
  readonly runId: string;
  readonly tools: readonly ToolCall[];
  readonly approvals: readonly SavedApproval[];
  /** null 이면 다시 붙을 교환이다. 도구 줄과 결정의 기록은 비어 있다. */
  readonly outcome: SavedOutcome | null;
}

/** 저장한 대화. 판과 묶음은 앞에 둔다. */
export interface Saved {
  readonly version: typeof VERSION;
  readonly bundle: Bundle;
  readonly exchanges: readonly SavedExchange[];
  readonly continueFrom: string | null;
  readonly reattach: string | null;
}

/** 대화에서 저장할 몫. 묶음은 부르는 쪽이 든다. */
export function snapshotOf(conversation: Conversation): Omit<Saved, "version" | "bundle"> {
  const { continueFrom, reattach } = conversation;
  const exchanges = conversation.exchanges.flatMap((exchange): SavedExchange[] => {
    const { request, runId, outcome } = exchange;
    if (runId === null) {
      return [];
    }
    const settled = savedOutcome(outcome);
    if (settled !== null) {
      const approvals = exchange.approvals.flatMap(savedApproval);
      return [{ request, runId, tools: exchange.tools, approvals, outcome: settled }];
    }
    return runId === reattach ? [{ request, runId, tools: [], approvals: [], outcome: null }] : [];
  });
  return { exchanges, continueFrom, reattach };
}

function savedOutcome(outcome: Outcome | null): SavedOutcome | null {
  switch (outcome?.kind) {
    case "finished":
    case "failed":
    case "unfinished":
    case "expired":
      return outcome;
    default:
      return null;
  }
}

function savedApproval(approval: Approval): SavedApproval[] {
  const { state } = approval;
  return state.kind === "waiting" ? [] : [{ ...approval, state }];
}

/** 저장한 대화를 화면의 대화로 되돌린다. 다시 붙을 교환은 도는 교환이고, 읽기 영역은 비어 있다. */
export function conversationOf(saved: Saved): Conversation {
  const exchanges: Exchange[] = saved.exchanges.map((exchange, index) => ({
    id: index,
    request: exchange.request,
    runId: exchange.runId,
    calling: [],
    tools: exchange.tools,
    approvals: exchange.approvals,
    outcome: exchange.outcome,
  }));
  // 용량 때문에 다시 붙을 교환의 요청 글까지 뺐으면 빈 요청의 교환으로 다시 붙는다. 화면은 빈 요청을 그리지 않는다.
  const last = exchanges.at(-1);
  if (saved.reattach !== null && (last?.outcome !== null || last.runId !== saved.reattach)) {
    exchanges.push({
      id: exchanges.length,
      request: "",
      runId: saved.reattach,
      calling: [],
      tools: [],
      approvals: [],
      outcome: null,
    });
  }
  return {
    exchanges,
    continueFrom: saved.continueFrom,
    reattach: saved.reattach,
    announcements: [],
    nextId: exchanges.length,
    errorStreak: 0,
    restarted: false,
  };
}

/** 위젯 창의 sessionStorage. 막힌 저장소(샌드박스의 SecurityError 등)면 null 이고, 그때는 메모리로만 이어 간다. */
export function sessionStore(): Storage | null {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

export type Loaded =
  /** 저장이 없다. 새 탭이거나 저장소에 닿지 못한다. */
  | { readonly kind: "none" }
  /** 판이 다르거나 모양이 틀렸다. 부르는 쪽이 지운다. */
  | { readonly kind: "invalid" }
  | { readonly kind: "saved"; readonly saved: Saved };

export function load(storage: Storage | null, key: string): Loaded {
  let text: string | null;
  try {
    text = storage?.getItem(key) ?? null;
  } catch {
    return { kind: "none" };
  }
  if (text === null) {
    return { kind: "none" };
  }
  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    return { kind: "invalid" };
  }
  const saved = readSaved(value);
  return saved === null ? { kind: "invalid" } : { kind: "saved", saved };
}

/**
 * 저장한다. 담을 것이 없으면 키를 지운다. 용량을 넘으면 오래된 교환부터 하나씩 빼며 다시 쓰고, 교환을 다 빼도 넘으면
 * 키를 지워 앞서 저장한 것이 남지 않게 한다.
 */
export function save(
  storage: Storage | null,
  key: string,
  bundle: Bundle,
  snapshot: Omit<Saved, "version" | "bundle">,
): void {
  if (storage === null) {
    return;
  }
  const { exchanges, continueFrom, reattach } = snapshot;
  if (exchanges.length > 0 || continueFrom !== null || reattach !== null) {
    for (let dropped = 0; dropped <= exchanges.length; dropped += 1) {
      const saved: Saved = {
        version: VERSION,
        bundle,
        exchanges: exchanges.slice(dropped),
        continueFrom,
        reattach,
      };
      try {
        storage.setItem(key, JSON.stringify(saved));
        return;
      } catch {
        // 용량을 넘었다. 오래된 교환을 하나 더 뺀다.
      }
    }
  }
  remove(storage, key);
}

export function remove(storage: Storage | null, key: string): void {
  try {
    storage?.removeItem(key);
  } catch {
    // 저장소에 닿지 못하면 지울 것도 없다.
  }
}

// --- 모양 검사 ---
//
// 읽은 값에서 같은 모양의 값을 새로 짓는다. 하나라도 어긋나면 null 이다.

function readSaved(value: unknown): Saved | null {
  if (
    typeof value !== "object" ||
    value === null ||
    !("version" in value) ||
    value.version !== VERSION ||
    !("bundle" in value) ||
    !("exchanges" in value) ||
    !("continueFrom" in value) ||
    !("reattach" in value)
  ) {
    return null;
  }
  const bundle = readBundle(value.bundle);
  const continueFrom = readNullableString(value.continueFrom);
  const reattach = readNullableString(value.reattach);
  const exchanges = readList(value.exchanges, readExchange);
  if (
    bundle === null ||
    continueFrom === undefined ||
    reattach === undefined ||
    exchanges === null ||
    // 요청 글만 든 교환은 다시 붙을 교환 하나뿐이고 맨 끝이다.
    exchanges.some(
      (exchange, index) =>
        exchange.outcome === null &&
        (exchange.runId !== reattach || index !== exchanges.length - 1),
    )
  ) {
    return null;
  }
  return { version: VERSION, bundle, exchanges, continueFrom, reattach };
}

function readBundle(value: unknown): Bundle | null {
  if (
    typeof value !== "object" ||
    value === null ||
    !("iss" in value) ||
    !("sub" in value) ||
    typeof value.iss !== "string" ||
    typeof value.sub !== "string"
  ) {
    return null;
  }
  return { iss: value.iss, sub: value.sub };
}

function readExchange(value: unknown): SavedExchange | null {
  if (
    typeof value !== "object" ||
    value === null ||
    !("request" in value) ||
    !("runId" in value) ||
    !("tools" in value) ||
    !("approvals" in value) ||
    !("outcome" in value) ||
    typeof value.request !== "string" ||
    typeof value.runId !== "string"
  ) {
    return null;
  }
  const tools = readList(value.tools, readTool);
  const approvals = readList(value.approvals, readApproval);
  const outcome = value.outcome === null ? null : readOutcome(value.outcome);
  if (tools === null || approvals === null || outcome === undefined) {
    return null;
  }
  return { request: value.request, runId: value.runId, tools, approvals, outcome };
}

function readTool(value: unknown): ToolCall | null {
  if (
    typeof value !== "object" ||
    value === null ||
    !("tool" in value) ||
    !("ok" in value) ||
    typeof value.tool !== "string" ||
    typeof value.ok !== "boolean"
  ) {
    return null;
  }
  return { tool: value.tool, ok: value.ok };
}

function readApproval(value: unknown): SavedApproval | null {
  if (
    typeof value !== "object" ||
    value === null ||
    !("pauseId" in value) ||
    !("tool" in value) ||
    !("args" in value) ||
    !("after" in value) ||
    !("state" in value) ||
    typeof value.pauseId !== "number" ||
    !Number.isSafeInteger(value.pauseId) ||
    typeof value.tool !== "string" ||
    typeof value.args !== "string" ||
    typeof value.after !== "number" ||
    !Number.isSafeInteger(value.after)
  ) {
    return null;
  }
  const state = readApprovalState(value.state);
  if (state === null) {
    return null;
  }
  return { pauseId: value.pauseId, tool: value.tool, args: value.args, after: value.after, state };
}

function readApprovalState(value: unknown): SavedApprovalState | null {
  if (typeof value !== "object" || value === null || !("kind" in value)) {
    return null;
  }
  switch (value.kind) {
    case "approved":
      return { kind: "approved" };
    case "expired":
      return { kind: "expired" };
    case "denied":
      return "reason" in value && typeof value.reason === "string"
        ? { kind: "denied", reason: value.reason }
        : null;
    default:
      return null;
  }
}

/** 결말. 어긋나면 undefined 다(null 은 다시 붙을 교환이라 부르는 쪽이 먼저 가른다). */
function readOutcome(value: unknown): SavedOutcome | undefined {
  if (typeof value !== "object" || value === null || !("kind" in value)) {
    return undefined;
  }
  switch (value.kind) {
    case "finished":
      return "output" in value && typeof value.output === "string"
        ? { kind: "finished", output: value.output }
        : undefined;
    case "failed": {
      if (!("cause" in value) || !("runId" in value) || typeof value.runId !== "string") {
        return undefined;
      }
      const cause = readCause(value.cause);
      return cause === undefined ? undefined : { kind: "failed", cause, runId: value.runId };
    }
    case "unfinished": {
      if (!("runId" in value)) {
        return undefined;
      }
      const runId = readNullableString(value.runId);
      return runId === undefined ? undefined : { kind: "unfinished", runId };
    }
    case "expired":
      return { kind: "expired" };
    default:
      return undefined;
  }
}

// 실패 원인(ADR 0031). 빠지거나 남는 원인이 있으면 `satisfies` 가 컴파일에서 깨진다.
const CAUSES = {
  conversation_summary: "conversation_summary",
  timeout: "timeout",
  tool_connection: "tool_connection",
  model_call: "model_call",
  tool_failure: "tool_failure",
  loop_limit: "loop_limit",
  resume_mismatch: "resume_mismatch",
  agent_code: "agent_code",
  other: "other",
} satisfies { readonly [K in FailureCause]: K };

const KNOWN_CAUSES = Object.values(CAUSES);

/**
 * 실패 원인. 계약 밖의 원인도 받은 그대로 그려지듯(organisms/FailureAlert 가 모르는 값으로 다룬다) 저장에서도 지우지
 * 않고, 모르는 글자는 그것과 같은 알림인 `other` 로 읽는다. 글자도 null 도 아니면 undefined 다.
 */
function readCause(value: unknown): FailureCause | null | undefined {
  if (value === null) {
    return null;
  }
  if (typeof value !== "string") {
    return undefined;
  }
  return KNOWN_CAUSES.find((cause) => cause === value) ?? "other";
}

function readNullableString(value: unknown): string | null | undefined {
  return value === null || typeof value === "string" ? value : undefined;
}

function readList<T>(value: unknown, read: (item: unknown) => T | null): T[] | null {
  if (!Array.isArray(value)) {
    return null;
  }
  const items: readonly unknown[] = value;
  const list: T[] = [];
  for (const item of items) {
    const parsed = read(item);
    if (parsed === null) {
      return null;
    }
    list.push(parsed);
  }
  return list;
}
