// 승인 묻기의 꺼짐 미리 알림이 쓰는 판정(web-admin 티켓 08, admin-login 티켓 11). 순수한 함수라 화면 부품과 시험이 함께 쓴다.

import type { PluginRow } from "../../api/plugins";

/**
 * 이 실행을 재개할 수 없게 꺼진 플러그인(ADR 0017, 0019). 실행의 에이전트와 그 매니페스트의 `mcp`, `model`,
 * `skills` 를 목록의 행과 잇는다. 목록이 없거나(아직 읽는 중이거나 읽다 실패했다), 에이전트를 모르거나, 에이전트 행이
 * 표지이거나 없으면 미리 알 수 없어 비어 있다. 그때는 누르면 서버의 봉투가 말한다. 서버의 꺼짐 순서(에이전트 → mcp →
 * 모델 → 스킬)와 같은 차례로 쌓는다.
 *
 * `model` 은 에이전트가 적었을 때만 본다. 적지 않은 에이전트는 기본 모델을 쓰는데, 관리 API 가 기본 모델의 이름을
 * 내지 않아 화면이 모른다. 그때도 누르면 서버의 봉투가 말한다. 모델 행이 표지(읽지 못한 매니페스트)이면 꺼짐으로 세지
 * 않는다. 읽지 못한 모델은 켜져 있어도 실행이 막히므로 그 까닭을 꺼짐이라 말하면 틀리다.
 *
 * `skills` 는 매니페스트에 적힌 순서대로 보고 세는 꼴은 모델의 것이다(ADR 0041의 "명세 검토가 쓰지 않는 칸의 뜻과
 * 칸의 패턴, 결정 칸의 꼴, 티켓의 순서를 바로잡았다" 이력). 표지 행(읽지 못한 매니페스트)은 꺼짐으로 세지 않는다.
 * 매니페스트를 읽지 못한 스킬은 켜져 있어도 실행이 막히므로 그 까닭을 꺼짐이라 말하면 틀리다. mcp 갈래는 표지를
 * 거르지 않지만 스킬은 거른다.
 *
 * 한계 하나: 목록은 스킬 문서(`SKILL.md`)를 읽지 않아 문서가 없거나 깨진 스킬도 보통 행이다. 그런 스킬이 꺼져 있으면
 * 화면은 꺼짐을 알리지만 서버는 깨짐을 꺼짐보다 먼저 판정해 읽을 수 없다고 답한다. 다시 켜도 막히는 그 경우는
 * 누른 뒤의 봉투가 말한다.
 */
export function disabledFor(
  agent: string | null,
  rows: readonly PluginRow[] | undefined,
): string[] {
  if (agent === null || rows === undefined) {
    return [];
  }
  const row = rows.find(({ kind, name }) => kind === "agent" && name === agent);
  if (row === undefined || !("manifest" in row)) {
    return [];
  }
  const found = row.enabled ? [] : [`에이전트 ${row.name}`];
  for (const mcp of row.manifest.mcp) {
    if (rows.some(({ kind, name, enabled }) => kind === "mcp" && name === mcp && !enabled)) {
      found.push(`MCP ${mcp}`);
    }
  }
  const { model } = row.manifest;
  if (
    model !== null &&
    rows.some(
      (other) =>
        other.kind === "model" && other.name === model && "manifest" in other && !other.enabled,
    )
  ) {
    found.push(`모델 ${model}`);
  }
  for (const skill of row.manifest.skills) {
    if (
      rows.some(
        (other) =>
          other.kind === "skill" && other.name === skill && "manifest" in other && !other.enabled,
      )
    ) {
      found.push(`스킬 ${skill}`);
    }
  }
  return found;
}
