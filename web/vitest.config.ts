import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    // 판정자 테스트가 web/ 아래에 임시 트리를 쓰고, tsconfig 검사의 저장소 상태 테스트가 web/ 를 훑는다.
    // 파일을 나란히 돌리면 쓰는 도중의 tsconfig 를 읽을 수 있어 파일은 차례로 돈다.
    fileParallelism: false,
    // 타입 기반 린트는 TypeScript 프로그램을 세우느라 첫 호출이 수 초 걸린다.
    testTimeout: 60_000,
    hookTimeout: 120_000,
  },
});
