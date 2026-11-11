// 준비(stack.ts)가 시험에 넘기는 것. 준비는 러너 프로세스에서 돌고 시험은 그 뒤에 띄워진 워커에서 돈다. 워커는 러너의 환경을
// 물려받으므로 준비가 환경 변수에 적은 값을 시험이 읽는다. 적고 읽는 길은 패키지 `@agent-os/e2e-stack` 이 낸다(`publish`,
// `received`). 변수 이름은 앱이 정한다.

// 아래 `LLM_ENV`·`TRACES_ENV` 는 거꾸로 실제 모델 e2e 를 감싸는 파이썬 시험(tests/test_portal_llm.py)이 러너에 주는
// 것이다(pilot-portal 티켓 09). 그 시험이 같은 이름을 따로 적는다.
// - `LLM_ENV` 가 `1` 이면 설정이 프로젝트 `llm` 을 세우고 준비가 저장소의 플러그인 루트를 함께 옮긴다.
// - `TRACES_ENV` 를 주면 serve 가 트레이스를 거기 남긴다. 없으면 준비의 작업 폴더이고 끝에 지운다.
// 어느 쪽이든 serve 가 트레이스를 남긴 폴더는 `TRACES_DIR_ENV` 로 시험에 넘어간다(`traces()`).

import { readFileSync } from "node:fs";
import { received } from "@agent-os/e2e-stack";

export const LLM_ENV = "AGENT_OS_PORTAL_LLM";
export const TRACES_ENV = "AGENT_OS_PORTAL_TRACES";

export const PORTAL_ORIGIN_ENV = "AGENT_OS_PORTAL_E2E_ORIGIN";
export const OTHER_ORIGIN_ENV = "AGENT_OS_PORTAL_E2E_OTHER_ORIGIN";
export const SECOND_ORIGIN_ENV = "AGENT_OS_PORTAL_E2E_SECOND_ORIGIN";
export const TRACES_DIR_ENV = "AGENT_OS_PORTAL_E2E_TRACES";
export const PORTAL_OUTPUT_ENV = "AGENT_OS_PORTAL_E2E_OUTPUT";

/**
 * 질문 페이지의 출처(같은 출처 중계의 주소), 확인 끝점으로 폼을 보내는 다른 출처의 페이지, 설정에 사이트 하나만 적은 둘째
 * 질문 페이지의 루프백 출처(사이트 파일의 허용 출처에 들어 있다. 중계를 거치지 않는다).
 */
export function stack(): {
  readonly portalOrigin: string;
  readonly otherOrigin: string;
  readonly secondOrigin: string;
} {
  return {
    portalOrigin: received(PORTAL_ORIGIN_ENV),
    otherOrigin: received(OTHER_ORIGIN_ENV),
    secondOrigin: received(SECOND_ORIGIN_ENV),
  };
}

/** serve 가 트레이스를 남기는 폴더. 시험이 `startedRuns` 로 읽는다. */
export function traces(): string {
  return received(TRACES_DIR_ENV);
}

/**
 * 지금까지 질문 페이지 프로세스가 stdout 과 stderr 에 낸 글. 준비가 프로세스의 출력을 받는 대로 파일에 이어 쓰므로 시험이 도는
 * 중에도 읽는다. 러너가 출력을 받아 쓰기까지 짧은 틈이 있어, 방금 한 동작의 출력은 조금 뒤에 실린다.
 */
export function portalOutput(): string {
  return readFileSync(received(PORTAL_OUTPUT_ENV), "utf-8");
}
