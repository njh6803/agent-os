// 글자 수 상한의 셈(web-widget 명세 "대화 화면"의 글자 수, "승인 묻기"의 사유의 상한). 입력창과 거부 사유 칸이 같은
// 상한과 같은 셈을 쓴다. 세는 단위는 서버와 같은 코드 포인트다. 이모지 하나는 UTF-16 으로 둘이지만 하나다.

const NUMBER = new Intl.NumberFormat("ko-KR");

/** 센 수를 보이기 시작하는 비율. */
const NEAR_LIMIT = 0.9;

/** 칸 아래에 보일 글자 수의 글. */
export interface CharNote {
  /** 상한을 넘었다. 보내기나 거부가 막힌다. */
  readonly over: boolean;
  /** 상한의 90% 이상이면 "19,850 / 20,000" 같은 센 수다. 아래면 null 이다. */
  readonly count: string | null;
  /** 넘었으면 "20,000자를 넘었습니다"다. 아니면 null 이다. */
  readonly overText: string | null;
}

export function charNote(text: string, limit: number): CharNote {
  const count = Array.from(text).length;
  const over = count > limit;
  return {
    over,
    count: count >= limit * NEAR_LIMIT ? `${NUMBER.format(count)} / ${NUMBER.format(limit)}` : null,
    overText: over ? `${NUMBER.format(limit)}자를 넘었습니다` : null,
  };
}
