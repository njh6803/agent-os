// 위젯 미리보기 페이지 설정 읽기. 글을 받아 칸과 규칙을 판정하는 순수 함수라 파일을 쓰지 않고 TOML 글로 부른다. 사이트 파일과
// 키를 대 보는 시작 검사는 load.test.ts 가 본다.

import { resolve } from "node:path";
import type { TomlValue } from "smol-toml";
import { expect, test } from "vitest";
import { type ConfigDoc, configDoc, configToml, PUBLIC_ORIGIN } from "../testing/fixtures.ts";
import { type PortalConfig, parseConfig } from "./config.ts";
import { COOKIE_LIFETIME_DAYS } from "./cookie-policy.ts";

const DIR = resolve("some", "operator", "dir");
// 값을 싣지 않는다는 단언이 잡도록 어긋난 값 자리에 넣는 글자. 규칙을 어길 만한 꼴이라 어느 칸에서도 거부된다.
const SENTINEL = "SENTINEL-값";

function read(doc: ConfigDoc, cookieDays = COOKIE_LIFETIME_DAYS) {
  return parseConfig(configToml(doc), DIR, cookieDays);
}

function accepted(doc: ConfigDoc, cookieDays = COOKIE_LIFETIME_DAYS): PortalConfig {
  const result = read(doc, cookieDays);
  if ("problems" in result) {
    throw new Error(`맞는 설정이 거부됐다: ${result.problems.join(" | ")}`);
  }
  return result;
}

function problemsOf(doc: ConfigDoc): readonly string[] {
  const result = read(doc);
  if (!("problems" in result)) {
    throw new Error("어긋난 설정이 받아들여졌다");
  }
  return result.problems;
}

function firstSite(doc: ConfigDoc): Record<string, TomlValue> {
  const [site] = doc.sites;
  if (site === undefined) {
    throw new Error("시험의 사이트가 없다");
  }
  return site;
}

test("맞는 설정이 읽히고 적지 않은 칸은 기본값으로 채워진다", () => {
  const config = accepted(configDoc());

  expect(config).toMatchObject({
    publicOrigin: PUBLIC_ORIGIN,
    kid: "portal-1",
    host: "127.0.0.1",
    port: 8080,
  });
  expect(config.sites).toHaveLength(1);
  expect(config.sites[0]).toMatchObject({
    name: "demo",
    issuer: "https://demo.example",
    agent: "calc",
    heading: "계산기",
    theme: "nokcheong",
    assurance: "anonymous",
  });
  expect(config.sites[0]?.intro).toBeUndefined();
  expect(config.sites[0]?.mode).toBeUndefined();
  expect(config.sites[0]?.reportUrl).toBeUndefined();
});

test("적은 칸은 그대로 읽는다", () => {
  const doc = configDoc();
  doc.portal["host"] = "::1";
  Object.assign(firstSite(doc), {
    intro: "한 줄 안내",
    theme: "jacho",
    mode: "dark",
    assurance: "both",
    report_url: "https://report.example/calc",
  });

  const config = accepted(doc);

  expect(config.host).toBe("::1");
  expect(config.sites[0]).toMatchObject({
    intro: "한 줄 안내",
    theme: "jacho",
    mode: "dark",
    assurance: "both",
    reportUrl: "https://report.example/calc",
  });
});

test("개인 키의 상대 경로는 설정 파일의 폴더에서 풀고 절대 경로는 그대로 둔다", () => {
  expect(accepted(configDoc()).privateKeyPath).toBe(resolve(DIR, "keys/portal.pem"));

  const absolute = resolve("elsewhere", "portal.pem");
  const doc = configDoc();
  doc.portal["private_key"] = absolute;

  expect(accepted(doc).privateKeyPath).toBe(absolute);
});

test("고지 전문은 사이트마다 시작 때 지어 설정 결과에 든다", () => {
  const doc = configDoc();
  doc.sites.push({
    ...firstSite(doc),
    name: "other",
    issuer: "https://other.example",
    notice: "다른 사이트의 고지입니다.",
  });

  const [basic, written] = accepted(doc).sites;

  expect(basic?.notice).toContain("이 페이지에서 보낸 질문과 받은 출력은 기록되고");
  expect(written?.notice.startsWith("다른 사이트의 고지입니다.\n\n")).toBe(true);
  expect(written?.notice.endsWith("동안 남습니다.")).toBe(true);
});

