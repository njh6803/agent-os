// 대화를 모는 비동기 일(web-widget 명세 "요청이 거절될 때", "재접속", "저장"). 시작·이어 가기(`run`), 결정(`decide`),
// 결정의 409 뒤 따라가기, 다시 잇기(`reconnect`), 저장한 대화 되돌리기(`restore`)가 같은 뼈대를 나눠 쓴다.
//
// 1. 임베드가 준 길(lib/connection)로 토큰을 새로 받아 그 묶음을 앞서 든 것과 견준다(`authorize`). 풀지 못한 토큰은 받지
//    못한 토큰과 같다. 묶음이 다르면 같은 탭에서 사이트 계정이 바뀐 것이다. 요청은 그 길의 기준 주소로 보낸다.
// 2. 요청 하나를 연다(`open`). 거절되면 그 상태 코드를 lib/rejection 의 걸음으로 옮겨 밟는다.
// 3. 받아들여지면 스트림을 끝까지 넘긴다(`pump`). 닫히거나 읽다 끊기거나 45초 동안 아무것도 오지 않으면 돌아온다.
// 4. 그 실행에서 마지막으로 받은 항목으로 갈라(lib/reconnect), 결말 전에 끊겼으면 다시 잇는다.
//
// 일 하나는 `Session` 하나를 받는다. 새 요청, 새 대화, 위젯이 걷히는 것이 그 신호를 끊고, 끊은 뒤에 온 결과는 부르는
// 쪽(useConversation)이 버린다.

import {
  RunRejected,
  sendDecision,
  sendRun,
  subscribeRun,
  type DecisionBody,
  type EndUserFrame,
  type EndUserItem,
} from "../../api/runs";
import type { Connection } from "../../lib/connection";
import type { Action } from "../../lib/conversation";
import { startWait } from "../../lib/limit";
import { endingOf, reconnectDelay, SILENCE_MS, type Reconnect } from "../../lib/reconnect";
import {
  decisionStep,
  ERRORS_UNTIL_LOST,
  followNotice,
  NOT_FOUND_RETRY_MS,
  runStep,
  subscriptionStep,
} from "../../lib/rejection";
import { bundleOf, conversationOf, type Bundle, type Saved } from "../../lib/storage";

type Frames = AsyncGenerator<EndUserFrame, void, undefined>;

/** 일 하나가 대화와 화면에 닿는 길. 끊긴 뒤의 부름은 아무것도 바꾸지 않는다. */
export interface Session {
  /** 최종 사용자 경로에 닿는 길. 토큰을 받고 요청을 보낸다. */
  readonly connection: Connection;
  readonly signal: AbortSignal;
  readonly dispatch: (action: Action) => void;
  /** 받은 토큰의 묶음이 앞서 든 묶음과 같은가. 앞서 든 것이 없으면(처음이면) 참이다. */
  readonly matches: (bundle: Bundle) => boolean;
  /** 받은 토큰의 묶음을 든다. 다음 견주기는 이것과 한다. */
  readonly hold: (bundle: Bundle) => void;
  /** 입력창 위 재접속 띠를 세우거나(값) 걷는다(null). */
  readonly reconnecting: (reconnect: Reconnect | null) => void;
  /** 앞 사람의 대화다. 열린 일을 끊고 저장과 화면을 비운다. */
  readonly forget: () => void;
}

type Authorized =
  | { readonly kind: "token"; readonly token: string; readonly switched: boolean }
  | { readonly kind: "no-token" }
  | { readonly kind: "aborted" };

/** 임베드가 준 길로 토큰을 새로 받아 묶음을 견준다. */
async function authorize(session: Session): Promise<Authorized> {
  const token = await session.connection.token();
  if (session.signal.aborted) {
    return { kind: "aborted" };
  }
  const bundle = token === null ? null : bundleOf(token);
  if (token === null || bundle === null) {
    return { kind: "no-token" };
  }
  const switched = !session.matches(bundle);
  session.hold(bundle);
  return { kind: "token", token, switched };
}

type Opened =
  | {
      readonly kind: "accepted";
      /** 스트림을 끝까지 넘긴다(`pump`). */
      readonly read: (onFrame: (frame: EndUserFrame) => void) => Promise<void>;
    }
  | { readonly kind: "rejected"; readonly rejected: RunRejected };

/**
 * 요청 하나를 연다. 연결은 일의 신호에 묶인 제 신호로 끊는다. 45초 무응답은 그 연결만 끊어야 하기 때문이다. 응답 전의
 * 네트워크 실패와 끊어서 난 에러는 상태 코드 없는 거절이다.
 */
