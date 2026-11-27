// 비밀번호 규칙을 화면에서 미리 대 보는 함수(admin-login 명세 "계정 이름과 비밀번호"의 "화면").
// 서버와 같은 정규화(`normalize("NFKC")`)와 코드 포인트 셈으로 센다. 입력 칸의 `maxlength` 는 쓰지 않는다. 그림 문자 128자는
// UTF-16 단위로 256이라(`"😀".repeat(128).length` 를 node 로 세어 본 값), 그 단위로 막으면 서버가 받는 비밀번호를 화면이 넘쳤다고 본다. 판정은 서버의 422 가 한다.

/** 비밀번호의 최소 글자 수(코드 포인트). */
export const PASSWORD_MIN = 8;
/** 비밀번호의 최대 글자 수(코드 포인트). */
export const PASSWORD_MAX = 128;

export interface PasswordCheck {
  /** 정규화한 뒤 코드 포인트로 센 글자 수. */
  readonly count: number;
  /** 8자 이상이다. */
  readonly length: boolean;
  /** 영문 대문자(A~Z)가 1자 이상이다. */
  readonly upper: boolean;
  /** 숫자(0~9)가 1자 이상이다. */
  readonly digit: boolean;
  /** 영문자와 숫자가 아닌 글자가 1자 이상이다. 한글도 여기에 든다. */
  readonly special: boolean;
  /** 128자를 넘었다. 규칙 목록이 아니라 따로 알린다. */
  readonly tooLong: boolean;
  /** 규칙 넷을 모두 맞추고 128자를 넘지 않았다. */
  readonly ok: boolean;
}

export function checkPassword(password: string): PasswordCheck {
  const chars = Array.from(password.normalize("NFKC"));
  const count = chars.length;
  const length = count >= PASSWORD_MIN;
  const upper = chars.some((char) => /^[A-Z]$/.test(char));
  const digit = chars.some((char) => /^[0-9]$/.test(char));
  const special = chars.some((char) => !/^[A-Za-z0-9]$/.test(char));
  const tooLong = count > PASSWORD_MAX;
  return {
    count,
    length,
    upper,
    digit,
    special,
    tooLong,
    ok: length && upper && digit && special && !tooLong,
  };
}
