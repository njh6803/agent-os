// 위젯 미리보기 페이지 e2e 가 설정과 사이트 파일에 싣는 사이트 넷(pilot-portal 명세 "Playwright e2e"). 준비(`stack.ts`)가 설정과 사이트
// 파일을 짓는 데, 시험이 기대하는 값을 읽는 데 같은 목록을 쓴다.
//
// - 익명 사이트 둘. 기본 모드에서는 같은 픽스처 에이전트를 열고(실제 모델 모드에서는 첫 사이트만 계산 에이전트를 연다. `stack.ts`)
//   하나(`limited`)는 사이트의 시간당 실행 상한이 1이다.
// - 익명과 로그인 둘 다 되는 사이트 하나, 로그인만 되는 사이트 하나.
// - 첫 사이트만 소개 글과 모드와 고지 글을 적어, `?site=` 를 주지 않은 첫 그림과 속성 다섯이 채워지는 것, 사이트의 고지 글이
//   덮개의 전문이 되는 것을 가르게 한다. 나머지는 기본 고지 글이다.
// - 보고서 주소는 첫 사이트와 둘 다 사이트만 적는다. 보고서 링크가 있는 사이트와 없는 사이트(한도가 작은 사이트, 로그인
//   사이트)를 모두 둔다. 주소는 열리지 않는 자리(`report.example`)이고 시험은 링크의 속성만 본다.

export interface E2eSite {
  readonly name: string;
  /** 사이트 파일의 항목을 고르는 열쇠. */
  readonly issuer: string;
  readonly heading: string;
  readonly intro?: string;
  readonly theme: string;
  readonly mode?: string;
  /** 사이트가 적은 고지 글. 없으면 위젯 미리보기 페이지의 기본 글이다. */
  readonly notice?: string;
  /** 평가 보고서 주소. 없으면 페이지가 보고서 링크를 그리지 않는다. */
  readonly reportUrl?: string;
  readonly assurance: "anonymous" | "login" | "both";
  /** 사이트 파일의 `hourly_runs_per_site`. */
  readonly hourlyRunsPerSite?: number;
}

/** 기본 모드에서 모든 사이트가 여는 픽스처 에이전트(`@agent-os/e2e-stack` 의 `AGENTS`). 실제 모델 모드의 첫 사이트는 다르다. */
export const AGENT = "echo";

export const SITES: readonly E2eSite[] = [
  {
    name: "first",
    issuer: "https://first.portal.e2e.example",
    heading: "첫째 사이트",
    intro: "첫째 사이트의 소개 글입니다.",
    theme: "jacho",
    mode: "dark",
    notice: "첫째 사이트가 직접 적은 고지 글입니다.",
    reportUrl: "https://report.example/first",
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
    reportUrl: "https://report.example/either",
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
