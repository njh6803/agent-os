// 아래 입력 자리. 입력창 위의 띠, 여러 줄 입력창과 보내기 버튼이고, 버튼은 디자인 시스템 버튼의 크기 그대로 입력창의
// 아래 끝에 맞춘다(web-widget 명세 "대화 화면"의 보내기 버튼의 크기).
//
// - Enter 는 보내고 Shift+Enter 는 줄을 바꾼다. 한글을 조합하는 중(`isComposing`)에 누른 Enter 는 보내지 않는다.
// - 글자 수는 코드 포인트로 센다(서버와 같다). 상한의 90% 이상이면 입력창 아래에 센 수를, 넘으면 넘었다는 글을 위험
//   색으로 보인다. 그 글은 입력창 부품이 `aria-describedby` 로 입력창에 묶는다. 칸 아래 글이 서면 입력창의 아래 끝이
//   그만큼 올라가므로 버튼도 그 글의 높이만큼 띄운다. 앞 요청이 422 로 되돌아왔으면 같은 자리에 고쳐 보내라는 글을
//   보인다. 넘었다는 글이 먼저다.
// - 상한(429)에 걸리면 띠가 상한의 문구와 기다릴 시간을 보인다. 숫자는 매초 줄지만 `aria-hidden` 이고, 화면 읽기
//   프로그램은 숨긴 사본의 처음 시간을 읽는다. 그래서 띠가 설 때 한 번, 시간이 다 되어 글이 바뀔 때 한 번 읽힌다.
// - 승인 묻기가 결정을 기다리는 동안 입력창은 막힌 채 남고, 띠가 승인이나 거부를 먼저 고르라고 한다. 결정이 429 를
//   받으면 상한의 띠가 앞서고, 그 시간이 다 되면 걷혀 승인 기다림의 띠로 돌아온다.
// - 보내기는 입력이 비었거나(앞뒤 공백만 있는 것도), 글자 수 상한을 넘었거나, 부르는 쪽이 막았을 때(실행이 돌거나
//   멈춰 있거나, 상한의 기다림이 남았거나, 설정이 잘못됐을 때) 막힌다.
import { IconButton, TextField } from "@agent-os/ui";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { charNote } from "../../lib/chars";
import { limitSentence, READY, waitText, type LimitWait } from "../../lib/limit";
import { ComposerBand, type Band } from "../molecules/ComposerBand";

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
  /**
   * 이 값이 null 이 아닌 다른 값으로 바뀌면 입력창에 포커스를 준다. 버튼 없이 요청을 고쳐 보내라는 실패(`loop_limit`)가
   * 그 교환의 번호로 준다. 같은 값으로 다시 그려도 포커스를 옮기지 않는다.
   */
  readonly focusFor: number | null;
  /** 상한(429)에 걸려 기다리는 중. 띠가 선다. 보내기를 막는 것은 부르는 쪽(`blocked`)이다. */
  readonly wait: LimitWait | null;
  /** 앞 요청이 422 로 되돌아왔다. */
  readonly invalid: boolean;
  /** 승인 묻기가 결정을 기다린다. 띠가 승인이나 거부를 먼저 고르라고 한다. */
  readonly awaitingDecision: boolean;
}

const INVALID = "요청을 보낼 수 없습니다. 요청을 고쳐 다시 보내 주세요.";

const APPROVAL: Band = { kind: "notice", icon: "info", text: "승인이나 거부를 먼저 골라 주세요." };

/**
 * 상한의 띠. 남은 시간이 있으면 상한의 문구이고, 다 됐으면 다시 보낼 수 있다는 글이다. 결정의 기다림은 다 되면
 * 걷혀, 승인 기다림의 띠가 다시 선다.
 */
function limitBand(wait: LimitWait | null): Band | null {
  if (wait === null) {
    return null;
  }
  if (wait.remaining === 0) {
    return wait.purpose === "decide" ? null : { kind: "notice", icon: "info", text: READY };
  }
  const { before, after } = limitSentence(wait.limit, wait.purpose);
  return {
    kind: "notice",
    icon: "info",
    text: (
      <>
        {before}
        <span aria-hidden="true">{waitText(wait.remaining)}</span>
        <span className="sr-only">{waitText(wait.seconds)}</span>
        {after}
      </>
    ),
  };
}

export function Composer({
  value,
  onChange,
  onSend,
  limit,
  disabled,
  blocked,
  focusFor,
  wait,
  invalid,
  awaitingDecision,
}: ComposerProps) {
  const box = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    if (focusFor !== null) {
      box.current?.focus();
    }
  }, [focusFor]);

  const note = charNote(value, limit);
  const sendable = !disabled && !blocked && !note.over && value.trim() !== "";
  const send = () => {
    if (sendable) {
      onSend(value);
    }
  };
  const error = note.overText ?? (invalid ? INVALID : null);
  const help = note.count;

  // 칸 아래 글만큼 버튼을 올린다. 글이 칸의 폭에서 몇 줄로 꺾일지 몰라(422 의 글은 400px 에서도 두 줄이다) 칸 묶음과
  // 입력창의 아래 끝 사이를 잰다. 글이 서거나 바뀌거나, 폭이나 늦게 실린 글꼴로 다시 꺾이면 칸 묶음의 높이가 바뀌므로
  // 그때마다 다시 잰다. 화면 동작 테스트의 jsdom 에는 ResizeObserver 가 없고 레이아웃도 없어 처음 한 번만 잰다. 잰
  // 값이라 공통 크기의 이름 있는 단계가 아니라 인라인 `style` 로 준다.
  const field = useRef<HTMLDivElement>(null);
  const [lift, setLift] = useState(0);
  useLayoutEffect(() => {
    const wrapper = field.current;
    if (wrapper === null) {
      return;
    }
    const measure = () => {
      const bottom = box.current?.getBoundingClientRect().bottom;
      setLift(bottom === undefined ? 0 : wrapper.getBoundingClientRect().bottom - bottom);
    };
    measure();
    if (typeof ResizeObserver === "undefined") {
      return;
    }
    const observer = new ResizeObserver(measure);
    observer.observe(wrapper);
    return () => {
      observer.disconnect();
    };
  }, []);

  return (
    <>
      <ComposerBand
        reconnect={null}
        limit={limitBand(wait)}
        approval={awaitingDecision ? APPROVAL : null}
      />
      <form
        className="flex shrink-0 items-end gap-2 p-3"
        onSubmit={(event) => {
          event.preventDefault();
          send();
        }}
      >
        <div ref={field} className="min-w-0 flex-1">
          <TextField
            ref={box}
            variant="multi"
            rows={1}
            label="요청"
            placeholder="요청을 적어 주세요"
            value={value}
            onChange={onChange}
            disabled={disabled}
            help={help}
            error={error}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
                event.preventDefault();
                send();
              }
            }}
          />
        </div>
        <div style={{ marginBottom: lift }}>
          <IconButton
            icon="send"
            label="보내기"
            variant="primary"
            disabled={!sendable}
            onClick={send}
          />
        </div>
      </form>
    </>
  );
}
