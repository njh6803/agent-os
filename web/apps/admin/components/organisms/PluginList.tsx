import { useId } from "react";
import { describeFailure } from "../../api/failure";
import type { PluginRow } from "../../api/plugins";
import { usePlugins } from "../../hooks/queries/plugins";
import { FailureNotice } from "../molecules/FailureNotice";

type PluginKind = PluginRow["kind"];

/** 종류의 차례와 이름. 이름은 용어집의 말이다. */
const KINDS = [
  ["agent", "에이전트"],
  ["mcp", "MCP"],
  ["skill", "스킬"],
  ["model", "모델"],
] as const satisfies readonly (readonly [PluginKind, string])[];

/** 로더가 아직 없는 종류. 끄고 켜도 런타임이 달라지지 않는다(스토리 21). */
const WITHOUT_LOADER: ReadonlySet<PluginKind> = new Set<PluginKind>(["skill", "model"]);

/**
 * 플러그인 목록(`GET /plugins`). 종류별로 묶고 행마다 켜짐을 보인다.
 *
 * 실패하면 목록 대신 실패를 보인다. 이미 보인 행이 있어도 지운다. 운영자 파일이 깨졌을 때 무엇이 꺼져 있는지 모르는
 * 채 옛 목록을 믿으면 안 되기 때문이다(스토리 16). 처음 불러오는 중은 자리표시, 이미 보인 것을 다시 확인하는 중은
 * 작은 표시이고 보인 것을 지우지 않는다(스토리 36).
 */
export function PluginList() {
  const { data, error, isValidating, mutate } = usePlugins();
  const headingId = useId();
  const shown = data !== undefined || error !== undefined;

  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId}>플러그인</h2>
      <button
        type="button"
        onClick={() => {
          void mutate();
        }}
      >
        새로 고침
      </button>
      {shown && isValidating ? <span role="status">다시 확인하는 중</span> : null}
      {error !== undefined ? (
        <FailureNotice {...describeFailure(error)} />
      ) : data === undefined ? (
        <p role="status">플러그인 목록을 불러오는 중이다</p>
      ) : (
        KINDS.map(([kind, label]) => (
          <KindGroup key={kind} label={label} rows={data.filter((row) => row.kind === kind)} />
        ))
      )}
    </section>
  );
}

function KindGroup({ label, rows }: { readonly label: string; readonly rows: PluginRow[] }) {
  const headingId = useId();
  return (
    <section aria-labelledby={headingId}>
      <h3 id={headingId}>{label}</h3>
      {rows.length === 0 ? (
        <p>등록된 것이 없다</p>
      ) : (
        <ul>
          {rows.map((row) => (
            <Row key={row.name} row={row} />
          ))}
        </ul>
      )}
    </section>
  );
}

function Row({ row }: { readonly row: PluginRow }) {
  return (
    <li>
      <span>{row.name}</span> <span>{row.enabled ? "켜짐" : "꺼짐"}</span>
      {"reason" in row ? <p>읽을 수 없는 매니페스트: {row.reason}</p> : null}
      {WITHOUT_LOADER.has(row.kind) ? <p>로더가 생기기 전에는 효과가 없다</p> : null}
    </li>
  );
}
