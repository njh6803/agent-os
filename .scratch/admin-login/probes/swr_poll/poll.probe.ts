// swr_poll — 결말 없는 실행의 트레이스를 3초마다 다시 읽다 조건이 되면 멈추는 규칙(ADR 0063 결정 "도는 실행을 이어
// 보기")을 설치된 SWR 로 지을 수 있는지 잰다. 돌리는 법, 판, 결과는 같은 폴더의 README.md 다.
//
// 무엇을 하나: jsdom 에서 useSWR 을 Testing Library 의 renderHook 으로 띄우고, 가짜 fetcher 가 불린 시각을 스스로
// 적는다. 시계는 vitest 의 가짜 시계(setTimeout·clearTimeout·setInterval·clearInterval·Date)이고, 100ms 씩 act 안에서
// 밀어 React 가 그 사이마다 그리게 한다. 창의 가려짐은 document.visibilityState 를 이 프로브의 getter 로 덮고
// visibilitychange 를 문서에 쏴서 흉내 낸다. 데이터는 트레이스의 대역(상태, 이벤트 수, 마지막 이벤트 시각)이다.
//
// 회차와 표지: 회차마다 재려는 상황이 실제로 났다는 표지를 적어 둔다(예: 일시정지 데이터를 받은 함수가 0 을
// 돌려줬다, 가려진 동안 SWR 이 visibilityState 를 읽었다, 주기 읽기 하나가 실패로 끝났다). 표지가 하나라도 없거나
// 예외로 끝난 회차는 측정이 아니라고 세고, 그런 회차가 있으면 afterAll 이 던져 종료 코드가 0 이 아니다. 결과(facts)는
// expected.json 의 스냅샷과 견주고 다르면 역시 던진다. 스냅샷이 없으면 이 회차의 결과로 쓰고 던진다(지우고 두 번 돌리면
// 다시 박힌다). 스냅샷은 미리 적은 기대가 아니라 첫 측정을 받아 적은 것이다.

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { act, cleanup, renderHook } from "@testing-library/react";
import { createElement, type ReactNode, useEffect, useState } from "react";
import useSWR, { SWRConfig, type SWRConfiguration } from "swr";
import { afterAll, describe, expect, it, vi } from "vitest";

const PROBE_DIR = dirname(fileURLToPath(import.meta.url));
const EXPECTED = join(PROBE_DIR, "expected.json");
const RESULTS = join(tmpdir(), "agent-os-swr-poll-results.json");

const T0 = Date.UTC(2026, 10, 24, 0, 0, 0);
const POLL_MS = 3000;
const STALE_MS = 600_000;
const STEP_MS = 100;
// 키 모양은 앱의 traceKeys.one 을 흉내 냈다. 값은 아무래도 같다.
const KEY = ["trace", 0, "run-probe"] as const;

/**
 * 앱의 읽기 정책(web/apps/admin/hooks/queries/admin/index.ts 의 READ)을 옮긴 것. 첫 회차가 앱 파일의 글과 견준다.
 * 앱이 이 값을 바꾸면 그 회차의 결과가 스냅샷과 달라진다.
 */
const READ = {
  revalidateOnFocus: true,
  revalidateOnReconnect: false,
  refreshInterval: 0,
  shouldRetryOnError: false,
} as const;

type Status = "unfinished" | "finished" | "failed" | "paused";

interface FakeTrace {
  readonly status: Status;
  readonly events: number;
  /** 마지막 이벤트의 시각(절대 ms). */
  readonly lastEventAt: number;
}

class ProbeFailure extends Error {
  readonly status: number | null;
  constructor(status: number | null) {
    super(status === null ? "서버에 닿지 못했다" : `HTTP ${status}`);
    this.status = status;
  }
}

const rel = (): number => Date.now() - T0;
const trace = (status: Status, events: number, lastEventRel: number): FakeTrace => ({
  status,
  events,
  lastEventAt: T0 + lastEventRel,
});
const show = (d: FakeTrace | undefined): string =>
  d === undefined ? "undefined" : `${d.status}/${d.events}/${d.lastEventAt - T0}`;

// ---------------------------------------------------------------------------------------------------------------
// 회차와 표지

interface RoundRecord {
  readonly name: string;
  readonly measured: boolean;
  readonly missing: readonly string[];
  readonly error: string | null;
  readonly facts: Record<string, unknown>;
}

const records: RoundRecord[] = [];

class Round {
  readonly facts: Record<string, unknown> = {};
  private readonly marks = new Map<string, boolean>();
  constructor(required: readonly string[]) {
    for (const label of required) {
      this.marks.set(label, false);
    }
  }
  mark(label: string, observed: boolean): void {
    if (!this.marks.has(label)) {
      throw new Error(`적어 두지 않은 표지: ${label}`);
    }
    if (observed) {
      this.marks.set(label, true);
    }
  }
  fact(name: string, value: unknown): void {
    this.facts[name] = value;
  }
  missing(): string[] {
    return [...this.marks].filter(([, seen]) => !seen).map(([label]) => label);
  }
}

