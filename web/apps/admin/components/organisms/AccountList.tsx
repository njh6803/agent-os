import {
  AccountStatusBadge,
  type AccountStatusBadgeStatus,
  Button,
  Card,
  IconButton,
  Switch,
} from "@agent-os/ui";
import { type ReactNode, useId, useState } from "react";
import type { AccountCreation, AccountRow, IssuedLink } from "../../api/accounts";
import { describeFailure } from "../../api/failure";
import { formatClockTime, formatMinute, localClock } from "../atoms/clock";
import { EmptyLine } from "../molecules/EmptyLine";
import { FailureAlert } from "../molecules/FailureAlert";
import { usePopupMenu } from "../../hooks/usePopupMenu";
import { CreateAccountDialog } from "./CreateAccountDialog";
import { DisableAccountDialog } from "./DisableAccountDialog";
import { PasswordLinkDialog } from "./PasswordLinkDialog";
import { ReadSection, type ReadState } from "./ReadSection";

/** 단계의 화면 이름. 계약의 값 둘에 하나씩 맞는다. */
const TIER_LABEL = {
  system_admin: "시스템 관리자",
  admin: "관리자",
} as const satisfies Record<AccountRow["tier"], string>;

/** 계정 상태가 잇는 배지의 상태. 잠김은 상태가 아니라 위에 더하는 배지라 여기 없다. */
const BADGE = {
  active: "active",
  disabled: "inactive",
  password_unset: "password-unset",
} as const satisfies Record<AccountRow["state"], AccountStatusBadgeStatus>;

/** 표의 열 머리. 마지막 열은 글자 없이 줄 끝의 메뉴 단추가 서서 화면 읽기 프로그램에만 이름이 있다. */
const COLUMNS = ["계정 이름", "단계", "상태", "만든 시각"] as const;

const HEAD_CELL =
  "h-row border-b border-border px-3 text-left text-small font-medium text-text-muted";
const CELL = "h-row border-b border-border px-3";
const TIME = "font-mono text-mono whitespace-nowrap text-text-muted";

const MENU_ITEM =
  "flex h-control items-center rounded-s px-3 text-left text-body hover:bg-bg-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring aria-disabled:text-text-disabled";

/** 줄 끝의 메뉴가 부르는 쓰기. 응답 뒤에 목록을 다시 읽는 것은 훅의 일이다. */
export interface AccountListActions {
  readonly create: (name: string) => Promise<AccountCreation>;
  readonly issueLink: (name: string) => Promise<IssuedLink>;
  readonly enable: (name: string) => Promise<void>;
  readonly disable: (name: string) => Promise<void>;
  readonly unlock: (name: string) => Promise<void>;
}

interface AccountListProps extends ReadState<readonly AccountRow[]> {
  /** 지금 로그인한 계정의 이름. 그 줄에 "지금 계정"이 붙는다. */
  readonly currentName: string;
  /** 로그인이 길어야 몇 분 안에 끊기는지. 비활성으로 바꾸기 창의 첫 줄에 든다. */
  readonly tokenMinutes: number;
  readonly actions: AccountListActions;
  /** 토큰으로 비밀번호 링크의 주소를 짓는다. 이 관리 화면의 출처가 든다. */
  readonly addressOf: (token: string) => string;
  /**
   * 열린 모양을 사진에 남기려는 스토리가 args 로 준다. 사진 비교는 클릭하기 전의 그림이다. 화면(pages)은 쓰지 않는다
   * (`.claude/rules/web-design.md`).
   */
  readonly preview?: {
    /** 비활성 계정도 보인 채 그린다. */
    readonly showInactive?: boolean;
    /** 이 이름의 줄 끝 메뉴를 연 채 그린다. */
    readonly openMenuOf?: string;
  };
}

/** 지금 열려 있는 창. 하나만 열린다. */
type Dialog =
  | { readonly kind: "create" }
  | { readonly kind: "link"; readonly link: IssuedLink }
  | { readonly kind: "disable"; readonly name: string };

function isLocked(row: AccountRow, now: number): boolean {
  return row.locked_until !== null && new Date(row.locked_until).getTime() > now;
}

