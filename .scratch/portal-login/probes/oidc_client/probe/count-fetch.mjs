// 회차 프로세스에 `--import` 로 먼저 싣는다. 전역 `fetch` 를 세는 겉으로 바꿔, 후보가 HTTP 를 전역 `fetch` 로 냈는지를
// 프로세스가 끝날 때 stderr 한 줄로 알린다. `flow.mjs` 가 그 줄을 읽는다. 라이브러리는 부를 때 전역 이름 `fetch` 를
// 찾으므로(oauth4webapi 3.8.8 과 jose 6.2.17 의 빌드 산출물을 읽었다) 이 겉을 지난다.
const original = globalThis.fetch;
let calls = 0;
globalThis.fetch = function countedFetch(...args) {
  calls += 1;
  return original.apply(this, args);
};
process.on("exit", () => {
  process.stderr.write(`[count-fetch] global fetch calls: ${String(calls)}\n`);
});
