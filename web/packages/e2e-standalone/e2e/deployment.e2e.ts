// 단독 배포 e2e 의 사례(release-image 티켓 09). 준비(stack.ts)가 실제 이미지 넷과 프록시로 띄운 배치를 실제 브라우저와 HTTP 로
// 지난다. 배치가 약속한 것(공개 면의 모양, 발행 포트, 컨테이너의 사용자, 재생성 뒤의 길, 네트워크 없는 MCP 실행, 데이터베이스의
// 판과 남는 데이터)을 잠근다.
//
// 429 사례는 마지막에 둔다. 토큰 끝점의 요청 상한은 IP 하나에 걸려 있어 먼저 돌면 뒤의 사례가 429 를 받는다. 파일 안의 사례는
// 차례로 돈다(playwright.config.ts 의 workers 1). 배치를 내렸다 다시 띄우는 데이터베이스 사례는 그 뒤의 사례가 다시 띄운 배치를
// 지나도록 재생성 사례 앞에 둔다.

import { randomBytes } from "node:crypto";
import { readFileSync } from "node:fs";
import { request as httpsRequest } from "node:https";
import { dirname, join } from "node:path";
import { expect, test } from "@playwright/test";
import { signedDirectToken } from "./direct.ts";
import { Compose, repositoryName, run, succeed } from "./docker.ts";
import {
  ADMIN_ORIGIN,
  CALC_AGENT,
  deployment,
  LLM_ENV,
  ORIGIN,
  PREVIEW_SITE,
  UP_WAIT_SECONDS,
} from "./env.ts";
import { saveLogsAtFailure } from "./failure-logs.ts";
import { productRevision } from "./migrations.ts";

const SERVICES = ["proxy", "postgres", "serve", "admin", "widget", "portal"] as const;
// 배치를 내렸다 다시 띄우는 사례의 상한. 다시 띄울 때 위젯이 사이트 파일로 다시 빌드한다.
const RESTART_TIMEOUT_MS = (UP_WAIT_SECONDS + 180) * 1000;
const COVER_TITLE = "질문하기 전에 읽어 주세요";
const ACKNOWLEDGE = "확인하고 질문하기";
const PUBLISHED = [80, 443, 3000];
// 재생성한 뒤 프록시가 새 주소를 따라 다시 200 을 내기까지 기다리는 상한(명세 사용자 이야기 20).
const RECOVER_MS = 15_000;

function compose(): Compose {
  const { project, dir, files } = deployment();
  return new Compose(project, dir, files);
}

// 뒤쪽 사례가 배치를 내렸다 올리거나 컨테이너를 다시 만들면 앞쪽 사례의 로그가 사라지므로, 실패한 사례는 그 자리에서 로그를
// 받아 둔다(failure-logs.ts).
test.afterEach(async ({}, testInfo) => {
  await saveLogsAtFailure(testInfo, compose());
});

/**
 * 경로를 다듬지 않고 그대로 보낸다. Playwright 의 요청과 `fetch` 는 URL 을 만들며 `..` 를 접어 버려 우회 시도가 프록시에
 * 닿기 전에 사라진다.
 */
function rawGet(path: string): Promise<{ status: number; body: string }> {
  // 인증서 검증은 끄지 않는다. 준비가 지은 자체 서명 인증서를 신뢰 목록으로 주고 이름은 localhost 로 맞춘다.
  const ca = readFileSync(join(deployment().dir, "tls", "fullchain.pem"));
  return new Promise((resolve, reject) => {
    const req = httpsRequest(
      { host: "127.0.0.1", port: 443, path, method: "GET", ca, servername: "localhost" },
      (response) => {
        const chunks: Buffer[] = [];
        response.on("data", (chunk: Buffer) => chunks.push(chunk));
        response.on("end", () => {
          resolve({
            status: response.statusCode ?? 0,
            body: Buffer.concat(chunks).toString("utf-8"),
          });
        });
      },
    );
    req.on("error", reject);
    req.end();
  });
}

function echoed(request: string): string {
  return `출력: chars:${String(request.length)}`;
}

