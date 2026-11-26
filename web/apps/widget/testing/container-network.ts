// 컨테이너 네트워크 예외의 사례 표를 읽는다(release-image 티켓 03). 파이썬 둘과 TS 셋이 같은 표를 따로 읽는다. 표의 모양과
// 판정의 종류는 tests/fixtures/container_network/README.md 가 원천이다. 앱 사이 import 는 층 경계가 막아, 읽는 자리는 앱마다 한
// 벌이다(관리 화면, 위젯, 위젯 미리보기 페이지). 바꾸면 셋을 함께 고친다.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect } from "vitest";

const FIXTURE = join(
  import.meta.dirname,
  "..",
  "..",
  "..",
  "..",
  "tests",
  "fixtures",
  "container_network",
  "cases.json",
);

/** 진단에 있어야 할 글과 없어야 할 글. `{host}` 와 `{env}` 는 받은 값으로 바꿔 읽는다. */
export interface Signal {
  readonly contains: readonly string[];
  readonly excludes: readonly string[];
}

/** 표의 칸 하나. `env` 가 undefined 이면 환경 변수가 없다. */
export interface NetworkCase {
  readonly marker: boolean;
  readonly env: string | undefined;
  readonly host: string;
  readonly verdict: string;
}

export interface NetworkCases {
  readonly envName: string;
  readonly markerPath: string;
  readonly binding: readonly NetworkCase[];
  readonly upstream: readonly NetworkCase[];
  readonly bindingSignals: Readonly<Record<string, Signal>>;
  readonly upstreamSignals: Readonly<Record<string, Signal>>;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function recordAt(parent: Record<string, unknown>, key: string): Record<string, unknown> {
  const value = parent[key];
  if (!isRecord(value)) {
    throw new Error(`cases.json 에 객체 ${key} 가 없다`);
  }
  return value;
}

function listAt(parent: Record<string, unknown>, key: string): readonly unknown[] {
  const value = parent[key];
  if (!Array.isArray(value)) {
    throw new Error(`cases.json 에 배열 ${key} 가 없다`);
  }
  return value;
}

function textAt(parent: Record<string, unknown>, key: string): string {
  const value = parent[key];
  if (typeof value !== "string") {
    throw new Error(`cases.json 에 글자 ${key} 가 없다`);
  }
  return value;
}

function texts(value: unknown, place: string): readonly string[] {
  if (!Array.isArray(value) || !value.every((item: unknown) => typeof item === "string")) {
    throw new Error(`cases.json 의 ${place} 가 글자 배열이 아니다`);
  }
  return value.map(String);
}

function casesOf(rows: readonly unknown[]): readonly NetworkCase[] {
  return rows.flatMap((row) => {
    if (!isRecord(row) || typeof row["marker"] !== "boolean") {
      throw new Error("cases.json 의 행에 marker 가 없다");
    }
    const { marker } = row;
    const env = row["env"] === null ? undefined : textAt(row, "env");
    return Object.entries(recordAt(row, "verdicts")).map(([host, verdict]) => {
      if (typeof verdict !== "string") {
        throw new Error(`cases.json 의 ${host} 의 판정이 글자가 아니다`);
      }
      return { marker, env, host, verdict };
    });
  });
}

function signalsOf(document: Record<string, unknown>, key: string): Record<string, Signal> {
  return Object.fromEntries(
    Object.entries(recordAt(document, key)).map(([kind, signal]) => {
      if (!isRecord(signal)) {
        throw new Error(`cases.json 의 ${key}.${kind} 가 객체가 아니다`);
      }
      return [
        kind,
        {
          contains: texts(signal["contains"], `${key}.${kind}.contains`),
          excludes: texts(signal["excludes"], `${key}.${kind}.excludes`),
        },
      ];
    }),
  );
}

function load(): NetworkCases {
  const document: unknown = JSON.parse(readFileSync(FIXTURE, "utf-8"));
  if (!isRecord(document)) {
    throw new Error("cases.json 이 객체가 아니다");
  }
  return {
    envName: textAt(document, "env_name"),
    markerPath: textAt(document, "marker_path"),
    binding: casesOf(listAt(document, "binding")),
    upstream: casesOf(listAt(document, "upstream")),
    bindingSignals: signalsOf(document, "binding_signals"),
    upstreamSignals: signalsOf(document, "upstream_signals"),
  };
}

export const CASES: NetworkCases = load();

/** 예외가 꺼진 입력. 표지 파일도 환경 변수도 없다. 예외와 상관없는 시험이 판정 함수에 넘긴다. */
export const OUTSIDE = { imageMarker: false, env: undefined } as const;

/** 사례의 이름. 시험 이름이 칸을 말한다. */
export function nameOf(item: NetworkCase): string {
  const env = item.env === undefined ? "없음" : JSON.stringify(item.env);
  return `표지 파일 ${item.marker ? "있음" : "없음"}, 환경 변수 ${env}, ${item.host} → ${item.verdict}`;
}

/** 진단이 그 종류의 신호를 지니는지 본다. 종류가 표에 없으면 시험이 빨개진다. */
export function expectSignals(
  found: string,
  signals: Readonly<Record<string, Signal>>,
  item: NetworkCase,
): void {
  const signal = signals[item.verdict];
  if (signal === undefined) {
    throw new Error(`표에 ${item.verdict} 의 신호가 없다`);
  }
  const fill = (text: string): string =>
    text.replaceAll("{host}", item.host).replaceAll("{env}", item.env ?? "");
  for (const text of signal.contains) {
    expect(found, nameOf(item)).toContain(fill(text));
  }
  for (const text of signal.excludes) {
    expect(found, nameOf(item)).not.toContain(fill(text));
  }
}
