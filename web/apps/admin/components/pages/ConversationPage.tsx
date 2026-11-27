"use client";

// 대화 하나를 읽는 화면(admin-login 티켓 10). 주소의 조각(끝 실행의 식별자)을 라우트가 그대로 넘긴다. 끝 실행의 트레이스를
// 읽고 시작 이벤트의 앞 실행을 거슬러 읽어 첫 실행부터 한 번에 그린다. 끝 실행이 결말 없이 도는 동안은 그 실행 하나만
// 3초마다 다시 읽는다("도는 실행을 이어 보기"). 이 화면은 읽기만 한다. 보내기와 이어 가기와 승인은 쓰기 티켓이 더한다.

import { useId, useMemo } from "react";
import { hasOutcome, isPastTimeout, previousRunOf, turnOf } from "../../api/conversation";
import { useEarlierRuns, useEndRun } from "../../hooks/queries/conversation";
import { useMe } from "../../hooks/queries/session";
import { useTrace } from "../../hooks/queries/traces";
import { useRunQuery } from "../../hooks/useRunQuery";
import { FailureNotice } from "../molecules/FailureNotice";
import { ScreenHeader } from "../molecules/ScreenHeader";
import { Conversation, type ConversationData } from "../organisms/Conversation";
import { RunPanel } from "../organisms/RunPanel";
import { AdminScreen } from "./AdminScreen";
import { readOf } from "./read";
import { decodeSegment } from "./segment";

/** 서버가 알려 주기 전의 실행 제한 시간(초). `GET /auth/me` 가 읽히기 전에는 본문이 서지 않아 실제로는 쓰이지 않는다. */
const DEFAULT_TIMEOUT_SECONDS = 600;

interface ConversationPageProps {
  /** 주소의 조각 그대로다. 퍼센트 인코딩이 풀리지 않았을 수 있다. */
  readonly runId: string;
}

export function ConversationPage({ runId }: ConversationPageProps) {
  const decoded = decodeSegment(runId);
  return (
    <AdminScreen current="chat">
      {decoded === null ? (
        <AddressFailure runId={runId} />
      ) : (
        <ConnectedConversation runId={decoded} />
      )}
    </AdminScreen>
  );
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

/**
 * 대화를 읽어 그린다. 주소를 푼 뒤, 로그인한 계정을 읽은 뒤에만 서므로 읽기도 그때 시작한다.
 *
 * 끝 실행의 주기 읽기(`useEndRun`)는 이 부품이 건다. 인라인 꼴의 간격 함수는 이 부품이 다시 그려질 때마다 타이머를 새로
 * 거므로, 자주 바뀌는 상태(쓰기 티켓의 입력 칸)는 이 부품이 아니라 형제 부품이 들어야 한다. 그래서 패널의 읽기도 따로
 * 둔 부품(`ConnectedPanel`)이 건다. 여닫는 일은 클릭 한 번이라 이 부품이 다시 그려지는 것으로 충분하다.
 */
function ConnectedConversation({ runId }: { readonly runId: string }) {
  const timeoutSeconds = useMe().data?.run_timeout_seconds ?? DEFAULT_TIMEOUT_SECONDS;
  const end = useEndRun(runId, timeoutSeconds);
  const earlier = useEarlierRuns(
    end.data === undefined ? undefined : previousRunOf(end.data),
    runId,
  );
  const [panelRun, setPanelRun] = useRunQuery();

  const data = useMemo<ConversationData | undefined>(
    () =>
      end.data === undefined || earlier.data === undefined
        ? undefined
        : {
            turns: [...earlier.data.traces, end.data].map(turnOf),
            earlier: earlier.data.end,
          },
    [end.data, earlier.data],
  );

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

  return (
    <>
      <Conversation
        {...read}
        stale={stale}
        timeoutSeconds={timeoutSeconds}
        openRun={panelRun}
        onOpenRun={setPanelRun}
      />
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
