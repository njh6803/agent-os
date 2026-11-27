// 운영자 계정의 SWR 훅(admin-login 티켓 12). 컴포넌트는 useSWR 이나 요청 함수를 직접 부르지 않고 이 훅을 쓴다. 읽기 정책은
// 다른 도메인과 함께 쓴다(`hooks/queries/admin`). 401 은 요청 함수 아래의 갱신 규칙이 받는다(`api/session`). 이 훅들은 로그인한
// 화면 안에서만 선다. `AdminScreen` 이 "지금 누구인지"를 읽은 뒤에 그린다.

import { useCallback, useMemo } from "react";
import useSWR, { type SWRResponse, useSWRConfig } from "swr";
import {
  createAccount,
  disableAccount,
  enableAccount,
  issueLink,
  listAccounts,
  unlockAccount,
  type AccountCreation,
  type AccountRow,
  type IssuedLink,
} from "../../../api/accounts";
import { READ } from "../admin";

/** SWR 키. 계정 목록은 하나다. */
export const accountKeys = {
  list: () => ["accounts"] as const,
};

/**
 * 계정 목록. `active` 가 거짓이면 부르지 않는다. 계정 화면은 시스템 관리자만 열 수 있어서, 관리자가 주소로 열었을 때는 서버에
 * 묻지 않는다(서버도 `manage_accounts` 가 없는 계정에 403 이다).
 */
export function useAccounts({
  active,
}: {
  readonly active: boolean;
}): SWRResponse<AccountRow[], unknown> {
  return useSWR(active ? accountKeys.list() : null, active ? listAccounts : null, READ);
}

/** 계정 화면의 쓰기 다섯. 응답 뒤에 목록을 다시 읽고, 그것이 끝나야 돌아온다. 실패해도 다시 읽고 실패를 그대로 던진다. */
export interface AccountActions {
  readonly create: (name: string) => Promise<AccountCreation>;
  readonly issueLink: (name: string) => Promise<IssuedLink>;
  readonly enable: (name: string) => Promise<void>;
  readonly disable: (name: string) => Promise<void>;
  readonly unlock: (name: string) => Promise<void>;
}

export function useAccountActions(): AccountActions {
  const { mutate } = useSWRConfig();
  // mutate 는 다시 읽기의 실패를 던지지 않고 그 키의 error 로 둔다. 그래서 이 finally 가 try 의 실패를 덮지 않는다.
  const reload = useCallback(() => mutate(accountKeys.list()), [mutate]);
  const after = useCallback(
    async <T>(request: () => Promise<T>): Promise<T> => {
      try {
        return await request();
      } finally {
        await reload();
      }
    },
    [reload],
  );
  return useMemo(
    () => ({
      create: (name) => after(() => createAccount(name)),
      issueLink: (name) => after(() => issueLink(name)),
      enable: (name) => after(() => enableAccount(name)),
      disable: (name) => after(() => disableAccount(name)),
      unlock: (name) => after(() => unlockAccount(name)),
    }),
    [after],
  );
}
