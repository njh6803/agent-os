// 대화 목록(화면 디자인 mk-conversation). 교환마다 오른쪽의 옅은 상자에 요청을, 그 아래에 응답을 쌓는다. 응답은 도는
// 동안 도구 줄과 진행 표시이고, 결말이 오면 도구 줄이 "도구 N개를 불렀습니다" 한 줄로 접히고 출력이나 알림이 선다.
//
// - 출력은 글자 그대로, 줄바꿈을 지키고 긴 낱말은 줄 끝에서 꺾어 그린다. 마크다운으로 그리지 않고 HTML 조각은 글자로
//   보인다(ADR 0024). React 가 글자를 글자로 넣는다.
// - 목록 자체에는 aria-live 나 role="log" 를 달지 않는다. 읽는 일은 화면의 숨긴 읽기 영역 하나가 맡는다(둘 다 읽히면
//   같은 줄이 두 번 들린다).
// - 이 부품이 스크롤하는 자리다. 새 내용이 오면, 최종 사용자가 대화의 끝을 보고 있었을 때만 끝으로 내린다. 스토리
//   시험이 잰다(jsdom 은 레이아웃을 하지 않는다).
// - 스크롤 자리는 이름 "대화"의 영역이고 포커스를 받는다. 도구 줄이 없는 교환만 있으면 안에 포커스 받는 것이 없어,
//   키보드로 스크롤할 길이 없다(axe 의 scrollable-region-focusable 이 스토리에서 잡았다). 그래서 포커스 차례는
//   "새 대화" → 이 영역 → 대화 안의 버튼 → 입력창 → 보내기다.
// - 승인 묻기의 카드(organisms/ApprovalCard)는 멈출 때까지 끝난 도구 줄 뒤에 서고, 결정 뒤의 도구 줄과 출력은 카드
//   아래에 이어진다(화면 디자인 mk-approval). 결말이 오면 카드 사이의 도구 줄도 저마다 한 줄로 접힌다.
// - 실패와 거절의 알림은 출력이 올 자리에 선다(organisms/FailureAlert). 이어 갈 대화를 서버가 찾지 못해 새 대화로 다시
//   시작했으면 맨 위에 정보 알림이 선다(화면 디자인 mk-rejection).
import { Alert, Icon, Progress } from "@agent-os/ui";
import { Fragment, useLayoutEffect, useRef, useState } from "react";
import { progressLabel, type Exchange, type Decision } from "../../lib/conversation";
import { ToolRow } from "../molecules/ToolRow";
import { ApprovalCard } from "./ApprovalCard";
import { FailureAlert } from "./FailureAlert";

export interface ConversationProps {
  readonly exchanges: readonly Exchange[];
  /** 이어 갈 대화를 서버가 찾지 못해 새 대화로 다시 시작했다. 맨 위에 정보 알림을 둔다. */
  readonly restarted: boolean;
  /** 그 교환의 요청을 같은 규칙으로 다시 보낸다. */
  readonly onRetry: (request: string) => void;
  /** "다시 보내기"를 막는다. 보내기와 같은 규칙이다. */
  readonly retryBlocked: boolean;
  /** 알림의 "새 대화". 위쪽 띠의 것과 같다. */
  readonly onNewConversation: () => void;
  readonly newConversationBlocked: boolean;
  /** 거부 사유의 글자 수 상한(코드 포인트). 입력창과 같다. */
  readonly reasonLimit: number;
  /** 결정의 상한(429)을 기다리는 중이라 결정 버튼을 막는다. */
  readonly decisionBlocked: boolean;
  /** 결정을 기다리는 승인 묻기에 결정을 보낸다. */
  readonly onDecide: (decision: Decision) => void;
}

// 끝에서 이만큼(px) 안이면 끝을 보고 있는 것으로 친다. 소수점 스크롤 위치의 오차를 받는다.
const BOTTOM_SLACK = 2;

export function Conversation({
  exchanges,
  restarted,
  onRetry,
  retryBlocked,
  onNewConversation,
  newConversationBlocked,
  reasonLimit,
  decisionBlocked,
  onDecide,
}: ConversationProps) {
  const scroller = useRef<HTMLDivElement>(null);
  const atBottom = useRef(true);

  useLayoutEffect(() => {
    const element = scroller.current;
    if (element !== null && atBottom.current) {
      element.scrollTop = element.scrollHeight;
    }
  });

  return (
    <div
      ref={scroller}
      onScroll={(event) => {
        const element = event.currentTarget;
        atBottom.current =
          element.scrollHeight - element.scrollTop - element.clientHeight <= BOTTOM_SLACK;
      }}
      role="region"
      aria-label="대화"
      tabIndex={0}
      className="flex min-h-0 flex-1 flex-col overflow-y-auto focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-focus-ring"
    >
      <ol className="mt-auto flex flex-col gap-4 p-4">
        {restarted ? (
          <li>
            <Alert title="이전 대화를 이어 갈 수 없어 새 대화로 시작합니다." />
          </li>
        ) : null}
        {exchanges.map((exchange) => (
          <ExchangeItems
            key={exchange.id}
            exchange={exchange}
            onRetry={onRetry}
            retryBlocked={retryBlocked}
            onNewConversation={onNewConversation}
            newConversationBlocked={newConversationBlocked}
            reasonLimit={reasonLimit}
            decisionBlocked={decisionBlocked}
            onDecide={onDecide}
          />
        ))}
      </ol>
    </div>
  );
}

