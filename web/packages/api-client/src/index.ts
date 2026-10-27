// 생성 클라이언트 패키지의 입구(ADR 0021). web 코드가 파이썬 서버를 부를 때 지나는 자리다.

export type { components, paths } from "./generated/openapi";
export {
  createAdminClient,
  createChannelClient,
  createWidgetClient,
  type AdminClient,
  type AdminPaths,
  type ChannelClient,
  type ChannelPaths,
  type WidgetClient,
  type WidgetPaths,
} from "./clients";
export {
  isEndUserItem,
  readEndUserFrames,
  readFrames,
  type EndUserFrame,
  type EndUserItem,
  type Event,
  type StreamFrame,
} from "./stream";
