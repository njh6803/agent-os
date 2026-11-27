import { IconButton } from "@agent-os/ui";
import { useEffect, useRef } from "react";
import type { Trace } from "../../api/traces";
import { EventItem } from "./EventItem";
import { ReadSection, type ReadState } from "./ReadSection";
import { starter } from "./RunDetail";

interface RunPanelProps extends ReadState<Trace> {
  readonly runId: string;
  /** 닫는다. 닫기 버튼과 Esc 가 부른다. 주소의 `?run=` 질의를 빼는 것은 부르는 쪽의 일이다. */
  readonly onClose: () => void;
}

/**
 * 실행 패널(admin-login 명세 "실행 패널"). 대화 화면 위 오른쪽에 뜨는 폭 480px 의 칸이고 지금 실행 상세 화면이 보이는
 * 것(실행 식별자, 에이전트, 주체, 이벤트의 열과 칸마다의 화면 이름)을 그대로 옮긴다. 시각은 트레이스의 UTC 값 그대로이고
 * 결정 자리는 두지 않는다(승인과 거부는 대화 안에서만 한다).
 *
 * 대화를 막지 않아 덮개가 없고, 열린 채로 다른 실행의 "자세히"를 누르면 내용만 바뀐다. 폭 `wide` 미만에서는 화면 전체를
 * 덮는다. 머리의 "새로 고침"은 그 실행의 트레이스를 다시 읽는다. 패널은 주기 읽기를 따로 걸지 않는다(끝 실행의 패널은
 * 대화 화면의 주기 읽기가 같은 값을 고친다). 새로 고침과 실패의 표시는 읽기 골격(`ReadSection`)이다. 다시 읽다 실패하면
 * 보인 이벤트를 지우고 실패만 보인다.
 *
 * 열리면 포커스가 닫기 버튼으로 가고, 닫히면 열기 전에 포커스가 있던 곳("자세히")으로 돌아온다. 키보드 사용자가 Esc 로
 * 닫는 길과 같은 자리에서 시작하게 한다. 이미 열린 채 내용만 바뀔 때는 포커스를 옮기지 않는다.
 */
export function RunPanel({ runId, onClose, ...read }: RunPanelProps) {
  const panelRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const opener = document.activeElement;
    panelRef.current?.querySelector<HTMLElement>("button[aria-label='닫기']")?.focus();
    return () => {
      // 닫히면 열 때 포커스가 있던 "자세히"로 돌려 키보드 사용자가 읽던 자리에서 이어 가게 한다. 주소로 바로 열려
      // 포커스가 문서 바탕에 있었으면 돌려줄 자리가 없다.
      if (opener instanceof HTMLElement && opener !== document.body && opener.isConnected) {
        opener.focus();
      }
    };
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [onClose]);

  return (
    <aside
      ref={panelRef}
      id="run-panel"
      aria-label="실행 패널"
      className="fixed inset-0 z-10 overflow-y-auto bg-bg px-6 py-4 wide:left-auto wide:w-panel wide:border-l wide:border-border wide:shadow-float"
    >
      <ReadSection
        headingLevel="h2"
        title="실행"
        description={
          <RunHeader runId={runId} trace={read.data} failed={read.error !== undefined} />
        }
        {...read}
        loadingLabel="실행을 불러오는 중"
        failureTitle="실행을 읽지 못했다"
        actions={<IconButton icon="x" label="닫기" onClick={onClose} />}
      >
        {(trace) => (
          <ol
            aria-label={`이벤트 ${String(trace.events.length)}개`}
            className="flex flex-col gap-3"
          >
            {trace.events.map((event, index) => (
              // 이벤트는 트레이스에 쓴 차례로만 갈린다. 같은 트레이스 안에서 그 차례는 바뀌지 않는다.
              <EventItem key={index} event={event} />
            ))}
          </ol>
        )}
      </ReadSection>
    </aside>
  );
}

/** 머리 설명. 고정폭 실행 식별자 한 줄과 에이전트·주체 줄이다. 값을 읽은 뒤에만 서고 실패하면 식별자만 남는다. */
function RunHeader({
  runId,
  trace,
  failed,
}: {
  readonly runId: string;
  readonly trace: Trace | undefined;
  readonly failed: boolean;
}) {
  return (
    <span className="flex flex-col gap-2">
      <span className="font-mono text-mono text-text wrap-anywhere">{runId}</span>
      {trace === undefined || failed ? null : starter(trace)}
    </span>
  );
}
