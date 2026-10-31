// 플러그인 하나(admin-style 티켓 05, 그림 mk-plugin, mk-plugin-m). 켜짐과 꺼짐이다. 표본 값은 그림의 것이고, 켜짐은
// 그림처럼 다시 확인하는 중이다. 틀 없이 그리고, 미리보기의 데코레이터가 본문 칸과 같은 컨테이너를 두른다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn, within } from "storybook/test";
import type { Plugin } from "../../api/plugins";
import { PluginDetail } from "./PluginDetail";

const CALC: Plugin = {
  kind: "agent",
  name: "calc",
  enabled: true,
  manifest: {
    schema_version: "1",
    kind: "agent",
    name: "calc",
    version: "0.1.0",
    entrypoint: "agent:Calc",
    mcp: ["everything"],
    requires_approval: [],
    conversation_limit: null,
    model: null,
    provider: null,
    model_id: null,
    max_tokens: null,
    temperature: null,
    server: null,
  },
};

const EVERYTHING: Plugin = {
  kind: "mcp",
  name: "everything",
  enabled: false,
  manifest: {
    schema_version: "1",
    kind: "mcp",
    name: "everything",
    version: "0.1.0",
    entrypoint: null,
    mcp: [],
    requires_approval: [],
    conversation_limit: null,
    model: null,
    provider: null,
    model_id: null,
    max_tokens: null,
    temperature: null,
    server: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-everything"],
      secret_args: {},
    },
  },
};

const meta = {
  title: "organisms/PluginDetail",
  component: PluginDetail,
  args: {
    kind: "agent",
    name: "calc",
    data: CALC,
    error: undefined,
    isValidating: false,
    onRefresh: fn(),
  },
} satisfies Meta<typeof PluginDetail>;

export default meta;
type Story = StoryObj<typeof meta>;

/** 켜진 플러그인을 다시 확인하는 중. 제목 옆에 켜짐이 서고 매니페스트는 두 칸 들여 쓴 JSON 이다. */
export const Enabled: Story = {
  args: { isValidating: true },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByRole("link", { name: "플러그인 목록" })).toHaveAttribute("href", "/");
    await expect(canvas.getByRole("heading", { level: 1, name: "calc" })).toBeVisible();
    await expect(canvas.getByText("켜짐")).toBeVisible();
    await expect(canvas.getByText("에이전트. 켜고 끄기는 플러그인 목록에서 한다.")).toBeVisible();
    await expect(canvas.getByRole("progressbar", { name: "다시 확인하는 중" })).toBeVisible();
    const manifest = canvas.getByRole("region", { name: "매니페스트" });
    await expect(manifest).toHaveTextContent('"entrypoint": "agent:Calc"');
    // 켜짐은 제목과 같은 줄에 선다.
    const heading = canvas.getByRole("heading", { level: 1 }).getBoundingClientRect();
    const mark = canvas.getByText("켜짐").getBoundingClientRect();
    await expect(mark.left).toBeGreaterThanOrEqual(heading.right);
    await expect(mark.top).toBeLessThan(heading.bottom);
  },
};

/** 꺼진 MCP 서버. 제목 옆에 꺼짐이 선다. */
export const Disabled: Story = {
  args: { kind: "mcp", name: "everything", data: EVERYTHING },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(canvas.getByText("꺼짐")).toBeVisible();
    await expect(canvas.queryByText("켜짐")).toBeNull();
    await expect(canvas.getByText("MCP. 켜고 끄기는 플러그인 목록에서 한다.")).toBeVisible();
  },
};
