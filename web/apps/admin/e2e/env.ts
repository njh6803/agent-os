// 준비(stack.ts)가 테스트에 넘기는 것. 준비는 러너 프로세스에서 돌고, 테스트는 그 뒤에 띄워진 워커에서 돈다.
// 워커는 러너의 환경을 물려받으므로 준비가 환경변수에 적은 값을 테스트가 읽는다.

export const ADMIN_URL_ENV = "AGENT_OS_E2E_ADMIN_URL";
export const ADMIN_TOKEN_ENV = "AGENT_OS_E2E_ADMIN_TOKEN";
export const PLUGINS_ROOT_ENV = "AGENT_OS_E2E_PLUGINS_ROOT";

/**
 * 준비가 띄운 관리 화면의 주소, 그 serve 가 받는 관리 토큰, 그 serve 의 플러그인 루트. 토큰은 테스트만 아는 값이다.
 * 켜고 끄기 흐름이 루트의 운영자 파일을 읽는다.
 */
export function stack(): {
  readonly adminUrl: string;
  readonly adminToken: string;
  readonly pluginsRoot: string;
} {
  const adminUrl = process.env[ADMIN_URL_ENV];
  const adminToken = process.env[ADMIN_TOKEN_ENV];
  const pluginsRoot = process.env[PLUGINS_ROOT_ENV];
  if (adminUrl === undefined || adminToken === undefined || pluginsRoot === undefined) {
    throw new Error("e2e 의 준비(globalSetup)가 돌지 않았다. playwright.config.ts 로 띄운다");
  }
  return { adminUrl, adminToken, pluginsRoot };
}
