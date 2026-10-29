import { Icon, Switch } from "@agent-os/ui";
import { useId, useState } from "react";
import { describeFailure, RequestFailure } from "../../api/failure";
import type { PluginKind, PluginRow } from "../../api/plugins";
import { TextLink } from "../atoms/TextLink";
import { EmptyLine } from "../molecules/EmptyLine";
import { FailureAlert } from "../molecules/FailureAlert";
import type { FailureNoticeProps } from "../molecules/FailureNotice";
import { ReadSection, type ReadState } from "./ReadSection";

/**
 * 종류의 이름과 차례(적은 차례대로 묶는다). 이름은 용어집의 말이다. `Record` 라서 계약에 종류가 늘거나 줄면 여기가
 * 컴파일에서 깨진다. 빠진 종류의 행이 목록에서 조용히 사라지지 않는다. 플러그인 하나의 설명도 이 이름을 쓴다.
 */
export const KIND_NAMES = {
  agent: "에이전트",
  mcp: "MCP",
  skill: "스킬",
  model: "모델",
} as const satisfies Record<PluginKind, string>;

/** 로더가 아직 없는 종류. 끄고 켜도 런타임이 달라지지 않는다(스토리 21). */
const WITHOUT_LOADER: ReadonlySet<PluginKind> = new Set<PluginKind>(["skill", "model"]);

/** 스위치의 실패 하나. 누른 행이 다시 읽은 목록에서 빠져도 보이도록 목록이 든다. 제목이 실패한 플러그인을 든다. */
interface SwitchFailure extends FailureNoticeProps {
  readonly title: string;
}

/** 켜고 끄기의 실패 알림이 메시지 다음에 더하는 글(admin-style 명세의 실패 알림 표). */
const SWITCH_FAILURE_NOTE = "스위치는 다시 읽은 값이다.";

/**
 * 플러그인 하나를 켜거나 끈다. 목록을 다시 읽은 뒤에 돌아오고, 실패는 `RequestFailure` 로 던진다(다시 읽기는 실패해도
 * 한다).
 */
type SetEnabled = (
  kind: PluginKind,
  name: string,
  change: { readonly enabled: boolean },
) => Promise<void>;

interface PluginListProps extends ReadState<readonly PluginRow[]> {
  readonly onSetEnabled: SetEnabled;
}

/**
 * 플러그인 목록(`GET /plugins`, 그림 mk-plugins, mk-plugins-m). 머리는 "플러그인 <전체 개수>"이고, 종류별로 묶어
 * 종류마다 "<종류 이름> <개수>" 머리 아래 행을 둔다. 개수는 읽은 목록이 보일 때만 붙는다. 새로 고침과 실패의 표시는
 * 읽기 골격(`ReadSection`)이다. 다시 읽다 실패하면 옛 행을 지운다. 운영자 파일이 깨졌을 때 무엇이 꺼져 있는지 모르는
 * 채 옛 목록을 믿으면 안 되기 때문이다(스토리 16).
 *
 * 켜고 끄기의 실패는 행이 아니라 화면 머리 아래에 보인다. 그 사이 플러그인이 사라져 404 이면 다시 읽은 목록에서 그
 * 행이 빠지는데, 실패를 행이 들면 메시지도 함께 사라진다(스토리 19). 다음 켜고 끄기가 시작될 때 걷힌다.
 */
export function PluginList(props: PluginListProps) {
  const [switchFailure, setSwitchFailure] = useState<SwitchFailure | null>(null);
  return (
    <PluginListView {...props} switchFailure={switchFailure} onSwitchFailure={setSwitchFailure} />
  );
}

interface PluginListViewProps extends PluginListProps {
  /** 머리 아래에 보일 켜고 끄기의 실패. 없으면 null 이다. */
  readonly switchFailure: SwitchFailure | null;
  readonly onSwitchFailure: (failure: SwitchFailure | null) => void;
}

/**
 * 플러그인 목록을 그린다. 켜고 끄기의 실패를 상태로 들지 않고 받는다. 화면은 `PluginList` 가 그 상태를 들어 넘기고,
 * 스토리는 실패한 모습을 누르지 않고 그린다.
 */
export function PluginListView({
  onSetEnabled,
  switchFailure,
  onSwitchFailure,
  ...read
}: PluginListViewProps) {
  // 실패 중에는 읽은 목록을 보이지 않으므로 개수도 붙이지 않는다.
  const shownRows = read.error === undefined ? read.data : undefined;

  return (
    <div className="max-w-content">
      <ReadSection
        title={
          shownRows === undefined ? (
            "플러그인"
          ) : (
            <Counted label="플러그인" count={shownRows.length} />
          )
        }
        description="종류마다 등록된 플러그인을 켜고 끈다."
        {...read}
        loadingLabel="플러그인 목록을 불러오는 중"
        failureTitle="플러그인 목록을 읽지 못했다"
        above={
          switchFailure === null ? null : (
            <FailureAlert {...switchFailure} note={SWITCH_FAILURE_NOTE} />
          )
        }
      >
        {(rows) => (
          <div className="flex flex-col gap-8">
            {Object.entries(KIND_NAMES).map(([kind, label]) => (
              <KindGroup
                key={kind}
                label={label}
                rows={rows.filter((row) => row.kind === kind)}
                onSetEnabled={onSetEnabled}
                onSwitchFailure={onSwitchFailure}
              />
            ))}
          </div>
        )}
      </ReadSection>
    </div>
  );
}

