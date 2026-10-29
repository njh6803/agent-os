// 설정 화면의 본문(admin-style 명세 "설정 화면과 테마", 그림 mk-settings, mk-settings-m). 화면 머리, 채널 토큰,
// 토큰 지우기이고 최대 폭 `content` 다. 서버에서 읽는 것이 없어 새로 고침이 없다. 토큰은 pages 가 스토어에서 읽어
// 넘긴다. 테마 카드는 09 가 더한다.
import { ScreenHeader } from "../molecules/ScreenHeader";
import { ChannelTokenForm } from "./ChannelTokenForm";
import { ClearTokens } from "./ClearTokens";

interface SettingsProps {
  /** 이 탭에 채널 토큰이 있는가. */
  readonly channelTokenEntered: boolean;
  readonly onEnterChannelToken: (token: string) => void;
  readonly onClearTokens: () => void;
}

export function Settings({
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
      <ChannelTokenForm entered={channelTokenEntered} onEnter={onEnterChannelToken} />
      <ClearTokens onClear={onClearTokens} />
    </div>
  );
}
