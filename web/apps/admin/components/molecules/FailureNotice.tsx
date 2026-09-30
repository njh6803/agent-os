interface FailureNoticeProps {
  readonly message: string;
  /** 추적 식별자. 서버의 표준 에러에서 같은 줄을 찾는 자리다(.claude/rules/http.md). 없으면 싣지 않는다. */
  readonly requestId: string | null;
}

/** 실패 하나. 메시지는 여러 줄일 수 있어 줄바꿈을 그대로 보인다. */
export function FailureNotice({ message, requestId }: FailureNoticeProps) {
  return (
    <div role="alert">
      <p style={{ whiteSpace: "pre-wrap" }}>{message}</p>
      {requestId === null ? null : (
        <p>
          추적 식별자: <code>{requestId}</code>
        </p>
      )}
    </div>
  );
}
