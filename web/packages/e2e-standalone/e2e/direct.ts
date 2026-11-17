// 시험이 최종 사용자 경로를 직접 부를 때 쓰는 서명 토큰. 위젯 미리보기 페이지가 쓰는 키 쌍을 준비가 배포 폴더에 써 두었으므로
// (`portal/keys/portal.pem`) 그 개인 키로 서명한다. 사이트 파일의 `direct` 사이트가 같은 공개 키와 `ISSUER` 를 든다.

import { createPrivateKey, createPublicKey } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { signToken } from "@agent-os/e2e-stack";

export function signedDirectToken(dir: string): string {
  const privateKey = createPrivateKey(readFileSync(join(dir, "portal", "keys", "portal.pem")));
  const publicPem = createPublicKey(privateKey).export({ type: "spki", format: "pem" }).toString();
  return signToken({ privateKey, publicPem });
}
