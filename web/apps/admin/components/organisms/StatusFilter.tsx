// 실행 상태의 이름과 배지, 그 상태로 거르는 알약 라디오(admin-style 명세 "실행 목록", admin-login 명세 "대화 목록"). 실행
// 목록과 대화 목록이 함께 쓴다. 대화의 상태는 끝 실행의 실행 상태라 같은 넷이다.

import type { StatusBadgeStatus } from "@agent-os/ui";
import { useId } from "react";
import type { RunStatus } from "../../api/traces";

/**
 * 실행 상태의 이름과 거르기의 차례. 이름은 용어집의 말이다. 결말 없음은 "지금 돌고 있다"가 아니라 끝내지 못하고 사라진
 * 실행과 구분되지 않는다는 뜻이라 "실행 중"으로 부르지 않는다(스토리 26, ADR 0021). `Record` 라서 계약에 상태가 늘거나
 * 줄면 여기가 컴파일에서 깨진다.
 */
export const STATUS_NAMES = {
  paused: "일시정지",
  finished: "끝남",
  failed: "실패",
  unfinished: "결말 없음",
} as const satisfies Record<RunStatus, string>;

/** 실행 상태가 잇는 배지의 상태(admin-style 명세 "실행 목록"). 배지의 글자는 배지가 쓰는 용어집의 말이다. */
export const BADGE = {
  paused: "paused",
  finished: "done",
  failed: "failed",
  unfinished: "no-outcome",
} as const satisfies Record<RunStatus, StatusBadgeStatus>;

/** 거르기의 값. null 은 전부다. */
export type StatusFilterValue = RunStatus | null;

/** 전부와 상태 넷. 상태는 STATUS_NAMES 에 적은 차례다. */
const FILTERS: readonly (readonly [StatusFilterValue, string])[] = [
  [null, "전부"],
  ...Object.keys(STATUS_NAMES)
    .filter(isRunStatus)
    .map((status) => [status, STATUS_NAMES[status]] as const),
];

function isRunStatus(value: string): value is RunStatus {
  return Object.hasOwn(STATUS_NAMES, value);
}

interface StatusFilterProps {
  readonly value: StatusFilterValue;
  readonly onChange: (value: StatusFilterValue) => void;
}

/**
 * 상태 거르기. 라디오 다섯을 알약 모양의 라벨로 감싼다(그림 mk-runs). 넓은 갈래에서는 이름 "상태"가 알약과 한 줄에
 * 서고, 좁은 갈래에서는 그 위에 선다. 떠 있는 `legend` 는 fieldset 의 테두리 자리를 떠나 줄의 첫 항목이 된다.
 */
export function StatusFilter({ value, onChange }: StatusFilterProps) {
  const name = useId();
  return (
    <fieldset className="flex flex-wrap items-center gap-2">
      <legend className="mb-2 text-small text-text-muted @split:float-left @split:mr-2 @split:mb-0">
        상태
      </legend>
      {FILTERS.map(([filter, label]) => {
        const checked = value === filter;
        return (
          <label
            key={label}
            className={`flex h-control items-center gap-2 rounded-full border px-3 text-body ${checked ? "border-text bg-bg-selected font-medium" : "border-border-control"}`}
          >
            <input
              type="radio"
              name={name}
              checked={checked}
              className="focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
              onChange={() => {
                onChange(filter);
              }}
            />
            {label}
          </label>
        );
      })}
    </fieldset>
  );
}
