import { useId, useState } from "react";
import { UNREACHABLE } from "../../api/failure";
import { useAdminTokenEntry } from "../../hooks/queries/plugins";
import { useTokens, type AdminTokenNotice } from "../../stores/tokens";
import { FailureNotice } from "../molecules/FailureNotice";

const FIELD = "adminToken";

const NOTICES = {
  rejected: "관리 토큰이 거부됐다",
  unreachable: UNREACHABLE,
} as const satisfies Record<AdminTokenNotice, string>;

/**
 * 관리 토큰을 넣는 자리. 넣으면 목록 요청 하나로 확인한다.
 *
 * 토큰은 헤더에만 실린다(스토리 9). 입력칸은 가린 입력이고 값을 React 상태로 들지 않는다. 제어하는 입력은 값을
 * 요소의 속성에도 옮겨 적는다. 넣는 즉시 칸을 비워 거부된 토큰도 문서에 남지 않는다. 폼은 보내지 않고 가로채므로
 * 토큰이 주소의 질의로 가지 않는다.
 */
export function AdminTokenForm() {
  const enter = useAdminTokenEntry();
  const notice = useTokens((state) => state.adminTokenNotice);
  const [checking, setChecking] = useState(false);
  const headingId = useId();

  async function submit(form: HTMLFormElement): Promise<void> {
    const token = new FormData(form).get(FIELD);
    form.reset();
    if (typeof token !== "string" || token.trim() === "") {
      return;
    }
    setChecking(true);
    try {
      await enter(token);
    } finally {
      // 예상하지 못한 예외(판정이 다시 던진 것)에도 버튼은 풀린다. 예외는 삼키지 않고 콘솔에 드러난다.
      setChecking(false);
    }
  }

  return (
    <section aria-labelledby={headingId}>
      <h2 id={headingId}>관리 토큰 넣기</h2>
      <p>
        <code>agent-os serve</code> 를 띄울 때 <code>AGENT_OS_ADMIN_TOKEN</code> 에 준 값이다. 이
        탭에만 남고 탭을 닫으면 사라진다.
      </p>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          void submit(event.currentTarget);
        }}
      >
        <label>
          관리 토큰 <input type="password" name={FIELD} autoComplete="off" required />
        </label>
        <button type="submit" disabled={checking}>
          넣기
        </button>
      </form>
      {notice === null ? null : <FailureNotice message={NOTICES[notice]} requestId={null} />}
    </section>
  );
}
