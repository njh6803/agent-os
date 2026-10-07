// 글 입력(디자인 파일 02.3). 라벨이 칸 위에 늘 보이고, 칸 아래 한 줄이 도움말이나 오류다. 변형 둘(한 줄, 여러 줄).
// 클래스는 쓰임새 토큰과 공통 크기의 유틸리티만 쓰고 상태마다 고른다. 쓸 수 없음과 오류에는 올림의 클래스를 두지 않는다.
// 누름과 불러오는 중은 디자인 파일의 상태 표가 두지 않았다.
//
// 라벨은 `<label for>` 로 칸에 잇는다. 도움말을 라벨 안에 두면 이름에 섞이고 `aria-describedby` 로 한 번 더 읽힌다.
// 오류가 있으면 그 글이 도움말의 자리를 차지한다(디자인 파일 02.3 의 오류 상태 그림). "선택"은 공백 하나 뒤의
// inline-block 이다. 접근 이름 계산은 inline 이 아닌 자식의 앞뒤에만 공백을 넣어, 그냥 붙이자 이름이 "플러그인
// 이름선택"이었다. 나머지 속성은 칸(`<input>`, `<textarea>`)에 넘긴다(`props.ts`). 그래서 props 는 변형마다 그 요소의
// 기본 속성을 받는 유니온이다.
import { useId, type ReactNode } from "react";
import type { NativeProps } from "../../props";
import { Icon } from "../atoms/Icon";

export type TextFieldVariant = "single" | "multi";

interface FieldOwnProps {
  /** 칸 위에 늘 보이는 이름. */
  label: string;
  /** 없으면 브라우저가 글을 든다. */
  value?: string;
  /** 예시만. 라벨을 대신하지 않는다. */
  placeholder?: string;
  help?: string | null;
  /** 있으면 오류 상태이고 이 글이 도움말의 자리에 보인다. */
  error?: string | null;
  /** 라벨 옆 "선택". */
  optional?: boolean;
  disabled?: boolean;
  onChange?: (value: string) => void;
}

interface SingleOwnProps extends FieldOwnProps {
  variant?: "single";
  /** 여러 줄에만 있다. 막지 않으면 `variant` 를 뺀 한 줄 칸에 넘긴 `rows` 가 `<input>` 에 샌다. */
  rows?: never;
}

interface MultiOwnProps extends FieldOwnProps {
  variant: "multi";
  /** 처음 줄 수. 기본 3. */
  rows?: number;
}

// 컴포넌트가 정하는 속성. 오류 상태와 도움말 잇기는 `error`·`help` 가 정한다.
type Decided = "children" | "aria-invalid" | "aria-describedby";

export type TextFieldProps =
  | (SingleOwnProps & NativeProps<"input", keyof SingleOwnProps | Decided | "type">)
  | (MultiOwnProps & NativeProps<"textarea", keyof MultiOwnProps | Decided>);

const CONTROL =
  "block w-full min-w-0 rounded-m border text-body focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus";

const SIZE_CLASS = {
  single: "h-control-m px-3",
  multi: "min-h-field-multi resize-y px-3 py-2",
} satisfies Record<TextFieldVariant, string>;

type State = "live" | "invalid" | "disabled";

// 쓸 수 없음은 자리 글자도 disabled-text 다. muted 로 두자 다크에서 넣은 글보다 밝아 쓸 수 있는 칸처럼 보였다.
const STATE_CLASS = {
  live: "border-border bg-raised text-text placeholder:text-muted hover:border-border-hover",
  invalid: "border-danger bg-raised text-text placeholder:text-muted",
  disabled:
    "cursor-not-allowed border-divider bg-disabled-surface text-disabled-text placeholder:text-disabled-text",
} satisfies Record<State, string>;

// 칸 아래 한 줄(도움말이나 오류)의 색. 오류 아이콘은 이 색을 그대로 받는다. 쓸 수 없어도 도움말은 muted 다. 디자인
// 파일은 disabled-text 로 그렸지만, 도움말은 쓸 수 없는 조작 요소도 그 라벨도 아니라 명암비의 예외가 아니다(axe 가
// 3.28:1 로 실패시켰다).
const NOTE_COLOR = {
  live: "text-muted",
  invalid: "text-danger",
  disabled: "text-muted",
} satisfies Record<State, string>;

export function TextField({
  label,
  help = null,
  error = null,
  optional = false,
  disabled = false,
  onChange,
  ...control
}: TextFieldProps) {
  const generated = useId();
  const id = control.id ?? generated;
  const noteId = `${id}-note`;
  const note = error ?? help;
  const state: State = disabled ? "disabled" : error === null ? "live" : "invalid";
  const wiring = {
    id,
    disabled,
    "aria-invalid": error === null ? undefined : true,
    "aria-describedby": note === null ? undefined : noteId,
  };

  let field: ReactNode;
  if (control.variant === "multi") {
    const { variant, rows = 3, ...native } = control;
    field = (
      <textarea
        {...native}
        {...wiring}
        rows={rows}
        onChange={(event) => onChange?.(event.currentTarget.value)}
        className={`${CONTROL} ${SIZE_CLASS[variant]} ${STATE_CLASS[state]}`}
      />
    );
  } else {
    const { variant = "single", ...native } = control;
    field = (
      <input
        {...native}
        {...wiring}
        type="text"
        onChange={(event) => onChange?.(event.currentTarget.value)}
        className={`${CONTROL} ${SIZE_CLASS[variant]} ${STATE_CLASS[state]}`}
      />
    );
  }

  return (
    <div className="flex min-w-0 flex-col gap-1">
      <label htmlFor={id} className={`text-small ${disabled ? "text-disabled-text" : "text-text"}`}>
        {label}
        {optional ? (
          <>
            {" "}
            <span className="inline-block font-regular text-muted">선택</span>
          </>
        ) : null}
      </label>
      {field}
      {note === null ? null : (
        <p
          id={noteId}
          className={`flex items-center gap-1 text-small font-regular ${NOTE_COLOR[state]}`}
        >
          {error === null ? null : <Icon name="circle-x" size="14" />}
          {note}
        </p>
      )}
    </div>
  );
}
