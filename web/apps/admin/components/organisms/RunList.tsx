import {
  Button,
  Card,
  Icon,
  type IconName,
  StatusBadge,
  type StatusBadgeStatus,
} from "@agent-os/ui";
import { type ReactNode, useId } from "react";
import type { RunRow, RunStatus, RunSummary, TracePage, UnreadableTrace } from "../../api/traces";
import { TextLink } from "../atoms/TextLink";
import { EmptyLine } from "../molecules/EmptyLine";
import { ReadSection, type ReadState } from "./ReadSection";

/**
 * 실행 상태의 이름과 거르기의 차례. 이름은 용어집의 말이다. 결말 없음은 "지금 돌고 있다"가 아니라 끝내지 못하고 사라진
 * 실행과 구분되지 않는다는 뜻이라 "실행 중"으로 부르지 않는다(스토리 26, ADR 0021). `Record` 라서 계약에 상태가 늘거나
 * 줄면 여기가 컴파일에서 깨진다.
 */
const STATUS_NAMES = {
  paused: "일시정지",
  finished: "끝남",
  failed: "실패",
  unfinished: "결말 없음",
} as const satisfies Record<RunStatus, string>;

/** 실행 상태가 잇는 배지의 상태(admin-style 명세 "실행 목록"). 배지의 글자는 배지가 쓰는 용어집의 말이다. */
const BADGE = {
  paused: "paused",
  finished: "done",
  failed: "failed",
  unfinished: "no-outcome",
} as const satisfies Record<RunStatus, StatusBadgeStatus>;

/** 거르기의 값. null 은 전부다. */
type Filter = RunStatus | null;

/** 전부와 상태 넷. 상태는 STATUS_NAMES 에 적은 차례다. */
const FILTERS: readonly (readonly [Filter, string])[] = [
  [null, "전부"],
  ...Object.keys(STATUS_NAMES)
    .filter(isRunStatus)
    .map((status) => [status, STATUS_NAMES[status]] as const),
];

function isRunStatus(value: string): value is RunStatus {
  return Object.hasOwn(STATUS_NAMES, value);
}

interface EmptyFiltered {
  readonly icon: IconName;
  readonly line: string;
}

/** 거른 상태에 실행이 없을 때의 한 줄. 아이콘은 그 상태의 배지 아이콘이다. 전부는 탐색의 실행 아이콘이다. */
const EMPTY_ALL: EmptyFiltered = { icon: "list", line: "실행이 없다" };
const EMPTY = {
  paused: { icon: "circle-pause", line: "일시정지한 실행이 없다" },
  finished: { icon: "circle-check", line: "끝난 실행이 없다" },
  failed: { icon: "circle-x", line: "실패한 실행이 없다" },
  unfinished: { icon: "circle-minus", line: "결말 없는 실행이 없다" },
} as const satisfies Record<RunStatus, EmptyFiltered>;

/** 표의 열 머리. 차례가 열의 차례다. 뼈대 행도 같은 머리를 둔다. */
const COLUMNS = ["상태", "실행", "에이전트", "주체", "시작", "마지막"] as const;

/** 뼈대 행의 수(그림 mk-runs-loading). */
const SKELETON_ROWS = 4;

const HEAD_CELL =
  "h-row border-b border-border px-3 text-left text-small font-medium text-text-muted";
const CELL = "h-row border-b border-border px-3";
const TIME = "font-mono text-mono whitespace-nowrap text-text-muted";

interface RunListProps extends ReadState<readonly TracePage[]> {
  /** 고른 거르기. 읽기는 이것으로 거른 쪽들이다. */
  readonly status: Filter;
  readonly onStatusChange: (status: Filter) => void;
  /** 다음 쪽을 더 읽는다. */
  readonly onMore: () => void;
}

