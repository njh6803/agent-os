// 지금의 위젯이 답을 그리는 모양(글자 그대로 문단 하나). 크기 증분의 기준선이다.
export function Answer({ text }: { readonly text: string }) {
  return <p>{text}</p>;
}
