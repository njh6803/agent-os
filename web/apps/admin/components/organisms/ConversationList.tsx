import { Button, Card, Icon, type IconName, StatusBadge } from "@agent-os/ui";
import type { ReactNode } from "react";
import type {
  Conversation,
  ConversationPage,
  ConversationRow,
  UnreadableTrace,
} from "../../api/conversations";
import type { RunStatus } from "../../api/traces";
import { TextLink } from "../atoms/TextLink";
import { EmptyLine } from "../molecules/EmptyLine";
import { formatTime, localClock } from "../atoms/clock";
import { isEndUserPrincipal } from "../molecules/principal";
import { ReadSection, type ReadState } from "./ReadSection";
import { BADGE, StatusFilter, type StatusFilterValue } from "./StatusFilter";

interface EmptyFiltered {
  readonly icon: IconName;
  readonly line: string;
}

/** 거른 상태에 대화가 없을 때의 한 줄. 아이콘은 그 상태의 배지 아이콘이다. 전부는 탐색의 대화 아이콘이다. */
const EMPTY_ALL: EmptyFiltered = { icon: "message-square", line: "대화가 없다" };
const EMPTY = {
  paused: { icon: "circle-pause", line: "일시정지한 대화가 없다" },
  finished: { icon: "circle-check", line: "끝난 대화가 없다" },
  failed: { icon: "circle-x", line: "실패한 대화가 없다" },
  unfinished: { icon: "circle-minus", line: "결말 없는 대화가 없다" },
} as const satisfies Record<RunStatus, EmptyFiltered>;

/** 표의 열 머리. 차례가 열의 차례다. 뼈대 행도 같은 머리를 둔다. */
const COLUMNS = ["첫 요청", "요청한 계정", "에이전트", "상태", "실행", "마지막"] as const;

/** 뼈대 행의 수. */
const SKELETON_ROWS = 4;

const HEAD_CELL =
  "h-row border-b border-border px-3 text-left text-small font-medium text-text-muted";
const CELL = "h-row border-b border-border px-3";
const TIME = "font-mono text-mono whitespace-nowrap text-text-muted";

interface ConversationListProps extends ReadState<readonly ConversationPage[]> {
  /** 고른 거르기. 읽기는 이것으로 거른 쪽들이다. */
  readonly status: StatusFilterValue;
  readonly onStatusChange: (status: StatusFilterValue) => void;
  /** 다음 쪽을 더 읽는다. */
  readonly onMore: () => void;
}

/**
 * 대화 목록(`GET /conversations`, admin-login 명세 "대화 목록"). 줄은 서버가 준 순서 그대로이고 화면이 다시 정렬하지
 * 않는다. 상태 넷과 전부로 거르고 다음 쪽이 있으면 더 본다. 저절로 다시 읽지 않는다. 새로 고침과 실패의 표시는 읽기
 * 골격(`ReadSection`)이다. 거르기는 실패 중에도 남는다.
 *
 * 본문 칸이 `split` 이상이면 표, 그 미만이면 대화마다 카드다. 명세는 경계를 폭 768px 로 적었으나(계정 목록과 탐색의 위
 * 막대와 같다), 이 앱의 목록 화면은 본문 칸의 폭으로 갈라 옆 탐색이 서는 넓은 창에서도 표가 좁은 칸에 구겨지지 않게 한다
 * (실행 목록과 같다). 두 갈래를 함께 그리고 컨테이너 질의로 하나를 숨긴다.
 *
 * 줄을 누르는 자리는 첫 요청의 링크다. 줄 전체를 누르는 곳으로 만들면 화면 읽기 프로그램에 링크가 둘로 읽히거나
 * 포커스가 줄 안에서 갈린다. 시각은 이 브라우저의 시간대다.
 */
