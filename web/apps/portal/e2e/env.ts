// 준비(stack.ts)가 시험에 넘기는 것. 준비는 러너 프로세스에서 돌고 시험은 그 뒤에 띄워진 워커에서 돈다. 워커는 러너의 환경을
// 물려받으므로 준비가 환경 변수에 적은 값을 시험이 읽는다. 적고 읽는 길은 패키지 `@agent-os/e2e-stack` 이 낸다(`publish`,
// `received`). 변수 이름은 앱이 정한다.

import { readFileSync } from "node:fs";
import { received } from "@agent-os/e2e-stack";

export const PORTAL_ORIGIN_ENV = "AGENT_OS_PORTAL_E2E_ORIGIN";
export const OTHER_ORIGIN_ENV = "AGENT_OS_PORTAL_E2E_OTHER_ORIGIN";
export const SECOND_ORIGIN_ENV = "AGENT_OS_PORTAL_E2E_SECOND_ORIGIN";
export const TRACES_DIR_ENV = "AGENT_OS_PORTAL_E2E_TRACES";
export const PORTAL_OUTPUT_ENV = "AGENT_OS_PORTAL_E2E_OUTPUT";

/**
 * 질문 페이지의 출처(같은 출처 중계의 주소), 확인 끝점으로 폼을 보내는 다른 출처의 페이지, 08 의 둘째 인스턴스가 쓸 루프백
 * 출처(사이트 파일의 허용 출처에 들어 있다. 이 티켓의 시험은 쓰지 않는다).
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
