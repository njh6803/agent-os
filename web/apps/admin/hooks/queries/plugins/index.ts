// 플러그인의 SWR 훅. 컴포넌트는 useSWR 이나 요청 함수를 직접 부르지 않고 이 훅을 쓴다. 읽기 정책은 실행의 훅과 함께 쓴다
// (`hooks/queries/admin`). 401 은 요청 함수 아래의 갱신 규칙이 받는다(`api/session`, admin-login 티켓 09). 이 훅들은 로그인한
// 화면 안에서만 선다. `AdminScreen` 이 "지금 누구인지"를 읽은 뒤에 그린다.

import { useCallback } from "react";
import useSWR, { type SWRResponse, useSWRConfig } from "swr";
import {
  listPlugins,
  readPlugin,
  setPluginEnabled,
  type Plugin,
  type PluginKind,
  type PluginRow,
} from "../../../api/plugins";
import { READ } from "../admin";

/**
 * SWR 키. 계정은 키에 싣지 않는다. 계정이 바뀌려면 로그인 화면을 지나 화면을 새로 불러오므로 앞 계정의 캐시가 남지
 * 않는다.
 */
export const pluginKeys = {
  list: () => ["plugins"] as const,
  one: (kind: PluginKind, name: string) => ["plugins", kind, name] as const,
};

/**
 * 플러그인 목록. `active` 가 거짓이면 부르지 않는다. `active` 는 목록을 쓰는 자리가 늘 서 있지 않은 화면의 것이다. 실행
 * 하나의 화면은 결정 자리가 설 때만 꺼짐 미리 알림에 목록을 읽는다.
 */
export function usePlugins({ active = true }: { readonly active?: boolean } = {}): SWRResponse<
  PluginRow[],
  unknown
> {
  return useSWR(active ? pluginKeys.list() : null, active ? listPlugins : null, READ);
}

/** 플러그인 하나. */
export function usePlugin(kind: PluginKind, name: string): SWRResponse<Plugin, unknown> {
  return useSWR(pluginKeys.one(kind, name), () => readPlugin(kind, name), READ);
}

/**
 * 플러그인 하나를 켜거나 끈다(web-admin 명세 "켜고 끄기"). 응답 뒤에 목록과 그 행을 다시 읽고, 그것이 끝나야
 * 돌아온다. 스위치는 화면이 뒤집은 값이 아니라 다시 읽은 값을 따른다(스토리 18). 실패해도 다시 읽고 실패를 그대로
 * 던진다(스토리 19).
 *
 * 그 행(플러그인 하나)은 캐시의 값을 버리며 다시 읽는다. 화면에 떠 있지 않으면 SWR 의 mutate 는 요청을 보내지 않으므로
 * 캐시를 버려야 다음에 열 때 옛 켜짐 대신 자리표시가 서고 새로 읽는다.
 */
export function useSetPluginEnabled(): (
  kind: PluginKind,
  name: string,
  change: { readonly enabled: boolean },
) => Promise<void> {
  const { mutate } = useSWRConfig();
  return useCallback(
    async (kind: PluginKind, name: string, change: { readonly enabled: boolean }) => {
      try {
        await setPluginEnabled(kind, name, change);
      } finally {
        // mutate 는 다시 읽기의 실패를 던지지 않고 그 키의 error 로 둔다. 그래서 이 finally 가 try 의 실패를 덮지
        // 않는다. 페이지 테스트 "켜고 끈 뒤 다시 읽기도 실패하면…"이 알림이 하나뿐인지로 그것을 본다.
        await Promise.all([
          mutate(pluginKeys.list()),
          mutate(pluginKeys.one(kind, name), undefined, { revalidate: true }),
        ]);
      }
    },
    [mutate],
  );
}
