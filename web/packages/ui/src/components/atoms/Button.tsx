// 버튼(재탐색 디자인 파일 2.1). 변형 셋(주·보조·위험)이고 크기는 고르지 않는다(높이 40px). 색은 재탐색의 상태 표이고,
// 치수는 아직 첫 탐색 디자인 파일의 값이다(design-refresh 티켓 04 가 옮긴다). 주는 `primary` 묶음으로 칠하고, 보조와
// 위험은 바탕 없이 `border` 테두리로 서서 올림·누름에 반투명 바탕을 겹친다. 위험의 누름은 디자인 파일의 `bg-active` 가
// 아니라 `bg-selected` 다. `bg-active` 위의 `danger` 글자가 다크에서 4.5:1 에 못 미쳤다(design-refresh 명세의 "위험
// 버튼의 누름", 사용자가 골랐다). 클래스는 쓰임새 토큰과 공통 크기의 유틸리티만 쓴다.
// 상태마다 클래스를 고른다. 쓸 수 없음과 불러오는 중에는 올림·누름의 클래스를 두지 않는다. 불러오는 중은 `disabled`
// 가 아니어서 `disabled:` 변형으로는 그 상태의 올림·누름을 끌 수 없다.
//
// 불러오는 중은 `disabled` 가 아니다. `aria-disabled`·`aria-busy` 를 달고 누름(제출 포함)을 무시하며, 색은 기본
// 그대로이고 포커스가 남는다. 너비를 지키려고 글자 자리를 그대로 두고 보이지 않게 한 뒤 도는 표시를 가운데에 그린다
// (디자인 파일은 도는 표시를 글자 앞에 그렸는데, 아이콘이 없는 버튼은 그만큼 넓어진다).
import type { MouseEvent } from "react";
import type { NativeProps } from "../../props";
import { Icon, Spinner, type IconName } from "./Icon";

export type ButtonVariant = "primary" | "secondary" | "danger";

const BASE =
  "relative inline-flex h-control-m items-center justify-center whitespace-nowrap rounded-m border px-4 text-body font-semibold focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring";

const VARIANT_CLASS = {
  primary: "border-transparent bg-primary text-on-primary",
  secondary: "border-border bg-transparent text-text",
  danger: "border-border bg-transparent text-danger",
} satisfies Record<ButtonVariant, string>;

const LIVE_CLASS = {
  primary: "hover:bg-primary-hover active:bg-primary-active",
  secondary: "hover:bg-bg-hover active:bg-bg-active",
  danger: "hover:bg-bg-hover active:bg-bg-selected",
} satisfies Record<ButtonVariant, string>;

const DISABLED_CLASS = "cursor-not-allowed border-bg-disabled bg-bg-disabled text-text-disabled";

interface ButtonOwnProps {
  /** 글자. 동사로 짧게. */
  children: string;
  variant?: ButtonVariant;
  /** 글자 앞 아이콘. */
  icon?: IconName;
  loading?: boolean;
  disabled?: boolean;
  type?: "button" | "submit";
  onClick?: () => void;
}

export type ButtonProps = ButtonOwnProps &
  NativeProps<"button", keyof ButtonOwnProps | "aria-busy" | "aria-disabled">;

export function Button({
  children,
  variant = "primary",
  icon,
  loading = false,
  disabled = false,
  type = "button",
  onClick,
  ...rest
}: ButtonProps) {
  const state = disabled
    ? DISABLED_CLASS
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
      type={type}
      disabled={disabled}
      aria-busy={loading || undefined}
      aria-disabled={loading || undefined}
      onClick={press}
      className={`${BASE} ${state}`}
    >
      <span className={`inline-flex items-center gap-2${loading ? " opacity-0" : ""}`}>
        {icon === undefined ? null : <Icon name={icon} />}
        {children}
      </span>
      {loading ? (
        <span className="absolute inset-0 flex items-center justify-center">
          <Spinner size="20" />
        </span>
      ) : null}
    </button>
  );
}