async function open(
  signal: AbortSignal,
  send: (signal: AbortSignal) => Promise<Frames>,
): Promise<Opened> {
  const cut = new AbortController();
  const abort = () => {
    cut.abort();
  };
  signal.addEventListener("abort", abort, { once: true });
  const release = () => {
    signal.removeEventListener("abort", abort);
  };
  let frames: Frames;
  try {
    frames = await send(cut.signal);
  } catch (error) {
    release();
    return {
      kind: "rejected",
      rejected:
        error instanceof RunRejected ? error : new RunRejected(null, undefined, { cause: error }),
    };
  }
  return {
    kind: "accepted",
    read: async (onFrame) => {
      try {
        await pump(frames, cut, onFrame);
      } finally {
        release();
      }
    },
  };
}

/** `ms` 가 지나면 풀리는 약속과 그 타이머를 거두는 함수. */
function deadline(ms: number): { readonly passed: Promise<"silent">; readonly clear: () => void } {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const passed = new Promise<"silent">((resolve) => {
    timer = setTimeout(() => {
      resolve("silent");
    }, ms);
  });
  return {
    passed,
    clear: () => {
      clearTimeout(timer);
    },
  };
}

/**
 * 스트림을 끝까지 넘긴다. 닫히거나 읽다 끊기면 돌아오고, 45초 동안 프레임도 keepalive 도 오지 않으면 연결을 끊고 돌아온다.
 * 반복자의 `return()` 은 기다리는 중인 `next()` 를 풀지 못해, 끊긴 것과 45초를 다음 프레임과 겨뤄 안다.
 *
 * 45초가 지났을 때 타이머 콜백이 아니라 겨룸의 이어짐에서 끊는다. 화면 동작 시험의 가짜 네트워크(MSW 인터셉터) 위에서
 * 응답을 읽던 fetch 를 타이머 콜백 안에서 끊으면 Node 의 fetch(undici)가 단언(`assert(!this.aborted)`)에 걸렸고, 뒤의
 * 테스트가 같은 출처로 보낸 요청이 실패했다. 마이크로태스크 안에서 끊으면 둘 다 나지 않았고, 망가진 것이 MSW 가 아니라
 * undici 의 연결이라는 것도 갈랐다(.scratch/web-widget/probes/msw_abort_order.mjs 가 쟀다). 가짜 소켓이 타이머 콜백에서
 * 끊기면 close 를 error 보다 먼저 낸다는 까닭은 인터셉터의 소스를 읽은 어림이고 재지 않았다.
 */
async function pump(
  frames: Frames,
  cut: AbortController,
  onFrame: (frame: EndUserFrame) => void,
): Promise<void> {
  const stopped = new Promise<"stopped">((resolve) => {
    if (cut.signal.aborted) {
      resolve("stopped");
      return;
    }
    cut.signal.addEventListener(
      "abort",
      () => {
        resolve("stopped");
      },
      { once: true },
    );
  });
  try {
    for (;;) {
      const silence = deadline(SILENCE_MS);
      const next = await Promise.race([frames.next(), stopped, silence.passed]).finally(
        silence.clear,
      );
      if (next === "silent") {
        cut.abort();
        return;
      }
      if (next === "stopped" || next.done === true) {
        return;
      }
      onFrame(next.value);
    }
  } catch {
    // 읽다 끊긴 것도 닫힌 것과 같다. 마지막 항목으로 가르는 것은 부르는 쪽이다.
  }
}

/**
 * 한 실행에서 받은 것. 이번 응답에서 받았든 앞 응답에서 받았든 같은 실행이면 이어 센다. 읽기(`take`)는 항목을 대화에
 * 넘기고 여기 적기만 하며, 무엇을 받았는지는 부르는 쪽이 필드로 묻는다.
 */
class Received {
  /** `started` 가 준 실행 식별자. 시작·이어 가기에서는 그것이 오기 전에 null 이다. */
  runId: string | null;
  /** 마지막으로 받은 프레임의 `id`. 다시 이을 때의 `Last-Event-ID` 다. */
  lastId: number | null;
  /** 마지막으로 받은 항목의 종류. 끊김을 이것으로 가른다. */
  last: EndUserItem["type"] | null;
  /** 받은 항목의 수. */
  count = 0;
  /** 결정 항목을 받았다. */
  decided = false;

  constructor(runId: string | null, lastId: number | null, last: EndUserItem["type"] | null) {
    this.runId = runId;
    this.lastId = lastId;
    this.last = last;
  }

