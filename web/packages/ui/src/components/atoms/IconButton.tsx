// 아이콘 버튼(디자인 파일 02.2). 글자 없이 아이콘 하나로 일을 일으키고 이름은 `label` 이 `aria-label` 과 `title` 로
// 붙는다. 변형 셋(주·보조·투명, 기본 투명), 크기 둘(40·32px 정사각형). 상태마다 클래스를 고르는 까닭은 Button 과 같다.
// 불러오는 중은 아이콘 자리에 도는 표시를 두고 이름은 그대로다.
import type { MouseEvent } from "react";
import type { NativeProps } from "../../props";
import { Icon, Spinner, type IconName, type IconSize } from "./Icon";

export type IconButtonVariant = "primary" | "secondary" | "ghost";
export type IconButtonSize = "m" | "s";

const BASE =
  "inline-flex shrink-0 items-center justify-center rounded-m focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus";

const SIZE_CLASS = { m: "size-control-m", s: "size-control-s" } satisfies Record<
  IconButtonSize,
  string
>;

const ICON_SIZE = { m: "20", s: "16" } satisfies Record<IconButtonSize, IconSize>;

const VARIANT_CLASS = {
  primary: "bg-accent text-on-accent",
  secondary: "bg-tint text-text",
  ghost: "bg-transparent text-muted",
} satisfies Record<IconButtonVariant, string>;

const LIVE_CLASS = {
  primary: "hover:bg-accent-hover active:bg-accent-press",
  secondary: "hover:bg-tint-hover active:bg-tint-press",
  ghost: "hover:bg-tint hover:text-text active:bg-tint-hover active:text-text",
} satisfies Record<IconButtonVariant, string>;

// 투명은 바탕 없이 글자색만 바꾼다(디자인 파일 상태 표).
const DISABLED_CLASS = {
  primary: "cursor-not-allowed bg-disabled-surface text-disabled-text",
  secondary: "cursor-not-allowed bg-disabled-surface text-disabled-text",
  ghost: "cursor-not-allowed bg-transparent text-disabled-text",
} satisfies Record<IconButtonVariant, string>;

interface IconButtonOwnProps {
  icon: IconName;
  /** 이름. `aria-label` 과 `title` 이 된다. */
  label: string;
  variant?: IconButtonVariant;
  size?: IconButtonSize;
  loading?: boolean;
  disabled?: boolean;
  onClick?: () => void;
}

export type IconButtonProps = IconButtonOwnProps &
  NativeProps<
    "button",
    | keyof IconButtonOwnProps
    | "children"
    | "type"
    | "title"
    | "aria-label"
    | "aria-busy"
    | "aria-disabled"
  >;

export function IconButton({
  icon,
  label,
  variant = "ghost",
  size = "m",
  loading = false,
  disabled = false,
  onClick,
  ...rest
}: IconButtonProps) {
  const state = disabled
    ? DISABLED_CLASS[variant]
    : `${VARIANT_CLASS[variant]}${loading ? "" : ` ${LIVE_CLASS[variant]}`}`;
  const press = (event: MouseEvent<HTMLButtonElement>): void => {
    if (loading) {
      event.preventDefault();
      return;
    }
    onClick?.();
  };
  return (
    <button
      {...rest}
      type="button"
      title={label}
      aria-label={label}
      disabled={disabled}
      aria-busy={loading || undefined}
      aria-disabled={loading || undefined}
      onClick={press}
      className={`${BASE} ${SIZE_CLASS[size]} ${state}`}
    >
      {loading ? <Spinner size={ICON_SIZE[size]} /> : <Icon name={icon} size={ICON_SIZE[size]} />}
    </button>
  );
}
