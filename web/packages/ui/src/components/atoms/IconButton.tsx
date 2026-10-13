// 아이콘 버튼(재탐색 디자인 파일 2.2). 글자 없이 아이콘 하나로 일을 일으키고 이름은 `label` 이 `aria-label` 과 `title`
// 로 붙는다. 변형 셋(주·보조·투명, 기본 투명), 크기 둘. `"m"` 은 밀도를 따르는 조작 높이의 정사각형(촘촘 32px, 보통
// 40px)이고 `"s"` 는 밀도와 상관없는 28px 이다(디자인 파일이 코드 칸 머리에 쓰는 작은 크기, 알림의 닫기). 아이콘은 크기와
// 상관없이 16px, 모서리 8px 이다. 색과 치수는 재탐색의 상태 표와 해부도다. 주는 버튼의 주와 같고, 보조는 디자인 파일이
// 상태를 적지 않아 버튼의 보조와 같게 둔다(design-refresh 명세). 상태마다 클래스를 고르는 까닭은 Button 과 같다.
// 불러오는 중은 아이콘 자리에 도는 표시를 두고 이름은 그대로다.
import type { MouseEvent } from "react";
import type { NativeProps } from "../../props";
import { Icon, Spinner, type IconName } from "./Icon";

export type IconButtonVariant = "primary" | "secondary" | "ghost";
export type IconButtonSize = "m" | "s";

const BASE =
  "inline-flex shrink-0 items-center justify-center rounded-m border focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring";

const SIZE_CLASS = { m: "size-control", s: "size-control-s" } satisfies Record<
  IconButtonSize,
  string
>;

const VARIANT_CLASS = {
  primary: "border-transparent bg-primary text-on-primary",
  secondary: "border-border bg-transparent text-text",
  ghost: "border-transparent bg-transparent text-text-muted",
} satisfies Record<IconButtonVariant, string>;

const LIVE_CLASS = {
  primary: "hover:bg-primary-hover active:bg-primary-active",
  secondary: "hover:bg-bg-hover active:bg-bg-active",
  ghost: "hover:bg-bg-hover hover:text-text active:bg-bg-active active:text-text",
} satisfies Record<IconButtonVariant, string>;

// 투명은 바탕 없이 아이콘의 색만 바꾼다(디자인 파일 상태 표).
const DISABLED_CLASS = {
  primary: "cursor-not-allowed border-bg-disabled bg-bg-disabled text-text-disabled",
  secondary: "cursor-not-allowed border-bg-disabled bg-bg-disabled text-text-disabled",
  ghost: "cursor-not-allowed border-transparent bg-transparent text-text-disabled",
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
      {loading ? <Spinner size="16" /> : <Icon name={icon} size="16" />}
    </button>
  );
}
