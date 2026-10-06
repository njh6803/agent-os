import type { ButtonHTMLAttributes } from "react";

// 디자인 파일 v3 의 버튼(02.1)을 쓰임새 토큰 클래스만으로 옮긴 표본. 변형 셋, 크기 둘.
export const BUTTON_VARIANTS = ["primary", "secondary", "danger"] as const;
export type ButtonVariant = (typeof BUTTON_VARIANTS)[number];
export const BUTTON_SIZES = ["m", "s"] as const;
export type ButtonSize = (typeof BUTTON_SIZES)[number];

const BASE =
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-m border font-strong focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus disabled:cursor-not-allowed disabled:border-transparent disabled:bg-disabled-surface disabled:text-disabled-text";

const SIZE_CLASS = {
  m: "h-control-m px-4 text-body",
  s: "h-control-s px-3 text-small",
} satisfies Record<ButtonSize, string>;

const VARIANT_CLASS = {
  primary: "border-transparent bg-accent text-on-accent hover:bg-accent-hover active:bg-accent-press",
  secondary: "border-transparent bg-tint text-text hover:bg-tint-hover active:bg-tint-press",
  danger: "border-danger bg-raised text-danger hover:bg-danger-tint active:bg-danger-tint-press",
} satisfies Record<ButtonVariant, string>;

export interface ButtonProps extends Omit<
  ButtonHTMLAttributes<HTMLButtonElement>,
  "className" | "style"
> {
  variant?: ButtonVariant;
  size?: ButtonSize;
}

export function Button({ variant = "primary", size = "m", type = "button", ...rest }: ButtonProps) {
  return (
    <button
      type={type}
      className={`${BASE} ${SIZE_CLASS[size]} ${VARIANT_CLASS[variant]}`}
      {...rest}
    />
  );
}