test("위젯 테스트 페이지가 프록시 뒤에서 CSP 위반 없이 그려지고 토큰 CSS 와 글꼴이 풀린다", async ({
  page,
}) => {
  const messages: string[] = [];
  page.on("console", (message) => {
    messages.push(message.text());
  });
  const failures: string[] = [];
  page.on("requestfailed", (request) => {
    failures.push(request.url());
  });
  // 연결은 됐는데 404 나 5xx 로 돌아온 자원(프록시 허용 목록에서 빠진 글꼴, 스크립트)도 실패로 센다.
  const statuses: string[] = [];
  page.on("response", (response) => {
    if (response.status() >= 400) {
      statuses.push(`${String(response.status())} ${response.url()}`);
    }
  });

  await page.goto(`${ORIGIN}/portal/`);
  await page.evaluate(() => document.fonts.ready);

  expect(messages.filter((text) => text.includes("Content Security Policy"))).toEqual([]);
  expect(failures).toEqual([]);
  expect(statuses).toEqual([]);
  // 글꼴이 실제로 풀렸는지: 불러온 글꼴 면이 하나 이상 있어야 한다.
  const loadedFaces = await page.evaluate(() => {
    let loaded = 0;
    document.fonts.forEach((face) => {
      if (face.status === "loaded") {
        loaded += 1;
      }
    });
    return loaded;
  });
  expect(loadedFaces).toBeGreaterThan(0);
  const sans = await page.evaluate(() =>
    getComputedStyle(document.documentElement).getPropertyValue("--sans").trim(),
  );
  expect(sans).toContain("Noto Sans KR");
});

test("고지를 확인한 최종 사용자의 질문에 모델 없는 에이전트가 프록시, 위젯, serve 를 지나 답한다", async ({
  page,
}) => {
  const request = "standalone-e2e";
  await page.goto(`${ORIGIN}/portal/`);
  await page
    .getByRole("region", { name: COVER_TITLE })
    .getByRole("button", { name: ACKNOWLEDGE })
    .click();
  await page.getByRole("textbox", { name: "질문" }).fill(request);
  await page.getByRole("button", { name: "보내기" }).click();

  await expect(page.getByText(echoed(request))).toBeVisible();
});

test("80 포트는 308 로 443 의 같은 주소로 넘기고 443 의 응답은 HSTS 머리를 단다", async ({
  request,
}) => {
  const moved = await request.get("http://127.0.0.1/portal/?site=preview", { maxRedirects: 0 });
  expect(moved.status()).toBe(308);
  expect(moved.headers()["location"]).toBe("https://127.0.0.1/portal/?site=preview");

  const served = await request.get(`${ORIGIN}/portal/health`);
  expect(served.status()).toBe(200);
  expect(served.headers()["strict-transport-security"]).toContain("max-age=");
});

test("프록시는 관리 면과 허용 목록 밖의 경로를 404 로 막고, 우회 시도도 같은 404 다", async () => {
  // 양성 대조. 같은 길로 허용된 경로는 열려 있어야 거절이 프록시의 것임을 읽는다.
  expect((await rawGet("/portal/health")).status).toBe(200);

  const blocked = [
    "/api/plugins",
    "/health",
    "/runs",
    "/plugins",
    "/end-user/../runs",
    "/end-user/%2e%2e/runs",
    "/widget/../health",
    "/portal/../health",
  ];
  const statuses = await Promise.all(
    blocked.map(async (path) => [path, (await rawGet(path)).status]),
  );
  expect(statuses).toEqual(blocked.map((path) => [path, 404]));
});

test("관리 화면은 서버의 루프백 3000 에서만 열리고 프록시를 거치지 않는다", async ({ request }) => {
  const admin = await request.get(ADMIN_ORIGIN);
  expect(admin.status()).toBe(200);
  // 프록시의 공개 출처에서 관리 화면의 경로(/api 중계)는 404 다. 위 사례가 경로별로 이미 본다.
  const relayed = await request.get(`${ORIGIN}/api/plugins`);
  expect(relayed.status()).toBe(404);
});

