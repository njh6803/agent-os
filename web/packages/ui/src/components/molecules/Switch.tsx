// 스위치(재탐색 디자인 파일 2.4). 누르는 즉시 적용되는 켜짐·꺼짐이다. `<label>` 전체가 누르는 곳이고(높이 `row-touch`
// 이상), 그 안에 라벨과 상태 글(켜짐·꺼짐), 트랙으로 그리는 `<input type="checkbox" role="switch">` 와 손잡이가 있다.
// 오류와 불러오는 중은 없다(바꾸지 못하면 쓰는 쪽이 되돌리고 알림으로 알린다). 색은 재탐색의 상태 표이고 치수는 아직
// 첫 탐색 디자인 파일의 값이다(design-refresh 티켓 04 가 옮긴다).
//
// 올림은 라벨 전체의 상태라 라벨의 group 을 보고, 트랙 위에 반투명 `bg-active` 를 겹친다. 트랙(입력 요소)의 바탕은 한
// 색이라 겹칠 면을 트랙과 손잡이 사이에 따로 둔다. 누름은 디자인 파일의 상태 표가 두지 않았다. 상태마다 클래스를 고르고
// 쓸 수 없음에는 올림을 두지 않는다. 이름은 라벨 하나이고(`aria-labelledby`), 상태 글은 checked 와 같은 뜻이라 화면 읽기
// 프로그램에서 숨는다. `checked` 를 넘기지 않으면 스스로 상태를 든다. 나머지 속성은 입력 요소에 넘긴다(`props.ts`).
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
  "block h-switch-h w-switch-w appearance-none rounded-full focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring";

const TRACK_CLASS = {
  off: "cursor-pointer bg-border-control",
  on: "cursor-pointer bg-accent",
  disabled: "cursor-not-allowed bg-bg-disabled",
} satisfies Record<State, string>;

// 트랙 위에 겹칠 면. 올림은 라벨의 이름 있는 group(`group/switch`)을 본다. 이름이 없으면 바깥 조상의 `.group`(목록 행의
// 올림 등)에도 걸린다. 쓸 수 없음에는 올림의 클래스를 두지 않는다.
const OVERLAY_CLASS = {
  off: "group-hover/switch:bg-bg-active",
  on: "group-hover/switch:bg-bg-active",
  disabled: "",
} satisfies Record<State, string>;

const KNOB_COLOR = {
  off: "bg-bg-raised",
  on: "bg-on-accent",
  disabled: "bg-text-disabled",
} satisfies Record<State, string>;

export function Switch({ label, checked, disabled = false, onChange, ...rest }: SwitchProps) {
  const [selfChecked, setSelfChecked] = useState(false);
  const on = checked ?? selfChecked;
  const labelId = useId();
  const state: State = disabled ? "disabled" : on ? "on" : "off";
  return (
    <label
      className={`${ROW} ${disabled ? "cursor-not-allowed text-text-disabled" : "group/switch cursor-pointer text-text"}`}
    >
      <span className="flex min-w-0 flex-col">
        <span id={labelId} className="text-body">
          {label}
        </span>
        <span
          aria-hidden
          className={`text-small font-regular ${disabled ? "text-text-disabled" : "text-text-muted"}`}
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
          className={`pointer-events-none absolute inset-0 rounded-full ${OVERLAY_CLASS[state]}`}
        />
        <span
          className={`pointer-events-none absolute top-1 size-3 rounded-full ${on ? "right-1" : "left-1"} ${KNOB_COLOR[state]}`}
        />
      </span>
    </label>
  );
}
