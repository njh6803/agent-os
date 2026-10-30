"use client";

// 실행 하나를 연 화면(web-admin 티켓 07). 주소의 조각(실행 식별자)을 라우트가 그대로 넘긴다.

import { type ReactNode, useId } from "react";
import type { Trace } from "../../api/traces";
import { useDecision } from "../../hooks/queries/approval";
import { usePlugins } from "../../hooks/queries/plugins";
import { useTrace } from "../../hooks/queries/traces";
import { useTokens } from "../../stores/tokens";
import { TextLink } from "../atoms/TextLink";
import { FailureNotice } from "../molecules/FailureNotice";
import { ScreenHeader } from "../molecules/ScreenHeader";
import { decisionPlaceStands, RunDecision } from "../organisms/RunDecision";
import { RunDetail } from "../organisms/RunDetail";
import { AdminScreen } from "./AdminScreen";
import { readOf } from "./read";
import { decodeSegment } from "./segment";

interface RunPageProps {
  /** 주소의 조각 그대로다. 퍼센트 인코딩이 풀리지 않았을 수 있다. */
  readonly runId: string;
}

export function RunPage({ runId }: RunPageProps) {
  const decoded = decodeSegment(runId);
  return (
    <AdminScreen current="runs">
      <div className="flex flex-col gap-6">
        <span className="self-start">
          <TextLink href="/runs">실행 목록</TextLink>
        </span>
        {decoded === null ? (
          <AddressFailure runId={runId} />
        ) : (
          <ConnectedRunDetail runId={decoded} />
        )}
      </div>
    </AdminScreen>
  );
}

/**
 * 주소를 풀지 못한 화면. 읽기 골격(`ReadSection`)을 지나지 않아도 화면 머리의 제목은 받은 조각 그대로다.
 */
function AddressFailure({ runId }: { readonly runId: string }) {
  const titleId = useId();
  return (
    <section aria-labelledby={titleId} className="flex flex-col gap-6">
      <ScreenHeader titleId={titleId} title={runId} />
      <FailureNotice message={`주소를 풀 수 없다: ${runId}`} requestId={null} />
    </section>
  );
}

/** 트레이스를 읽어 그린다. 주소를 푼 뒤, 관리 토큰이 받아들여진 뒤에만 서므로 읽기도 그때 시작한다. */
function ConnectedRunDetail({ runId }: { readonly runId: string }) {
  const trace = useTrace(runId);
  return (
    <RunDetail
      runId={runId}
      {...readOf(trace)}
      body={(shown, events) => <ConnectedRunDecision runId={runId} trace={shown} events={events} />}
    />
  );
}

/**
 * 결정 자리와 재개 스트림을 채운다. 트레이스 값의 갈래 안에 서므로, 다시 읽다 실패하면 결정의 훅도 함께 걷히고 보낸
 * 결정의 연결을 끊는다(`useDecision`). 꺼짐 미리 알림의 플러그인 목록은 결정 자리가 설 때만 읽는다.
 */
function ConnectedRunDecision({
  runId,
  trace,
  events,
}: {
  readonly runId: string;
  readonly trace: Trace;
  readonly events: ReactNode;
}) {
  const channelTokenEntered = useTokens((state) => state.channelToken !== null);
  const { busy, frames, cut, failure, decide } = useDecision(runId);
  const { data, error } = usePlugins({
    active: decisionPlaceStands(trace, { channelTokenEntered }),
  });
  return (
    <RunDecision
      trace={trace}
      events={events}
      channelTokenEntered={channelTokenEntered}
      busy={busy}
      frames={frames}
      cut={cut}
      failure={failure}
      onDecide={decide}
      plugins={{ data, error }}
    />
  );
}
