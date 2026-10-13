// 스토리가 컴포넌트 모듈에서 함께 import 하는 상수. /design-sync 는 컴포넌트 모듈의 import 를 번들의 전역
// (window.AgentOsUi)으로 돌리는데, 이 상수들은 패키지 진입점이 내보내지 않아 미리보기에서 undefined 였다.
// cfg.extraEntries 가 이 모듈을 전역에 합친다. 같은 dist 파일을 가리켜 컴포넌트가 두 벌로 번들되지 않는다.
export { ICON_NAMES, ICON_SIZES } from "../web/packages/ui/dist/components/atoms/Icon.js";
export { STATUS_BADGE_STATUSES } from "../web/packages/ui/dist/components/atoms/StatusBadge.js";
