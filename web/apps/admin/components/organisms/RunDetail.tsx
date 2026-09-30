import { Fragment, useId } from "react";
import type { TraceEvent } from "../../api/traces";
import { useTrace } from "../../hooks/queries/traces";
import { ReadSection } from "./ReadSection";

/**
 * 실행 하나(`GET /traces/{run_id}`). 이벤트를 쓴 순서 그대로 전부 보인다(스토리 28). 응답에는 요약이 없어 형식 버전은
 * 트레이스에서 읽는다. 목록을 거치지 않고 곧장 열어도 선다(ADR 0010 의 2026-09-24 이력). 새로 고침과 실패의 표시는
 * 읽기 골격(`ReadSection`)이다. 없는 실행(404)과 읽을 수 없는 파일(500)은 봉투의 메시지다.
 *
 * **트레이스의 내용은 글자로만 그린다**(스토리 32). 도구 결과와 프롬프트는 바깥에서 온 텍스트라, HTML 로 그리면 XSS 가
 * 곧 토큰 유출이다(ADR 0019). 값은 모두 React 의 텍스트 자식으로만 넣어 기본 이스케이프에 기댄다.
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
        </>
      )}
    </ReadSection>
  );
}

/** 이벤트 종류 가운데 어느 하나라도 가진 필드의 이름. 판별자와 실행 식별자는 보이지 않는다. */
type EventField = Exclude<FieldOf<TraceEvent>, "type" | "run_id">;
type FieldOf<T> = T extends unknown ? keyof T : never;

/**
 * 필드 이름 앞에 붙이는 용어집의 말. `Record` 라서 계약의 이벤트에 필드가 늘거나 줄면 여기가 컴파일에서 깨진다. 화면이
 * 빌드된 뒤 서버에 는 필드는 이름만 보인다.
 */
const FIELD_NAMES = {
  ts: "시각",
  agent: "에이전트",
  principal: "주체",
  request: "요청",
  model: "모델",
  prompt: "프롬프트",
  text: "응답 텍스트",
  tool_calls: "도구 호출",
  input_tokens: "입력 토큰 수",
  output_tokens: "응답 토큰 수",
  tool: "도구",
  ok: "성공",
  args: "인자",
  content: "결과 내용",
  approver: "승인자",
  reason: "사유",
  output: "출력",
  error: "에러",
  raw: "원문",
} as const satisfies Record<EventField, string>;

function isEventField(name: string): name is EventField {
  return Object.hasOwn(FIELD_NAMES, name);
}

/**
 * 이벤트 하나. 제목은 종류(`type`)이고 필드를 서버가 준 차례대로, 용어집의 말과 계약의 이름을 함께 보인다(스토리 31).
 * 모르는 종류는 원문 문자열(`raw`) 하나다(스토리 29). 실행 식별자는 화면의 제목이라 되풀이하지 않는다.
 */
function EventItem({ event }: { readonly event: TraceEvent }) {
  return (
    <li>
      <h4>{event.type === "unknown" ? "모르는 종류" : event.type}</h4>
      <dl>
        {Object.entries(event)
          .filter(([name]) => name !== "type" && name !== "run_id")
          .map(([name, value]) => (
            <Fragment key={name}>
              <dt>
                {isEventField(name) ? `${FIELD_NAMES[name]} ` : null}
                <code>{name}</code>
              </dt>
              <dd style={{ whiteSpace: "pre-wrap" }}>{asText(value)}</dd>
            </Fragment>
          ))}
      </dl>
    </li>
  );
}

/**
 * 필드 값의 글자. 문자열은 들어온 그대로다. 그 밖의 JSON 값(수, 참거짓, 인자 같은 객체, 도구 호출 같은 배열)은 두 칸
 * 들여 적는다. 마스킹된 인자는 서버가 이미 `***` 로 적어 보낸다.
 */
function asText(value: unknown): string {
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}
