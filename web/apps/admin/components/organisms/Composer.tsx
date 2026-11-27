import { Alert, Icon, IconButton, TextField } from "@agent-os/ui";
import { useId, useState } from "react";
import { TextLink } from "../atoms/TextLink";
import { APPROVAL_ANCHOR } from "./ApprovalAsk";

/** 새 대화에서 고를 수 있는 에이전트를 읽은 결과. */
export type AgentChoice =
  | { readonly kind: "loading" }
  | { readonly kind: "failed" }
  | { readonly kind: "none" }
  | { readonly kind: "some"; readonly names: readonly string[] };

/**
 * 입력 칸의 상태(admin-login 명세 "대화 화면").
 * - `new`: 켜진 에이전트를 고르고 첫 요청을 쓴다.
 * - `open`: 끝 실행에서 이어 보낼 수 있다. 실패한 끝 실행이면 `help` 가 그 앞에서 잇는다고 알린다.
 * - `blocked`: 지금은 보낼 수 없다(도는 실행, 승인을 기다리는 일시정지, 끝맺지 못한 실행, 보내는 중). 글은 쓸 수 있다.
 * - `endUser`: 최종 사용자의 대화라 입력 칸 대신 한 줄이 선다.
 */
export type ComposerState =
  | { readonly kind: "new"; readonly agents: AgentChoice }
  | { readonly kind: "open"; readonly help: string | null }
  | { readonly kind: "blocked"; readonly help: string; readonly waitingTool: string | null }
  | { readonly kind: "endUser" };

interface ComposerProps {
  readonly state: ComposerState;
  /** 요청을 보낸다. 새 대화면 고른 에이전트를, 이어 가기면 null 을 함께 준다(에이전트는 끝 실행의 것이다). */
  readonly onSend: (request: string, agent: string | null) => void;
}

/**
 * 입력 칸(admin-login 명세 "대화 화면", 그림 ch-new·ch-a·ch-running). 대화 아래에 붙어 서고 요청과 보내기 버튼, 그리고 상태를
 * 말하는 도움말 한 줄이다. 막힌 동안에도 글은 쓸 수 있다(실행이 끝나면 보낼 초안). 보내기만 막는다.
 *
 * 쓰는 글과 고른 에이전트는 이 부품 안에 둔다. 글을 칠 때마다 대화를 읽는 부품이 다시 그려지지 않게 하려는 것이다. 주기 읽기의
 * 간격 함수는 그 부품이 그려질 때마다 타이머를 새로 걸기 때문이다("주기 읽기를 입력 칸과 떼어 둔다").
 */
export function Composer({ state, onSend }: ComposerProps) {
  if (state.kind === "endUser") {
    return (
      <Band>
        <p className="flex items-start gap-2 text-body text-text">
          <Icon name="info" size="16" />
          <span>최종 사용자의 대화라 이어 가거나 결정할 수 없다</span>
        </p>
      </Band>
    );
  }
  return <Field state={state} onSend={onSend} />;
}

/** 대화 아래에 붙는 띠. 위에 줄이 있고 바탕이 대화와 같다. */
function Band({ children }: { readonly children: React.ReactNode }) {
  return (
    <div className="sticky bottom-0 mt-6 flex flex-col gap-3 border-t border-border bg-bg pt-4">
      {children}
    </div>
  );
}

function Field({
  state,
  onSend,
}: {
  readonly state: Exclude<ComposerState, { kind: "endUser" }>;
  readonly onSend: ComposerProps["onSend"];
}) {
  const [text, setText] = useState("");
  const [picked, setPicked] = useState<string | null>(null);
  const agent = state.kind === "new" ? agentOf(state.agents, picked) : null;
  const request = text.trim();
  const sendable =
    request !== "" &&
    state.kind !== "blocked" &&
    (state.kind !== "new" || (state.agents.kind === "some" && agent !== null));

  return (
    <Band>
      {state.kind === "new" ? (
        <AgentPicker agents={state.agents} value={agent} onChange={setPicked} />
      ) : null}
      {state.kind === "blocked" && state.waitingTool !== null ? (
        <div className="flex flex-wrap items-center justify-between gap-2 rounded-m border border-border bg-bg-raised px-3 py-2 text-body">
          <span className="flex flex-wrap items-center gap-2">
            <span className="text-warning">
              <Icon name="circle-pause" size="16" />
            </span>
            승인을 기다린다:
            <span className="font-mono text-mono font-medium">{state.waitingTool}</span>
          </span>
          <TextLink href={`#${APPROVAL_ANCHOR}`}>승인 묻기로 가기</TextLink>
        </div>
      ) : null}
      <div className="flex items-end gap-2">
        <div className="min-w-0 flex-1">
          <TextField
            variant="multi"
            rows={2}
            label="요청"
            value={text}
            onChange={setText}
            placeholder={state.kind === "new" ? "에이전트에게 보낼 요청을 적는다" : undefined}
            help={helpOf(state)}
          />
        </div>
        <IconButton
          icon="send"
          label="보내기"
          variant="primary"
          disabled={!sendable}
          onClick={() => {
            onSend(request, agent);
            setText("");
          }}
        />
      </div>
    </Band>
  );
}

/** 고른 에이전트. 고르지 않았으면 첫 에이전트다. 고른 에이전트가 목록에서 꺼졌으면 첫 에이전트로 돌아간다. */
function agentOf(agents: AgentChoice, picked: string | null): string | null {
  if (agents.kind !== "some") {
    return null;
  }
  return picked !== null && agents.names.includes(picked) ? picked : (agents.names[0] ?? null);
}

function helpOf(state: Exclude<ComposerState, { kind: "endUser" }>): string | null {
  switch (state.kind) {
    case "new":
      return "한 대화에서는 처음 고른 에이전트로 이어 간다.";
    case "open":
      return state.help;
    case "blocked":
      return state.help;
  }
}

function AgentPicker({
  agents,
  value,
  onChange,
}: {
  readonly agents: AgentChoice;
  readonly value: string | null;
  readonly onChange: (agent: string) => void;
}) {
  const id = useId();
  switch (agents.kind) {
    case "loading":
      return <p className="text-small text-text-muted">켜진 에이전트를 불러오는 중</p>;
    case "failed":
      return <Alert tone="danger" title="플러그인 목록을 읽지 못해 에이전트를 고르지 못한다" />;
    case "none":
      return (
        <p className="flex flex-wrap items-center gap-2 text-body">
          <Icon name="circle-minus" size="16" />
          켜진 에이전트가 없다. <TextLink href="/">플러그인 목록</TextLink>
        </p>
      );
    case "some":
      return (
        <div className="flex flex-col gap-2">
          <label htmlFor={id} className="text-small font-medium">
            에이전트
          </label>
          <select
            id={id}
            value={value ?? ""}
            onChange={(event) => {
              onChange(event.target.value);
            }}
            className="h-control w-full max-w-form rounded-m border border-border-control bg-bg px-3 text-body text-text focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring"
          >
            {agents.names.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>
      );
  }
}
