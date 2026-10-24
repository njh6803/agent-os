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
// 실패 원인마다의 알림과 거절의 표는 티켓 07, 승인 묻기는 08, 재접속은 09 가 들인다. 그동안 실패(`failed`)와 끝내지
// 못함(`unfinished`)은 한 결말 `failed` 이고, 401 과 토큰을 받지 못한 것은 `unauthorized`, 그 밖의 거절과 결말 없이
// 끝난 스트림은 `rejected` 다.

import type { EndUserItem } from "../api/runs";

export interface ToolCall {
  readonly tool: string;
  readonly ok: boolean;
}

/** 교환의 결말. 도는 동안에는 없다. */
export type Outcome =
  | { readonly kind: "finished"; readonly output: string }
  | { readonly kind: "failed" }
  | { readonly kind: "paused" }
  | { readonly kind: "unauthorized" }
  | { readonly kind: "rejected" };

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
}

export type Action =
  | { readonly type: "sent"; readonly request: string }
  | { readonly type: "item"; readonly item: EndUserItem }
  /** 스트림이 끝났다. 결말 없이 끝났으면 거절과 같다(재접속은 티켓 09). */
  | { readonly type: "ended" }
  /** 실행이 받아들여지지 않았다. 상태 코드이고 응답 전의 네트워크 실패면 null 이다. */
  | { readonly type: "rejected"; readonly status: number | null }
  /** 토큰을 받지 못했다. 요청을 보내지 않는다. */
  | { readonly type: "no-token" }
  /** 새 대화. */
  | { readonly type: "reset" };

export const INITIAL: Conversation = {
  exchanges: [],
  continueFrom: null,
  announcements: [],
  nextId: 0,
};

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
    case "rejected":
      return settle(state, { kind: action.status === 401 ? "unauthorized" : "rejected" });
    case "ended":
      return settle(state, { kind: "rejected" });
    case "item":
      return applyItem(state, action.item);
  }
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
    case "finished": {
      const next = settle(state, { kind: "finished", output: item.output });
      return announce({ ...next, continueFrom: running.runId ?? state.continueFrom }, item.output);
    }
    case "failed":
    case "unfinished":
      return settle(state, { kind: "failed" });
  }
}

function withoutFirst(names: readonly string[], name: string): readonly string[] {
  const at = names.indexOf(name);
  return at === -1 ? names : [...names.slice(0, at), ...names.slice(at + 1)];
}

function announce(state: Conversation, text: string): Conversation {
  return { ...state, announcements: [...state.announcements, text] };
}
