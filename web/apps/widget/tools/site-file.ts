/**
 * 위젯 빌드의 입력. 서버(`serve --site-file`)가 읽는 사이트 파일(ADR 0023)을 빌드도 읽어 두 값을 끌어낸다(web-widget
 * 티켓 04). 하나는 모든 사이트의 허용 출처를 합친 목록(처음 나온 차례, 겹친 것은 한 번)이고 iframe 페이지의
 * `frame-ancestors` 가 쓴다. 다른 하나는 모든 사이트의 요청 글자 수 상한 가운데 가장 작은 값(적지 않은 사이트는 서버의
 * 기본값)이다. 설정 파일(`next.config.ts`)이 이것을 부르고 두 값을 `env` 로 번들에 싣는다. 번들에서 읽는 법은 티켓 05
 * 의 머리에 적었다.
 *
 * 판정은 fail-closed 다(ADR 0024). 변수가 없으면 사이트 없음(빈 허용 출처와 기본 상한)이고, 변수를 줬는데 비었거나 그
 * 파일이 없거나 읽지 못하면 빌드가 실패한다. 읽지 못하는 것은 둘이다. 하나는 모양이 서버의 pydantic 모델과 어긋난
 * 것이다. TOML 이 깨졌거나, 판이 "1" 이 아니거나, 모르는 키가 있거나, 필수 키가 빠졌거나, 값의 타입이 엄격한 타입과
 * 다르면 그렇다. 다른 하나는 빌드가 읽는 두 값이 서버가 거절할 값인 것이다(아래 표기 밖의 허용 출처, 1 보다 작은
 * `request_chars`). 서버만 보는 제약(공개 키의 수, 다른 상한의 범위, 발급자의 빈 값·겹침·`|`, 공개 키의 PEM 과 `kid`,
 * 열 에이전트의 이름)은 다시 판정하지 않는다. smol-toml 은 TOML 1.1 을 따라 파이썬 tomllib(TOML 1.0)이 거절하는 문법(여러 줄 인라인
 * 표, `\e` 이스케이프 등)도 받는다. 그런 파일로는 빌드가 지나도 serve 가 뜨지 못해, 조용히 지나가지 않는다.
 *
 * 허용 출처의 표기는 브라우저가 `Origin` 헤더에 싣는 직렬화 그대로여야 한다. 규칙의 이름과 차례와 사례는
 * `tests/fixtures/site_file/` 가 원천이고, 파이썬(`src/agent_os/main.py` 의 `_origin_rule`)이 같은 차례로 판정한다.
 * 차례가 다르면 두 규칙을 함께 어긴 값에서 두 언어가 다른 이름을 낸다. 진단은 어긴 규칙을 말하되 값을 싣지 않는다.
 * 사용자 정보를 적은 값에는 비밀번호가 들 수 있다.
 *
 * TOML 파서는 smol-toml 이다(티켓 04 가 골랐다, ADR 0024 가 넘긴 셋째). 정수를 bigint 로 읽게 해 수(`4000`)와 실수
 * (`4000.0`)를 가른다. 파이썬의 엄격한 정수는 실수를 받지 않는다. 파일 머리의 BOM 은 smol-toml 이 받지만 파이썬의
 * tomllib 이 거절해 여기서 막는다.
 */

import { readFileSync } from "node:fs";
import { parse, TomlError, type TomlTable, type TomlValue } from "smol-toml";

export const SITE_FILE_ENV = "AGENT_OS_SITE_FILE";
/** 빌드가 싣는 합친 허용 출처. 공백으로 잇는다. 표기 규칙을 지난 출처에는 공백이 없다. */
export const WIDGET_ORIGINS_ENV = "AGENT_OS_WIDGET_ORIGINS";
/**
 * 빌드가 싣는 가장 작은 요청 글자 수 상한. 지수 꼴이 아닌 십진수 글이다. 2^53 을 넘는 상한은 `number` 를 거쳐 가까운
 * 정수로 싣는다.
 */
