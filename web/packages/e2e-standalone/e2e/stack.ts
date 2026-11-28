/**
 * 단독 배포 e2e 의 준비(globalSetup, release-image 티켓 09). 지은 이미지 다섯과 배포 파일 묶음(`deploy/standalone/`)을 04 의
 * 도구(`tools/release.py bundle`)로 묶어 임시 폴더에 풀고, 운영자가 채울 것(인증서와 키, 사이트 파일, 위젯 테스트 페이지
 * 설정과 개인 키, 환경 변수 파일)을 시험 값으로 채워 `docker compose up` 으로 띄운다. 시험이 끝나면 그 실행이 만든 컨테이너,
 * 볼륨, 네트워크를 지운다.
 *
 * - 이미지: 이름공간과 태그를 환경 변수로 받으면(`NAMESPACE_ENV`, `VERSION_ENV`) 그 이미지로 띄운다. 없으면 저장소에서 다섯을
 *   지어 `LOCAL_NAMESPACE`/`LOCAL_VERSION` 으로 띄운다. PostgreSQL 은 묶음의 compose 가 digest 로 고정한 공식 이미지를 받고,
 *   migrate 는 serve 와 같은 이미지다(postgres-foundation 티켓 02). 위젯 쪽도 PostgreSQL 이 하나 더 있고 widget-admin-migrate 는 위젯 관리 서버와 같은 이미지다(widget-admin-server 티켓 04).
 * - 픽스처: serve 에는 모델 없이 정해진 답을 내는 `echo` 에이전트를 넣는다. 길은 시험만 쓰는 덧씌움 `compose.fixtures.yaml`
 *   의 일회용 서비스다. serve 와 같은 이미지에 플러그인 볼륨을 붙여 `cp` 로 복사하므로 이름 있는 볼륨의 첫 채움(이미지의
 *   내용을 소유자째 복사)을 깨지 않는다. 그 파일은 이 패키지가 가진다.
 * - 거두기: 프로젝트 이름이 실행마다 새로 지어져(`agent-os-e2e-<무작위>`) `down --volumes` 가 그 실행의 것만 지운다. 이미지는
 *   지우지 않는다(다음 실행의 캐시다).
 * - 발행 포트는 배포 파일 묶음의 것 그대로(443, 80, 127.0.0.1:3000)라 같은 포트를 쓰는 다른 실행이 있으면 시작에서 던진다.
 */

