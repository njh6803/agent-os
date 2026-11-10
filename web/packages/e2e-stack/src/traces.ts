// 시험이 `serve` 의 트레이스 폴더를 읽는 길. 준비가 `serve` 에 준 폴더를 시험에 넘기면(`env.ts`) 시험이 여기서 실행이
// 누구의 것으로 시작했는지를 읽는다. 읽기만 하고, 파일은 파이썬 어댑터(`src/agent_os/adapters/jsonl.py`)가 쓴다.
//
// 트레이스는 `<폴더>/<실행 식별자>.jsonl` 이고 한 줄에 JSON 하나다. 첫 줄은 스키마 버전과 실행 식별자의 헤더이고 이벤트는
// 그 뒤다. 시작 이벤트(`run_started`)가 에이전트·요청·주체를 든다.

import { readdirSync, readFileSync } from "node:fs";
import { join, parse } from "node:path";

export interface StartedRun {
  readonly runId: string;
  readonly agent: string;
  readonly request: string;
  /** 실행의 주체. 최종 사용자의 실행이면 `발급자|sub` 이다(`principalOf`). */
  readonly principal: string;
}

/** 그 폴더의 트레이스 가운데 시작 이벤트를 읽은 실행들. 폴더가 없으면 비어 있다. 이름 순이다. */
export function startedRuns(traces: string): StartedRun[] {
  let names: string[];
  try {
    names = readdirSync(traces).filter((name) => name.endsWith(".jsonl"));
  } catch (error: unknown) {
    if (isMissing(error)) {
      return [];
    }
    throw error;
  }
  const runs: StartedRun[] = [];
  for (const name of names.toSorted()) {
    const started = startOf(readFileSync(join(traces, name), "utf-8"), parse(name).name);
    if (started !== null) {
      runs.push(started);
    }
  }
  return runs;
}

function startOf(text: string, runId: string): StartedRun | null {
  // 마지막 줄은 쓰는 도중일 수 있어 읽다 만 줄이면 건너뛴다. 헤더 줄에는 `type` 이 없어 같은 길로 건너뛰고, 처음 만나는
  // 시작 이벤트에서 멈춘다.
  for (const line of text.split("\n")) {
    const event = parseLine(line);
    if (
      isRecord(event) &&
      event["type"] === "run_started" &&
      typeof event["agent"] === "string" &&
      typeof event["request"] === "string" &&
      typeof event["principal"] === "string"
    ) {
      return {
        runId,
        agent: event["agent"],
        request: event["request"],
        principal: event["principal"],
      };
    }
  }
  return null;
}

function parseLine(line: string): unknown {
  try {
    const value: unknown = JSON.parse(line);
    return value;
  } catch {
    return null;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isMissing(error: unknown): boolean {
  return error instanceof Error && "code" in error && error.code === "ENOENT";
}
