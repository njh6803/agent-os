// 준비(stack.ts)가 시험에 넘기는 것. 준비는 러너 프로세스에서 돌고 시험은 그 뒤에 띄워진 워커에서 돈다. 워커는 러너의
// 환경을 물려받으므로 준비가 환경 변수에 적은 값을 시험이 읽는다. 적고 읽는 길과 트레이스를 읽는 길은 패키지
// `@agent-os/e2e-stack` 이 낸다(`publish`, `received`, `startedRuns`). 변수 이름은 앱이 정한다.
//
// 아래 `LLM_ENV`·`TRACES_ENV` 는 거꾸로 실제 모델 e2e 를 감싸는 파이썬 시험(tests/test_widget_llm.py)이 러너에 주는
// 것이다(web-widget 티켓 11). 그 시험이 같은 이름을 따로 적는다.
// - `LLM_ENV` 가 `1` 이면 설정이 프로젝트 `llm` 을 세우고 준비가 저장소의 플러그인 루트를 함께 옮긴다.
// - `TRACES_ENV` 를 주면 serve 가 트레이스를 거기 남긴다. 없으면 준비의 작업 폴더이고 끝에 지운다.
// 어느 쪽이든 serve 가 트레이스를 남긴 폴더는 `TRACES_DIR_ENV` 로 시험에 넘어간다(`traces()`).
// - `DOC_SEARCH_URL_ENV` 를 주면 준비가 옮긴 저장소 플러그인의 `doc-search` 연결 주소를 그 값으로 바꿔 쓴다. 파이썬 시험이
//   가짜 문서 검색 서버를 띄워 그 주소를 준다(기본 에이전트 `assistant` 사례가 쓴다). `DOC_SEARCH_AUTHORIZATION` 은 그
//   시험이 자식의 환경에 주고 serve 가 물려받는다.

import { received } from "@agent-os/e2e-stack";

export const LLM_ENV = "AGENT_OS_WIDGET_LLM";
export const TRACES_ENV = "AGENT_OS_WIDGET_TRACES";
export const DOC_SEARCH_URL_ENV = "AGENT_OS_WIDGET_DOC_SEARCH_URL";

export const WIDGET_ORIGIN_ENV = "AGENT_OS_E2E_WIDGET_ORIGIN";
export const SITE_ORIGIN_ENV = "AGENT_OS_E2E_SITE_ORIGIN";
export const OTHER_ORIGIN_ENV = "AGENT_OS_E2E_OTHER_ORIGIN";
export const GATES_ENV = "AGENT_OS_E2E_GATES";
export const TRACES_DIR_ENV = "AGENT_OS_E2E_TRACES";
export const CONTROL_ENV = "AGENT_OS_E2E_CONTROL";

/**
 * 준비가 사이트 파일에 적는 글자 수 상한. 서버의 기본값(20,000)과 다르게 두어, 입력창의 상한이 기본값이 아니라 값 파일에서
 * 온 것임을 시험이 가른다. 상수라 준비와 시험이 같은 값을 직접 읽는다(환경 변수로 넘기지 않는다).
 */
export const SITE_REQUEST_CHARS = 1_500;

/**
 * 준비가 위젯을 빌드할 때만 주는 사이트 파일(미끼)의 허용 출처와 상한. 띄울 때 주는 사이트 파일과 다르다. 빌드가 사이트 파일을
 * 읽어 값을 산출물에 굳히면 이 출처가 응답 머리에 박혀, 서비스 시작이 바꿀 자리를 찾지 못하고 준비가 멈춘다(widget-runtime-values
 * 티켓 02). 어느 사이트도 아닌 출처라 읽혀도 다른 사례를 가리지 않는다.
 */
export const DECOY_ORIGIN = "http://decoy.localhost:9";
export const DECOY_REQUEST_CHARS = 999;

/** 위젯을 다시 띄우는 사례가 사이트 파일에 적는 상한. 준비가 처음 준 상한과 서버의 기본값과 모두 다르다. */
export const RESTART_REQUEST_CHARS = 777;

/**
 * 위젯의 출처(같은 출처 중계의 주소), 허용 출처의 사이트 페이지, 허용 밖 출처의 사이트 페이지, 도구 에이전트가 둘째
 * 도구 앞에서 기다리는 문의 폴더. 문은 그 폴더에 요청과 같은 이름의 파일이 생기면 열린다(`@agent-os/e2e-stack` 의
 * `plugins.ts`).
 */
export function stack(): {
  readonly widgetOrigin: string;
  readonly siteOrigin: string;
  readonly otherOrigin: string;
  readonly gates: string;
} {
  return {
    widgetOrigin: received(WIDGET_ORIGIN_ENV),
    siteOrigin: received(SITE_ORIGIN_ENV),
    otherOrigin: received(OTHER_ORIGIN_ENV),
    gates: received(GATES_ENV),
  };
}

/** 위젯만 다시 띄우는 손잡이의 주소(`control.ts`). `helpers.ts` 의 `restartWidget` 이 부른다. */
export function control(): string {
  return received(CONTROL_ENV);
}

/** serve 가 트레이스를 남기는 폴더. 시험이 `startedRuns` 로 읽는다. */
export function traces(): string {
  return received(TRACES_DIR_ENV);
}