  /**
   * 응답 하나를 끝까지 읽어 항목을 대화에 넘긴다. `skipThrough` 까지의 프레임은 이미 받은 것이라 건너뛴다(409 뒤
   * 처음부터 다시 구독할 때). 원문 블록은 화면을 바꾸지 않지만 그 `id` 는 받은 것으로 센다.
   */
  async take(
    read: (onFrame: (frame: EndUserFrame) => void) => Promise<void>,
    dispatch: Session["dispatch"],
    skipThrough: number | null = null,
  ): Promise<void> {
    await read((frame) => {
      if (frame.kind === "keepalive" || frame.id === null) {
        return;
      }
      if (skipThrough !== null && frame.id <= skipThrough) {
        return;
      }
      this.lastId = frame.id;
      if (frame.kind !== "item") {
        return;
      }
      const { item } = frame;
      this.last = item.type;
      this.count += 1;
      this.decided ||= item.type === "decided";
      if (item.type === "started") {
        this.runId = item.run_id;
      }
      dispatch({ type: "item", id: frame.id, item });
    });
  }
}

/** 받은 것이 결말 전에 끊겼으면 다시 잇는다. */
async function carryOn(session: Session, runId: string, received: Received): Promise<void> {
  if (endingOf(received.last) === "cut") {
    await reconnect(session, runId, received, "after-cut");
  }
}

/**
 * 요청 하나를 보낸다. 이어 갈 실행이 있으면 이어 가기이고 없으면 시작이다. 이어 가기가 404 면 1초 뒤 한 번 더 보내고,
 * 또 404 면 화면과 기억을 비운 뒤 같은 요청을 시작으로 보낸다. 그 시작의 404 는 시작의 404 이고 더 보내지 않는다. 받은
 * 토큰의 묶음이 앞 사람의 것이면 앞 대화를 비우고 같은 요청을 시작으로 보낸다.
 *
 * 받아들여지면 끝까지 읽는다. 시작 항목 전에 끝났으면 처리하지 못한 것이고, 결말 전에 끊겼으면 다시 잇는다. `refuse` 는
 * 요청을 입력창으로 되돌리는 거절(422, 429)을 받는다.
 */
export async function run(
  session: Session,
  agent: string,
  request: string,
  continueFrom: string | null,
  refuse: (rejected: RunRejected) => void,
): Promise<void> {
  let target = continueFrom;
  let retried = false;
  for (;;) {
    const authorized = await authorize(session);
    if (authorized.kind === "aborted") {
      return;
    }
    if (authorized.kind === "no-token") {
      session.dispatch({ type: "no-token" });
      return;
    }
    if (authorized.switched) {
      session.dispatch({ type: "switched" });
      target = null;
    }
    const opened = await open(session.signal, (signal) =>
      sendRun(session.connection.baseUrl, authorized.token, agent, request, target, signal),
    );
    if (session.signal.aborted) {
      return;
    }
    if (opened.kind === "accepted") {
      const received = new Received(null, null, null);
      await received.take(opened.read, session.dispatch);
      if (received.runId === null) {
        session.dispatch({ type: "ended" });
        return;
      }
      await carryOn(session, received.runId, received);
      return;
    }
    const { rejected } = opened;
    switch (runStep(rejected.status, { continuing: target !== null, retried })) {
      case "retry":
        retried = true;
        // 기다리는 동안 끊겼으면 토큰을 다시 청하지 않는다.
        if (!(await sleep(NOT_FOUND_RETRY_MS, session.signal))) {
          return;
        }
        continue;
      case "restart":
        session.dispatch({ type: "restarted" });
        target = null;
        continue;
      case "return":
        refuse(rejected);
        break;
      case "settle":
        if (rejected.status === 404) {
          console.error(`위젯 에이전트 ${agent}: 서버가 찾지 못했다(404)`);
        }
        break;
    }
    session.dispatch({ type: "rejected", status: rejected.status });
    return;
  }
}

/**
 * 결정 하나를 보낸다(명세 "요청이 거절될 때"의 결정 행). 받아들여지면 결정 항목부터 실행을 이어 받는다. 결정 항목 전에
 * 끝나면 처리하지 못한 것이고, 그 뒤 결말 전에 끊겼으면 다시 잇는다. 거절은 lib/rejection 의 `decisionStep` 대로 간다.
 * 받은 토큰의 묶음이 앞 사람의 것이면 결정을 보내지 않고 저장과 화면을 비운다. `limited` 는 결정의 429 를 받는다.
 */
