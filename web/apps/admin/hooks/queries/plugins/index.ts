// 플러그인의 SWR 훅. 컴포넌트는 useSWR 이나 요청 함수를 직접 부르지 않고 이 훅을 쓴다. 읽기 정책과 401 의 처리는
// 실행의 훅과 함께 쓴다(`hooks/queries/admin`).
//
// 관리 토큰의 판정은 결과를 돌려주지 않고 스토어에 남긴다. 받아들임, 거부, 판정하지 못함이 모두 스토어의 값이다.

import { useCallback } from "react";
import useSWR, { type SWRResponse, useSWRConfig } from "swr";
import { RequestFailure } from "../../../api/failure";
import {
  listPlugins,
  readPlugin,
  setPluginEnabled,
  type Plugin,
  type PluginKind,
  type PluginRow,
} from "../../../api/plugins";
import { useTokens } from "../../../stores/tokens";
import { isRejection, orRejectAdminToken, READ } from "../admin";

/**
 * SWR 키. 토큰은 키에 싣지 않는다. 토큰은 요청의 헤더에만 있다. 대신 토큰을 받아들인 횟수를 실어 토큰마다 캐시와
 * 진행 중인 요청을 가른다(스토어의 `adminTokenGeneration`).
 */
export const pluginKeys = {
  list: (generation: number) => ["plugins", generation] as const,
  one: (generation: number, kind: PluginKind, name: string) =>
    ["plugins", generation, kind, name] as const,
};

type Verdict = "accepted" | "rejected" | "unjudged";

/** 플러그인 목록. 관리 토큰이 없으면 부르지 않는다. */
export function usePlugins(): SWRResponse<PluginRow[], unknown> {
  const adminToken = useTokens((state) => state.adminToken);
  const generation = useTokens((state) => state.adminTokenGeneration);
  return useSWR(
    adminToken === null ? null : pluginKeys.list(generation),
    adminToken === null ? null : () => orRejectAdminToken(adminToken, listPlugins),
    READ,
  );
}

/** 플러그인 하나. 관리 토큰이 없으면 부르지 않는다. */
export function usePlugin(kind: PluginKind, name: string): SWRResponse<Plugin, unknown> {
  const adminToken = useTokens((state) => state.adminToken);
  const generation = useTokens((state) => state.adminTokenGeneration);
  return useSWR(
    adminToken === null ? null : pluginKeys.one(generation, kind, name),
    adminToken === null
      ? null
      : () => orRejectAdminToken(adminToken, (token) => readPlugin(token, kind, name)),
    READ,
  );
}

/**
 * 플러그인 하나를 켜거나 끈다(web-admin 명세 "켜고 끄기"). 응답 뒤에 목록과 그 행을 다시 읽고, 그것이 끝나야
 * 돌아온다. 스위치는 화면이 뒤집은 값이 아니라 다시 읽은 값을 따른다(스토리 18). 실패해도 다시 읽고 실패를 그대로
 * 던진다(스토리 19).
 *
 * 그 행(플러그인 하나)은 캐시의 값을 버리며 다시 읽는다. 화면에 떠 있지 않으면 SWR 의 mutate 는 요청을 보내지 않으므로
 * 캐시를 버려야 다음에 열 때 옛 켜짐 대신 자리표시가 서고 새로 읽는다.
 *
 * 401 이면 관리 토큰을 내려놓는다. 목록은 토큰과 함께 화면에서 걷히고, mutate 는 걷힌 키를 다시 읽지 않는다. 거부된
 * 토큰으로 목록을 다시 읽지 않는다는 것은 페이지 테스트가 요청 수로 본다. jsdom 에서 401 뒤 finally 에 닿을 때 목록의
 * 스위치가 문서에 없는 것을 쟀다(`.scratch/web-admin/probes/switch_after_rejection.mjs`).
 */
export function useSetPluginEnabled(): (
  kind: PluginKind,
  name: string,
  enabled: boolean,
) => Promise<void> {
  const adminToken = useTokens((state) => state.adminToken);
  const generation = useTokens((state) => state.adminTokenGeneration);
  const { mutate } = useSWRConfig();
  return useCallback(
    async (kind: PluginKind, name: string, enabled: boolean) => {
      if (adminToken === null) {
        // 스위치는 관리 토큰이 있을 때만 서는 목록에 있다.
        return;
      }
      try {
        await orRejectAdminToken(adminToken, (token) =>
          setPluginEnabled(token, kind, name, enabled),
        );
      } finally {
        // mutate 는 다시 읽기의 실패를 던지지 않고 그 키의 error 로 둔다. 그래서 이 finally 가 try 의 실패를 덮지
        // 않는다. 페이지 테스트 "켜고 끈 뒤 다시 읽기도 실패하면…"이 알림이 하나뿐인지로 그것을 본다.
        await Promise.all([
          mutate(pluginKeys.list(generation)),
          mutate(pluginKeys.one(generation, kind, name), undefined, { revalidate: true }),
        ]);
      }
    },
    [adminToken, generation, mutate],
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