test("설정을 읽은 결과의 전문은 쿠키 수명 상수의 일수를 싣고, 넘긴 일수를 따른다", () => {
  const doc = configDoc();

  expect(accepted(doc).sites[0]?.notice).toContain(
    `${String(COOKIE_LIFETIME_DAYS)}일 동안 남습니다.`,
  );
  // 상수만 넘기는 시험은 30 을 글로 박은 구현도 지나가, 30 이 아닌 값을 넘겨 일수가 인자에서 오는 것을 본다.
  expect(accepted(doc, 7).sites[0]?.notice).toContain("7일 동안 남습니다.");
  expect(accepted(doc, 7).sites[0]?.notice).not.toContain("30일");
});

const MISMATCHES: readonly (readonly [string, (doc: ConfigDoc) => void, string])[] = [
  ["판이 다르다", (doc) => void (doc.schema_version = "2"), "schema_version"],
  ["판이 없다", (doc) => void Reflect.deleteProperty(doc, "schema_version"), "schema_version"],
  ["판이 글자가 아니다", (doc) => void (doc.schema_version = 1n), "schema_version"],
  [
    "공개 출처가 표기 규칙을 어긴다",
    (doc) => void (doc.portal["public_origin"] = `${SENTINEL}://x`),
    "portal.public_origin",
  ],
  [
    "공개 출처가 글자가 아니다",
    (doc) => void (doc.portal["public_origin"] = 5),
    "portal.public_origin",
  ],
  [
    "개인 키 경로가 없다",
    (doc) => void Reflect.deleteProperty(doc.portal, "private_key"),
    "portal.private_key",
  ],
  ["개인 키 경로가 비었다", (doc) => void (doc.portal["private_key"] = ""), "portal.private_key"],
  ["kid 가 빈 글이다", (doc) => void (doc.portal["kid"] = ""), "portal.kid"],
  ["kid 가 없다", (doc) => void Reflect.deleteProperty(doc.portal, "kid"), "portal.kid"],
  ["포트가 없다", (doc) => void Reflect.deleteProperty(doc.portal, "port"), "portal.port"],
  ["포트가 0 이다", (doc) => void (doc.portal["port"] = 0), "portal.port"],
  ["포트가 65535 를 넘는다", (doc) => void (doc.portal["port"] = 65536), "portal.port"],
  ["포트가 실수다", (doc) => void (doc.portal["port"] = 8080.5), "portal.port"],
  ["포트가 글자다", (doc) => void (doc.portal["port"] = "8080"), "portal.port"],
  ["호스트가 글자가 아니다", (doc) => void (doc.portal["host"] = 1), "portal.host"],
  [
    "portal 표에 모르는 칸이 있다",
    (doc) => void (doc.portal[SENTINEL] = "x"),
    `portal.${SENTINEL}`,
  ],
  ["최상위에 모르는 칸이 있다", (doc) => void Object.assign(doc, { [SENTINEL]: "x" }), SENTINEL],
  [
    "사이트에 모르는 칸이 있다",
    (doc) => void Object.assign(firstSite(doc), { [SENTINEL]: "x" }),
    `sites[0].${SENTINEL}`,
  ],
  [
    "사이트 이름이 없다",
    (doc) => void Reflect.deleteProperty(firstSite(doc), "name"),
    "sites[0].name",
  ],
  ["사이트 이름이 꼴이 아니다", (doc) => void (firstSite(doc)["name"] = SENTINEL), "sites[0].name"],
  ["사이트 이름이 한 글자다", (doc) => void (firstSite(doc)["name"] = "a"), "sites[0].name"],
  [
    "사이트 이름이 숫자로 시작한다",
    (doc) => void (firstSite(doc)["name"] = "1abc"),
    "sites[0].name",
  ],
  [
    "발급자가 없다",
    (doc) => void Reflect.deleteProperty(firstSite(doc), "issuer"),
    "sites[0].issuer",
  ],
  ["에이전트가 빈 글이다", (doc) => void (firstSite(doc)["agent"] = " "), "sites[0].agent"],
  [
    "머리글이 없다",
    (doc) => void Reflect.deleteProperty(firstSite(doc), "heading"),
    "sites[0].heading",
  ],
  ["안내가 글자가 아니다", (doc) => void (firstSite(doc)["intro"] = 1), "sites[0].intro"],
  ["테마가 목록에 없다", (doc) => void (firstSite(doc)["theme"] = SENTINEL), "sites[0].theme"],
  ["모드가 목록에 없다", (doc) => void (firstSite(doc)["mode"] = SENTINEL), "sites[0].mode"],
  [
    "보증 모드가 없다",
    (doc) => void Reflect.deleteProperty(firstSite(doc), "assurance"),
    "sites[0].assurance",
  ],
  [
    "보증 모드가 셋 밖이다",
    (doc) => void (firstSite(doc)["assurance"] = SENTINEL),
    "sites[0].assurance",
  ],
  ["고지가 빈 글이다", (doc) => void (firstSite(doc)["notice"] = ""), "sites[0].notice"],
  ["고지가 공백뿐이다", (doc) => void (firstSite(doc)["notice"] = " \n\t "), "sites[0].notice"],
  ["고지가 글자가 아니다", (doc) => void (firstSite(doc)["notice"] = 1), "sites[0].notice"],
  [
    "보고서 주소가 http 나 https 가 아니다",
    (doc) => void (firstSite(doc)["report_url"] = `ftp://${SENTINEL}`),
    "sites[0].report_url",
  ],
  [
    "보고서 주소가 주소가 아니다",
    (doc) => void (firstSite(doc)["report_url"] = SENTINEL),
    "sites[0].report_url",
  ],
  ["sites 가 비었다", (doc) => void (doc.sites.length = 0), "sites"],
  ["sites 가 없다", (doc) => void Reflect.deleteProperty(doc, "sites"), "sites"],
  ["portal 표가 없다", (doc) => void Reflect.deleteProperty(doc, "portal"), "portal"],
];

