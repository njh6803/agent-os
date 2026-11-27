// 설정 화면의 본문(admin-style 명세 "설정 화면과 테마", 그림 mk-settings, mk-settings-m). 화면 머리와 테마이고 최대 폭
// `content` 다. 서버에서 읽는 것이 없어 새로 고침이 없다. 지금 테마(문서 뿌리의 속성)는 pages 가 읽어 넘긴다. 토큰을 넣는
// 칸과 지우는 단추는 없다. 로그인으로 바뀌어 관리 화면이 토큰을 쓰지 않는다(admin-login 티켓 09).
import type { ThemeKey } from "@agent-os/ui";
import { ScreenHeader } from "../molecules/ScreenHeader";
import { ThemePicker } from "./ThemePicker";

interface SettingsProps {
  /** 지금 그려지는 테마. */
  readonly theme: ThemeKey;
  readonly onChooseTheme: (theme: ThemeKey) => void;
}

export function Settings({ theme, onChooseTheme }: SettingsProps) {
  return (
    <div className="flex max-w-content flex-col gap-8">
      <ScreenHeader title="설정" description="테마는 이 브라우저에 남는다." />
      <ThemePicker theme={theme} onChoose={onChooseTheme} />
    </div>
  );
}
