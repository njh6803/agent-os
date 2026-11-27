// 비활성으로 바꾸기 창(admin-login 명세 "계정 화면과 내 비밀번호", 그림 mk-accounts-disable). 제목과 네 줄, 취소와 확인이다.
// 첫 줄의 N 분은 서버가 알려 준 로그인 유지 시간(`token_minutes`)이다. 열려 있는 스트림은 계정이 막힌 뒤에도 끊지 않으므로
// 도는 실행은 끝까지 간다. 되돌리는 쪽(활성으로 바꾸기)은 창 없이 바로 바꾼다.
import { Button } from "@agent-os/ui";
import { useState } from "react";
import { describeFailure } from "../../api/failure";
import { Dialog } from "../molecules/Dialog";
import { FailureAlert } from "../molecules/FailureAlert";

interface DisableAccountDialogProps {
  readonly name: string;
  /** 로그인이 길어야 몇 분 안에 끊기는지. */
  readonly tokenMinutes: number;
  readonly onConfirm: () => Promise<void>;
  readonly onClose: () => void;
}

export function DisableAccountDialog({
  name,
  tokenMinutes,
  onConfirm,
  onClose,
}: DisableAccountDialogProps) {
  const [failure, setFailure] = useState<unknown>(null);
  const [pending, setPending] = useState(false);

  async function confirm(): Promise<void> {
    if (pending) {
      return;
    }
    setPending(true);
    setFailure(null);
    try {
      await onConfirm();
      onClose();
    } catch (cause) {
      setFailure(cause);
    } finally {
      setPending(false);
    }
  }

  const failureText = failure === null ? null : describeFailure(failure);
  return (
    <Dialog
      title={
        <>
          <span className="font-mono">{name}</span>을 비활성으로 바꾼다
        </>
      }
      onClose={onClose}
      busy={pending}
    >
      {failureText === null ? null : (
        <FailureAlert
          title="계정을 바꾸지 못했다"
          message={failureText.message}
          requestId={failureText.requestId}
        />
      )}
      <ul className="m-0 flex list-disc flex-col gap-2 pl-4 text-body">
        <li>
          이 계정의 로그인은 길어야 {tokenMinutes}분 안에 모두 끊긴다. 도는 실행은 끝까지 간다.
        </li>
        <li>이 이름으로 새 계정을 만들 수 없다.</li>
        <li>실행 기록에 남은 이름은 그대로다.</li>
        <li>언제든 활성으로 되돌릴 수 있다.</li>
      </ul>
      <div className="flex justify-end gap-2">
        <Button variant="secondary" disabled={pending} onClick={onClose}>
          취소
        </Button>
        <Button
          loading={pending}
          onClick={() => {
            void confirm();
          }}
        >
          비활성으로 바꾸기
        </Button>
      </div>
    </Dialog>
  );
}
