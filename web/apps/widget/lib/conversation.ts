// 대화의 상태와 그것을 바꾸는 규칙(web-widget 명세 "대화 화면"). 화면이 보일 것만 들고, 스트림의 블록은 부르는 쪽
// (components/pages/useConversation)이 항목만 골라 넘긴다. 원문 블록과 keepalive 는 화면을 바꾸지 않는다.
//
// - 교환은 요청 하나와 그 응답이다. "다시 보내기"도 새 교환으로 덧붙고, 실패한 교환은 그대로 남는다.
// - 진행 표시의 이름표는 교환마다 부르는 중인 도구의 줄에서 나온다. `calling` 이 오면 그 `tools` 를 줄 끝에 붙이고,
//   `progress` 가 오면 줄에서 같은 이름의 첫 것을 뺀다. 거부한 도구도 `progress`(실패)로 빠지므로 `decided` 는 줄을
//   바꾸지 않는다. 모델 없이 부른 도구의 `progress` 는 뺄 것이 없어 그냥 지나간다.
// - 다음 요청은 마지막으로 끝난(`finished`) 실행의 이어 가기다. 실패한 교환은 이어 갈 실행을 바꾸지 않는다.
// - 화면 읽기 프로그램이 읽을 글(새 도구 줄, 끝난 출력)을 생긴 차례로 쌓는다. 진행 표시의 "부르는 중"은 쌓지 않는다.
//
// - 시작과 이어 가기의 거절은 상태 코드로 가른다(명세 "요청이 거절될 때"). 401·404·409 와 처리하지 못한 것은 요청을
//   남긴 채 결말이 되고, 422 와 429 는 요청을 입력창으로 되돌리므로 교환을 뺀다. 처리하지 못한 것이 결말을 받은 요청
//   없이 세 번째로 거듭되면 그 알림에 "새 대화"가 붙는다.
// - 이어 가기가 두 번 404 면 대화를 비우고 같은 요청의 교환 하나로 다시 시작한다. 다시 보내는 것은 부르는 쪽이다.
//
// 승인 묻기는 티켓 08, 재접속은 09 가 들인다. 그때까지 시작 항목 뒤에 결말 없이 끝난 스트림은 처리하지 못한 것이다.

import type { EndUserItem } from "../api/runs";

/** 실패 항목의 원인(ADR 0031). */
export type FailureCause = NonNullable<Extract<EndUserItem, { type: "failed" }>["cause"]>;

export interface ToolCall {
  readonly tool: string;
  readonly ok: boolean;
}

/** 교환의 결말. 도는 동안에는 없다. */
export type Outcome =
  | { readonly kind: "finished"; readonly output: string }
  /** 실패 항목. 원인은 받은 그대로다. 계약 밖의 값도 그대로 들고, 그리는 쪽이 모르는 값으로 다룬다. */
  | { readonly kind: "failed"; readonly cause: FailureCause | null; readonly runId: string }
  /** 끝내지 못함 항목. 그 항목은 실행 식별자를 들지 않아 `started` 의 것을 쓴다. */
  | { readonly kind: "unfinished"; readonly runId: string | null }
  | { readonly kind: "paused" }
  /** 401, 또는 토큰을 받지 못했다. */
  | { readonly kind: "unauthorized" }
  /** 시작의 404. 에이전트가 없거나 그 사이트의 열 에이전트 밖이다. */
  | { readonly kind: "not-found" }
  /** 409. 꺼진 에이전트와 끝나지 않은 앞 실행이 같은 코드다. */
  | { readonly kind: "unavailable" }
  /**
   * 처리하지 못했다. 500, 표 밖의 상태, 응답 전의 네트워크 실패, 결말 없이 끝난 스트림이다. 같은 대화에서 세 번째로
   * 거듭된 것이면 `offerNew` 가 참이고 알림에 "새 대화"가 붙는다.
   */
  | { readonly kind: "error"; readonly offerNew: boolean };

