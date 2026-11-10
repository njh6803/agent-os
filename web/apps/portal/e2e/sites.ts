// 질문 페이지 e2e 가 설정과 사이트 파일에 싣는 사이트 넷(pilot-portal 명세 "Playwright e2e"). 준비(`stack.ts`)가 설정과 사이트
// 파일을 짓는 데, 시험이 기대하는 값을 읽는 데 같은 목록을 쓴다.
//
// - 익명 사이트 둘. 같은 픽스처 에이전트를 열고 하나(`limited`)는 사이트의 시간당 실행 상한이 1이다.
// - 익명과 로그인 둘 다 되는 사이트 하나, 로그인만 되는 사이트 하나.
// - 첫 사이트만 소개 글과 모드를 적어, `?site=` 를 주지 않은 첫 그림과 속성 다섯이 채워지는 것을 가르게 한다.

export interface E2eSite {
  readonly name: string;
  /** 사이트 파일의 항목을 고르는 열쇠. */
  readonly issuer: string;
  readonly heading: string;
  readonly intro?: string;
  readonly theme: string;
  readonly mode?: string;
  readonly assurance: "anonymous" | "login" | "both";
  /** 사이트 파일의 `hourly_runs_per_site`. */
  readonly hourlyRunsPerSite?: number;
}

/** 모든 사이트가 여는 픽스처 에이전트(`@agent-os/e2e-stack` 의 `AGENTS`). */
export const AGENT = "echo";

export const SITES: readonly E2eSite[] = [
  {
    name: "first",
    issuer: "https://first.portal.e2e.example",
    heading: "첫째 사이트",
    intro: "첫째 사이트의 소개 글입니다.",
    theme: "jacho",
    mode: "dark",
    assurance: "anonymous",
  },
  {
    name: "limited",
    issuer: "https://limited.portal.e2e.example",
    heading: "한도가 작은 사이트",
    theme: "guncheong",
    assurance: "anonymous",
    hourlyRunsPerSite: 1,
  },
  {
    name: "either",
    issuer: "https://either.portal.e2e.example",
    heading: "둘 다 되는 사이트",
    theme: "jjokbit",
    assurance: "both",
  },
  {
    name: "gated",
    issuer: "https://gated.portal.e2e.example",
    heading: "로그인 사이트",
    theme: "nokcheong",
    assurance: "login",
  },
];
