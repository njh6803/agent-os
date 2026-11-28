import {
  type KeyboardEvent as ReactKeyboardEvent,
  type RefObject,
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

interface PopupMenuOptions {
  /** 처음부터 연 채 그린다. 사진 비교의 스토리가 쓴다. 이때는 첫 항목에 포커스를 옮기지 않는다. */
  readonly initiallyOpen?: boolean;
  /**
   * 닫을 수 있는가. 거짓이면 Esc 와 메뉴 밖 누르기와 단추가 메뉴를 닫지 않는다. 요청이 가는 동안 응답을 못 본 채 메뉴가
   * 사라지지 않게 하려는 것이다.
   */
  readonly canClose?: boolean;
}

export interface PopupMenu {
  readonly open: boolean;
  /** 메뉴와 단추를 함께 감싼 요소. 이 밖을 누르면 닫힌다. */
  readonly rootRef: RefObject<HTMLDivElement | null>;
  /** 메뉴를 여닫는 단추. 닫히면 포커스가 여기로 돌아온다. */
  readonly triggerRef: RefObject<HTMLButtonElement | null>;
  /** `role="menu"` 요소. 연 뒤 첫 항목에 포커스가 가고 방향 키가 항목 사이를 옮긴다. */
  readonly menuRef: RefObject<HTMLDivElement | null>;
  readonly toggle: () => void;
  readonly close: () => void;
  /** 항목을 골랐다. 메뉴를 닫고 포커스를 단추로 돌린 뒤 그 일을 한다(그 일이 띄운 창이 단추로 돌아올 곳을 알게 한다). */
  readonly choose: (action: () => void) => void;
  readonly onMenuKeyDown: (event: ReactKeyboardEvent) => void;
}

/** 메뉴 안의 쓸 수 있는 항목들. 쓸 수 없는 항목(`aria-disabled`)은 건너뛴다. */
function enabledItems(menu: HTMLElement | null): HTMLElement[] {
  if (menu === null) {
    return [];
  }
  return Array.from(menu.querySelectorAll<HTMLElement>('[role="menuitem"]')).filter(
    (item) => item.getAttribute("aria-disabled") !== "true",
  );
}

/**
 * 단추가 여는 메뉴의 동작(WAI-ARIA 의 메뉴 단추 패턴). 사용자가 열면 첫 항목에 포커스가 가고, 위아래·처음·끝 키가 항목
 * 사이를 옮기고, Esc 는 메뉴를 닫으며 포커스를 단추로 돌린다. 메뉴 밖을 누르면 포커스를 따로 옮기지 않고(누른 곳이 포커스를 받는다) 닫는다. Tab 은 메뉴를
 * 닫고 포커스를 자연스럽게 다음으로 보낸다.
 */
export function usePopupMenu({
  initiallyOpen = false,
  canClose = true,
}: PopupMenuOptions = {}): PopupMenu {
  const [open, setOpen] = useState(initiallyOpen);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const focusFirst = useRef(false);

  useEffect(() => {
    if (open && focusFirst.current) {
      focusFirst.current = false;
      enabledItems(menuRef.current)[0]?.focus();
    }
  }, [open]);

  useEffect(() => {
    if (!open) {
      return;
    }
    function closeOnOutside(event: MouseEvent): void {
      if (
        canClose &&
        event.target instanceof Node &&
        rootRef.current?.contains(event.target) !== true
      ) {
        setOpen(false);
      }
    }
    function closeOnEscape(event: KeyboardEvent): void {
      if (canClose && event.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    }
    document.addEventListener("mousedown", closeOnOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open, canClose]);

  const toggle = useCallback(() => {
    if (open && !canClose) {
      return;
    }
    focusFirst.current = !open;
    setOpen(!open);
  }, [open, canClose]);

  const close = useCallback(() => {
    setOpen(false);
  }, []);

  const choose = useCallback((action: () => void) => {
    setOpen(false);
    triggerRef.current?.focus();
    action();
  }, []);

  const onMenuKeyDown = useCallback(
    (event: ReactKeyboardEvent) => {
      if (event.key === "Tab") {
        if (canClose) {
          setOpen(false);
        }
        return;
      }
      const items = enabledItems(menuRef.current);
      const at = items.findIndex((item) => item === document.activeElement);
      let next: number | null = null;
      switch (event.key) {
        case "ArrowDown":
          next = items.length === 0 ? null : (at + 1) % items.length;
          break;
        case "ArrowUp":
          next = items.length === 0 ? null : (at <= 0 ? items.length : at) - 1;
          break;
        case "Home":
          next = items.length === 0 ? null : 0;
          break;
        case "End":
          next = items.length === 0 ? null : items.length - 1;
          break;
        default:
          return;
      }
      event.preventDefault();
      if (next !== null) {
        items[next]?.focus();
      }
    },
    [canClose],
  );

  return { open, rootRef, triggerRef, menuRef, toggle, close, choose, onMenuKeyDown };
}
