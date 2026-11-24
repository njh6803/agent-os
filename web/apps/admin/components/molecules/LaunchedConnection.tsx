// 켜 둔 stdio MCP 서버 행의 접속 확인(connection-check 명세 "행에 보이는 것"). stdio 서버는 확인할 때 프로세스를 띄우므로
// 운영자가 '접속 확인' 버튼을 눌러야만 확인한다. 버튼은 응답까지 눌리지 않고, 응답 뒤에는 결과와 시각이 버튼 옆에 선다.
// 결과를 읽어 오는 일은 이 부품이 아니라 쓰는 쪽(pages)이 한다.
import { Button } from "@agent-os/ui";
import type { PressedResult } from "../../types/connection";
import { ConnectionLine } from "./ConnectionLine";

interface LaunchedConnectionProps {
  /** 꺼 둔 플러그인이면 버튼을 누를 수 없고 결과도 보이지 않는다. */
  readonly enabled: boolean;
  /** 응답을 기다리는 중이다. */
  readonly pending: boolean;
  readonly latest: PressedResult | undefined;
  readonly onRun: () => void;
}

export function LaunchedConnection({ enabled, pending, latest, onRun }: LaunchedConnectionProps) {
  const settled = !pending && enabled ? latest : undefined;
  return (
    <div className="flex flex-wrap items-start gap-x-4 gap-y-2">
      <Button variant="secondary" loading={pending} disabled={!enabled} onClick={onRun}>
        접속 확인
      </Button>
      {/* 기다리는 중과 결과가 같은 자리의 한 줄이라 상태 영역이 이어져, 바뀐 결과를 화면 읽기 도구가 알린다. */}
      {pending || settled !== undefined ? (
        <ConnectionLine
          result={settled?.result}
          stamp={
            settled === undefined
              ? undefined
              : {
                  at: settled.at,
                  label: settled.result.state === "failed" ? "누른 시각" : "확인한 시각",
                }
          }
        />
      ) : null}
    </div>
  );
}
