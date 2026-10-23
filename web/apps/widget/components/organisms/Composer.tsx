// 아래 입력 자리. 여러 줄 입력창과 보내기 버튼이고, 버튼은 입력창의 아래 끝에 맞춘다. 보내는 길과 Enter 의 규칙은
// web-widget 티켓 05 가 잇는다.
import { IconButton, TextField } from "@agent-os/ui";

export interface ComposerProps {
  /** 설정이 잘못돼 요청을 보낼 수 없을 때 입력창과 버튼을 함께 막는다. */
  readonly disabled: boolean;
}

export function Composer({ disabled }: ComposerProps) {
  return (
    <form className="flex shrink-0 items-end gap-2 border-t border-border p-3">
      <div className="min-w-0 flex-1">
        <TextField
          variant="multi"
          rows={1}
          label="요청"
          placeholder="요청을 적어 주세요"
          disabled={disabled}
        />
      </div>
      <IconButton icon="send" label="보내기" variant="primary" disabled={disabled} />
    </form>
  );
}
