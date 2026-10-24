// 도구 줄 하나(화면 디자인 mk-conversation). 아이콘, 고정폭 도구 이름, 성공·실패 글자다. 성공과 실패는 아이콘 모양과
// 글자로 함께 가르고 색만으로 가르지 않는다. 아이콘은 글자 옆이라 화면 읽기 프로그램에서 숨는다.
import { Icon } from "@agent-os/ui";

export interface ToolRowProps {
  /** 고치거나 줄이지 않고 그대로 보인다. */
  readonly tool: string;
  readonly ok: boolean;
}

export function ToolRow({ tool, ok }: ToolRowProps) {
  return (
    <li className="flex items-center gap-2 text-small text-text-muted">
      <span className={`flex ${ok ? "text-success" : "text-danger"}`}>
        <Icon name={ok ? "circle-check" : "circle-x"} size="14" />
      </span>
      <span className="font-mono font-medium wrap-anywhere text-text">{tool}</span>
      <span className="shrink-0">{ok ? "성공" : "실패"}</span>
    </li>
  );
}
