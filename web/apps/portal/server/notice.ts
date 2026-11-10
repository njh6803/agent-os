// 고지 전문 짓기(pilot-portal 명세 "질문 페이지 설정"). 서버가 시작 때 사이트마다 한 번 짓는다. 사이트가 글을 적었으면 그
// 글이 앞이고, 적지 않았으면 기본 글 세 문단이다. 쿠키 문장은 둘 다 전문의 끝에 붙어, 사이트가 쿠키를 말하지 않아도
// 방문자는 읽는다. 짧은 고지(질문 페이지의 한 줄)는 사이트가 바꾸지 못하는 상수라 페이지를 짓는 쪽에 둔다.

const FIRST_PARAGRAPH =
  "이 페이지에서 보낸 질문과 받은 출력은 기록되고, 출력을 만들기 위해 모델 API로 보내집니다.";
const LAST_PARAGRAPH = "이름, 연락처, 주민등록번호 같은 개인정보를 질문에 넣지 마세요.";

/**
 * 쿠키 문장. 일수는 인자로 받는다. 시험이 쿠키 수명 상수와 다른 값을 넘겨, 일수가 글이 아니라 값에서 그려지는 것을 본다.
 */
function cookieSentence(cookieDays: number): string {
  return `이 브라우저를 알아보기 위해 익명 식별자를 쿠키로 둡니다. 쿠키는 마지막으로 질문한 뒤 ${String(cookieDays)}일 동안 남습니다.`;
}

/** 사이트의 고지 전문. `custom` 은 사이트가 적은 글이고 적지 않았으면 undefined 다. */
export function noticeText(custom: string | undefined, cookieDays: number): string {
  const paragraphs =
    custom === undefined
      ? [FIRST_PARAGRAPH, cookieSentence(cookieDays), LAST_PARAGRAPH]
      : [custom, cookieSentence(cookieDays)];
  return paragraphs.join("\n\n");
}
