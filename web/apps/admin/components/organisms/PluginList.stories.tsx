// 플러그인 목록(admin-style 티켓 05, 그림 mk-plugins, mk-plugins-m). 종류 넷과 표지 줄, 빈 종류, 켜고 끄기의 실패다.
// 표본 값은 그림의 것이다. 틀 없이 그리고, 미리보기의 데코레이터가 본문 칸과 같은 컨테이너를 두른다. 이름이나 스위치를
// 누르면 요청이 가는 행동과 다시 읽은 값을 따르는 스위치는 페이지 시험이 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import type { ReactNode } from "react";
import { expect, fn, within } from "storybook/test";
import type { Plugin, PluginRow } from "../../api/plugins";
import { ConnectionLine } from "../molecules/ConnectionLine";
import { LaunchedConnection } from "../molecules/LaunchedConnection";
import { PluginListView } from "./PluginList";

function manifest(kind: PluginRow["kind"], name: string): Plugin["manifest"] {
  return {
    schema_version: "1",
    kind,
    name,
    version: "0.1.0",
    entrypoint: kind === "agent" ? "agent:Agent" : null,
    mcp: [],
    requires_approval: [],
    conversation_limit: null,
    max_turns: null,
    max_tool_calls: null,
    model: null,
    skills: [],
    provider: null,
    model_id: null,
    max_tokens: null,
    temperature: null,
    base_url: null,
    api_key_env: null,
    server: null,
  };
}

/** 그림 mk-plugins 의 목록. 모델은 등록된 것이 없다. */
const ROWS: readonly PluginRow[] = [
  { kind: "agent", name: "calc", enabled: true, manifest: manifest("agent", "calc") },
  {
    kind: "agent",
    name: "support-bot",
    enabled: false,
    manifest: manifest("agent", "support-bot"),
  },
  { kind: "mcp", name: "everything", enabled: true, manifest: manifest("mcp", "everything") },
  { kind: "mcp", name: "filesystem", enabled: true, reason: "[server] 표에 command가 없다" },
  {
    kind: "skill",
    name: "refund-policy",
    enabled: false,
    manifest: manifest("skill", "refund-policy"),
  },
];

const meta = {
  title: "organisms/PluginList",
  component: PluginListView,
  args: {
    data: ROWS,
    error: undefined,
    isValidating: false,
    onRefresh: fn(),
    onSetEnabled: fn(),
    switchFailure: null,
    onSwitchFailure: fn(),
  },
} satisfies Meta<typeof PluginListView>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 종류 넷이 차례대로 개수와 함께 서고, 줄마다 이름이 스위치의 이름이며 끝에 "매니페스트" 링크가 있다. */
export const List: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("heading", { level: 1 })).toHaveTextContent("플러그인 5");
    const kinds = canvas.getAllByRole("heading", { level: 2 }).map((h) => h.textContent);
    await expect(kinds).toEqual(["에이전트 2", "MCP 2", "스킬 1", "모델 0"]);
    await expect(canvas.getByRole("switch", { name: "calc" })).toBeChecked();
    await expect(canvas.getByRole("switch", { name: "support-bot" })).not.toBeChecked();
    const links = canvas.getAllByRole("link", { name: "매니페스트" });
    await expect(links).toHaveLength(5);
    // 포인터로 누르는 목표는 24px 이상이다(명세 "접근성과 폭").
    for (const link of links) {
      await expect(link.getBoundingClientRect().height).toBeGreaterThanOrEqual(24);
    }
    // 본문은 넓어도 최대 폭 content(880px)를 넘지 않는다.
    const region = canvas.getByRole("region", { name: "플러그인 5" });
    await expect(region.getBoundingClientRect().width).toBeLessThanOrEqual(880);
    // 표지 줄과 빈 종류는 아이콘과 한 줄이다.
    await expect(
      canvas.getByText("읽을 수 없는 매니페스트: [server] 표에 command가 없다"),
    ).toBeVisible();
    await expect(canvas.queryByText("로더가 생기기 전에는 효과가 없다")).toBeNull();
    await expect(canvas.getByText("등록된 것이 없다")).toBeVisible();
  },
};

/** 접속 확인이 있는 행의 이름과 그 행에 보일 것(connection-check 티켓 04). */
const CONNECTION_ROWS: readonly PluginRow[] = [
  { kind: "mcp", name: "docs", enabled: true, manifest: manifest("mcp", "docs") },
  { kind: "mcp", name: "search", enabled: true, manifest: manifest("mcp", "search") },
  { kind: "mcp", name: "billing", enabled: true, manifest: manifest("mcp", "billing") },
  { kind: "mcp", name: "wiki", enabled: true, manifest: manifest("mcp", "wiki") },
  { kind: "mcp", name: "files", enabled: true, manifest: manifest("mcp", "files") },
  { kind: "mcp", name: "shell", enabled: true, manifest: manifest("mcp", "shell") },
  { kind: "mcp", name: "archive", enabled: false, manifest: manifest("mcp", "archive") },
  { kind: "mcp", name: "broken", enabled: true, reason: "[server] 표에 command가 없다" },
  { kind: "model", name: "sonnet", enabled: true, manifest: manifest("model", "sonnet") },
  { kind: "model", name: "haiku", enabled: false, manifest: manifest("model", "haiku") },
];

