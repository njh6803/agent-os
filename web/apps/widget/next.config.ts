// 위젯의 Next 설정. iframe 페이지(/widget)와 위젯이 내주는 공개 파일(/widget/fonts/)을 낸다(ADR 0024).
//
// - basePath 는 /widget 이다(ADR 0024 의 2026-10-23 이력). nginx 가 그 접두사 하나를 Next 로 넘긴다. headers 의 source
//   에는 basePath 가 저절로 붙는다(Next 16.3.6 설치본의 headers 문서).
// - 설정은 단계(phase)를 받는 함수다. 사이트 파일(`@agent-os/site-file`)을 읽는 것은 개발 서버 단계(`next dev`)뿐이다. 그 단계는
//   이 파일이 읽힐 때 AGENT_OS_SITE_FILE 이 가리키는 파일을 읽어 응답 머리를 내고, 읽지 못하면 진단을 던져 next 가 종료 코드
//   1로 멈춘다. 변수가 없으면 사이트 없음이다. 빌드와 서비스 시작 단계는 사이트 파일을 읽지 않는다(widget-runtime-values
//   티켓 02, ADR 0064).
// - frame-ancestors 는 모든 사이트의 허용 출처를 합친 목록이고, 목록이 비면 'none' 이다. 그래서 사이트 파일이 없거나
//   허용 출처가 없으면 어떤 사이트도 iframe 페이지를 품지 못한다(ADR 0024 의 fail-closed). 빌드는 사이트 파일을 읽지 않고
//   언제나 'none' 으로 굳힌다. 그 값이 빌드 산출물(routes-manifest.json)에 박히고, 운영 모드의 시작 래퍼가 뜰 때마다 그
//   자리를 사이트 파일의 허용 출처로 바꾼 사본을 쓴다(tools/manifest.ts). 그래서 한 번 지은 산출물을 사이트 파일만 바꿔 가며
//   다시 띄울 수 있다. 개발 서버는 이 원본과 사본(`.next/routes-manifest*.json`)을 쓰지 않아 설정이 뜰 때 바로 읽는다.
// - 번들은 사이트 파일의 값을 싣지 않는다. 합친 허용 출처와 가장 작은 요청 글자 수 상한은 시작 래퍼가 뜰 때 값 파일
//   (public/runtime.json, tools/runtime.ts)로 쓰고, 브라우저 쪽이 열릴 때 `/widget/runtime.json` 으로 받는다
//   (widget-runtime-values 티켓 01). 그래서 `env` 로 싣지 않는다.
// - 글꼴 파일(public/fonts/, `@agent-os/ui/fonts`)과 페이지 안 번들(public/element.js, tools/element.ts)은 시작 래퍼가 빌드
//   전에 짓는다. 값 파일(public/runtime.json)은 시작 래퍼가 서기 전에 쓴다. 셋 다 자격 증명 없이 받는 공개 파일이라
//   Access-Control-Allow-Origin 을 * 로 단다. 글꼴은 페이지 안 번들이 사이트 문서에서 FontFace 로 받고, 번들은 사이트가
//   script 에 crossorigin 을 붙이면 CORS 로 받는다. 그 헤더가 없으면 그때 번들이 실리지 않는다(web-widget 명세 "번들의
//   꼴"). 값 파일은 사이트 페이지 안에서 도는 번들이 받으므로 같은 헤더가 필요하다. 캐시 머리는 달지 않는다.
// - rewrites 를 두지 않는다. API 는 nginx 가 파이썬에 바로 넘기므로, 처음 바깥에 열리는 Next 가 중계가 되지 않게
//   하기 위해서다(ADR 0024).
// - agentRules: false. next dev 가 에이전트를 감지하면 앱 폴더에 AGENTS.md 와 CLAUDE.md 를 만든다(ADR 0021).

import { widgetValues } from "@agent-os/site-file";
import type { NextConfig } from "next";
import { PHASE_DEVELOPMENT_SERVER } from "next/constants";

/** `frame-ancestors` 의 값. 목록이 비면 어떤 사이트도 품지 못한다. */
function ancestorsOf(allowedOrigins: readonly string[]): string {
  return allowedOrigins.length === 0 ? "'none'" : allowedOrigins.join(" ");
}

export default function config(phase: string): NextConfig {
  const ancestors =
    phase === PHASE_DEVELOPMENT_SERVER
      ? ancestorsOf(widgetValues(process.env).allowedOrigins)
      : ancestorsOf([]);

  return {
    basePath: "/widget",
    agentRules: false,
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
        {
          source: "/runtime.json",
          headers: [{ key: "Access-Control-Allow-Origin", value: "*" }],
        },
      ]);
    },
  };
}
