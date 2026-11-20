// 저장소의 제품 마이그레이션 폴더에서 마지막 판 번호를 읽는다(postgres-foundation 티켓 02). 단독 배포 e2e 가 띄운 배치의 판
// 기록 표(`alembic_version`)와 견준다. 번호를 글자로 적어 두면 다음 마이그레이션이 더해질 때 깨지고, 이 시험은 main 으로
// 가는 PR 에서만 돌아 그 PR 에서는 보이지 않으므로 폴더에서 읽는다.
//
// 판 번호는 파일 이름이 아니라 파일 안의 `revision` 줄에서 읽는다. alembic 이 판 기록 표에 적는 것이 그 값이다. 번호는 네
// 자리로 차례로 늘므로 가장 큰 번호가 마지막 판이다(가지가 갈린 판은 이 제품에 없다). 폴더가 비었거나 번호 줄이 없는 파일이
// 있으면 던진다. 경로가 틀려 아무것도 읽지 못한 채 지나가지 않게 하려는 것이다.

import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { REPO } from "@agent-os/e2e-stack";

export const PRODUCT_VERSIONS = join(
  REPO,
  "src",
  "agent_os",
  "adapters",
  "postgres",
  "migrations",
  "versions",
);

const REVISION = /^revision(?:[ \t]*:[ \t]*str)?[ \t]*=[ \t]*"([0-9]+)"/mu;

/** 마이그레이션 파일들의 글에서 마지막 판 번호를 고른다. */
export function lastRevision(sources: readonly string[]): string {
  if (sources.length === 0) {
    throw new Error("제품 마이그레이션 파일이 하나도 없다");
  }
  const numbers = sources.map((source) => {
    const found = REVISION.exec(source)?.[1];
    if (found === undefined) {
      throw new Error(`판 번호(revision) 줄이 없는 마이그레이션 파일이 있다:\n${source}`);
    }
    return found;
  });
  return numbers.reduce((last, next) => (Number(next) > Number(last) ? next : last));
}

/** 이 저장소의 제품 마이그레이션 폴더의 마지막 판 번호. */
export function productRevision(): string {
  const names = readdirSync(PRODUCT_VERSIONS).filter((name) => name.endsWith(".py"));
  return lastRevision(names.map((name) => readFileSync(join(PRODUCT_VERSIONS, name), "utf-8")));
}