test("발행된 호스트 포트는 80, 443, 3000 셋뿐이고 3000 은 루프백에만 묶인다", async () => {
  const outcome = await compose().call(["ps", "--all", "--format", "json"], 60_000);
  expect(outcome.code).toBe(0);
  const publishers = new Map<number, Set<string>>();
  for (const line of outcome.stdout.split("\n")) {
    if (line.trim() === "") {
      continue;
    }
    const parsed: unknown = JSON.parse(line);
    for (const [port, address] of publishedOf(parsed)) {
      publishers.set(port, (publishers.get(port) ?? new Set<string>()).add(address));
    }
  }
  expect([...publishers.keys()].toSorted((a, b) => a - b)).toEqual(PUBLISHED);
  // 3000 은 루프백에만 묶이고, 공개 면인 80 과 443 은 모든 IPv4 주소(0.0.0.0)에 묶이며 루프백에 갇히지 않는다.
  expect([...(publishers.get(3000) ?? [])]).toEqual(["127.0.0.1"]);
  for (const port of [80, 443]) {
    const addresses = publishers.get(port) ?? new Set<string>();
    expect(addresses.has("0.0.0.0"), `${String(port)} 의 묶은 주소`).toBe(true);
    expect(addresses.has("127.0.0.1"), `${String(port)} 가 루프백에 갇히지 않는다`).toBe(false);
  }
});

/** `docker compose ps --format json` 한 줄에서 (발행 포트, 묶은 주소) 쌍을 뽑는다. */
function publishedOf(entry: unknown): [number, string][] {
  if (typeof entry !== "object" || entry === null || !("Publishers" in entry)) {
    return [];
  }
  const list: unknown = entry.Publishers;
  if (!Array.isArray(list)) {
    return [];
  }
  const items: readonly unknown[] = list;
  const found: [number, string][] = [];
  for (const item of items) {
    if (
      typeof item === "object" &&
      item !== null &&
      "PublishedPort" in item &&
      "URL" in item &&
      typeof item.PublishedPort === "number" &&
      typeof item.URL === "string" &&
      item.PublishedPort > 0
    ) {
      found.push([item.PublishedPort, item.URL]);
    }
  }
  return found;
}

test("컨테이너는 모두 root 가 아닌 사용자로 돌고 serve 의 판은 묶음의 판과 같다", async () => {
  const { version } = deployment();
  for (const service of SERVICES) {
    const uid = (await compose().inService(service, ["id", "-u"])).trim();
    expect(uid, `${service} 의 사용자`).toMatch(/^[1-9][0-9]*$/u);
  }
  const printed = await compose().inService("serve", ["agent-os", "--version"]);
  // 부분 문자열이면 `0.1.0-rc.10` 이 `0.1.0-rc.1` 을 통과시킨다. 판 번호의 앞뒤가 판 번호 문자가 아닌 자리에서만 맞춘다.
  const escaped = version.replace(/[.*+?^${}()|[\]\\]/gu, "\\$&");
  expect(printed).toMatch(
    new RegExp(`(?<![0-9A-Za-z.+-])${escaped}(?![0-9A-Za-z+-]|\\.[0-9])`, "u"),
  );
});

interface Container {
  readonly service: string;
  readonly name: string;
  readonly state: string;
  readonly health: string;
  readonly exitCode: number;
}

/** `docker compose ps --all --format json` 한 줄을 읽는다. 모르는 꼴이면 `undefined`. */
function containerOf(entry: unknown): Container | undefined {
  if (
    typeof entry === "object" &&
    entry !== null &&
    "Service" in entry &&
    typeof entry.Service === "string" &&
    "Name" in entry &&
    typeof entry.Name === "string" &&
    "State" in entry &&
    typeof entry.State === "string" &&
    "Health" in entry &&
    typeof entry.Health === "string" &&
    "ExitCode" in entry &&
    typeof entry.ExitCode === "number"
  ) {
    return {
      service: entry.Service,
      name: entry.Name,
      state: entry.State,
      health: entry.Health,
      exitCode: entry.ExitCode,
    };
  }
  return undefined;
}

/** 배치의 한 서비스가 만든 컨테이너들. 끝난 것도 든다. */
async function containersOf(service: string): Promise<Container[]> {
  const outcome = await compose().call(["ps", "--all", "--format", "json"], 60_000);
  expect(outcome.code, outcome.stderr).toBe(0);
  const found: Container[] = [];
  for (const line of outcome.stdout.split("\n")) {
    if (line.trim() === "") {
      continue;
    }
    const parsed: unknown = JSON.parse(line);
    const container = containerOf(parsed);
    if (container === undefined) {
      throw new Error(`compose ps 의 줄을 읽지 못했다: ${line}`);
    }
    if (container.service === service) {
      found.push(container);
    }
  }
  return found;
}

