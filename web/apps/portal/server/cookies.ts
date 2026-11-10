// `Cookie` 요청 헤더 읽기. 실린 차례를 지켜 모두 돌려준다. 같은 이름이 여럿일 때 첫 것을 쓴다는 규칙(명세 "익명 식별자
// 쿠키")은 값을 고르는 쪽의 몫이다.

export interface Cookie {
  readonly name: string;
  readonly value: string;
}

/** 헤더의 쿠키들. 헤더가 없거나, 등호가 없거나, 이름이 빈 조각은 버린다. */
export function parseCookieHeader(header: string | undefined): readonly Cookie[] {
  if (header === undefined) {
    return [];
  }
  return header.split(";").flatMap((piece) => {
    const at = piece.indexOf("=");
    const name = at < 0 ? "" : piece.slice(0, at).trim();
    return name === "" ? [] : [{ name, value: piece.slice(at + 1).trim() }];
  });
}
