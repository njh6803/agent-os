// 관리 화면이 서버를 부르는 자리(admin-login 티켓 09). 토큰을 받지 않는 운영자 클라이언트 하나를 만들고 갱신 규칙(`rule.ts`)을
// 꽂는다. 다른 도메인(`api/plugins` 따위)의 요청 함수는 이 클라이언트를 `operatorClient()` 로 받는다. 쿠키는 브라우저가 같은
// 출처의 중계에 스스로 싣는다. 클라이언트는 부를 때 만든다. 만들 때 `location` 을 읽어 브라우저에서만 설 수 있다. 그래서 이
// 도메인의 함수들은 SWR 의 fetcher 나 이벤트 처리기에서만 부른다(`api/plugins` 의 머리 설명과 같다).
//
// 이 도메인의 요청 가운데 로그인과 첫 계정 확인은 갱신 규칙을 지나지 않는다(`rule.ts`).

import { createOperatorClient, type components, type OperatorClient } from "@agent-os/api-client";
import { failureOf, unreachable } from "../failure";
import { refreshRule, renewWhileStreaming } from "./rule";

export {
  canSignInAt,
  currentPlace,
  isPublicPath,
  loginAddress,
  nextTarget,
  noticeOf,
  setPasswordAddress,
  type LoginNotice,
} from "./address";
export { goTo } from "./navigation";

export type Me = components["schemas"]["Me"];

let client: OperatorClient | null = null;

/** 갱신 규칙이 꽂힌 운영자 클라이언트. 탭에 하나다. 같은 탭의 갱신이 하나라는 규칙이 이 하나에 기댄다. */
export function operatorClient(): OperatorClient {
  if (client === null) {
    client = createOperatorClient();
    client.use(refreshRule);
  }
  return client;
}

/**
 * 열린 스트림 동안 로그인을 이어 둔다(`POST /auth/refresh`). 갱신이 거절되면 지금 대화의 주소로 돌아올 로그인 화면으로
 * 보낸다. 이벤트 처리기나 타이머에서만 부른다.
 */
export function keepSignedIn(): Promise<void> {
  return renewWhileStreaming(async () => {
    const { response } = await operatorClient().POST("/auth/refresh");
    return response;
  });
}

/**
 * 지금 로그인한 계정을 읽는다(`GET /auth/me`). 쿠키가 없거나 끝났으면 갱신하고, 갱신까지 실패하면 로그인 화면으로
 * 보낸 뒤 401 의 RequestFailure 를 던진다(로그인 화면 자신이 읽을 때는 보내지 않는다).
 */
export async function readMe(): Promise<Me> {
  const { data, error, response } = await operatorClient()
    .GET("/auth/me")
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data === undefined) {
    throw failureOf(response.status, error);
  }
  return data;
}

/** 첫 계정이 필요한지 로그인 없이 묻는다(`GET /auth/setup`). */
export async function readNeedsFirstAccount(): Promise<boolean> {
  const { data, error, response } = await operatorClient()
    .GET("/auth/setup")
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data === undefined) {
    throw failureOf(response.status, error);
  }
  return data.needs_first_account;
}

/**
 * 계정 이름과 비밀번호로 로그인한다(`POST /auth/login`). 204 면 서버가 쿠키 둘을 심었다. 401 은 이름이나 비밀번호가
 * 맞지 않은 것이라 던지지 않고 거절로 돌려준다(서버는 어느 쪽이 틀렸는지 알리지 않는다). 그 밖의 실패는 던진다.
 */
export async function logIn(name: string, password: string): Promise<"signed-in" | "rejected"> {
  const { error, response } = await operatorClient()
    .POST("/auth/login", { body: { name, password } })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (response.status === 204) {
    return "signed-in";
  }
  if (response.status === 401) {
    return "rejected";
  }
  throw failureOf(response.status, error);
}

