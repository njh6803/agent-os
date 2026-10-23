// 첫 화면의 대화 자리. 사이트가 준 할 수 있는 일 한 줄(있을 때)과 그 아래 안내 한 줄이다(web-widget 명세 "대화
// 화면"의 첫 화면).
export interface WelcomeProps {
  /** null 이면 그 줄을 그리지 않는다. */
  readonly intro: string | null;
}

export function Welcome({ intro }: WelcomeProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-2 p-6 text-center">
      {intro === null ? null : <p className="text-body">{intro}</p>}
      <p className="text-small text-text-muted">아래에 요청을 적어 보내 주세요.</p>
    </div>
  );
}
