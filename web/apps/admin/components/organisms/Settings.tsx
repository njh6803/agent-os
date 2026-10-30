// 설정 화면의 본문(admin-style 명세 "설정 화면과 테마", 그림 mk-settings, mk-settings-m). 화면 머리, 테마, 채널 토큰,
// 토큰 지우기이고 최대 폭 `content` 다. 서버에서 읽는 것이 없어 새로 고침이 없다. 지금 테마(문서 뿌리의 속성)와 토큰
// 스토어의 값은 pages 가 읽어 넘긴다.
//
// 채널 토큰과 토큰 지우기의 머리(`h2` 와 흐린 설명 한 줄)는 두 구역이 저마다 적는다. 테마는 `fieldset` 의 `legend` 가
// 머리이고 머리 바로 아래에 흐린 설명 줄이 없어 그 모양이 아니다. 같은 모양이 둘뿐이라 묶지 않는다(admin-style 티켓 09).
import type { ThemeKey } from "@agent-os/ui";
import { ScreenHeader } from "../molecules/ScreenHeader";
import { ChannelTokenForm } from "./ChannelTokenForm";
import { ClearTokens } from "./ClearTokens";
import { ThemePicker } from "./ThemePicker";

interface SettingsProps {
  /** 지금 그려지는 테마. */
  readonly theme: ThemeKey;
  readonly onChooseTheme: (theme: ThemeKey) => void;
  /** 이 탭에 채널 토큰이 있는가. */
  readonly channelTokenEntered: boolean;
  readonly onEnterChannelToken: (token: string) => void;
  readonly onClearTokens: () => void;
}

export function Settings({
  theme,
  onChooseTheme,
  channelTokenEntered,
  onEnterChannelToken,
  onClearTokens,
}: SettingsProps) {
  return (
    <div className="flex max-w-content flex-col gap-8">
      <ScreenHeader
        title="설정"
        description="테마는 이 브라우저에, 토큰은 이 탭에만 남는다. 서버의 구성은 바꾸지 않는다."
      />
      <ThemePicker theme={theme} onChoose={onChooseTheme} />
      <ChannelTokenForm entered={channelTokenEntered} onEnter={onEnterChannelToken} />
      <ClearTokens onClear={onClearTokens} />
    </div>
  );
}
