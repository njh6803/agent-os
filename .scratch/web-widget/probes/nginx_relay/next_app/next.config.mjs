// nginx 중계 측정의 최소 위젯 앱. 관리 화면(web/apps/admin/next.config.ts)의 중계를 본뜬다.
//   - compress: false. 관리 화면과 같다(ADR 0019, 기본 압축은 SSE 를 끝에 몰았다)
//   - rewrites: 같은 출처의 /chat/* 를 파이썬의 /chat/* 로 넘긴다. basePath 밖의 경로라 basePath: false
//   - basePath: /widget. 페이지와 정적 자산(/_next/...)이 모두 /widget/ 아래에 서서 nginx 허용 목록이 두 접두사로 끝난다
// 상류는 PROBE_UPSTREAM(기본 http://127.0.0.1:18700, measure.py 의 sse_app.py 포트). rewrites 는 빌드 때 박힌다.
const upstream = process.env.PROBE_UPSTREAM ?? "http://127.0.0.1:18700";

/** @type {import('next').NextConfig} */
const config = {
  basePath: "/widget",
  compress: false,
  agentRules: false,
  async rewrites() {
    return [{ source: "/chat/:path*", destination: `${upstream}/chat/:path*`, basePath: false }];
  },
};

export default config;