/**
 * 계정 목록(`GET /accounts`, admin-login 명세 "계정 화면과 내 비밀번호"). 열은 계정 이름, 단계, 상태, 만든 시각, 동작이고
 * 본문 칸이 `split` 이상이면 표, 미만이면 계정마다 카드다(실행 목록과 같은 갈래). 비활성 계정은 기본으로 숨기고 "비활성
 * 계정도 보기"를 켜면 보인다. 잠긴 계정은 상태 배지 옆에 잠김 배지와 풀리는 시각(이 브라우저의 시간대)이 선다.
 *
 * 줄 끝의 메뉴는 계정마다 다르다. 시스템 관리자의 줄에는 메뉴가 없고 잠겼을 때만 "잠금 풀기"가 선다. 비활성 계정에는
 * "활성으로 바꾸기"만 있다. 그 밖의 계정에는 "비밀번호 링크 만들기", 잠겼으면 "잠금 풀기", "비활성으로 바꾸기"가 있다.
 * 링크를 만들거나 계정을 만들면 비밀번호 링크 창이 열리고, 비활성으로 바꿀 때는 확인 창이 먼저 열린다.
 */
export function AccountList({
  currentName,
  tokenMinutes,
  actions,
  addressOf,
  preview,
  ...read
}: AccountListProps) {
  const clock = localClock();
  const [showInactive, setShowInactive] = useState(preview?.showInactive ?? false);
  const [dialog, setDialog] = useState<Dialog | null>(null);
  const [working, setWorking] = useState(false);
  const [failure, setFailure] = useState<unknown>(null);

  /** 메뉴에서 고른 일을 한다. 하는 동안 다른 메뉴 일은 받지 않고, 실패하면 목록 위에 알린다. */
  async function run(request: () => Promise<void>): Promise<void> {
    if (working) {
      return;
    }
    setWorking(true);
    setFailure(null);
    try {
      await request();
    } catch (cause) {
      setFailure(cause);
    } finally {
      setWorking(false);
    }
  }

  const handlers: RowHandlers = {
    working,
    openMenuOf: preview?.openMenuOf ?? null,
    onLink: (name) =>
      run(async () => {
        const link = await actions.issueLink(name);
        setDialog({ kind: "link", link });
      }),
    onUnlock: (name) => run(() => actions.unlock(name)),
    onEnable: (name) => run(() => actions.enable(name)),
    onDisable: (name) => {
      setDialog({ kind: "disable", name });
    },
  };

  const failureText = failure === null ? null : describeFailure(failure);
  return (
    <>
      <ReadSection
        title="운영자 계정"
        description={`관리 화면에 로그인하는 계정을 만들고 막는다. 시스템 관리자에게만 보인다. 시각은 이 브라우저의 시간대(${clock.resolvedOptions().timeZone})로 적었다.`}
        {...read}
        loadingLabel="계정 목록을 불러오는 중"
        failureTitle="계정 목록을 읽지 못했다"
        above={
          <>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <Switch
                label="비활성 계정도 보기"
                checked={showInactive}
                onChange={setShowInactive}
              />
              <Button
                onClick={() => {
                  setDialog({ kind: "create" });
                }}
              >
                계정 만들기
              </Button>
            </div>
            {failureText === null ? null : (
              <FailureAlert
                title="계정을 바꾸지 못했다"
                message={failureText.message}
                requestId={failureText.requestId}
              />
            )}
          </>
        }
      >
        {(accounts) => {
          const rows = accounts.filter((row) => showInactive || row.state !== "disabled");
          const now = Date.now();
          return rows.length === 0 ? (
            <EmptyLine icon="users" iconSize="20">
              계정이 없다
            </EmptyLine>
          ) : (
            <>
              <AccountTable
                rows={rows}
                clock={clock}
                now={now}
                currentName={currentName}
                handlers={handlers}
              />
              <AccountCards
                rows={rows}
                clock={clock}
                now={now}
                currentName={currentName}
                handlers={handlers}
              />
            </>
          );
        }}
      </ReadSection>
      {dialog?.kind === "create" ? (
        <CreateAccountDialog
          onCreate={actions.create}
          onCreated={(link) => {
            setDialog({ kind: "link", link });
          }}
          onClose={() => {
            setDialog(null);
          }}
        />
      ) : null}
      {dialog?.kind === "link" ? (
        <PasswordLinkDialog
          link={dialog.link}
          addressOf={addressOf}
          onClose={() => {
            setDialog(null);
          }}
        />
      ) : null}
      {dialog?.kind === "disable" ? (
        <DisableAccountDialog
          name={dialog.name}
          tokenMinutes={tokenMinutes}
          onConfirm={() => actions.disable(dialog.name)}
          onClose={() => {
            setDialog(null);
          }}
        />
      ) : null}
    </>
  );
}

