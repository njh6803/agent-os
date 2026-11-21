/**
 * 시험이 실패한 그 순간의 배치 로그를 그 시험의 결과 폴더에 남긴다.
 *
 * 배치 전체의 로그(`compose.log`)는 준비가 끝날 때(`stack.ts` 의 거두기) 한 번 받는다. 그런데 뒤쪽 시험이 배치를 내렸다
 * 올리거나(`docker compose down` 과 `up`) 컨테이너 하나를 다시 만들면 그 컨테이너의 앞선 로그는 사라진다. 그래서 앞쪽
 * 시험의 실패는 끝에 받는 로그에 흔적이 없다(출시 PR 의 `e2e-standalone` 이 질문 길의 시험에서 빨갰을 때, 받은 로그에는
 * 그 시험 뒤에 돈 데이터베이스 시험과 재생성 시험이 다시 만든 컨테이너의 기록만 있었다). 실패한 시험의 바로 뒤에 받으면
 * 그 시험이 지난 요청이 프록시와 serve 에 남긴 줄이 든다.
 */

import { writeFileSync } from "node:fs";

/** Playwright 의 `TestInfo` 가운데 쓰는 부분. */
export interface FinishedTest {
  readonly status?: string | undefined;
  readonly expectedStatus: string;
  /** 그 시험의 결과 폴더 안의 경로. */
  readonly outputPath: (name: string) => string;
}

/** `docker.ts` 의 `Outcome` 가운데 쓰는 부분. 명령이 실패해도 던지지 않고 이 값으로 돌려준다. */
export interface LogOutcome {
  readonly code: number | null;
  readonly stdout: string;
  readonly stderr: string;
  readonly timedOut: boolean;
}

/** `Compose` 가운데 쓰는 부분. */
export interface LogSource {
  readonly call: (rest: readonly string[], timeoutMs: number) => Promise<LogOutcome>;
}

const FILE = "compose-at-failure.log";
const LOGS_TIMEOUT_MS = 60_000;

function unfinishedNote(outcome: LogOutcome): string {
  if (outcome.timedOut) {
    return "[docker compose logs 가 제한 시간을 넘겨 죽었다. 아래는 그때까지 받은 것이다]\n";
  }
  if (outcome.code !== 0) {
    return `[docker compose logs 가 ${String(outcome.code)} 로 끝났다. 아래는 받은 것이다]\n`;
  }
  return "";
}

/**
 * 기대한 대로 끝나지 않은 시험이면 로그를 받아 쓴다. 로그를 받지 못해도 던지지 않는다. 시험의 실패가 이 일의 실패에 가려지면
 * 안 되기 때문이다. 명령이 정상으로 끝나지 않았으면 그 사실을 파일 첫 줄에 적어, 빈 로그와 받지 못한 로그를 가른다.
 */
export async function saveLogsAtFailure(test: FinishedTest, source: LogSource): Promise<void> {
  if (test.status === test.expectedStatus) {
    return;
  }
  try {
    const logs = await source.call(["logs", "--no-color", "--timestamps"], LOGS_TIMEOUT_MS);
    writeFileSync(test.outputPath(FILE), `${unfinishedNote(logs)}${logs.stdout}\n${logs.stderr}`);
  } catch (error) {
    console.error(`실패한 시험의 compose 로그를 남기지 못했다: ${String(error)}`);
  }
}
