// 코드 칸(admin-style 티켓 04, 명세 "앱 부품"). 매니페스트처럼 긴 경로와 식별자가 든 JSON 을 두 칸 들여 그린다. 폭 320px
// 에서도 가로로 밀지 않는 것은 미리보기의 afterEach 가 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, within } from "storybook/test";
import { CodeBlock, formatJson } from "./CodeBlock";

const MANIFEST = {
  schema_version: "1",
  kind: "agent",
  name: "calc",
  version: "0.1.0",
  entrypoint: "agent:Calc",
  description: "C:/root/plugins/agents/calc/a-very-long-directory-name-without-any-spaces/agent.py",
};

const meta = {
  title: "atoms/CodeBlock",
  component: CodeBlock,
  args: { children: formatJson(MANIFEST) },
} satisfies Meta<typeof CodeBlock>;

export default meta;
type Story = StoryObj<typeof meta>;

/** JSON 은 두 칸 들여 쓰고 긴 낱말은 줄을 바꿔 흐른다. */
export const Json: Story = {
  play: async ({ canvasElement }) => {
    const block = within(canvasElement).getByText(/"entrypoint": "agent:Calc"/);
    await expect(block.tagName).toBe("PRE");
    await expect(block.textContent).toContain('\n  "kind": "agent",\n');
    await expect(block.scrollWidth).toBeLessThanOrEqual(block.clientWidth);
  },
};
