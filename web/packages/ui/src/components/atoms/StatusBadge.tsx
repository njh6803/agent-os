// 상태 배지(디자인 파일 02.5). 실행의 상태 넷(일시정지, 끝남, 실패, 결말 없음)을 아이콘 모양과 용어집의 말로 함께 보인다.
// 색만으로 상태를 가르지 않는다. 글자는 컴포넌트가 스스로 쓰는 화면 문구이고 아이콘은 그 옆의 꾸밈이라 숨는다. 누르는
// 곳이 아니어서 상호작용 상태가 없다. 폭은 늘 내용의 폭이다(`w-fit`). 줄이 폭을 채우는 세로 묶음(카드 안 등)에 놓여도
// 늘어나지 않는다.
import type { NativeProps } from "../../props";
import { Icon, type IconName } from "./Icon";

export const STATUS_BADGE_STATUSES = ["paused", "done", "failed", "no-outcome"] as const;
export type StatusBadgeStatus = (typeof STATUS_BADGE_STATUSES)[number];

const BASE =
  "inline-flex h-6 w-fit shrink-0 items-center gap-1 whitespace-nowrap rounded-m px-2 text-caption";

// 용어집(CONTEXT.md 실행·인터럽트 절)의 말.
const TEXT = {
  paused: "일시정지",
  done: "끝남",
  failed: "실패",
  "no-outcome": "결말 없음",
} satisfies Record<StatusBadgeStatus, string>;

const ICON = {
  paused: "circle-pause",
  done: "circle-check",
  failed: "circle-x",
  "no-outcome": "circle-minus",
} satisfies Record<StatusBadgeStatus, IconName>;

const STATUS_CLASS = {
  paused: "bg-warning-tint text-warning",
  done: "bg-success-tint text-success",
  failed: "bg-danger-tint text-danger",
  "no-outcome": "bg-tint text-muted",
} satisfies Record<StatusBadgeStatus, string>;

interface StatusBadgeOwnProps {
  status: StatusBadgeStatus;
}

export type StatusBadgeProps = StatusBadgeOwnProps &
  NativeProps<"span", keyof StatusBadgeOwnProps | "children">;

export function StatusBadge({ status, ...rest }: StatusBadgeProps) {
  return (
    <span {...rest} className={`${BASE} ${STATUS_CLASS[status]}`}>
      <Icon name={ICON[status]} size="14" />
      {TEXT[status]}
    </span>
  );
}
