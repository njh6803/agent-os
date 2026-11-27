// 로그인한 계정의 자리와 그 메뉴(admin-login 명세 "탐색", 그림 mk-account-menu, mk-account-menu-m). 틀(AdminFrame)의
// `account` 슬롯에 든다. 넓은 폭(`wide` 이상)에서는 옆 탐색의 맨 아래에 이름과 단계가 두 줄로 서고 메뉴가 위로 열린다. 좁은
// 폭에서는 위 막대 첫 줄 오른쪽에 이름만 든 단추가 서고 메뉴가 아래로 열리며, 단계는 메뉴 맨 위에 보인다. 두 벌을 그리지
// 않고 같은 요소의 배치만 바꾼다(AdminFrame 의 머리 주석과 같은 까닭).
//
// 메뉴의 항목은 "로그아웃" 하나다("내 비밀번호 바꾸기"는 티켓 12가 더한다). 로그아웃은 요청을 처리기로 받는다(organisms 는
// 서버 요청을 props 로 받은 처리기로만 일으킨다). 쿠키를 지우는 응답을 받지 못했으면 `failed` 가 참이고, 메뉴를 닫지 않은
// 채 그 자리에 알린다. 성공하면 화면이 로그인 화면으로 옮겨 가므로 이 부품이 따로 할 일이 없다.
import { Icon } from "@agent-os/ui";
import { useEffect, useId, useRef, useState } from "react";
import type { Me } from "../../api/session";

/** 단계의 화면 이름. 계약의 값 둘에 하나씩 맞는다. */
const TIER_LABEL = {
  system_admin: "시스템 관리자",
  admin: "관리자",
} as const satisfies Record<Me["tier"], string>;

interface AccountMenuProps {
  readonly name: string;
  readonly tier: Me["tier"];
  /** 로그아웃 요청이 가는 동안 참이다. 이 동안 다시 누를 수 없다. */
  readonly pending: boolean;
  /** 쿠키를 지우는 응답을 받지 못했다. 다시 누르면 걷힌다. */
  readonly failed: boolean;
  readonly onLogOut: () => Promise<void>;
  /**
   * 메뉴를 연 채 그린다. 화면(pages)은 쓰지 않는다. 사진 비교는 클릭하기 전의 그림이라, 열린 모양을 사진에 남기려는 스토리가
   * args 로 그린다(`.claude/rules/web-design.md`).
   */
  readonly initiallyOpen?: boolean;
}

export function AccountMenu({
  name,
  tier,
  pending,
  failed,
  onLogOut,
  initiallyOpen = false,
}: AccountMenuProps) {
  const [open, setOpen] = useState(initiallyOpen);
  const root = useRef<HTMLDivElement>(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) {
      return;
    }
    // 메뉴 밖을 누르거나 Esc 를 누르면 닫는다. 요청이 가는 동안에는 닫지 않는다(응답을 못 본 채 사라지지 않게).
    function closeOnOutside(event: MouseEvent): void {
      if (
        !pending &&
        event.target instanceof Node &&
        root.current?.contains(event.target) !== true
      ) {
        setOpen(false);
      }
    }
    function closeOnEscape(event: KeyboardEvent): void {
      if (!pending && event.key === "Escape") {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", closeOnOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open, pending]);

  return (
    <div
      ref={root}
      className="relative order-2 wide:order-none wide:mt-auto wide:border-t wide:border-border wide:pt-3"
    >
      {open ? (
        // 카드(테두리와 그림자)는 이름 없는 상자다. 메뉴(`role="menu"`)는 메뉴 항목만 자식으로 가질 수 있어서 알림을 그 밖, 같은
        // 카드 안에 나란히 둔다.
        <div className="absolute top-full right-0 z-10 mt-1 flex min-w-cell-max flex-col rounded-m border border-border bg-bg-raised p-1 shadow-float wide:top-auto wide:right-0 wide:bottom-full wide:left-0 wide:mt-0 wide:mb-1">
          <div id={menuId} role="menu" aria-label={`${name} 계정`} className="flex flex-col">
            {/* 좁은 폭의 단추에는 이름만 있어 단계를 메뉴 맨 위에 보인다. 넓은 폭은 단추에 이미 있다. */}
            <div className="flex flex-col px-3 py-2 wide:hidden">
              <span className="font-mono text-mono font-medium">{name}</span>
              <span className="text-small text-text-muted">{TIER_LABEL[tier]}</span>
            </div>
            <div role="separator" className="my-1 border-t border-border wide:hidden" />
            <button
              type="button"
              role="menuitem"
              disabled={pending}
              onClick={() => {
                void onLogOut();
              }}
              className="flex h-control items-center gap-2 rounded-s px-3 text-left text-body hover:bg-bg-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring disabled:cursor-not-allowed disabled:text-text-disabled"
            >
              <Icon name="log-out" size="16" />
              로그아웃
            </button>
          </div>
          {failed ? (
            <p role="alert" className="px-3 py-2 text-small text-danger">
              로그아웃하지 못했다. 다시 누른다
            </p>
          ) : null}
        </div>
      ) : null}
      <button
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        onClick={() => {
          // 로그아웃 요청이 가는 동안은 메뉴를 닫지 않는다. 닫으면 진행 중인 요청의 실패 알림이 보이지 않는다.
          if (!pending) {
            setOpen((shown) => !shown);
          }
        }}
        className={`flex h-control w-full items-center gap-1 rounded-m px-2 text-left text-body hover:bg-bg-hover focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring wide:h-auto wide:gap-2 wide:px-3 wide:py-2 ${open ? "bg-bg-active" : ""}`}
      >
        <span className="flex min-w-0 flex-1 flex-col">
          <span className="truncate font-mono text-mono font-medium">{name}</span>
          <span className="hidden text-small text-text-muted wide:block">{TIER_LABEL[tier]}</span>
        </span>
        <span className="shrink-0 text-text-muted">
          <Icon name="chevrons-up-down" size="16" />
        </span>
      </button>
    </div>
  );
}
