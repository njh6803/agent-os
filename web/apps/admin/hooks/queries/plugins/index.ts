// 플러그인의 SWR 훅. 컴포넌트는 useSWR 이나 요청 함수를 직접 부르지 않고 이 훅을 쓴다.
//
// 다시 읽는 때는 창 포커스, 새로 고침 버튼, 쓰기 직후뿐이다(web-admin 명세 "새로 고침과 상태"). 주기 재검증을 두지
// 않고, 재연결과 실패 뒤의 재시도도 끈다. 둘 다 시간이 흐르는 것만으로 서버를 다시 부른다(스토리 35).
//
// 관리 토큰의 판정은 결과를 돌려주지 않고 스토어에 남긴다. 받아들임, 거부, 판정하지 못함이 모두 스토어의 값이다.

import { useCallback } from "react";
import useSWR, { type SWRResponse } from "swr";
import { RequestFailure } from "../../../api/failure";
import { listPlugins, type PluginRow } from "../../../api/plugins";
import { useTokens } from "../../../stores/tokens";

/**
 * SWR 키. 토큰은 키에 싣지 않는다. 토큰은 요청의 헤더에만 있다. 대신 토큰을 받아들인 횟수를 실어 토큰마다 캐시와
 * 진행 중인 요청을 가른다(스토어의 `adminTokenGeneration`).
 */
export const pluginKeys = {
  list: (generation: number) => ["plugins", generation] as const,
};

const READ = {
  revalidateOnFocus: true,
  revalidateOnReconnect: false,
  refreshInterval: 0,
  shouldRetryOnError: false,
} as const;

type Verdict = "accepted" | "rejected" | "unjudged";

/** 플러그인 목록. 관리 토큰이 없으면 부르지 않는다. */
export function usePlugins(): SWRResponse<PluginRow[], unknown> {
  const adminToken = useTokens((state) => state.adminToken);
  const generation = useTokens((state) => state.adminTokenGeneration);
  return useSWR(
    adminToken === null ? null : pluginKeys.list(generation),
    adminToken === null ? null : () => listOrReject(adminToken),
    READ,
  );
}

/**
 * 관리 토큰을 넣는다(web-admin 명세 "관리 화면 — 토큰"). 목록 요청 하나로 판정해 받아들이면 스토어에 둔다. 401 이면
 * 저장하지 않고 거부됐다고 남긴다. 틀린 토큰이 저장된 뒤 화면마다 401 을 되풀이하지 않게 하기 위해서다. 서버에 닿지
 * 못했으면 판정하지 못했으므로 저장하지 않고 그렇게 남긴다.
 */
export function useAdminTokenEntry(): (token: string) => Promise<void> {
  const accept = useTokens((state) => state.acceptAdminToken);
  const reject = useTokens((state) => state.rejectAdminToken);
  const leave = useTokens((state) => state.leaveAdminTokenUnjudged);
  return useCallback(
    async (token: string) => {
      const verdict = await judgeAdminToken(token);
      if (verdict === "accepted") {
        accept(token);
      } else if (verdict === "rejected") {
        reject();
      } else {
        leave();
      }
    },
    [accept, reject, leave],
  );
}

async function judgeAdminToken(token: string): Promise<Verdict> {
  try {
    await listPlugins(token);
    return "accepted";
  } catch (error: unknown) {
    return verdictOf(error);
  }
}

/**
 * 확인 요청의 실패가 토큰에 대해 말하는 것. 봉투가 왔으면 인증 미들웨어를 지난 것이라 받아들인다. 목록의 실패(운영자
 * 파일 손상 같은 500)는 목록 자리가 말한다.
 */
function verdictOf(error: unknown): Verdict {
  // 요청 함수는 응답이 없거나 데이터가 아닌 것을 모두 RequestFailure 로 던진다. 그 밖의 예외는 이 코드의 결함이라
  // "서버에 닿지 못했다"로 덮지 않고 다시 던진다. 넣는 자리는 그때도 버튼을 푼다.
  if (!(error instanceof RequestFailure)) {
    throw error;
  }
  if (isRejection(error)) {
    return "rejected";
  }
  return error.envelope === null ? "unjudged" : "accepted";
}

/** 관리 토큰이 거부됐다는 실패인가. 401 이 거부라는 규칙은 확인 요청과 fetcher 가 이것 하나를 쓴다. */
function isRejection(error: unknown): boolean {
  return error instanceof RequestFailure && error.status === 401;
}

/** SWR 의 fetcher. 목록을 읽고, 401 이면 그 요청이 실은 관리 토큰을 내려놓는다. */
async function listOrReject(adminToken: string): Promise<PluginRow[]> {
  try {
    return await listPlugins(adminToken);
  } catch (error: unknown) {
    rejectIfStillHeld(error, adminToken);
    throw error;
  }
}

/** 그 사이 운영자가 다른 토큰을 넣었으면 그것은 둔다. 거부된 것은 옛 요청이 실은 토큰이다. */
function rejectIfStillHeld(error: unknown, adminToken: string): void {
  const tokens = useTokens.getState();
  if (isRejection(error) && tokens.adminToken === adminToken) {
    tokens.rejectAdminToken();
  }
}
