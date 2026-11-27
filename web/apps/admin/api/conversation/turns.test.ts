import { describe, expect, it } from "vitest";
import {
  denied,
  failed,
  finished,
  granted,
  llm,
  paused,
  resumed,
  started,
  summarized,
  toolCalled,
  trace,
} from "../../testing/events";
import { RequestFailure } from "../failure";
import type { Trace } from "../traces";
import { EARLIER_CAP, hasOutcome, pollInterval, readEarlier, turnOf } from "./turns";

const T0 = "2026-11-27T01:00:00+00:00";

describe("turnOf", () => {
  it("요청과 출력을 실행 하나의 차례로 묶는다", () => {
    const turn = turnOf(
      trace("r1", [
        started("r1"),
        llm("r1"),
        finished("r1", "답이다", "2026-11-27T01:00:05+00:00"),
      ]),
    );
    expect(turn).toMatchObject({
      runId: "r1",
      agent: "support-bot",
      principal: "operator",
      requestingAccount: "kim.dev",
      request: "r1의 요청",
      startedAt: T0,
      outcome: { kind: "finished", output: "답이다", at: "2026-11-27T01:00:05+00:00" },
    });
  });

  it("도구 호출은 이름과 성공 여부만 차례로 든다", () => {
    const turn = turnOf(
      trace("r1", [
        started("r1"),
        toolCalled("r1", "search", "ok"),
        toolCalled("r1", "mail", "error"),
        finished("r1", "끝"),
      ]),
    );
    expect(turn.tools).toEqual([
      { tool: "search", ok: true },
      { tool: "mail", ok: false },
    ]);
  });

  it("대화 요약 이벤트와 모델 호출은 차례에 싣지 않는다", () => {
    const turn = turnOf(trace("r1", [started("r1"), summarized("r1"), llm("r1")]));
    expect(turn.tools).toEqual([]);
    expect(turn.approvals).toEqual([]);
    expect(turn.outcome).toEqual({ kind: "running", step: "tool" });
  });

  it("실패 이벤트는 실패의 글을 든다", () => {
    const turn = turnOf(trace("r1", [started("r1"), failed("r1", "모델이 답하지 않았다")]));
    expect(turn.outcome).toMatchObject({ kind: "failed", error: "모델이 답하지 않았다" });
  });

  it("결정이 아직 없는 일시정지는 기다리는 승인으로 든다", () => {
    const turn = turnOf(trace("r1", [started("r1"), paused("r1", "mail")]));
    expect(turn.approvals).toEqual([{ state: "waiting", tool: "mail", at: T0, pauseIndex: 1 }]);
    expect(turn.outcome).toEqual({ kind: "paused" });
  });

  it("승인은 결정한 계정과 시각을 들고, 결정한 계정이 비면 주체 이름을 쓴다", () => {
    const withAccount = turnOf(
      trace("r1", [
        started("r1"),
        paused("r1", "mail"),
        granted("r1", "lee.ops", "2026-11-27T01:00:09+00:00"),
        resumed("r1"),
        finished("r1", "보냈다"),
      ]),
    );
    expect(withAccount.approvals).toEqual([
      {
        state: "granted",
        tool: "mail",
        at: "2026-11-27T01:00:09+00:00",
        by: "lee.ops",
        pauseIndex: 1,
      },
    ]);
    const withoutAccount = turnOf(
      trace("r1", [started("r1"), paused("r1", "mail"), granted("r1", null), resumed("r1")]),
    );
    expect(withoutAccount.approvals[0]).toMatchObject({ state: "granted", by: "operator" });
  });

  it("거부는 사유를 든다", () => {
    const turn = turnOf(
      trace("r1", [
        started("r1"),
        paused("r1", "mail"),
        denied("r1", "lee.ops", "보내지 마라"),
        finished("r1", "안 보냈다"),
      ]),
    );
    expect(turn.approvals[0]).toMatchObject({
      state: "denied",
      by: "lee.ops",
      reason: "보내지 마라",
    });
  });

  it("일시정지의 자리는 이벤트의 0부터 센 인덱스다", () => {
    const turn = turnOf(
      trace("r1", [
        started("r1"),
        toolCalled("r1", "a", "ok"),
        paused("r1", "mail"),
        granted("r1", "lee.ops"),
        resumed("r1"),
        paused("r1", "pay"),
      ]),
    );
    expect(turn.approvals.map((approval) => approval.pauseIndex)).toEqual([2, 5]);
    expect(turn.approvals.map((approval) => approval.state)).toEqual(["granted", "waiting"]);
  });

  it("실행 중의 단계는 마지막 이벤트의 다음 일로 짐작한다", () => {
    expect(turnOf(trace("r1", [started("r1")])).outcome).toEqual({
      kind: "running",
      step: "model",
    });
    expect(turnOf(trace("r1", [started("r1"), llm("r1")])).outcome).toEqual({
      kind: "running",
      step: "tool",
    });
    const afterTool = trace("r1", [started("r1"), llm("r1"), toolCalled("r1", "a", "ok")]);
    expect(turnOf(afterTool).outcome).toEqual({ kind: "running", step: "model" });
  });
});

describe("hasOutcome", () => {
  it("마지막 이벤트가 끝남, 실패, 일시정지면 결말이 있다", () => {
    expect(hasOutcome(trace("r", [started("r"), finished("r", "")]))).toBe(true);
    expect(hasOutcome(trace("r", [started("r"), failed("r", "")]))).toBe(true);
    expect(hasOutcome(trace("r", [started("r"), paused("r", "t")]))).toBe(true);
  });

  it("승인으로 다시 도는 실행은 앞의 일시정지가 남아 있어도 결말이 없다", () => {
    expect(
      hasOutcome(trace("r", [started("r"), paused("r", "t"), granted("r", null), resumed("r")])),
    ).toBe(false);
  });

  it("결말 없는 실행은 결말이 없다", () => {
    expect(hasOutcome(trace("r", [started("r"), llm("r")]))).toBe(false);
  });
});

