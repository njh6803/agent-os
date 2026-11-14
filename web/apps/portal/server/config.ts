/**
 * 위젯 미리보기 페이지 설정 읽기(pilot-portal 명세 "위젯 미리보기 페이지 설정"). TOML 글을 받아 칸과 규칙을 판정하는 순수 함수다. 파일을
 * 읽는 것도, 사이트 파일과 개인 키를 대 보는 것도 하지 않는다. 그 둘은 `load.ts` 가 한다.
 *
 * - `schema_version = "1"` 이 필수이고 모르는 칸은 거부한다(사이트 파일과 같은 규약).
 * - 어긋남은 첫 것에서 멈추지 않고 모두 모아 `<자리>: <까닭>` 줄로 낸다. 자리는 `sites[0].agent`, `portal.public_origin`
 *   꼴이고 까닭에 어긋난 값은 싣지 않는다. 예외는 루프백 밖의 `portal.host` 하나다(받은 값을 싣는다. 호스트는 비밀이
 *   아니고 위젯의 시작 래퍼도 싣는다).
 * - 고지 전문은 사이트마다 여기서 짓는다. 쿠키 수명 일수는 인자로 받는다(`noticeText`).
 * - 읽는 TOML 파서는 smol-toml 이고 정수를 bigint 로 읽어 수(`8080`)와 실수(`8080.5`)를 가른다.
 *
 * 사이트 파일 쪽 규칙(허용 출처의 표기)은 `@agent-os/site-file` 의 `originRule` 로 판정한다.
 */

import { originRule } from "@agent-os/site-file";
import { DEFAULT_THEME, MODES, type Mode, THEMES, type ThemeKey } from "@agent-os/ui/themes";
import { resolve } from "node:path";
import { parse, TomlError, type TomlTable, type TomlValue } from "smol-toml";
import { noticeText } from "./notice.ts";

// 바인딩을 허용하는 주소 전부. 순서가 진단의 문장이 된다. 같은 목록을 `serve`(`src/agent_os/main.py` 의
// `LOOPBACK_HOSTS`), 관리 화면(`web/apps/admin/tools/loopback.ts`), 위젯(`web/apps/widget/tools/start.ts`)이 따로 든다.
// 앱 사이 import 는 층 경계가 막아, 바꾸면 넷을 함께 고친다.
const LOOPBACK_HOSTS: readonly string[] = ["127.0.0.1", "::1"];
const DEFAULT_HOST = "127.0.0.1";
const MAX_PORT = 65_535;
const NAME_SHAPE = /^[a-z][a-z0-9-]{1,62}$/u;

export const ASSURANCES = ["anonymous", "login", "both"] as const;
export type Assurance = (typeof ASSURANCES)[number];

export interface PortalSite {
  /** 경로와 쿠키 경로에 쓰는 이름. */
  readonly name: string;
  /** 사이트 파일의 항목을 고르는 열쇠. */
  readonly issuer: string;
  readonly agent: string;
  readonly heading: string;
  readonly intro: string | undefined;
  readonly theme: ThemeKey;
  /** 적지 않았으면 브라우저의 시스템 설정을 따른다. */
  readonly mode: Mode | undefined;
  readonly assurance: Assurance;
  /** 고지 전문. 시작 때 지어 둔 글이다. */
  readonly notice: string;
  readonly reportUrl: string | undefined;
}

export interface PortalConfig {
  readonly publicOrigin: string;
  /** 설정 파일의 폴더에서 푼 절대 경로. */
  readonly privateKeyPath: string;
  readonly kid: string;
  readonly host: string;
  readonly port: number;
  readonly sites: readonly PortalSite[];
}

export interface Problems {
  readonly problems: readonly string[];
}

const FILE_KEYS: readonly string[] = ["schema_version", "portal", "sites"];
const PORTAL_KEYS: readonly string[] = ["public_origin", "private_key", "kid", "host", "port"];
const SITE_KEYS: readonly string[] = [
  "name",
  "issuer",
  "agent",
  "heading",
  "intro",
  "theme",
  "mode",
  "assurance",
  "notice",
  "report_url",
];

