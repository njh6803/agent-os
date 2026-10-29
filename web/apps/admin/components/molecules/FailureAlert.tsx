// 실패 알림(admin-style 명세 "화면 머리와 공통 상태"의 실패 알림 표). 패키지 `Alert` 의 위험이다. 제목은 실패한 일이고,
// 본문은 메시지(봉투의 `message`, 봉투가 아니면 "서버에 닿지 못했다")와 그 아래 고정폭의 "추적 식별자: <값>"(있을 때)다.
// 추적 식별자는 서버의 표준 에러에서 같은 줄을 찾는 자리다(.claude/rules/http.md). 메시지는 여러 줄일 수 있어 줄바꿈을
// 그대로 보인다. 그 아래에 실패마다 더할 것(결정의 형식 오류의 위반 목록)을 `children` 으로 받는다.
import { Alert } from "@agent-os/ui";
import type { ReactNode } from "react";
import type { FailureNoticeProps } from "./FailureNotice";

interface FailureAlertProps extends FailureNoticeProps {
  readonly title: string;
  /** 추적 식별자 아래에 더할 것. */
  readonly children?: ReactNode;
}

export function FailureAlert({ title, message, requestId, children = null }: FailureAlertProps) {
  return (
    <Alert tone="danger" title={title}>
      {/* `children` 이 목록(`ul`)일 수 있어 묶음은 구문 콘텐츠만 받는 `span` 이 아니라 `div` 다. */}
      <div className="flex flex-col gap-1">
        <span className="whitespace-pre-wrap">{message}</span>
        {requestId === null ? null : (
          <span>
            추적 식별자: <code className="font-mono text-mono wrap-anywhere">{requestId}</code>
          </span>
        )}
        {children}
      </div>
    </Alert>
  );
}