export const WIDGET_REQUEST_CHARS_ENV = "AGENT_OS_WIDGET_REQUEST_CHARS";
/** 서버의 기본값(`src/agent_os/channel/http/limits.py` 의 `DEFAULT_REQUEST_CHARS`). 두 언어의 시험이 같은 값을 본다. */
export const DEFAULT_REQUEST_CHARS = 20_000;

export interface BuildInput {
  readonly allowedOrigins: readonly string[];
  readonly requestChars: number;
}

export interface SiteFileProblems {
  readonly problems: readonly string[];
}

const NO_SITES: BuildInput = { allowedOrigins: [], requestChars: DEFAULT_REQUEST_CHARS };

/** 환경 변수가 가리키는 사이트 파일의 빌드 입력. 읽지 못하면 진단을 든 오류를 던져 빌드를 멈춘다. */
export function buildInput(env: Readonly<Record<string, string | undefined>>): BuildInput {
  const path = env[SITE_FILE_ENV];
  if (path === undefined) {
    return NO_SITES;
  }
  if (path === "") {
    throw new Error(`${SITE_FILE_ENV} 가 비었다. 사이트 파일의 경로를 주거나 변수를 뺀다.`);
  }
  const input = readSiteFile(path);
  if ("problems" in input) {
    throw new Error(diagnostic(path, input.problems));
  }
  return input;
}

function readSiteFile(path: string): BuildInput | SiteFileProblems {
  const text = textOf(path);
  return typeof text === "string" ? siteFileInput(universalNewlines(text)) : text;
}

/**
 * 줄 끝 `\r\n` 과 `\r` 을 `\n` 으로 바꾼 글. 서버는 파일을 텍스트 모드(`Path.read_text`)로 읽어 TOML 파서에 넘기기
 * 전에 이렇게 바꾼다(보편 줄바꿈). 바꾸지 않으면 줄 끝이 `\r` 하나인 파일을 서버는 받고 smol-toml 은 거절한다.
 */
function universalNewlines(text: string): string {
  return text.replace(/\r\n?/g, "\n");
}

/** 파일의 글. 서버처럼 UTF-8 로 엄격하게 풀고 머리의 BOM 을 그대로 둔다. */
function textOf(path: string): string | SiteFileProblems {
  let bytes;
  try {
    bytes = readFileSync(path);
  } catch (error: unknown) {
    if (error instanceof Error && "code" in error && error.code === "ENOENT") {
      return { problems: ["파일이 없다"] };
    }
    return {
      problems: [`읽을 수 없다(${error instanceof Error ? error.message : String(error)})`],
    };
  }
  try {
    return new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes);
  } catch {
    return { problems: ["읽을 수 없다(UTF-8 이 아니다)"] };
  }
}

function diagnostic(path: string, problems: readonly string[]): string {
  const lines = problems.map((problem) => `\n  - ${problem}`).join("");
  return (
    `사이트 파일 ${path} 을 받아들일 수 없다(${SITE_FILE_ENV}, ADR 0023).${lines}\n` +
    `  고친 뒤 다시 빌드한다. ${SITE_FILE_ENV} 를 빼면 어느 사이트도 위젯을 iframe 으로 품지 못한다.`
  );
}

/** 사이트 파일의 글에서 빌드 입력을, 또는 받아들일 수 없는 이유들을 끌어낸다. */
export function siteFileInput(text: string): BuildInput | SiteFileProblems {
  if (text.startsWith("\uFEFF")) {
    return { problems: ["TOML 이 아니다: 파일 머리에 BOM 이 있다. BOM 없는 UTF-8 로 저장한다"] };
  }
  let document: TomlTable;
  try {
    document = parse(text, { integersAsBigInt: true, unsafeKeyBehaviour: "throw" });
  } catch (error: unknown) {
    return { problems: [`TOML 이 아니다: ${parseFailure(error)}`] };
  }
  const { value: sites, problems } = sitesOf(document);
  if (problems.length > 0) {
    return { problems };
  }
  const notation = sites.flatMap(originProblems);
  if (notation.length > 0) {
    return { problems: notation };
  }
  if (sites.length === 0) {
    return NO_SITES;
  }
  const limits = sites.map(({ requestChars }) => requestChars ?? BigInt(DEFAULT_REQUEST_CHARS));
  return {
    allowedOrigins: [...new Set(sites.flatMap(({ origins }) => origins))],
    requestChars: Number(limits.reduce((smallest, limit) => (limit < smallest ? limit : smallest))),
  };
}