function round(name: string, required: readonly string[], body: (r: Round) => Promise<void>): void {
  it(name, async () => {
    const r = new Round(required);
    let error: string | null = null;
    try {
      await body(r);
    } catch (caught: unknown) {
      error = caught instanceof Error ? `${caught.name}: ${caught.message}` : String(caught);
    } finally {
      teardown();
    }
    const missing = r.missing();
    records.push({ name, measured: error === null && missing.length === 0, missing, error, facts: r.facts });
    expect(error, "회차가 예외로 끝났다").toBeNull();
    expect(missing, "표지가 없는 회차는 측정이 아니다").toEqual([]);
  });
}

// ---------------------------------------------------------------------------------------------------------------
// 장면: 가짜 시계, 가려짐, 가짜 fetcher 의 기록

interface FetchRecord {
  readonly at: number;
  readonly outcome: string;
}
interface DecisionRecord {
  readonly at: number;
  readonly by: "swr" | "effect";
  readonly arg: string;
  readonly returned: number;
}
interface RenderRecord {
  readonly at: number;
  readonly stale: boolean;
}

class Scene {
  readonly fetches: FetchRecord[] = [];
  readonly decisions: DecisionRecord[] = [];
  readonly renders: RenderRecord[] = [];
  readonly hiddenReads: number[] = [];
  readonly visibilityEvents: string[] = [];
  visibility: DocumentVisibilityState = "visible";
  // getter 를 거치지 않고 읽는다. getter 로 읽으면 이 기록이 hiddenReads 에 들어 SWR 의 읽기와 섞인다(첫 판이 그랬다).
  readonly onVisibility = (): void => {
    this.visibilityEvents.push(`${rel()}:${this.visibility}`);
  };
  fetchesIn(from: number, to: number): number[] {
    return this.fetches.filter((f) => f.at >= from && f.at < to).map((f) => f.at);
  }
  decisionsIn(from: number, to: number): string[] {
    return this.decisions
      .filter((d) => d.at >= from && d.at < to)
      .map((d) => `${d.at}@${d.by}:${d.arg}=>${d.returned}`);
  }
}

let current: Scene | null = null;

function begin(): Scene {
  vi.useFakeTimers({
    toFake: ["setTimeout", "clearTimeout", "setInterval", "clearInterval", "Date"],
    now: T0,
  });
  const s = new Scene();
  Object.defineProperty(document, "visibilityState", {
    configurable: true,
    get: () => {
      if (s.visibility === "hidden") {
        s.hiddenReads.push(rel());
      }
      return s.visibility;
    },
  });
  Object.defineProperty(document, "hidden", {
    configurable: true,
    get: () => s.visibility === "hidden",
  });
  document.addEventListener("visibilitychange", s.onVisibility);
  current = s;
  return s;
}

function teardown(): void {
  cleanup();
  if (current !== null) {
    document.removeEventListener("visibilitychange", current.onVisibility);
    current = null;
  }
  Reflect.deleteProperty(document, "visibilityState");
  Reflect.deleteProperty(document, "hidden");
  vi.useRealTimers();
}

/** 가짜 시계를 목표 시각(T0 에서 잰 ms)까지 100ms 씩 act 안에서 민다. */
async function advanceTo(target: number): Promise<void> {
  while (rel() < target) {
    const step = Math.min(STEP_MS, target - rel());
    await act(async () => {
      await vi.advanceTimersByTimeAsync(step);
    });
  }
}

async function setVisibility(s: Scene, state: DocumentVisibilityState): Promise<void> {
  await act(async () => {
    s.visibility = state;
    document.dispatchEvent(new Event("visibilitychange"));
  });
}

type Script = (index: number, at: number) => FakeTrace | ProbeFailure;

function fetcherOf(s: Scene, script: Script): () => Promise<FakeTrace> {
  return async () => {
    const at = rel();
    const out = script(s.fetches.length, at);
    if (out instanceof ProbeFailure) {
      s.fetches.push({ at, outcome: `fail:${out.status ?? "network"}` });
      throw out;
    }
    s.fetches.push({ at, outcome: show(out) });
    return { ...out };
  };
}

/**
 * 규칙. 결말 없음이고 마지막 이벤트 뒤 10분이 안 됐으면 3초, 아니면 0. 아직 데이터가 없을 때(undefined)는 `unknown`
 * 이 정한다.
 */
function decide(d: FakeTrace | undefined, unknown: "poll" | "stop"): number {
  if (d === undefined) {
    return unknown === "poll" ? POLL_MS : 0;
  }
  if (d.status !== "unfinished") {
    return 0;
  }
  return Date.now() - d.lastEventAt < STALE_MS ? POLL_MS : 0;
}

function logged(s: Scene, by: "swr" | "effect", unknown: "poll" | "stop") {
  return (d: FakeTrace | undefined): number => {
    const returned = decide(d, unknown);
    s.decisions.push({ at: rel(), by, arg: show(d), returned });
    return returned;
  };
}

/** 그리는 자리에서 "끝맺지 못한 것으로 보입니다"를 세우는 조건. */
const staleAt = (d: FakeTrace | undefined): boolean =>
  d !== undefined && d.status === "unfinished" && Date.now() - d.lastEventAt >= STALE_MS;