export async function decide(
  session: Session,
  runId: string,
  pauseId: number,
  body: DecisionBody,
  limited: (rejected: RunRejected) => void,
): Promise<void> {
  let retried = false;
  for (;;) {
    const authorized = await authorize(session);
    if (authorized.kind === "aborted") {
      return;
    }
    if (authorized.kind === "no-token") {
      session.dispatch({ type: "decision-refused", notice: "unauthorized" });
      return;
    }
    if (authorized.switched) {
      session.forget();
      return;
    }
    const opened = await open(session.signal, (signal) =>
      sendDecision(session.connection.baseUrl, authorized.token, runId, body, signal),
    );
    if (session.signal.aborted) {
      return;
    }
    if (opened.kind === "accepted") {
      const received = new Received(runId, pauseId, "paused");
      await received.take(opened.read, session.dispatch);
      if (!received.decided) {
        session.dispatch({ type: "decision-refused", notice: "error" });
        return;
      }
      await carryOn(session, runId, received);
      return;
    }
    const step = decisionStep(opened.rejected.status, { retried });
    switch (step.kind) {
      case "retry":
        retried = true;
        if (!(await sleep(NOT_FOUND_RETRY_MS, session.signal))) {
          return;
        }
        continue;
      case "expired":
        session.dispatch({ type: "expired" });
        return;
      case "follow":
        await follow(session, runId, pauseId);
        return;
      case "limited":
        limited(opened.rejected);
        session.dispatch({ type: "decision-refused", notice: null });
        return;
      case "refused":
        session.dispatch({ type: "decision-refused", notice: step.notice });
        return;
    }
  }
}

/**
 * 결정이 409 였다. 일시정지 프레임 뒤부터 그 실행을 다시 구독해, 새 항목이 오면 따라간다(다른 탭이 결정했다). 아무것도
 * 없이 닫히면 일시정지가 그대로라 보내지 못한 것이다. 토큰을 받지 못하면 로그인 정보를 받지 못한 것이고, 구독의 거절은
 * lib/rejection 의 `followNotice` 대로 간다. 따라간 뒤 결말 전에 끊겼으면 다시 잇는다.
 */
async function follow(session: Session, runId: string, pauseId: number): Promise<void> {
  const authorized = await authorize(session);
  if (authorized.kind === "aborted") {
    return;
  }
  if (authorized.kind === "no-token") {
    session.dispatch({ type: "decision-refused", notice: "unauthorized" });
    return;
  }
  if (authorized.switched) {
    session.forget();
    return;
  }
  const opened = await open(session.signal, (signal) =>
    subscribeRun(session.connection.baseUrl, authorized.token, runId, pauseId, signal),
  );
  if (session.signal.aborted) {
    return;
  }
  if (opened.kind === "rejected") {
    session.dispatch({ type: "decision-refused", notice: followNotice(opened.rejected.status) });
    return;
  }
  const received = new Received(runId, pauseId, "paused");
  await received.take(opened.read, session.dispatch);
  if (received.count === 0) {
    session.dispatch({ type: "decision-refused", notice: "conflict" });
  } else if (!received.decided) {
    session.dispatch({ type: "decision-refused", notice: "error" });
  } else {
    await carryOn(session, runId, received);
  }
}

/** 다시 붙는 때. 실행이 끊긴 뒤(`after-cut`)인가, 새로 고친 뒤(`after-reload`)인가. */
type Reattaching = "after-cut" | "after-reload";

/**
 * 끊긴 실행에 다시 붙는다(명세 "재접속"과 거절 표의 구독 행). 간격대로 기다린 뒤 마지막으로 받은 프레임 뒤부터 구독하고,
 * 받아들여지면 띠를 걷고 끝까지 읽어 다시 가른다. 새 항목을 받으면 간격이 처음으로 돌아간다. 새로 고친 뒤면 기다리지
 * 않고 `Last-Event-ID` 없이 처음부터 받는다. 그때는 띠를 세우지 않는다. 끊긴 것이 아니라 다시 붙는 중이다.
 */
