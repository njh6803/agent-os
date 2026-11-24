// 플러그인 목록의 행마다 서는 접속 확인(connection-check 티켓 04). 행마다 서버에서 읽어야 하는 값이라 organisms 가
// 읽지 못한다. 이 부품이 pages 에서 읽고, 목록(`PluginList`)의 슬롯으로 넘겨져 행 안에 선다.
//
// 어느 행에 무엇이 서는지는 명세 "행에 보이는 것"의 표다. 켜 둔 원격 MCP 서버와 켜 둔 모델은 스스로 확인하고, 켜 둔
// stdio MCP 서버는 버튼을 눌러야 확인하며, 꺼 둔 행은 결과를 보이지 않는다. 에이전트와 스킬에는 확인이 없다. 매니페스트를
// 읽지 못한 표지 행에는 목록이 이 부품을 부르지 않는다.

import type { CheckableKind } from "../../api/connection";
import type { PluginRow } from "../../api/plugins";
import { useAutoConnection, useManualConnection } from "../../hooks/queries/connection";
import { ConnectionLine } from "../molecules/ConnectionLine";
import { LaunchedConnection } from "../molecules/LaunchedConnection";

export function RowConnection({ row }: { readonly row: PluginRow }) {
  if ("reason" in row) {
    return null;
  }
  if (row.kind === "model") {
    return <AutoConnection kind="model" name={row.name} enabled={row.enabled} />;
  }
  if (row.kind === "mcp") {
    const transport = row.manifest.server?.transport;
    if (transport === "http") {
      return <AutoConnection kind="mcp" name={row.name} enabled={row.enabled} />;
    }
    if (transport === "stdio") {
      return <PressedConnection name={row.name} enabled={row.enabled} />;
    }
  }
  return null;
}

interface AutoConnectionProps {
  readonly kind: CheckableKind;
  readonly name: string;
  readonly enabled: boolean;
}

/** 스스로 하는 확인의 결과. 꺼 둔 행은 확인을 멈추고 아무것도 보이지 않는다. */
function AutoConnection({ kind, name, enabled }: AutoConnectionProps) {
  const result = useAutoConnection({ kind, name, enabled });
  return enabled ? <ConnectionLine result={result} /> : null;
}

/** 켜 둔 stdio MCP 서버. 서버를 띄우므로 운영자가 버튼을 눌러야만 확인한다. 응답까지 버튼은 눌리지 않는다. */
function PressedConnection({
  name,
  enabled,
}: {
  readonly name: string;
  readonly enabled: boolean;
}) {
  const { pending, latest, run } = useManualConnection({ kind: "mcp", name, enabled });
  return <LaunchedConnection enabled={enabled} pending={pending} latest={latest} onRun={run} />;
}
