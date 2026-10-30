import { THEMES, type ThemeKey } from "@agent-os/ui";
import { useId } from "react";
import { ThemeCard } from "../molecules/ThemeCard";

interface ThemePickerProps {
  /** 지금 그려지는 테마. 그 카드가 골라져 있다. */
  readonly theme: ThemeKey;
  readonly onChoose: (theme: ThemeKey) => void;
}

/**
 * 설정 화면의 테마 구역(admin-style 명세 "설정 화면과 테마", 그림 mk-settings, mk-settings-m). `fieldset` "테마" 안에
 * 패키지의 `THEMES` 차례로 카드를 둔다. 저장 버튼은 없다. 카드를 누르면 받은 처리기가 바로 화면 전체를 그 테마로 바꾼다.
 * 본문 칸이 `split` 이상이면 한 줄에 넷, 그 미만이면 두 줄에 둘씩이다. 모드는 고르지 않는다.
 */
export function ThemePicker({ theme, onChoose }: ThemePickerProps) {
  const group = useId();
  return (
    <fieldset className="flex min-w-0 flex-col gap-3">
      <legend className="mb-3 text-body font-semibold">테마</legend>
      <div className="grid grid-cols-2 gap-3 @split:grid-cols-4">
        {THEMES.map(({ key, name }) => (
          <ThemeCard
            key={key}
            theme={key}
            name={name}
            group={group}
            chosen={key === theme}
            onChoose={onChoose}
          />
        ))}
      </div>
      <p className="text-small text-text-muted">모드(라이트·다크)는 시스템 설정을 따른다.</p>
    </fieldset>
  );
}
