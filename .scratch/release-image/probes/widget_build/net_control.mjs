/**
 * `net_hook.cjs` 의 양성 대조. `measure.mjs net` 이 빌드와 같은 `NODE_OPTIONS=--require=<훅>` 으로 띄운다.
 *
 * 루프백이 아닌 대상 셋에 node 의 전역 `fetch` 를 건다. Next 의 텔레메트리가 보내는 길이 `fetch` 다
 * (Next 16.3.6 의 `dist/telemetry/post-telemetry-payload.js` 를 읽었다). 훅이 실렸으면 셋 다 훅이 적고, 걸지 않은 채 오류로
 * 끝낸다. 그래야 빌드 회차의 "밖으로 가는 시도 0"이 "훅이 그런 시도를 적지 못한다"와 갈린다.
 *
 * 대상은 어디에도 닿지 않는 자리다. `192.0.2.1` 은 문서용 주소(RFC 5737)이고 `.invalid` 는 풀리지 않는 이름(RFC 2606)이다.
 * 훅이 실리지 않았어도 바깥 서비스에 닿지 않고, 요청에 싣는 값도 없다.
 *
 * 마지막 stdout 줄이 결과 JSON 이다. 대상마다 `reached`(응답을 받았다)와 `refusedByHook`(오류의 사슬에 훅의 문구가 있다)을
 * 적는다.
 *
 * 사용: node net_control.mjs   (환경: NODE_OPTIONS=--require=<net_hook.cjs>, AGENT_OS_PROBE_NET_LOG)
 */

// 포트는 기본값을 쓴다. fetch 는 막힌 포트 목록(9 등)의 주소를 연결을 걸기 전에 "bad port" 로 거절해, 훅까지 오지 않는다.
const TARGETS = [
  "http://192.0.2.1/",
  "http://widget-build-probe.invalid/",
  "https://widget-build-probe.invalid/",
];
// 훅이 막을 때 오류에 싣는 문구의 머리(`net_hook.cjs`).
const HOOK_MARK = "probe:";

/** 오류와 그 `cause` 사슬을 한 줄로 편다. fetch 는 소켓의 오류를 `cause` 로 감싼다. */
function chain(error) {
  const texts = [];
  for (let current = error; current !== undefined && current !== null && texts.length < 8; current = current.cause) {
    texts.push(`${String(current.code ?? "")} ${String(current.message ?? current)}`.trim());
  }
  return texts.join(" <- ");
}

const results = [];
for (const url of TARGETS) {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(5000) });
    results.push({ url, reached: true, status: response.status, refusedByHook: false });
  } catch (error) {
    const text = chain(error);
    results.push({ url, reached: false, refusedByHook: text.includes(HOOK_MARK), error: text.slice(0, 300) });
  }
}
console.log(JSON.stringify(results));