/**
 * refreshInterval 을 주는 갈래.
 * - stable: 회차마다 한 번 지은 함수(그리기마다 같은 것). 모듈 수준 함수나 의존성 없는 useCallback 과 같은 모양.
 * - inline: 그리기마다 새로 짓는 함수.
 * - state: 숫자. 데이터가 바뀔 때 효과(useEffect)가 규칙으로 다시 정해 상태에 둔다.
 * 1a·1c 는 셋을, 1b 는 stable·inline 을, 2a·2d·3a·3b·4a·4b·4c 는 stable·inline 을(이름에 꼴이 없는 2a~2e·3a·3b 는
 * stable), 2f·2g·3c 는 inline 만, 2b·2c·2e 는 stable 만, 4d 는 state 만 돈다.
 */
type Pattern = "stable" | "inline" | "state";

interface MountOptions {
  readonly pattern: Pattern;
  readonly script: Script;
  readonly config?: SWRConfiguration<FakeTrace>;
  /** all 은 앱의 readOf 처럼 data·error·isValidating 을 그리는 동안 읽는다. data 는 data 만 읽는다. */
  readonly reads?: "all" | "data";
  readonly unknown?: "poll" | "stop";
}

interface Shown {
  readonly data: FakeTrace | undefined;
  readonly error: unknown;
  readonly mutate: () => Promise<unknown>;
}

function mount(s: Scene, o: MountOptions) {
  const fetcher = fetcherOf(s, o.script);
  const unknown = o.unknown ?? "poll";
  const stableFn = logged(s, "swr", unknown);
  const reads = o.reads ?? "all";
  function useProbe(): Shown {
    const [ms, setMs] = useState<number>(POLL_MS);
    const refreshInterval =
      o.pattern === "stable" ? stableFn : o.pattern === "inline" ? logged(s, "swr", unknown) : ms;
    const r = useSWR<FakeTrace>(KEY, fetcher, { ...READ, ...o.config, refreshInterval });
    const data = r.data;
    useEffect(() => {
      if (o.pattern === "state") {
        setMs(logged(s, "effect", unknown)(data));
      }
    }, [data]);
    s.renders.push({ at: rel(), stale: staleAt(data) });
    if (reads === "data") {
      return { data, error: undefined, mutate: r.mutate };
    }
    const { error, isValidating } = r;
    void isValidating;
    return { data, error, mutate: r.mutate };
  }
  const wrapper = ({ children }: { readonly children: ReactNode }) =>
    createElement(SWRConfig, { value: { provider: () => new Map() } }, children);
  return renderHook(useProbe, { wrapper });
}

// ---------------------------------------------------------------------------------------------------------------
// 0. 앱의 읽기 정책

describe("0. 앱의 읽기 정책", () => {
  round("0 앱 파일의 READ 가 프로브의 READ 와 같다", ["앱 파일에서 READ 블록을 찾았다"], async (r) => {
    const file = join(PROBE_DIR, "..", "..", "..", "..", "web", "apps", "admin", "hooks", "queries", "admin", "index.ts");
    const text = readFileSync(file, "utf8");
    const block = /export const READ = \{([\s\S]*?)\} as const;/.exec(text);
    r.mark("앱 파일에서 READ 블록을 찾았다", block !== null);
    const inApp = Object.fromEntries(
      [...(block?.[1] ?? "").matchAll(/^\s*(\w+):\s*([^,\n]+),?\s*$/gm)].map((m) => [m[1], m[2]?.trim()]),
    );
    const inProbe = Object.fromEntries(Object.entries(READ).map(([k, v]) => [k, String(v)]));
    r.fact("app", inApp);
    r.fact("same", JSON.stringify(inApp) === JSON.stringify(inProbe));
  });
});

// ---------------------------------------------------------------------------------------------------------------
// 1. 함수가 0 을 돌려주면 멈추는가, 다시 양수가 되면 다시 도는가

/** 0·3초 결말 없음, 6초 일시정지. resumed 가 서면 결말 없음(이벤트 4, 60초). */
function stopThenResume(phase: { resumed: boolean }): Script {
  return (index) => {
    if (phase.resumed) {
      return trace("unfinished", 4, 60_000);
    }
    return index < 2 ? trace("unfinished", 1 + index, index * 3000) : trace("paused", 3, 6000);
  };
}

