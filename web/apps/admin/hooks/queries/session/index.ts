// 로그인 상태의 훅(admin-login 티켓 09). 지금 누구인지 읽기, 첫 계정 확인, 로그인, 로그아웃이다. 쿠키는 HttpOnly 라 화면은
// 로그인했는지를 "지금 누구인지"를 읽어서만 안다. 401 에서 갱신하고 다시 보내는 규칙은 요청 함수 아래(`api/session`)에 있어
// 이 훅들은 갱신을 모른다.

import { useCallback, useState } from "react";
import useSWR, { type SWRResponse } from "swr";
import { RequestFailure } from "../../../api/failure";
import {
  changePassword,
  goTo,
  loginAddress,
  logIn,
  logOut,
  readMe,
  readNeedsFirstAccount,
  setPassword,
  type Me,
} from "../../../api/session";
import { READ } from "../admin";

export const sessionKeys = {
  me: () => ["me"] as const,
  setup: () => ["setup"] as const,
};

/**
 * 지금 로그인한 계정. 화면 하나가 뜰 때 한 번 읽는다. 창 포커스로 다시 읽지 않는다(이 읽기가 곧 화면을 쫓아내는 판정이라,
 * 다른 읽기가 쓰는 창 포커스 읽기와 겹쳐 같은 때에 갱신을 부르게 하지 않는다). 쿠키가 없거나 끝났으면 요청 함수 아래의
 * 규칙이 갱신하고, 갱신까지 실패하면 로그인 화면으로 보낸다.
 */
export function useMe(): SWRResponse<Me, unknown> {
  return useSWR(sessionKeys.me(), readMe, { ...READ, revalidateOnFocus: false });
}

/** 첫 계정이 필요한 서버인가. 로그인 화면이 뜰 때 읽는다. */
export function useNeedsFirstAccount(): SWRResponse<boolean, unknown> {
  return useSWR(sessionKeys.setup(), readNeedsFirstAccount, { ...READ, revalidateOnFocus: false });
}

export interface LogInAttempt {
  /** 요청이 가는 동안 참이다. 이 동안 다시 누를 수 없다. */
  readonly pending: boolean;
  /** 이름이나 비밀번호가 맞지 않아 거절됐다. 다음 시도를 보내면 걷힌다. */
  readonly rejected: boolean;
  /** 지금까지 거절된 횟수. 거절될 때마다 늘어, 쓰는 쪽이 비밀번호 칸을 새로 세우는 열쇠로 쓴다. */
  readonly rejections: number;
  /** 거절이 아닌 실패(서버에 닿지 못함, 서버의 오류). 없으면 null 이다. */
  readonly failure: RequestFailure | null;
  /** 로그인한다. 204 면 `destination` 으로 화면을 옮긴다. */
  readonly submit: (name: string, password: string) => Promise<void>;
}

/** 로그인 요청 하나와 그 결과. 성공하면 보던 화면(`destination`)으로 돌아간다. */
export function useLogIn(destination: string): LogInAttempt {
  const [pending, setPending] = useState(false);
  const [rejections, setRejections] = useState(0);
  const [rejected, setRejected] = useState(false);
  const [failure, setFailure] = useState<RequestFailure | null>(null);
  const submit = useCallback(
    async (name: string, password: string) => {
      setPending(true);
      setRejected(false);
      setFailure(null);
      try {
        const outcome = await logIn(name, password);
        if (outcome === "signed-in") {
          goTo(destination);
          return;
        }
        setRejected(true);
        setRejections((count) => count + 1);
      } catch (error: unknown) {
        // 요청 함수는 실패를 모두 RequestFailure 로 던진다. 그 밖의 예외는 이 코드의 결함이라 덮지 않고 다시 던진다.
        if (!(error instanceof RequestFailure)) {
          throw error;
        }
        setFailure(error);
      } finally {
        setPending(false);
      }
    },
    [destination],
  );
  return { pending, rejected, rejections, failure, submit };
}

export interface PasswordChangeAttempt {
  readonly pending: boolean;
  /** 바뀌었다. 다음 시도를 보내면 걷힌다. */
  readonly changed: boolean;
  /** 계정이 잠겼다(409). */
  readonly locked: boolean;
  /** 서버가 지금 비밀번호 칸에 단 글(422). */
  readonly currentError: string | null;
  /** 서버가 새 비밀번호 칸에 단 글(422). */
  readonly newError: string | null;
  /** 지금까지 바뀐 횟수. 쓰는 쪽이 칸들을 새로 세워 비우는 열쇠로 쓴다. */
  readonly changes: number;
  /** 서버에 닿지 못함, 서버의 오류. 없으면 null 이다. */
  readonly failure: RequestFailure | null;
  readonly submit: (currentPassword: string, newPassword: string) => Promise<void>;
}