interface RowHandlers {
  /** 메뉴의 쓰기가 가는 중이다. 이 동안 다른 항목을 받지 않는다. */
  readonly working: boolean;
  /** 처음부터 메뉴를 연 줄의 이름. 스토리만 준다. */
  readonly openMenuOf: string | null;
  readonly onLink: (name: string) => Promise<void>;
  readonly onUnlock: (name: string) => Promise<void>;
  readonly onEnable: (name: string) => Promise<void>;
  readonly onDisable: (name: string) => void;
}

interface RowsProps {
  readonly rows: readonly AccountRow[];
  readonly clock: Intl.DateTimeFormat;
  readonly now: number;
  readonly currentName: string;
  readonly handlers: RowHandlers;
}

interface RowProps {
  readonly row: AccountRow;
  readonly clock: Intl.DateTimeFormat;
  readonly now: number;
  readonly current: boolean;
  readonly handlers: RowHandlers;
}

/** 넓은 갈래. 칸에 세로줄 없이 행 사이에 옅은 가로줄이다(실행 목록의 표와 같다). */
function AccountTable({ rows, clock, now, currentName, handlers }: RowsProps) {
  return (
    <table className="hidden w-full border-collapse text-table @split:table">
      <thead>
        <tr>
          {COLUMNS.map((column) => (
            <th key={column} scope="col" className={HEAD_CELL}>
              {column}
            </th>
          ))}
          <th scope="col" className="h-row border-b border-border">
            <span className="sr-only">동작</span>
          </th>
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <AccountTableRow
            key={row.name}
            row={row}
            clock={clock}
            now={now}
            current={row.name === currentName}
            handlers={handlers}
          />
        ))}
      </tbody>
    </table>
  );
}

function AccountTableRow({ row, clock, now, current, handlers }: RowProps) {
  return (
    <tr className="hover:bg-bg-hover">
      <td className={CELL}>
        <NameWithMark name={row.name} current={current} />
      </td>
      <td className={CELL}>{TIER_LABEL[row.tier]}</td>
      <td className={CELL}>
        <Status row={row} clock={clock} now={now} />
      </td>
      <td className={`${CELL} ${TIME}`}>{formatMinute(clock, row.created_at)}</td>
      <td className={`${CELL} text-right`}>
        <RowMenu row={row} locked={isLocked(row, now)} handlers={handlers} />
      </td>
    </tr>
  );
}

