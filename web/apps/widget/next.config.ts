// 위젯의 Next 설정. iframe 페이지(/widget)와 위젯이 내주는 공개 파일(/widget/fonts/)을 낸다(ADR 0024).
//
// - basePath 는 /widget 이다(ADR 0024 의 2026-10-23 이력). nginx 가 그 접두사 하나를 Next 로 넘긴다. headers 의 source
//   에는 basePath 가 저절로 붙는다(Next 16.3.6 설치본의 headers 문서).
// - frame-ancestors 는 'none' 이다. 사이트 파일에서 허용 출처를 넣는 것은 web-widget 티켓 04 이고, 그 전에는 어떤
//   사이트도 품지 못하게 해 ADR 0024 의 fail-closed 가 처음부터 선다. 헤더는 빌드 산출물(routes-manifest.json)에 박혀,
//   운영 모드의 start 는 빌드 때의 값을 낸다(관리 화면의 next.config.ts 가 rewrites 에 대해 적은 것과 같다).
// - 글꼴 파일은 시작 래퍼가 public/fonts/ 에 복사한다(tools/fonts.ts). 자격 증명 없이 받는 공개 파일이라
//   Access-Control-Allow-Origin 을 * 로 단다. 페이지 안 번들(티켓 10)이 사이트 문서에서 FontFace 로 받는다.
// - rewrites 를 두지 않는다. API 는 nginx 가 파이썬에 바로 넘기므로, 처음 바깥에 열리는 Next 가 중계가 되지 않게
//   하기 위해서다(ADR 0024).
// - agentRules: false. next dev 가 에이전트를 감지하면 앱 폴더에 AGENTS.md 와 CLAUDE.md 를 만든다(ADR 0021).

import type { NextConfig } from "next";

const config: NextConfig = {
  basePath: "/widget",
  agentRules: false,
  headers() {
    return Promise.resolve([
      {
        source: "/:path*",
        headers: [{ key: "Content-Security-Policy", value: "frame-ancestors 'none'" }],
      },
      {
        source: "/fonts/:path*",
        headers: [{ key: "Access-Control-Allow-Origin", value: "*" }],
      },
    ]);
  },
};

export default config;
