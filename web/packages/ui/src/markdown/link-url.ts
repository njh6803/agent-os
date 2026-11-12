// 마크다운 부품의 링크 주소 정책(ADR 0053 결정 "링크", 명세 "링크"). 화면을 그리지 않는 순수 함수라 컴포넌트 폴더 밖에 두고
// 패키지 밖으로 내보내지 않는다.
//
// - 브라우저와 Node 가 함께 가진 URL 파서로 기준 주소 없이 푼다. 풀리지 않는 것(상대 주소, `#top`, 스킴 없는 주소, 빈 주소)은
//   링크가 아니다.
// - 스킴이 `http:` 나 `https:` 가 아니면 링크가 아니다(`javascript:`, `data:`, `mailto:` 등).
// - 사용자 이름이나 비밀번호가 비어 있지 않으면 링크가 아니다(`https://믿는곳@다른곳/`). `https://@host/` 는 파서가 사용자
//   정보 없는 주소로 읽으므로 링크가 되고, 낸 주소에는 `@` 가 없다.
// - 링크이면 원문이 아니라 파서가 정규화한 주소를 돌려준다. 판정한 글자와 브라우저가 여는 글자가 같아야 하기 때문이다.

/** 링크로 그려도 되는 주소이면 파서가 정규화한 주소이고, 아니면 null 이다. */
export function linkHref(value: string): string | null {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    return null;
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") return null;
  if (url.username !== "" || url.password !== "") return null;
  return url.href;
}
