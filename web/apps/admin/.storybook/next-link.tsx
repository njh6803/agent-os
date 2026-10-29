// `next/link` 의 대역. 관리 화면의 Storybook 이 viteFinal 에서 `next/link` 를 이 파일로 별칭한다(main.ts). 화면 사이의
// 이동은 Storybook 의 몫이 아니라 평범한 `<a href>` 를 그린다. 관리 화면의 `Link` 는 `href` 와 글자만 넘긴다.
import type { ComponentProps } from "react";

export default function Link(props: ComponentProps<"a"> & { readonly href: string }) {
  return <a {...props} />;
}
