import { describe, expect, it } from "vitest";
import type { Plugin, PluginRow } from "../../api/plugins";
import { disabledFor } from "./disabledPlugins";

interface Wiring {
  readonly enabled?: boolean;
  readonly mcp?: readonly string[];
  readonly model?: string | null;
  readonly skills?: readonly string[];
}

/** 매니페스트를 읽은 보통 행. 에이전트가 이름으로 고르는 것(`mcp`, `model`, `skills`)을 정한다. */
function row(kind: Plugin["kind"], name: string, wiring: Wiring = {}): Plugin {
  const { enabled = true, mcp = [], model = null, skills = [] } = wiring;
  return {
    kind,
    name,
    enabled,
    manifest: {
      schema_version: "1",
      kind,
      name,
      version: "0.1.0",
      entrypoint: null,
      mcp: [...mcp],
      requires_approval: [],
      conversation_limit: null,
      max_turns: null,
      max_tool_calls: null,
      model,
      skills: [...skills],
      provider: null,
      model_id: null,
      max_tokens: null,
      temperature: null,
      base_url: null,
      api_key_env: null,
      server: null,
    },
  };
}

/** 매니페스트를 읽지 못한 표지 행. 켜져 있는지 말하지 못한다. */
function marker(kind: Plugin["kind"], name: string): PluginRow {
  return { kind, name, enabled: false, reason: "매니페스트를 읽을 수 없다" };
}

describe("disabledFor", () => {
  it("목록이 없거나 에이전트를 모르면 미리 알 수 없어 비어 있다", () => {
    expect(disabledFor("calc", undefined)).toEqual([]);
    expect(disabledFor(null, [row("agent", "calc", { enabled: false })])).toEqual([]);
  });

  it("목록에 에이전트가 없거나 에이전트 행이 표지면 비어 있다", () => {
    expect(disabledFor("calc", [row("mcp", "fixture", { enabled: false })])).toEqual([]);
    expect(
      disabledFor("calc", [marker("agent", "calc"), row("mcp", "fixture", { enabled: false })]),
    ).toEqual([]);
  });

  it("꺼진 에이전트와 에이전트가 쓰는 꺼진 MCP 를 센다", () => {
    const rows = [
      row("agent", "calc", { enabled: false, mcp: ["fixture", "other"] }),
      row("mcp", "fixture", { enabled: false }),
      row("mcp", "other"),
    ];

    expect(disabledFor("calc", rows)).toEqual(["에이전트 calc", "MCP fixture"]);
  });

  it("에이전트가 고른 모델이 꺼졌으면 세고, 고르지 않은 모델이 꺼진 것은 세지 않는다", () => {
    const rows = [
      row("agent", "calc", { model: "sonnet" }),
      row("model", "sonnet", { enabled: false }),
      row("model", "haiku", { enabled: false }),
    ];
    const otherOnly = [
      row("agent", "calc", { model: "sonnet" }),
      row("model", "sonnet"),
      row("model", "haiku", { enabled: false }),
    ];

    expect(disabledFor("calc", rows)).toEqual(["모델 sonnet"]);
    expect(disabledFor("calc", otherOnly)).toEqual([]);
  });

  it("model 을 적지 않은 에이전트는 꺼진 모델이 있어도 미리 막지 않는다", () => {
    const rows = [row("agent", "calc"), row("model", "sonnet", { enabled: false })];

    expect(disabledFor("calc", rows)).toEqual([]);
  });

  it("고른 모델의 행이 표지면 꺼짐으로 세지 않는다", () => {
    const rows = [row("agent", "calc", { model: "sonnet" }), marker("model", "sonnet")];

    expect(disabledFor("calc", rows)).toEqual([]);
  });

  it("고른 스킬이 꺼졌으면 매니페스트에 적힌 순서로 센다", () => {
    const rows = [
      row("agent", "calc", { skills: ["review", "docs", "idle"] }),
      row("skill", "docs", { enabled: false }),
      row("skill", "review", { enabled: false }),
      row("skill", "idle"),
    ];

    expect(disabledFor("calc", rows)).toEqual(["스킬 review", "스킬 docs"]);
  });

  it("고르지 않은 스킬이 꺼진 것과 표지인 스킬 행은 세지 않는다", () => {
    const rows = [
      row("agent", "calc", { skills: ["review"] }),
      row("skill", "docs", { enabled: false }),
      marker("skill", "review"),
    ];

    expect(disabledFor("calc", rows)).toEqual([]);
  });

  it("같은 이름의 꺼진 모델 행이 있어도 고른 스킬로 세지 않는다", () => {
    const rows = [
      row("agent", "calc", { skills: ["review"] }),
      row("model", "review", { enabled: false }),
    ];

    expect(disabledFor("calc", rows)).toEqual([]);
  });

  it("꺼진 것이 여럿이면 에이전트, MCP, 모델, 스킬의 차례로 쌓는다", () => {
    const rows = [
      row("agent", "calc", {
        enabled: false,
        mcp: ["fixture"],
        model: "sonnet",
        skills: ["review"],
      }),
      row("skill", "review", { enabled: false }),
      row("model", "sonnet", { enabled: false }),
      row("mcp", "fixture", { enabled: false }),
    ];

    expect(disabledFor("calc", rows)).toEqual([
      "에이전트 calc",
      "MCP fixture",
      "모델 sonnet",
      "스킬 review",
    ]);
  });
});
