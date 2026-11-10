/**
 * 질문 페이지의 시작 명령. 질문 페이지 설정과 사이트 파일, 설정이 가리키는 개인 키를 읽어 서로 맞을 때만 서버를 띄운다
 * (pilot-portal 명세 "띄우기와 타입 검사", "시작 검사와 진단").
 *
 * - 빌드 단계와 `dist` 폴더가 없다. node 가 타입만 벗겨 `.ts` 를 바로 돌리고, 앱 폴더에 산출을 쓰지 않는다.
 * - 인자 둘(`--config`, `--site-file`)이 필수이고 듣는 호스트와 포트는 설정에서 읽는다. 상대 경로는 이 명령을 부른 자리를
 *   기준으로 푼다. 개인 키의 상대 경로는 설정 파일의 폴더 기준이다.
 * - 어긋나면 서지 않고 stderr 에 `구성 오류:` 한 줄과 어긋난 자리마다 한 줄을 찍은 뒤 종료 코드 1로 끝난다. 서면 stdout 에
 *   시작 로그 한 줄을 찍는다. 접근 로그는 남기지 않는다.
 *
 * 사용: node tools/start.ts --config <질문 페이지 설정> --site-file <사이트 파일>
 */

import { resolve } from "node:path";
import { parseArgs } from "node:util";
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

function failureCode(error: unknown): string {
  return error instanceof Error && "code" in error ? String(error.code) : "알 수 없는 오류";
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
  try {
    await listen(handle, host, port);
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
