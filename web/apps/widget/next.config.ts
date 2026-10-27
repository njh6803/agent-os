// 위젯의 Next 설정. iframe 페이지(/widget)와 위젯이 내주는 공개 파일(/widget/fonts/)을 낸다(ADR 0024).
//
// - basePath 는 /widget 이다(ADR 0024 의 2026-10-23 이력). nginx 가 그 접두사 하나를 Next 로 넘긴다. headers 의 source
//   에는 basePath 가 저절로 붙는다(Next 16.3.6 설치본의 headers 문서).
// - 빌드의 입력은 사이트 파일이다(web-widget 티켓 04, tools/site-file.ts). 이 파일이 읽힐 때 AGENT_OS_SITE_FILE 이
//   가리키는 파일을 읽고, 읽지 못하면 진단을 던져 next 가 종료 코드 1로 멈춘다. 변수가 없으면 사이트 없음이다. build 는
//   tools/start.spawn.test.ts 가 보고, dev·start 는 손으로 봤다(둘 다 next 의 Ready 를 찍은 뒤 멈췄다, 일지 2026-10-24-05).
// - frame-ancestors 는 모든 사이트의 허용 출처를 합친 목록이고, 목록이 비면 'none' 이다. 그래서 사이트 파일이 없거나
//   허용 출처가 없으면 어떤 사이트도 iframe 페이지를 품지 못한다(ADR 0024 의 fail-closed). 헤더는 빌드 산출물
//   (routes-manifest.json)에 박혀, 운영 모드의 start 는 빌드 때의 값을 낸다(관리 화면의 next.config.ts 가 rewrites 에
//   대해 적은 것과 같다).
// - env 에 합친 허용 출처(공백으로 이은 글)와 가장 작은 요청 글자 수 상한(십진수 글)을 싣는다. 번들에서 읽는 법은
//   티켓 05 의 머리에 적었다. Next 는 env 의 값을 빌드 때 번들에 박는다(Next 16.3.6 설치본의 env 문서).
// - 글꼴 파일(public/fonts/, tools/fonts.ts)과 페이지 안 번들(public/element.js, tools/element.ts)은 시작 래퍼가 빌드
//   전에 짓는다. 둘 다 자격 증명 없이 받는 공개 파일이라 Access-Control-Allow-Origin 을 * 로 단다. 글꼴은 페이지 안
//   번들이 사이트 문서에서 FontFace 로 받고, 번들은 사이트가 script 에 crossorigin 을 붙이면 CORS 로 받는다. 그 헤더가
//   없으면 그때 번들이 실리지 않는다(web-widget 명세 "번들의 꼴").
// - rewrites 를 두지 않는다. API 는 nginx 가 파이썬에 바로 넘기므로, 처음 바깥에 열리는 Next 가 중계가 되지 않게
//   하기 위해서다(ADR 0024).
// - agentRules: false. next dev 가 에이전트를 감지하면 앱 폴더에 AGENTS.md 와 CLAUDE.md 를 만든다(ADR 0021).

import type { NextConfig } from "next";
import { buildInput, WIDGET_ORIGINS_ENV, WIDGET_REQUEST_CHARS_ENV } from "./tools/site-file.ts";

const input = buildInput(process.env);
const ancestors = input.allowedOrigins.length === 0 ? "'none'" : input.allowedOrigins.join(" ");

const config: NextConfig = {
  basePath: "/widget",
  agentRules: false,
  env: {
    [WIDGET_ORIGINS_ENV]: input.allowedOrigins.join(" "),
    // String(n) 은 10^21 부터 지수 꼴(1e+21)이라 BigInt 로 십진수 글을 짓는다.
    [WIDGET_REQUEST_CHARS_ENV]: BigInt(input.requestChars).toString(),
  },
  headers() {
    return Promise.resolve([
      {
        source: "/:path*",
        headers: [{ key: "Content-Security-Policy", value: `frame-ancestors ${ancestors}` }],
      },
      {
        source: "/fonts/:path*",
        headers: [{ key: "Access-Control-Allow-Origin", value: "*" }],
      },
      {
        source: "/element.js",
        headers: [{ key: "Access-Control-Allow-Origin", value: "*" }],
      },
    ]);
  },
};

export default config;
