// 컨테이너 안에서 주소 하나가 처음 200 을 낼 때까지 기다리고 그 시각을 한 줄로 찍는다. 진입 단계(entry.mjs)가 next 를
// 부르기 전에 뒤에서 띄운다. 기한(기본 120초)을 넘기면 WRV_PROBE first-ok-timeout 을 찍고 종료 1 로 끝난다.
//
// 사용: node wait.mjs <url> [기한 ms]

import http from "node:http";

const [url, limit = "120000"] = process.argv.slice(2);
if (url === undefined) {
  console.error("사용: node wait.mjs <url> [기한 ms]");
  process.exit(2);
}
const deadline = Date.now() + Number(limit);
let tries = 0;

function attempt() {
  if (Date.now() > deadline) {
    console.log(`WRV_PROBE first-ok-timeout tries=${String(tries)}`);
    process.exit(1);
  }
  tries += 1;
  let settled = false;
  const again = () => {
    if (!settled) {
      settled = true;
      setTimeout(attempt, 50);
    }
  };
  const request = http.get(url, { agent: false, timeout: 2000 }, (response) => {
    response.resume();
    if (response.statusCode === 200) {
      settled = true;
      console.log(`WRV_PROBE first-ok t=${(Date.now() / 1000).toFixed(3)} tries=${String(tries)}`);
      process.exit(0);
    }
    again();
  });
  request.on("timeout", () => request.destroy(new Error("timeout")));
  request.on("error", again);
}

attempt();
