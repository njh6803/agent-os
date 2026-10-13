// 진행 표시(재탐색 디자인 파일 2.7). 실행이 단계를 밟는 동안 몇째인지 보인다. 값을 알면 보이는 이름 아래 8px 사이를
// 두고 높이 4px 의 둥근 트랙(`bg-active`)에 막대(`text-muted`)를 그린다. 값을 모르면 `aria-valuenow` 를 두지 않고, 끝을
// 모르는 막대를 채우는 대신 트랙 없이 16px 의 도는 표시와 이름을 사이 8px 로 한 줄에 놓는다. 이름과 도는 표시는 둘 다
// `text-muted` 다. 도는 표시는 한 바퀴 0.8초이고 움직임 줄이기 설정이면 멈춘다. 그 한 줄은 이름 한 줄의 높이라 막대가
// 있는 모양보다 낮다. 값을 알게 되면 이름 아래 사이와 트랙만큼(12px) 자라고, 그 자리를 미리 비워 두지 않는다(디자인
// 파일이 막대와 회전을 다른 모양으로 그린다). 치수는 밀도와 상관없다.
//
// `<progress>` 가 아니라 `<div role="progressbar">` 다(공통의 "브라우저 기본 요소" 문장의 예외. design-system 명세의
// 컴포넌트 공통 절 주석). 이름은 보이는 글자와 같은 `aria-label` 이다. WAI-ARIA 가 progressbar 의 자식을 꾸밈(children
// presentational)으로 정해 이름을 두 번 읽지 않는다고 본다(정의에서 나온 어림. 화면 읽기 프로그램으로 듣지 않았다).
// 최소값은 0 으로 두고(`aria-valuemin` 을 받지 않는다. progressbar 의 기본이 0 이다) 막대는 자른 값을 `max` 로 나눈
// 비율이다(아래 `clamp`).
import type { NativeProps } from "../../props";
import { Spinner } from "./Icon";

interface ProgressOwnProps {
  /** null 이면 값 모름(불러오는 중). 기본 null. */
  value?: number | null;
  /**
   * 끝 값. 기본 1. 0 보다 크게 넘긴다. 0 이하이면 막대는 비고 범위는 0 부터 0 까지다(`aria-valuemax` 가 최소 0 보다 작게
   * 나가지 않는다).
   */
  max?: number;
  /** 보이는 이름이자 접근 이름. 몇 단계 중 몇째인지 글로 적는다. */
  label: string;
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

export function Progress({ value = null, max = 1, label, ...rest }: ProgressProps) {
  const now = value === null ? null : clamp(value, max);
  const name = <span className="text-small text-text-muted">{label}</span>;
  return (
    <div
      {...rest}
      role="progressbar"
      aria-label={label}
      aria-valuenow={now ?? undefined}
      aria-valuemax={Math.max(max, 0)}
      className={now === null ? "flex items-center gap-2 text-text-muted" : "flex flex-col gap-2"}
    >
      {now === null ? (
        <>
          <Spinner size="16" />
          {name}
        </>
      ) : (
        <>
          {name}
          <div className="relative h-progress overflow-hidden rounded-full bg-bg-active">
            <div
              className="absolute inset-y-0 left-0 rounded-full bg-text-muted"
              style={{ width: `${String(max > 0 ? (now / max) * 100 : 0)}%` }}
            />
          </div>
        </>
      )}
    </div>
  );
}