function parseFailure(error: unknown): string {
  if (error instanceof TomlError) {
    const [head = error.message] = error.message.split("\n");
    return `${head} (${String(error.line)}행 ${String(error.column)}열)`;
  }
  return error instanceof Error ? error.message : String(error);
}

// --- 모양 ----------------------------------------------------------------------------------------------------------
// 서버의 pydantic 모델(`src/agent_os/main.py` 의 `_SiteFile`)이 보는 모양이다. 자리는 서버의 진단과 같이
// `sites[0].public_keys[1].pem` 꼴이다. 문구는 서버가 pydantic 의 영어 문구를 그대로 싣는 것과 달리 한국어다.

const FILE_KEYS: readonly string[] = ["schema_version", "sites"];
const SITE_KEYS: readonly string[] = [
  "issuer",
  "audience",
  "public_keys",
  "allowed_origins",
  "agents",
  "limits",
];
const REQUIRED_SITE_KEYS: readonly string[] = [
  "issuer",
  "audience",
  "public_keys",
  "allowed_origins",
  "agents",
];
const KEY_KEYS: readonly string[] = ["pem", "kid"];
const LIMIT_KEYS: readonly string[] = [
  "request_chars",
  "concurrent_runs_per_principal",
  "hourly_runs_per_principal",
  "concurrent_runs_per_site",
  "hourly_runs_per_site",
  "subscriptions_per_principal",
];

interface SiteEntry {
  readonly place: string;
  readonly origins: readonly string[];
  readonly requestChars: bigint | undefined;
}

/** 모양을 보며 읽은 값과 그 자리에서 찾은 문제들. 문제가 있어도 값은 읽을 수 있는 만큼 채운다. */
interface Read<T> {
  readonly value: T;
  readonly problems: readonly string[];
}

function sitesOf(document: TomlTable): Read<readonly SiteEntry[]> {
  const head = [
    ...unknownKeyProblems(document, FILE_KEYS, ""),
    ...versionProblems(document["schema_version"]),
  ];
  const sites = document["sites"];
  if (sites === undefined) {
    return { value: [], problems: head };
  }
  if (!Array.isArray(sites)) {
    return { value: [], problems: [...head, "sites: 표의 배열이어야 한다"] };
  }
  const entries = sites.map((entry, index): Read<readonly SiteEntry[]> => {
    const place = `sites[${String(index)}]`;
    if (!isTable(entry)) {
      return { value: [], problems: [`${place}: 표여야 한다`] };
    }
    const site = siteOf(entry, place);
    return { value: [site.value], problems: site.problems };
  });
  return {
    value: entries.flatMap(({ value }) => value),
    problems: [...head, ...entries.flatMap(({ problems }) => problems)],
  };
}

function versionProblems(version: TomlValue | undefined): readonly string[] {
  if (version === undefined) {
    return ["schema_version: 빠졌다"];
  }
  return version === "1" ? [] : ['schema_version: 글자 "1" 이어야 한다'];
}

function siteOf(site: TomlTable, place: string): Read<SiteEntry> {
  const origins = textsOf(site["allowed_origins"], `${place}.allowed_origins`);
  const requestChars = requestCharsOf(site["limits"], `${place}.limits`);
  return {
    value: { place, origins: origins.value, requestChars: requestChars.value },
    problems: [
      ...unknownKeyProblems(site, SITE_KEYS, place),
      ...REQUIRED_SITE_KEYS.filter((key) => site[key] === undefined).map(
        (key) => `${place}.${key}: 빠졌다`,
      ),
      ...textProblems(site["issuer"], `${place}.issuer`),
      ...textProblems(site["audience"], `${place}.audience`),
      ...keyProblems(site["public_keys"], `${place}.public_keys`),
      ...textsOf(site["agents"], `${place}.agents`).problems,
      ...origins.problems,
      ...requestChars.problems,
    ],
  };
}

