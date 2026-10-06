import type { ButtonHTMLAttributes } from "react";

export const BUTTON_VARIANTS = ["primary", "secondary", "danger"] as const;
export type ButtonVariant = (typeof BUTTON_VARIANTS)[number];

const BASE =
  "inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:opacity-50";

const VARIANT_CLASS: Record<ButtonVariant, string> = {
  primary: "bg-accent text-on-accent shadow-sm",
  secondary: "border border-border bg-surface text-text",
  danger: "bg-danger text-on-danger",
};

export interface ButtonProps extends Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "className" | "style"
> {
  variant?: ButtonVariant;
}

export function Button({ variant = "primary", type = "button", ...rest }: ButtonProps) {
  return <button type={type} className={`${BASE} ${VARIANT_CLASS[variant]}`} {...rest} />;
}
