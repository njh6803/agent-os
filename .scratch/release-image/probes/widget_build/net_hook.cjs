/**
 * 빌드의 node 프로세스가 밖으로 거는 연결을 적고 막는 훅. `measure.mjs net` 이 `NODE_OPTIONS=--require=<이 파일>` 로 싣는다.
 * `AGENT_OS_PROBE_NET_LOG` 가 가리키는 파일에 줄마다 JSON 하나를 덧붙인다. 변수가 없으면 아무것도 하지 않는다.
 *
 * - 실릴 때마다(프로세스와 워커 스레드마다) `loaded` 한 줄을 적고, 닫힌 루프백 포트로 미끼 연결을 한 번 건다. 미끼가
 *   `connect` 줄로 적히면 바꿔 끼운 `connect` 가 그 스레드에서 돈다는 표지다.
 * - `net.Socket.prototype.connect` 를 바꿔 끼워 대상(호스트와 포트, 또는 파이프 경로)을 적는다. http·https·fetch(undici)·tls 가
 *   모두 이 메서드를 지난다. 루프백(127.0.0.0/8, ::1, localhost, *.localhost)과 파이프가 아닌 대상은 걸지 않고 오류로
 *   끝낸다. 네트워크가 없는 자리를 흉내 낸다.
 * - `dns.lookup` 과 `dns.promises.lookup` 을 바꿔 끼워 이름을 적는다. 루프백이 아닌 이름은 묻지 않고 ENOTFOUND 로 답한다.
 *
 * 못 보는 것: node 가 아닌 프로세스와 네이티브 코드(Turbopack 의 Rust)가 직접 여는 소켓, UDP(dgram), `dns.resolve*` 계열.
 */

"use strict";

const fs = require("node:fs");
const net = require("node:net");
const dns = require("node:dns");
const { threadId } = require("node:worker_threads");

const LOG = process.env.AGENT_OS_PROBE_NET_LOG;
// 닫혀 있으리라 보는 루프백 포트(discard). 열려 있어도 미끼는 적힌다.
const CANARY_PORT = 9;

function record(entry) {
  try {
    fs.appendFileSync(LOG, `${JSON.stringify({ pid: process.pid, threadId, at: Date.now(), ...entry })}\n`);
  } catch {
    // 적지 못해도 빌드를 깨지 않는다. 적히지 않은 스레드는 measure.mjs 의 표지(미끼 수 = 실린 수)가 잡는다.
  }
}

function isLoopback(host) {
  const name = String(host ?? "").toLowerCase();
  return name === "localhost" || name.endsWith(".localhost") || name === "::1" || name === "[::1]" || /^127\./.test(name);
}

/** `connect` 의 인자에서 대상을 읽는다. node 안쪽은 정규화한 배열 하나로 부르기도 한다. */
function target(args) {
  const first = Array.isArray(args[0]) ? args[0][0] : args[0];
  if (typeof first === "string") {
    return { pipe: true, path: first };
  }
  if (typeof first === "number") {
    return { pipe: false, host: typeof args[1] === "string" ? args[1] : "localhost", port: first };
  }
  if (first !== null && typeof first === "object") {
    if (typeof first.path === "string") {
      return { pipe: true, path: first.path };
    }
    return { pipe: false, host: first.host ?? "localhost", port: first.port };
  }
  return { pipe: false, host: "?", port: undefined };
}

if (LOG) {
  let inCanary = false;
  record({ kind: "loaded", argv: process.argv.slice(1, 4) });

  const connect = net.Socket.prototype.connect;
  net.Socket.prototype.connect = function probedConnect(...args) {
    const to = target(args);
    record({ kind: "connect", canary: inCanary, ...to });
    if (!to.pipe && !isLoopback(to.host)) {
      const error = Object.assign(new Error(`probe: 밖으로 가는 연결을 막았다(${String(to.host)}:${String(to.port)})`), {
        code: "ECONNREFUSED",
      });
      process.nextTick(() => this.destroy(error));
      return this;
    }
    return connect.apply(this, args);
  };

  const refuse = (host) => Object.assign(new Error(`probe: 이름 풀기를 막았다(${host})`), { code: "ENOTFOUND", hostname: host });
  const lookup = dns.lookup;
  dns.lookup = function probedLookup(host, ...rest) {
    record({ kind: "lookup", host });
    const callback = rest.at(-1);
    if (!isLoopback(host) && net.isIP(String(host)) === 0 && typeof callback === "function") {
      process.nextTick(() => callback(refuse(host)));
      return {};
    }
    return lookup.call(this, host, ...rest);
  };
  const promisedLookup = dns.promises.lookup;
  dns.promises.lookup = function probedPromisedLookup(host, ...rest) {
    record({ kind: "lookup", host });
    if (!isLoopback(host) && net.isIP(String(host)) === 0) {
      return Promise.reject(refuse(host));
    }
    return promisedLookup.call(this, host, ...rest);
  };

  inCanary = true;
  try {
    const canary = new net.Socket();
    canary.on("error", () => {});
    canary.connect({ host: "127.0.0.1", port: CANARY_PORT });
    canary.unref();
    canary.setTimeout(2000, () => canary.destroy());
  } finally {
    inCanary = false;
  }
}
