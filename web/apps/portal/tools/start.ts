/**
 * 질문 페이지의 시작 명령. 질문 페이지 설정과 사이트 파일, 설정이 가리키는 개인 키를 읽어 서로 맞을 때만 서버를 띄운다
 * (pilot-portal 명세 "띄우기와 타입 검사", "시작 검사와 진단").
 *
 * - 빌드 단계와 `dist` 폴더가 없다. node 가 타입만 벗겨 `.ts` 를 바로 돌리고, 앱 폴더에 산출을 쓰지 않는다. 페이지 스크립트와
 *   토큰 CSS 와 글꼴 표는 서버가 뜨기 전에 메모리에 짓는다(`server/assets.ts`). 하나라도 못 지으면 서지 않고 1로 끝난다.
 * - `ExperimentalWarning` 은 `package.json` 의 `start` 가 `--disable-warning=ExperimentalWarning` 으로 끈다. 켜 두면 시작할 때마다
 *   `stripTypeScriptTypes`(페이지 스크립트를 벗기는 실험 기능)가 stderr 에 경고를 찍어, 시작 실패
 *   진단(`구성 오류:`)과 운영의 로그 수집에서 진짜 경고가 가려진다. 이 경고 하나만 끄고 다른 경고(`DeprecationWarning` 등)는 그대로 둔다.
 * - 인자 둘(`--config`, `--site-file`)이 필수이고 듣는 호스트와 포트는 설정에서 읽는다. 상대 경로는 이 명령을 부른 자리를
 *   기준으로 푼다. 개인 키의 상대 경로는 설정 파일의 폴더 기준이다.
 * - 어긋나면 서지 않고 stderr 에 `구성 오류:` 한 줄과 어긋난 자리마다 한 줄을 찍은 뒤 종료 코드 1로 끝난다. 서면 stdout 에
 *   시작 로그 한 줄을 찍는다. 접근 로그는 남기지 않는다.
 *
 * 사용: node tools/start.ts --config <질문 페이지 설정> --site-file <사이트 파일>
 */

import { randomUUID } from "node:crypto";
import { resolve } from "node:path";
import { parseArgs } from "node:util";
import { buildAssets } from "../server/assets.ts";
import { portalContext } from "../server/context.ts";
import { configErrorText, listenLine } from "../server/diagnostics.ts";
import { handle } from "../server/handler.ts";
import { loadPortal } from "../server/load.ts";
import { listen } from "../server/serve.ts";
import { withoutSeparator } from "./args.ts";

const USAGE =
  "질문 페이지의 시작 명령은 --config <질문 페이지 설정> 과 --site-file <사이트 파일> 둘을 받는다. 호스트와 포트는 설정에서 읽는다.";

export type StartArgs =
  { readonly config: string; readonly siteFile: string } | { readonly problem: string };

/** 시작 명령이 받은 인자를 판정한다. 필수 둘 가운데 하나라도 없거나 모르는 인자가 있으면 까닭을 낸다. */
export function parseStartArgs(argv: readonly string[]): StartArgs {
  let values;
  try {
    ({ values } = parseArgs({
      args: [...withoutSeparator(argv)],
      options: { config: { type: "string" }, "site-file": { type: "string" } },
      allowPositionals: false,
      strict: true,
    }));
  } catch (error: unknown) {
    return { problem: `${USAGE}\n  ${error instanceof Error ? error.message : String(error)}` };
  }
  const { config, "site-file": siteFile } = values;
  if (config === undefined || config === "" || siteFile === undefined || siteFile === "") {
    return { problem: USAGE };
  }
  return { config, siteFile };
}

/**
 * 시작 실패의 진단에 실을 코드. 코드는 오류 자체에 있기도 하고(`EADDRINUSE`) 원인(`cause`)에만 있기도 하다
 * (페이지 스크립트를 벗기지 못한 오류는 `stripTypeScriptTypes` 의 오류를 원인으로 싼다). 문자열이나 숫자가 아닌
 * 코드(자식 프로세스가 시간 제한으로 죽을 때의 `null`)는 건너뛰고 원인을 따라간다. 메시지와 경로는 싣지 않는다.
 */
export function failureCode(error: unknown): string {
  if (error instanceof Error) {
    if ("code" in error && (typeof error.code === "string" || typeof error.code === "number")) {
      return String(error.code);
    }
    if (error.cause !== undefined) return failureCode(error.cause);
  }
  return "알 수 없는 오류";
}

async function main(argv: readonly string[]): Promise<void> {
  const args = parseStartArgs(argv);
  if ("problem" in args) {
    console.error(args.problem);
    process.exitCode = 1;
    return;
  }
  const loaded = loadPortal(resolve(args.config), resolve(args.siteFile));
  if ("problems" in loaded) {
    console.error(configErrorText(loaded.problems));
    process.exitCode = 1;
    return;
  }
  const { host, port, sites } = loaded.config;
  let assets;
  try {
    assets = await buildAssets(sites);
  } catch (error: unknown) {
    console.error(`질문 페이지의 정적 파일을 짓지 못했다(${failureCode(error)})`);
    process.exitCode = 1;
    return;
  }
  const context = portalContext(loaded, assets, {
    now: () => Date.now(),
    newAnonymousId: () => randomUUID(),
  });
  try {
    await listen((request) => handle(request, context), host, port);
  } catch (error: unknown) {
    console.error(`질문 페이지를 열지 못했다(${failureCode(error)})`);
    process.exitCode = 1;
    return;
  }
  console.log(listenLine(host, port, sites.length));
}

if (import.meta.main) {
  await main(process.argv.slice(2));
}