/** 내 비밀번호 바꾸기의 결과. 칸의 잘못(422)은 던지지 않고 칸마다의 글로 돌려준다. */
export type PasswordChange =
  | { readonly kind: "changed" }
  | { readonly kind: "locked" }
  | {
      readonly kind: "invalid";
      /** `body.current_password` 의 글. 이 칸의 잘못이 아니면 null 이다. */
      readonly current: string | null;
      /** `body.new_password` 의 글. 이 칸의 잘못이 아니면 null 이다. */
      readonly next: string | null;
    };

/**
 * 로그인한 계정의 비밀번호를 바꾼다(`POST /auth/password`). 204 면 바뀌었고 그 계정의 다른 로그인이 끊긴다. 잠겼으면 409,
 * 칸이 틀렸으면 422 다. 틀린 지금 비밀번호도 401 이 아니라 422(`body.current_password`)다. 401 이면 갱신 규칙이 같은 시도를
 * 두 번 세기 때문이다. 그 밖의 실패는 던진다.
 */
export async function changePassword(
  currentPassword: string,
  newPassword: string,
): Promise<PasswordChange> {
  const { error, response } = await operatorClient()
    .POST("/auth/password", {
      body: { current_password: currentPassword, new_password: newPassword },
    })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (response.status === 204) {
    return { kind: "changed" };
  }
  if (response.status === 409) {
    return { kind: "locked" };
  }
  const failure = failureOf(response.status, error);
  if (response.status === 422) {
    const violations = failure.envelope?.violations ?? [];
    const messageOf = (field: string): string | null =>
      violations.find((violation) => violation.field === field)?.message ?? null;
    const current = messageOf("body.current_password");
    const next = messageOf("body.new_password");
    if (current !== null || next !== null) {
      return { kind: "invalid", current, next };
    }
  }
  throw failure;
}

/** 링크로 비밀번호 정하기의 결과. */
export type PasswordSetting =
  | { readonly kind: "set" }
  /** 링크를 더 쓸 수 없다(쓴 링크, 끝난 링크, 다시 만들어 못 쓰게 된 링크, 비활성 계정, 모르는 토큰). */
  | { readonly kind: "unusable" }
  | { readonly kind: "invalid"; readonly message: string };

/**
 * 링크의 토큰으로 비밀번호를 정한다(`POST /auth/set-password`). 로그인 없이 쓰는 요청이라 갱신 규칙을 지나지 않는다. 204 면
 * 정해졌고 로그인시키지 않는다. 링크가 죽었으면 404 다. 판정은 형식, 링크, 비밀번호 규칙의 차례라 쓸 수 없는 링크가 규칙보다
 * 먼저 알려진다.
 */
export async function setPassword(token: string, password: string): Promise<PasswordSetting> {
  const { error, response } = await operatorClient()
    .POST("/auth/set-password", { body: { token, password } })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (response.status === 204) {
    return { kind: "set" };
  }
  if (response.status === 404) {
    return { kind: "unusable" };
  }
  const failure = failureOf(response.status, error);
  if (response.status === 422) {
    const violations = failure.envelope?.violations ?? [];
    if (violations.some(({ field }) => field === "body.token")) {
      // 토큰의 모양이 아닌 글은 어느 링크도 아니다.
      return { kind: "unusable" };
    }
    const message = violations.find(({ field }) => field === "body.password")?.message;
    if (message !== undefined) {
      return { kind: "invalid", message };
    }
  }
  throw failure;
}

/**
 * 이 로그인을 끊는다(`POST /auth/logout`). 쿠키를 지우는 응답(204)을 받아야 끝난 것이다. 쿠키는 HttpOnly 라 화면이 지우지
 * 못한다. 받지 못했으면(네트워크가 끊겼거나 500, 다시 보낸 뒤의 401) 던진다. 짧은 JWT 가 만료돼 401 이면 갱신 규칙이 갱신한
 * 뒤 한 번 다시 보낸다. 갱신이 거절돼도 쿠키를 지우는 줄이 왔으므로 204 와 같다.
 */
export async function logOut(): Promise<void> {
  const { error, response } = await operatorClient()
    .POST("/auth/logout")
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (response.status !== 204) {
    throw failureOf(response.status, error);
  }
}
