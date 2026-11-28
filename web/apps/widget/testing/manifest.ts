// 응답 머리 목록(`.next/routes-manifest.json`)의 시험용 모양. 실제 빌드가 낸 목록을 줄인 것이다. 머리 규칙 넷과 머리 밖의 키들이
// 있다. 바꿀 자리를 찾는 규칙은 `tools/manifest.test.ts`, 그 코드가 서비스 시작의 차례 안에서 도는 것은 `tools/start.test.ts` 가
// 본다. 실제 빌드가 낸 목록의 모양은 위젯 e2e 의 준비가 지난다.

import { PLACEHOLDER } from "../tools/manifest.ts";

/** 빌드가 낸 목록. `frame-ancestors` 값은 기본으로 빌드가 굳히는 `'none'` 이다. */
export function builtManifest(frameAncestors: string = PLACEHOLDER): Record<string, unknown> {
  return {
    version: 3,
    pages404: true,
    basePath: "/widget",
    redirects: [{ source: "/:path+/", destination: "/:path+", statusCode: 308 }],
    headers: [
      {
        source: "/widget/:path*",
        headers: [{ key: "Content-Security-Policy", value: frameAncestors }],
        regex: "^/widget(?:/((?:[^/]+?)(?:/(?:[^/]+?))*))?(?:/)?$",
      },
      {
        source: "/widget/fonts/:path*",
        headers: [{ key: "Access-Control-Allow-Origin", value: "*" }],
        regex: "^/widget/fonts(?:/((?:[^/]+?)(?:/(?:[^/]+?))*))?(?:/)?$",
      },
      {
        source: "/widget/element.js",
        headers: [{ key: "Access-Control-Allow-Origin", value: "*" }],
        regex: "^/widget/element\\.js(?:/)?$",
      },
      {
        source: "/widget/runtime.json",
        headers: [{ key: "Access-Control-Allow-Origin", value: "*" }],
        regex: "^/widget/runtime\\.json(?:/)?$",
      },
    ],
    rewrites: { beforeFiles: [], afterFiles: [], fallback: [] },
  };
}
