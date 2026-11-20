// 단독 배포 e2e 의 환경 변수 이름. 입력은 시험을 돌리는 사람이 주고, 출력은 준비(stack.ts)가 시험(워커)에 넘긴다.
// 적고 읽는 길은 패키지 `@agent-os/e2e-stack` 이 낸다(`publish`, `received`).

import { delimiter } from "node:path";
import { received } from "@agent-os/e2e-stack";

// 입력. 이미지의 이름공간과 태그. 둘 다 주면 이미지를 짓지 않고 그 이미지로 띄운다(첫 판을 지켜보는 세션이 레지스트리에서
// 받은 이미지로 같은 시험을 돌린다. 명세 Testing Decisions 의 넷째). 둘 다 없으면 저장소에서 이미지 넷을 지어 지역 이름공간
// `LOCAL_NAMESPACE` 와 `LOCAL_VERSION` 으로 띄운다. 하나만 주면 던진다.
export const NAMESPACE_ENV = "AGENT_OS_STANDALONE_NAMESPACE";
export const VERSION_ENV = "AGENT_OS_STANDALONE_VERSION";
export const LOCAL_NAMESPACE = "agent-os-e2e";
export const LOCAL_VERSION = "0.1.0-rc.1";

// 입력. `1` 이면 프로젝트 `llm` 이 더해지고 준비가 모델 제공사의 API 키(`ANTHROPIC_API_KEY`)를 serve 의 환경 변수 파일에
// 싣는다. 키가 없으면 준비가 던진다. 감싸는 파이썬 시험은 두지 않았다(이 패키지의 명령으로 직접 켠다).
export const LLM_ENV = "AGENT_OS_STANDALONE_LLM";
export const API_KEY_ENV = "ANTHROPIC_API_KEY";

// 입력. `1` 이면 컨테이너마다 커널의 IPv6 를 끄는 덧씌움(`compose.no-ipv6.yaml`)을 얹어 IPv6 가 없는 환경에서도 배치가
// 서는지 본다. 사례는 그대로 돈다.
export const NO_IPV6_ENV = "AGENT_OS_STANDALONE_NO_IPV6";

// 출력.
export const PROJECT_ENV = "AGENT_OS_STANDALONE_E2E_PROJECT";
/** 준비가 compose 명령마다 더한 덧씌움 파일들(경로 구분자로 이은 글). 없으면 빈 글이다. */
export const FILES_ENV = "AGENT_OS_STANDALONE_E2E_FILES";
export const DIR_ENV = "AGENT_OS_STANDALONE_E2E_DIR";
export const VERSION_OUT_ENV = "AGENT_OS_STANDALONE_E2E_VERSION";
export const ADMIN_TOKEN_ENV = "AGENT_OS_STANDALONE_E2E_ADMIN_TOKEN";
export const FIXTURE_AGENT = "echo";
/** 위젯 미리보기 페이지의 첫 사이트 이름. 픽스처 에이전트를 연다. */
export const PREVIEW_SITE = "preview";
export const CALC_SITE = "calc";
export const CALC_AGENT = "calc";

/** 프록시가 443 으로 닿는 공개 출처. 인증서의 이름과 사이트 파일의 허용 출처, 위젯 미리보기 페이지의 공개 출처가 모두 이것이다. */
export const ORIGIN = "https://localhost";
/** 서버의 127.0.0.1 에만 발행하는 관리 화면. */
export const ADMIN_ORIGIN = "http://127.0.0.1:3000";

/** `docker compose up --wait` 가 모든 컨테이너를 기다리는 상한(초). 위젯이 뜰 때 사이트 파일로 빌드하는 시간이 대부분이다. */
export const UP_WAIT_SECONDS = 420;

export function deployment(): {
  readonly project: string;
  readonly dir: string;
  readonly files: readonly string[];
  readonly version: string;
  readonly adminToken: string;
} {
  const files = process.env[FILES_ENV] ?? "";
  return {
    project: received(PROJECT_ENV),
    dir: received(DIR_ENV),
    files: files === "" ? [] : files.split(delimiter),
    version: received(VERSION_OUT_ENV),
    adminToken: received(ADMIN_TOKEN_ENV),
  };
}