export function ConversationList({
  status,
  onStatusChange,
  onMore,
  ...read
}: ConversationListProps) {
  const clock = localClock();
  return (
    <ReadSection
      title="대화"
      description={`이어 가기로 이어진 실행들이다. 끝 실행이 최근인 대화가 위에 온다. 시각은 이 브라우저의 시간대(${clock.resolvedOptions().timeZone})로 적었다.`}
      {...read}
      loadingLabel="대화 목록을 불러오는 중"
      failureTitle="대화 목록을 읽지 못했다"
      above={<StatusFilter value={status} onChange={onStatusChange} />}
      skeleton={<SkeletonTable />}
    >
      {(pages) => {
        const rows = pages.flatMap((page) => page.conversations);
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
                <ConversationTable rows={rows} clock={clock} />
                <ConversationCards rows={rows} clock={clock} />
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

/** 대화 하나로 가는 주소. 끝 실행의 식별자다. */
function chatHref(runId: string): string {
  return `/chat/${encodeURIComponent(runId)}`;
}

/** 줄이 읽을 수 없는 트레이스의 표지인지 가린다. 계약의 두 모양 가운데 `reason` 은 표지에만 있다. */
function isUnreadable(row: ConversationRow): row is UnreadableTrace {
  return "reason" in row;
}

/** 줄의 키. 대화는 끝 실행, 표지는 그 트레이스의 식별자다. */
function keyOf(row: ConversationRow): string {
  return isUnreadable(row) ? row.run_id : row.last_run;
}

/**
 * 요청한 계정 칸의 글. 계정이 있으면 그 이름이다. 비면 주체를 흐린 글자로 보이고, 최종 사용자의 대화는 그 앞에 "최종
 * 사용자"를 붙인다. 명령줄 실행은 공유 토큰으로 시작한 실행과 같아 가를 수 없어 "명령줄"을 붙이지 않는다(명세 "대화 목록").
 */
function Requester({ row }: { readonly row: Conversation }) {
  if (row.requesting_account !== null) {
    return <span className="wrap-anywhere">{row.requesting_account}</span>;
  }
  return (
    <span className="text-text-muted wrap-anywhere">
      {isEndUserPrincipal(row.principal) ? `최종 사용자 ${row.principal}` : row.principal}
    </span>
  );
}

/** 첫 요청 옆의 알림. 첫 실행이 대화의 처음이 아니면 앞부분을 읽지 못한 것이다. */
function Incomplete() {
  return (
    <span className="inline-flex items-center gap-1 text-small whitespace-nowrap text-warning">
      <Icon name="triangle-alert" size="14" />
      앞부분을 읽지 못함
    </span>
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
  readonly rows: readonly ConversationRow[];
  readonly clock: Intl.DateTimeFormat;
}

/** 넓은 갈래. 칸에 세로줄 없이 행 사이에 옅은 가로줄, 행 높이 `h-row`, 글자 `text-table`, 행에 올리면 `bg-hover` 다. */
function ConversationTable({ rows, clock }: RowsProps) {
  return (
    <table className="hidden w-full border-collapse text-table @split:table">
      <thead>
        <HeadRow />
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={keyOf(row)} className="hover:bg-bg-hover">
            {isUnreadable(row) ? (
              <UnreadableCells row={row} />
            ) : (
              <ConversationCells row={row} clock={clock} />
            )}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

interface ConversationProps {
  readonly row: Conversation;
  readonly clock: Intl.DateTimeFormat;
}

function ConversationCells({ row, clock }: ConversationProps) {
  return (
    <>
      <td className={CELL}>
        <div className="flex items-center gap-3">
          <TextLink href={chatHref(row.last_run)} fit="clip">
            {row.first_request}
          </TextLink>
          {row.complete ? null : <Incomplete />}
        </div>
      </td>
      <td className={CELL}>
        <Requester row={row} />
      </td>
      <td className={`${CELL} wrap-anywhere`}>{row.agent}</td>
      <td className={CELL}>
        <StatusBadge status={BADGE[row.status]} />
      </td>
      <td className={`${CELL} whitespace-nowrap`}>{row.run_count}</td>
      <td className={`${CELL} ${TIME}`}>{formatTime(clock, row.last_at)}</td>
    </>
  );
}

/** 읽을 수 없는 트레이스의 줄. 첫 칸에 표지와 링크, 나머지 다섯을 합친 칸에 이유다. 열면 이유를 단건 읽기의 봉투로 본다. */
function UnreadableCells({ row }: { readonly row: UnreadableTrace }) {
  return (
    <>
      <td className={`${CELL} text-warning`}>
        <div className="flex items-center gap-2">
          <Icon name="triangle-alert" size="16" />
          <TextLink href={chatHref(row.run_id)} font="mono">
            {row.run_id}
          </TextLink>
        </div>
      </td>
      <td colSpan={5} className={`${CELL} text-warning wrap-anywhere`}>
        읽을 수 없는 트레이스: {row.reason}
      </td>
    </>
  );
}

/**
 * 좁은 갈래. 대화마다 카드이고 첫 줄에 상태 배지와 마지막 시각, 그 아래에 첫 요청 링크, 요청한 계정, 에이전트, 실행이다.
 * 라벨과 값은 CSS 표로 세워 라벨 폭이 가장 긴 라벨을 따른다(실행 목록의 카드와 같다).
 */
function ConversationCards({ rows, clock }: RowsProps) {
  return (
    <ul className="flex flex-col gap-3 @split:hidden">
      {rows.map((row) => (
        <li key={keyOf(row)}>
          <Card padding="3">
            {isUnreadable(row) ? (
              <UnreadableCard row={row} />
            ) : (
              <ConversationCard row={row} clock={clock} />
            )}
          </Card>
        </li>
      ))}
    </ul>
  );
}

function ConversationCard({ row, clock }: ConversationProps) {
  return (
    <>
      <div className="flex items-center justify-between gap-2">
        <StatusBadge status={BADGE[row.status]} />
        <span className={TIME}>{formatTime(clock, row.last_at)}</span>
      </div>
      <TextLink href={chatHref(row.last_run)}>{row.first_request}</TextLink>
      {row.complete ? null : <Incomplete />}
      <dl className="table w-fit border-separate border-spacing-y-1 text-table">
        <Field term="요청한 계정">
          <Requester row={row} />
        </Field>
        <Field term="에이전트">{row.agent}</Field>
        <Field term="실행">{row.run_count}</Field>
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
      <TextLink href={chatHref(row.run_id)} font="mono">
        {row.run_id}
      </TextLink>
    </>
  );
}

/**
 * 처음 불러오는 동안의 넓은 갈래. 표 머리와, 진짜 행과 같은 높이의 막대 행이다. 막대는 움직이지 않는다
 * (`.claude/rules/web-design.md` 의 뼈대 줄). 화면 읽기 프로그램에서는 숨고, 불러오는 중이라는 말은 읽기 골격의 상태
 * 영역이 한다.
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

/** 막대의 폭. 첫 요청과 요청한 계정은 행마다 길이를 엇갈려 진짜 목록처럼 보이게 한다. */
function barWidth(column: (typeof COLUMNS)[number], index: number): string {
  const odd = index % 2 === 1;
  switch (column) {
    case "첫 요청":
      return odd ? "w-1/2" : "w-3/4";
    case "요청한 계정":
      return odd ? "w-1/3" : "w-2/3";
    case "에이전트":
      return odd ? "w-1/3" : "w-2/3";
    case "상태":
      return "w-1/2";
    case "실행":
      return "w-1/4";
    case "마지막":
      return "w-full";
  }
}
