// 채팅 위젯 하나(Preact 11, preact/compat 없이). 입력창, 메시지 목록, 보내기 버튼. 보내면 실행을 일으키고 프레임을 받는
// 대로 목록에 붙인다. 커스텀 요소(shadow root)와 iframe 페이지가 이 컴포넌트를 같이 쓴다.

import type { JSX, TargetedSubmitEvent } from "preact";
import { useEffect, useRef, useState } from "preact/hooks";
import { startRun, type RunTarget } from "../../api/runs";
import { describeFrame, type Line, type Role } from "../../lib/frames";

export function ChatWidget({ target }: { readonly target: RunTarget }): JSX.Element {
  const [lines, setLines] = useState<readonly Line[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const nextId = useRef(0);
  const running = useRef<AbortController | null>(null);

  useEffect(
    () => () => {
      running.current?.abort();
    },
    [],
  );

  function append(role: Role, text: string): void {
    const id = nextId.current;
    nextId.current += 1;
    setLines((previous) => [...previous, { id, role, text }]);
  }

  async function send(request: string): Promise<void> {
    const controller = new AbortController();
    running.current = controller;
    setBusy(true);
    append("user", request);
    try {
      for await (const frame of await startRun(target, request, controller.signal)) {
        const { role, text } = describeFrame(frame);
        append(role, text);
      }
    } catch (error: unknown) {
      append("event", error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  }

  function submit(event: TargetedSubmitEvent<HTMLFormElement>): void {
    event.preventDefault();
    const request = draft.trim();
    if (request === "" || busy) {
      return;
    }
    setDraft("");
    void send(request);
  }

  return (
    <section class="widget" aria-label="채팅">
      <ul class="messages" aria-label="메시지">
        {lines.map((line) => (
          <li key={line.id} data-role={line.role}>
            {line.text}
          </li>
        ))}
      </ul>
      <form onSubmit={submit}>
        <input
          aria-label="메시지 입력"
          value={draft}
          onInput={(event) => {
            setDraft(event.currentTarget.value);
          }}
        />
        <button type="submit" disabled={busy}>
          보내기
        </button>
      </form>
    </section>
  );
}
