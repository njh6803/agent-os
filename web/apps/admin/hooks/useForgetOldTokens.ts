import { useEffect } from "react";

/** 공유 토큰을 이 탭의 sessionStorage 에 남기던 옛 판의 키. 지금은 토큰을 쓰지 않는다. */
const OLD_TOKENS_KEY = "agent-os-admin-tokens";

/**
 * 옛 판이 이 탭에 남긴 토큰을 화면이 뜰 때 지운다(admin-login 명세 "설정 화면"). 판을 올리기 전에 연 탭이 그대로
 * 열려 있으면 옛 토큰이 그 탭의 저장소에 남아 있고, 쓰지 않는 비밀 글을 남겨 둘 까닭이 없다. 저장소를 못 쓰는
 * 환경(막은 창)에서는 지울 것도 없으므로 실패는 삼킨다.
 */
export function useForgetOldTokens(): void {
  useEffect(() => {
    try {
      sessionStorage.removeItem(OLD_TOKENS_KEY);
    } catch {
      // 저장소를 읽지 못하면 남은 토큰도 이 화면이 읽지 못한다.
    }
  }, []);
}