/** 좁은 갈래. 계정마다 카드이고 첫 줄에 이름과 메뉴 단추, 그 아래에 단계, 상태, 만든 시각이다. */
function AccountCards({ rows, clock, now, currentName, handlers }: RowsProps) {
  return (
    <ul className="flex flex-col gap-3 @split:hidden">
      {rows.map((row) => (
        <li key={row.name}>
          <Card padding="3">
            <div className="flex items-center justify-between gap-2">
              <NameWithMark name={row.name} current={row.name === currentName} />
              <RowMenu row={row} locked={isLocked(row, now)} handlers={handlers} />
            </div>
            <dl className="table w-fit border-separate border-spacing-y-1 text-table">
              <Field term="단계">{TIER_LABEL[row.tier]}</Field>
              <Field term="상태">
                <Status row={row} clock={clock} now={now} />
              </Field>
              <Field term="만든 시각">
                <span className="font-mono text-mono">{formatMinute(clock, row.created_at)}</span>
              </Field>
            </dl>
          </Card>
        </li>
      ))}
    </ul>
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

function NameWithMark({ name, current }: { readonly name: string; readonly current: boolean }) {
  return (
    <span className="flex min-w-0 flex-wrap items-center gap-x-2">
      <span className="font-mono text-mono wrap-anywhere">{name}</span>
      {current ? <span className="text-small text-text-muted">지금 계정</span> : null}
    </span>
  );
}

/** 상태 배지 하나와, 잠겼으면 그 옆에 잠김 배지와 풀리는 시각이다. */
function Status({
  row,
  clock,
  now,
}: {
  readonly row: AccountRow;
  readonly clock: Intl.DateTimeFormat;
  readonly now: number;
}) {
  const until = isLocked(row, now) ? row.locked_until : null;
  return (
    <span className="flex flex-wrap items-center gap-2">
      <AccountStatusBadge status={BADGE[row.state]} />
      {until === null ? null : (
        <>
          <AccountStatusBadge status="locked" />
          <span className="font-mono text-mono whitespace-nowrap text-text-muted">
            {formatClockTime(clock, until)}까지
          </span>
        </>
      )}
    </span>
  );
}

interface MenuItem {
  readonly label: string;
  readonly run: () => void;
  /** 이 항목 앞에 가르는 줄을 둔다. */
  readonly separated?: boolean;
}

/** 줄의 계정에 맞는 메뉴 항목들. 비어 있으면 메뉴가 없다. */
function itemsOf(
  row: AccountRow,
  { locked, handlers }: { readonly locked: boolean; readonly handlers: RowHandlers },
): MenuItem[] {
  const unlock: MenuItem = {
    label: "잠금 풀기",
    run: () => {
      void handlers.onUnlock(row.name);
    },
  };
  if (row.tier === "system_admin") {
    return locked ? [unlock] : [];
  }
  if (row.state === "disabled") {
    return [
      {
        label: "활성으로 바꾸기",
        run: () => {
          void handlers.onEnable(row.name);
        },
      },
    ];
  }
  return [
    {
      label: "비밀번호 링크 만들기",
      run: () => {
        void handlers.onLink(row.name);
      },
    },
    ...(locked ? [unlock] : []),
    {
      label: "비활성으로 바꾸기",
      separated: true,
      run: () => {
        handlers.onDisable(row.name);
      },
    },
  ];
}

/**
 * 줄 끝의 메뉴. 메뉴 단추 패턴이다(`hooks/usePopupMenu`). 항목이 없으면 단추도 없다. 쓰기가 가는 동안은 항목이 `aria-disabled`
 * 이고 눌러도 받지 않는다.
 */
function RowMenu({
  row,
  locked,
  handlers,
}: {
  readonly row: AccountRow;
  readonly locked: boolean;
  readonly handlers: RowHandlers;
}) {
  const menu = usePopupMenu({ initiallyOpen: handlers.openMenuOf === row.name });
  const menuId = useId();
  const items = itemsOf(row, { locked, handlers });
  if (items.length === 0) {
    return null;
  }
  return (
    <div ref={menu.rootRef} className="relative inline-block text-left">
      <IconButton
        ref={menu.triggerRef}
        icon="ellipsis"
        label={`${row.name}의 동작`}
        size="s"
        aria-haspopup="menu"
        aria-expanded={menu.open}
        aria-controls={menu.open ? menuId : undefined}
        onClick={menu.toggle}
      />
      {menu.open ? (
        <div
          ref={menu.menuRef}
          id={menuId}
          role="menu"
          aria-label={`${row.name}의 동작`}
          onKeyDown={menu.onMenuKeyDown}
          className="absolute top-full right-0 z-10 mt-1 flex min-w-cell-max flex-col rounded-m border border-border bg-bg-raised p-1 shadow-float"
        >
          {items.map((item) => (
            <MenuEntry key={item.label} item={item} busy={handlers.working} choose={menu.choose} />
          ))}
        </div>
      ) : null}
    </div>
  );
}

function MenuEntry({
  item,
  busy,
  choose,
}: {
  readonly item: MenuItem;
  readonly busy: boolean;
  readonly choose: (action: () => void) => void;
}) {
  return (
    <>
      {item.separated === true ? (
        <div role="separator" className="my-1 border-t border-border" />
      ) : null}
      <button
        type="button"
        role="menuitem"
        tabIndex={-1}
        aria-disabled={busy}
        onClick={() => {
          if (!busy) {
            choose(item.run);
          }
        }}
        className={MENU_ITEM}
      >
        {item.label}
      </button>
    </>
  );
}
