import Link from "next/link";
import { Fragment } from "react";
import type { TraceEvent } from "../../api/traces";

// 이벤트 하나를 글자로 그린다. 트레이스 상세의 이벤트와 재개 스트림으로 받은 이벤트가 이것 하나를 지난다. 이벤트
// 타입이 `api/` 에 있어 molecules 가 아니라 여기 둔다(atoms·molecules 는 API 의 자리를 import 하지 않는다).
//
// **글자로만 그린다**(web-admin 스토리 32). 도구 결과와 프롬프트는 바깥에서 온 텍스트라, HTML 로 그리면 XSS 가 곧
// 토큰 유출이다(ADR 0019). 값은 React 의 텍스트 자식으로만 넣어 기본 이스케이프에 기댄다. 예외 하나가 실행 식별자
// 필드 둘(`RUN_FIELDS`)이다. 그 값은 링크의 글자이면서 `href` 에도 든다. 글자로만 그린다는 규칙과 양립하는 것은
// `href` 가 트레이스의 값을 그대로 받지 않고 `/runs/` 뒤에 `encodeURIComponent` 로 감싼 조각으로만 받기 때문이다.
// 빗금·물음표·우물 정자·콜론이 모두 인코딩되어 값이 그 경로 조각 밖으로 나가지 못하고, `javascript:` 로 시작하는 값도
// 같은 경로 아래의 식별자 글자가 된다. 인코딩이 그대로 두는 `.` 과 `..` 만은 `/runs/..` 이 `/` 로 풀리므로 링크가 아니라
// 글자다(`runHref`). 실행 목록의 링크와 같은 모양이다(`RunList`).

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
 * 값이 다른 실행의 식별자인 필드. 시작 이벤트의 앞 실행과 요약이 덮는 끝이고, 그 실행의 상세로 가는 링크로 그린다.
 * 운영자가 대화를 거슬러 보고 요약을 원문 교환과 대조하는 길이다(conversation 스토리 41·43). 값이 없으면(이어 가지 않은
 * 실행의 `null`) 다른 필드처럼 글자다.
 */
const RUN_FIELDS: ReadonlySet<EventField> = new Set(["previous_run", "last_covered_run"]);

/**
 * 이벤트 하나. 제목은 종류(`type`)이고 필드를 서버가 준 차례대로, 용어집의 말과 계약의 이름을 함께 보인다(스토리 31).
 * 모르는 종류는 원문 문자열(`raw`) 하나다(스토리 29). 실행 식별자는 화면의 제목이라 되풀이하지 않는다.
 */
export function EventItem({ event }: { readonly event: TraceEvent }) {
  return (
    <li>
      <h4>{event.type === "unknown" ? "모르는 종류" : event.type}</h4>
      <dl>
        {Object.entries<unknown>(event)
          .filter(([name]) => name !== "type" && name !== "run_id")
          .map(([name, value]) => (
            <Fragment key={name}>
              <dt>
                {isEventField(name) ? `${FIELD_NAMES[name]} ` : null}
                <code>{name}</code>
              </dt>
              <dd style={{ whiteSpace: "pre-wrap" }}>
                <FieldValue name={name} value={value} />
              </dd>
            </Fragment>
          ))}
      </dl>
    </li>
  );
}

/** 필드 값 하나. 실행 식별자 필드의 문자열 값은 그 실행으로 가는 링크이고, 나머지는 글자다(`asText`). */
function FieldValue({ name, value }: { readonly name: string; readonly value: unknown }) {
  if (isEventField(name) && RUN_FIELDS.has(name) && typeof value === "string") {
    const href = runHref(value);
    if (href !== null) {
      return <Link href={href}>{value}</Link>;
    }
  }
  return asText(value);
}

/**
 * 실행 상세의 주소. `encodeURIComponent` 가 그대로 두는 `.` 과 `..` 은 브라우저가 `/runs/` 위로 풀어 다른 화면으로 보내므로
 * 주소가 없다(null). 계약의 식별자 패턴은 둘을 허락하지 않지만, 트레이스는 바깥에서 온 텍스트라 여기서 믿지 않는다.
 */
function runHref(runId: string): string | null {
  return runId === "." || runId === ".." ? null : `/runs/${encodeURIComponent(runId)}`;
}

/**
 * 필드 값의 글자. 문자열은 들어온 그대로다. 그 밖의 JSON 값(수, 참거짓, 인자 같은 객체, 도구 호출 같은 배열)은 두 칸
 * 들여 적는다. 마스킹된 인자는 서버가 이미 `***` 로 적어 보낸다.
 */
export function asText(value: unknown): string {
  return typeof value === "string" ? value : JSON.stringify(value, null, 2);
}
