// 생성물이다. 손으로 고치지 않는다. widget-admin/openapi.json 에서 `pnpm -C web run generate:api-client` 로 만든다.
// openapi-typescript 의 출력 그대로다(web/tools/generate-api-client.ts).

export interface paths {
  "/health": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** Read Health */
    get: operations["read_health"];
    put?: never;
    post?: never;
    delete?: never;
    options?: never;
    head?: never;
    patch?: never;
    trace?: never;
  };
  "/widget-settings/{site}": {
    parameters: {
      query?: never;
      header?: never;
      path?: never;
      cookie?: never;
    };
    /** 사이트 하나의 위젯 설정을 읽는다 */
    get: operations["read_widget_settings"];
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
     * ErrorCode
     * @description 에러 봉투의 어휘. 표 안의 상태 코드와 1:1 이다.
     * @enum {string}
     */
    ErrorCode: "invalid_request" | "not_found" | "internal_error";
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
    /**
     * ExpiryNoticeStyle
     * @description 로그인 만료 안내를 보이는 모양.
     * @enum {string}
     */
    ExpiryNoticeStyle: "card" | "overlay" | "banner";
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
    /**
     * LoginPromptStyle
     * @description 로그인 전의 모양.
     * @enum {string}
     */
    LoginPromptStyle: "card" | "input_button" | "intro_button";
    /**
     * LogoutMethod
     * @description 로그아웃 주소를 부르는 방법.
     * @enum {string}
     */
    LogoutMethod: "background" | "new_window";
    /**
     * Mode
     * @description 위젯의 밝기.
     * @enum {string}
     */
    Mode: "light" | "dark";
    /**
     * NoticeFullStyle
     * @description 고지 전문을 보이는 모양.
     * @enum {string}
     */
    NoticeFullStyle: "inline" | "overlay" | "card";
    /**
     * Theme
     * @description 위젯의 색 이름.
     * @enum {string}
     */
    Theme: "guncheong" | "nokcheong" | "jacho" | "jjokbit";
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
    /**
     * WidgetSettings
     * @description 사이트의 위젯 설정. 값이 없으면 null, 예시 질문은 빈 목록, 밝기 스위치 숨기기는 거짓이다.
     */
    WidgetSettings: {
      /** Agent */
      agent: string | null;
      /** Contact Url */
      contact_url: string | null;
      /** Example Questions */
      example_questions: string[];
      expiry_notice_style: components["schemas"]["ExpiryNoticeStyle"] | null;
      /** Heading */
      heading: string | null;
      /** Hide Mode Switch */
      hide_mode_switch: boolean;
      /** Intro */
      intro: string | null;
      /** Login Label */
      login_label: string | null;
      login_prompt_style: components["schemas"]["LoginPromptStyle"] | null;
      /** Login Url */
      login_url: string | null;
      logout_method: components["schemas"]["LogoutMethod"] | null;
      /** Logout Url */
      logout_url: string | null;
      mode: components["schemas"]["Mode"] | null;
      /** Notice Full */
      notice_full: string | null;
      notice_full_style: components["schemas"]["NoticeFullStyle"] | null;
      /** Notice Summary */
      notice_summary: string | null;
      /** Placeholder */
      placeholder: string | null;
      /** Schema Version */
      schema_version: number;
      /** Tab Title */
      tab_title: string | null;
      theme: components["schemas"]["Theme"] | null;
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
    };
  };
  read_widget_settings: {
    parameters: {
      query?: never;
      header?: never;
      path: {
        site: string;
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
          "application/json": components["schemas"]["WidgetSettings"];
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
