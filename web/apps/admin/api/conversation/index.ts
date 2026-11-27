// 대화 하나를 읽는 요청 함수. 끝 실행의 트레이스는 `api/traces` 의 `readTrace` 로 읽고(패널과 같은 열쇠의 같은 값), 여기는
// 그 앞 실행을 거슬러 읽는 일을 묶는다. 트레이스를 대화의 차례로 바꾸는 일, 다시 읽을 간격, 거슬러 읽는 규칙은 `./turns`
// 가 갖는다. 도메인 폴더는 이 barrel 로만 가져온다.

import { readTrace } from "../traces";
import { type Earlier, readEarlier } from "./turns";

export {
  type Approval,
  type Earlier,
  EARLIER_CAP,
  hasOutcome,
  isPastTimeout,
  type Outcome,
  pollInterval,
  previousRunOf,
  readEarlier,
  turnOf,
  type Turn,
} from "./turns";

/** 끝 실행의 앞 실행들을 가장 오래된 것부터 읽는다(상한 100, 끊긴 고리는 읽은 데까지). */
export function readEarlierRuns(previousRun: string | null, endRunId: string): Promise<Earlier> {
  return readEarlier(previousRun, endRunId, readTrace);
}
