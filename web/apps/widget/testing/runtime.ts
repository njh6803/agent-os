// 위젯 시험이 값 파일(lib/runtime.ts)에 두는 값. 허용 출처는 사이트의 흉내 하나이고 글자 수 상한은 서버의 기본값 20,000
// 이다. 사례마다 받은 상태로 시작하도록 testing/setup.ts 가 이 값을 미리 둔다. 값 파일을 실제로 받는 길(받기 전, 실패, 404,
// 10초)은 components/pages/WidgetSettings.test.tsx 가 응답을 흉내 내어 따로 본다.

import { seedRuntimeValues, type RuntimeValues } from "../lib/runtime";
import { SITE_ORIGIN } from "./site";

export const DEFAULT_VALUES: RuntimeValues = {
  allowedOrigins: [SITE_ORIGIN],
  requestChars: 20_000,
};

/** 기준 주소 아래 값 파일을 받은 상태로 둔다. 값을 주지 않으면 기본값이다. */
export function seedValues(baseUrl: URL, values: RuntimeValues = DEFAULT_VALUES): void {
  seedRuntimeValues(baseUrl, values);
}
