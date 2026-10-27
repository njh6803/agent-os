import type { ReadState } from "../organisms/ReadSection";

/** 읽기 훅(SWR)이 돌려준 것 가운데 읽기 골격이 쓰는 넷. 하나의 키와 무한 목록이 모두 이 모양이다. */
interface ReadResponse<T> {
  readonly data: T | undefined;
  readonly error: unknown;
  readonly isValidating: boolean;
  readonly mutate: () => Promise<unknown>;
}

/**
 * 읽기 훅의 응답을 읽기 골격을 지나는 organisms 의 props 로 옮긴다. 새로 고침은 그 키를 다시 읽는다. SWR 은 그리는
 * 동안 읽은 필드만 지켜보므로 넷을 여기서 모두 읽는다. 화면마다 읽기 훅을 부르는 자리가 쓴다.
 */
export function readOf<T>({ data, error, isValidating, mutate }: ReadResponse<T>): ReadState<T> {
  return {
    data,
    error,
    isValidating,
    onRefresh: () => {
      void mutate();
    },
  };
}