describe("1. 0 을 돌려주면 멈추고, 다시 양수면 다시 도는가", () => {
  for (const pattern of ["stable", "inline", "state"] as const) {
    round(
      `1a ${pattern}: 일시정지에서 멈추고 60초의 새로 고침이 결말 없음을 읽은 뒤`,
      ["일시정지 데이터로 규칙이 0 을 냈다", "새로 고침이 결말 없음을 읽었다"],
      async (r) => {
        const s = begin();
        const phase = { resumed: false };
        const h = mount(s, { pattern, script: stopThenResume(phase) });
        await advanceTo(60_000);
        r.mark(
          "일시정지 데이터로 규칙이 0 을 냈다",
          s.decisions.some((d) => d.arg.startsWith("paused/") && d.returned === 0),
        );
        phase.resumed = true;
        const before = s.fetches.length;
        await act(async () => {
          await h.result.current.mutate();
        });
        r.mark(
          "새로 고침이 결말 없음을 읽었다",
          s.fetches.length === before + 1 &&
            s.fetches.at(-1)?.outcome === "unfinished/4/60000" &&
            h.result.current.data?.status === "unfinished",
        );
        await advanceTo(90_000);
        r.fact("fetchesUntilStop", s.fetchesIn(0, 6001));
        r.fact("fetchesAfterStopBeforeRefresh", s.fetchesIn(6001, 60_000));
        r.fact("fetchesFromRefresh", s.fetchesIn(60_000, 90_001));
        r.fact("zeroDecisions", s.decisions.filter((d) => d.returned === 0).length);
        r.fact("firstDecisions", s.decisionsIn(0, 6001));
      },
    );
  }

  for (const pattern of ["stable", "inline"] as const) {
    round(
      `1b ${pattern}: 데이터 전(undefined)에 0 을 돌려주는 규칙`,
      ["데이터 전에 규칙이 불려 0 을 냈다", "첫 읽기가 결말 없음을 받았다"],
      async (r) => {
        const s = begin();
        const h = mount(s, { pattern, unknown: "stop", script: () => trace("unfinished", 1, 0) });
        await advanceTo(30_000);
        r.mark(
          "데이터 전에 규칙이 불려 0 을 냈다",
          s.decisions.some((d) => d.arg === "undefined" && d.returned === 0),
        );
        r.mark(
          "첫 읽기가 결말 없음을 받았다",
          s.fetchesIn(0, 1).length === 1 && h.result.current.data?.status === "unfinished",
        );
        r.fact("fetches", s.fetchesIn(0, 30_001));
        r.fact("decisionsFirst5", s.decisionsIn(0, 30_001).slice(0, 5));
      },
    );
  }

  for (const pattern of ["stable", "inline", "state"] as const) {
    round(
      `1c ${pattern}: 1초마다 다시 그려지는 동안의 주기 읽기`,
      ["1초마다 다시 그리기가 서른 번 났다"],
      async (r) => {
        const s = begin();
        const h = mount(s, { pattern, script: () => trace("unfinished", 1, 0) });
        let rerenders = 0;
        for (let k = 1; k <= 30; k++) {
          await advanceTo(k * 1000);
          h.rerender();
          rerenders++;
        }
        const rendersOnTheSecond = s.renders.filter((x) => x.at > 0 && x.at % 1000 === 0).length;
        r.mark("1초마다 다시 그리기가 서른 번 났다", rerenders === 30 && rendersOnTheSecond >= 30);
        r.fact("fetches", s.fetchesIn(0, 30_001));
        // 주기 효과가 다시 돌면 next() 가 규칙을 부른다. 다시 그린 시각(1초 단위)에 규칙이 불렸는지가 그 표시다.
        r.fact("decisionsOnRerenderSeconds", s.decisions.filter((d) => d.at > 0 && d.at % 1000 === 0 && d.at % POLL_MS !== 0).length);
      },
    );
  }
});

// ---------------------------------------------------------------------------------------------------------------
// 2. 가려진 동안 멈추는가, 돌아오면 바로 읽는가

/**
 * 가려짐 갈래의 표지. 둘 다 SWR 이 문서를 가려진 것으로 읽었다는 관찰이다(이 프로브의 getter 가 hidden 을 돌려준
 * 읽기).
 * - tick: 가린 순간의 이벤트 처리(1초 안)를 뺀 뒤, 가려진 동안 주기의 틱이 읽었다. 틱이 visibilityState 를 읽지 않는
 *   갈래(refreshWhenHidden: true 면 `refreshWhenHidden || isVisible()` 에서 앞이 참이라 읽지 않는다)에는 걸지 않는다.
 * - any: 가려진 동안 어느 때든 읽었다. 가린 순간의 포커스 처리(revalidateOnFocus 이고 focusThrottleInterval 이 지났을
 *   때 isActive 를 부른다)가 읽는다.
 * 첫 실행은 2b 에 tick 을 걸어 그 회차가 측정 아님이었다. 위의 까닭으로 2b 를 any 로 바꿨다. 둘째 실행에서 이 프로브의
 * 이벤트 기록이 getter 로 읽어 any 가 SWR 없이도 서는 것을 보고, 기록이 getter 를 거치지 않게 고쳤다(README "판정 기준을
 * 바꾼 것").
 */
type HiddenMark = "tick" | "any";

interface HideCase {
  readonly name: string;
  /** 회차 이름에 꼴이 없는 것(2a~2e 의 첫 판)은 stable 이다. inline 회차는 같은 시각과 데이터로 꼴만 바꾼다. */
  readonly pattern: "stable" | "inline";
  readonly config: SWRConfiguration<FakeTrace>;
  readonly hideAt: number;
  readonly showAt: number;
  readonly until: number;
  readonly marks: readonly HiddenMark[];
}