/** 이름과 그 옆의 흐린 개수. 제목 요소 안에 두어 제목의 이름이 "<이름> <개수>"가 된다. */
function Counted({ label, count }: { readonly label: string; readonly count: number }) {
  return (
    <>
      {label} <span className="font-regular text-text-muted">{count}</span>
    </>
  );
}

interface KindGroupProps {
  readonly label: string;
  readonly rows: PluginRow[];
  readonly onSetEnabled: SetEnabled;
  readonly onSwitchFailure: (failure: SwitchFailure | null) => void;
}

function KindGroup({ label, rows, onSetEnabled, onSwitchFailure }: KindGroupProps) {
  const headingId = useId();
  return (
    <section aria-labelledby={headingId} className="flex flex-col gap-2">
      <h2 id={headingId} className="text-body font-semibold">
        <Counted label={label} count={rows.length} />
      </h2>
      {rows.length === 0 ? (
        <div className="flex min-h-row items-center border-y border-border wide:px-3">
          <EmptyLine icon="circle-minus" iconSize="16">
            등록된 것이 없다
          </EmptyLine>
        </div>
      ) : (
        <ul className="border-t border-border">
          {rows.map((row) => (
            <Row
              key={row.name}
              row={row}
              onSetEnabled={onSetEnabled}
              onSwitchFailure={onSwitchFailure}
            />
          ))}
        </ul>
      )}
    </section>
  );
}

interface RowProps {
  readonly row: PluginRow;
  readonly onSetEnabled: SetEnabled;
  /** 켜고 끄기의 실패를 목록에 알린다. 누르기 시작하면 앞의 실패를 걷는다(null). */
  readonly onSwitchFailure: (failure: SwitchFailure | null) => void;
}

/**
 * 행 하나. 패키지 `Switch` 의 보이는 이름이 플러그인 이름이라 이름이나 스위치를 누르면 그 자리에서 켜고 끈다. 플러그인
 * 하나로 가는 링크는 같은 줄 끝의 "매니페스트"다. 표지 행도 스위치와 링크를 둔다. 깨진 것을 끈 채로 고치고 싶을 수
 * 있고(스토리 20), 열면 그 경로와 이유를 본다(스토리 15).
 *
 * 스위치는 목록이 읽은 켜짐을 그대로 보인다. 누르면 요청을 보내고 목록을 다시 읽을 때까지 막는다. 화면이 값을 먼저
 * 뒤집어 두지 않고(스토리 18), 응답 전의 두 번째 누름이 요청을 더 보내지 않는다(스토리 22).
 */
function Row({ row, onSetEnabled, onSwitchFailure }: RowProps) {
  const [pending, setPending] = useState(false);

  async function setOpposite(): Promise<void> {
    setPending(true);
    onSwitchFailure(null);
    try {
      await onSetEnabled(row.kind, row.name, { enabled: !row.enabled });
    } catch (error: unknown) {
      // 요청 함수는 실패를 모두 RequestFailure 로 던진다. 그 밖의 예외는 이 코드의 결함이라 덮지 않고 다시 던진다.
      if (!(error instanceof RequestFailure)) {
        throw error;
      }
      onSwitchFailure({
        title: `켜고 끄지 못했다: ${row.kind}/${row.name}`,
        ...describeFailure(error),
      });
    } finally {
      setPending(false);
    }
  }

  return (
    <li className="flex min-h-row flex-col justify-center gap-1 border-b border-border py-2 wide:px-3">
      <div className="flex items-center gap-3 wide:gap-4">
        <div className="min-w-0 flex-1">
          <Switch
            label={row.name}
            checked={row.enabled}
            disabled={pending}
            onChange={() => {
              void setOpposite();
            }}
          />
        </div>
        {/* 표지의 이름은 패턴 밖일 수 있어 조각으로 적는다. */}
        <TextLink href={`/plugins/${row.kind}/${encodeURIComponent(row.name)}`}>
          매니페스트
        </TextLink>
      </div>
      {"reason" in row ? (
        <p className="flex items-start gap-2 text-small text-warning">
          <Icon name="triangle-alert" size="14" />
          <span className="min-w-0 wrap-anywhere">읽을 수 없는 매니페스트: {row.reason}</span>
        </p>
      ) : null}
      {WITHOUT_LOADER.has(row.kind) ? (
        <p className="flex items-start gap-2 text-small text-text-muted">
          <Icon name="info" size="14" />
          <span>로더가 생기기 전에는 효과가 없다</span>
        </p>
      ) : null}
    </li>
  );
}