/**
 * 설정의 글에서 설정을, 또는 받아들일 수 없는 이유들을 읽는다. `configDir` 은 개인 키의 상대 경로를 푸는 기준이고
 * `cookieDays` 는 고지 전문의 쿠키 문장이 그리는 일수다.
 */
export function parseConfig(
  text: string,
  configDir: string,
  cookieDays: number,
): PortalConfig | Problems {
  let document: TomlTable;
  try {
    document = parse(text, { integersAsBigInt: true, unsafeKeyBehaviour: "throw" });
  } catch (error: unknown) {
    return { problems: [`설정 파일: TOML 이 아니다: ${parseFailure(error)}`] };
  }
  const problems: string[] = [
    ...unknownKeys(document, FILE_KEYS, ""),
    ...versionProblems(document["schema_version"]),
  ];
  const portal = portalOf(document["portal"], configDir, problems);
  const sites = sitesOf(document["sites"], cookieDays, problems);
  if (problems.length > 0 || portal === undefined || sites === undefined) {
    return { problems };
  }
  return { ...portal, sites };
}

function parseFailure(error: unknown): string {
  if (error instanceof TomlError) {
    const [head = error.message] = error.message.split("\n");
    return `${head} (${String(error.line)}행 ${String(error.column)}열)`;
  }
  return error instanceof Error ? error.message : String(error);
}

function versionProblems(version: TomlValue | undefined): readonly string[] {
  if (version === undefined) {
    return ["schema_version: 빠졌다"];
  }
  return version === "1" ? [] : ['schema_version: 글자 "1" 이어야 한다'];
}

function isTable(value: TomlValue | undefined): value is TomlTable {
  return typeof value === "object" && !Array.isArray(value) && !(value instanceof Date);
}

function unknownKeys(table: TomlTable, known: readonly string[], place: string): readonly string[] {
  return Object.keys(table)
    .filter((key) => !known.includes(key))
    .map((key) => `${place === "" ? key : `${place}.${key}`}: 모르는 칸이다`);
}

/** 빈 글이나 공백뿐인 글이 아닌 필수 글자 칸. 어긋나면 문제를 더하고 undefined 다. */
function requiredText(
  table: TomlTable,
  key: string,
  place: string,
  problems: string[],
): string | undefined {
  const value = table[key];
  if (value === undefined) {
    problems.push(`${place}: 빠졌다`);
    return undefined;
  }
  if (typeof value !== "string") {
    problems.push(`${place}: 글자여야 한다`);
    return undefined;
  }
  if (value.trim() === "") {
    problems.push(`${place}: 비지 않은 글이어야 한다`);
    return undefined;
  }
  return value;
}

/** 적지 않아도 되는 글자 칸. 적었는데 글자가 아니면 문제를 더한다. */
function optionalText(
  table: TomlTable,
  key: string,
  place: string,
  problems: string[],
): string | undefined {
  const value = table[key];
  if (value === undefined) {
    return undefined;
  }
  if (typeof value !== "string") {
    problems.push(`${place}: 글자여야 한다`);
    return undefined;
  }
  return value;
}

function portalOf(value: TomlValue | undefined, configDir: string, problems: string[]) {
  if (value === undefined) {
    problems.push("portal: 빠졌다");
    return undefined;
  }
  if (!isTable(value)) {
    problems.push("portal: 표여야 한다");
    return undefined;
  }
  const before = problems.length;
  problems.push(...unknownKeys(value, PORTAL_KEYS, "portal"));
  const publicOrigin = publicOriginOf(value, problems);
  const privateKey = requiredText(value, "private_key", "portal.private_key", problems);
  const kid = requiredText(value, "kid", "portal.kid", problems);
  const host = hostOf(value, problems);
  const port = portOf(value, problems);
  if (
    problems.length > before ||
    publicOrigin === undefined ||
    privateKey === undefined ||
    kid === undefined ||
    host === undefined ||
    port === undefined
  ) {
    return undefined;
  }
  return { publicOrigin, privateKeyPath: resolve(configDir, privateKey), kid, host, port };
}