const HIDDEN_MARK: Record<HiddenMark, string> = {
  tick: "가려진 동안 주기의 틱이 visibilityState 를 hidden 으로 읽었다",
  any: "가려진 동안 SWR 이 visibilityState 를 hidden 으로 읽었다",
};

const hideCases: readonly HideCase[] = [
  {
    name: "2a 앱의 정책: 10.5초에 가리고 70.5초에 돌아온다",
    pattern: "stable",
    config: {},
    hideAt: 10_500,
    showAt: 70_500,
    until: 80_000,
    marks: ["tick"],
  },
  {
    name: "2a inline 앱의 정책: 10.5초에 가리고 70.5초에 돌아온다",
    pattern: "inline",
    config: {},
    hideAt: 10_500,
    showAt: 70_500,
    until: 80_000,
    marks: ["tick"],
  },
  {
    name: "2b 대조 refreshWhenHidden: true: 같은 시각",
    pattern: "stable",
    config: { refreshWhenHidden: true },
    hideAt: 10_500,
    showAt: 70_500,
    until: 80_000,
    marks: ["any"],
  },
  {
    name: "2c 대조 revalidateOnFocus: false: 같은 시각",
    pattern: "stable",
    config: { revalidateOnFocus: false },
    hideAt: 10_500,
    showAt: 70_500,
    until: 80_000,
    marks: ["tick"],
  },
  // 가린 동안 틱이 없고(첫 틱은 3초) 가린 순간은 포커스 처리의 5초 안이라 SWR 이 가려짐을 읽을 자리가 없다.
  // 돌아오는 순간의 읽기만 본다. 그 대조가 2e 다.
  {
    name: "2d 앱의 정책: 0.5초에 가리고 2.5초에 돌아온다",
    pattern: "stable",
    config: {},
    hideAt: 500,
    showAt: 2_500,
    until: 10_000,
    marks: [],
  },
  {
    name: "2d inline 앱의 정책: 0.5초에 가리고 2.5초에 돌아온다",
    pattern: "inline",
    config: {},
    hideAt: 500,
    showAt: 2_500,
    until: 10_000,
    marks: [],
  },
  {
    name: "2e 대조 focusThrottleInterval: 0: 0.5초에 가리고 2.5초에 돌아온다",
    pattern: "stable",
    config: { focusThrottleInterval: 0 },
    hideAt: 500,
    showAt: 2_500,
    until: 10_000,
    marks: ["any"],
  },
];

