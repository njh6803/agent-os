// 위젯의 미리보기 설정. iframe 페이지처럼 위젯의 CSS 와 글꼴 CSS 를 둘 다 전역으로 싣는다. globals·데코레이터·
// afterEach 의 판정은 디자인 시스템 패키지의 본체(`@agent-os/ui/storybook`)다. shadow 틀에는 위젯의 CSS 를 넘긴다.
// 디자인 토큰 CSS 만 넘기면 shadow 틀 안에서 위젯의 클래스가 규칙을 잃는다(본체의 storyPreview 주석).
//
// 밀도의 처음 값은 보통이다. 위젯은 문서 뿌리에 data-density="regular" 를 단다(web-widget 명세 "테마·모드·밀도·글꼴").
import "../styles/widget.css";
import "@agent-os/ui/fonts.css";
import { storyPreview } from "@agent-os/ui/storybook";
import css from "../styles/widget.css?inline";

const base = storyPreview(css);

// 기본 내보내기는 객체 리터럴이어야 한다(패키지의 .storybook/preview.tsx 주석).
export default { ...base, initialGlobals: { ...base.initialGlobals, density: "regular" } };
