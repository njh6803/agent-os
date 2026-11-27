// 준비(stack.ts)가 테스트에 넘기는 것. 준비는 러너 프로세스에서 돌고, 테스트는 그 뒤에 띄워진 워커에서 돈다.
// 워커는 러너의 환경을 물려받으므로 준비가 환경변수에 적은 값을 테스트가 읽는다.

export const ADMIN_URL_ENV = "AGENT_OS_E2E_ADMIN_URL";
export const ACCOUNT_NAME_ENV = "AGENT_OS_E2E_ACCOUNT_NAME";
export const ACCOUNT_PASSWORD_ENV = "AGENT_OS_E2E_ACCOUNT_PASSWORD";
export const CHANNEL_TOKEN_ENV = "AGENT_OS_E2E_CHANNEL_TOKEN";
export const PLUGINS_ROOT_ENV = "AGENT_OS_E2E_PLUGINS_ROOT";

/**
 * 준비가 띄운 관리 화면의 주소, 준비가 만든 시스템 관리자 계정의 이름과 비밀번호, 그 serve 가 받는 채널 토큰, 그 serve 의
 * 플러그인 루트. 비밀번호와 토큰은 테스트만 아는 값이다. 켜고 끄기 흐름이 루트의 운영자 파일을 읽는다. 채널 토큰은 실행을
 * 시작하는 준비의 요청(`channel.ts`)이 싣는다. 관리 화면은 토큰 없이 로그인으로 들어가므로 화면에 넣는 토큰은 없다.
 */
export function stack(): {
  readonly adminUrl: string;
  readonly accountName: string;
  readonly accountPassword: string;
  readonly channelToken: string;
  readonly pluginsRoot: string;
} {
  const adminUrl = process.env[ADMIN_URL_ENV];
  const accountName = process.env[ACCOUNT_NAME_ENV];
  const accountPassword = process.env[ACCOUNT_PASSWORD_ENV];
  const channelToken = process.env[CHANNEL_TOKEN_ENV];
  const pluginsRoot = process.env[PLUGINS_ROOT_ENV];
  if (
    adminUrl === undefined ||
    accountName === undefined ||
    accountPassword === undefined ||
    channelToken === undefined ||
    pluginsRoot === undefined
  ) {
    throw new Error("e2e 의 준비(globalSetup)가 돌지 않았다. playwright.config.ts 로 띄운다");
  }
  return { adminUrl, accountName, accountPassword, channelToken, pluginsRoot };
}
