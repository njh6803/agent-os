/**
 * 확인 명령(design-reverse-sync 명세 "확인"). 받은 폴더와 읽지 못한 것을 읽어 판정(`check.ts`)에 넘기고 결과를 보고
 * (`check-report.ts`)로 낸다. 스킬은 `paths` 가 낸 경로를 받고 읽지 못한 것을 적기를 `paths` 가 빌 때까지 되풀이한 뒤
 * `judge` 로 결과를 얻는다. 스킬은 받을 경로를 손으로 짓지 않는다.
 *
 * 명령: `check paths --web <받은 폴더> [--reads <읽지 못한 것>]`,
 * `check judge --web <받은 폴더> [--reads <읽지 못한 것>] [--branch <지금 브랜치> --code-tokens <tokens.json>]
 * [--inherit-out <이어받을 기준본>]`.
 *
 * - 받은 폴더는 받은 파일을 아티팩트 경로 그대로(`project/…`) 둔 폴더다.
 * - 읽지 못한 것은 JSON `{"absent": [경로, …], "failed": {경로: 문구}}` 이고, `absent` 는 없다는 까닭으로 읽지 못한
 *   경로, `failed` 는 다른 까닭으로 읽지 못한 경로와 그 문구다.
 * - 지금 브랜치와 지금 코드에서 지은 `tokens.json`(`build` 의 산출)은 기록에 `claim` 이 있을 때 있어야 하고, 없으면
 *   `usage` 오류다. 스킬은 늘 넘긴다. 들이기가 번호를 옮겨 브랜치 이름을 바꾼 직후 자기 `claim` 을 고쳐 쓰는 확인만
 *   지금 브랜치 대신 `claim` 이 든 옛 브랜치를 준다. 명세의 차례가 이름을 먼저 바꾸고 `claim` 을 다시 쓰는 것이라
 *   새 이름으로는 자기 것으로 보이지 않는다. 그 사이에 끊겨 이어받은 세션은 새 이름으로 확인해 PR 이 없는 남의
 *   `claim` 으로 본다(명세 "자기 `claim`"의 2026-10-22 주석).
 * - 이어받을 기준본은 남의 `claim` 에 더 고친 몫이 있을 때 쓰는 파일이다. 썼으면 보고의 `inherit` 이 그 절대 경로다.
 *
 * `judge` 는 받을 경로가 폴더에도 읽지 못한 것에도 없으면 `input` 오류다. 보고는 `paths` 면 아직 받지 않은 경로
 * (`paths`), `judge` 면 확인 결과의 칸이다.
 */

import { parseArgs } from "node:util";
import { reportFields } from "./check-report.ts";
import { judgeWithInherit, nextFetch, type WebFiles } from "./check.ts";
import { CommandError, parsedArgs, writeOutput, type ReportFields } from "./command.ts";
import { inputError, isArtifactPath, isRecord, readFolder, readJson, stringList } from "./io.ts";
import { readTokens } from "./tokens-json.ts";

/** 읽지 못한 것의 파일. 주지 않으면 비었다. */
function readReads(path: string | undefined): Pick<WebFiles, "absent" | "failed"> {
  if (path === undefined) {
    return { absent: new Set(), failed: new Map() };
  }
  const raw = readJson(path);
  if (!isRecord(raw) || Object.keys(raw).some((key) => key !== "absent" && key !== "failed")) {
    throw inputError(path, "absent 와 failed 만 든 JSON 객체가 아니다");
  }
  const absent = raw.absent === undefined ? [] : stringList(raw.absent);
  if (absent === undefined || !absent.every(isArtifactPath)) {
    throw inputError(path, "absent 로 project/ 아래 경로의 배열을 들지 않는다");
  }
  const failedRaw = raw.failed ?? {};
  if (!isRecord(failedRaw)) {
    throw inputError(path, "failed 로 경로마다 문구를 든 객체를 들지 않는다");
  }
  const failed = new Map<string, string>();
  for (const [failedPath, message] of Object.entries(failedRaw)) {
    if (!isArtifactPath(failedPath) || typeof message !== "string") {
      throw inputError(
        path,
        `failed 의 ${JSON.stringify(failedPath)} 가 project/ 아래 경로와 문구가 아니다`,
      );
    }
    failed.set(failedPath, message);
  }
  return { absent: new Set(absent), failed };
}

/** 확인 명령. */
export function runCheck(args: readonly string[]): ReportFields {
  const { values, positionals } = parsedArgs(() =>
    parseArgs({
      args: [...args],
      options: {
        web: { type: "string" },
        reads: { type: "string" },
        branch: { type: "string" },
        "code-tokens": { type: "string" },
        "inherit-out": { type: "string" },
      },
      strict: true,
      allowPositionals: true,
    }),
  );
  const [action, ...rest] = positionals;
  if ((action !== "paths" && action !== "judge") || rest.length > 0) {
    throw new CommandError("usage", "check 는 paths 나 judge 하나를 받는다");
  }
  if (values.web === undefined) {
    throw new CommandError("usage", `check ${action} 에는 --web <받은 폴더> 가 있어야 한다`);
  }
  const judgeOnly = ["branch", "code-tokens", "inherit-out"].filter((key) => key in values);
  if (action === "paths" && judgeOnly.length > 0) {
    throw new CommandError(
      "usage",
      `check paths 는 ${judgeOnly.map((key) => `--${key}`).join(", ")} 를 받지 않는다`,
    );
  }
  const web: WebFiles = { files: readFolder(values.web, ""), ...readReads(values.reads) };
  if (action === "paths") {
    return { action, paths: nextFetch(web) };
  }
  const codeTokens = values["code-tokens"];
  const { report, inherit } = judgeWithInherit(web, {
    branch: values.branch ?? null,
    codeTokens: codeTokens === undefined ? null : readTokens(readJson(codeTokens)),
  });
  const out = values["inherit-out"];
  if (report.result === "importing" && inherit !== null && out !== undefined) {
    const written = writeOutput(out, `${JSON.stringify(inherit, null, 2)}\n`);
    return { action, ...reportFields({ ...report, inherit: written }) };
  }
  return { action, ...reportFields(report) };
}
