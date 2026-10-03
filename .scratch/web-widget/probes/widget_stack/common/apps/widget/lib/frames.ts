// 목록의 한 줄과, 프레임 하나를 한 줄로 바꾸는 것. 후보 넷이 같은 것을 쓴다.

import type { StreamFrame } from "../api/runs";

export type Role = "user" | "agent" | "event";

export interface Line {
  readonly id: number;
  readonly role: Role;
  readonly text: string;
}

export function describeFrame(frame: StreamFrame): { readonly role: Role; readonly text: string } {
  if (frame.kind === "raw") {
    return { role: "event", text: frame.raw };
  }
  const { event } = frame;
  switch (event.type) {
    case "run_finished":
      return { role: "agent", text: event.output };
    case "run_failed":
      return { role: "event", text: `실패: ${event.error}` };
    default:
      return { role: "event", text: event.type };
  }
}
