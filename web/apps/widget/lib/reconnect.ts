// 재접속(web-widget 명세 "재접속", ADR 0023). 실행 도중 연결이 끊기면 받은 것을 그대로 두고 같은 실행을 구독해 다시
// 붙는다.
//
// - 끊김은 마지막으로 받은 항목으로 가른다. 스트림이 끝나거나, 읽는 도중 네트워크가 끊기거나, 45초 동안 프레임도
//   keepalive 도 오지 않으면 그 실행에서 마지막으로 받은 항목을 본다. 이번 응답에서 받았든 앞 응답에서 받았든 같다.
//   결말이면 끝난 것, `paused` 면 결정을 기다리는 것, 그 밖이면 끊긴 것이다. `paused` 뒤에 닫힌 스트림을 끊김으로 세면
//   다시 이을 때마다 같은 `paused` 까지 받고 또 닫혀 끝없이 다시 잇는다.
// - 이 규칙 밖은 둘이다. 시작·이어 가기의 응답이 시작 항목 전에 끝난 것은 새 실행이 서지 않은 것이라 거절 표의 500
//   행이고, 결정의 응답이 `decided` 전에 끝난 것은 결정 행이다. 가르는 것은 부르는 쪽이다.
// - 서버는 15초마다 keepalive 를 보내므로 45초는 그것을 셋 놓친 것이다.
// - 다시 잇는 간격은 1, 2, 4, 8, 16초이고 그 뒤로는 30초마다이며 끝이 없다. 새 항목을 받으면 처음으로 돌아간다.

import type { EndUserItem } from "../api/runs";
import type { LimitWait } from "./limit";

/** 이만큼 아무것도 오지 않으면 끊긴 것으로 본다. */
export const SILENCE_MS = 45_000;

const DELAYS_MS = [1_000, 2_000, 4_000, 8_000, 16_000] as const;

const STEADY_MS = 30_000;

/** `attempt` 번째(0 부터) 다시 잇기까지 기다리는 밀리초. */
export function reconnectDelay(attempt: number): number {
  return DELAYS_MS[attempt] ?? STEADY_MS;
}

/** 스트림이 닫힌 뒤 그 실행이 어디에 있는가. */
export type Ending =
  /** 결말을 받았다. */
  | "done"
  /** 승인 묻기가 결정을 기다린다. 다시 잇지 않는다. */
  | "waiting"
  /** 결말 전에 끊겼다. 다시 잇는다. */
  | "cut";

/** 그 실행에서 마지막으로 받은 항목의 종류로 가른다. */
export function endingOf(last: EndUserItem["type"] | null): Ending {
  switch (last) {
    case "finished":
    case "failed":
    case "unfinished":
      return "done";
    case "paused":
      return "waiting";
    default:
      return "cut";
  }
}

/** 다시 잇는 중. 입력창 위 띠가 맨 앞에 선다. */
export type Reconnect =
  /** 끊겨 다시 잇고 있다. 띠는 진행 표시다. */
  | { readonly kind: "cut" }
  /** 구독이 상한(429)에 걸려 기다린다. 띠가 기다릴 시간을 보인다. */
  | { readonly kind: "limited"; readonly wait: LimitWait };

/** 끊긴 띠의 글. */
export const CUT_TEXT = "연결이 끊겨 다시 잇고 있습니다. 받은 내용은 그대로 있습니다.";
