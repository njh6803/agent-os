// 플러그인 행의 접속 확인 한 줄(connection-check 명세 "행에 보이는 것"). 상태는 색만으로 보이지 않고 아이콘 모양과 글자가
// 함께 있다. 디자인 시스템의 `StatusBadge` 는 실행 상태 넷 전용이라 쓰지 않고, 아이콘과 글자 색 토큰으로 그린다.
//
// 글자가 든 상태 영역(`role="status"`)은 상태가 바뀔 때만 화면 읽기 프로그램에 알린다. 30초마다 같은 결과가 다시 와도 이
// 부품은 같은 값으로 다시 그려질 뿐이라 노드가 바뀌지 않고, 읽어 주지 않는다.
import { Icon, type IconName } from "@agent-os/ui";
import type { ConnectionResult } from "../../types/connection";

interface Look {
  readonly icon: IconName;
  readonly label: string;
  readonly tone: string;
}

/** 결과가 없으면(응답을 기다리는 중) 확인하는 중이다. `Record` 라서 결과의 상태가 늘면 여기가 컴파일에서 깨진다. */
const LOOKS = {
  checking: { icon: "ellipsis", label: "확인하는 중", tone: "text-text-muted" },
  reached: { icon: "circle-check", label: "붙음", tone: "text-success" },
  unreached: { icon: "circle-x", label: "붙지 못함", tone: "text-danger" },
  failed: { icon: "triangle-alert", label: "확인하지 못함", tone: "text-warning" },
} as const satisfies Record<ConnectionResult["state"] | "checking", Look>;

/** 결과 옆의 시각. 눌러서 한 확인이 스스로 새로워지지 않아서 함께 보인다. */
export interface ConnectionStamp {
  readonly at: Date;
  /** 성공과 붙지 못함은 확인한 시각이고, 요청이 실패했으면 누른 시각이다. */
  readonly label: "확인한 시각" | "누른 시각";
}

interface ConnectionLineProps {
  /** 없으면 응답을 기다리는 중이다. */
  readonly result: ConnectionResult | undefined;
  readonly stamp?: ConnectionStamp;
}

const CLOCK = new Intl.DateTimeFormat("ko-KR", {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hourCycle: "h23",
});

function detailOf(result: ConnectionResult | undefined): string | null {
  switch (result?.state) {
    case "unreached":
      return result.reason;
    case "failed":
      return result.message;
    case "reached":
    case undefined:
      return null;
  }
}

export function ConnectionLine({ result, stamp }: ConnectionLineProps) {
  const look = LOOKS[result?.state ?? "checking"];
  const detail = detailOf(result);
  return (
    <div className="flex min-w-0 flex-wrap items-start gap-x-4 gap-y-1 text-small">
      <p role="status" className="flex min-w-0 items-start gap-2">
        <span className={`flex shrink-0 items-center gap-1 font-medium ${look.tone}`}>
          <Icon name={look.icon} size="14" />
          <span>{look.label}</span>
        </span>
        {detail === null ? null : (
          <span className="min-w-0 wrap-anywhere text-text-muted">{detail}</span>
        )}
      </p>
      {stamp === undefined ? null : (
        <p className="text-text-muted">
          <span>{stamp.label}</span>{" "}
          <time dateTime={stamp.at.toISOString()}>{CLOCK.format(stamp.at)}</time>
        </p>
      )}
    </div>
  );
}
