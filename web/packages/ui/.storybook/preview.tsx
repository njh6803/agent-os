// 미리보기 설정. Storybook 은 자기 문서에 선언하는 쪽이라 디자인 토큰 CSS 와 글꼴 CSS 를 둘 다 전역으로 싣는다.
// globals·데코레이터·afterEach 의 판정은 src/storybook/preview.tsx 의 본체다.
import "../src/styles/theme.css";
import "../src/styles/fonts.css";
import css from "../src/styles/theme.css?inline";
import { storyPreview } from "../src/storybook/preview";

// 기본 내보내기는 객체 리터럴이어야 한다. Storybook 이 미리보기를 정적으로도 읽어, 함수 호출이면 "CSF Parsing error:
// Expected 'ObjectExpression'" 경고를 낸다(10.6.1 의 스토리 테스트에서 손으로 봤다).
export default { ...storyPreview(css) };
