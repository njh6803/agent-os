// 입력창 위의 띠(web-widget 명세 "입력창 위의 띠"). 재접속, 상한, 승인 기다림의 안내를 입력창 바로 위에 하나만
// 세운다. 여럿이 겹치면 재접속, 상한, 승인 기다림의 차례로 앞의 것을 보인다.
//
// - 모양은 위 테두리 한 줄이고, 앞에 아이콘이나 진행 표시 하나, 그 뒤에 글이다(화면 디자인 mk-limit, mk-reconnect).
//   아이콘은 글 옆의 꾸밈이라 화면 읽기 프로그램에서 숨는다(Icon 이 숨긴다). 작은 글자 한 줄이 16px 라 16px 아이콘은
//   첫 줄에 맞는다.
// - `role="status"` 의 틀은 띠가 없어도 늘 선다. 처음부터 서 있어야 글이 바뀔 때 읽힌다. 띠가 없으면 위 테두리만 남아
//   대화와 입력 자리를 가른다.
import { Icon, Progress, type IconName } from "@agent-os/ui";
import type { ReactNode } from "react";

/** 띠 하나. 진행 표시와 그 이름이거나, 아이콘과 글이다. */
export type Band =
  | { readonly kind: "progress"; readonly label: string }
  | { readonly kind: "notice"; readonly icon: IconName; readonly text: ReactNode };

export interface ComposerBandProps {
  /** 연결이 끊겨 다시 잇는 중. */
  readonly reconnect: Band | null;
  /** 상한에 걸려 기다리는 중. */
  readonly limit: Band | null;
  /** 승인을 기다리는 중. */
  readonly approval: Band | null;
}

export function ComposerBand({ reconnect, limit, approval }: ComposerBandProps) {
  const band = reconnect ?? limit ?? approval;
  return (
    <div role="status" className="shrink-0 border-t border-border">
      {band === null ? null : (
        <div className="flex items-start gap-2 px-4 py-2 text-small text-text">
          {band.kind === "progress" ? (
            <Progress label={band.label} />
          ) : (
            <>
              <Icon name={band.icon} size="16" />
              <span className="min-w-0">{band.text}</span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