test.each(MISMATCHES)(
  "%s: 어긋난 자리가 진단에 들고 어긋난 값은 들지 않는다",
  (_name, edit, place) => {
    const doc = configDoc();
    edit(doc);

    const problems = problemsOf(doc);

    expect(problems.some((problem) => problem.startsWith(`${place}: `))).toBe(true);
    expect(problems.filter((problem) => problem.includes(SENTINEL))).toEqual(
      // 모르는 칸의 진단은 칸 이름이 곧 자리라 그 이름은 싣는다. 값은 싣지 않는다.
      place.includes(SENTINEL)
        ? problems.filter((problem) => problem.startsWith(`${place}: `))
        : [],
    );
  },
);

test("루프백 밖의 호스트는 받은 값을 진단에 싣는다", () => {
  const doc = configDoc();
  doc.portal["host"] = "0.0.0.0";

  expect(problemsOf(doc)).toContain(
    "portal.host: 루프백만 받는다(127.0.0.1, ::1). 받은 값: 0.0.0.0",
  );
});

test("루프백인 호스트 둘은 받는다", () => {
  for (const host of ["127.0.0.1", "::1"]) {
    const doc = configDoc();
    doc.portal["host"] = host;

    expect(accepted(doc).host).toBe(host);
  }
});

test("localhost 는 루프백이라는 보장이 없어 받지 않는다", () => {
  const doc = configDoc();
  doc.portal["host"] = "localhost";

  expect(problemsOf(doc)).toContain(
    "portal.host: 루프백만 받는다(127.0.0.1, ::1). 받은 값: localhost",
  );
});

test("발급자가 겹치면 겹친 사이트의 자리에 진단이 선다", () => {
  const doc = configDoc();
  doc.sites.push({ ...firstSite(doc), name: "other" });

  expect(problemsOf(doc)).toEqual(["sites[1].issuer: 앞선 사이트와 겹친다"]);
});

test("앞선 사이트가 다른 칸 때문에 어긋나도 뒤 사이트의 발급자와 이름 겹침을 함께 알린다", () => {
  const doc = configDoc();
  doc.sites.push({ ...firstSite(doc) });
  delete firstSite(doc)["heading"];

  expect(problemsOf(doc)).toEqual([
    "sites[0].heading: 빠졌다",
    "sites[1].issuer: 앞선 사이트와 겹친다",
    "sites[1].name: 앞선 사이트와 겹친다",
  ]);
});

test("사이트 이름이 겹치면 겹친 사이트의 자리에 진단이 선다", () => {
  const doc = configDoc();
  doc.sites.push({ ...firstSite(doc), issuer: "https://other.example" });

  expect(problemsOf(doc)).toEqual(["sites[1].name: 앞선 사이트와 겹친다"]);
});

test("어긋남은 첫 것에서 멈추지 않고 모두 모아 알린다", () => {
  const doc = configDoc();
  doc.portal["port"] = 0;
  doc.portal["host"] = "0.0.0.0";
  firstSite(doc)["theme"] = SENTINEL;
  firstSite(doc)["notice"] = "  ";

  expect(problemsOf(doc).map((problem) => problem.split(":")[0])).toEqual([
    "portal.host",
    "portal.port",
    "sites[0].theme",
    "sites[0].notice",
  ]);
});

test("TOML 이 아닌 글은 줄과 열만 싣고 글의 내용은 싣지 않는다", () => {
  const result = parseConfig(`schema_version = "1"\n[portal\n${SENTINEL}`, DIR, 30);

  expect("problems" in result && result.problems).toEqual([
    expect.stringMatching(/^설정 파일: TOML 이 아니다: .*\(\d+행 \d+열\)$/u),
  ]);
  expect(JSON.stringify(result)).not.toContain(SENTINEL);
});
