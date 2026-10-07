// 컴포넌트 props 의 공통 모양(design-system 티켓 01 이 정하고 03·04 가 따른다).
//
// - 디자인 파일 05절의 props 표가 계약의 최소다. 표의 이름은 표의 타입으로 받는다. 그 이름이 요소의 기본 속성과
//   겹치면(버튼의 `onClick: () => void`, `children: string`, 알림의 `title`, 글 입력·스위치의 `onChange(value)`) 기본
//   속성의 타입을 지우고 표의 타입이 이긴다.
// - 표에 없는 기본 속성(`aria-*`, `id`, `name`, `data-*`, `ref` 등)은 `NativeProps<요소, 표의 이름 | 컴포넌트가 정하는
//   이름>` 으로 받아 그 요소에 그대로 넘긴다. `className` 과 `style` 은 받지 않는다(ADR 0026: 소비자가 클래스로 모양을
//   덮는 길을 두지 않는다).
// - 컴포넌트가 스스로 정하는 속성(아이콘 버튼의 `aria-label`·`title`, 불러오는 중의 `aria-busy`·`aria-disabled`)도 빼서
//   쓰는 쪽이 덮지 못하게 한다.
// - 여러 요소를 엮는 컴포넌트(글 입력, 스위치)는 나머지 속성을 바깥 `<label>` 이 아니라 입력 요소(`<input>`,
//   `<textarea>`)에 넘긴다. `name`, `id`, `autoComplete`, `maxLength`, `aria-*` 가 모두 입력 요소의 것이기 때문이다.
import type { ComponentProps, JSX } from "react";

export type NativeProps<Tag extends keyof JSX.IntrinsicElements, Own extends PropertyKey> = Omit<
  ComponentProps<Tag>,
  "className" | "style" | Own
>;
