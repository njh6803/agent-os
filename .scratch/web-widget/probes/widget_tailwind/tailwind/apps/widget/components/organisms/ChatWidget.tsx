// 채팅 위젯 하나(React 19, Tailwind). 머리(제목, 닫기), 메시지 목록, 입력창과 보내기. 보내면 실행을 일으키고 프레임을
// 받는 대로 목록에 붙인다. 커스텀 요소(shadow root)와 iframe 페이지(Vite 정적, Next)가 이 컴포넌트를 같이 쓴다.
// 클래스는 shadow root 에서 `@property` 에 기대는 유틸리티(border, shadow, ring, gradient, space-y, scale)를 일부러 든다.

import { useEffect, useRef, useState, type ReactElement, type SubmitEvent } from "react";
import { startRun, type RunTarget } from "../../api/runs";
import { describeFrame, type Line, type Role } from "../../lib/frames";
import { CloseIcon, SendIcon } from "../atoms/icons";

const LINE_CLASS: Record<Role, string> = {
  user: "font-semibold",
  agent: "text-blue-700 dark:text-blue-300",
  event: "text-xs text-gray-500",
};

export function ChatWidget({ target }: { readonly target: RunTarget }): ReactElement {
  const [open, setOpen] = useState(true);
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

  function submit(event: SubmitEvent<HTMLFormElement>): void {
    event.preventDefault();
    const request = draft.trim();
    if (request === "" || busy) {
      return;
    }
    setDraft("");
    void send(request);
  }

  if (!open) {
    return (
      <button
        type="button"
        className="rounded-full bg-blue-600 px-4 py-2 text-sm text-white shadow-lg"
        onClick={() => {
          setOpen(true);
        }}
      >
        채팅 열기
      </button>
    );
  }

  return (
    <section
      className="flex w-80 flex-col gap-2 rounded-lg border border-gray-300 bg-white p-3 text-sm text-gray-900 shadow-md dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100"
      aria-label="채팅"
    >
      <header className="flex items-center justify-between">
        <h2 className="text-base font-semibold">Agent OS</h2>
        <button
          type="button"
          aria-label="닫기"
          className="rounded p-1 text-gray-500 hover:bg-gray-100 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none"
          onClick={() => {
            setOpen(false);
          }}
        >
          <CloseIcon className="size-4" />
        </button>
      </header>
      <ul className="max-h-60 list-none space-y-1 overflow-y-auto" aria-label="메시지">
        {lines.map((line) => (
          <li key={line.id} data-role={line.role} className={LINE_CLASS[line.role]}>
            {line.text}
          </li>
        ))}
      </ul>
      <form className="flex gap-1" onSubmit={submit}>
        <input
          aria-label="메시지 입력"
          className="min-w-0 flex-1 rounded border border-gray-300 px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800"
          value={draft}
          onChange={(event) => {
            setDraft(event.currentTarget.value);
          }}
        />
        <button
          type="submit"
          disabled={busy}
          className="inline-flex items-center gap-1 rounded bg-linear-to-r from-blue-600 to-indigo-600 px-3 py-1 text-white shadow-sm transition hover:scale-105 disabled:opacity-50"
        >
          <SendIcon className="size-4" />
          보내기
        </button>
      </form>
    </section>
  );
}