describe("2. 가려진 동안과 돌아올 때", () => {
  for (const c of hideCases) {
    const required = ["가려짐과 돌아옴의 이벤트가 문서에 났다", ...c.marks.map((m) => HIDDEN_MARK[m])];
    round(
      c.name,
      required,
      async (r) => {
        const s = begin();
        mount(s, { pattern: c.pattern, config: c.config, script: () => trace("unfinished", 1, 0) });
        await advanceTo(c.hideAt);
        await setVisibility(s, "hidden");
        await advanceTo(c.showAt);
        await setVisibility(s, "visible");
        await advanceTo(c.until);
        r.mark(
          "가려짐과 돌아옴의 이벤트가 문서에 났다",
          s.visibilityEvents.includes(`${c.hideAt}:hidden`) && s.visibilityEvents.includes(`${c.showAt}:visible`),
        );
        // 가린 순간의 이벤트 처리 몫(1초 안)은 빼고, 그 뒤 주기의 틱이 읽은 것만 센다.
        const readsByTicks = s.hiddenReads.filter((t) => t >= c.hideAt + 1000 && t < c.showAt);
        const readsWhileHidden = s.hiddenReads.filter((t) => t >= c.hideAt && t < c.showAt);
        if (c.marks.includes("tick")) {
          r.mark(HIDDEN_MARK.tick, readsByTicks.length > 0);
        }
        if (c.marks.includes("any")) {
          r.mark(HIDDEN_MARK.any, readsWhileHidden.length > 0);
        }
        r.fact("hiddenReadTimes", [...new Set(readsWhileHidden)].slice(0, 3));
        r.fact("fetchesBeforeHide", s.fetchesIn(0, c.hideAt));
        r.fact("fetchesWhileHidden", s.fetchesIn(c.hideAt, c.showAt));
        r.fact("fetchesAfterReturn", s.fetchesIn(c.showAt, c.until + 1));
        r.fact("hiddenReadTimesByTicks", [...new Set(readsByTicks)]);
        // 돌아온 뒤 규칙이 불린 시각. 효과가 다시 돌면 그 자리에서 불린다(1c 의 decisionsOnRerenderSeconds 와 같은 표시).
        // inline 회차에만 싣는다. stable 회차의 결과(스냅샷)를 첫 판 그대로 두려고.
        if (c.pattern === "inline") {
          r.fact("decisionsAfterReturn", s.decisionsIn(c.showAt, c.showAt + 6000));
        }
      },
    );
  }

  // 두 번 돌아오는 장면. 2d 는 "시작 뒤 5초 안"의 돌아옴만 쟀다. 여기서는 첫 돌아옴(22초)이 시작 뒤 5초를 한참 넘기고,
  // 두 번째 돌아옴(25초)이 첫 돌아옴에서 3초 뒤다. 2g 는 포커스 처리의 5초 간격을 끈 대조다.
  const twice = { hide1: 20_000, show1: 22_000, hide2: 23_000, show2: 25_000, until: 35_000 } as const;
  const returnTwiceCases: readonly { readonly name: string; readonly config: SWRConfiguration<FakeTrace> }[] = [
    { name: "2f inline 앱의 정책: 20초에 가리고 22초에 돌아온 뒤 23초에 가리고 25초에 돌아온다", config: {} },
    { name: "2g inline 대조 focusThrottleInterval: 0: 2f 와 같은 시각", config: { focusThrottleInterval: 0 } },
  ];
  for (const c of returnTwiceCases) {
    round(c.name, ["가려짐과 돌아옴의 이벤트가 두 번씩 문서에 났다", HIDDEN_MARK.tick], async (r) => {
      const s = begin();
      mount(s, { pattern: "inline", config: c.config, script: () => trace("unfinished", 1, 0) });
      await advanceTo(twice.hide1);
      await setVisibility(s, "hidden");
      await advanceTo(twice.show1);
      await setVisibility(s, "visible");
      await advanceTo(twice.hide2);
      await setVisibility(s, "hidden");
      await advanceTo(twice.show2);
      await setVisibility(s, "visible");
      await advanceTo(twice.until);
      const events = [
        `${twice.hide1}:hidden`,
        `${twice.show1}:visible`,
        `${twice.hide2}:hidden`,
        `${twice.show2}:visible`,
      ];
      r.mark(
        "가려짐과 돌아옴의 이벤트가 두 번씩 문서에 났다",
        events.every((e) => s.visibilityEvents.includes(e)),
      );
      // 첫 가림의 순간(포커스 처리 몫, 1초 안)은 빼고 주기의 틱이 가려짐을 읽었는지 본다.
      r.mark(HIDDEN_MARK.tick, s.hiddenReads.some((x) => x >= twice.hide1 + 1000 && x < twice.show1));
      r.fact("readAtFirstReturn", s.fetchesIn(twice.show1, twice.show1 + 1).length > 0);
      r.fact("readAtSecondReturn", s.fetchesIn(twice.show2, twice.show2 + 1).length > 0);
      r.fact("fetchesBeforeFirstHide", s.fetchesIn(0, twice.hide1));
      r.fact("fetchesWhileHidden", [...s.fetchesIn(twice.hide1, twice.show1), ...s.fetchesIn(twice.hide2, twice.show2)]);
      r.fact("fetchesFromFirstReturn", s.fetchesIn(twice.show1, twice.hide2));
      r.fact("fetchesFromSecondReturn", s.fetchesIn(twice.show2, twice.until + 1));
      r.fact("hiddenReadTimes", [...new Set(s.hiddenReads)]);
    });
  }
});

// ---------------------------------------------------------------------------------------------------------------
// 3. 주기 읽기가 실패한 뒤

/**
 * 3초 읽기가 실패하고 30초에 새로 고침하는 장면. status 가 null 이면 네트워크 실패(응답 없음), 숫자면 그 상태 코드의
 * 응답이다. 앱의 요청 함수(`api/traces` 의 readTrace)는 응답이 없으면 `unreachable(cause)`, 데이터가 아닌 응답이면
 * `failureOf(response.status, error)` 로 RequestFailure(Error 의 하위 클래스, status 필드)를 던진다. ProbeFailure 는 그
 * 모양(Error 의 하위 클래스가 async 함수에서 던져져 거절된 약속, status 필드)을 따르고 봉투(envelope)는 싣지 않는다.
 */
function failThenRefresh(name: string, pattern: "stable" | "inline", status: number | null): void {
  const outcome = `fail:${status ?? "network"}`;
  round(name, ["주기 읽기 하나가 실패로 끝났다", "실패가 남은 동안 규칙이 불렸다"], async (r) => {
    const s = begin();
    const h = mount(s, {
      pattern,
      script: (index) => (index === 1 ? new ProbeFailure(status) : trace("unfinished", 1, 0)),
    });
    await advanceTo(29_000);
    const errorShown = h.result.current.error instanceof ProbeFailure;
    r.mark("주기 읽기 하나가 실패로 끝났다", s.fetches.some((f) => f.at === 3000 && f.outcome === outcome) && errorShown);
    r.mark("실패가 남은 동안 규칙이 불렸다", s.decisions.some((d) => d.at > 3000 && d.at < 29_000));
    r.fact("dataWhileError", show(h.result.current.data));
    await advanceTo(30_000);
    r.fact("fetchesDuringError", s.fetchesIn(3001, 30_000));
    r.fact("decisionsDuringError", s.decisionsIn(3000, 30_000));
    await act(async () => {
      await h.result.current.mutate();
    });
    await advanceTo(45_000);
    r.fact("fetchesFromRefresh", s.fetchesIn(30_000, 45_001));
    r.fact("errorAfterRefresh", h.result.current.error !== undefined);
  });
}

