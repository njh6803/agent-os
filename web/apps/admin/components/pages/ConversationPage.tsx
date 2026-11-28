"use client";

// 대화 하나를 읽고 보내고 결정하는 화면(admin-login 티켓 10·11). 주소의 조각(끝 실행의 식별자)을 라우트가 그대로 넘기고, 새 대화
// (`/chat/new`)는 조각이 없다. 끝 실행의 트레이스를 읽고 시작 이벤트의 앞 실행을 거슬러 읽어 첫 실행부터 한 번에 그린다. 끝 실행이
// 결말 없이 도는 동안은 그 실행 하나만 3초마다 다시 읽는다("도는 실행 이어 보기"). 입력 칸으로 보내거나 이어 가고, 일시정지의
// 승인 묻기에 결정하고, 응답 스트림은 받는 대로 그린다.

import { usePathname } from "next/navigation";
import { useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { useSWRConfig } from "swr";
import {
  earlierAfterSend,
  hasOutcome,
  isPastTimeout,
  previousRunOf,
  turnOf,
  type Turn,
} from "../../api/conversation";
import type { PluginRow } from "../../api/plugins";
import type { Trace } from "../../api/traces";
import { conversationKeys, useEarlierRuns, useEndRun } from "../../hooks/queries/conversation";
import { usePlugins } from "../../hooks/queries/plugins";
import { useRunStream, type RunStream } from "../../hooks/queries/run";
import { useKeepSignedIn, useMe } from "../../hooks/queries/session";
import { useTrace } from "../../hooks/queries/traces";
import { replaceAddress, useRunQuery } from "../../hooks/useRunQuery";
import { FailureNotice } from "../molecules/FailureNotice";
import { isEndUserPrincipal } from "../molecules/principal";
import { ScreenHeader } from "../molecules/ScreenHeader";
import { Composer, type AgentChoice, type ComposerState } from "../organisms/Composer";
import { Conversation, type ConversationData } from "../organisms/Conversation";
import { RunNotices } from "../organisms/RunNotices";
import { RunPanel } from "../organisms/RunPanel";
import { AdminScreen } from "./AdminScreen";
import { readOf } from "./read";
import { decodeSegment } from "./segment";

/** 서버가 알려 주기 전의 실행 제한 시간(초). `GET /auth/me` 가 읽히기 전에는 본문이 서지 않아 실제로는 쓰이지 않는다. */
const DEFAULT_TIMEOUT_SECONDS = 600;

interface ConversationPageProps {
  /** 주소의 조각 그대로다. 퍼센트 인코딩이 풀리지 않았을 수 있다. 새 대화는 null 이다. */
  readonly runId: string | null;
}

export function ConversationPage({ runId }: ConversationPageProps) {
  const decoded = runId === null ? null : decodeSegment(runId);
  return (
    <AdminScreen current="chat">
      {runId !== null && decoded === null ? (
        <AddressFailure runId={runId} />
      ) : (
        <ChatHost initialRun={decoded} />
      )}
    </AdminScreen>
  );
}

/** 주소의 조각에서 대화의 끝 실행을 푼다. 새 대화(`/chat/new`)와 대화 화면이 아닌 주소는 null 이다. */
function runOfPath(pathname: string | null): string | null {
  const match = pathname === null ? null : /^\/chat\/([^/]+)$/.exec(pathname);
  const segment = match?.[1];
  return segment === undefined || segment === "new" ? null : decodeSegment(segment);
}

/**
 * 대화 한 벌(`ChatSession`)이 주소와 어긋나지 않게 거는 부품. 시작 이벤트가 오면 이 화면이 스스로 주소를 바꾸는데
 * (`replaceAddress`), 라우터는 그 화면을 그대로 두므로, 그 뒤 "새 대화"나 뒤로 가기로 옮겨 가도 이전 대화가 남는다. 그래서
 * 이 화면이 바꾼 것이 아닌 주소가 오면 대화 한 벌을 새로 세워 그 주소의 대화를 처음부터 읽는다.
 */
function ChatHost({ initialRun }: { readonly initialRun: string | null }) {
  const pathname = usePathname();
  const own = useRef<string | null>(null);
  const seen = useRef(pathname);
  // 라우터가 저장해 둔 화면을 복원하면 속성(`initialRun`)은 처음 그릴 때의 것이라 지금 주소와 어긋날 수 있다. 그래서 주소에서
  // 읽은 실행을 먼저 따르고, 읽을 수 없을 때(라우터 밖의 시험은 주소가 없다)만 속성을 쓴다.
  const [start, setStart] = useState({
    generation: 0,
    run: runOfPath(pathname) ?? initialRun,
  });
  useEffect(() => {
    if (pathname === seen.current) {
      return;
    }
    seen.current = pathname;
    if (pathname === own.current) {
      return;
    }
    own.current = null;
    setStart((previous) => ({ generation: previous.generation + 1, run: runOfPath(pathname) }));
  }, [pathname]);
  const onAddress = useCallback((path: string) => {
    own.current = path;
    replaceAddress(path);
  }, []);
  return <ChatSession key={start.generation} initialRun={start.run} onAddress={onAddress} />;
}

/** 주소를 풀지 못한 화면. 읽기 골격을 지나지 않아도 화면 머리의 제목은 받은 조각 그대로다. */
function AddressFailure({ runId }: { readonly runId: string }) {
  const titleId = useId();
  return (
    <section aria-labelledby={titleId} className="flex flex-col gap-6">
      <ScreenHeader titleId={titleId} title={runId} />
      <FailureNotice message={`주소를 풀 수 없다: ${runId}`} requestId={null} />
    </section>
  );
}

/** 이 대화가 어느 실행에서 이어 간 것인가. 보낸 뒤 새 끝 실행의 앞 실행들을 채울 때(`earlierAfterSend`) 쓴다. */
interface Sent {
  readonly from: string | null;
}

/**
 * 대화를 읽어 그리고 보내기와 결정을 건다. 주소를 푼 뒤, 로그인한 계정을 읽은 뒤에만 서므로 읽기도 그때 시작한다.
 *
 * 끝 실행의 주기 읽기(`useEndRun`)는 이 부품이 건다. 인라인 꼴의 간격 함수는 이 부품이 다시 그려질 때마다 타이머를 새로 거므로,
 * 자주 바뀌는 상태는 이 부품이 들지 않는다. 입력 칸의 글과 고른 에이전트는 `Composer` 가, 거부 사유는 승인 묻기가 들어
 * 글을 쳐도 이 부품은 다시 그려지지 않는다. 응답 스트림의 프레임이 오면 다시 그려지지만 그때 끝 실행은 결말이 있어 주기 읽기가
 * 멈춰 있다. 패널을 여닫거나 목록과 계정을 다시 읽을 때도 다시 그려지지만 글을 칠 때마다 일어나는 일은 아니다. 패널의 읽기도
 * 따로 둔 부품(`ConnectedPanel`)이 건다.
 *
 * 새 대화나 이어 가기의 시작 이벤트가 오면 주소를 그 실행으로 바꾸고(`replaceAddress`), 스트림이 끝나 그 실행의 트레이스를 읽은
 * 뒤 끝 실행을 그 실행으로 옮긴다. 옮기기 전에 이미 읽은 앞 실행들을 새 끝 실행의 몫으로 채워 대화를 다시 거슬러 읽지 않는다.
 */
function ChatSession({
  initialRun,
  onAddress,
}: {
  readonly initialRun: string | null;
  /** 시작 이벤트가 오면 주소를 그 실행의 대화로 바꾸는 처리기. 호스트가 바꾼 주소를 기억한다. */
  readonly onAddress: (path: string) => void;
}) {
  const { mutate } = useSWRConfig();
  const timeoutSeconds = useMe().data?.run_timeout_seconds ?? DEFAULT_TIMEOUT_SECONDS;
  const [endRun, setEndRun] = useState<string | null>(initialRun);
  const end = useEndRun(endRun, timeoutSeconds);
  const earlier = useEarlierRuns(
    end.data === undefined ? undefined : previousRunOf(end.data),
    endRun,
  );
  const [panelRun, setPanelRun] = useRunQuery();
  const sent = useRef<Sent>({ from: null });

  const stream = useRunStream({
    onStarted: (runId) => {
      onAddress(`/chat/${encodeURIComponent(runId)}`);
    },
    onSettled: async (runId, kind) => {
      if (kind !== "send") {
        return;
      }
      const seeded = earlierAfterSend(sent.current.from, end.data, earlier.data);
      if (seeded !== null) {
        await mutate(conversationKeys.earlier(runId, sent.current.from), seeded, {
          revalidate: false,
        });
      }
      setEndRun(runId);
    },
  });
  useKeepSignedIn({ open: stream.busy });

  const baseTurns = useMemo<Turn[] | undefined>(
    () =>
      end.data === undefined || earlier.data === undefined
        ? undefined
        : [...earlier.data.traces, end.data].map(turnOf),
    [end.data, earlier.data],
  );
  const turns = useMemo(() => withLive(baseTurns, end.data, stream), [baseTurns, end.data, stream]);
  const data = useMemo<ConversationData | undefined>(() => {
    if (endRun === null) {
      return { turns: turns ?? [], earlier: "start" };
    }
    return turns === undefined || earlier.data === undefined
      ? undefined
      : { turns, earlier: earlier.data.end };
  }, [endRun, turns, earlier.data]);

  // 멈출 때가 지났는지는 그릴 때의 시계로 가른다. 마지막 읽기가 같은 트레이스를 가져와도 `isValidating` 이 바뀌어 다시
  // 그려지고, 그때 알림이 선다(`swr_poll` 결과 4c). `readOf` 가 `isValidating` 을 읽는다.
  const stale =
    end.data !== undefined &&
    !hasOutcome(end.data) &&
    isPastTimeout(end.data, timeoutSeconds, Date.now());

  const read = readOf({
    data,
    error: end.error ?? earlier.error,
    isValidating: end.isValidating || earlier.isValidating,
    mutate: () => Promise.all([end.mutate(), earlier.mutate()]),
  });

  const base = baseTurns?.at(-1);
  const endUser = baseTurns?.[0] !== undefined && isEndUserPrincipal(baseTurns[0].principal);
  const asking = !endUser && base?.approvals.some((approval) => approval.state === "waiting");
  // 에이전트 고르는 칸과 꺼짐 미리 알림이 같은 목록을 쓴다. 둘 다 서지 않으면 읽지 않는다.
  const plugins = usePlugins({ active: endRun === null || asking === true });

  const retryFrom = end.data === undefined ? null : previousRunOf(end.data);
  const send = useCallback(
    (from: string | null, agent: string, request: string) => {
      sent.current = { from };
      stream.send({ agent, request, from });
    },
    [stream],
  );

  return (
    <>
      <Conversation
        {...read}
        fresh={endRun === null}
        stale={stale}
        timeoutSeconds={timeoutSeconds}
        openRun={panelRun}
        onOpenRun={setPanelRun}
        actions={{
          canAct: !endUser,
          busy: stream.busy,
          invalid:
            stream.failure?.kind === "decide" && stream.failure.error.status === 422
              ? stream.failure.error
              : null,
          plugins: { data: plugins.data, error: plugins.error },
          onDecide: stream.decide,
          onRetry: () => {
            if (base !== undefined) {
              send(retryFrom, base.agent, base.request);
            }
          },
        }}
      />
      <RunNotices failure={stream.failure} cut={stream.cut} />
      {data === undefined || read.error !== undefined ? null : (
        <Composer
          state={composerOf({
            fresh: endRun === null,
            agents: agentsOf(plugins),
            base,
            endUser,
            busy: stream.busy,
            stale,
            retryFrom,
          })}
          onSend={(request, agent) => {
            if (endRun === null) {
              if (agent !== null) {
                send(null, agent, request);
              }
            } else if (base !== undefined) {
              send(base.outcome.kind === "failed" ? retryFrom : base.runId, base.agent, request);
            }
          }}
        />
      )}
      {panelRun === null ? null : (
        <ConnectedPanel
          runId={panelRun}
          onClose={() => {
            setPanelRun(null);
          }}
        />
      )}
    </>
  );
}

/**
 * 읽은 대화에 응답 스트림에서 받는 중인 것을 더한다. 보내기(시작·이어 가기)는 새 실행이라 끝에 한 차례를 붙이고, 결정은 끝 실행의
 * 이벤트 뒤에 받은 이벤트를 이어 붙여 그 차례를 다시 만든다. 시작 이벤트가 오기 전의 보내기는 보낸 요청만 말풍선에 둔다.
 * 받는 것이 없으면 읽은 대화 그대로다.
 */
function withLive(
  base: readonly Turn[] | undefined,
  end: Trace | undefined,
  stream: RunStream,
): Turn[] | undefined {
  const events = stream.frames.flatMap((frame) => (frame.kind === "event" ? [frame.event] : []));
  const first = events[0];
  const sending = stream.pending !== null || first?.type === "run_started";
  if (sending) {
    const started = events.find((event) => event.type === "run_started");
    const live: Turn =
      started === undefined
        ? pendingTurn(stream.pending ?? "", base?.at(-1)?.agent ?? "")
        : turnOf({ run_id: started.run_id, events });
    return [...(base ?? []), live];
  }
  if (base === undefined || end === undefined || events.length === 0) {
    return base === undefined ? undefined : [...base];
  }
  return [...base.slice(0, -1), turnOf({ run_id: end.run_id, events: [...end.events, ...events] })];
}

/** 시작 이벤트가 오기 전에 보낸 요청이 말풍선으로 서고 진행 표시가 "모델을 부르는 중"인 한 차례. */
function pendingTurn(request: string, agent: string): Turn {
  return {
    runId: "",
    agent,
    principal: "",
    requestingAccount: null,
    startedAt: "",
    request,
    tools: [],
    approvals: [],
    outcome: { kind: "running", step: "model" },
  };
}

/** 켜진 에이전트의 이름. 플러그인 목록의 에이전트 행 가운데 켜져 있고 매니페스트를 읽은 것이다. */
function agentsOf({
  data,
  error,
}: {
  readonly data: readonly PluginRow[] | undefined;
  readonly error: unknown;
}): AgentChoice {
  if (error !== undefined) {
    return { kind: "failed" };
  }
  if (data === undefined) {
    return { kind: "loading" };
  }
  const names = data
    .filter((row) => row.kind === "agent" && row.enabled && "manifest" in row)
    .map(({ name }) => name);
  return names.length === 0 ? { kind: "none" } : { kind: "some", names };
}

interface ComposerInput {
  readonly fresh: boolean;
  readonly agents: AgentChoice;
  /** 읽은 끝 실행의 차례. 새 대화이거나 아직 읽지 못했으면 undefined 다. */
  readonly base: Turn | undefined;
  readonly endUser: boolean;
  readonly busy: boolean;
  readonly stale: boolean;
  /** 끝 실행의 앞 실행. 실패한 끝 실행은 여기서 이어 간다. */
  readonly retryFrom: string | null;
}

/**
 * 입력 칸의 상태(admin-login 명세 "대화 화면"). 최종 사용자의 대화는 입력 칸이 없고, 보내는 동안과 결말 없음과 일시정지는 보내기만
 * 막는다. 끝남은 열려 있고, 실패는 그 앞의 실행에서 잇는다고 알린다.
 */
function composerOf(input: ComposerInput): ComposerState {
  const { fresh, agents, base, endUser, busy, stale, retryFrom } = input;
  const wait = { kind: "blocked", help: "실행이 끝나면 보낼 수 있다.", waitingTool: null } as const;
  if (endUser) {
    return { kind: "endUser" };
  }
  if (busy) {
    return wait;
  }
  if (fresh) {
    return { kind: "new", agents };
  }
  switch (base?.outcome.kind) {
    case "finished":
      return { kind: "open", help: null };
    case "failed":
      return {
        kind: "open",
        help:
          retryFrom === null
            ? "실패한 실행은 이어 가지 못해, 보내면 같은 에이전트로 새 대화를 시작한다."
            : "실패한 실행은 이어 가지 못해, 보내면 그 앞의 실행에서 이어 간다.",
      };
    case "paused":
      return {
        kind: "blocked",
        help: "승인이나 거부를 먼저 고른다.",
        waitingTool: base.approvals.find((approval) => approval.state === "waiting")?.tool ?? null,
      };
    default:
      return stale
        ? { kind: "blocked", help: "결말 없는 실행은 이어 갈 수 없다.", waitingTool: null }
        : wait;
  }
}

/** 실행 패널. 끝 실행이면 대화 화면의 읽기와 같은 열쇠라 SWR 의 같은 값을 쓴다. 주기 읽기는 걸지 않는다. */
function ConnectedPanel({
  runId,
  onClose,
}: {
  readonly runId: string;
  readonly onClose: () => void;
}) {
  const trace = useTrace(runId);
  return <RunPanel runId={runId} {...readOf(trace)} onClose={onClose} />;
}
