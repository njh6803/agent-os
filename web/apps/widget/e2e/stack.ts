/**
 * 위젯 e2e 의 준비(globalSetup, web-widget 티켓 06). 실제 `serve`, 실제 위젯 Next(미끼 사이트 파일로 빌드하고 진짜 사이트
 * 파일로 띄운다), 둘을 한 출처 아래에 모으는 같은 출처의 중계, 두 방식으로 위젯을 품는 다른 출처의 사이트(`site.ts`)를
 * 띄운다. 위젯만 다시 띄우는 손잡이(`control.ts`)도 연다. 기본은 모델을
 * 부르지 않는다. 프로세스와 서버를 띄우고 거두는 몸통(`serve`, 중계, 픽스처 플러그인, 사이트 키, 기다리기와 끄기)은 패키지
 * `@agent-os/e2e-stack` 이 내고, 여기에는 위젯만의 몫(위젯 Next 의 빌드와 start, 사이트 서버, 출처의 모양)이 남는다.
 * 선례는 관리 화면 e2e 의 준비(`apps/admin/e2e/stack.ts`)다.
 *
 * 실제 모델 e2e(티켓 11)를 감싸는 파이썬 시험이 `LLM_ENV` 를 `1` 로 주면 둘이 더해진다. 임시 플러그인 루트에 저장소의
 * 플러그인 루트를 먼저 옮기고(`copyRepoPlugins`), 사이트 파일의 에이전트에 계산 에이전트와 기본 에이전트 `assistant` 를
 * 넣는다. `DOC_SEARCH_URL_ENV` 가 있으면 `assistant` 의 문서 검색 연결이 그 주소(파이썬 시험이 띄운 가짜 검색 서버)를
 * 가리키게 바꿔 쓴다. 이 에이전트들만 모델을 부르고, 키는 serve 환경이 물려준다. 그 시험이 `TRACES_ENV` 로 준 자리에 serve 가 트레이스를 남기고, 주지 않으면 작업
 * 폴더에 남겨 끝에 지운다. 어느 쪽이든 그 폴더는 시험에 넘어간다(`env.ts` 의 `traces()`).
 *
 * - 출처는 모두 `*.localhost` 호스트 이름이다. 위젯은 `widget.localhost`, 허용 출처의 사이트는 `site.localhost`, 허용 밖
 *   출처의 사이트는 `other.localhost` 이고 포트로 가른다. 표기 규칙은 IP 호스트의 출처도 지나보내지만 CSP3 의 문법은
 *   host-part 대조를 domain 에만 맞춘다(`tests/fixtures/site_file/README.md`). 브라우저는 `*.localhost` 를 보안 맥락으로
 *   보아 TLS 없이도 위젯의 `crypto.randomUUID` 가 선다. 이름 풀기는 Playwright 설정이 맡는다.
 * - 포트를 먼저 고른다. 허용 출처가 사이트 파일에 실리기 때문이다. 빌드는 사이트 파일을 읽지 않아(widget-runtime-values
 *   티켓 02) 산출물에는 허용 출처도 글자 수 상한도 박히지 않는다. 그 값은 위젯이 뜰 때 받는다. 응답 머리의 `frame-ancestors`
 *   는 서비스 시작이 쓰는 사본으로, 입력창의 상한은 값 파일(`/widget/runtime.json`)로 나간다. 빌드가 사이트 파일을 읽는
 *   회귀를 잡으려고 빌드에는 다른 출처와 상한을 적은 미끼 사이트 파일을 주고, 띄울 때 진짜 파일을 준다.
 * - 사이트 파일은 사이트 하나이고 `request_chars` 를 기본값과 다른 `SITE_REQUEST_CHARS` 로 적는다. 입력창은 값 파일로, 서버는
 *   사이트 파일로 같은 상한을 따른다.
 * - 사이트의 키 쌍은 `node:crypto` 가 짓고 개인 키는 이 프로세스의 사이트 서버만 든다.
 * - serve 의 환경에는 부모의 환경을 펼친다(관리 화면 e2e 와 같다).
 *   위젯 Next 는 API 를 모르고(ADR 0024) 사이트 파일만 읽는다.
 * - 거두는 것은 관리 화면 e2e 와 같이 `kill()` 이다(제때 끝나지 않을 때만 SIGKILL). 그 준비가 잰 프로세스 트리의 모양
 *   (`.scratch/web-admin/probes/e2e_process_tree.mjs`, 관리 화면의 래퍼를 쟀다)을 위젯에도 쓴다. 위젯의 시작 래퍼도 next CLI
 *   를 같은 프로세스에서 부른다는 것은 재지 않고 `tools/start.ts` 를 읽었다. 중계와 사이트는 이 프로세스 안의 서버라 닫는다.
 * - 세 프로세스(serve, build, widget)의 출력은 끝에 `test-results/` 에 남긴다. 토큰과 개인 키는 싣지 않는다. 다시 띄운
 *   위젯은 `widget-restart-<번호>` 로 따로 남는다.
 */

import { mkdirSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import {
  accepts,
  AGENTS,
  ASSISTANT_AGENT,
  copyRepoPlugins,
  createStack,
  freePort,
  interpreter,
  LLM_AGENT,
  MARKDOWN_IMAGE_PATH,
  MCP_FIXTURE_SERVER,
  pointDocSearchAt,
  prepareDatabase,
  publish,
  REPO,
  siteFileToml,
  siteKey,
  startRelay,
  startServe,
  stop,
  until,
  writeFixturePlugins,
  type Launched,
  type Stack,
} from "@agent-os/e2e-stack";
import { startControl } from "./control";
import {
  CONTROL_ENV,
  DECOY_ORIGIN,
  DECOY_REQUEST_CHARS,
  DOC_SEARCH_URL_ENV,
  GATES_ENV,
  LLM_ENV,
  OTHER_ORIGIN_ENV,
  SITE_ORIGIN_ENV,
  SITE_REQUEST_CHARS,
  TRACES_DIR_ENV,
  TRACES_ENV,
  WIDGET_ORIGIN_ENV,
} from "./env";
import { startSite } from "./site";

const APP = dirname(import.meta.dirname);
const LOGS = join(APP, "test-results");
const QUIET = { NEXT_TELEMETRY_DISABLED: "1" };

export default async function globalSetup(): Promise<() => Promise<void>> {
  const stack = createStack({ prefix: "agent-os-widget-e2e-", logs: LOGS });
  try {
    const [relayPort, sitePort, nextPort] = [await freePort(), await freePort(), await freePort()];
    const widgetOrigin = `http://widget.localhost:${String(relayPort)}`;
    const siteOrigin = `http://site.localhost:${String(sitePort)}`;
    const otherOrigin = `http://other.localhost:${String(sitePort)}`;

    const llm = process.env[LLM_ENV] === "1";
    const python = interpreter();
    const plugins = join(stack.work, "plugins");
    const gates = join(stack.work, "gates");
    mkdirSync(gates);
    if (llm) {
      copyRepoPlugins(REPO, plugins);
      const docSearch = process.env[DOC_SEARCH_URL_ENV];
      if (docSearch !== undefined && docSearch !== "") {
        pointDocSearchAt(plugins, docSearch);
      }
    }
    writeFixturePlugins(
      plugins,
      python,
      MCP_FIXTURE_SERVER,
      gates,
      `${siteOrigin}${MARKDOWN_IMAGE_PATH}`,
    );
    const key = siteKey();
    const siteFile = join(stack.work, "sites.toml");
    const agents: readonly string[] = llm ? [...AGENTS, LLM_AGENT, ASSISTANT_AGENT] : AGENTS;
    writeFileSync(siteFile, siteFileToml(siteOrigin, key.publicPem, agents, SITE_REQUEST_CHARS));
    const traces = process.env[TRACES_ENV] ?? join(stack.work, "traces");

    // `serve` 는 표의 판이 맞는 데이터베이스가 있어야 뜬다. 이 준비만의 데이터베이스를 만들어 표를 올려 넘긴다.
    const databaseUrl = prepareDatabase(stack, python);
    const serveUrl = await startServe(stack, { plugins, traces, siteFile, python, databaseUrl });

    // 빌드는 미끼 사이트 파일로, 띄우기는 진짜 사이트 파일로 한다. 빌드가 사이트 파일을 읽어 값을 산출물에 굳히면 응답 머리의
    // 자리가 미끼 출처로 차 있어, 서비스 시작이 바꿀 자리를 찾지 못하고 아래 `startWidget` 이 그 진단과 함께 던진다.
    const decoyFile = join(stack.work, "decoy-sites.toml");
    writeFileSync(
      decoyFile,
      siteFileToml(DECOY_ORIGIN, key.publicPem, agents, DECOY_REQUEST_CHARS),
    );
    await build(stack, decoyFile);

    let widget = await startWidget(stack, "widget", nextPort, siteFile);
    let restarts = 0;
    // 사례가 위젯만 다시 띄울 때 쓰는 손잡이(`control.ts`). 사이트 파일을 바꿔 띄우면 값 파일과 응답 머리의 사본이 새로 쓰인다.
    const control = await startControl(async (request) => {
      let file = siteFile;
      if (request !== null) {
        restarts += 1;
        file = join(stack.work, `restart-${String(restarts)}-sites.toml`);
        writeFileSync(
          file,
          siteFileToml(request.origin, key.publicPem, agents, request.requestChars),
        );
      }
      await stop(widget.child);
      widget = await startWidget(stack, `widget-restart-${String(restarts)}`, nextPort, file);
    });
    stack.own(control.server);

    stack.own(
      await startRelay(relayPort, {
        serve: serveUrl,
        next: `http://127.0.0.1:${String(nextPort)}`,
      }),
    );
    stack.own(await startSite(sitePort, { widget: widgetOrigin, other: otherOrigin }, key));

    publish(WIDGET_ORIGIN_ENV, widgetOrigin);
    publish(SITE_ORIGIN_ENV, siteOrigin);
    publish(OTHER_ORIGIN_ENV, otherOrigin);
    publish(GATES_ENV, gates);
    publish(TRACES_DIR_ENV, traces);
    publish(CONTROL_ENV, control.url);
    return () => stack.teardown();
  } catch (error: unknown) {
    await stack.teardown();
    throw error;
  }
}

/** 위젯 Next(빌드와 start)의 환경. 이 셸의 환경에 사이트 파일을 얹는다. */
function nextEnv(siteFile: string): NodeJS.ProcessEnv {
  return { ...process.env, ...QUIET, AGENT_OS_SITE_FILE: siteFile };
}

/**
 * 위젯을 띄우고 그 포트가 연결을 받을 때까지 기다린다. 시작 래퍼가 그 사이트 파일에서 값 파일과 응답 머리의 사본(허용 출처를
 * 넣은 `routes-manifest.json`)을 쓴 뒤에 Next 를 세우므로, 허용 출처와 글자 수 상한은 이 사이트 파일을 따른다. 같은 앱
 * 폴더의 그 두 파일을 덮어쓰므로 앞 위젯을 끈 뒤에만 다시 부른다.
 */
async function startWidget(
  stack: Stack,
  name: string,
  nextPort: number,
  siteFile: string,
): Promise<Launched> {
  const widget = stack.launch(
    name,
    process.execPath,
    [join(APP, "tools", "start.ts"), "start", "--port", String(nextPort)],
    APP,
    nextEnv(siteFile),
  );
  await until(widget, "위젯 Next 가 서지 않았다", async () =>
    (await accepts(nextPort)) ? nextPort : null,
  );
  return widget;
}

/**
 * 미끼 사이트 파일을 주고 위젯을 빌드한다. 빌드는 사이트 파일을 읽지 않는다. 응답 머리의 `frame-ancestors` 는 `'none'` 으로
 * 지어지고 `.next/routes-manifest.original.json` 에 원본이 남는다. 허용 출처와 글자 수 상한은 뒤이은 `start` 가 쓴다. 그래서
 * 호출한 쪽은 진짜 파일이 아니라 미끼를 준다(빌드가 파일을 읽으면 미끼의 값이 산출물에 들어 사례가 빨개진다). 시작 래퍼로
 * 빌드해 글꼴 파일의 복사와 페이지 안 번들의 빌드까지 운영과 같은 길을 지난다. 빌드는 앱의 `.next/`, `public/fonts/`,
 * `public/element.js` 를 다시 쓴다.
 */
async function build(stack: Stack, decoyFile: string): Promise<void> {
  // 시작 래퍼가 next 를 같은 프로세스에서 부르므로 next 의 진입점이 깔렸는지만 먼저 본다.
  createRequire(join(APP, "package.json")).resolve("next/dist/bin/next");
  const built = stack.launch(
    "build",
    process.execPath,
    [join(APP, "tools", "start.ts"), "build"],
    APP,
    nextEnv(decoyFile),
  );
  const code = await new Promise<number | null>((resolve) => {
    built.child.once("exit", resolve);
  });
  if (code !== 0) {
    throw new Error(`위젯을 빌드하지 못했다(종료 ${String(code)}):\n${built.output()}`);
  }
}
