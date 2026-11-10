/**
 * 시작 검사(pilot-portal 명세 "시작 검사와 진단"). 설정과 사이트 파일을 읽고, 둘과 개인 키가 서로 맞을 때만 설정을 낸다.
 * 어긋남은 모두 모아 `<자리>: <까닭>` 줄로 낸다. 두 단계다.
 *
 * 1. 파일마다 따로 볼 수 있는 것. 설정의 모양(`parseConfig`)과 사이트 파일이 `site-file` 패키지의 판정을 지나는지.
 *    하나라도 어긋나면 둘의 어긋남을 모두 낸다. 설정의 사이트와 사이트 파일의 사이트를 맞대 보려면 둘 다 읽혀야 한다.
 * 2. 읽은 둘과 개인 키를 대 보는 것(`site-check.ts`). 개인 키를 읽지 못해도 사이트 파일 대조는 계속해, 키가 맞는지만
 *    빼고 알린다.
 *
 * 두 파일과 키는 시작 때 한 번 읽는다. 운영 중에 바꾸면 다시 띄워야 한다(ADR 0050).
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import type { KeyObject } from "node:crypto";
import { readSiteFile, type SiteFile } from "@agent-os/site-file";
import { type PortalConfig, type Problems, parseConfig } from "./config.ts";
import { COOKIE_LIFETIME_DAYS } from "./cookie-policy.ts";
import { readPrivateKey, siteProblems } from "./site-check.ts";

/** 시작 검사를 지난 결과. 요청을 받을 때 쓰도록 시작 때 읽어 둔 개인 키(토큰 서명)와 사이트 파일(`audience`)을 함께 든다. */
export interface LoadedPortal {
  readonly config: PortalConfig;
  readonly privateKey: KeyObject;
  readonly siteFile: SiteFile;
}

/** 두 파일의 경로에서 서로 맞는 설정을, 또는 어긋난 곳들을 읽는다. */
export function loadPortal(configPath: string, siteFilePath: string): LoadedPortal | Problems {
  const text = textOf(configPath);
  const parsed =
    typeof text === "string"
      ? parseConfig(text, dirname(resolve(configPath)), COOKIE_LIFETIME_DAYS)
      : { problems: [`설정 파일: ${text.problem}`] };
  const siteFile = readSiteFile(siteFilePath);
  const first = [
    ...("problems" in parsed ? parsed.problems : []),
    ...("problems" in siteFile
      ? siteFile.problems.map((problem) => `사이트 파일: ${problem}`)
      : []),
  ];
  if ("problems" in parsed || "problems" in siteFile) {
    return { problems: first };
  }
  const read = privateKeyOf(parsed.privateKeyPath);
  const privateKey = "key" in read ? read.key : undefined;
  const problems = [
    ...("problem" in read ? [read.problem] : []),
    ...siteProblems(parsed, siteFile, privateKey),
  ];
  if (problems.length > 0 || privateKey === undefined) {
    return { problems };
  }
  return { config: parsed, privateKey, siteFile };
}

function privateKeyOf(path: string) {
  const text = textOf(path);
  if (typeof text !== "string") {
    return { problem: "portal.private_key: 읽지 못한다" };
  }
  return readPrivateKey(text);
}

/** 파일의 글. 읽지 못하면 까닭을 낸다. 내용이나 시스템 오류 문구는 싣지 않는다. */
function textOf(path: string): string | { readonly problem: string } {
  let bytes;
  try {
    bytes = readFileSync(path);
  } catch (error: unknown) {
    return {
      problem:
        error instanceof Error && "code" in error && error.code === "ENOENT"
          ? "파일이 없다"
          : "읽을 수 없다",
    };
  }
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch {
    return { problem: "읽을 수 없다(UTF-8 이 아니다)" };
  }
}
