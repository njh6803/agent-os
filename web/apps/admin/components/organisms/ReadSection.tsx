import { type ReactNode, useId } from "react";
import { describeFailure } from "../../api/failure";
import { FailureNotice } from "../molecules/FailureNotice";

interface ReadSectionProps<T> {
  readonly heading: string;
  /** 서버에서 읽은 값. 아직 없으면 undefined 다. */
  readonly data: T | undefined;
  /** 마지막 읽기의 실패. 없으면 undefined 다. */
  readonly error: unknown;
  readonly isValidating: boolean;
  readonly onRefresh: () => void;
  /** 처음 불러오는 동안 값의 자리에 서는 문구. */
  readonly placeholder: string;
  /** 새로 고침과 값의 갈래 사이에 늘 서는 자리. 실패 중에도 남는다. 거르기나 켜고 끄기의 실패가 선다. */
  readonly above?: ReactNode;
  readonly children: (data: T) => ReactNode;
}

/**
 * 서버 데이터를 읽어 보이는 화면의 골격. 제목, 새로 고침 버튼, 다시 확인하는 중의 작은 표시, 그리고 실패·자리표시·
 * 값의 갈래다. 플러그인 목록, 플러그인 하나, 실행 목록, 실행 하나가 이 골격을 지난다.
 *
 * 처음 불러오는 중은 자리표시, 이미 보인 것을 다시 확인하는 중은 작은 표시이고 보인 것을 지우지 않는다(스토리 36).
 * 다시 읽다 실패하면 이미 보인 것을 지우고 실패만 보인다. 운영자가 옛 값을 믿지 않게 한다(`.claude/rules/web-admin.md`).
 * 실패는 봉투의 메시지와 추적 식별자다(스토리 37).
 */
export function ReadSection<T>({
  heading,
  data,
  error,
  isValidating,
  onRefresh,
  placeholder,
  above,
  children,
}: ReadSectionProps<T>) {
  const headingId = useId();
  const shown = data !== undefined || error !== undefined;

  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId}>{heading}</h2>
      <button type="button" onClick={onRefresh}>
        새로 고침
      </button>
      {shown && isValidating ? <span role="status">다시 확인하는 중</span> : null}
      {above}
      {error !== undefined ? (
        <FailureNotice {...describeFailure(error)} />
      ) : data === undefined ? (
        <p role="status">{placeholder}</p>
      ) : (
        children(data)
      )}
    </section>
  );
}
