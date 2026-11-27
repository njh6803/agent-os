import { Alert } from "@agent-os/ui";
import { describeFailure, type RequestFailure } from "../../api/failure";
import { FailureAlert } from "../molecules/FailureAlert";

interface RunNoticesProps {
  /** 마지막 요청이 받아들여지지 않은 실패와 그 요청의 갈래. 없으면 null 이다. */
  readonly failure: { readonly kind: "decide" | "send"; readonly error: RequestFailure } | null;
  /** 마지막 응답 스트림이 결말 없이 끊겼다. */
  readonly cut: boolean;
}

const TITLE = {
  decide: "결정을 보내지 못했다",
  send: "요청을 보내지 못했다",
} as const satisfies Record<"decide" | "send", string>;

/**
 * 대화 아래, 입력 칸 위에 서는 알림 둘(admin-login 명세 "대화 화면"). 요청이 받아들여지지 않은 실패와 결말 없이 끊긴 응답
 * 스트림이다. 결정 본문의 형식 오류(422)는 승인 묻기의 사유 칸 아래에 서므로 여기 없다. 그 밖(409 의 뜻 넷, 없는 실행, 서버
 * 오류)은 제목과 봉투의 메시지와 추적 식별자이고, 봉투가 없으면(닿지 못함) "서버에 닿지 못했다"다. 401 도 같다. 갱신까지 401
 * 이면 화면이 로그인 화면으로 가지만 갱신이 네트워크나 서버 오류로 실패했으면 가지 않고 처음 401 이 남는다(`api/session`의
 * `rule.ts`). 그때 알림이 없으면 운영자가 요청이 나갔는지 알 길이 없다. 끊긴 알림은 패키지 `Alert`(정보, `role="status"`)가
 * 끊길 때 영역째 들어온다.
 */
export function RunNotices({ failure, cut }: RunNoticesProps) {
  const shown = failure === null || failure.error.status === 422 ? null : failure;
  return (
    <>
      {shown === null ? null : (
        <FailureAlert title={TITLE[shown.kind]} {...describeFailure(shown.error)} />
      )}
      {cut ? (
        <Alert tone="info" title="응답 스트림이 끊겼다. 실행은 서버에서 계속된다">
          창을 닫거나 떠나도 실행은 끝까지 간다. 돌아오면 트레이스로 이어 본다.
        </Alert>
      ) : null}
    </>
  );
}