/** 3초 읽기가 401 로 실패하고 20초에 가리고 30.5초에 돌아오는 장면. */
function failThenReturn(name: string, pattern: "stable" | "inline"): void {
  round(name, ["주기 읽기 하나가 실패로 끝났다", "가려짐과 돌아옴의 이벤트가 문서에 났다"], async (r) => {
    const s = begin();
    const h = mount(s, {
      pattern,
      script: (index) => (index === 1 ? new ProbeFailure(401) : trace("unfinished", 1, 0)),
    });
    await advanceTo(19_000);
    r.mark(
      "주기 읽기 하나가 실패로 끝났다",
      s.fetches.some((f) => f.at === 3000 && f.outcome === "fail:401") && h.result.current.error instanceof ProbeFailure,
    );
    r.fact("dataWhileError", show(h.result.current.data));
    await advanceTo(20_000);
    await setVisibility(s, "hidden");
    await advanceTo(30_500);
    await setVisibility(s, "visible");
    await advanceTo(45_000);
    r.mark(
      "가려짐과 돌아옴의 이벤트가 문서에 났다",
      s.visibilityEvents.includes("20000:hidden") && s.visibilityEvents.includes("30500:visible"),
    );
    r.fact("fetchesDuringError", s.fetchesIn(3001, 30_500));
    r.fact("fetchesFromReturn", s.fetchesIn(30_500, 45_001));
    r.fact("errorAfterReturn", h.result.current.error !== undefined);
    // 2a·2d 의 inline 회차와 같은 까닭으로 inline 회차에만 싣는다.
    if (pattern === "inline") {
      r.fact("decisionsAfterReturn", s.decisionsIn(30_500, 36_500));
    }
  });
}

describe("3. 주기 읽기가 실패한 뒤", () => {
  failThenRefresh("3a 네트워크 실패(3초), 30초에 새로 고침", "stable", null);
  failThenRefresh("3a inline 네트워크 실패(3초), 30초에 새로 고침", "inline", null);
  failThenReturn("3b 401 실패(3초), 20초에 가리고 30.5초에 돌아온다", "stable");
  failThenReturn("3b inline 401 실패(3초), 20초에 가리고 30.5초에 돌아온다", "inline");
  failThenRefresh("3c inline 500 실패(3초), 30초에 새로 고침", "inline", 500);
});

// ---------------------------------------------------------------------------------------------------------------
// 4. 마지막 이벤트 뒤 10분

describe("4. 마지막 이벤트 뒤 10분", () => {
  // stable 이 첫 판이고 inline 은 같은 시각과 데이터로 꼴만 바꾼 것이다. 회차 이름의 꼴 자리만 다르다.
  for (const pattern of ["stable", "inline"] as const) {
    round(
      `4a ${pattern}: 이벤트가 -2초에 하나, 15분까지`,
      ["10분을 넘긴 시각에 규칙이 0 을 냈다", "새 이벤트 없이 15분이 흘렀다"],
      async (r) => {
        const s = begin();
        mount(s, { pattern, script: () => trace("unfinished", 1, -2000) });
        await advanceTo(900_000);
        const zero = s.decisions.find((d) => d.arg.startsWith("unfinished/") && d.returned === 0);
        r.mark("10분을 넘긴 시각에 규칙이 0 을 냈다", zero !== undefined && zero.at + 2000 >= STALE_MS);
        r.mark(
          "새 이벤트 없이 15분이 흘렀다",
          rel() >= 900_000 && s.fetches.every((f) => f.outcome === "unfinished/1/-2000"),
        );
        r.fact("fetchCount", s.fetches.length);
        r.fact("lastFetches", s.fetchesIn(590_000, 900_001));
        r.fact("decisionsAroundBoundary", s.decisionsIn(594_000, 900_001));
      },
    );
  }

  for (const pattern of ["stable", "inline"] as const) {
    round(
      `4b ${pattern} 대조: 300초에 새 이벤트, 20분까지`,
      ["새 이벤트를 담은 데이터를 받았다", "새 이벤트 뒤 10분을 넘긴 시각에 규칙이 0 을 냈다"],
      async (r) => {
        const s = begin();
        mount(s, {
          pattern,
          script: (_index, at) => (at < 300_000 ? trace("unfinished", 1, -2000) : trace("unfinished", 2, 300_000)),
        });
        await advanceTo(1_200_000);
        r.mark("새 이벤트를 담은 데이터를 받았다", s.fetches.some((f) => f.outcome === "unfinished/2/300000"));
        const zero = s.decisions.find((d) => d.returned === 0);
        r.mark(
          "새 이벤트 뒤 10분을 넘긴 시각에 규칙이 0 을 냈다",
          zero !== undefined && zero.arg === "unfinished/2/300000" && zero.at - 300_000 >= STALE_MS,
        );
        r.fact("fetchesAround598s", s.fetchesIn(594_000, 606_001));
        r.fact("lastFetches", s.fetchesIn(890_000, 1_200_001));
        r.fact("decisionsAroundBoundary", s.decisionsIn(897_000, 1_200_001));
      },
    );
  }

  for (const pattern of ["stable", "inline"] as const) {
    for (const reads of ["all", "data"] as const) {
      round(
        `4c ${pattern}, 그리는 쪽이 ${reads === "all" ? "data·error·isValidating 을" : "data 만"} 읽을 때 알림이 서는가`,
        ["10분을 넘긴 시각에 규칙이 0 을 냈다"],
        async (r) => {
          const s = begin();
          mount(s, { pattern, reads, script: () => trace("unfinished", 1, -2000) });
          await advanceTo(700_000);
          const zero = s.decisions.find((d) => d.returned === 0);
          r.mark("10분을 넘긴 시각에 규칙이 0 을 냈다", zero !== undefined && zero.at + 2000 >= STALE_MS);
          r.fact("firstStaleRenderAt", s.renders.find((x) => x.stale)?.at ?? null);
          r.fact("rendersFrom590s", s.renders.filter((x) => x.at >= 590_000).map((x) => `${x.at}:${x.stale}`));
          r.fact("lastFetch", s.fetches.at(-1)?.at ?? null);
        },
      );
    }
  }

  round(
    "4d state 대조: 숫자를 데이터가 바뀔 때만 다시 정하면",
    ["효과가 결말 없음 데이터로 간격을 정했다", "새 이벤트 없이 15분이 흘렀다"],
    async (r) => {
      const s = begin();
      mount(s, { pattern: "state", script: () => trace("unfinished", 1, -2000) });
      await advanceTo(900_000);
      r.mark(
        "효과가 결말 없음 데이터로 간격을 정했다",
        s.decisions.some((d) => d.by === "effect" && d.arg === "unfinished/1/-2000"),
      );
      r.mark(
        "새 이벤트 없이 15분이 흘렀다",
        rel() >= 900_000 && s.fetches.every((f) => f.outcome === "unfinished/1/-2000"),
      );
      r.fact("fetchCount", s.fetches.length);
      r.fact("fetchesAfter600s", s.fetchesIn(600_001, 900_001).length);
      r.fact("lastFetch", s.fetches.at(-1)?.at ?? null);
      r.fact("decisions", s.decisionsIn(0, 900_001));
    },
  );
});

