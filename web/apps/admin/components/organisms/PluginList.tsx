import Link from "next/link";
import { useId, useState } from "react";
import { describeFailure, RequestFailure } from "../../api/failure";
import type { PluginKind, PluginRow } from "../../api/plugins";
import { usePlugins, useSetPluginEnabled } from "../../hooks/queries/plugins";
import { FailureNotice, type FailureNoticeProps } from "../molecules/FailureNotice";

/**
 * 종류의 이름과 차례(적은 차례대로 묶는다). 이름은 용어집의 말이다. `Record` 라서 계약에 종류가 늘거나 줄면 여기가
 * 컴파일에서 깨진다. 빠진 종류의 행이 목록에서 조용히 사라지지 않는다.
 */
const KIND_NAMES = {
  agent: "에이전트",
  mcp: "MCP",
  skill: "스킬",
  model: "모델",
} as const satisfies Record<PluginKind, string>;

/** 로더가 아직 없는 종류. 끄고 켜도 런타임이 달라지지 않는다(스토리 21). */
const WITHOUT_LOADER: ReadonlySet<PluginKind> = new Set<PluginKind>(["skill", "model"]);

/** 스위치의 실패 하나. 누른 행이 다시 읽은 목록에서 빠져도 보이도록 목록이 든다. 모양은 보이는 자리의 것이다. */
type SwitchFailure = FailureNoticeProps;

/**
 * 플러그인 목록(`GET /plugins`). 종류별로 묶고 행마다 켜짐과 스위치를 보인다.
 *
 * 실패하면 목록 대신 실패를 보인다. 이미 보인 행이 있어도 지운다. 운영자 파일이 깨졌을 때 무엇이 꺼져 있는지 모르는
 * 채 옛 목록을 믿으면 안 되기 때문이다(스토리 16). 처음 불러오는 중은 자리표시, 이미 보인 것을 다시 확인하는 중은
 * 작은 표시이고 보인 것을 지우지 않는다(스토리 36).
 *
 * 켜고 끄기의 실패는 행이 아니라 목록의 머리에 보인다. 그 사이 플러그인이 사라져 404 이면 다시 읽은 목록에서 그 행이
 * 빠지는데, 실패를 행이 들면 메시지도 함께 사라진다(스토리 19). 다음 켜고 끄기가 시작될 때 걷힌다.
 */
export function PluginList() {
  const { data, error, isValidating, mutate } = usePlugins();
  const [switchFailure, setSwitchFailure] = useState<SwitchFailure | null>(null);
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
      {switchFailure === null ? null : <FailureNotice {...switchFailure} />}
      {error !== undefined ? (
        <FailureNotice {...describeFailure(error)} />
      ) : data === undefined ? (
        <p role="status">플러그인 목록을 불러오는 중이다</p>
      ) : (
        Object.entries(KIND_NAMES).map(([kind, label]) => (
          <KindGroup
            key={kind}
            label={label}
            rows={data.filter((row) => row.kind === kind)}
            onSwitchFailure={setSwitchFailure}
          />
        ))
      )}
    </section>
  );
}

interface KindGroupProps {
  readonly label: string;
  readonly rows: PluginRow[];
  readonly onSwitchFailure: (failure: SwitchFailure | null) => void;
}

function KindGroup({ label, rows, onSwitchFailure }: KindGroupProps) {
  const headingId = useId();
  return (
    <section aria-labelledby={headingId}>
      <h3 id={headingId}>{label}</h3>
      {rows.length === 0 ? (
        <p>등록된 것이 없다</p>
      ) : (
        <ul>
          {rows.map((row) => (
            <Row key={row.name} row={row} onSwitchFailure={onSwitchFailure} />
          ))}
        </ul>
      )}
    </section>
  );
}

interface RowProps {
  readonly row: PluginRow;
  /** 켜고 끄기의 실패를 목록에 알린다. 누르기 시작하면 앞의 실패를 걷는다(null). */
  readonly onSwitchFailure: (failure: SwitchFailure | null) => void;
}

/**
 * 행 하나. 표지 행도 스위치를 둔다. 깨진 것을 끈 채로 고치고 싶을 수 있다(스토리 20).
 *
 * 스위치는 목록이 읽은 켜짐을 그대로 보인다. 누르면 요청을 보내고 목록을 다시 읽을 때까지 막는다. 화면이 값을 먼저
 * 뒤집어 두지 않고(스토리 18), 응답 전의 두 번째 누름이 요청을 더 보내지 않는다(스토리 22).
 */
function Row({ row, onSwitchFailure }: RowProps) {
  const setEnabled = useSetPluginEnabled();
  const [pending, setPending] = useState(false);

  async function setOpposite(): Promise<void> {
    setPending(true);
    onSwitchFailure(null);
    try {
      await setEnabled(row.kind, row.name, !row.enabled);
    } catch (error: unknown) {
      // 요청 함수는 실패를 모두 RequestFailure 로 던진다. 그 밖의 예외는 이 코드의 결함이라 덮지 않고 다시 던진다.
      if (!(error instanceof RequestFailure)) {
        throw error;
      }
      const { message, requestId } = describeFailure(error);
      onSwitchFailure({
        message: `켜고 끄지 못했다: ${row.kind}/${row.name}\n${message}`,
        requestId,
      });
    } finally {
      setPending(false);
    }
  }

  return (
    <li>
      {/* 표지 행도 연다. 열면 그 경로와 이유를 본다(스토리 15). 표지의 이름은 패턴 밖일 수 있어 조각으로 적는다. */}
      <Link href={`/plugins/${row.kind}/${encodeURIComponent(row.name)}`}>{row.name}</Link>{" "}
      <input
        type="checkbox"
        role="switch"
        aria-label={`${row.name} 켜고 끄기`}
        checked={row.enabled}
        disabled={pending}
        onChange={() => {
          void setOpposite();
        }}
      />{" "}
      <span>{row.enabled ? "켜짐" : "꺼짐"}</span>
      {"reason" in row ? <p>읽을 수 없는 매니페스트: {row.reason}</p> : null}
      {WITHOUT_LOADER.has(row.kind) ? <p>로더가 생기기 전에는 효과가 없다</p> : null}
    </li>
  );
}
