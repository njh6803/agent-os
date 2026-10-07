// 진행 표시(디자인 파일 02.7). 실행이 단계를 밟는 동안 몇째인지 보인다. 보이는 이름 아래 6px 트랙(`tint`)에 막대
// (`accent`, 실패하면 `danger`)를 그린다. 값을 모르면 `aria-valuenow` 를 두지 않고 막대가 자리를 옮겨 다니며, 움직임
// 줄이기 설정이면 멈춘다.
//
// `<progress>` 가 아니라 `<div role="progressbar">` 다(공통의 "브라우저 기본 요소" 문장의 예외. design-system 명세의
// 컴포넌트 공통 절 주석). 이름은 보이는 글자와 같은 `aria-label` 이다. WAI-ARIA 가 progressbar 의 자식을 꾸밈(children
// presentational)으로 정해 이름을 두 번 읽지 않는다고 본다(정의에서 나온 어림. 화면 읽기 프로그램으로 듣지 않았다).
// 최소값은 0 으로 두고(`aria-valuemin` 을 받지 않는다. progressbar 의 기본이 0 이다) 막대는 자른 값을 `max` 로 나눈
// 비율이다(아래 `clamp`).
import type { NativeProps } from "../../props";

export type ProgressTone = "accent" | "danger";

const BAR_CLASS = { accent: "bg-accent", danger: "bg-danger" } satisfies Record<
  ProgressTone,
  string
>;

// 값을 모르는 막대는 트랙의 30% 이고 `progress` 움직임이 left 를 옮긴다. 움직임이 멈추면(줄이기, 사진) 디자인 파일의
// 정지 그림처럼 가운데(35%)에 선다. 왼쪽에 서면 값이 30% 인 막대와 구분되지 않는다.
const INDETERMINATE_CLASS = "left-7/20 w-3/10 animate-progress motion-reduce:animate-none";

interface ProgressOwnProps {
  /** null 이면 값 모름(불러오는 중). 기본 null. */
  value?: number | null;
  /** 끝 값. 기본 1. */
  max?: number;
  /** 보이는 이름이자 접근 이름. 몇 단계 중 몇째인지 글로 적는다. */
  label: string;
  tone?: ProgressTone;
}

export type ProgressProps = ProgressOwnProps &
  NativeProps<
    "div",
    | keyof ProgressOwnProps
    | "children"
    | "role"
    | "aria-label"
    | "aria-labelledby"
    | "aria-valuenow"
    | "aria-valuemin"
    | "aria-valuemax"
  >;

/**
 * 값을 0 과 끝 값 사이로 자른다. 끝 값이 0 이하이면 0 이다. `aria-valuenow` 는 최소·최대 밖에 두지 않고(WAI-ARIA),
 * 막대의 폭도 이 값에서 나와 둘이 어긋나지 않는다.
 */
function clamp(value: number, max: number): number {
  return Math.min(Math.max(value, 0), Math.max(max, 0));
}

export function Progress({
  value = null,
  max = 1,
  label,
  tone = "accent",
  ...rest
}: ProgressProps) {
  const now = value === null ? null : clamp(value, max);
  const bar =
    now === null ? (
      <div
        className={`absolute inset-y-0 rounded-full ${BAR_CLASS[tone]} ${INDETERMINATE_CLASS}`}
      />
    ) : (
      <div
        className={`absolute inset-y-0 left-0 rounded-full ${BAR_CLASS[tone]}`}
        style={{ width: `${String(max > 0 ? (now / max) * 100 : 0)}%` }}
      />
    );
  return (
    <div
      {...rest}
      role="progressbar"
      aria-label={label}
      aria-valuenow={now ?? undefined}
      aria-valuemax={max}
      className="flex flex-col gap-2"
    >
      <span className="text-small text-text">{label}</span>
      <div className="relative h-progress overflow-hidden rounded-full bg-tint">{bar}</div>
    </div>
  );
}
