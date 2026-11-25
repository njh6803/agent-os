/**
 * 관리 화면의 루프백 판정. 관리 화면은 브라우저가 든 토큰을 같은 출처에서 받아 파이썬 서버로 넘기는 중계다
 * (ADR 0019). 중계가 LAN 에 서거나 상류가 다른 호스트면 토큰이 그 사이를 평문으로 지난다(ADR 0011 의 CWE-319,
 * 2026-09-28 이력). 그래서 두 자리가 같은 루프백 판정을 지나고, 상류는 아래처럼 하나를 더 좁힌다.
 *
 * - 시작 래퍼(`start.ts`)의 바인딩 호스트. `next dev`·`next start` 는 인자 없이 `0.0.0.0` 과 `[::]` 에 선다.
 * - 설정 파일(`next.config.ts`)의 상류. `dev`·`build`·`start` 가 모두 그 파일을 읽어 한 자리에서 막힌다.
 *
 * 규칙은 `serve` 와 같다(`src/agent_os/main.py` 의 `LOOPBACK_HOSTS`). 위젯의 시작 래퍼(`web/apps/widget/tools/start.ts`)
 * 와 위젯 미리보기 페이지의 설정 읽기(`web/apps/portal/server/config.ts`)도 같은 목록과 같은 예외를 따로 든다. 앱 사이 import 는
 * 층 경계가 막아, 바꾸면 다섯을 함께 고치고 같은 판정을 내는지는 사례 표가 잠근다(web-widget 티켓 03, pilot-portal 티켓 04,
 * release-image 티켓 03). 컨테이너 네트워크 예외는 아래 `ContainerNetwork` 가 설명한다.
 * 허용 목록은 둘이고 문자열 그대로 비교한다.
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

import { existsSync } from "node:fs";

// 순서가 진단의 문장이 된다. serve 의 진단과 같은 순서다.
const LOOPBACK_HOSTS: readonly string[] = ["127.0.0.1", "::1"];

export const DEFAULT_HOST = "127.0.0.1";
// 관리 화면이 /api 를 넘기는 곳(상류)을 받는 환경 변수.
export const UPSTREAM_ENV = "AGENT_OS_UPSTREAM";
// 상류를 주지 않았을 때. serve 의 기본 주소다.
export const DEFAULT_UPSTREAM = "http://127.0.0.1:8000";
const UPSTREAM_HOST = "127.0.0.1";

/**
 * 루프백 규칙의 예외(ADR 0056 결정 "루프백 규칙의 예외"). 둘이 함께 있을 때만 켜진다. 표지 파일은 이미지를 지을 때 root 소유로
 * 굽고(앱 사용자는 만들 수 없고 개발 PC 에는 그 경로가 없다) "이미지 안에서만"을, compose 가 주는 환경 변수 `=1` 이
 * "명시적"을 맡는다. 켜지면 듣는 주소로 `0.0.0.0` 하나가, 상류의 호스트로 compose 의 서비스 이름 `serve` 하나가 늘 뿐이다.
 * 같은 규칙을 `serve`, 위젯, 위젯 미리보기 페이지가 따로 들고, 사례 표(`tests/fixtures/container_network/cases.json`)가
 * 다섯이 같은 판정을 내는지 잠근다.
 */
export const IMAGE_MARKER = "/etc/agent-os/image";
export const CONTAINER_NETWORK_ENV = "AGENT_OS_CONTAINER_NETWORK";
const CONTAINER_HOST = "0.0.0.0";
const UPSTREAM_SERVICE = "serve";

/** 예외를 켜는 두 입력. 판정은 이 값만 보고 파일도 환경도 읽지 않는다. `env` 가 undefined 이면 환경 변수가 없다. */
export interface ContainerNetwork {
  readonly imageMarker: boolean;
  readonly env: string | undefined;
}

/** 지금 프로세스의 두 입력. 판정과 달리 파일과 환경을 읽는 자리다. */
export function currentNetwork(): ContainerNetwork {
  return { imageMarker: existsSync(IMAGE_MARKER), env: process.env[CONTAINER_NETWORK_ENV] };
}

function isLoopback(host: string): boolean {
  return LOOPBACK_HOSTS.includes(host);
}

function sshForward(port: string): string {
  return `ssh -L ${port}:127.0.0.1:${port} <서버>`;
}

/** 환경 변수의 값이 `1` 도 빈 값도 아니면 그 구성 오류. 오타가 조용히 꺼짐으로 읽히지 않게 한다. */
function envProblem({ env }: ContainerNetwork): string | null {
  if (env === undefined || env === "" || env === "1") {
    return null;
  }
  return [
    `${CONTAINER_NETWORK_ENV} 는 비우거나 1 만 받는다. 받은 값: ${env}`,
    "  오타가 조용히 꺼짐으로 읽히지 않게 시작 자리에서 끝낸다.",
  ].join("\n");
}

function isEnabled({ imageMarker, env }: ContainerNetwork): boolean {
  return imageMarker && env === "1";
}