function publicOriginOf(portal: TomlTable, problems: string[]): string | undefined {
  const origin = requiredText(portal, "public_origin", "portal.public_origin", problems);
  if (origin === undefined) {
    return undefined;
  }
  const rule = originRule(origin);
  if (rule !== null) {
    problems.push(
      `portal.public_origin: 브라우저가 Origin 헤더에 싣는 표기가 아니다(규칙 ${rule}). 사이트 파일의 허용 출처와 같은 표기로 적는다`,
    );
    return undefined;
  }
  return origin;
}

function hostOf(portal: TomlTable, problems: string[]): string | undefined {
  const value = portal["host"];
  if (value === undefined) {
    return DEFAULT_HOST;
  }
  if (typeof value !== "string") {
    problems.push("portal.host: 글자여야 한다");
    return undefined;
  }
  if (!LOOPBACK_HOSTS.includes(value)) {
    problems.push(`portal.host: 루프백만 받는다(${LOOPBACK_HOSTS.join(", ")}). 받은 값: ${value}`);
    return undefined;
  }
  return value;
}

function portOf(portal: TomlTable, problems: string[]): number | undefined {
  const value = portal["port"];
  if (value === undefined) {
    problems.push("portal.port: 빠졌다");
    return undefined;
  }
  if (typeof value !== "bigint" || value < 1n || value > BigInt(MAX_PORT)) {
    problems.push(`portal.port: 1 이상 ${String(MAX_PORT)} 이하의 정수여야 한다`);
    return undefined;
  }
  return Number(value);
}

function sitesOf(value: TomlValue | undefined, cookieDays: number, problems: string[]) {
  if (value === undefined) {
    problems.push("sites: 하나 이상 있어야 한다");
    return undefined;
  }
  if (!Array.isArray(value)) {
    problems.push("sites: 표의 배열이어야 한다");
    return undefined;
  }
  if (value.length === 0) {
    problems.push("sites: 하나 이상 있어야 한다");
    return undefined;
  }
  const sites = value.map((entry, index) => siteOf(entry, index, cookieDays, problems));
  problems.push(...overlaps(value.map(identityOf)));
  const found = sites.filter((site) => site !== undefined);
  return found.length === sites.length ? found : undefined;
}

/** 사이트를 가르는 두 값. 칸 하나가 유효한 값이면 담고 아니면 비운다. */
interface Identity {
  readonly issuer: string | undefined;
  readonly name: string | undefined;
}

/** 다른 칸이 어긋난 사이트의 겹침도 함께 알리려고, 사이트가 통째로 유효한지와 상관없이 두 값만 뽑는다. */
function identityOf(entry: TomlValue): Identity {
  if (!isTable(entry)) {
    return { issuer: undefined, name: undefined };
  }
  const { issuer, name } = entry;
  return {
    issuer: typeof issuer === "string" && issuer.trim() !== "" ? issuer : undefined,
    name: typeof name === "string" && NAME_SHAPE.test(name) ? name : undefined,
  };
}

/** 앞선 사이트와 `issuer` 나 `name` 이 겹친 사이트의 자리. 보증 모드와 상관없이 본다. */
function overlaps(identities: readonly Identity[]): readonly string[] {
  return identities.flatMap(({ issuer, name }, index) => {
    const earlier = identities.slice(0, index);
    return [
      ...(issuer !== undefined && earlier.some((other) => other.issuer === issuer)
        ? [`sites[${String(index)}].issuer: 앞선 사이트와 겹친다`]
        : []),
      ...(name !== undefined && earlier.some((other) => other.name === name)
        ? [`sites[${String(index)}].name: 앞선 사이트와 겹친다`]
        : []),
    ];
  });
}

