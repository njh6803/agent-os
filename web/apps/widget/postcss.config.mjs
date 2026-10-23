// Next 가 위젯의 CSS(styles/widget.css)를 Tailwind 로 짓는 길. 위젯의 Storybook 은 이 파일을 읽지 않고
// @tailwindcss/vite 를 단다(.storybook/main.ts).
export default {
  plugins: { "@tailwindcss/postcss": {} },
};