export interface Exchange {
  /** 대화 안에서 겹치지 않는 번호. 화면의 key 다. */
  readonly id: number;
  readonly request: string;
  /** `started` 항목이 준 실행 식별자. 오기 전에는 null 이다. */
  readonly runId: string | null;
  /** 모델이 요청했고 아직 끝나지 않은 도구. 이름표는 첫 이름이다. */
  readonly calling: readonly string[];
  /** 끝난 도구 호출. 온 차례다. */
  readonly tools: readonly ToolCall[];
  /** null 이면 아직 도는 중이다. */
  readonly outcome: Outcome | null;
}

export interface Conversation {
  readonly exchanges: readonly Exchange[];
  /** 다음 요청이 이어 갈 실행. 없으면 다음 요청은 시작이다. */
  readonly continueFrom: string | null;
  /** 숨긴 읽기 영역이 차례로 읽을 글. */
  readonly announcements: readonly string[];
  readonly nextId: number;
  /** 처리하지 못한 거절(`error`)이 결말을 받은 요청 없이 거듭된 수. */
  readonly errorStreak: number;
  /** 이어 갈 대화를 서버가 찾지 못해 새 대화로 다시 시작했다. 대화의 맨 위에 정보 알림이 선다. */
  readonly restarted: boolean;
}

export type Action =
  | { readonly type: "sent"; readonly request: string }
  | { readonly type: "item"; readonly item: EndUserItem }
  /**
   * 스트림이 끝났다. 결말 없이 끝났으면 처리하지 못한 것이다. 시작 항목 전이면 거절 표의 500 행이고, 뒤면 티켓 09 가
   * 재접속으로 갈라낼 때까지 같은 알림이다.
   */
  | { readonly type: "ended" }
  /** 실행이 받아들여지지 않았다. 상태 코드이고 응답 전의 네트워크 실패면 null 이다. */
  | { readonly type: "rejected"; readonly status: number | null }
  /** 토큰을 받지 못했다. 요청을 보내지 않는다. */
  | { readonly type: "no-token" }
  /**
   * 이어 가기가 두 번 404 였다. 화면과 기억을 비우고 도는 교환 하나만 남긴다. 그 요청은 시작으로 다시 간다(ADR 0024
   * 이력 2026-10-23).
   */
  | { readonly type: "restarted" }
  /** 새 대화. */
  | { readonly type: "reset" };

export const INITIAL: Conversation = {
  exchanges: [],
  continueFrom: null,
  announcements: [],
  nextId: 0,
  errorStreak: 0,
  restarted: false,
};

/** 이만큼째 거듭된 처리하지 못한 거절에 "새 대화"를 단다. */
const OFFER_NEW_AT = 3;

/** 대화가 어디에 있는가. 마지막 교환으로 가른다. */
export type Phase = "idle" | "running" | "paused";

export function phaseOf(conversation: Conversation): Phase {
  const last = conversation.exchanges.at(-1);
  if (last === undefined) {
    return "idle";
  }
  if (last.outcome === null) {
    return "running";
  }
  return last.outcome.kind === "paused" ? "paused" : "idle";
}

/** 진행 표시의 이름표. */
export function progressLabel(exchange: Exchange): string {
  const first = exchange.calling[0];
  return first === undefined ? "요청을 처리하고 있습니다." : `${first} 부르는 중`;
}