/** PostgreSQL 컨테이너 안의 psql 로 SQL 을 치고 줄만 받는다. 컨테이너의 유닉스 소켓은 비밀번호를 묻지 않는다. */
function psql(sql: string): Promise<string> {
  return compose().inService("postgres", [
    "psql",
    "-U",
    "agent_os",
    "-d",
    "agent_os",
    "-v",
    "ON_ERROR_STOP=1",
    "-tAc",
    sql,
  ]);
}

test("migrate 는 읽기 전용 루트로 빈 데이터베이스의 표를 올리고 0 으로 끝나며, 판 기록 표는 저장소의 마지막 판이다", async () => {
  const revision = productRevision();
  const migrate = await containersOf("migrate");
  expect(migrate.map(({ state, exitCode }) => [state, exitCode])).toEqual([["exited", 0]]);
  for (const { name } of migrate) {
    const readOnly = await succeed(
      "docker",
      ["inspect", "--format", "{{.HostConfig.ReadonlyRootfs}}", name],
      { timeoutMs: 60_000 },
    );
    expect(readOnly.trim(), `${name} 의 루트`).toBe("true");
  }
  const logs = await compose().ensure(["logs", "--no-color", "migrate"], 60_000);
  expect(logs).toContain(`표를 없음에서 ${revision}으로 올렸습니다.`);
  // 휠과 이미지에 제품 마이그레이션 폴더가 들지 않았으면 판 기록 표가 비거나 다른 판이다.
  const recorded = (await psql("SELECT version_num FROM alembic_version")).trim();
  expect(recorded.split("\n")).toEqual([revision]);
});

test("관리 화면의 중계가 관리 토큰으로 플러그인을 켜고 토큰 없이는 401 이다", async ({
  request,
}) => {
  const { adminToken } = deployment();
  const url = `${ADMIN_ORIGIN}/api/plugins/skill/cite-sources/enabled`;

  const headers = { Authorization: `Bearer ${adminToken}` };

  const without = await request.put(url, { data: { enabled: false } });
  expect(without.status()).toBe(401);
  // 이미 켜진 플러그인을 켜는 요청은 쓰기 없이 204 라 볼륨 쓰기를 지나지 않는다. 끈 뒤 다시 켜서 두 번 모두 쓰기를 거치게 한다.
  const disabled = await request.put(url, { headers, data: { enabled: false } });
  expect(disabled.status()).toBe(204);
  const enabled = await request.put(url, { headers, data: { enabled: true } });
  expect(enabled.status()).toBe(204);
});

test("네트워크 없는 MCP 실행: 계산 에이전트의 실행이 도구 연결이 아니라 모델 호출에서 끝난다", async ({
  request,
}) => {
  test.skip(
    process.env[LLM_ENV] === "1",
    "실제 모델 모드에서는 calc.llm.ts 가 같은 길을 실제 모델로 지난다",
  );
  // 이 배치의 serve 는 네트워크에 붙어 있어(프록시가 닿아야 한다) 인터넷이 있는 CI 에서는 npx 로 내려받는 서버도 떴을 것이다.
  // 그래서 "네트워크가 필요 없다"는 것을 실행 결과가 아니라 구성으로 본다. 예시 MCP 서버는 이미지에 든 실행 파일이고 npx 가
  // 아니다. 네트워크 없이 `docker run` 으로 같은 길을 지나는 것은 티켓 07 이 손으로 봤다.
  const manifest = await compose().inService("serve", [
    "sh",
    "-c",
    "command -v mcp-server-everything && cat /app/plugins/mcp/everything/plugin.toml",
  ]);
  expect(manifest).toContain('command = "mcp-server-everything"');
  const response = await request.post(`${ORIGIN}/end-user/runs`, {
    headers: { Authorization: `Bearer ${signedDirectToken(deployment().dir)}` },
    data: { agent: CALC_AGENT, request: "2 더하기 3은?" },
    timeout: 90_000,
  });
  expect(response.status()).toBe(200);
  const body = await response.text();
  // 모델 키가 없어 모델 호출에서 실패한다. MCP 서버가 네트워크 없이 뜨지 못했다면 원인이 tool_connection 이다.
  expect(body).toContain('"type":"failed"');
  expect(body).toContain('"cause":"model_call"');
  expect(body).not.toContain("tool_connection");
});

