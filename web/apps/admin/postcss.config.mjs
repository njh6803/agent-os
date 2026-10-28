// Next 가 관리 화면의 CSS(styles/admin.css)를 Tailwind 로 짓는 길. 관리 화면의 Storybook 은 이 파일을 읽지 않고
// @tailwindcss/vite 를 단다(.storybook/main.ts).
export default {
  plugins: { "@tailwindcss/postcss": {} },
};
