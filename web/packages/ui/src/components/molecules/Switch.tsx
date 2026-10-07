// 스위치(디자인 파일 02.4). 누르는 즉시 적용되는 켜짐·꺼짐이다. `<label>` 전체가 누르는 곳이고(높이 `row-touch`
// 이상), 그 안에 라벨과 상태 글(켜짐·꺼짐), 트랙으로 그리는 `<input type="checkbox" role="switch">` 와 손잡이가 있다.
// 오류와 불러오는 중은 없다(바꾸지 못하면 쓰는 쪽이 되돌리고 알림으로 알린다).
//
// 올림·누름은 라벨 전체의 상태라 라벨의 `group` 을 보고 트랙을 칠한다. 상태마다 클래스를 고르고 쓸 수 없음에는 올림·
// 누름을 두지 않는다. 이름은 라벨 하나이고(`aria-labelledby`), 상태 글은 checked 와 같은 뜻이라 화면 읽기 프로그램에서
// 숨는다. `checked` 를 넘기지 않으면 스스로 상태를 든다. 나머지 속성은 입력 요소에 넘긴다(`props.ts`).
import { useId, useState } from "react";
import type { NativeProps } from "../../props";

interface SwitchOwnProps {
  /** 보이는 이름. */
  label: string;
  /** 넘기면 그 값을 그리고, 넘기지 않으면 꺼짐에서 시작해 스스로 바꾼다. */
  checked?: boolean;
  disabled?: boolean;
  onChange?: (checked: boolean) => void;
}

export type SwitchProps = SwitchOwnProps &
  NativeProps<
    "input",
    | keyof SwitchOwnProps
    | "children"
    | "type"
    | "role"
    | "defaultChecked"
    | "aria-checked"
    | "aria-labelledby"
  >;

type State = "off" | "on" | "disabled";

const ROW = "flex min-h-row-touch items-center justify-between gap-3";

const TRACK =
  "block h-switch-h w-switch-w appearance-none rounded-full border focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus";

const TRACK_CLASS = {
  off: "cursor-pointer border-border bg-raised group-hover:border-border-hover group-active:border-border-hover group-active:bg-tint",
  on: "cursor-pointer border-accent bg-accent group-hover:border-accent-hover group-hover:bg-accent-hover group-active:border-accent-press group-active:bg-accent-press",
  disabled: "cursor-not-allowed border-divider bg-disabled-surface",
} satisfies Record<State, string>;

const KNOB_COLOR = {
  off: "bg-muted",
  on: "bg-on-accent",
  disabled: "bg-disabled-text",
} satisfies Record<State, string>;

export function Switch({ label, checked, disabled = false, onChange, ...rest }: SwitchProps) {
  const [selfChecked, setSelfChecked] = useState(false);
  const on = checked ?? selfChecked;
  const labelId = useId();
  const state: State = disabled ? "disabled" : on ? "on" : "off";
  return (
    <label
      className={`${ROW} ${disabled ? "cursor-not-allowed text-disabled-text" : "group cursor-pointer text-text"}`}
    >
      <span className="flex min-w-0 flex-col">
        <span id={labelId} className="text-body">
          {label}
        </span>
        <span
          aria-hidden
          className={`text-small font-regular ${disabled ? "text-disabled-text" : "text-muted"}`}
        >
          {on ? "켜짐" : "꺼짐"}
        </span>
      </span>
      <span className="relative block shrink-0">
        <input
          {...rest}
          type="checkbox"
          role="switch"
          checked={on}
          disabled={disabled}
          aria-labelledby={labelId}
          onChange={(event) => {
            setSelfChecked(event.currentTarget.checked);
            onChange?.(event.currentTarget.checked);
          }}
          className={`${TRACK} ${TRACK_CLASS[state]}`}
        />
        <span
          className={`pointer-events-none absolute top-1 size-3 rounded-full ${on ? "right-1" : "left-1"} ${KNOB_COLOR[state]}`}
        />
      </span>
    </label>
  );
}