function ExchangeItems({
  exchange,
  onRetry,
  retryBlocked,
  onNewConversation,
  newConversationBlocked,
  reasonLimit,
  decisionBlocked,
  onDecide,
}: {
  readonly exchange: Exchange;
} & Omit<ConversationProps, "exchanges" | "restarted">) {
  const { outcome, approvals } = exchange;
  const settled = outcome !== null && outcome.kind !== "paused";
  // 승인 묻기는 멈출 때까지 끝난 도구 줄 뒤에 선다. 도구 줄을 카드 자리마다 잘라 온 차례대로 그린다.
  const before = approvals.map((approval, index) =>
    exchange.tools.slice(approvals[index - 1]?.after ?? 0, approval.after),
  );
  const last = exchange.tools.slice(approvals.at(-1)?.after ?? 0);
  const tail =
    last.length > 0 ||
    outcome === null ||
    (outcome.kind !== "paused" && outcome.kind !== "expired");
  return (
    <>
      <li className="max-w-5/6 self-end rounded-l bg-bg-selected px-3 py-2 text-body wrap-anywhere whitespace-pre-wrap">
        <span className="sr-only">요청: </span>
        {exchange.request}
      </li>
      {approvals.map((approval, index) => {
        const tools = before[index] ?? [];
        return (
          <Fragment key={approval.pauseId}>
            {tools.length === 0 ? null : (
              <li className="flex flex-col gap-2">
                {settled ? (
                  <ToolSummary tools={tools} />
                ) : (
                  <ToolList tools={tools} running={null} />
                )}
              </li>
            )}
            <li className="flex flex-col gap-2">
              <ApprovalCard
                approval={approval}
                limit={reasonLimit}
                blocked={decisionBlocked}
                onDecide={onDecide}
              />
            </li>
          </Fragment>
        );
      })}
      {tail ? (
        <ExchangeTail
          exchange={exchange}
          tools={last}
          settled={settled}
          onRetry={onRetry}
          retryBlocked={retryBlocked}
          onNewConversation={onNewConversation}
          newConversationBlocked={newConversationBlocked}
        />
      ) : null}
    </>
  );
}

/** 교환의 끝. 마지막 카드 뒤의 도구 줄과 진행 표시, 그리고 출력이나 알림이다. */
function ExchangeTail({
  exchange,
  tools,
  settled,
  onRetry,
  retryBlocked,
  onNewConversation,
  newConversationBlocked,
}: {
  readonly exchange: Exchange;
  readonly tools: Exchange["tools"];
  readonly settled: boolean;
} & Pick<
  ConversationProps,
  "onRetry" | "retryBlocked" | "onNewConversation" | "newConversationBlocked"
>) {
  const { outcome } = exchange;
  return (
    <>
      <li className="flex flex-col gap-2">
        {settled ? (
          tools.length === 0 ? null : (
            <ToolSummary tools={tools} />
          )
        ) : (
          <ToolList tools={tools} running={outcome === null ? exchange : null} />
        )}
        {outcome?.kind === "finished" ? (
          <p className="text-body wrap-anywhere whitespace-pre-wrap">
            <span className="sr-only">출력: </span>
            {outcome.output}
          </p>
        ) : null}
        {outcome === null ? null : (
          <FailureAlert
            outcome={outcome}
            onRetry={() => {
              onRetry(exchange.request);
            }}
            retryBlocked={retryBlocked}
            onNewConversation={onNewConversation}
            newConversationBlocked={newConversationBlocked}
          />
        )}
      </li>
    </>
  );
}

/** 도는 동안(또는 승인을 기다리며 멈춘 동안)의 도구 줄. 도는 동안에는 끝에 진행 표시가 선다. */
function ToolList({
  tools,
  running,
}: {
  readonly tools: Exchange["tools"];
  readonly running: Exchange | null;
}) {
  if (tools.length === 0 && running === null) {
    return null;
  }
  return (
    <ul aria-label="부른 도구" className="flex flex-col gap-2">
      {tools.map((call, index) => (
        // 같은 도구가 여러 번 불릴 수 있고 줄은 뒤에만 붙어 자리가 곧 줄의 이름이다.
        <ToolRow key={index} tool={call.tool} ok={call.ok} />
      ))}
      {running === null ? null : (
        <li>
          <Progress label={progressLabel(running)} />
        </li>
      )}
    </ul>
  );
}

/** 결말 뒤의 접힌 도구 줄. 누르면 편다. */
function ToolSummary({ tools }: { readonly tools: Exchange["tools"] }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <>
      <button
        type="button"
        aria-expanded={expanded}
        onClick={() => {
          setExpanded(!expanded);
        }}
        className="flex min-h-6 cursor-pointer items-center gap-2 self-start rounded-s text-small text-text-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
      >
        <Icon name="wrench" size="14" />
        <span>{`도구 ${String(tools.length)}개를 불렀습니다`}</span>
      </button>
      {expanded ? (
        <ul aria-label="부른 도구" className="flex flex-col gap-2 pl-6">
          {tools.map((call, index) => (
            <ToolRow key={index} tool={call.tool} ok={call.ok} />
          ))}
        </ul>
      ) : null}
    </>
  );
}
