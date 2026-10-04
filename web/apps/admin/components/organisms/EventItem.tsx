import { Fragment } from "react";
import type { TraceEvent } from "../../api/traces";

// 이벤트 하나를 글자로 그린다. 트레이스 상세의 이벤트와 재개 스트림으로 받은 이벤트가 이것 하나를 지난다. 이벤트
// 타입이 `api/` 에 있어 molecules 가 아니라 여기 둔다(atoms·molecules 는 API 의 자리를 import 하지 않는다).
//
// **글자로만 그린다**(web-admin 스토리 32). 도구 결과와 프롬프트는 바깥에서 온 텍스트라, HTML 로 그리면 XSS 가 곧
// 토큰 유출이다(ADR 0019). 값은 모두 React 의 텍스트 자식으로만 넣어 기본 이스케이프에 기댄다.

/** 이벤트 종류 가운데 어느 하나라도 가진 필드의 이름. 판별자와 실행 식별자는 보이지 않는다. */
type EventField = Exclude<FieldOf<TraceEvent>, "type" | "run_id">;
type FieldOf<T> = T extends unknown ? keyof T : never;

/**
 * 필드 이름 앞에 붙이는 용어집의 말. `Record` 라서 계약의 이벤트에 필드가 늘거나 줄면 여기가 컴파일에서 깨진다. 화면이
 * 빌드된 뒤 서버에서 느는 필드는 이름만 보인다.
 */
const FIELD_NAMES = {
  ts: "시각",
  agent: "에이전트",
  principal: "주체",
  previous_run: "앞 실행",
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
  summary: "요약 글",
  last_covered_run: "덮는 끝",
  raw: "원문",
} as const satisfies Record<EventField, string>;

function isEventField(name: string): name is EventField {
  return Object.hasOwn(FIELD_NAMES, name);
}

/**
 * 이벤트 하나. 제목은 종류(`type`)이고 필드를 서버가 준 차례대로, 용어집의 말과 계약의 이름을 함께 보인다(스토리 31).
 * 모르는 종류는 원문 문자열(`raw`) 하나다(스토리 29). 실행 식별자는 화면의 제목이라 되풀이하지 않는다.
 */
export function EventItem({ event }: { readonly event: TraceEvent }) {
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
export function asText(value: unknown): string {
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}
