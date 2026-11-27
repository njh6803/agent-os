// 관리 화면의 창(admin-login 명세 "계정 화면과 내 비밀번호", 그림 mk-accounts-create, mk-accounts-link, mk-accounts-disable).
// 어두운 막 위에 가운데 정렬한 카드가 뜨고, 제목과 내용이 선다. 디자인 시스템의 부품이 아니라 앱이 짓는다(ADR 0026. 헤드리스
// 라이브러리를 들이지 않고 기본 요소로 짓는다).
//
// 본문 칸(`@container`)은 레이아웃 격리라 그 안의 `fixed` 요소가 본문 칸을 기준으로 선다. 그래서 문서 `body` 에 포털로 그린다.
// 창이 열리면 첫 조작 요소에 포커스가 가고, Tab 은 창 안에서 돌며, 닫히면 포커스가 열기 전의 자리로 돌아온다(그 자리가 아직 문서에 있을 때만이다. 비활성으로 바꾼 줄처럼 사라졌으면
// 돌아가지 않는다). Esc 로 닫는다.
// 막을 눌러 닫지 않는다. 비밀번호 링크처럼 닫으면 다시 볼 수 없는 내용이 있기 때문이다.
import {
  type KeyboardEvent as ReactKeyboardEvent,
  type ReactNode,
  useEffect,
  useId,
  useRef,
} from "react";
import { createPortal } from "react-dom";

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

function focusables(box: HTMLElement | null): HTMLElement[] {
  return box === null ? [] : Array.from(box.querySelectorAll<HTMLElement>(FOCUSABLE));
}

interface DialogProps {
  /** 창의 제목(`h2`). 창의 이름이 된다. */
  readonly title: ReactNode;
  /** 닫는다. Esc 가 부른다. 닫기 단추는 쓰는 쪽이 창 안에 두고 같은 함수를 이어 준다. */
  readonly onClose: () => void;
  /** 요청이 가는 동안 참이다. 이 동안 Esc 로 닫지 않는다(응답을 못 본 채 사라지지 않게). */
  readonly busy?: boolean;
  readonly children: ReactNode;
}

export function Dialog({ title, onClose, busy = false, children }: DialogProps) {
  const titleId = useId();
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const before = document.activeElement;
    const first = focusables(box.current)[0];
    if (first === undefined) {
      box.current?.focus();
    } else {
      first.focus();
    }
    return () => {
      if (before instanceof HTMLElement && before.isConnected) {
        before.focus();
      }
    };
  }, []);

  // Esc 는 포커스가 창 안에 없어도 닫는다. 막을 눌러도 포커스는 옮겨 가지 않지만(아래), 화면 읽기 프로그램이 창 밖을 읽고
  // 있을 수 있다. 요청이 가는 동안은 닫지 않는다.
  useEffect(() => {
    function closeOnEscape(event: KeyboardEvent): void {
      if (event.key === "Escape" && !busy) {
        onClose();
      }
    }
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [busy, onClose]);

  function onKeyDown(event: ReactKeyboardEvent): void {
    if (event.key !== "Tab") {
      return;
    }
    const items = focusables(box.current);
    const first = items[0];
    const last = items.at(-1);
    if (first === undefined || last === undefined) {
      event.preventDefault();
      return;
    }
    // 창 안의 빈 곳을 눌러 포커스가 상자 자신(`tabIndex={-1}`)에 있을 때도 거꾸로 가면 맨 끝으로 돈다. 막지 않으면 브라우저가
    // 문서 순서상 앞 요소(창 밖의 배경 화면)로 포커스를 옮긴다.
    if (
      event.shiftKey &&
      (document.activeElement === first || document.activeElement === box.current)
    ) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return createPortal(
    <div className="fixed inset-0 z-20 flex items-start justify-center overflow-y-auto p-4">
      {/* 막을 눌러도 창을 닫지 않고 포커스도 창 밖으로 옮기지 않는다. */}
      <div
        aria-hidden="true"
        className="fixed inset-0 bg-text opacity-30"
        onMouseDown={(event) => {
          event.preventDefault();
        }}
      />
      <div
        ref={box}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        onKeyDown={onKeyDown}
        className="relative mt-8 flex w-full max-w-form flex-col gap-4 rounded-l border border-border bg-bg-raised p-6 text-text shadow-float focus:outline-none"
      >
        <h2 id={titleId} className="text-title wrap-anywhere">
          {title}
        </h2>
        {children}
      </div>
    </div>,
    document.body,
  );
}
