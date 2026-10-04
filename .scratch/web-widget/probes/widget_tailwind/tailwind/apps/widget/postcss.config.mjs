// Next(iframe 페이지)가 읽는 PostCSS 설정. Tailwind 의 설정은 CSS 원본(styles/widget.css)에 있고 여기는 플러그인만
// 단다. Vite 도 같은 폴더의 이 파일을 찾아 읽는다(vite.config.ts 의 견줌 모드가 그 효과를 잰다).
export default {
  plugins: { "@tailwindcss/postcss": {} },
};
