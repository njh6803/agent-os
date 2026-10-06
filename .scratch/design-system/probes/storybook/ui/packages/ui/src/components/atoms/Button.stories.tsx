import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn } from "storybook/test";
import { Button } from "./Button";

const meta = {
  title: "atoms/Button",
  component: Button,
  args: { children: "보내기", onClick: fn() },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = { args: { variant: "primary" } };

export const Secondary: Story = { args: { variant: "secondary" } };

export const Danger: Story = { args: { variant: "danger", children: "거부" } };

export const PrimaryDark: Story = { args: { variant: "primary" }, globals: { theme: "dark" } };

export const SecondaryDark: Story = { args: { variant: "secondary" }, globals: { theme: "dark" } };

export const Disabled: Story = { args: { variant: "primary", disabled: true } };

export const Click: Story = {
  args: { variant: "primary" },
  play: async ({ args, canvas, userEvent }) => {
    await userEvent.click(canvas.getByRole("button", { name: "보내기" }));
    await expect(args.onClick).toHaveBeenCalledOnce();
  },
};
