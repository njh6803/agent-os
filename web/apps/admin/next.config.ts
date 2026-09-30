// 관리 화면의 Next 설정. Next 는 같은 출처의 /api/* 를 파이썬 서버(상류)로 넘기는 중계일 뿐이다(ADR 0019).
//
// - 상류는 AGENT_OS_UPSTREAM(기본 http://127.0.0.1:8000, serve 의 기본 주소)이고 호스트는 127.0.0.1 이어야 한다. 판정은
//   이 파일을 읽을 때다. dev·build·start 가 모두 이 파일을 읽으므로 한 자리에서 막힌다(ADR 0011 의 2026-09-28·2026-09-30
//   이력, 판정은 tools/loopback.ts).
// - rewrites 는 빌드 산출물(routes-manifest.json)에 박힌다(.scratch/web-admin/probes/admin_relay.mjs). start 는 이 파일을 다시 읽어 판정하지만 실제로 넘기는 곳은
//   빌드 때의 값이다. 상류를 바꾸면 다시 빌드한다. 빌드 때 판정을 지난 값만 박힌다.
// - compress: false. 기본 압축은 SSE 를 끝에 몰았고, 끄면 생기는 대로 흘렀다(.scratch/web-admin/probes/next_measure.mjs).
//   회귀를 잡는 것은 결정 화면의 e2e(티켓 08)다. 그 전에는 SSE 를 중계로 받는 화면이 없어 빠져도 빨개지지 않는다.
// - agentRules: false. next dev 가 에이전트를 감지하면 앱 폴더에 AGENTS.md 와 CLAUDE.md 를 만든다(ADR 0021).
//   만들어지면 tools/check_instructions.py 의 중첩 지침 파일 검사가 빨갛다. 블록의 요지는 .claude/rules/web-admin.md 에 있다.

import type { NextConfig } from "next";
import { DEFAULT_UPSTREAM, UPSTREAM_ENV, upstreamProblem } from "./tools/loopback.ts";

const given = process.env[UPSTREAM_ENV];
const upstream = given === undefined || given === "" ? DEFAULT_UPSTREAM : given;
const problem = upstreamProblem(upstream);
if (problem !== null) {
  throw new Error(problem);
}
// 판정을 지난 값은 출처 하나라 끝의 빗금만 떼면 된다.
const origin = new URL(upstream).origin;

const config: NextConfig = {
  compress: false,
  agentRules: false,
  rewrites() {
    return Promise.resolve([{ source: "/api/:path*", destination: `${origin}/:path*` }]);
  },
};

export default config;