/**
 * 실행 목록(`GET /traces`). 행은 서버가 준 순서 그대로다(스토리 23). 화면이 다시 정렬하지 않는다. 상태 넷과 전부로
 * 거르고(스토리 24), 다음 쪽이 있으면 더 본다(스토리 25). 새로 고침과 실패의 표시는 읽기 골격(`ReadSection`)이다.
 * 거르기는 실패 중에도 남는다.
 *
 * 본문 칸이 `split` 이상이면 표, 그 미만이면 실행마다 카드다(admin-style 명세 "실행 목록"). 두 갈래를 함께 그리고
 * 컨테이너 질의로 하나를 숨긴다. 숨은 갈래는 화면 읽기 프로그램에도 없다. 처음 불러오는 동안 넓은 갈래는 표 머리와 뼈대
 * 행이고 좁은 갈래는 읽기 골격의 진행 표시다. 서버가 목록을 한 쪽씩 주므로 개수는 그리지 않는다.
 *
 * 시각은 이 브라우저의 시간대로 적고 그 시간대 이름을 머리 설명에 한 번 밝힌다. 하이드레이션 뒤에만 그려지는 본문이라
 * 서버의 시간대와 갈릴 일이 없다(`AdminScreen`).
 */
export function RunList({ status, onStatusChange, onMore, ...read }: RunListProps) {
  const clock = localClock();
  return (
    <ReadSection
      title="실행"
      description={`트레이스로 남은 실행이다. 새로 시작한 것이 위에 온다. 시각은 이 브라우저의 시간대(${clock.resolvedOptions().timeZone})로 적었다.`}
      {...read}
      loadingLabel="실행 목록을 불러오는 중"
      failureTitle="실행 목록을 읽지 못했다"
      above={<StatusFilter value={status} onChange={onStatusChange} />}
      skeleton={<SkeletonTable />}
    >
      {(pages) => {
        const rows = pages.flatMap((page) => page.runs);
        const nextCursor = pages.at(-1)?.next_cursor ?? null;
        const empty = status === null ? EMPTY_ALL : EMPTY[status];
        return (
          <>
            {rows.length === 0 ? (
              <EmptyLine icon={empty.icon} iconSize="20">
                {empty.line}
              </EmptyLine>
            ) : (
              <>
                <RunTable rows={rows} clock={clock} />
                <RunCards rows={rows} clock={clock} />
              </>
            )}
            {nextCursor === null ? null : (
              <div className="flex justify-center">
                <Button variant="secondary" disabled={read.isValidating} onClick={onMore}>
                  더 보기
                </Button>
              </div>
            )}
          </>
        );
      }}
    </ReadSection>
  );
}

/**
 * 이 브라우저의 시간대로 시각을 적는 형식. 시간대를 주지 않아 `Intl` 이 고른 시간대이고, 그 이름도 이것이 든다. 숫자는
 * 늘 라틴 숫자이고 시는 0~23 이다. `hour12: false` 대신 시 주기를 바로 준다. 옛 사양을 따르는 엔진은 `hour12: false` 에
 * en-US 의 자정을 24 로 적을 수 있다(그런 엔진에서 재지는 않았다. Node 24.19·ICU 78.3 에서 `node -e` 로 손으로 보니
 * 둘 다 00 이었다).
 */
function localClock(): Intl.DateTimeFormat {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
    numberingSystem: "latn",
  });
}

/** 서버의 시각(ISO 8601)을 "YYYY-MM-DD HH:mm:ss"로 적는다. 초 아래는 버린다. */
function formatTime(clock: Intl.DateTimeFormat, at: string): string {
  const parts = clock.formatToParts(new Date(at));
  const part = (type: Intl.DateTimeFormatPartTypes): string =>
    parts.find((found) => found.type === type)?.value ?? "";
  return `${part("year")}-${part("month")}-${part("day")} ${part("hour")}:${part("minute")}:${part("second")}`;
}

/** 실행 하나로 가는 고정폭 링크. 글자는 실행 식별자 그대로다. */
function RunLink({ runId }: { readonly runId: string }) {
  return (
    <TextLink href={`/runs/${encodeURIComponent(runId)}`} font="mono">
      {runId}
    </TextLink>
  );
}