/** 로그인한 계정의 비밀번호를 바꾸는 요청 하나와 그 결과(admin-login 티켓 12). */
export function useChangePassword(): PasswordChangeAttempt {
  const [pending, setPending] = useState(false);
  const [changes, setChanges] = useState(0);
  const [changed, setChanged] = useState(false);
  const [locked, setLocked] = useState(false);
  const [currentError, setCurrentError] = useState<string | null>(null);
  const [newError, setNewError] = useState<string | null>(null);
  const [failure, setFailure] = useState<RequestFailure | null>(null);
  const submit = useCallback(async (currentPassword: string, newPassword: string) => {
    setPending(true);
    setChanged(false);
    setLocked(false);
    setCurrentError(null);
    setNewError(null);
    setFailure(null);
    try {
      const outcome = await changePassword(currentPassword, newPassword);
      switch (outcome.kind) {
        case "changed":
          setChanged(true);
          setChanges((count) => count + 1);
          break;
        case "locked":
          setLocked(true);
          break;
        case "invalid":
          setCurrentError(outcome.current);
          setNewError(outcome.next);
          break;
      }
    } catch (error: unknown) {
      if (!(error instanceof RequestFailure)) {
        throw error;
      }
      setFailure(error);
    } finally {
      setPending(false);
    }
  }, []);
  return { pending, changed, locked, currentError, newError, changes, failure, submit };
}

export interface PasswordSettingAttempt {
  readonly pending: boolean;
  /** 링크를 더 쓸 수 없다(404). 화면이 입력 칸을 걷는다. */
  readonly unusable: boolean;
  /** 서버가 비밀번호 칸에 단 글(422). */
  readonly passwordError: string | null;
  /** 서버에 닿지 못함, 서버의 오류. 없으면 null 이다. */
  readonly failure: RequestFailure | null;
  /** 정한다. 204 면 로그인 화면으로 옮긴다. */
  readonly submit: (password: string) => Promise<void>;
}

/**
 * 링크로 비밀번호를 정하는 요청 하나와 그 결과(admin-login 티켓 12). `token` 이 없으면(주소에 `#` 뒤가 없었다) 요청을 보내지
 * 않고 쓸 수 없는 링크로 본다.
 */
export function useSetPassword(token: string | null): PasswordSettingAttempt {
  const [pending, setPending] = useState(false);
  const [unusable, setUnusable] = useState(token === null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [failure, setFailure] = useState<RequestFailure | null>(null);
  const submit = useCallback(
    async (password: string) => {
      if (token === null) {
        setUnusable(true);
        return;
      }
      setPending(true);
      setPasswordError(null);
      setFailure(null);
      try {
        const outcome = await setPassword(token, password);
        switch (outcome.kind) {
          case "set":
            goTo(loginAddress({ notice: "password-set" }));
            break;
          case "unusable":
            setUnusable(true);
            break;
          case "invalid":
            setPasswordError(outcome.message);
            break;
        }
      } catch (error: unknown) {
        if (!(error instanceof RequestFailure)) {
          throw error;
        }
        setFailure(error);
      } finally {
        setPending(false);
      }
    },
    [token],
  );
  return { pending, unusable: unusable || token === null, passwordError, failure, submit };
}

export interface LogOutAttempt {
  readonly pending: boolean;
  /** 쿠키를 지우는 응답을 받지 못했다. 다시 누르면 걷힌다. */
  readonly failed: boolean;
  readonly submit: () => Promise<void>;
}

/**
 * 로그아웃한다. 쿠키를 지우는 응답(204)을 받아야 로그인 화면으로 간다. 받지 못했으면 가지 않고 실패를 알린다. 쿠키는
 * HttpOnly 라 화면이 지우지 못하므로, 이때 로그인 화면으로 보내면 갱신용 번호가 브라우저에 남아 공용 PC 의 다음 사람이
 * 그 로그인을 이어 받는다.
 */
export function useLogOut(): LogOutAttempt {
  const [pending, setPending] = useState(false);
  const [failed, setFailed] = useState(false);
  const submit = useCallback(async () => {
    setPending(true);
    setFailed(false);
    try {
      await logOut();
      goTo(loginAddress({ notice: "logged-out" }));
    } catch (error: unknown) {
      if (!(error instanceof RequestFailure)) {
        throw error;
      }
      setFailed(true);
    } finally {
      setPending(false);
    }
  }, []);
  return { pending, failed, submit };
}
