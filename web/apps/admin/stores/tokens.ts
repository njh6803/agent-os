// 토큰을 드는 스토어(ADR 0019, 0021). 브라우저가 토큰을 들고 매 요청의 헤더에 싣는다. 토큰은 그 탭의
// sessionStorage 에만 남는다. 새로 고쳐도 다시 넣지 않고, 탭을 닫으면 사라진다. localStorage 는 디스크에 평문으로
// 남고 모든 탭이 나눠 가져서 쓰지 않는다.
//
// persist 는 토큰만 저장한다(partialize). 넣는 자리의 알림은 화면의 상태라 새로 고치면 사라진다. 서버 응답은 여기
// 복사하지 않는다. 서버 데이터는 SWR 이 든다.
//
// 채널 토큰은 결정 화면(티켓 08)이 더한다.

import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

/** 관리 토큰을 넣는 자리가 운영자에게 알릴 것. 거부됐다, 또는 서버에 닿지 못해 판정하지 못했다. */
export type AdminTokenNotice = "rejected" | "unreachable";

interface Tokens {
  /** 받아들여진 관리 토큰. 없으면 관리 화면은 토큰을 넣는 자리다. */
  readonly adminToken: string | null;
  /**
   * 관리 토큰을 받아들인 횟수. SWR 키에 토큰 대신 싣는다. 키가 토큰마다 같으면 지운 토큰의 진행 중인 요청을 새
   * 토큰의 목록이 나눠 받는다(SWR 의 중복 제거). 새로 고치면 0 부터 다시 센다. 그때는 캐시도 새로 선다.
   */
  readonly adminTokenGeneration: number;
  /** 넣는 자리의 알림. 토큰이 받아들여지거나 지워지면 걷힌다. */
  readonly adminTokenNotice: AdminTokenNotice | null;
  readonly acceptAdminToken: (token: string) => void;
  /** 거부된 관리 토큰을 내려놓는다. 거부된 토큰을 들고 있으면 모든 요청이 같은 401 을 되풀이한다. */
  readonly rejectAdminToken: () => void;
  /** 넣은 관리 토큰을 판정하지 못했다. 저장하지 않는다. */
  readonly leaveAdminTokenUnjudged: () => void;
  readonly clearTokens: () => void;
}

export const useTokens = create<Tokens>()(
  persist(
    (set) => ({
      adminToken: null,
      adminTokenGeneration: 0,
      adminTokenNotice: null,
      acceptAdminToken: (token) => {
        set(({ adminTokenGeneration }) => ({
          adminToken: token,
          adminTokenGeneration: adminTokenGeneration + 1,
          adminTokenNotice: null,
        }));
      },
      rejectAdminToken: () => {
        set({ adminToken: null, adminTokenNotice: "rejected" });
      },
      leaveAdminTokenUnjudged: () => {
        set({ adminTokenNotice: "unreachable" });
      },
      clearTokens: () => {
        set({ adminToken: null, adminTokenNotice: null });
      },
    }),
    {
      name: "agent-os-admin-tokens",
      // 서버에서 한 번 그릴 때는 sessionStorage 가 없다. 그때 zustand 는 저장소 없이 선다.
      storage: createJSONStorage(() => sessionStorage),
      partialize: ({ adminToken }) => ({ adminToken }),
    },
  ),
);
