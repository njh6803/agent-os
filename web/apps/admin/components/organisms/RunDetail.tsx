import { useId } from "react";
import { useTrace } from "../../hooks/queries/traces";
import { EventItem } from "./EventItem";
import { ReadSection } from "./ReadSection";
import { RunDecision } from "./RunDecision";

/**
 * 실행 하나(`GET /traces/{run_id}`). 이벤트를 쓴 순서 그대로 전부 보인다(스토리 28). 응답에는 요약이 없어 형식 버전은
 * 트레이스에서 읽는다. 목록을 거치지 않고 곧장 열어도 선다(ADR 0010 의 2026-09-24 이력). 새로 고침과 실패의 표시는
 * 읽기 골격(`ReadSection`)이다. 없는 실행(404)과 읽을 수 없는 파일(500)은 봉투의 메시지다.
 *
 * 이벤트 아래에 결정 자리와 재개 스트림이 선다(`RunDecision`). 둘 다 값의 갈래 안이라, 다시 읽다 실패하면 함께 걷힌다.
 * 트레이스의 내용은 글자로만 그린다(`EventItem`).
 */
export function RunDetail({ runId }: { readonly runId: string }) {
  const { data, error, isValidating, mutate } = useTrace(runId);
  const eventsId = useId();

  return (
    <ReadSection
      heading={runId}
      data={data}
      error={error}
      isValidating={isValidating}
      onRefresh={() => {
        void mutate();
      }}
      placeholder="트레이스를 불러오는 중이다"
    >
      {(trace) => (
        <>
          {trace.schema_version === "1" ? (
            <p>형식 1 트레이스라 읽을 수 있지만 재개할 수 없다</p>
          ) : null}
          <section aria-labelledby={eventsId}>
            <h3 id={eventsId}>이벤트</h3>
            <ol>
              {trace.events.map((event, index) => (
                // 이벤트는 트레이스에 쓴 차례로만 갈린다. 같은 트레이스 안에서 그 차례는 바뀌지 않는다.
                <EventItem key={index} event={event} />
              ))}
            </ol>
          </section>
          <RunDecision runId={runId} trace={trace} />
        </>
      )}
    </ReadSection>
  );
}
