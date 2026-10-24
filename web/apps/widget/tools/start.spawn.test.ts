// 위젯의 시작 래퍼를 실제 프로세스로 띄운다. 인자의 판정은 start.test.ts 가 잰다. 여기서는 거부가 next 를 띄우기 전에
// 끝나는지와, 래퍼가 푼 사이트 파일을 빌드가 읽는지를 본다. build 에서 그 파일을 먼저 읽는 것은 페이지 안 번들의 빌드
// (element.ts)이고, 읽지 못하면 next 를 부르기 전에 끝난다. next 의 설정 파일이 같은 파일을 읽는 것은 위젯 e2e 의 빌드가
// 본다(frame-ancestors). 운영체제별 명령에 기대지 않는다. 윈도우와 CI 의 ubuntu 에서 같이 돈다.

import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { expect, test } from "vitest";

const START = join(import.meta.dirname, "start.ts");

test("루프백이 아닌 호스트로 띄우면 next 를 부르지 않고 실패 종료 코드로 끝난다", () => {
  // next 가 떴다면 이 프로세스는 스스로 끝나지 않는다. 시간 제한에 걸리면 status 가 null 이다.
  const run = spawnSync(process.execPath, [START, "dev", "--hostname", "0.0.0.0"], {
    encoding: "utf-8",
    timeout: 30_000,
    env: { ...process.env, PORT: "3456" },
  });

  expect(run.status).toBe(1);
  expect(run.stderr).toContain("ssh -L 3456:127.0.0.1:3456");
  // next 의 첫 줄(판과 주소)이 없다. next 를 부르기 전에 끝났다.
  expect(run.stdout).toBe("");
});

test("상대 경로로 준 사이트 파일을 래퍼를 부른 자리에서 찾고, 읽지 못하면 빌드가 그 진단으로 실패한다", () => {
  // 번들 빌드가 사이트 파일을 읽다 멈추기까지 이 PC에서 이 시험만 돌려 1.4초였다(2026-10-24, vitest 가 보고한 시험
  // 시간). 번들 빌드가 앞에 서기 전 next 가 설정 파일을 읽다 멈출 때는 처음 한 번이 8.9초였다(같은 날 세션 스크래치패드의
  // 스크립트로 손으로 봤다). 처음 한 번과 다른 검사와 함께 돌 때를 생각해 시간 제한을 그 값의 다섯 배쯤으로 둔다.
  const operator = mkdtempSync(join(tmpdir(), "widget-start-"));
  writeFileSync(join(operator, "sites.toml"), 'schema_version = "1"\n[[sites]\n', "utf-8");

  const run = spawnSync(process.execPath, [START, "build"], {
    cwd: operator,
    encoding: "utf-8",
    timeout: 50_000,
    env: { ...process.env, AGENT_OS_SITE_FILE: "sites.toml" },
  });

  expect(run.status).toBe(1);
  expect(run.stderr).toContain(`사이트 파일 ${join(operator, "sites.toml")} 을 받아들일 수 없다`);
  // 앱 폴더에서 풀었다면 "파일이 없다" 다.
  expect(run.stderr).toContain("TOML 이 아니다");
});
