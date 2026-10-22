/**
 * 판정자 임시 트리. 판정자 테스트(eslint.config.test.ts)가 위반 사례를 web/ 아래 `judge-<여섯 글자>` 트리에 쓰고
 * `afterAll` 에서 지운다. 검사 러너가 그 도중에 멈추면(인계로 앞 세션이 끝날 때) `afterAll` 이 돌지 않아 트리가
 * 생성 클라이언트로 가는 junction 과 함께 남았다(대기열 379, 일지 2026-10-20-01·2026-10-20-16·2026-10-22-11). 남은
 * 트리의 위반 사례는 다음 verify 의 린트를, 한 줄로 쓴 프로젝트 tsconfig.json 은 Prettier 를 빨갛게 한다. 그래서
 * verify 의 첫 단계와 판정자 테스트의 `beforeAll` 이 새 트리를 만들기 전에 남은 트리를 지운다. 만드는 이름과 지우는
 * 이름의 원천이 이 모듈 하나다.
 *
 * 지우기는 Node `rmSync` 다. 트리 안의 junction(Linux 에서는 심볼릭 링크)은 링크 자체만 지우고 대상 패키지로
 * 내려가지 않는다(judge-trees.test.ts 가 이 PC 의 Windows 와 CI 의 Linux 에서 본다). 손으로 지울 때도 링크를
 * 따라가지 않는 것을 시험이 보는 이 명령을 쓴다. 윈도우에서 다른 프로세스가 파일을 잠깐 잡아 나는 `EPERM` 은
 * `maxRetries` 로 견딘다.
 *
 * 지우는 것은 web/ 바로 아래에서 이름이 `judge-` 와 영숫자 여섯인 디렉터리뿐이다(`mkdtempSync` 가 붙이는 꼴).
 * 그 이름의 링크와 파일, 꼴이 다른 이름은 남긴다.
 *
 * 못 보는 것: 트리가 앞 실행의 것인지 지금 도는 다른 실행의 것인지 가르지 않는다. 같은 체크아웃에서 verify 둘이
 * 함께 돌면 한쪽의 청소가 다른 쪽의 판정자 테스트가 쓰는 도중의 트리를 지울 수 있다(재지 않았다). 그렇게 겹친
 * 경우는 이 청소 전에도 한쪽의 Prettier 가 다른 쪽의 트리를 읽어 빨갰다(일지 2026-10-07-18). 재시도 뒤에도 지우지
 * 못하면 던지고 그 단계가 빨갛다.
 *
 * 사용: node tools/judge-trees.ts [루트]. 루트를 주지 않으면 web/ 다. 지운 트리를 한 줄씩 쓴다.
 */

import { mkdtempSync, readdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";

const PREFIX = "judge-";
// `mkdtempSync` 가 접두 뒤에 붙이는 여섯 글자(libuv 의 영숫자).
const NAME = /^judge-[A-Za-z0-9]{6}$/;

/** `root` 아래에 새 판정자 트리를 만들고 그 경로를 돌려준다. */
export function makeJudgeTree(root: string): string {
  return mkdtempSync(join(root, PREFIX));
}

/** `root` 바로 아래의 남은 판정자 트리를 지우고 지운 경로를 돌려준다. */
export function removeLeftoverJudgeTrees(root: string): string[] {
  const removed: string[] = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    if (!entry.isDirectory() || !NAME.test(entry.name)) {
      continue;
    }
    const tree = join(root, entry.name);
    rmSync(tree, { recursive: true, force: true, maxRetries: 5 });
    removed.push(tree);
  }
  return removed;
}

if (import.meta.main) {
  const root = process.argv[2] ?? dirname(import.meta.dirname);
  for (const tree of removeLeftoverJudgeTrees(root)) {
    console.log(`남은 판정자 트리를 지웠다: ${tree}`);
  }
}
