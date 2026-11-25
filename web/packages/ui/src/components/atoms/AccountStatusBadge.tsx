// 계정 상태 배지(admin-login 명세 "디자인 시스템에 더하는 것"). 운영자 계정의 상태 넷(활성, 비활성, 비밀번호 미설정,
// 잠김)을 글자와 아이콘으로 함께 보인다. 색만으로 상태를 가르지 않는다. 실행의 상태 배지(`StatusBadge`)는 실행 상태 넷에만
// 쓰므로 고치지 않고, 같은 모양(바탕을 칠하지 않고 `border` 테두리 안에 글자와 아이콘, 치수도 같다)의 컴포넌트를 따로 둔다.
// 앞의 셋은 상태 점(`circle`)이고 잠김만 자물쇠(`lock`)다. 글자는 컴포넌트가 스스로 쓰는 화면 문구이고 아이콘은 그 옆의
// 꾸밈이라 숨는다. 누르는 곳이 아니어서 상호작용 상태가 없다. 폭은 늘 내용의 폭이다(`w-fit`).
import type { NativeProps } from "../../props";
import { Icon, type IconName } from "./Icon";

export const ACCOUNT_STATUS_BADGE_STATUSES = [
  "active",
  "inactive",
  "password-unset",
  "locked",
] as const;
export type AccountStatusBadgeStatus = (typeof ACCOUNT_STATUS_BADGE_STATUSES)[number];

const BASE =
  "inline-flex h-badge w-fit shrink-0 items-center gap-1 whitespace-nowrap rounded-s border border-border bg-transparent pr-2 pl-badge-start text-badge";

// admin-login 명세 "배지의 이름"의 말이다. 계정의 "비활성"은 꺼진 플러그인을 말하지 않는다(CONTEXT.md 운영자 계정 절이
// 그 풀이를 든다).
const TEXT = {
  active: "활성",
  inactive: "비활성",
  "password-unset": "비밀번호 미설정",
  locked: "잠김",
} satisfies Record<AccountStatusBadgeStatus, string>;

const ICON = {
  active: "circle",
  inactive: "circle",
  "password-unset": "circle",
  locked: "lock",
} satisfies Record<AccountStatusBadgeStatus, IconName>;

// 활성은 놓인 곳의 글자색이고(그린 화면대로) 잠김만 `warning` 이다. 비활성과 비밀번호 미설정은 같은 흐린 색이지만 문구가
// 다르다.
const STATUS_CLASS = {
  active: "text-text",
  inactive: "text-text-muted",
  "password-unset": "text-text-muted",
  locked: "text-warning",
} satisfies Record<AccountStatusBadgeStatus, string>;

interface AccountStatusBadgeOwnProps {
  status: AccountStatusBadgeStatus;
}

export type AccountStatusBadgeProps = AccountStatusBadgeOwnProps &
  NativeProps<"span", keyof AccountStatusBadgeOwnProps | "children">;

export function AccountStatusBadge({ status, ...rest }: AccountStatusBadgeProps) {
  return (
    <span {...rest} className={`${BASE} ${STATUS_CLASS[status]}`}>
      <Icon name={ICON[status]} size="14" />
      {TEXT[status]}
    </span>
  );
}
