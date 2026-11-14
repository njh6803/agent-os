import { join } from "node:path";

/**
 * 디자인 시스템 아티팩트의 페이지가 싣는 React·ReactDOM 18.3.1 을 시험이 읽을 자리. 이 패키지는 그 두 판을 고정해 들고, 시험이 읽을 값(자리와 판 문자열)만 내보낸다.
 * 디자인 시스템 패키지(React 19)나 Storybook 이 든 자리에 별칭으로 두면 pnpm 이 `react-dom` 의 피어를 그쪽 React 와
 * 짝지어 버려, 18.3.1 의 `react-dom` 이 19 의 `react` 와 엮인다(그래서 따로 둔 패키지다).
 */
export const REACT_18_MODULES = join(import.meta.dirname, "..", "node_modules");

/** 이 패키지가 고정한 판. 시험이 설치된 판과 맞댄다. */
export const REACT_18_VERSION = "18.3.1";
