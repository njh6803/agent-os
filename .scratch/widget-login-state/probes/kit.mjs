// widget-login-state 프로브들이 함께 쓰는 것이다. 프로브가 아니고 스스로 재는 것이 없다.
//
//   makeCert      자체 서명 인증서를 openssl 로 짓는다. 준 이름을 모두 subjectAltName 에 넣는다
//   createProxy   준 이름으로 가는 CONNECT 만 로컬 서버로 잇는 프록시. 브라우저를 이 프록시로 띄워 이름을 127.0.0.1 에
//                 맞춘다. hosts 파일은 건드리지 않고, 그 밖의 이름(브라우저가 스스로 여는 연결)은 바깥으로 잇지 않는다
//   listen        서버를 127.0.0.1 의 빈 포트에 띄우고 그 포트를 돌려준다
//   differences   두 값이 다른 자리를 경로와 함께 낸다. expected.json 과 견줄 때 쓴다
//
// 쓰는 프로브: logout_fetch/probe.mjs, opener_message/probe.mjs

import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import http from "node:http";
import { connect } from "node:net";
import { join } from "node:path";

export function makeCert(outDir, hostNames) {
  const key = join(outDir, "key.pem");
  const cert = join(outDir, "cert.pem");
  const names = hostNames.map((name) => `DNS:${name}`).join(",");
  const made = spawnSync(
    "openssl",
    [
      ...["req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", key, "-out", cert, "-days", "2"],
      ...["-subj", `/CN=${hostNames[0]}`, "-addext", `subjectAltName=${names}`],
    ],
    { encoding: "utf-8", timeout: 60_000 },
  );
  if (made.status !== 0 || !existsSync(cert) || !existsSync(key)) {
    return { problem: made.error?.message ?? `openssl 종료 ${made.status}: ${made.stderr ?? ""}` };
  }
  return { key: readFileSync(key), cert: readFileSync(cert) };
}

export function createProxy(target, hostNames) {
  const allowed = new Set(hostNames);
  const sockets = new Set();
  const refusedHosts = new Set();
  const server = http.createServer((_request, response) => {
    response.writeHead(502);
    response.end();
  });
  server.on("connect", (request, client) => {
    const host = (request.url ?? "").replace(/:\d+$/, "");
    if (!allowed.has(host)) {
      // 브라우저가 스스로 여는 연결(갱신 확인 따위)이다. 바깥으로 잇지 않는다.
      refusedHosts.add(host);
      client.end("HTTP/1.1 403 Forbidden\r\n\r\n");
      return;
    }
    const upstream = connect(target(), "127.0.0.1", () => {
      client.write("HTTP/1.1 200 Connection Established\r\n\r\n");
      upstream.pipe(client);
      client.pipe(upstream);
    });
    for (const socket of [client, upstream]) {
      sockets.add(socket);
      socket.on("close", () => sockets.delete(socket));
    }
    upstream.on("error", () => client.destroy());
    client.on("error", () => upstream.destroy());
  });
  return { server, sockets, refusedHosts };
}

export function listen(server) {
  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve(server.address().port));
  });
}

export function differences(left, right, path = "") {
  if (JSON.stringify(left) === JSON.stringify(right)) return [];
  const bothObjects =
    left !== null &&
    right !== null &&
    typeof left === "object" &&
    typeof right === "object" &&
    !Array.isArray(left) &&
    !Array.isArray(right);
  if (!bothObjects) return [`${path || "(뿌리)"}: ${JSON.stringify(left)} != ${JSON.stringify(right)}`];
  const keys = new Set([...Object.keys(left), ...Object.keys(right)]);
  return [...keys].flatMap((key) => differences(left[key], right[key], path === "" ? key : `${path}.${key}`));
}
