// 알림(디자인 파일 02.6). 화면이나 영역 전체에 걸린 일을 아이콘과 제목, 본문으로 알린다. 톤 셋(실패·경고·정보, 기본
// 정보). 실패만 `role="alert"` 로 화면 읽기 프로그램을 끊고, 경고와 정보는 `role="status"` 라 읽던 글을 끊지 않는다.
// 알림 자체는 누르는 곳이 아니고 포커스를 받지 않는다. 그래서 상호작용 상태가 없고, 닫기 버튼(투명·작은 아이콘 버튼)
// 이 아이콘 버튼의 상태를 따른다. 제목이 표의 `title` 이라 요소의 `title` 속성(툴팁)은 받지 않는다(`props.ts`).
import type { ReactNode } from "react";
import type { NativeProps } from "../../props";
import { Icon, type IconName } from "../atoms/Icon";
import { IconButton } from "../atoms/IconButton";

export type AlertTone = "danger" | "warning" | "info";

interface AlertOwnProps {
  /** 일어난 일. */
  title: string;
  tone?: AlertTone;
  /** 본문. 까닭이나 할 일. */
  children?: ReactNode;
  /** 버튼과 링크의 자리. 본문 아래에 놓인다. */
  actions?: ReactNode;
  /** 있으면 오른쪽 끝에 이름이 "닫기"인 아이콘 버튼을 두고 누르면 부른다. */
  onClose?: (() => void) | null;
}

export type AlertProps = AlertOwnProps &
  NativeProps<"div", keyof AlertOwnProps | "role" | "tabIndex">;

const TONE_CLASS = {
  danger: "bg-danger-tint",
  warning: "bg-warning-tint",
  info: "bg-info-tint",
} satisfies Record<AlertTone, string>;

const ICON_CLASS = {
  danger: "text-danger",
  warning: "text-warning",
  info: "text-info",
} satisfies Record<AlertTone, string>;

const ICON = {
  danger: "circle-x",
  warning: "triangle-alert",
  info: "info",
} satisfies Record<AlertTone, IconName>;

export function Alert({
  title,
  tone = "info",
  children = null,
  actions = null,
  onClose = null,
  ...rest
}: AlertProps) {
  return (
    <div
      {...rest}
      role={tone === "danger" ? "alert" : "status"}
      className={`flex items-start gap-3 rounded-l px-4 py-3 text-text ${TONE_CLASS[tone]}`}
    >
      <span className={`flex shrink-0 ${ICON_CLASS[tone]}`}>
        <Icon name={ICON[tone]} />
      </span>
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <div className="flex flex-col">
          <p className="text-small font-strong">{title}</p>
          {children === null ? null : (
            <div className="text-small font-regular text-muted">{children}</div>
          )}
        </div>
        {actions === null ? null : (
          <div className="flex flex-wrap items-center gap-3">{actions}</div>
        )}
      </div>
      {onClose === null ? null : (
        // 32px 버튼이 20px 제목 줄보다 높아 위아래로 4px 씩 내밀고, 오른쪽 여백을 8px 로 줄인다.
        <span className="-my-1 -mr-2 shrink-0">
          <IconButton icon="x" label="닫기" size="s" onClick={onClose} />
        </span>
      )}
    </div>
  );
}
