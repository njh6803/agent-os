// (2) iframe 페이지를 서빙하는 Next 앱의 설정. 관리 화면처럼 같은 출처의 /api/* 를 채널(측정에서는 shadow.mjs 의 가짜
// 서버)로 넘긴다. 그래서 iframe 안의 요청은 같은 출처라 CORS 를 타지 않는다. compress: false 는 관리 화면과 같은
// 이유다(기본 압축이 SSE 를 끝에 몬다, `.scratch/web-admin/probes/next_measure.mjs`). rewrites 는 빌드에 박힌다.

import type { NextConfig } from "next";

const upstream = new URL(process.env.WIDGET_PROBE_UPSTREAM ?? "http://127.0.0.1:8790").origin;

const config: NextConfig = {
  compress: false,
  agentRules: false,
  rewrites() {
    return Promise.resolve([{ source: "/api/:path*", destination: `${upstream}/:path*` }]);
  },
};

export default config;
