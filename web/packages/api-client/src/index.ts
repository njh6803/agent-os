// 생성 클라이언트 패키지의 입구(ADR 0021). web 코드가 파이썬 서버를 부를 때 지나는 자리다.

export type { components, paths } from "./generated/openapi";
export {
  createAdminClient,
  createChannelClient,
  type AdminClient,
  type AdminPaths,
  type ChannelClient,
  type ChannelPaths,
} from "./clients";
export { readFrames, type Event, type StreamFrame } from "./stream";
