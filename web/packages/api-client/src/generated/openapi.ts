// 생성물이다. 손으로 고치지 않는다. 루트 openapi.json 에서 `pnpm -C web run generate:api-client` 로 만든다.
// openapi-typescript 의 출력에서 재귀 Json 한 자리만 unknown 으로 바꿨다(web/tools/generate-api-client.ts).

export interface paths {
  "/end-user/runs": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** 서명한 최종 사용자로 실행 하나를 일으켜 그 항목을 생기는 대로 흘린다 */
    post: operations["start_end_user_run"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/end-user/runs/{run_id}/approval": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** 서명한 최종 사용자의 멈춘 실행에 결정 하나를 내고 결정 항목부터 흘린다 */
    post: operations["decide_end_user_approval"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/end-user/runs/{run_id}/subscription": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** 서명한 최종 사용자의 실행에 다시 붙어 놓친 항목부터 결말까지 흘린다 */
    get: operations["subscribe_end_user_run"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/health": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** 살아 있는지만 답한다 */
    get: operations["read_health"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/plugins": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** 등록된 플러그인 전부를 종류를 가리지 않고 켜짐과 함께 한 목록으로 */
    get: operations["list_plugins"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/plugins/{kind}/{name}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** 플러그인 하나를 켜짐과 매니페스트 통째로를 든 행으로 */
    get: operations["read_plugin"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/plugins/{kind}/{name}/enabled": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    /** 플러그인 하나를 켜거나 끈다 */
    put: operations["set_plugin_enabled"];
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/runs": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** 실행 하나를 일으켜 그 이벤트를 생기는 대로 흘린다 */
    post: operations["start_run"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/runs/{run_id}/approval": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** 멈춘 실행에 결정 하나를 내고 재개된 실행의 이벤트를 생기는 대로 흘린다 */
    post: operations["decide_approval"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/runs/{run_id}/continuation": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    get?: never;
    put?: never;
    /** 끝난 실행을 이어 가는 새 실행을 일으켜 그 이벤트를 생기는 대로 흘린다 */
    post: operations["continue_run"];
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/traces": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** 지나간 실행의 요약을 최근 것부터 한 쪽씩 */
    get: operations["list_traces"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/traces/{run_id}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** 한 실행의 이벤트 전부를 쓴 순서 그대로 */
    get: operations["read_trace"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
}
export type webhooks = Record<string, never>;
export interface components {
  schemas: {
    /**
     * ApprovalDenied
     * @description 사람이 거부했다. 사유는 거부에만 있다. 거부는 실행을 끝내지 않는다.
     */
    ApprovalDenied: {
      /** Approver */
      approver: string;
      /** Reason */
      reason: string;
      /** Run Id */
      run_id: string;
      /**
       * Ts
       * Format: date-time
       */
      ts: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "approval_denied";
    };
    /**
     * ApprovalGranted
     * @description 사람이 일시정지한 도구 호출을 허가했다. 승인자는 필수다(ADR 0009).
     */
    ApprovalGranted: {
      /** Approver */
      approver: string;
      /** Run Id */
      run_id: string;
      /**
       * Ts
       * Format: date-time
       */
      ts: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "approval_granted";
    };
    /**
     * Approve
     * @description 허가. 멈춘 도구 호출이 실제로 실행된다. 사유를 담을 자리가 없다.
     */
    Approve: {
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      decision: "approve";
      /**
       * Pause Index
       * @description 이 결정이 답하는 run_paused 이벤트가 트레이스 상세 events 에서 서는 0부터 센 인덱스. 최종 사용자 스트림에서는 일시정지 항목의 id 다. 지금의 일시정지가 아니면 409 다
       */
      pause_index: number;
    };
    /**
     * ConversationSummarized
     * @description 런타임이 앞 요약과 오래된 교환을 새 대화 요약으로 접었다. 에이전트가 내면 실행이 실패한다.
     */
    ConversationSummarized: {
      /** Input Tokens */
      input_tokens: number;
      /** Last Covered Run */
      last_covered_run: string;
      /** Model */
      model: string;
      /** Output Tokens */
      output_tokens: number;
      /** Run Id */
      run_id: string;
      /** Summary */
      summary: string;
      /**
       * Ts
       * Format: date-time
       */
      ts: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "conversation_summarized";
    };
    /**
     * DecidedItem
     * @description 결정이 기록됐다. 허가인지 거부인지와 거부의 사유를 든다.
     */
    DecidedItem: {
      /**
       * Decision
       * @enum {string}
       */
      decision: "approve" | "deny";
      /** Reason */
      reason: string | null;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "decided";
    };
    Decision: components["schemas"]["Approve"] | components["schemas"]["Deny"];
    /**
     * Deny
     * @description 거부. 도구를 부르지 않고 사유를 모델에 되돌린다. 사유는 비어 있을 수 없다.
     */
    Deny: {
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      decision: "deny";
      /**
       * Pause Index
       * @description 이 결정이 답하는 run_paused 이벤트가 트레이스 상세 events 에서 서는 0부터 센 인덱스. 최종 사용자 스트림에서는 일시정지 항목의 id 다. 지금의 일시정지가 아니면 409 다
       */
      pause_index: number;
      /** Reason */
      reason: string;
    };
    EndUserItem:
      | components["schemas"]["StartedItem"]
      | components["schemas"]["ProgressItem"]
      | components["schemas"]["PausedItem"]
      | components["schemas"]["DecidedItem"]
      | components["schemas"]["FinishedItem"]
      | components["schemas"]["FailedItem"]
      | components["schemas"]["UnfinishedItem"];
    /**
     * ErrorCode
     * @description 에러 봉투의 어휘. 상태 코드와 1:1 이다.
     * @enum {string}
     */
    ErrorCode:
      | "unauthorized"
      | "invalid_request"
      | "not_found"
      | "conflict"
      | "too_many_requests"
      | "internal_error";
    /**
     * ErrorEnvelope
     * @description 에러 응답의 모양. 성공 응답은 이것으로 감싸지 않는다.
     */
    ErrorEnvelope: {
      code: components["schemas"]["ErrorCode"];
      /** Message */
      message: string;
      /** Request Id */
      request_id: string;
      /** Violations */
      violations: components["schemas"]["Violation"][];
    };
    Event:
      | components["schemas"]["RunStarted"]
      | components["schemas"]["LlmCalled"]
      | components["schemas"]["ToolCalled"]
      | components["schemas"]["RunPaused"]
      | components["schemas"]["ApprovalGranted"]
      | components["schemas"]["ApprovalDenied"]
      | components["schemas"]["RunResumed"]
      | components["schemas"]["RunFinished"]
      | components["schemas"]["RunFailed"]
      | components["schemas"]["ConversationSummarized"];
    /**
     * FailedItem
     * @description 실행이 실패로 끝났다. 고정 문구와 실행 식별자를 든다.
     */
    FailedItem: {
      /** Message */
      message: string;
      /** Run Id */
      run_id: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "failed";
    };
    /**
     * FinishedItem
     * @description 실행이 출력을 내고 끝났다.
     */
    FinishedItem: {
      /** Output */
      output: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "finished";
    };
    /**
     * Health
     * @description 살아 있다는 것만 답한다. 내부 구성을 싣지 않는다.
     */
    Health: {
      /**
       * Status
       * @constant
       */
      status: "ok";
    };
    Json: unknown;
    /**
     * LlmCalled
     * @description 모델 호출 하나. 관찰용이면서 재개의 입력이다. prompt 는 루프의 첫 턴에만 담긴다.
     */
    LlmCalled: {
      /** Input Tokens */
      input_tokens: number;
      /** Model */
      model: string;
      /** Output Tokens */
      output_tokens: number;
      /**
       * Prompt
       * @default
       */
      prompt: string;
      /** Run Id */
      run_id: string;
      /**
       * Text
       * @default
       */
      text: string;
      /**
       * Tool Calls
       * @default []
       */
      tool_calls: components["schemas"]["ToolCall"][];
      /**
       * Ts
       * Format: date-time
       */
      ts: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "llm_called";
    };
    /**
     * McpServer
     * @description mcp 플러그인이 가리키는 stdio 서버의 실행 정보.
     */
    McpServer: {
      /**
       * Args
       * @default []
       */
      args: string[];
      /** Command */
      command: string;
      /**
       * Secret Args
       * @default {}
       */
      secret_args: {
        [key: string]: string[];
      };
    };
    /**
     * PausedItem
     * @description 승인을 기다리며 멈췄다. 멈춘 도구와 그 인자를 든다. 이 항목의 id 가 결정의 pause_index 다.
     */
    PausedItem: {
      /** Args */
      args: {
        [key: string]: components["schemas"]["Json"];
      };
      /** Tool */
      tool: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "paused";
    };
    /**
     * Plugin
     * @description 등록된 플러그인 하나. 종류와 이름과 켜짐, 그리고 매니페스트 통째로다.
     */
    Plugin: {
      /** Enabled */
      enabled: boolean;
      kind: components["schemas"]["PluginKind"];
      manifest: components["schemas"]["PluginManifest"];
      /** Name */
      name: string;
    };
    /**
     * PluginKind
     * @description 플러그인의 종류. 값은 넷이다.
     * @enum {string}
     */
    PluginKind: "agent" | "mcp" | "skill" | "model";
    /**
     * PluginManifest
     * @description 플러그인 하나의 매니페스트. plugin.toml 하나를 옮긴 것이다.
     */
    PluginManifest: {
      /** Conversation Limit */
      conversation_limit: number | null;
      /** Entrypoint */
      entrypoint: string | null;
      kind: components["schemas"]["PluginKind"];
      /**
       * Mcp
       * @default []
       */
      mcp: string[];
      /** Name */
      name: string;
      /**
       * Requires Approval
       * @default []
       */
      requires_approval: string[];
      /**
       * Schema Version
       * @constant
       */
      schema_version: "1";
      server: components["schemas"]["McpServer"] | null;
      /** Version */
      version: string;
    };
    /**
     * PluginPlaceholder
     * @description 매니페스트로 읽히지 않는 플러그인의 자리에 서는 표지. 종류와 이름과 켜짐과 이유를 든다.
     */
    PluginPlaceholder: {
      /** Enabled */
      enabled: boolean;
      kind: components["schemas"]["PluginKind"];
      /** Name */
      name: string;
      /** Reason */
      reason: string;
    };
    PluginRow: components["schemas"]["Plugin"] | components["schemas"]["PluginPlaceholder"];
    /**
     * ProgressItem
     * @description 도구 하나가 불렸다. 도구 이름과 성패만 든다.
     */
    ProgressItem: {
      /** Ok */
      ok: boolean;
      /** Tool */
      tool: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "progress";
    };
    /**
     * RunFailed
     * @description 실행이 실패로 끝났다. error 는 실패의 내용이다. 런타임이 낸다.
     */
    RunFailed: {
      /** Error */
      error: string;
      /** Run Id */
      run_id: string;
      /**
       * Ts
       * Format: date-time
       */
      ts: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "run_failed";
    };
    /**
     * RunFinished
     * @description 실행이 출력을 내고 끝났다. 에이전트가 마지막에 하나 낸다.
     */
    RunFinished: {
      /** Output */
      output: string;
      /** Run Id */
      run_id: string;
      /**
       * Ts
       * Format: date-time
       */
      ts: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "run_finished";
    };
    /**
     * RunPaused
     * @description 승인을 기다리며 멈췄다. 실패도 끝난 것도 아니다. 도구 하나만 담아 승인과 실행이 1:1이다.
     */
    RunPaused: {
      /** Args */
      args: {
        [key: string]: components["schemas"]["Json"];
      };
      /** Run Id */
      run_id: string;
      /** Tool */
      tool: string;
      /**
       * Ts
       * Format: date-time
       */
      ts: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "run_paused";
    };
    /**
     * RunResumed
     * @description 재생이 끝나고 실제 실행이 다시 시작된다. 재생 구간과 실제 구간의 경계다.
     */
    RunResumed: {
      /** Run Id */
      run_id: string;
      /**
       * Ts
       * Format: date-time
       */
      ts: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "run_resumed";
    };
    RunRow: components["schemas"]["RunSummary"] | components["schemas"]["UnreadableTrace"];
    /**
     * RunStarted
     * @description 실행이 시작됐다. 에이전트, 요청, 주체, 이어 간 앞 실행(없으면 null)을 든다. 런타임이 낸다.
     */
    RunStarted: {
      /** Agent */
      agent: string;
      /** Previous Run */
      previous_run: string | null;
      /** Principal */
      principal: string;
      /** Request */
      request: string;
      /** Run Id */
      run_id: string;
      /**
       * Ts
       * Format: date-time
       */
      ts: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "run_started";
    };
    /** @enum {string} */
    RunStatus: "paused" | "finished" | "failed" | "unfinished";
    /**
     * RunSummary
     * @description 목록에서 보이는 한 실행의 개요. 프롬프트와 토큰 수는 싣지 않는다.
     */
    RunSummary: {
      /** Agent */
      agent: string;
      /**
       * Last At
       * Format: date-time
       */
      last_at: string;
      /** Principal */
      principal: string;
      /** Run Id */
      run_id: string;
      schema_version: components["schemas"]["TraceSchemaVersion"];
      /**
       * Started At
       * Format: date-time
       */
      started_at: string;
      status: components["schemas"]["RunStatus"];
    };
    /**
     * ServerSentEvent
     * @description Represents a single Server-Sent Event.
     *
     *     When `yield`ed from a *path operation function* that uses
     *     `response_class=EventSourceResponse`, each `ServerSentEvent` is encoded
     *     into the [SSE wire format](https://html.spec.whatwg.org/multipage/server-sent-events.html#parsing-an-event-stream)
     *     (`text/event-stream`).
     *
     *     If you yield a plain object (dict, Pydantic model, etc.) instead, it is
     *     automatically JSON-encoded and sent as the `data:` field.
     *
     *     All `data` values **including plain strings** are JSON-serialized.
     *
     *     For example, `data="hello"` produces `data: "hello"` on the wire (with
     *     quotes).
     */
    ServerSentEvent: {
      /** Comment */
      comment?: string | null;
      /** Data */
      data?: unknown;
      /** Event */
      event?: string | null;
      /** Id */
      id?: string | null;
      /** Raw Data */
      raw_data?: string | null;
      /** Retry */
      retry?: number | null;
    };
    /**
     * SetEnabled
     * @description 켜짐 하나를 쓰는 요청. 거짓이면 끄고 참이면 켠다. 이미 그 상태여도 성공이다.
     */
    SetEnabled: {
      /** Enabled */
      enabled: boolean;
    };
    /**
     * StartRun
     * @description 실행 하나를 일으키는 요청. 등록된 에이전트의 이름과 요청 문자열이다.
     */
    StartRun: {
      /** Agent */
      agent: string;
      /** Request */
      request: string;
    };
    /**
     * StartedItem
     * @description 실행이 시작됐다. 구독과 결정에 쓸 실행 식별자를 든다.
     */
    StartedItem: {
      /** Run Id */
      run_id: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "started";
    };
    /**
     * ToolCall
     * @description 모델이 요청한 도구 호출 하나. 실행되기 전이다. 실행된 기록은 ToolCalled 다.
     */
    ToolCall: {
      /** Args */
      args: {
        [key: string]: components["schemas"]["Json"];
      };
      /** Id */
      id: string;
      /** Name */
      name: string;
    };
    /**
     * ToolCalled
     * @description 실행된 도구 호출 하나. ok 가 거짓이면 content 는 에러 내용이다(용어집 "도구 결과").
     */
    ToolCalled: {
      /**
       * Args
       * @default {}
       */
      args: {
        [key: string]: components["schemas"]["Json"];
      };
      /**
       * Content
       * @default
       */
      content: string;
      /** Ok */
      ok: boolean;
      /** Run Id */
      run_id: string;
      /** Tool */
      tool: string;
      /**
       * Ts
       * Format: date-time
       */
      ts: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "tool_called";
    };
    /**
     * Trace
     * @description 한 실행의 트레이스. 이벤트는 쓴 순서 그대로다.
     */
    Trace: {
      /** Events */
      events: components["schemas"]["TraceEvent"][];
      /** Run Id */
      run_id: string;
      schema_version: components["schemas"]["TraceSchemaVersion"];
    };
    TraceEvent:
      | components["schemas"]["RunStarted"]
      | components["schemas"]["LlmCalled"]
      | components["schemas"]["ToolCalled"]
      | components["schemas"]["RunPaused"]
      | components["schemas"]["ApprovalGranted"]
      | components["schemas"]["ApprovalDenied"]
      | components["schemas"]["RunResumed"]
      | components["schemas"]["RunFinished"]
      | components["schemas"]["RunFailed"]
      | components["schemas"]["ConversationSummarized"]
      | components["schemas"]["UnknownEvent"];
    /**
     * TracePage
     * @description 실행 목록의 한 쪽. 최근 실행이 먼저다. next_cursor 가 null 이면 더 없다.
     */
    TracePage: {
      /** Next Cursor */
      next_cursor: string | null;
      /** Runs */
      runs: components["schemas"]["RunRow"][];
    };
    /** @enum {string} */
    TraceSchemaVersion: "1" | "2" | "3";
    /**
     * UnfinishedItem
     * @description 실행이 끝내지 못하고 사라졌다. 구독이 닫을 때만 낸다.
     */
    UnfinishedItem: {
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "unfinished";
    };
    /**
     * UnknownEvent
     * @description 이 런타임이 모르는 종류의 이벤트. 원문 한 줄을 문자열 그대로 든다.
     */
    UnknownEvent: {
      /** Raw */
      raw: string;
      /**
       * @description discriminator enum property added by openapi-typescript
       * @enum {string}
       */
      type: "unknown";
    };
    /**
     * UnreadableTrace
     * @description 트레이스로 읽히지 않는 것의 표지. 실행 식별자와 이유를 든다. 실행 요약이 아니다.
     */
    UnreadableTrace: {
      /** Reason */
      reason: string;
      /** Run Id */
      run_id: string;
    };
    /**
     * Violation
     * @description 형식 오류 하나. field 는 `query.limit` 처럼 점으로 이은 경로 문자열이다.
     */
    Violation: {
      /** Field */
      field: string;
      /** Message */
      message: string;
    };
  };
  responses: never;
  parameters: never;
  requestBodies: never;
  headers: never;
  pathItems: never;
}
export type $defs = Record<string, never>;
export interface operations {
  start_end_user_run: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["StartRun"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "text/event-stream": unknown;
        };
      };
      /** @description 토큰이 없거나 틀리다 */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 찾는 것이 없다 */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 있지만 상태나 주체가 요청을 허락하지 않는다 */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 요청의 형식이 올바르지 않거나 request 가 그 사이트의 글자 수 상한을 넘었다. 글자는 코드 포인트(파이썬 len)로 세고 상한의 기본값은 20,000자다 */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 요청하는 쪽의 상한을 넘었다. Retry-After 의 초가 지난 뒤 다시 보낸다 */
      429: {
        headers: {
          /** @description 다시 보내도 되기까지의 초. 1 이상의 정수다 */
          "Retry-After"?: number;
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 서버가 요청을 처리하지 못했다 */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
    };
  };
  decide_end_user_approval: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        run_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["Decision"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "text/event-stream": unknown;
        };
      };
      /** @description 토큰이 없거나 틀리다 */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 찾는 것이 없다 */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 있지만 상태나 주체가 요청을 허락하지 않는다 */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 요청의 형식이 올바르지 않다 */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 요청하는 쪽의 상한을 넘었다. Retry-After 의 초가 지난 뒤 다시 보낸다 */
      429: {
        headers: {
          /** @description 다시 보내도 되기까지의 초. 1 이상의 정수다 */
          "Retry-After"?: number;
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 서버가 요청을 처리하지 못했다 */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
    };
  };
  subscribe_end_user_run: {
    parameters: {
      query?: never;
      header?: {
        "last-event-id"?: string | null;
      };
      path: {
        run_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "text/event-stream": unknown;
        };
      };
      /** @description 토큰이 없거나 틀리다 */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 찾는 것이 없다 */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 있지만 상태나 주체가 요청을 허락하지 않는다 */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 요청의 형식이 올바르지 않다 */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 요청하는 쪽의 상한을 넘었다. Retry-After 의 초가 지난 뒤 다시 보낸다 */
      429: {
        headers: {
          /** @description 다시 보내도 되기까지의 초. 1 이상의 정수다 */
          "Retry-After"?: number;
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 서버가 요청을 처리하지 못했다 */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
    };
  };
  read_health: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Health"];
        };
      };
      /** @description 서버가 요청을 처리하지 못했다 */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
    };
  };
  list_plugins: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["PluginRow"][];
        };
      };
      /** @description 토큰이 없거나 틀리다 */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 서버가 요청을 처리하지 못했다 */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
    };
  };
  read_plugin: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        kind: components["schemas"]["PluginKind"];
        name: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Plugin"];
        };
      };
      /** @description 토큰이 없거나 틀리다 */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 찾는 것이 없다 */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 요청의 형식이 올바르지 않다 */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 서버가 요청을 처리하지 못했다 */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
    };
  };
  set_plugin_enabled: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        kind: components["schemas"]["PluginKind"];
        name: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["SetEnabled"];
      };
    };
    responses: {
      /** @description Successful Response */
      204: {
        headers: {
          [name: string]: unknown;
        };
        content?: never;
      };
      /** @description 토큰이 없거나 틀리다 */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 찾는 것이 없다 */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 요청의 형식이 올바르지 않다 */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 서버가 요청을 처리하지 못했다 */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
    };
  };
  start_run: {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["StartRun"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "text/event-stream": unknown;
        };
      };
      /** @description 토큰이 없거나 틀리다 */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 찾는 것이 없다 */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 있지만 상태나 주체가 요청을 허락하지 않는다 */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 요청의 형식이 올바르지 않다 */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 서버가 요청을 처리하지 못했다 */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
    };
  };
  decide_approval: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        run_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["Decision"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "text/event-stream": unknown;
        };
      };
      /** @description 토큰이 없거나 틀리다 */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 찾는 것이 없다 */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 있지만 상태나 주체가 요청을 허락하지 않는다 */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 요청의 형식이 올바르지 않다 */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 서버가 요청을 처리하지 못했다 */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
    };
  };
  continue_run: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        run_id: string;
      };
      cookie?: never;
    };
    requestBody: {
      content: {
        "application/json": components["schemas"]["StartRun"];
      };
    };
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "text/event-stream": unknown;
        };
      };
      /** @description 토큰이 없거나 틀리다 */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 찾는 것이 없다 */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 있지만 상태나 주체가 요청을 허락하지 않는다 */
      409: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 요청의 형식이 올바르지 않다 */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 서버가 요청을 처리하지 못했다 */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
    };
  };
  list_traces: {
    parameters: {
      query?: {
        /** @description 없으면 전부다. paused 가 곧 멈춘 실행 목록이다 */
        status?: components["schemas"]["RunStatus"] | null;
        limit?: number;
        /** @description 앞 쪽의 next_cursor 를 그대로 넘긴다 */
        after?: string | null;
      };
      header?: never;
      path?: never;
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["TracePage"];
        };
      };
      /** @description 토큰이 없거나 틀리다 */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 요청의 형식이 올바르지 않다 */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 서버가 요청을 처리하지 못했다 */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
    };
  };
  read_trace: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        run_id: string;
      };
      cookie?: never;
    };
    requestBody?: never;
    responses: {
      /** @description Successful Response */
      200: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["Trace"];
        };
      };
      /** @description 토큰이 없거나 틀리다 */
      401: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 찾는 것이 없다 */
      404: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 요청의 형식이 올바르지 않다 */
      422: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
      /** @description 서버가 요청을 처리하지 못했다 */
      500: {
        headers: {
          [name: string]: unknown;
        };
        content: {
          "application/json": components["schemas"]["ErrorEnvelope"];
        };
      };
    };
  };
}
