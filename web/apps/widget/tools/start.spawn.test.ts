// 위젯의 시작 래퍼를 실제 프로세스로 띄운다. 인자의 판정은 start.test.ts 가 잰다. 여기서는 거부가 next 를 띄우기 전에
// 끝나는지와, 래퍼가 푼 사이트 파일을 읽는지를 본다. start 는 값 파일을 쓰려고 그 파일을 먼저 읽고(runtime.ts), 읽지
// 못하면 next 를 부르기 전에 끝난다. build 는 값 파일을 쓰지 않아 next 의 설정 파일이 같은 파일을 읽다 멈춘다
// (frame-ancestors, 빌드가 사이트 파일을 읽지 않게 되면 이 사례가 바뀐다). 운영체제별 명령에 기대지 않는다. 윈도우와 CI
// 의 ubuntu 에서 같이 돈다.

import { spawnSync } from "node:child_process";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { expect, test } from "vitest";
import { CASES, expectSignals, nameOf } from "../testing/container-network.ts";

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

// 사례 표(tests/fixtures/container_network/cases.json)의 거부 사례 가운데 표지 파일이 없는 것. 환경에서 온 값이 진입점까지
// 닿는지를 본다. 표지 파일은 `/etc` 에 있어 시험이 만들지 못하므로 있는 쪽은 start.test.ts 의 순수 판정이 본다. 받는 사례는
// next 가 떠서 스스로 끝나지 않으므로 띄우지 않는다.
for (const item of CASES.binding.filter(
  ({ marker, env, verdict }) => !marker && env !== undefined && verdict !== "ok",
)) {
  test(`환경에서 온 값이 진입점에서 거부된다: ${nameOf(item)}`, () => {
    const run = spawnSync(process.execPath, [START, "dev", "--hostname", item.host], {
      encoding: "utf-8",
      timeout: 30_000,
      env: { ...process.env, [CASES.envName]: item.env },
    });

    expect(run.status).toBe(1);
    expectSignals(run.stderr, CASES.bindingSignals, item);
    expect(run.stdout).toBe("");
  });
}

const BROKEN_SITE_FILE = 'schema_version = "1"\n[[sites]\n';

test("상대 경로로 준 사이트 파일을 서비스 시작이 래퍼를 부른 자리에서 찾고, 읽지 못하면 그 진단으로 next 를 부르기 전에 끝난다", () => {
  // 값 파일을 쓰려고 사이트 파일을 읽다 멈추므로 next 를 띄우지 않는다. next 가 떴다면 이 프로세스는 스스로 끝나지 않아
  // 시간 제한에 걸리고 status 가 null 이다. next 의 첫 줄(판과 주소)도 없다.
  const operator = mkdtempSync(join(tmpdir(), "widget-start-"));
  writeFileSync(join(operator, "sites.toml"), BROKEN_SITE_FILE, "utf-8");

  const run = spawnSync(process.execPath, [START, "start"], {
    cwd: operator,
    encoding: "utf-8",
    timeout: 30_000,
    env: { ...process.env, AGENT_OS_SITE_FILE: "sites.toml" },
  });

  expect(run.status).toBe(1);
  expect(run.stderr).toContain(`사이트 파일 ${join(operator, "sites.toml")} 을 받아들일 수 없다`);
  // 앱 폴더에서 풀었다면 "파일이 없다" 다.
  expect(run.stderr).toContain("TOML 이 아니다");
  expect(run.stdout).toBe("");
});

test("상대 경로로 준 사이트 파일을 읽지 못하면 빌드는 next 의 설정 파일이 그 진단으로 멈춘다", () => {
  // 지금의 빌드는 사이트 파일을 next 의 설정 파일이 읽어 `frame-ancestors` 에 굳힌다(widget-runtime-values 티켓 02 가 바꾼다).
  // 번들을 짓고 next 가 설정 파일을 읽다 멈추기까지 처음 한 번이 8.9초였다(2026-10-24 세션 스크래치패드의 스크립트로 손으로
  // 봤다). 처음 한 번과 다른 검사와 함께 돌 때를 생각해 시간 제한을 그 값의 다섯 배쯤으로 둔다.
  const operator = mkdtempSync(join(tmpdir(), "widget-start-"));
  writeFileSync(join(operator, "sites.toml"), BROKEN_SITE_FILE, "utf-8");

  const run = spawnSync(process.execPath, [START, "build"], {
    cwd: operator,
    encoding: "utf-8",
    timeout: 50_000,
    env: { ...process.env, AGENT_OS_SITE_FILE: "sites.toml" },
  });

  expect(run.status).toBe(1);
  expect(run.stderr).toContain(`사이트 파일 ${join(operator, "sites.toml")} 을 받아들일 수 없다`);
  expect(run.stderr).toContain("TOML 이 아니다");
});