describe("pollInterval", () => {
  const LAST = "2026-11-27T01:00:10+00:00";
  const lastMs = Date.parse(LAST);
  const running = trace("r", [started("r"), llm("r", LAST)]);

  it("데이터가 없으면 3000이다", () => {
    expect(pollInterval(undefined, 300, lastMs)).toBe(3000);
  });

  it("결말이 없고 제한 시간 안이면 3000이다", () => {
    expect(pollInterval(running, 300, lastMs + 299_999)).toBe(3000);
  });

  it("마지막 이벤트 뒤 실행 제한 시간이 지나면 0이다", () => {
    expect(pollInterval(running, 300, lastMs + 300_000)).toBe(0);
  });

  it("결말이 있으면 0이다", () => {
    expect(pollInterval(trace("r", [started("r"), finished("r", "", LAST)]), 300, lastMs)).toBe(0);
  });
});

describe("readEarlier", () => {
  function chain(length: number): Map<string, Trace> {
    // r1 이 가장 오래된 실행이고 r<length> 가 가장 최근이다.
    const traces = new Map<string, Trace>();
    for (let index = 1; index <= length; index += 1) {
      const id = `r${String(index)}`;
      const previous = index === 1 ? null : `r${String(index - 1)}`;
      traces.set(id, trace(id, [started(id, previous), finished(id, "")]));
    }
    return traces;
  }

  function readerOf(traces: Map<string, Trace>, reads: string[] = []) {
    return (runId: string): Promise<Trace> => {
      reads.push(runId);
      const found = traces.get(runId);
      return found === undefined
        ? Promise.reject(new RequestFailure(404, null))
        : Promise.resolve(found);
    };
  }

  it("앞 실행이 없으면 아무것도 읽지 않는다", async () => {
    const reads: string[] = [];
    const result = await readEarlier(null, "end", readerOf(new Map(), reads));
    expect(result).toEqual({ traces: [], end: "start" });
    expect(reads).toEqual([]);
  });

  it("앞 실행을 하나씩 거슬러 읽고 첫 실행부터 돌려준다", async () => {
    const reads: string[] = [];
    const result = await readEarlier("r3", "r4", readerOf(chain(3), reads));
    expect(result.end).toBe("start");
    expect(result.traces.map((item) => item.run_id)).toEqual(["r1", "r2", "r3"]);
    expect(reads).toEqual(["r3", "r2", "r1"]);
  });

  it("끝 실행을 뺀 상한 100개에서 멈추고 더 앞이 있음을 알린다", async () => {
    const reads: string[] = [];
    const result = await readEarlier("r150", "r151", readerOf(chain(150), reads));
    expect(EARLIER_CAP).toBe(100);
    expect(result.end).toBe("cap");
    expect(result.traces).toHaveLength(100);
    expect(result.traces[0]?.run_id).toBe("r51");
    expect(result.traces[99]?.run_id).toBe("r150");
    expect(reads).toHaveLength(100);
  });

  it("딱 100개로 첫 실행에 닿으면 상한이 아니라 처음이다", async () => {
    const result = await readEarlier("r100", "r101", readerOf(chain(100)));
    expect(result.end).toBe("start");
    expect(result.traces).toHaveLength(100);
  });

  it("앞 실행이 404면 읽은 데까지 돌려주고 끊겼다고 알린다", async () => {
    const traces = chain(3);
    traces.delete("r1");
    const result = await readEarlier("r3", "r4", readerOf(traces));
    expect(result.end).toBe("broken");
    expect(result.traces.map((item) => item.run_id)).toEqual(["r2", "r3"]);
  });

  it("앞 실행이 읽히지 않아 500이면 끊겼다고 알린다", async () => {
    const result = await readEarlier("r2", "r3", (runId) =>
      runId === "r2"
        ? Promise.resolve(trace("r2", [started("r2", "r1"), finished("r2", "")]))
        : Promise.reject(new RequestFailure(500, null)),
    );
    expect(result.end).toBe("broken");
    expect(result.traces.map((item) => item.run_id)).toEqual(["r2"]);
  });

  it("지난 실행으로 돌아오는 순환은 거기서 끊는다", async () => {
    const traces = new Map<string, Trace>([
      ["a", trace("a", [started("a", "b"), finished("a", "")])],
      ["b", trace("b", [started("b", "a"), finished("b", "")])],
    ]);
    const result = await readEarlier("a", "end", readerOf(traces));
    expect(result.end).toBe("broken");
    expect(result.traces.map((item) => item.run_id)).toEqual(["b", "a"]);
  });

  it("끝 실행으로 돌아오는 순환도 끊는다", async () => {
    const traces = new Map<string, Trace>([
      ["a", trace("a", [started("a", "end"), finished("a", "")])],
    ]);
    const result = await readEarlier("a", "end", readerOf(traces));
    expect(result.end).toBe("broken");
    expect(result.traces.map((item) => item.run_id)).toEqual(["a"]);
  });

  it("서버에 닿지 못한 실패는 끊김이 아니라 읽기의 실패로 던진다", async () => {
    await expect(
      readEarlier("r1", "r2", () => Promise.reject(new RequestFailure(null, null))),
    ).rejects.toBeInstanceOf(RequestFailure);
  });
});