import { randomBytes } from "node:crypto";
import { chmodSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { delimiter, dirname, join } from "node:path";
import {
  accepts,
  AUDIENCE,
  createStack,
  interpreter,
  ISSUER,
  KEY_ID,
  publish,
  REPO,
  siteKey,
  writeEchoAgent,
} from "@agent-os/e2e-stack";
import { Compose, repositoryName, succeed } from "./docker.ts";
import {
  ADMIN_TOKEN_ENV,
  API_KEY_ENV,
  CALC_AGENT,
  DIR_ENV,
  FILES_ENV,
  FIXTURE_AGENT,
  LLM_ENV,
  LOCAL_NAMESPACE,
  LOCAL_VERSION,
  NAMESPACE_ENV,
  NO_IPV6_ENV,
  ORIGIN,
  PROJECT_ENV,
  UP_WAIT_SECONDS,
  VERSION_ENV,
  VERSION_OUT_ENV,
} from "./env.ts";
import { fillEnv, portalConfigToml, siteFileToml, type E2eSite } from "./files.ts";

const PACKAGE = dirname(import.meta.dirname);
const LOGS = join(PACKAGE, "test-results");
const OVERLAY = join(PACKAGE, "compose.fixtures.yaml");
const NO_IPV6_OVERLAY = join(PACKAGE, "compose.no-ipv6.yaml");
const SOURCE_LABEL = "agent-os-e2e";
const PUBLISHED_PORTS = [443, 80, 3000];

const MINUTE_MS = 60_000;
const BUILD_MS = 15 * MINUTE_MS;

// 위젯 테스트 페이지가 그리는 사이트 둘. 둘째는 저장소의 계산 에이전트(이미지에 든 예시 MCP 서버를 쓴다)를 연다.
const PREVIEW: E2eSite = {
  name: "preview",
  issuer: "https://preview.standalone.e2e.example",
  agent: FIXTURE_AGENT,
  heading: "단독 배포 미리보기",
  theme: "jacho",
};
const CALC: E2eSite = {
  name: "calc",
  issuer: "https://calc.standalone.e2e.example",
  agent: CALC_AGENT,
  heading: "계산 에이전트",
  theme: "guncheong",
};
// 시험이 e2e-stack 의 토큰 서명(`signToken`)으로 최종 사용자 경로를 직접 부를 때 쓰는 사이트. 위젯 테스트 페이지 설정에는
// 들지 않는다.
const DIRECT: E2eSite = {
  name: "direct",
  issuer: ISSUER,
  agent: CALC_AGENT,
  heading: "직접 호출",
  theme: "jacho",
};

export default async function globalSetup(): Promise<() => Promise<void>> {
  const stack = createStack({ prefix: "agent-os-standalone-e2e-", logs: LOGS });
  let compose: Compose | undefined;
  const cleanup = async (): Promise<void> => {
    let downFailure: string | undefined;
    try {
      if (compose !== undefined) {
        // 로그를 못 남겨도 배치는 내려야 한다. 남은 컨테이너가 443·80·3000 을 쥐면 다음 실행이 포트 확인에서 막힌다.
        try {
          const logs = await compose.call(["logs", "--no-color", "--timestamps"], MINUTE_MS);
          mkdirSync(LOGS, { recursive: true });
          writeFileSync(join(LOGS, "compose.log"), `${logs.stdout}\n${logs.stderr}`);
        } catch (error) {
          console.error(`compose 로그를 남기지 못했다: ${String(error)}`);
        }
        const down = await compose.call(
          ["down", "--volumes", "--remove-orphans", "--timeout", "10"],
          2 * MINUTE_MS,
        );
        if (down.code !== 0) {
          downFailure = `compose down 이 ${down.timedOut ? "제한 시간을 넘겼다" : `종료 ${String(down.code)}`}:\n${down.stderr}`;
        }
      }
    } finally {
      await stack.teardown();
    }
    if (downFailure !== undefined) {
      throw new Error(`배치가 남았을 수 있다. ${downFailure}`);
    }
  };

  try {
    await requireFreePorts();
    const llm = process.env[LLM_ENV] === "1";
    const apiKey = process.env[API_KEY_ENV] ?? "";
    if (llm && apiKey === "") {
      throw new Error(`${LLM_ENV}=1 인데 ${API_KEY_ENV} 가 없다`);
    }

    const { namespace, version } = await imagesToRun();
    const python = interpreter();

    // 04 의 도구로 묶음을 짓고 풀어 배포 폴더를 얻는다.
    const dist = join(stack.work, "dist");
    const tarball = (
      await succeed(
        python,
        [
          "tools/release.py",
          "bundle",
          "--number",
          version,
          "--namespace",
          namespace,
          "--out",
          dist,
        ],
        { cwd: REPO, timeoutMs: MINUTE_MS },
      )
    ).trim();
    const unpacked = join(stack.work, "unpacked");
    await succeed(
      python,
      [
        "-I",
        "-c",
        "import sys, tarfile; tarfile.open(sys.argv[1]).extractall(sys.argv[2], filter='data')",
        tarball,
        unpacked,
      ],
      { cwd: stack.work, timeoutMs: MINUTE_MS },
    );
    const dir = join(unpacked, `agent-os-${version}`);

    await fillOperatorFiles(dir, { llm, apiKey });

    const project = `agent-os-e2e-${randomBytes(4).toString("hex")}`;
    const overlays = process.env[NO_IPV6_ENV] === "1" ? [NO_IPV6_OVERLAY] : [];
    compose = new Compose(project, dir, overlays);
    // 플러그인 볼륨의 첫 채움을 픽스처 서비스가 맡는다(위 머리 주석). 그 서비스는 `up` 에 넣지 않는다.
    await compose.ensure(["run", "--rm", "fixtures"], 5 * MINUTE_MS, [OVERLAY]);
    const up = await compose.call(
      ["up", "--detach", "--wait", "--wait-timeout", String(UP_WAIT_SECONDS)],
      (UP_WAIT_SECONDS + 60) * 1000,
    );
    if (up.code !== 0) {
      const state = await compose.call(["ps", "--all"], MINUTE_MS);
      throw new Error(
        `docker compose up 이 종료 ${String(up.code)}:\n${up.stdout}\n${up.stderr}\n${state.stdout}`,
      );
    }

    publish(PROJECT_ENV, project);
    publish(DIR_ENV, dir);
    publish(FILES_ENV, overlays.join(delimiter));
    publish(VERSION_OUT_ENV, version);
    return cleanup;
  } catch (error: unknown) {
    await cleanup();
    throw error;
  }
}

/** 발행할 호스트 포트를 이미 누가 듣고 있으면 던진다. 단독 배포는 포트를 바꿀 수 없다. */
async function requireFreePorts(): Promise<void> {
  const busy: number[] = [];
  for (const port of PUBLISHED_PORTS) {
    if (await accepts(port)) {
      busy.push(port);
    }
  }
  if (busy.length > 0) {
    throw new Error(
      `호스트의 포트 ${busy.join(", ")} 를 다른 프로세스가 듣고 있다. 단독 배포는 443, 80, 127.0.0.1:3000 에 발행한다. 비운 뒤 다시 친다`,
    );
  }
}

/** 이름공간과 태그를 고른다. 둘 다 환경 변수로 받았으면 그대로 쓰고, 없으면 저장소에서 다섯을 짓는다. */
async function imagesToRun(): Promise<{ namespace: string; version: string }> {
  const given = process.env[NAMESPACE_ENV];
  const tag = process.env[VERSION_ENV];
  if (given !== undefined && tag !== undefined) {
    return { namespace: given, version: tag };
  }
  if (given !== undefined || tag !== undefined) {
    throw new Error(`${NAMESPACE_ENV} 와 ${VERSION_ENV} 는 둘 다 주거나 둘 다 주지 않는다`);
  }
  const revision = (
    await succeed("git", ["rev-parse", "HEAD"], { cwd: REPO, timeoutMs: MINUTE_MS })
  ).trim();
  const [
    serveRepository,
    adminRepository,
    widgetRepository,
    portalRepository,
    widgetAdminRepository,
  ] = await Promise.all([
    repositoryName("serve"),
    repositoryName("admin"),
    repositoryName("widget"),
    repositoryName("portal"),
    repositoryName("widget-admin"),
  ]);
  const name = (repository: string): string => `${LOCAL_NAMESPACE}/${repository}:${LOCAL_VERSION}`;
  const label = [
    ["--build-arg", `IMAGE_VERSION=${LOCAL_VERSION}`],
    ["--build-arg", `IMAGE_REVISION=${revision}`],
    ["--build-arg", `IMAGE_SOURCE=${SOURCE_LABEL}`],
  ].flat();
  const web = (image: string, repository: string): Promise<string> =>
    succeed(
      "docker",
      [
        "build",
        "--file",
        `deploy/images/${image}.Dockerfile`,
        ...label,
        "--tag",
        name(repository),
        "web",
      ],
      { cwd: REPO, timeoutMs: BUILD_MS },
    );
  // 파이썬 이미지 둘(serve, 위젯 관리 서버)은 같은 꼴로 짓는다. 컨텍스트는 저장소 루트다.
  const python = (image: string, repository: string): Promise<string> =>
    succeed(
      "docker",
      [
        "build",
        "--file",
        `deploy/images/${image}.Dockerfile`,
        "--build-arg",
        `APP_VERSION=${LOCAL_VERSION}`,
        "--build-arg",
        `REVISION=${revision}`,
        "--build-arg",
        `SOURCE=${SOURCE_LABEL}`,
        "--tag",
        name(repository),
        ".",
      ],
      { cwd: REPO, timeoutMs: BUILD_MS },
    );
  await Promise.all([
    python("serve", serveRepository),
    web("admin", adminRepository),
    web("widget", widgetRepository),
    web("portal", portalRepository),
    python("widget-admin", widgetAdminRepository),
  ]);
  return { namespace: LOCAL_NAMESPACE, version: LOCAL_VERSION };
}

interface Mode {
  readonly llm: boolean;
  readonly apiKey: string;
}

/**
 * 풀어 놓은 배포 폴더에서 운영자가 채우는 자리를 시험 값으로 채운다. 인증서와 키는 모두에게 읽히게 둔다(운영에서는 키를
 * 그룹에만 연다. 시험은 소유를 바꿀 권한이 없을 수 있다).
 */
async function fillOperatorFiles(dir: string, mode: Mode): Promise<void> {
  await succeed(
    "openssl",
    [
      "req",
      "-x509",
      "-newkey",
      "rsa:2048",
      "-nodes",
      "-keyout",
      join(dir, "tls", "privkey.pem"),
      "-out",
      join(dir, "tls", "fullchain.pem"),
      "-days",
      "2",
      "-subj",
      "/CN=localhost",
      "-addext",
      "subjectAltName=DNS:localhost,IP:127.0.0.1",
    ],
    { cwd: dir, timeoutMs: MINUTE_MS },
  );
  chmodSync(join(dir, "tls", "privkey.pem"), 0o644);

  const key = siteKey();
  writeFileSync(
    join(dir, "site", "sites.toml"),
    siteFileToml({
      origin: ORIGIN,
      audience: AUDIENCE,
      kid: KEY_ID,
      publicPem: key.publicPem,
      sites: [PREVIEW, CALC, DIRECT],
    }),
  );
  writeFileSync(
    join(dir, "portal", "portal.toml"),
    portalConfigToml({ origin: ORIGIN, kid: KEY_ID, sites: [PREVIEW, CALC] }),
  );
  const privatePem = join(dir, "portal", "keys", "portal.pem");
  writeFileSync(privatePem, key.privateKey.export({ type: "pkcs8", format: "pem" }));
  chmodSync(privatePem, 0o644);

  const adminToken = `e2e-admin-${randomBytes(16).toString("hex")}`;
  const channelToken = `e2e-channel-${randomBytes(16).toString("hex")}`;
  // 배포 안내가 운영자에게 시키는 꼴(`openssl rand -hex 32`, 영문자와 숫자만)과 같은 값이다. 시험은 이 값을 넘겨받지 않는다.
  // 데이터베이스는 PostgreSQL 컨테이너 안의 psql 로 보고, 그 컨테이너의 유닉스 소켓은 비밀번호를 묻지 않는다.
  const databasePassword = randomBytes(32).toString("hex");
  // 위젯 쪽 데이터베이스의 비밀번호는 Agent OS 쪽과 다른 값이다(배포 안내가 그렇게 시킨다).
  const widgetDatabasePassword = randomBytes(32).toString("hex");
  publish(ADMIN_TOKEN_ENV, adminToken);
  const template = readFileSync(join(dir, ".env.example"), "utf-8");
  writeFileSync(
    join(dir, ".env"),
    fillEnv(template, {
      AGENT_OS_ADMIN_TOKEN: adminToken,
      AGENT_OS_CHANNEL_TOKEN: channelToken,
      AGENT_OS_DATABASE_PASSWORD: databasePassword,
      WIDGET_ADMIN_DATABASE_PASSWORD: widgetDatabasePassword,
      ...(mode.llm ? { ANTHROPIC_API_KEY: mode.apiKey } : {}),
    }),
  );

  // serve 의 플러그인 볼륨에 넣을 픽스처. 덧씌움의 일회용 서비스가 ./fixtures 를 읽는다.
  writeEchoAgent(join(dir, "fixtures"));
}