// ---------------------------------------------------------------------------------------------------------------
// 판과 마무리

function versionAt(dir: string, name: string): string {
  try {
    const pkg: unknown = JSON.parse(readFileSync(join(dir, "node_modules", name, "package.json"), "utf8"));
    return typeof pkg === "object" && pkg !== null && "version" in pkg ? String(pkg.version) : "?";
  } catch {
    return "없음";
  }
}

afterAll(() => {
  const appDir = process.env.SWR_POLL_APP_DIR ?? "";
  const webDir = process.env.SWR_POLL_WEB_DIR ?? "";
  const versions = {
    swr: versionAt(appDir, "swr"),
    react: versionAt(appDir, "react"),
    "react-dom": versionAt(appDir, "react-dom"),
    "@testing-library/react": versionAt(appDir, "@testing-library/react"),
    vitest: versionAt(webDir, "vitest"),
    jsdom: versionAt(webDir, "jsdom"),
    jsdomUserAgent: navigator.userAgent,
    node: process.version,
    platform: process.platform,
  };
  const unmeasured = records.filter((x) => !x.measured);
  const facts = Object.fromEntries(records.map((x) => [x.name, x.facts]));
  writeFileSync(
    RESULTS,
    `${JSON.stringify({ versions, appDir, webDir, measured: records.length - unmeasured.length, unmeasured, records }, null, 2)}\n`,
  );
  console.log(`swr_poll 판 ${JSON.stringify(versions)}`);
  console.log(`swr_poll 의존성 web/: ${webDir}`);
  console.log(`swr_poll 회차 ${records.length}, 측정 ${records.length - unmeasured.length}, 측정 아님 ${unmeasured.length}`);
  console.log(`swr_poll 원본 기록: ${RESULTS}`);
  for (const x of records) {
    console.log(`swr_poll ${x.measured ? "측정" : "측정 아님"} | ${x.name} | ${JSON.stringify(x.facts)}`);
  }
  if (unmeasured.length > 0) {
    throw new Error(`측정 아닌 회차 ${unmeasured.length}: ${unmeasured.map((x) => x.name).join(", ")}`);
  }
  if (!existsSync(EXPECTED)) {
    writeFileSync(EXPECTED, `${JSON.stringify(facts, null, 2)}\n`);
    throw new Error("expected.json 이 없어 이 회차의 결과로 썼다. 다시 돌려 견준다");
  }
  const expected: unknown = JSON.parse(readFileSync(EXPECTED, "utf8"));
  const want = typeof expected === "object" && expected !== null ? Object.entries(expected) : [];
  const differ = [
    ...want.filter(([name, value]) => JSON.stringify(facts[name]) !== JSON.stringify(value)).map(([name]) => name),
    ...Object.keys(facts).filter((name) => !want.some(([w]) => w === name)),
  ];
  if (differ.length > 0) {
    throw new Error(`expected.json 과 다른 회차: ${differ.join(", ")}`);
  }
  console.log("swr_poll expected.json 과 같다");
});
