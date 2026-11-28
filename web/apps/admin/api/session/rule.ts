// 화면이 갱신을 부르는 규칙(admin-login 명세 "화면이 갱신을 부르는 규칙"). 화면의 모든 요청이 지나는 운영자 클라이언트의
// 중간 층 하나에 둔다. 한 자리라서 화면마다 갱신을 다르게 쓰지 못한다.
//
// - 요청이 401 을 받으면 갱신을 한 번 부르고, 204 면 처음 요청을 한 번 다시 보낸다. 다시 보낸 요청이 또 401 이면 갱신을
//   다시 부르지 않고 로그인 화면으로 간다(같은 요청이 갱신을 끝없이 되풀이하지 않게 한다).
// - 같은 탭의 갱신은 하나다. 도는 갱신이 있으면 401 을 받은 다른 요청은 새 갱신을 보내지 않고 그것을 함께 기다린다.
// - 갱신이 401 이면 `/login?next=<지금 주소>&notice=expired` 로 간다. 다만 화면을 열면서 처음 묻는 "지금 누구인지"
//   (`/auth/me`)가 갱신까지 401 이면 알림 없이 `/login?next=<지금 주소>` 다. 방금 연 화면에 "로그인이 끝났다"를 알릴
//   일이 아니다. 갱신이 그 밖의 실패(네트워크, 5xx)면 로그인이 끝났는지 모르므로 보내지 않고 처음 401 을 그대로 돌려준다.
// - 로그인, 갱신, 첫 계정 확인, 링크로 비밀번호 정하기는 이 규칙을 지나지 않는다. 앞의 셋은 로그인 상태를 만들거나 로그인하기
//   전에 묻는 요청이고, 마지막은 로그인 없이 쓰는 화면의 요청이다.
//
// 갱신하고 다시 보내는 일을 SWR 이 결과를 받기 전에 끝낸다. 요청 함수 안에서 끝나므로 SWR 은 실패를 보지 못한다. SWR 은
// 읽기가 실패하면 실패가 걷힐 때까지 주기 읽기를 쉬기 때문이다(`.scratch/admin-login/probes/swr_poll/README.md` 결과 3).

import type { OperatorMiddleware } from "@agent-os/api-client";
import { currentPlace, isPublicPath, loginAddress } from "./address";
import { goTo } from "./navigation";

/**
 * 규칙을 지나지 않는 경로. 로그인과 갱신과 첫 계정 확인은 로그인 상태를 만들거나 로그인하기 전에 묻는 요청이고, 링크로
 * 비밀번호 정하기(`/auth/set-password`)는 로그인 없이 쓰는 화면의 요청이다.
 */
const OUTSIDE_RULE: ReadonlySet<string> = new Set([
  "/auth/login",
  "/auth/refresh",
  "/auth/setup",
  "/auth/set-password",
]);

/** 갱신의 결과. 갱신됐다, 로그인이 끝났다, 끝났는지 모른다(네트워크나 5xx). */
type Renewal = "renewed" | "ended" | "unknown";

/** 다시 보낼 복사본. 처음 요청은 보내면서 본문을 쓰므로 보내기 전에 복사해 둔다. 요청마다 `id` 가 다르다. */
const copies = new Map<string, Request>();

/** 도는 갱신. 있으면 새로 보내지 않고 이것을 함께 기다린다. */
let running: Promise<Renewal> | null = null;

async function refresh(request: () => Promise<Response>): Promise<Renewal> {
  try {
    const response = await request();
    if (response.status === 204) {
      return "renewed";
    }
    return response.status === 401 ? "ended" : "unknown";
  } catch {
    // 응답을 받지 못했다. 로그인이 끝났는지는 모르므로 로그인 화면으로 보내지 않는다.
    return "unknown";
  }
}

function refreshOnce(request: () => Promise<Response>): Promise<Renewal> {
  running ??= refresh(request).finally(() => {
    running = null;
  });
  return running;
}

/**
 * 스트림이 열린 동안의 갱신(명세 "스트림이 열린 동안의 갱신"). 다른 요청이 없어 401 이 나지 않으니 화면이 짧은 JWT 수명에
 * 맞춰 스스로 부른다. 도는 갱신이 있으면 그것을 함께 기다리므로 같은 탭의 갱신은 여전히 하나다. 갱신이 401 이면 지금 대화의
 * 주소를 `next` 에 싣고 로그인 화면으로 간다("스트림 도중 갱신이 실패하면"). 네트워크나 5xx 는 로그인이 끝났는지 모르므로
 * 아무것도 하지 않는다.
 */
export async function renewWhileStreaming(request: () => Promise<Response>): Promise<void> {
  if ((await refreshOnce(request)) === "ended") {
    leave("");
  }
}

/**
 * 로그인이 끝났다고 보고 로그인 화면으로 보낸다. 어디서 쫓겨났는지에 따라 알림이 다르다. 지금 화면이 로그인 없이 열리는
 * 화면이면(로그인 화면 자신이 "지금 누구인지"를 읽는 때) 보내지 않는다. 이미 그 자리다.
 */
function leave(schemaPath: string): void {
  if (isPublicPath(location.pathname)) {
    return;
  }
  if (schemaPath === "/auth/me") {
    // 화면을 열면서 처음 묻는 일이다. 방금 열었으니 "로그인이 끝났다"가 아니다.
    goTo(loginAddress({ next: currentPlace() }));
  } else {
    goTo(loginAddress({ next: currentPlace(), notice: "expired" }));
  }
}

export const refreshRule: OperatorMiddleware = {
  onRequest({ request, schemaPath, id }) {
    if (!OUTSIDE_RULE.has(schemaPath)) {
      copies.set(id, request.clone());
    }
    return undefined;
  },
  async onResponse({ response, schemaPath, options, id }) {
    const copy = copies.get(id);
    copies.delete(id);
    if (copy === undefined || response.status !== 401) {
      return undefined;
    }
    // 브라우저의 `fetch` 는 `options` 의 메서드로 부르면 "Illegal invocation" 이 나서 갱신이 나가지도 못한 채 "모름"이 된다.
    // 그래서 함수만 꺼내 부른다.
    const send = options.fetch;
    const outcome = await refreshOnce(() =>
      send(new Request(`${options.baseUrl}/auth/refresh`, { method: "POST" })),
    );
    if (outcome === "unknown") {
      return undefined;
    }
    if (outcome === "ended") {
      if (schemaPath === "/auth/logout") {
        // 거절된 갱신은 쿠키를 지우는 줄 둘을 싣는다. 로그아웃이 204 로 끝난 것과 같아 로그아웃의 호출이 로그아웃 알림의
        // 로그인 화면으로 보낸다.
        return new Response(null, { status: 204 });
      }
      leave(schemaPath);
      return undefined;
    }
    const again = await send(copy);
    // 다시 보낸 로그아웃이 또 401 이면 쿠키를 지우는 응답을 받지 못한 것이다. 로그인 화면으로 보내지 않고 부른 쪽이 "로그아웃하지
    // 못했다"를 보이게 둔다. 갱신용 번호가 브라우저에 남기 때문이다.
    if (again.status === 401 && schemaPath !== "/auth/logout") {
      leave(schemaPath);
    }
    return again;
  },
  onError({ id }) {
    copies.delete(id);
    return undefined;
  },
};
