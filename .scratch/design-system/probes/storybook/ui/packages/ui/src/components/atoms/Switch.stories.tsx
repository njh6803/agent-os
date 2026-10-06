import type { Meta, StoryObj } from "@storybook/react-vite";
import { expect, fn } from "storybook/test";
import { Switch } from "./Switch";

const meta = {
  title: "atoms/Switch",
  component: Switch,
  args: { label: "알림 받기", onCheckedChange: fn() },
} satisfies Meta<typeof Switch>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Off: Story = {};

export const On: Story = { args: { defaultChecked: true } };

export const OnDark: Story = { args: { defaultChecked: true }, globals: { theme: "dark" } };

export const Disabled: Story = { args: { disabled: true } };

export const Toggle: Story = {
  play: async ({ args, canvas, userEvent }) => {
    const control = canvas.getByRole("switch", { name: "알림 받기" });
    await expect(control).not.toBeChecked();
    await userEvent.click(control);
    await expect(control).toBeChecked();
    await expect(args.onCheckedChange).toHaveBeenCalledWith(true);
  },
};
