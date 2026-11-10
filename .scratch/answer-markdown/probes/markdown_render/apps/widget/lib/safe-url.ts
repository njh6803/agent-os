// 링크의 주소 정책. 두 후보의 컴포넌트가 이 함수 하나를 쓴다(크기 비교에서 같은 몫이 되게).
//
// - `http:` 와 `https:` 만 지난다. 판정은 브라우저의 URL 파서(`new URL`)가 읽은 스킴으로 한다. 그래서 대소문자, 앞의
//   공백, 탭·줄바꿈을 끼운 스킴(`java\tscript:`)도 브라우저가 읽는 그대로 판정된다.
// - 상대 주소(`/path`, `#frag`, `//host`, `www.example`)는 지나지 못한다. 기준 주소를 주지 않아 `new URL` 이 던진다.
//   페이지 안 방식에서 상대 주소는 사이트 페이지의 주소에 붙는다.
// - 지나면 파서가 정규화한 글(`href`)을 돌려준다. 판정한 글과 내보내는 글이 같다.

/** `http:`·`https:` 주소면 정규화한 주소이고, 아니면 null 이다. */
export function httpUrl(value: string): string | null {
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    return null;
  }
  return url.protocol === "http:" || url.protocol === "https:" ? url.href : null;
}