async function reconnect(
  session: Session,
  runId: string,
  received: Received,
  when: Reattaching,
): Promise<void> {
  let attempt = 0;
  const backoff = () => {
    const ms = reconnectDelay(attempt);
    attempt += 1;
    session.reconnecting({ kind: "cut" });
    return ms;
  };
  let errors = 0;
  let notFound = false;
  // `Last-Event-ID` 없이 처음부터 받는다. 이미 받은 프레임은 건너뛴다.
  let replay = when === "after-reload";
  let delay = replay ? 0 : backoff();
  for (;;) {
    if (delay > 0 && !(await sleep(delay, session.signal))) {
      return;
    }
    const authorized = await authorize(session);
    if (authorized.kind === "aborted") {
      return;
    }
    if (authorized.kind === "no-token") {
      session.reconnecting(null);
      session.dispatch({ type: "no-token" });
      return;
    }
    if (authorized.switched) {
      session.forget();
      return;
    }
    const skipThrough = replay ? received.lastId : null;
    const opened = await open(session.signal, (signal) =>
      subscribeRun(
        session.connection.baseUrl,
        authorized.token,
        runId,
        replay ? null : received.lastId,
        signal,
      ),
    );
    if (session.signal.aborted) {
      return;
    }
    if (opened.kind === "accepted") {
      session.reconnecting(null);
      errors = 0;
      notFound = false;
      const before = received.count;
      await received.take(opened.read, session.dispatch, skipThrough);
      replay = false;
      if (endingOf(received.last) !== "cut") {
        return;
      }
      if (received.count > before) {
        attempt = 0;
      }
      delay = backoff();
      continue;
    }
    const { rejected } = opened;
    const step = subscriptionStep(rejected.status, { notFound, fromStart: replay });
    // 1초 뒤 한 번 더 보낸 것만 "또 404"다. 그 사이에 다른 거절이 끼면 다음 404 는 다시 첫 404 다.
    notFound = step === "retry";
    switch (step) {
      case "cut":
        delay = backoff();
        continue;
      case "unauthorized":
        session.reconnecting(null);
        session.dispatch({ type: "rejected", status: 401 });
        return;
      case "retry":
        delay = NOT_FOUND_RETRY_MS;
        continue;
      case "vanished":
        session.reconnecting(null);
        session.dispatch({ type: "vanished" });
        return;
      case "from-start":
        replay = true;
        delay = 0;
        continue;
      case "limited": {
        const wait = startWait(
          "subscribe",
          rejected.detail.limit,
          rejected.detail.retryAfter,
          Date.now(),
        );
        session.reconnecting({ kind: "limited", wait });
        // 서버는 1 이상만 보내지만 사이의 프록시가 0 을 보내면 기다림 없이 되풀이한다. 재접속의 첫 간격을 바닥으로 둔다.
        delay = Math.max(wait.seconds * 1_000, reconnectDelay(0));
        continue;
      }
      case "error":
        errors += 1;
        if (errors >= ERRORS_UNTIL_LOST) {
          session.reconnecting(null);
          session.dispatch({ type: "lost" });
          return;
        }
        delay = backoff();
        continue;
    }
  }
}

/** 되돌린 뒤 화면이 설 자리. */
export type Restored =
  /** 토큰을 받지 못했다. 저장을 지우지도 그리지도 않는다. */
  | "unauthorized"
  /** 그렸다. 묶음이 달랐으면 빈 화면이다. */
  | "ready";

/**
 * 저장한 대화를 되돌린다(명세 "저장"의 묶음 견주기). 먼저 토큰을 받아 그 묶음을 저장한 것과 견준 뒤에 그린다. 같으면
 * 대화를 되돌리고, 다시 붙을 실행이 있으면 `Last-Event-ID` 없이 처음부터 다시 붙는다. 다르면 앞 사람의 대화라 그리지
 * 않는다. 저장을 지우는 것은 빈 화면을 저장하는 부르는 쪽이다. `settled` 는 화면이 설 자리를 받는다.
 */
export async function restore(
  session: Session,
  saved: Saved,
  settled: (restored: Restored) => void,
): Promise<void> {
  session.hold(saved.bundle);
  const authorized = await authorize(session);
  if (authorized.kind === "aborted") {
    return;
  }
  if (authorized.kind === "no-token") {
    settled("unauthorized");
    return;
  }
  if (authorized.switched) {
    settled("ready");
    return;
  }
  session.dispatch({ type: "restored", conversation: conversationOf(saved) });
  settled("ready");
  if (saved.reattach !== null) {
    await reconnect(
      session,
      saved.reattach,
      new Received(saved.reattach, null, null),
      "after-reload",
    );
  }
}

/** 기다린다. 끝까지 기다렸으면 참이고, 끊으면 곧바로 거짓으로 돌아온다. */
function sleep(ms: number, signal: AbortSignal): Promise<boolean> {
  return new Promise((resolve) => {
    // 이미 끊긴 신호에는 abort 가 다시 오지 않는다.
    if (signal.aborted) {
      resolve(false);
      return;
    }
    const stop = () => {
      clearTimeout(timer);
      resolve(false);
    };
    const timer = setTimeout(() => {
      // 다시 잇는 동안 30초마다 잠들어, 떼지 않으면 일이 끝날 때까지 리스너가 쌓인다.
      signal.removeEventListener("abort", stop);
      resolve(true);
    }, ms);
    signal.addEventListener("abort", stop, { once: true });
  });
}