export function reduce(state: Conversation, action: Action): Conversation {
  switch (action.type) {
    case "reset":
      return INITIAL;
    case "sent":
      return {
        ...state,
        exchanges: [
          ...state.exchanges,
          {
            id: state.nextId,
            request: action.request,
            runId: null,
            calling: [],
            tools: [],
            outcome: null,
          },
        ],
        nextId: state.nextId + 1,
      };
    case "no-token":
      return settle(state, { kind: "unauthorized" });
    case "restarted": {
      const running = state.exchanges.at(-1);
      if (running?.outcome !== null) {
        return state;
      }
      return { ...INITIAL, exchanges: [running], nextId: state.nextId, restarted: true };
    }
    case "rejected":
      switch (action.status) {
        case 401:
          return settle(state, { kind: "unauthorized" });
        case 404:
          return settle(state, { kind: "not-found" });
        case 409:
          return settle(state, { kind: "unavailable" });
        // 요청을 입력창으로 되돌리므로 대화에서 뺀다. 되돌리는 것은 부르는 쪽이다.
        case 422:
        case 429:
          return withdraw(state);
        default:
          return settleError(state);
      }
    case "ended":
      return settleError(state);
    case "item":
      return applyItem(state, action.item);
  }
}

/** 도는 교환을 대화에서 뺀다. */
function withdraw(state: Conversation): Conversation {
  if (state.exchanges.at(-1)?.outcome !== null) {
    return state;
  }
  return { ...state, exchanges: state.exchanges.slice(0, -1) };
}

/** 처리하지 못한 것으로 끝낸다. 셈을 하나 올리고, 세 번째로 거듭된 것이면 "새 대화"를 단다. */
function settleError(state: Conversation): Conversation {
  if (state.exchanges.at(-1)?.outcome !== null) {
    return state;
  }
  const errorStreak = state.errorStreak + 1;
  return {
    ...settle(state, { kind: "error", offerNew: errorStreak >= OFFER_NEW_AT }),
    errorStreak,
  };
}

/** 도는 교환에 결말을 준다. 이미 결말이 있으면 그대로다. */
function settle(state: Conversation, outcome: Outcome): Conversation {
  return updateRunning(state, (exchange) => ({ ...exchange, calling: [], outcome }));
}

function updateRunning(
  state: Conversation,
  update: (exchange: Exchange) => Exchange,
): Conversation {
  const last = state.exchanges.at(-1);
  if (last?.outcome !== null) {
    return state;
  }
  return { ...state, exchanges: [...state.exchanges.slice(0, -1), update(last)] };
}

function applyItem(state: Conversation, item: EndUserItem): Conversation {
  const running = state.exchanges.at(-1);
  if (running?.outcome !== null) {
    return state;
  }
  switch (item.type) {
    case "started":
      return updateRunning(state, (exchange) => ({ ...exchange, runId: item.run_id }));
    case "calling":
      return updateRunning(state, (exchange) => ({
        ...exchange,
        calling: [...exchange.calling, ...item.tools],
      }));
    case "progress": {
      const next = updateRunning(state, (exchange) => ({
        ...exchange,
        calling: withoutFirst(exchange.calling, item.tool),
        tools: [...exchange.tools, { tool: item.tool, ok: item.ok }],
      }));
      return announce(next, `${item.tool} ${item.ok ? "성공" : "실패"}`);
    }
    case "decided":
      return state;
    case "paused":
      return settle(state, { kind: "paused" });
    // 결말을 받은 요청이 오면 처리하지 못한 거절의 셈이 처음으로 돌아간다.
    case "finished": {
      const next = settle(state, { kind: "finished", output: item.output });
      return announce(
        { ...next, continueFrom: running.runId ?? state.continueFrom, errorStreak: 0 },
        item.output,
      );
    }
    case "failed":
      return {
        ...settle(state, { kind: "failed", cause: item.cause, runId: item.run_id }),
        errorStreak: 0,
      };
    case "unfinished":
      return { ...settle(state, { kind: "unfinished", runId: running.runId }), errorStreak: 0 };
  }
}

function withoutFirst(names: readonly string[], name: string): readonly string[] {
  const at = names.indexOf(name);
  return at === -1 ? names : [...names.slice(0, at), ...names.slice(at + 1)];
}

function announce(state: Conversation, text: string): Conversation {
  return { ...state, announcements: [...state.announcements, text] };
}
