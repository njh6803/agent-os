import { Button, StatusBadge, type ThemeKey } from "@agent-os/ui";
import { useId } from "react";

const CARD_CLASS = {
  chosen: "border-2 border-accent bg-bg-selected",
  other: "border border-border-control bg-bg-raised",
} satisfies Record<"chosen" | "other", string>;

interface ThemeCardProps {
  readonly theme: ThemeKey;
  /** 화면에 보이는 테마 이름. 라디오의 이름이다. */
  readonly name: string;
  /** 같은 묶음의 라디오가 나눠 갖는 `name`. */
  readonly group: string;
  readonly chosen: boolean;
  readonly onChoose: (theme: ThemeKey) => void;
}

/**
 * 설정 화면의 테마 카드 하나(admin-style 명세 "설정 화면과 테마", 그림 mk-settings, mk-settings-m). 라디오 하나와 그 테마로
 * 칠한 표본이고, 카드 전체가 누르는 곳이다. 고른 카드는 라디오의 체크와 강조색 테두리로 드러난다.
 *
 * 표본은 `data-theme` 만 단 요소다. `data-mode` 를 달지 않아 그 테마의 시스템 모드 값을 받는다(쟀다,
 * .scratch/admin-style/probes/card_theme.mjs). `inert` 라 표본의 버튼은 누르거나 포커스할 수 없다. 표본을 누르면 그
 * 누름이 카드(라벨)에 가 라디오가 골라진다고 본다(어림. 시험은 `inert` 속성만 본다). 라디오의 이름은 테마 이름 하나로
 * 잇는다. 카드가 라벨이라 잇지 않으면 표본의 글자가 이름에 섞인다.
 */
export function ThemeCard({ theme, name, group, chosen, onChoose }: ThemeCardProps) {
  const nameId = useId();
  return (
    <label
      className={`flex flex-col gap-3 rounded-l p-3 ${CARD_CLASS[chosen ? "chosen" : "other"]}`}
    >
      <span className="flex items-center gap-2 text-body font-medium">
        <input
          type="radio"
          name={group}
          value={theme}
          checked={chosen}
          aria-labelledby={nameId}
          className="focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
          onChange={() => {
            onChoose(theme);
          }}
        />
        <span id={nameId}>{name}</span>
      </span>
      <span
        inert
        data-theme={theme}
        className="flex flex-col items-start gap-2 rounded-m border border-border bg-bg p-2 text-text @split:p-3"
      >
        <Button>승인</Button>
        <StatusBadge status="done" />
        <span className="font-mono text-mono wrap-anywhere">payments.refund</span>
      </span>
    </label>
  );
}
