// 요청이 거절될 때의 다음 걸음(web-widget 명세 "요청이 거절될 때"). 경로마다 상태 코드를 위젯이 할 일로 옮긴다. 응답 전의
// 네트워크 실패는 상태 코드가 null 이다. 걸음을 밟는 것(기다리기, 다시 보내기, 대화에 넘기기)은 부르는 쪽이다.

import type { DecisionNotice } from "./conversation";

/** 시작과 이어 가기의 거절. 결말은 대화의 규칙(lib/conversation 의 `rejected`)이 상태 코드로 고른다. */
export type RunStep =
  /** 이어 가기의 첫 404. 1초 뒤 한 번 더 보낸다. */
  | "retry"
  /** 이어 가기의 둘째 404. 대화를 비우고 같은 요청을 시작으로 보낸다. */
  | "restart"
  /** 422, 429. 요청을 입력창으로 되돌린다. */
  | "return"
  /** 그 밖. 결말을 준다. */
  | "settle";

export function runStep(
  status: number | null,
  { continuing, retried }: { readonly continuing: boolean; readonly retried: boolean },
): RunStep {
  if (status === 404 && continuing) {
    return retried ? "restart" : "retry";
  }
  return status === 422 || status === 429 ? "return" : "settle";
}

/** 결정의 거절. */
export type DecisionStep =
  /** 첫 404. 1초 뒤 한 번 더 보낸다. */
  | { readonly kind: "retry" }
  /** 둘째 404. 그 승인 묻기를 더 받을 수 없다. */
  | { readonly kind: "expired" }
  /** 409. 일시정지 프레임 뒤부터 다시 구독해 다른 탭의 결정을 따라간다. */
  | { readonly kind: "follow" }
  /** 429. 결정의 기다림을 세우고 다시 결정을 받는다. */
  | { readonly kind: "limited" }
  /** 그 밖. 까닭을 들고 다시 결정을 받는다. */
  | { readonly kind: "refused"; readonly notice: DecisionNotice };

export function decisionStep(
  status: number | null,
  { retried }: { readonly retried: boolean },
): DecisionStep {
  switch (status) {
    case 404:
      return retried ? { kind: "expired" } : { kind: "retry" };
    case 409:
      return { kind: "follow" };
    case 429:
      return { kind: "limited" };
    case 401:
      return { kind: "refused", notice: "unauthorized" };
    default:
      return { kind: "refused", notice: "error" };
  }
}

/**
 * 결정의 409 뒤 다시 구독한 것의 거절. 401 은 로그인 정보를 받지 못한 것이고 그 밖은 처리하지 못한 것이다. 404 도
 * 그렇다. 구독 표의 404 행(1초 뒤 한 번 더)은 끊긴 실행에 다시 붙는 구독의 행이고, 여기서는 카드가 다시 결정을 받는다.
 */
export function followNotice(status: number | null): DecisionNotice {
  return status === 401 ? "unauthorized" : "error";
}

/** 구독의 거절. */
export type SubscriptionStep =
  /** 응답 전의 네트워크 실패. 끊긴 것과 같아 간격대로 다시 잇고 세지 않는다. */
  | "cut"
  /** 401. 다시 잇기를 멈춘다. */
  | "unauthorized"
  /** 첫 404. 1초 뒤 한 번 더. */
  | "retry"
  /** 둘째 404. 저장과 화면을 비운다. */
  | "vanished"
  /** 첫 409. `Last-Event-ID` 없이 곧바로 처음부터 구독한다. */
  | "from-start"
  /** 429. 기다릴 시간만큼 띠를 보인 뒤 다시 구독한다. */
  | "limited"
  /** 422, 500, 표 밖, 처음부터 구독한 뒤의 409. 간격대로 다시 구독하고, 세 번 거듭되면 멈춘다. */
  | "error";

export function subscriptionStep(
  status: number | null,
  { notFound, fromStart }: { readonly notFound: boolean; readonly fromStart: boolean },
): SubscriptionStep {
  switch (status) {
    case null:
      return "cut";
    case 401:
      return "unauthorized";
    case 404:
      return notFound ? "vanished" : "retry";
    case 409:
      return fromStart ? "error" : "from-start";
    case 429:
      return "limited";
    default:
      return "error";
  }
}

/** 구독의 처리하지 못한 거절이 이만큼 거듭되면 다시 잇기를 멈춘다. */
export const ERRORS_UNTIL_LOST = 3;

/** 이어 가기, 결정, 구독의 404 뒤 한 번 더 보내기까지 기다리는 시간. */
export const NOT_FOUND_RETRY_MS = 1_000;
