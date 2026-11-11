// 시제품의 링크 주소 정책(ADR 0053 결정 "링크"). 기존 `safe-url.ts` 의 `httpUrl` 에 사용자 정보 규칙을 더한 것이다.
//
// - `http:` 와 `https:` 만 지난다. 판정은 브라우저의 URL 파서(`new URL`)가 읽은 값으로 한다.
// - 주소에 사용자 정보가 들면(`https://정상사이트@가짜사이트/`, `https://user:pw@host/`) 지나지 못한다. 파서가 읽은
//   `username` 이나 `password` 가 비어 있지 않은 주소다. `@` 앞이 빈 주소(`https://@host/`)는 사용자 정보가 없는 것으로
//   읽혀 지나고, 내보내는 주소(`href`)에서 `@` 가 빠진다.
// - 상대 주소는 지나지 못한다(기준 주소를 주지 않아 `new URL` 이 던진다).
// - 지나면 파서가 정규화한 글(`href`)을 돌려준다. 판정한 글과 내보내는 글이 같다.

/** 링크로 그려도 되는 주소면 정규화한 주소이고, 아니면 null 이다. */
export function linkUrl(value: string): string | null {
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
