// 운영자 계정의 요청 함수(admin-login 티켓 12, 명세 "계정을 다루는 경로"). 공용 운영자 클라이언트만 쓰고 데이터만 돌려준다.
// 데이터가 아니면 RequestFailure 를 던진다. 다만 화면이 문구를 달리 보이는 갈래(이름이 이미 있음, 이름이 규칙을 어김)는
// 던지지 않고 값으로 돌려준다. 이 함수들은 SWR 의 fetcher 나 이벤트 처리기에서만 부른다(`api/plugins` 의 머리 설명과 같다).

import type { components } from "@agent-os/api-client";
import { failureOf, unreachable } from "../failure";
import { operatorClient } from "../session";

export type AccountRow = components["schemas"]["AccountSummary"];

/** 새로 만든 비밀번호 링크. 토큰은 이 응답에서만 볼 수 있다(서버는 토큰의 해시만 둔다). */
export interface IssuedLink {
  readonly name: string;
  readonly token: string;
  /** 링크가 끝나는 시각(ISO 8601). */
  readonly expiresAt: string;
}

/** 운영자 계정 전부(`GET /accounts`). 시스템 관리자가 먼저이고 나머지는 이름순이다. 비활성 계정도 든다. */
export async function listAccounts(): Promise<AccountRow[]> {
  const { data, error, response } = await operatorClient()
    .GET("/accounts")
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data === undefined) {
    throw failureOf(response.status, error);
  }
  return data.accounts;
}

/** 계정을 만든 결과. 이름이 이미 있거나 규칙을 어긴 것은 던지지 않고 돌려준다. */
export type AccountCreation =
  | { readonly kind: "created"; readonly link: IssuedLink }
  | { readonly kind: "taken" }
  | { readonly kind: "invalid"; readonly message: string };

/**
 * 계정을 만든다(`POST /accounts`). 단계는 언제나 관리자이고 첫 비밀번호 링크가 함께 온다. 같은 이름의 계정이 어느 상태로든
 * 있으면 409, 이름이 규칙을 어기면 422(`body.name`)다.
 */
export async function createAccount(name: string): Promise<AccountCreation> {
  const { data, error, response } = await operatorClient()
    .POST("/accounts", { body: { name } })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data !== undefined) {
    return {
      kind: "created",
      link: { name: data.name, token: data.link_token, expiresAt: data.link_expires_at },
    };
  }
  if (response.status === 409) {
    return { kind: "taken" };
  }
  const failure = failureOf(response.status, error);
  if (response.status === 422) {
    const message = failure.envelope?.violations.find(
      ({ field }) => field === "body.name",
    )?.message;
    if (message !== undefined) {
      return { kind: "invalid", message };
    }
  }
  throw failure;
}

/** 계정의 새 비밀번호 링크를 만든다(`POST /accounts/{name}/link`). 앞의 쓰지 않은 링크는 못 쓰게 된다. */
export async function issueLink(name: string): Promise<IssuedLink> {
  const { data, error, response } = await operatorClient()
    .POST("/accounts/{name}/link", { params: { path: { name } } })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (data === undefined) {
    throw failureOf(response.status, error);
  }
  return { name, token: data.link_token, expiresAt: data.link_expires_at };
}

/** 계정을 활성으로 바꾼다(`PUT /accounts/{name}/active`). 멱등이고 답은 본문 없는 204 다. */
export function enableAccount(name: string): Promise<void> {
  return putActive(name, { active: true });
}

/** 계정을 비활성으로 바꾼다. 그 계정의 쓰지 않은 비밀번호 링크도 못 쓰게 된다. */
export function disableAccount(name: string): Promise<void> {
  return putActive(name, { active: false });
}

async function putActive(name: string, body: { readonly active: boolean }): Promise<void> {
  const { error, response } = await operatorClient()
    .PUT("/accounts/{name}/active", { params: { path: { name } }, body })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (!response.ok) {
    throw failureOf(response.status, error);
  }
}

/** 계정의 잠금과 틀린 횟수를 지운다(`POST /accounts/{name}/unlock`). */
export async function unlockAccount(name: string): Promise<void> {
  const { error, response } = await operatorClient()
    .POST("/accounts/{name}/unlock", { params: { path: { name } } })
    .catch((cause: unknown) => {
      throw unreachable(cause);
    });
  if (!response.ok) {
    throw failureOf(response.status, error);
  }
}