/** 행이 읽을 수 없는 트레이스의 표지인지 가린다. 계약의 두 모양 가운데 `reason` 은 표지에만 있다. */
function isUnreadable(row: RunRow): row is UnreadableTrace {
  return "reason" in row;
}

interface StatusFilterProps {
  readonly value: Filter;
  readonly onChange: (value: Filter) => void;
}

/**
 * 상태 거르기. 라디오 다섯을 알약 모양의 라벨로 감싼다(그림 mk-runs). 넓은 갈래에서는 이름 "상태"가 알약과 한 줄에
 * 서고, 좁은 갈래에서는 그 위에 선다. 떠 있는 `legend` 는 fieldset 의 테두리 자리를 떠나 줄의 첫 항목이 된다.
 */
function StatusFilter({ value, onChange }: StatusFilterProps) {
  const name = useId();
  return (
    <fieldset className="flex flex-wrap items-center gap-2">
      <legend className="mb-2 text-small text-text-muted @split:float-left @split:mr-2 @split:mb-0">
        상태
      </legend>
      {FILTERS.map(([filter, label]) => {
        const checked = value === filter;
        return (
          <label
            key={label}
            className={`flex h-control items-center gap-2 rounded-full border px-3 text-body ${checked ? "border-text bg-bg-selected font-medium" : "border-border-control"}`}
          >
            <input
              type="radio"
              name={name}
              checked={checked}
              className="focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
              onChange={() => {
                onChange(filter);
              }}
            />
            {label}
          </label>
        );
      })}
    </fieldset>
  );
}

function HeadRow() {
  return (
    <tr>
      {COLUMNS.map((column) => (
        <th key={column} scope="col" className={HEAD_CELL}>
          {column}
        </th>
      ))}
    </tr>
  );
}

interface RowsProps {
  readonly rows: readonly RunRow[];
  readonly clock: Intl.DateTimeFormat;
}

/**
 * 넓은 갈래. 칸에 세로줄 없이 행 사이에 옅은 가로줄, 행 높이 `h-row`, 글자 `text-table`, 행에 올리면 `bg-hover` 다(명세
 * "앱 부품"의 표). 열 폭은 내용이 정한다.
 */
