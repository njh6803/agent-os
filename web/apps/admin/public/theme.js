// 관리 화면의 테마를 첫 그림 전에 문서 뿌리 <html> 의 data-theme 에 단다(admin-style 명세 "그리기 전 스크립트"). 뿌리
// 레이아웃(app/layout.tsx)의 <head> 가 막는 <script src> 로 싣는다. 하이드레이션 뒤의 테마는 stores/theme.ts 가 든다.
//
// 이 파일은 브라우저가 그대로 받는 평범한 JS 라 @agent-os/ui 의 THEMES 와 저장 키(stores/theme.ts 의
// THEME_STORAGE_KEY)를 import 하지 못해 둘을 여기 따로 적는다. THEMES 에 테마를 더하거나 저장 키를 바꾸고 이 파일을
// 고치지 않으면 stores/theme.prepaint.test.ts 가 빨갛다. THEMES 에서 테마를 빼고 이 목록에 남긴 것은 그 시험이 잡지
// 않는다. 타입 표기를 쓰지 않는다. public/ 의 .js 는 JS 파서가 읽어 타입 표기가 파싱 오류다.
//
// 저장 값이 목록에 없거나 저장소를 읽지 못하면(저장소를 막은 브라우저) 아무것도 달지 않는다. 속성이 없는 문서는 기본
// 테마로 그린다.
try {
  const theme = localStorage.getItem("agent-os-admin-theme");
  if (theme !== null && ["guncheong", "nokcheong", "jacho", "jjokbit"].includes(theme)) {
    document.documentElement.dataset.theme = theme;
  }
} catch {
  // 기본 테마로 그린다.
}
