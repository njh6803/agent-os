import { type ReactNode, useId } from "react";
import type { Trace } from "../../api/traces";
import { EmptyLine } from "../molecules/EmptyLine";
import { EventItem } from "./EventItem";
import { ReadSection, type ReadState } from "./ReadSection";

interface RunDetailProps extends ReadState<Trace> {
  readonly runId: string;
  /**
   * 머리 아래의 본문(`RunDecision`). 보인 트레이스와 이벤트 칸을 받아, 이벤트 칸 둘레에 결정 칸·재개 스트림·결정 뒤의
   * 알림을 놓는다.
   */
  readonly body: (trace: Trace, events: ReactNode) => ReactNode;
}

/**
 * 실행 하나(`GET /traces/{run_id}`). 이벤트를 쓴 순서 그대로 전부 보인다(스토리 28). 응답에는 요약이 없어 형식 버전은
 * 트레이스에서 읽는다. 목록을 거치지 않고 곧장 열어도 선다(ADR 0010 의 2026-09-24 이력). 새로 고침과 실패의 표시는
 * 읽기 골격(`ReadSection`)이다. 없는 실행(404)과 읽을 수 없는 파일(500)은 봉투의 메시지다.
 *
 * 머리는 고정폭 실행 식별자와 그 아래 시작 이벤트에서 읽은 에이전트·주체 줄이다(admin-style 티켓 07). 상태 배지는 그리지
 * 않는다. 실행 하나의 응답에는 상태가 없고, 화면이 상태를 계산하면 core `run_status()` 한 곳의 규칙을 어긴다(명세).
 * 에이전트·주체 줄은 값을 읽은 뒤에 서므로, 다시 읽다 실패하면 이벤트와 함께 걷힌다.
 *
 * 이벤트 칸 둘레의 본문은 `body` 다. 값의 갈래 안이라 다시 읽다 실패하면 함께 걷힌다. 트레이스의 내용은 글자로만
 * 그린다(`EventItem`).
 */
export function RunDetail({ runId, body, ...read }: RunDetailProps) {
  const eventsId = useId();

  return (
    <ReadSection
      title={<span className="font-mono">{runId}</span>}
      description={
        read.data === undefined || read.error !== undefined ? undefined : starter(read.data)
      }
      {...read}
      loadingLabel="트레이스를 불러오는 중"
      failureTitle="실행을 읽지 못했다"
    >
      {(trace) => (
        <>
          {trace.schema_version === "1" ? (
            <EmptyLine icon="circle-minus" iconSize="16">
              형식 1 트레이스라 읽을 수 있지만 재개할 수 없다
            </EmptyLine>
          ) : null}
          {body(
            trace,
            <section aria-labelledby={eventsId} className="flex flex-col gap-3">
              <h2 id={eventsId} className="text-body font-semibold">
                이벤트 <span className="font-regular text-text-muted">{trace.events.length}</span>
              </h2>
              <ol className="flex flex-col gap-3">
                {trace.events.map((event, index) => (
                  // 이벤트는 트레이스에 쓴 차례로만 갈린다. 같은 트레이스 안에서 그 차례는 바뀌지 않는다.
                  <EventItem key={index} event={event} />
                ))}
              </ol>
            </section>,
          )}
        </>
      )}
    </ReadSection>
  );
}

/** 머리 설명의 에이전트·주체 줄. 첫 이벤트가 시작 이벤트가 아니면 없다. 긴 주체(`<발급자>|<sub>`)는 줄을 바꿔 흐른다. */
function starter(trace: Trace): ReactNode {
  const first = trace.events[0];
  if (first?.type !== "run_started") {
    return undefined;
  }
  return (
    <span className="flex flex-wrap gap-x-3 wrap-anywhere">
      <span>에이전트 {first.agent}</span> <span>주체 {first.principal}</span>
    </span>
  );
}