test("루프백이 아닌 주소에 묶으려는 serve 는 예외 환경 변수 없이는 시작하지 않는다", async () => {
  const image = await serveImage();
  const outcome = await run(
    "docker",
    [
      "run",
      "--rm",
      "--network",
      "none",
      "--env",
      "AGENT_OS_ADMIN_TOKEN=distinct-admin-token",
      "--env",
      "AGENT_OS_CHANNEL_TOKEN=distinct-channel-token",
      image,
      "agent-os",
      "serve",
      "--plugins-root",
      "/app/plugins",
      "--traces",
      "/tmp/traces",
      "--host",
      "0.0.0.0",
    ],
    { timeoutMs: 120_000 },
  );
  expect(outcome.code).not.toBe(0);
  expect(outcome.code).not.toBeNull();
  expect(outcome.stderr).toContain("--host");
});

async function serveImage(): Promise<string> {
  const printed = await compose().call(["config", "--images"], 60_000);
  const marker = `/${await repositoryName("serve")}:`;
  const image = printed.stdout.split("\n").find((line) => line.trim().includes(marker));
  if (image === undefined) {
    throw new Error(`compose config --images 에 serve 이미지가 없다:\n${printed.stdout}`);
  }
  return image.trim();
}

test("데이터베이스에 넣어 둔 줄은 docker compose down 과 up 뒤에도 남고 serve 가 다시 정상이다", async () => {
  test.setTimeout(RESTART_TIMEOUT_MS);
  // 판 기록 표만 보면 데이터가 사라져도 migrate 가 같은 줄을 다시 만들어 지나간다. migrate 가 모르는 표에 무작위 값을 넣는다.
  const value = randomBytes(16).toString("hex");
  await psql(
    `CREATE TABLE e2e_kept (value text NOT NULL); INSERT INTO e2e_kept (value) VALUES ('${value}');`,
  );

  // 볼륨은 남긴다(`--volumes` 없음). 운영자가 판을 바꾸거나 다시 띄울 때 치는 꼴이다.
  await compose().ensure(["down", "--timeout", "10"], 2 * 60_000);
  await compose().ensure(
    ["up", "--detach", "--wait", "--wait-timeout", String(UP_WAIT_SECONDS)],
    (UP_WAIT_SECONDS + 60) * 1000,
  );

  const serve = await containersOf("serve");
  expect(serve.map(({ state, health }) => [state, health])).toEqual([["running", "healthy"]]);
  expect((await psql("SELECT value FROM e2e_kept")).trim()).toBe(value);
  const logs = await compose().ensure(["logs", "--no-color", "migrate"], 60_000);
  expect(logs).toContain(`표가 이미 마지막 판(${productRevision()})입니다.`);
});