/**
 * 예외로 열리는 주소를 받았는데 켜지지 않았을 때 진단에 더할 한 줄. 환경 변수만 있고 표지 파일이 없으면 이미지 밖에서는 켜지지
 * 않는다고, 표지 파일만 있고 환경 변수가 없으면 그 환경 변수를 알린다. 둘 다 아니면 더할 것이 없다.
 */
function exceptionHint(network: ContainerNetwork, opened: string): readonly string[] {
  if (network.imageMarker) {
    return [`  이미지 안에서 ${opened} 에 묶으려면 환경 변수 ${CONTAINER_NETWORK_ENV}=1 도 준다.`];
  }
  if (network.env === "1") {
    return [
      `  ${CONTAINER_NETWORK_ENV} 는 이미지 밖에서는 켜지지 않는다(표지 파일 ${IMAGE_MARKER} 가 없다).`,
    ];
  }
  return [];
}

/** 관리 화면이 설 호스트의 구성 오류. 받으면 null. `port` 는 SSH 안내에 싣는다. */
export function bindingProblem(
  host: string,
  port: string,
  network: ContainerNetwork,
): string | null {
  const invalid = envProblem(network);
  if (invalid !== null) {
    return invalid;
  }
  if (isLoopback(host) || (isEnabled(network) && host === CONTAINER_HOST)) {
    return null;
  }
  if (isEnabled(network)) {
    return [
      `--hostname 은 루프백이나 컨테이너 네트워크 주소만 받는다(${[...LOOPBACK_HOSTS, CONTAINER_HOST].join(", ")}). 받은 값: ${host}`,
      `  컨테이너 네트워크 주소는 ${CONTAINER_HOST} 하나다. 다른 주소와 이름은 받지 않는다.`,
      `  원격에서 보려면 SSH 포트 포워딩을 쓴다: ${sshForward(port)}`,
    ].join("\n");
  }
  return [
    `--hostname 은 루프백만 받는다(${LOOPBACK_HOSTS.join(", ")}). 받은 값: ${host}`,
    "  벗어나면 브라우저가 싣는 토큰이 관리 화면의 중계까지 LAN 위를 평문으로 지난다.",
    `  원격에서 보려면 SSH 포트 포워딩을 쓴다: ${sshForward(port)}`,
    ...(host === CONTAINER_HOST ? exceptionHint(network, CONTAINER_HOST) : []),
  ].join("\n");
}

/**
 * 상류 입력의 구성 오류. http 출처 하나이고 호스트가 `127.0.0.1` 이면 null. 예외가 켜졌으면 compose 의 서비스 이름 `serve` 도
 * 받는다. 이미지는 지을 때 상류를 `http://serve:8000` 으로 굳히므로(시작 때 준 값은 중계 대상을 바꾸지 못한다) 상류 검사는
 * 빌드 때와 시작 때 모두 이 판정을 지난다.
 *
 * 출처(스킴, 호스트, 포트) 밖의 것(경로, 질의, 조각, 계정)은 받지 않는다. 조용히 버리면 운영자가 적은 것과 중계가
 * 넘기는 곳이 갈린다. 그 진단은 받은 값을 싣지 않는다. 계정의 비밀번호가 로그에 남는다(원칙 V).
 */
export function upstreamProblem(value: string, network: ContainerNetwork): string | null {
  const invalid = envProblem(network);
  if (invalid !== null) {
    return invalid;
  }
  const url = URL.parse(value);
  if (url === null || url.protocol !== "http:" || url.href !== `${url.origin}/`) {
    return `${UPSTREAM_ENV} 는 http 출처 하나다(스킴, 호스트, 포트. 예: ${DEFAULT_UPSTREAM}). 경로, 질의, 계정은 받지 않는다.`;
  }
  const host = url.hostname.replace(/^\[(.*)\]$/, "$1");
  if (host === UPSTREAM_HOST || (isEnabled(network) && host === UPSTREAM_SERVICE)) {
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
  if (isEnabled(network)) {
    return [
      `${UPSTREAM_ENV} 의 호스트는 ${UPSTREAM_HOST} 과 ${UPSTREAM_SERVICE} 만 받는다. 받은 값: ${host}`,
      "  벗어나면 중계가 브라우저의 토큰을 그 호스트까지 평문으로 넘긴다.",
    ].join("\n");
  }
  return [
    `${UPSTREAM_ENV} 의 호스트는 루프백 ${UPSTREAM_HOST} 만 받는다. 받은 값: ${host}`,
    "  벗어나면 중계가 브라우저의 토큰을 그 호스트까지 평문으로 넘긴다.",
    `  파이썬 서버가 다른 기계에 있으면 SSH 포트 포워딩으로 이 기계의 루프백에 가져온다: ${sshForward(port)}`,
    ...(host === UPSTREAM_SERVICE ? exceptionHint(network, UPSTREAM_SERVICE) : []),
  ].join("\n");
}