const CHECKED_AT = new Date(Date.UTC(2026, 10, 24, 3, 4, 5));

const CONNECTION_SLOTS: Readonly<Record<string, ReactNode>> = {
  docs: <ConnectionLine result={{ state: "reached" }} />,
  search: (
    <ConnectionLine
      result={{
        state: "unreached",
        reason: "연결을 거부했다: https://search.example.com/mcp (HTTP 401 Unauthorized)",
      }}
    />
  ),
  billing: <ConnectionLine result={undefined} />,
  wiki: <ConnectionLine result={{ state: "failed", message: "서버에 닿지 못했다" }} />,
  files: <LaunchedConnection enabled pending={false} latest={undefined} onRun={fn()} />,
  shell: (
    <LaunchedConnection
      enabled
      pending={false}
      latest={{ result: { state: "reached" }, at: CHECKED_AT }}
      onRun={fn()}
    />
  ),
  archive: <LaunchedConnection enabled={false} pending={false} latest={undefined} onRun={fn()} />,
  sonnet: <ConnectionLine result={{ state: "reached" }} />,
};

/**
 * 접속 확인이 있는 행. 켜 둔 원격 MCP 서버와 모델은 상태가 줄 아래에 서고, 켜 둔 stdio 서버는 버튼이 서며, 꺼 둔 행은
 * 결과가 없다. 표지 행에는 두지 않는다. 행마다 읽는 일은 페이지 시험이 본다.
 */
export const Connections: Story = {
  args: {
    data: CONNECTION_ROWS,
    connection: (row) => CONNECTION_SLOTS[row.name] ?? null,
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    // 읽기 골격의 상태 영역(행 밖)은 세지 않는다.
    const inRows = canvas.getAllByRole("status").filter((status) => status.closest("li") !== null);
    await expect(inRows).toHaveLength(6);
    await expect(canvas.getAllByRole("button", { name: "접속 확인" })).toHaveLength(3);
    // 표지 행은 경고 한 줄뿐이다.
    const broken = canvas.getByText("broken").closest("li");
    await expect(broken).not.toBeNull();
    if (broken !== null) {
      await expect(within(broken).queryByRole("status")).toBeNull();
      await expect(within(broken).queryByRole("button", { name: "접속 확인" })).toBeNull();
    }
    await expect(document.documentElement.scrollWidth).toBeLessThanOrEqual(
      document.documentElement.clientWidth,
    );
  },
};

/** 등록된 것이 하나도 없다. 종류마다 개수 0 과 빈 줄이다. */
export const Empty: Story = {
  args: { data: [] },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("heading", { level: 1 })).toHaveTextContent("플러그인 0");
    await expect(canvas.getAllByText("등록된 것이 없다")).toHaveLength(4);
    await expect(canvas.queryByRole("switch")).toBeNull();
  },
};

/** 켜고 끄지 못했다. 화면 머리 아래에 실패한 플러그인을 제목으로 든 위험 알림이 서고 목록은 그대로다. */
export const SwitchFailed: Story = {
  args: {
    switchFailure: {
      title: "켜고 끄지 못했다: agent/support-bot",
      message: "운영자 파일이 깨졌다: plugins/disabled.toml",
      requestId: "4f1c9a2e7b3d4c5e8a6f0b1d2c3e4f5a",
    },
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    const alert = canvas.getByRole("alert");
    await expect(alert).toHaveTextContent("켜고 끄지 못했다: agent/support-bot");
    await expect(alert).toHaveTextContent("스위치는 다시 읽은 값이다.");
    await expect(alert).toHaveTextContent("추적 식별자: 4f1c9a2e7b3d4c5e8a6f0b1d2c3e4f5a");
    // 알림은 화면 머리와 종류 묶음 사이에 선다.
    const header = canvas.getByRole("heading", { level: 1 });
    const firstKind = canvas.getByRole("heading", { level: 2, name: "에이전트 2" });
    await expect(alert.getBoundingClientRect().top).toBeGreaterThan(
      header.getBoundingClientRect().bottom,
    );
    await expect(alert.getBoundingClientRect().bottom).toBeLessThan(
      firstKind.getBoundingClientRect().top,
    );
  },
};
