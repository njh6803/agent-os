// 판정 함수가 잡는지 보려고 일부러 심은 클래스(프로브 표본). 기본 테마를 비운 뒤 CSS 를 만들지 않는 것
// (text-base, rounded, font-bold, shadow, text-red-500), 원색 토큰 이름(bg-gray-500), --spacing 을 읽는 것(p-5, w-64),
// 임의값(디자인 토큰을 건너뛰는 p-[13px], 없는 변수를 읽는 bg-[var(--nope)]), 그리고 우리 디자인 토큰(bg-bg, text-text,
// p-4)을 섞는다.
export function Planted() {
  return (
    <div className="text-base rounded font-bold shadow text-red-500 bg-gray-500 p-5 w-64 animate-pulse p-[13px] bg-[var(--nope)] bg-bg text-text p-4">
      심은 클래스
    </div>
  );
}
