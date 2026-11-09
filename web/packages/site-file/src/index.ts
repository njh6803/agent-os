// `@agent-os/site-file` 의 진입점. node 가 빌드 없이 읽는 꼴이라 상대 import 에 확장자를 붙인다. 확장자를 빼면 node 는
// `ERR_MODULE_NOT_FOUND` 로 멈추고, 이 패키지의 tsconfig(`nodenext`)는 `TS2835` 로 먼저 잡는다(pilot-portal 명세 "띄우기와
// 타입 검사").

export * from "./site-file.ts";
