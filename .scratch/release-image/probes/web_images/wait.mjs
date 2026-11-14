// 컨테이너 안에서 서비스가 첫 요청에 답한 시각을 잰다. 시제품 진입 스크립트가 뒤에서 띄운다.
//
// 사용: node wait.mjs <url> [<기한 초>]
// 25ms 마다 GET 을 걸어 상태 200 을 처음 받은 때의 시각(epoch ms)을 한 줄로 찍고 끝난다. 기한을 넘기면 그렇게 찍고 1로
// 끝난다. 요청마다 새 연결을 연다(연결을 붙잡아 두면 서버의 종료를 늦춘다). 본문의 표지는 보지 않는다. 그것은 프로브가
// 따로 건 요청으로 본다.

import http from "node:http";

const [url, limit = "600"] = process.argv.slice(2);
if (url === undefined) {
  console.error("사용: node wait.mjs <url> [<기한 초>]");
  process.exit(2);
}
const started = Date.now();
const deadline = started + Number(limit) * 1000;
let attempts = 0;

// 소켓 비활성 제한(timeout)은 서버가 본문 조각을 계속 보내며 응답을 끝내지 않으면 요청을 못 끊는다.
// 그래서 남은 전체 시간에 별도 타이머를 걸어 요청을 중단한다.
function once() {
  return new Promise((resolve) => {
    let cap;
    const finish = (status) => {
      clearTimeout(cap);
      resolve(status);
    };
    const request = http.get(url, { agent: false, timeout: 2000 }, (response) => {
      response.resume();
      response.on("end", () => finish(response.statusCode ?? 0));
      response.on("error", () => finish(0));
      response.on("close", () => finish(0));
    });
    cap = setTimeout(() => request.destroy(), Math.max(0, deadline - Date.now()));
    request.on("timeout", () => request.destroy());
    request.on("error", () => finish(0));
  });
}

for (;;) {
  attempts += 1;
  const status = await once();
  // 기한 뒤에 받은 200 은 성공이 아니다.
  if (status === 200 && Date.now() <= deadline) {
    console.log(
      `RI_PROBE first-ok epoch_ms=${Date.now()} attempts=${attempts} waited_ms=${Date.now() - started} url=${url}`,
    );
    process.exit(0);
  }
  if (Date.now() > deadline) {
    console.log(`RI_PROBE first-ok-timeout attempts=${attempts} last_status=${status} url=${url}`);
    process.exit(1);
  }
  await new Promise((resolve) => setTimeout(resolve, 25));
}