function RunTable({ rows, clock }: RowsProps) {
  return (
    <table className="hidden w-full border-collapse text-table @split:table">
      <thead>
        <HeadRow />
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row.run_id} className="hover:bg-bg-hover">
            {isUnreadable(row) ? (
              <UnreadableCells row={row} />
            ) : (
              <SummaryCells row={row} clock={clock} />
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

interface SummaryProps {
  readonly row: RunSummary;
  readonly clock: Intl.DateTimeFormat;
}

function SummaryCells({ row, clock }: SummaryProps) {
  return (
    <>
      <td className={CELL}>
        <StatusBadge status={BADGE[row.status]} />
      </td>
      <td className={CELL}>
        <RunLink runId={row.run_id} />
      </td>
      <td className={`${CELL} wrap-anywhere`}>{row.agent}</td>
      <td className={`${CELL} wrap-anywhere`}>{row.principal}</td>
      <td className={`${CELL} ${TIME}`}>{formatTime(clock, row.started_at)}</td>
      <td className={`${CELL} ${TIME}`}>{formatTime(clock, row.last_at)}</td>
    </>
  );
}

/** 읽을 수 없는 트레이스의 행. 상태 칸에 표지, 실행 칸에 링크, 나머지 넷을 합친 칸에 이유다. 열면 이유를 봉투로 본다. */
function UnreadableCells({ row }: { readonly row: UnreadableTrace }) {
  return (
    <>
      <td className={`${CELL} text-warning`}>
        <Icon name="triangle-alert" size="16" />
      </td>
      <td className={CELL}>
        <RunLink runId={row.run_id} />
      </td>
      <td colSpan={4} className={`${CELL} text-warning wrap-anywhere`}>
        읽을 수 없는 트레이스: {row.reason}
      </td>
    </>
  );
}

/**
 * 좁은 갈래. 실행마다 카드이고 첫 줄에 상태 배지와 시작 시각, 그 아래에 실행 식별자 링크, 에이전트, 주체, 마지막이다.
 * 라벨과 값은 CSS 표로 세워 라벨 폭이 가장 긴 라벨을 따른다. 표는 카드 폭으로 늘리지 않고 내용 폭이다. 늘리면 남는
 * 폭이 칸의 내용 폭에 비례해 나뉘어 라벨 칸의 폭이 카드마다 달라진다. 라벨은 줄을 바꾸지 않아, 값이 카드보다 길면 값이
 * 줄을 바꾼다. 그림의 라벨 폭 px 는 옮기지 않는다.
 */
function RunCards({ rows, clock }: RowsProps) {
  return (
    <ul className="flex flex-col gap-3 @split:hidden">
      {rows.map((row) => (
        <li key={row.run_id}>
          <Card padding="3">
            {isUnreadable(row) ? (
              <UnreadableCard row={row} />
            ) : (
              <SummaryCard row={row} clock={clock} />
            )}
          </Card>
        </li>
      ))}
    </ul>
  );
}

function SummaryCard({ row, clock }: SummaryProps) {
  return (
    <>
      <div className="flex items-center justify-between gap-2">
        <StatusBadge status={BADGE[row.status]} />
        <span className={TIME}>{formatTime(clock, row.started_at)}</span>
      </div>
      <RunLink runId={row.run_id} />
      <dl className="table w-fit border-separate border-spacing-y-1 text-table">
        <Field term="에이전트">{row.agent}</Field>
        <Field term="주체">{row.principal}</Field>
        <Field term="마지막">
          <span className="font-mono text-mono">{formatTime(clock, row.last_at)}</span>
        </Field>
      </dl>
    </>
  );
}

function Field({ term, children }: { readonly term: string; readonly children: ReactNode }) {
  return (
    <div className="table-row">
      <dt className="table-cell pr-2 whitespace-nowrap text-text-muted">{term}</dt>
      <dd className="table-cell wrap-anywhere">{children}</dd>
    </div>
  );
}

function UnreadableCard({ row }: { readonly row: UnreadableTrace }) {
  return (
    <>
      <p className="flex items-start gap-2 text-table text-warning">
        <Icon name="triangle-alert" size="16" />
        <span className="min-w-0 wrap-anywhere">읽을 수 없는 트레이스: {row.reason}</span>
      </p>
      <RunLink runId={row.run_id} />
    </>
  );
}

/**
 * 처음 불러오는 동안의 넓은 갈래(그림 mk-runs-loading). 표 머리와, 진짜 행과 같은 높이의 막대 행이다. 막대는 움직이지
 * 않는다(`.claude/rules/web-design.md` 의 뼈대 줄). 막대 길이는 그림의 px 를 옮기지 않고 칸 폭의 몫이다. 화면 읽기
 * 프로그램에서는 숨고, 불러오는 중이라는 말은 읽기 골격의 상태 영역이 한다.
 */
function SkeletonTable() {
  return (
    <table aria-hidden="true" className="w-full border-collapse">
      <thead>
        <HeadRow />
      </thead>
      <tbody>
        {Array.from({ length: SKELETON_ROWS }, (_, index) => (
          <tr key={index}>
            {COLUMNS.map((column) => (
              <td key={column} className={CELL}>
                <span className={`block h-3 rounded-s bg-bg-selected ${barWidth(column, index)}`} />
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

/** 막대의 폭. 에이전트와 주체는 행마다 길이를 엇갈려 진짜 목록처럼 보이게 한다. */
function barWidth(column: (typeof COLUMNS)[number], index: number): string {
  const odd = index % 2 === 1;
  switch (column) {
    case "상태":
      return "w-1/2";
    case "에이전트":
      return odd ? "w-1/3" : "w-2/3";
    case "주체":
      return odd ? "w-3/4" : "w-1/2";
    case "실행":
    case "시작":
    case "마지막":
      return "w-full";
  }
}
