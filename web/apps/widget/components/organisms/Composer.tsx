// 아래 입력 자리. 여러 줄 입력창과 보내기 버튼이고, 버튼은 디자인 시스템 버튼의 크기 그대로 입력창의 아래 끝에
// 맞춘다(web-widget 명세 "대화 화면"의 보내기 버튼의 크기).
//
// - Enter 는 보내고 Shift+Enter 는 줄을 바꾼다. 한글을 조합하는 중(`isComposing`)에 누른 Enter 는 보내지 않는다.
// - 글자 수는 코드 포인트로 센다(서버와 같다). 상한의 90% 이상이면 입력창 아래에 센 수를, 넘으면 넘었다는 글을 위험
//   색으로 보인다. 그 글은 입력창 부품이 `aria-describedby` 로 입력창에 묶는다. 칸 아래 글이 서면 입력창의 아래 끝이
//   그만큼 올라가므로 버튼도 그 글의 높이만큼 띄운다.
// - 보내기는 입력이 비었거나(앞뒤 공백만 있는 것도), 상한을 넘었거나, 부르는 쪽이 막았을 때(실행이 돌거나 멈춰
//   있거나, 설정이 잘못됐을 때) 막힌다. 상한의 기다림으로 막히는 것은 티켓 07 이 더한다.
import { IconButton, TextField } from "@agent-os/ui";

export interface ComposerProps {
  readonly value: string;
  readonly onChange: (value: string) => void;
  /** 다듬지 않은 입력을 넘긴다. 보낼 수 있을 때만 부른다. */
  readonly onSend: (request: string) => void;
  /** 요청 글자 수 상한(코드 포인트). */
  readonly limit: number;
  /** 입력창을 막는다. 설정이 잘못됐거나 승인을 기다리며 멈춰 있을 때다. */
  readonly disabled: boolean;
  /** 보내기만 막는다. 실행이 돌거나 멈춰 있을 때다. */
  readonly blocked: boolean;
}

const NUMBER = new Intl.NumberFormat("ko-KR");

/** 센 수를 보이기 시작하는 비율. */
const NEAR_LIMIT = 0.9;

export function Composer({ value, onChange, onSend, limit, disabled, blocked }: ComposerProps) {
  // 코드 포인트로 센다. 이모지 하나는 UTF-16 으로 둘이지만 하나다.
  const count = Array.from(value).length;
  const over = count > limit;
  const near = count >= limit * NEAR_LIMIT;
  const sendable = !disabled && !blocked && !over && value.trim() !== "";
  const send = () => {
    if (sendable) {
      onSend(value);
    }
  };
  const note = over || near;

  return (
    <form
      className="flex shrink-0 items-end gap-2 border-t border-border p-3"
      onSubmit={(event) => {
        event.preventDefault();
        send();
      }}
    >
      <div className="min-w-0 flex-1">
        <TextField
          variant="multi"
          rows={1}
          label="요청"
          placeholder="요청을 적어 주세요"
          value={value}
          onChange={onChange}
          disabled={disabled}
          help={!over && near ? `${NUMBER.format(count)} / ${NUMBER.format(limit)}` : null}
          error={over ? `${NUMBER.format(limit)}자를 넘었습니다` : null}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
              event.preventDefault();
              send();
            }
          }}
        />
      </div>
      {/* 칸 아래 글은 칸과 글 사이 4px 와 작은 글자 한 줄 16px 이다. */}
      <div className={note ? "mb-4 pb-1" : undefined}>
        <IconButton
          icon="send"
          label="보내기"
          variant="primary"
          disabled={!sendable}
          onClick={send}
        />
      </div>
    </form>
  );
}
