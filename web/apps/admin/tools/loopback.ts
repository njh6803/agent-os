/**
 * 관리 화면의 루프백 판정. 관리 화면은 브라우저가 든 토큰을 같은 출처에서 받아 파이썬 서버로 넘기는 중계다
 * (ADR 0019). 중계가 LAN 에 서거나 상류가 다른 호스트면 토큰이 그 사이를 평문으로 지난다(ADR 0011 의 CWE-319,
 * 2026-09-28 이력). 그래서 두 자리가 같은 루프백 판정을 지나고, 상류는 아래처럼 하나를 더 좁힌다.
 *
 * - 시작 래퍼(`start.ts`)의 바인딩 호스트. `next dev`·`next start` 는 인자 없이 `0.0.0.0` 과 `[::]` 에 선다.
 * - 설정 파일(`next.config.ts`)의 상류. `dev`·`build`·`start` 가 모두 그 파일을 읽어 한 자리에서 막힌다.
 *
 * 규칙은 `serve` 와 같다(`src/agent_os/main.py` 의 `LOOPBACK_HOSTS`). 허용 목록은 둘이고 문자열 그대로 비교한다.
 * `localhost` 는 `::1` 로도 풀릴 수 있어 루프백이라는 보장이 없다. 상류는 URL 파서가 먼저 정규화한 호스트를
 * 비교한다(`127.1` 은 `127.0.0.1` 이 되고, IPv6 는 대괄호를 벗긴다).
 *
 * 상류는 하나를 더 좁혀 `127.0.0.1` 만 받는다. Next 16.3.6 의 `rewrites` 는 목적지의 호스트 이름을 경로 틀로
 * 컴파일해, `[::1]` 은 빌드를 지나고 요청마다 `Missing parameter name` 으로 500 이었다(이 판정을 두기 전 실측, ADR
 * 0011 의 2026-09-30 이력). 그 자리의 `prepareDestination` 이 던지는 것은 `.scratch/web-admin/probes/admin_relay.mjs`
 * 가 다시 잰다. 요청 때 드러날 것을 설정을 읽을 때 막는다.
 *
 * 못 보는 것: 운영자가 `next` 를 직접 다른 인자로 띄우는 것(ADR 0019. `uvicorn` 을 직접 띄우는 것과 같은 자리).
 */

// 순서가 진단의 문장이 된다. serve 의 진단과 같은 순서다.
const LOOPBACK_HOSTS: readonly string[] = ["127.0.0.1", "::1"];

export const DEFAULT_HOST = "127.0.0.1";
// 관리 화면이 /api 를 넘기는 곳. serve 의 기본 주소다.
export const UPSTREAM_ENV = "AGENT_OS_UPSTREAM";
export const DEFAULT_UPSTREAM = "http://127.0.0.1:8000";
const UPSTREAM_HOST = "127.0.0.1";

function isLoopback(host: string): boolean {
  return LOOPBACK_HOSTS.includes(host);
}

function sshForward(port: string): string {
  return `ssh -L ${port}:127.0.0.1:${port} <서버>`;
}

/** 관리 화면이 설 호스트의 구성 오류. 루프백이면 null. `port` 는 SSH 안내에 싣는다. */
export function bindingProblem(host: string, port: string): string | null {
  if (isLoopback(host)) {
    return null;
  }
  return [
    `--hostname 은 루프백만 받는다(${LOOPBACK_HOSTS.join(", ")}). 받은 값: ${host}`,
    "  벗어나면 브라우저가 싣는 토큰이 관리 화면의 중계까지 LAN 위를 평문으로 지난다.",
    `  원격에서 보려면 SSH 포트 포워딩을 쓴다: ${sshForward(port)}`,
  ].join("\n");
}

/**
 * 상류 입력의 구성 오류. http 출처 하나이고 호스트가 `127.0.0.1` 이면 null.
 *
 * 출처(스킴, 호스트, 포트) 밖의 것(경로, 질의, 조각, 계정)은 받지 않는다. 조용히 버리면 운영자가 적은 것과 중계가
 * 넘기는 곳이 갈린다. 그 진단은 받은 값을 싣지 않는다. 계정의 비밀번호가 로그에 남는다(원칙 V).
 */
export function upstreamProblem(value: string): string | null {
  const url = URL.parse(value);
  if (url === null || url.protocol !== "http:" || url.href !== `${url.origin}/`) {
    return `${UPSTREAM_ENV} 는 http 출처 하나다(스킴, 호스트, 포트. 예: ${DEFAULT_UPSTREAM}). 경로, 질의, 계정은 받지 않는다.`;
  }
  const host = url.hostname.replace(/^\[(.*)\]$/, "$1");
  if (host === UPSTREAM_HOST) {
    return null;
  }
  // http 의 기본 포트(80)는 URL 이 비워 둔다.
  const port = url.port === "" ? "80" : url.port;
  if (isLoopback(host)) {
    return [
      `${UPSTREAM_ENV} 의 호스트는 ${UPSTREAM_HOST} 만 받는다. 받은 값: ${host}`,
      "  Next 의 rewrites 는 IPv6 주소로 넘기지 못한다(요청마다 500).",
      `  serve 를 --host ${UPSTREAM_HOST} 로 띄우고 ${UPSTREAM_ENV} 를 http://${UPSTREAM_HOST}:${port} 로 둔다.`,
    ].join("\n");
  }
  return [
    `${UPSTREAM_ENV} 의 호스트는 루프백 ${UPSTREAM_HOST} 만 받는다. 받은 값: ${host}`,
    "  벗어나면 중계가 브라우저의 토큰을 그 호스트까지 평문으로 넘긴다.",
    `  파이썬 서버가 다른 기계에 있으면 SSH 포트 포워딩으로 이 기계의 루프백에 가져온다: ${sshForward(port)}`,
  ].join("\n");
}
