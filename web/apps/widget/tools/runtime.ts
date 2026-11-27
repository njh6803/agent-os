/**
 * 값 파일(`/widget/runtime.json`)을 쓰는 코드. 위젯이 뜰 때 시작 래퍼(`start.ts`)가 사이트 파일을 읽어 위젯이 받아 갈 두 값을
 * 이 파일로 낸다(widget-runtime-values 명세 "값 파일", ADR 0064). 브라우저 쪽이 받는 길은 `lib/runtime.ts` 다.
 *
 * - 두 값은 지금 빌드가 쓰는 `@agent-os/site-file` 의 같은 함수(`buildInput`)가 낸다. 모든 사이트의 허용 출처를 합친 목록과
 *   가장 작은 요청 글자 수 상한이다. 읽지 못하면 그 함수가 진단을 든 오류를 던진다.
 * - 키는 `allowedOrigins` 와 `requestChars` 둘뿐이다. 누구나 읽는 파일이라 사이트 파일의 다른 값(공개 키, 발급자, 열
 *   에이전트)은 싣지 않는다.
 * - 상한이 `Number` 로 바뀔 때 무한대가 되면(약 1.8×10^308 이상) 가장 큰 유한한 수로 쓴다. 무한대를 JSON 으로 쓰면 `null`
 *   이 되어, 읽는 쪽이 다시 시도로도 풀리지 않는 알림에 갇힌다.
 * - 그 자리를 열어 바로 쓴다. 임시 파일에 쓴 뒤 이름을 바꿔 덮지 않는다. 이미지가 그 자리를 쓰는 폴더 안을 가리키는 링크로
 *   바꿔도(widget-runtime-values 티켓 03) 이 코드를 다시 고치지 않게 하려는 것이다. 이름 바꾸기는 링크를 따라가지 않아 읽기 전용
 *   루트에서 실패한다(리눅스의 동작으로 아는 것이고 재지 않았다, 명세 "위젯 이미지").
 */

import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { buildInput } from "@agent-os/site-file";

/** 앱 폴더 안 Next 의 공개 파일 폴더에 놓이는 값 파일의 이름. Next 가 `/widget/runtime.json` 으로 낸다. */
export const RUNTIME_FILE = "runtime.json";

/** 값 파일의 내용. */
export interface RuntimeValuesFile {
  readonly allowedOrigins: readonly string[];
  readonly requestChars: number;
}

/** 환경 변수가 가리키는 사이트 파일에서 값 파일의 내용을 끌어낸다. 읽지 못하면 진단을 든 오류를 던진다. */
export function runtimeValues(
  env: Readonly<Record<string, string | undefined>>,
): RuntimeValuesFile {
  const { allowedOrigins, requestChars } = buildInput(env);
  return {
    allowedOrigins,
    requestChars: Number.isFinite(requestChars) ? requestChars : Number.MAX_VALUE,
  };
}

/** 운영자가 로그에서 고친 값이 들어갔는지 보는 한 줄. 합친 허용 출처와 상한만 싣는다. */
export function describeValues({ allowedOrigins, requestChars }: RuntimeValuesFile): string {
  const origins = allowedOrigins.length === 0 ? "없음" : allowedOrigins.join(" ");
  return `위젯이 받은 값: 허용 출처 ${origins}, 요청 글자 수 상한 ${String(requestChars)}`;
}

/**
 * 값 파일을 `appDir/public/runtime.json` 에 쓰고 받은 값을 `log` 로 한 줄 알린다. 사이트 파일을 읽지 못하면 아무것도 쓰지
 * 않고 오류를 던진다.
 */
export function writeRuntimeValues(
  env: Readonly<Record<string, string | undefined>>,
  appDir: string,
  log: (line: string) => void,
): RuntimeValuesFile {
  const values = runtimeValues(env);
  const publicDir = join(appDir, "public");
  mkdirSync(publicDir, { recursive: true });
  writeFileSync(join(publicDir, RUNTIME_FILE), JSON.stringify(values));
  log(describeValues(values));
  return values;
}
