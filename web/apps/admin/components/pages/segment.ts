/**
 * 주소의 조각을 푼다. Next 16.3.6 은 동적 조각을 퍼센트 인코딩된 채로 넘긴다(e2e 의 패턴 밖 표지 흐름이 쟀다). 요청
 * 함수가 다시 인코딩하므로 풀지 않으면 두 번 인코딩된다. 풀 수 없는 조각이면 null 이다. 주소가 있는 화면(플러그인
 * 하나, 실행 하나)이 쓴다.
 */
export function decodeSegment(segment: string): string | null {
  try {
    return decodeURIComponent(segment);
  } catch {
    return null;
  }
}
