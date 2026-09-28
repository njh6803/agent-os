// web-admin 프로브의 최소 Next 앱 설정. 값은 환경 변수로 바꾼다(next_measure.mjs가 넘긴다).
//   PROBE_UPSTREAM  상류 주소. 기본 http://127.0.0.1:8765 (next_sse_upstream.mjs)
//   PROBE_COMPRESS  "0"이면 compress: false. 없으면 compress를 적지 않는다(Next 기본값)
//   PROBE_DIST      distDir. compress 켬·끔 빌드를 따로 두려고 쓴다
const upstream = process.env.PROBE_UPSTREAM ?? "http://127.0.0.1:8765";

/** @type {import('next').NextConfig} */
const config = {
  ...(process.env.PROBE_COMPRESS === "0" ? { compress: false } : {}),
  ...(process.env.PROBE_DIST ? { distDir: process.env.PROBE_DIST } : {}),
  async rewrites() {
    // (a) 길: /rw/* 를 상류로 넘긴다
    return [{ source: "/rw/:path*", destination: `${upstream}/:path*` }];
  },
};

export default config;
