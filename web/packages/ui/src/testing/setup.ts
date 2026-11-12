// 디자인 시스템 패키지의 부품 시험(vitest 프로젝트 `ui-pages`, jsdom)의 격리. 시험마다 그린 것을 걷는다. Testing Library 는
// 전역 `afterEach` 가 있을 때만 스스로 걷는데 이 저장소의 Vitest 는 전역을 켜지 않으므로 직접 건다(선례: 위젯 앱의
// `apps/widget/testing/setup.ts`). 진입점 `./testing`(index.ts)과 달리 패키지 밖으로 내보내지 않는다.
import { cleanup } from "@testing-library/react";
import { afterEach } from "vitest";

afterEach(() => {
  cleanup();
});
