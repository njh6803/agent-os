// 준비(stack.ts)가 시험에 넘기는 것. 준비는 러너 프로세스에서 돌고 시험은 그 뒤에 띄워진 워커에서 돈다. 워커는 러너의
// 환경을 물려받으므로 준비가 환경 변수에 적은 값을 시험이 읽는다(관리 화면 e2e 의 env.ts 와 같다).
//
// 아래 `LLM_ENV`·`TRACES_ENV` 는 거꾸로 실제 모델 e2e 를 감싸는 파이썬 시험(tests/test_widget_llm.py)이 러너에 주는
// 것이다(web-widget 티켓 11). 그 시험이 같은 이름을 따로 적는다.
// - `LLM_ENV` 가 `1` 이면 설정이 프로젝트 `llm` 을 세우고 준비가 저장소의 플러그인 루트를 함께 옮긴다.
// - `TRACES_ENV` 를 주면 serve 가 트레이스를 거기 남긴다. 없으면 준비의 작업 폴더이고 끝에 지운다.

export const LLM_ENV = "AGENT_OS_WIDGET_LLM";
export const TRACES_ENV = "AGENT_OS_WIDGET_TRACES";

export const WIDGET_ORIGIN_ENV = "AGENT_OS_E2E_WIDGET_ORIGIN";
export const SITE_ORIGIN_ENV = "AGENT_OS_E2E_SITE_ORIGIN";
export const OTHER_ORIGIN_ENV = "AGENT_OS_E2E_OTHER_ORIGIN";
export const GATES_ENV = "AGENT_OS_E2E_GATES";

/**
 * 위젯의 출처(같은 출처 중계의 주소), 허용 출처의 사이트 페이지, 허용 밖 출처의 사이트 페이지, 도구 에이전트가 둘째
 * 도구 앞에서 기다리는 문의 폴더. 문은 그 폴더에 요청과 같은 이름의 파일이 생기면 열린다(`plugins.ts`).
 */
export function stack(): {
  readonly widgetOrigin: string;
  readonly siteOrigin: string;
  readonly otherOrigin: string;
  readonly gates: string;
} {
  const widgetOrigin = process.env[WIDGET_ORIGIN_ENV];
  const siteOrigin = process.env[SITE_ORIGIN_ENV];
  const otherOrigin = process.env[OTHER_ORIGIN_ENV];
  const gates = process.env[GATES_ENV];
  if (
    widgetOrigin === undefined ||
    siteOrigin === undefined ||
    otherOrigin === undefined ||
    gates === undefined
  ) {
    throw new Error("위젯 e2e 의 준비(globalSetup)가 돌지 않았다. playwright.config.ts 로 띄운다");
  }
  return { widgetOrigin, siteOrigin, otherOrigin, gates };
}