function keyProblems(value: TomlValue | undefined, place: string): readonly string[] {
  if (value === undefined) {
    return [];
  }
  if (!Array.isArray(value)) {
    return [`${place}: 표의 배열이어야 한다`];
  }
  return value.flatMap((entry, at) => {
    const where = `${place}[${String(at)}]`;
    if (!isTable(entry)) {
      return [`${where}: 표여야 한다`];
    }
    return [
      ...unknownKeyProblems(entry, KEY_KEYS, where),
      ...(entry["pem"] === undefined ? [`${where}.pem: 빠졌다`] : []),
      ...textProblems(entry["pem"], `${where}.pem`),
      ...textProblems(entry["kid"], `${where}.kid`),
    ];
  });
}

/** 상한 표의 모양을 보며 `request_chars` 를 읽는다. 적지 않았으면 값은 undefined. */
function requestCharsOf(value: TomlValue | undefined, place: string): Read<bigint | undefined> {
  if (value === undefined) {
    return { value: undefined, problems: [] };
  }
  if (!isTable(value)) {
    return { value: undefined, problems: [`${place}: 표여야 한다`] };
  }
  const limits = value;
  const shape = [
    ...unknownKeyProblems(limits, LIMIT_KEYS, place),
    ...LIMIT_KEYS.filter((key) => limits[key] !== undefined && typeof limits[key] !== "bigint").map(
      (key) => `${place}.${key}: 정수여야 한다`,
    ),
  ];
  const chars = limits["request_chars"];
  if (typeof chars !== "bigint") {
    return { value: undefined, problems: shape };
  }
  return {
    value: chars,
    problems: chars < 1n ? [...shape, `${place}.request_chars: 1 이상이어야 한다`] : shape,
  };
}

function textProblems(value: TomlValue | undefined, place: string): readonly string[] {
  return value === undefined || typeof value === "string" ? [] : [`${place}: 글자여야 한다`];
}

/** 글자의 배열의 모양을 보며 그 글자들을 읽는다. 글자가 아닌 항목은 빼고 그 자리를 문제로 낸다. */
function textsOf(value: TomlValue | undefined, place: string): Read<readonly string[]> {
  if (value === undefined) {
    return { value: [], problems: [] };
  }
  if (!Array.isArray(value)) {
    return { value: [], problems: [`${place}: 글자의 배열이어야 한다`] };
  }
  return {
    value: value.filter((item) => typeof item === "string"),
    problems: value.flatMap((item, at) =>
      typeof item === "string" ? [] : [`${place}[${String(at)}]: 글자여야 한다`],
    ),
  };
}

function unknownKeyProblems(
  table: TomlTable,
  known: readonly string[],
  place: string,
): readonly string[] {
  return Object.keys(table)
    .filter((key) => !known.includes(key))
    .map((key) => `${place === "" ? key : `${place}.${key}`}: 모르는 키다`);
}

function originProblems({ place, origins }: SiteEntry): readonly string[] {
  return origins.flatMap((origin, at) => {
    const rule = originRule(origin);
    return rule === null
      ? []
      : [
          `${place}.allowed_origins[${String(at)}]: 브라우저가 Origin 헤더에 싣는 표기가 아니다(규칙 ${rule}). ${ORIGIN_RULES[rule]}`,
        ];
  });
}

function isTable(value: TomlValue | undefined): value is TomlTable {
  return typeof value === "object" && !Array.isArray(value) && !(value instanceof Date);
}

// --- 허용 출처의 표기 ----------------------------------------------------------------------------------------------

export type OriginRule =
  | "wildcard"
  | "null"
  | "shape"
  | "scheme"
  | "case"
  | "path"
  | "userinfo"
  | "port"
  | "default-port"
  | "idn"
  | "ipv6"
  | "host"
  | "ipv4";