function siteOf(
  entry: TomlValue,
  index: number,
  cookieDays: number,
  problems: string[],
): PortalSite | undefined {
  const place = `sites[${String(index)}]`;
  if (!isTable(entry)) {
    problems.push(`${place}: 표여야 한다`);
    return undefined;
  }
  const before = problems.length;
  problems.push(...unknownKeys(entry, SITE_KEYS, place));
  const name = nameOf(entry, `${place}.name`, problems);
  const issuer = requiredText(entry, "issuer", `${place}.issuer`, problems);
  const agent = requiredText(entry, "agent", `${place}.agent`, problems);
  const heading = requiredText(entry, "heading", `${place}.heading`, problems);
  const intro = optionalText(entry, "intro", `${place}.intro`, problems);
  const theme = themeOf(entry, `${place}.theme`, problems);
  const mode = modeOf(entry, `${place}.mode`, problems);
  const assurance = assuranceOf(entry, `${place}.assurance`, problems);
  const notice = noticeOf(entry, `${place}.notice`, problems);
  const reportUrl = reportUrlOf(entry, `${place}.report_url`, problems);
  if (
    problems.length > before ||
    name === undefined ||
    issuer === undefined ||
    agent === undefined ||
    heading === undefined ||
    theme === undefined ||
    assurance === undefined
  ) {
    return undefined;
  }
  return {
    name,
    issuer,
    agent,
    heading,
    intro,
    theme,
    mode,
    assurance,
    notice: noticeText(notice, cookieDays),
    reportUrl,
  };
}

function nameOf(site: TomlTable, place: string, problems: string[]): string | undefined {
  const value = site["name"];
  if (value === undefined) {
    problems.push(`${place}: 빠졌다`);
    return undefined;
  }
  if (typeof value !== "string" || !NAME_SHAPE.test(value)) {
    problems.push(`${place}: 소문자로 시작하는 소문자·숫자·하이픈 2~63자여야 한다`);
    return undefined;
  }
  return value;
}

/** 테마. 적지 않으면 기본 테마이고, 목록에 없는 키는 문제다. */
function themeOf(site: TomlTable, place: string, problems: string[]): ThemeKey | undefined {
  const value = site["theme"];
  if (value === undefined) {
    return DEFAULT_THEME;
  }
  const entry = THEMES.find(({ key }) => key === value);
  if (entry === undefined) {
    problems.push(
      `${place}: 디자인 시스템의 테마 키(${THEMES.map(({ key }) => key).join(", ")})여야 한다`,
    );
    return undefined;
  }
  return entry.key;
}

/** 모드. 적지 않으면 undefined 이고 브라우저의 시스템 설정을 따른다. */
function modeOf(site: TomlTable, place: string, problems: string[]): Mode | undefined {
  const value = site["mode"];
  if (value === undefined) {
    return undefined;
  }
  const mode = MODES.find((candidate) => candidate === value);
  if (mode === undefined) {
    problems.push(`${place}: ${MODES.join(", ")} 가운데 하나여야 한다`);
  }
  return mode;
}

function assuranceOf(site: TomlTable, place: string, problems: string[]): Assurance | undefined {
  const value = site["assurance"];
  if (value === undefined) {
    problems.push(`${place}: 빠졌다`);
    return undefined;
  }
  const assurance = ASSURANCES.find((candidate) => candidate === value);
  if (assurance === undefined) {
    problems.push(`${place}: ${ASSURANCES.join(", ")} 가운데 하나여야 한다`);
  }
  return assurance;
}

/** 사이트가 적은 고지 글. 적었는데 비었거나 공백뿐이면 기본 글로 덮지 않고 문제로 낸다. */
function noticeOf(site: TomlTable, place: string, problems: string[]): string | undefined {
  const notice = optionalText(site, "notice", place, problems);
  if (notice !== undefined && notice.trim() === "") {
    problems.push(`${place}: 적었으면 비지 않은 글이어야 한다(공백뿐인 글도 받지 않는다)`);
    return undefined;
  }
  return notice;
}

function reportUrlOf(site: TomlTable, place: string, problems: string[]): string | undefined {
  const value = optionalText(site, "report_url", place, problems);
  if (value === undefined) {
    return undefined;
  }
  if (!isWebUrl(value)) {
    problems.push(`${place}: http 나 https 주소여야 한다`);
    return undefined;
  }
  return value;
}

function isWebUrl(text: string): boolean {
  try {
    const { protocol } = new URL(text);
    return protocol === "http:" || protocol === "https:";
  } catch {
    return false;
  }
}