test("백엔드 하나를 다시 만들어도 프록시가 새 주소를 따라 15초 안에 다시 200 을 낸다", async ({
  request,
}) => {
  const before = await request.get(`${ORIGIN}/portal/health`);
  expect(before.status()).toBe(200);

  await compose().ensure(["up", "--detach", "--force-recreate", "--no-deps", "portal"], 120_000);

  const started = Date.now();
  let status = 0;
  // 요청마다 남은 시간만큼만 기다려, 느리게 온 200 이 기한을 넘겨 통과하지 못하게 한다.
  while (Date.now() - started < RECOVER_MS) {
    try {
      const remaining = Math.max(1_000, RECOVER_MS - (Date.now() - started));
      status = (await request.get(`${ORIGIN}/portal/health`, { timeout: remaining })).status();
    } catch {
      status = 0;
    }
    if (status === 200) {
      break;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  expect(status, `${String(RECOVER_MS)}ms 안에 200 으로 돌아오지 않았다`).toBe(200);
  expect(Date.now() - started, `200 이 ${String(RECOVER_MS)}ms 를 넘겨 도착했다`).toBeLessThan(
    RECOVER_MS + 1_000,
  );
});

// 프록시의 바깥 DNS 를 끊는 덧씌움. 아직 없는 이름을 물으면 Docker 의 내장 DNS 가 `Server failure` 를 돌려준다.
const DEAD_DNS_OVERLAY = join(dirname(import.meta.dirname), "compose.dead-dns.yaml");

test("프록시가 serve 를 못 찾고 시작해도 serve 가 건강해지면 15초 안에 최종 사용자 길이 열린다", async ({
  request,
}) => {
  test.setTimeout(RESTART_TIMEOUT_MS);
  const upServe = [
    "up",
    "--detach",
    "--no-deps",
    "--wait",
    "--wait-timeout",
    String(UP_WAIT_SECONDS),
    "serve",
  ];
  const serveTimeoutMs = (UP_WAIT_SECONDS + 60) * 1000;
  try {
    // serve 가 없는 채로 프록시를 다시 만든다. 프록시가 시작할 때 serve 이름을 물으면 내장 DNS 가 `Server failure` 를 돌려준다.
    // 출시 PR 의 CI 에서는 serve 가 postgres 와 migrate 를 기다리느라 프록시보다 늦게 떠서 같은 일이 났다.
    await compose().ensure(["rm", "--stop", "--force", "serve"], 2 * 60_000);
    await compose().ensure(["up", "--detach", "--force-recreate", "--no-deps", "proxy"], 120_000, [
      DEAD_DNS_OVERLAY,
    ]);
    await compose().ensure(upServe, serveTimeoutMs);

    // 시험이 만들려던 상황이 맞는지 본다. 프록시가 시작할 때 serve 이름을 못 풀었어야 한다.
    const logs = await compose().ensure(["logs", "--no-color", "proxy"], 60_000);
    expect(logs).toContain("serve could not be resolved (2: Server failure)");

    const started = Date.now();
    let status = 0;
    while (Date.now() - started < RECOVER_MS) {
      try {
        const remaining = Math.max(1_000, RECOVER_MS - (Date.now() - started));
        status = (await request.post(`${ORIGIN}/end-user/runs`, { timeout: remaining })).status();
      } catch {
        status = 0;
      }
      // 토큰 없는 요청이라 serve 가 거절하는 것이 맞다. 프록시가 serve 에 닿았다는 것만 본다(닿지 못하면 502 다).
      if (status !== 0 && status < 500) {
        break;
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    // 아래 finally 가 프록시를 다시 만들면 이 프록시의 로그가 사라지므로, 실패 메시지에 지금 끝부분을 싣는다.
    const proxyTail = (
      await compose().ensure(
        ["logs", "--no-color", "--timestamps", "--tail", "15", "proxy"],
        60_000,
      )
    ).trim();
    expect(
      status,
      `serve 가 건강해진 뒤 ${String(RECOVER_MS)}ms 안에 프록시가 길을 열지 않았다. 프록시 로그의 끝:\n${proxyTail}`,
    ).toBeLessThan(500);
    expect(status, "프록시가 응답하지 않았다").not.toBe(0);
  } finally {
    // 뒤의 사례가 평소 프록시를 지나도록 되돌린다. 앞에서 실패해 serve 가 없을 수 있으므로 serve 부터 올리되,
    // serve 가 올라오지 못해도 프록시는 죽은 DNS 덧씌움 없이 다시 만든다(안 그러면 뒤의 사례가 모두 연쇄로 실패한다).
    try {
      await compose().ensure(upServe, serveTimeoutMs);
    } finally {
      await compose().ensure(["up", "--detach", "--force-recreate", "--no-deps", "proxy"], 120_000);
    }
  }
});

test("토큰 끝점은 짧은 시간에 요청이 몰리면 429 를 내고 앞선 요청은 막지 않는다", async ({
  request,
}) => {
  const url = `${ORIGIN}/portal/sites/${PREVIEW_SITE}/token`;
  const statuses: number[] = [];
  for (let sent = 0; sent < 60; sent += 1) {
    const response = await request.post(url);
    statuses.push(response.status());
  }
  // 확인 전의 요청이라 막히지 않은 쪽은 401 이다. 앞쪽은 상한 안이라 429 가 아니고 뒤쪽은 상한을 넘어 429 다.
  expect(statuses[0]).toBe(401);
  expect(statuses).toContain(429);
});
