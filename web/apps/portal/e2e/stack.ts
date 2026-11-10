/**
 * 질문 페이지 e2e 의 준비(globalSetup, pilot-portal 티켓 06). 실제 `serve`(픽스처 플러그인), 같은 사이트 파일로 빌드한 실제
 * 위젯 Next, 실제 질문 페이지, 셋을 한 출처 아래에 모으는 같은 출처의 중계, 폼으로 확인 끝점을 부르는 다른 출처의 페이지를
 * 띄운다. 프로세스와 서버를 띄우고 거두는 몸통은 패키지 `@agent-os/e2e-stack` 이 내고, 여기에는 질문 페이지만의 몫(설정과
 * 사이트 파일, 두 번째 앱 프로세스, 출처의 모양)이 남는다. 선례는 위젯 e2e 의 준비(`apps/widget/e2e/stack.ts`)다.
 *
 * - 출처는 모두 `*.localhost` 호스트 이름이다. 질문 페이지는 `portal.localhost`(중계의 포트), 다른 출처의 페이지는
 *   `other.localhost`, 사이트 하나만 적은 둘째 질문 페이지는 `second.localhost` 이고 포트로 가른다. 이름 풀기는 Playwright
 *   설정이 맡는다. 첫 질문 페이지의 `public_origin` 은 중계의 주소이고 사이트 파일의 모든 사이트가 그것과 둘째 출처를 허용
 *   출처로 든다. 둘째 질문 페이지는 중계를 거치지 않고 제 주소로 열고, 그 `public_origin` 이 둘째 출처다.
 * - 사이트는 넷이다(`sites.ts`). 키 쌍은 `node:crypto` 가 짓고 개인 키는 작업 폴더의 파일로만 간다. 질문 페이지의 `kid` 는
 *   사이트 파일의 모든 사이트가 같은 공개 키로 든다.
 * - 위젯 Next 는 질문 페이지가 쓰는 사이트 파일로 빌드한다. 허용 출처가 빌드에 박힌다. 위젯의 시작 래퍼는 이 앱이 import 하지
 *   않고 프로세스로만 부른다(앱 사이 import 는 층 경계가 막는다).
 * - 질문 페이지 프로세스의 출력은 러너가 받는 대로 작업 폴더의 파일에 이어 쓰고 그 경로를 시험에 넘긴다(`env.ts` 의
 *   `portalOutput()`). 끝에 `test-results/` 의 로그로도 남는다. 쿠키와 토큰이 출력에 없는지는 시험(티켓 07)이 본다.
 * - 거두는 것은 위젯 e2e 와 같이 `kill()` 이다. 중계와 다른 출처의 페이지는 이 프로세스 안의 서버라 닫는다.
 */

import { appendFileSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import {
  accepts,
  AUDIENCE,
  createStack,
  freePort,
  interpreter,
  KEY_ID,
  MCP_FIXTURE_SERVER,
  publish,
  siteKey,
  startRelay,
  startServe,
  until,
  writeFixturePlugins,
  type SiteKey,
  type Stack,
} from "@agent-os/e2e-stack";
import { stringify } from "smol-toml";
import {
  OTHER_ORIGIN_ENV,
  PORTAL_ORIGIN_ENV,
  PORTAL_OUTPUT_ENV,
  SECOND_ORIGIN_ENV,
  TRACES_DIR_ENV,
} from "./env.ts";
import { startOtherPage } from "./other-page.ts";
import { AGENT, SITES, type E2eSite } from "./sites.ts";

const APP = dirname(import.meta.dirname);
const WIDGET = join(dirname(APP), "widget");
const LOGS = join(APP, "test-results");
const QUIET = { NEXT_TELEMETRY_DISABLED: "1" };
// serve 가 읽는 토큰 변수. 위젯 Next 로 가는 환경에서는 벗긴다.
const SERVE_TOKENS = ["AGENT_OS_ADMIN_TOKEN", "AGENT_OS_CHANNEL_TOKEN"];
// 질문 페이지가 서면 찍는 시작 로그의 가운데 글(`server/diagnostics.ts` 의 `listenLine`).
const LISTENING = "에 섰다";

export default async function globalSetup(): Promise<() => Promise<void>> {
  const stack = createStack({ prefix: "agent-os-portal-e2e-", logs: LOGS });
  try {
    const [relayPort, portalPort, otherPort, secondPort, nextPort] = [
      await freePort(),
      await freePort(),
      await freePort(),
      await freePort(),
      await freePort(),
    ];
    const portalOrigin = `http://portal.localhost:${String(relayPort)}`;
    const otherOrigin = `http://other.localhost:${String(otherPort)}`;
    const secondOrigin = `http://second.localhost:${String(secondPort)}`;

    const python = interpreter();
    const plugins = join(stack.work, "plugins");
    const gates = join(stack.work, "gates");
    mkdirSync(gates);
    writeFixturePlugins(plugins, python, MCP_FIXTURE_SERVER, gates);
    const key = siteKey();
    const siteFile = join(stack.work, "sites.toml");
    writeFileSync(siteFile, siteFileToml([portalOrigin, secondOrigin], key));
    const traces = join(stack.work, "traces");

    const serveUrl = await startServe(stack, { plugins, traces, siteFile, python });

    await buildWidget(stack, siteFile);
    const widget = stack.launch(
      "widget",
      process.execPath,
      [join(WIDGET, "tools", "start.ts"), "start", "--port", String(nextPort)],
      WIDGET,
      widgetEnv(siteFile),
    );
    await until(widget, "위젯 Next 가 서지 않았다", async () =>
      (await accepts(nextPort)) ? nextPort : null,
    );

    const output = join(stack.work, "portal-output.log");
    writeFileSync(output, "");
    await startPortal(stack, {
      name: "portal",
      portalOrigin,
      portalPort,
      sites: SITES,
      siteFile,
      key,
      output,
    });
    // 둘째 인스턴스. 설정에 사이트 하나만 적은 질문 페이지가 제 루프백 주소에 선다(중계 뒤가 아니다). 위젯 번들은 그 출처에
    // 없어 위젯은 그리지 않고, 사이트가 하나일 때 셀렉트와 라벨이 숨는 것만 본다(명세 "Playwright e2e").
    const [onlySite] = SITES;
    if (onlySite === undefined) {
      throw new Error("e2e 사이트 목록이 비었다");
    }
    await startPortal(stack, {
      name: "portal-second",
      portalOrigin: secondOrigin,
      portalPort: secondPort,
      sites: [onlySite],
      siteFile,
      key,
    });

    stack.own(
      await startRelay(relayPort, {
        serve: serveUrl,
        next: `http://127.0.0.1:${String(nextPort)}`,
        portal: `http://127.0.0.1:${String(portalPort)}`,
      }),
    );
    const [first] = SITES;
    if (first === undefined) {
      throw new Error("e2e 사이트 목록이 비었다");
    }
    stack.own(await startOtherPage(otherPort, { portalOrigin, siteName: first.name }));

    publish(PORTAL_ORIGIN_ENV, portalOrigin);
    publish(OTHER_ORIGIN_ENV, otherOrigin);
    publish(SECOND_ORIGIN_ENV, secondOrigin);
    publish(TRACES_DIR_ENV, traces);
    publish(PORTAL_OUTPUT_ENV, output);
    return () => stack.teardown();
  } catch (error: unknown) {
    await stack.teardown();
    throw error;
  }
}

/** 사이트마다 항목 하나. 모두 같은 공개 키와 같은 허용 출처를 들고 상한만 사이트가 정한다. */
function siteFileToml(origins: readonly string[], key: SiteKey): string {
  return stringify({
    schema_version: "1",
    sites: SITES.map((site) => ({
      issuer: site.issuer,
      audience: AUDIENCE,
      allowed_origins: [...origins],
      agents: [AGENT],
      public_keys: [{ kid: KEY_ID, pem: key.publicPem }],
      ...(site.hourlyRunsPerSite === undefined
        ? {}
        : { limits: { hourly_runs_per_site: site.hourlyRunsPerSite } }),
    })),
  });
}

/** 질문 페이지 설정. 개인 키는 설정 파일 옆 `keys/` 에 둔다. */
function configToml(publicOrigin: string, port: number, sites: readonly E2eSite[]): string {
  return stringify({
    schema_version: "1",
    portal: {
      public_origin: publicOrigin,
      private_key: "keys/portal.pem",
      kid: KEY_ID,
      port,
    },
    sites: sites.map((site) => ({
      name: site.name,
      issuer: site.issuer,
      agent: AGENT,
      heading: site.heading,
      ...(site.intro === undefined ? {} : { intro: site.intro }),
      theme: site.theme,
      ...(site.mode === undefined ? {} : { mode: site.mode }),
      ...(site.notice === undefined ? {} : { notice: site.notice }),
      ...(site.reportUrl === undefined ? {} : { report_url: site.reportUrl }),
      assurance: site.assurance,
    })),
  });
}

interface PortalLaunch {
  /** 프로세스와 설정 파일의 이름. 같은 작업 폴더에서 질문 페이지가 둘 서므로 가른다. */
  readonly name: string;
  readonly portalOrigin: string;
  readonly portalPort: number;
  readonly sites: readonly E2eSite[];
  readonly siteFile: string;
  readonly key: SiteKey;
  /** 프로세스의 출력을 받는 대로 이어 쓸 파일. 없으면 모으지 않는다. */
  readonly output?: string;
}

/** 질문 페이지를 띄우고 서는 것을 기다린다. 설정과 개인 키는 작업 폴더에 쓴다. */
async function startPortal(stack: Stack, launch: PortalLaunch): Promise<void> {
  const dir = join(stack.work, launch.name);
  mkdirSync(join(dir, "keys"), { recursive: true });
  const config = join(dir, "portal.toml");
  writeFileSync(config, configToml(launch.portalOrigin, launch.portalPort, launch.sites));
  writeFileSync(
    join(dir, "keys", "portal.pem"),
    launch.key.privateKey.export({ type: "pkcs8", format: "pem" }),
  );
  const portal = stack.launch(
    launch.name,
    process.execPath,
    [
      "--disable-warning=ExperimentalWarning",
      join(APP, "tools", "start.ts"),
      "--config",
      config,
      "--site-file",
      launch.siteFile,
    ],
    APP,
    process.env,
  );
  const { output } = launch;
  if (output !== undefined) {
    for (const stream of [portal.child.stdout, portal.child.stderr]) {
      stream?.on("data", (chunk: Buffer) => {
        appendFileSync(output, chunk);
      });
    }
  }
  await until(portal, "질문 페이지가 서지 않았다", () =>
    portal.output().includes(LISTENING) ? true : null,
  );
}

/** 위젯 Next(빌드와 start)의 환경. 이 셸의 환경에서 serve 의 토큰 변수를 벗기고 사이트 파일을 준다. */
function widgetEnv(siteFile: string): NodeJS.ProcessEnv {
  const env: NodeJS.ProcessEnv = { ...process.env, ...QUIET, AGENT_OS_SITE_FILE: siteFile };
  for (const name of SERVE_TOKENS) {
    Reflect.deleteProperty(env, name);
  }
  return env;
}

/**
 * 그 사이트 파일로 위젯을 빌드한다. 허용 출처가 빌드에 박힌다. 위젯의 시작 래퍼로 빌드해 글꼴 파일의 복사와 페이지 안
 * 번들의 빌드까지 운영과 같은 길을 지난다. 빌드는 위젯 앱의 `.next/`, `public/fonts/`, `public/element.js` 를 다시 쓴다.
 */
async function buildWidget(stack: Stack, siteFile: string): Promise<void> {
  const built = stack.launch(
    "build",
    process.execPath,
    [join(WIDGET, "tools", "start.ts"), "build"],
    WIDGET,
    widgetEnv(siteFile),
  );
  const code = await new Promise<number | null>((resolve) => {
    built.child.once("exit", resolve);
  });
  if (code !== 0) {
    throw new Error(`위젯을 빌드하지 못했다(종료 ${String(code)}):\n${built.output()}`);
  }
}