const ORIGIN_RULES: Readonly<Record<OriginRule, string>> = {
  wildcard: "'*' 를 적지 않는다. 출처를 하나씩 적는다",
  null: "'null' 은 불투명한 출처라 받지 않는다",
  shape: "'스킴://호스트' 꼴로 적는다",
  scheme: "스킴은 http 나 https 다",
  case: "스킴과 호스트는 소문자로 적는다",
  path: "호스트와 포트 뒤에 경로, 끝 슬래시, 질의, 조각을 적지 않는다",
  userinfo: "사용자 정보('@' 앞)를 적지 않는다",
  port: "포트는 앞에 0 이 없는 65535 이하의 십진수다",
  "default-port": "기본 포트(http 의 80, https 의 443)는 적지 않는다",
  idn: "국제화 도메인은 퓨니코드(xn--)로 적는다",
  ipv6: "IPv6 주소는 대괄호 안의 RFC 5952 압축형으로 적는다",
  host: "호스트는 비지 않고, 브라우저가 거절하거나 바꾸는 글자(공백, 제어 문자, %, <, >, ^, |, \\ 등)가 없다",
  ipv4: "IPv4 주소는 앞에 0 이 없는 0~255 의 십진수 넷을 점으로 잇는다",
};

const ORIGIN_SHAPE = /^([A-Za-z][A-Za-z0-9+.-]*):\/\/([^/?#]*)(.*)$/su;
const UPPERCASE = /[A-Z]/u;
const NON_ASCII = /\P{ASCII}/u;
const PORT = /^(?:0|[1-9][0-9]{0,4})$/u;
const MAX_PORT = 65_535;
// WHATWG URL 의 금지된 도메인 글자(forbidden domain code point) 가운데 C0 제어 문자(U+0000~U+001F), 공백, DEL 이 아닌
// 것. ASCII 도메인에 금지된 도메인 글자가 들면 브라우저의 URL 파서가 실패한다. `%` 는 퍼센트 인코딩을 먼저 풀어 그 결과를
// 보므로, 든 값은 바뀌거나 실패한다.
const FORBIDDEN_DOMAIN_SIGNS = "#%/:<>?@[\\]^|";
const SPACE = 0x20;
const DELETE = 0x7f;
// 끝 라벨이 이 꼴이면 브라우저는 호스트를 IPv4 로 읽는다(WHATWG URL 의 ends in a number checker).
const NUMERIC_LABEL = /^(?:[0-9]+|0x[0-9a-f]*)$/u;
const IPV4_PART = /^(?:0|[1-9][0-9]{0,2})$/u;
const MAX_IPV4_PART = 255;
const IPV6_GROUP = /^[0-9a-f]{1,4}$/u;
const IPV6_GROUPS = 8;

/** 허용 출처가 어긴 첫 규칙의 이름, 또는 null. 규칙의 뜻은 `ORIGIN_RULES`. */
export function originRule(origin: string): OriginRule | null {
  if (origin.includes("*")) {
    return "wildcard";
  }
  if (origin === "null") {
    return "null";
  }
  const shape = ORIGIN_SHAPE.exec(origin);
  if (shape === null) {
    return "shape";
  }
  const [, scheme = "", authority = "", rest = ""] = shape;
  const lower = scheme.toLowerCase();
  if (lower !== "http" && lower !== "https") {
    return "scheme";
  }
  if (UPPERCASE.test(scheme + authority)) {
    return "case";
  }
  if (rest !== "") {
    return "path";
  }
  if (authority.includes("@")) {
    return "userinfo";
  }
  const [host, after] = splitHost(authority);
  if (after !== "" && !(after.startsWith(":") && isPort(after.slice(1)))) {
    return "port";
  }
  if (after === `:${scheme === "http" ? "80" : "443"}`) {
    return "default-port";
  }
  return hostRule(host);
}

/** 권한부를 호스트와 그 뒤(`""` 이거나 `:` 로 시작하는 글)로. 대괄호로 적은 호스트는 `]` 에서, 그 밖은 첫 `:` 에서
 * 가른다. 닫는 `]` 가 없으면 모두 호스트다. */
function splitHost(authority: string): readonly [string, string] {
  const end = authority.startsWith("[") ? authority.indexOf("]") : authority.indexOf(":");
  if (end < 0) {
    return [authority, ""];
  }
  const cut = authority.startsWith("[") ? end + 1 : end;
  return [authority.slice(0, cut), authority.slice(cut)];
}

function isPort(text: string): boolean {
  return PORT.test(text) && Number(text) <= MAX_PORT;
}

/** 호스트가 어긴 규칙의 이름, 또는 null. 대소문자는 부르는 쪽이 먼저 봤다. */
function hostRule(host: string): OriginRule | null {
  if (NON_ASCII.test(host)) {
    return "idn";
  }
  if (host.startsWith("[")) {
    return isCanonicalIpv6(host) ? null : "ipv6";
  }
  if (host === "" || hasForbiddenDomainCodePoint(host)) {
    return "host";
  }
  const labels = host.split(".");
  // 끝 라벨은 끝 점 하나를 떼고 본다(ends in a number checker). 그렇게 IPv4 로 읽힌 호스트는 브라우저가 정규형으로 다시
  // 적고 끝 점도 뗀다(IPv4 parser, `127.0.0.1.` 은 `127.0.0.1` 이 된다). 그래서 정규형 판정은 끝 점째 본다.
  const names = labels.length > 1 && labels.at(-1) === "" ? labels.slice(0, -1) : labels;
  if (NUMERIC_LABEL.test(names.at(-1) ?? "")) {
    return isCanonicalIpv4(labels) ? null : "ipv4";
  }
  return null;
}

/** 앞의 idn 규칙이 ASCII 밖의 호스트를 막아, 여기 오는 호스트는 글자 하나가 코드 단위 하나다. */
function hasForbiddenDomainCodePoint(host: string): boolean {
  return Array.from(host).some((char) => {
    const code = char.charCodeAt(0);
    return code <= SPACE || code === DELETE || FORBIDDEN_DOMAIN_SIGNS.includes(char);
  });
}

function isCanonicalIpv4(parts: readonly string[]): boolean {
  return (
    parts.length === 4 &&
    parts.every((part) => IPV4_PART.test(part) && Number(part) <= MAX_IPV4_PART)
  );
}

/** 대괄호 안이 파이썬 `ipaddress.IPv6Address(…).compressed` 와 같은 압축형인가. 영역 식별자(`%`)는 받지 않는다. */
function isCanonicalIpv6(host: string): boolean {
  if (!host.endsWith("]") || host.includes("%")) {
    return false;
  }
  const inner = host.slice(1, -1);
  const groups = ipv6Groups(inner);
  return groups !== null && compressedIpv6(groups) === inner;
}

/** 16진수 그룹과 `::` 하나로 적은 IPv6 주소의 그룹 여덟. 압축형에 들지 않는 꼴(점으로 적은 IPv4)은 읽지 않는다. */
function ipv6Groups(text: string): readonly number[] | null {
  const halves = text.split("::");
  const [head = "", tail = ""] = halves;
  const front = hexGroups(head);
  if (halves.length === 1) {
    return front?.length === IPV6_GROUPS ? front : null;
  }
  const back = hexGroups(tail);
  if (
    halves.length > 2 ||
    front === null ||
    back === null ||
    front.length + back.length >= IPV6_GROUPS
  ) {
    return null;
  }
  return [...front, ...Array<number>(IPV6_GROUPS - front.length - back.length).fill(0), ...back];
}

function hexGroups(text: string): readonly number[] | null {
  if (text === "") {
    return [];
  }
  const groups = text.split(":");
  return groups.every((group) => IPV6_GROUP.test(group))
    ? groups.map((group) => Number.parseInt(group, 16))
    : null;
}

/** RFC 5952 압축형. 0 이 둘 이상 이어진 가장 긴 열 가운데 앞의 것을 `::` 로 줄인다(파이썬과 WHATWG URL 이 같다). */
function compressedIpv6(groups: readonly number[]): string {
  let bestStart = -1;
  let bestLength = 1;
  let start = -1;
  groups.forEach((group, index) => {
    if (group !== 0) {
      start = -1;
      return;
    }
    if (start < 0) {
      start = index;
    }
    if (index - start + 1 > bestLength) {
      bestStart = start;
      bestLength = index - start + 1;
    }
  });
  const hex = groups.map((group) => group.toString(16));
  if (bestStart < 0) {
    return hex.join(":");
  }
  return `${hex.slice(0, bestStart).join(":")}::${hex.slice(bestStart + bestLength).join(":")}`;
}
