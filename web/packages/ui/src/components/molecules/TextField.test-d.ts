// 글 입력의 `type` 의 타입 테스트. tsc 가 판정한다. 한 줄 변형만 `type` 으로 text 와 password 를 받고, 여러 줄 변형과
// 그 밖의 값은 컴파일이 막는다는 것을 고정한다(admin-style 명세 "패키지에 더하는 것").

import type { TextFieldProps } from "./TextField";

export const 한_줄_칸은_type_없이_쓴다: TextFieldProps = { label: "플러그인 이름" };
export const 한_줄_칸은_type_으로_text_를_받는다: TextFieldProps = {
  label: "플러그인 이름",
  type: "text",
};
export const 한_줄_칸은_type_으로_password_를_받는다: TextFieldProps = {
  label: "관리 토큰",
  type: "password",
};

// 바로 쓴 객체의 오류는 객체 안의 그 속성 줄에서 난다. 지시문은 그 줄 바로 위에 둔다.
export const 여러_줄_칸에_type_을_주면_컴파일이_실패한다: TextFieldProps = {
  variant: "multi",
  label: "거부 사유",
  // @ts-expect-error: 여러 줄 변형은 type 을 받지 않는다
  type: "password",
};

// 바로 쓴 객체는 초과 속성 검사가 여러 줄 변형의 `type?: never` 없이도 막는다. 변수에 담아 넘긴 객체는 그 검사를
// 거치지 않아 `type?: never` 만이 막는다.
const 가린_여러_줄 = { variant: "multi", label: "거부 사유", type: "password" } as const;
// @ts-expect-error: 변수로 넘겨도 여러 줄 변형은 type 을 받지 않는다
export const 여러_줄_칸에_type_이_든_변수를_넘기면_컴파일이_실패한다: TextFieldProps = 가린_여러_줄;

export const 한_줄_칸에_type_으로_number_를_주면_컴파일이_실패한다: TextFieldProps = {
  label: "개수",
  // @ts-expect-error: 한 줄 변형의 type 은 text 와 password 뿐이다
  type: "number",
};
