// 위젯 관리 서버의 생성 클라이언트 패키지의 입구(ADR 0064). web 코드가 위젯 관리 서버를 부를 때 지나는 자리다.

export type { components, paths } from "./generated/openapi";
export { createPublicClient, type PublicClient, type PublicPaths } from "./clients";
