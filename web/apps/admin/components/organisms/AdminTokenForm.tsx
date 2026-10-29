import { Alert, Button, Card, TextField } from "@agent-os/ui";
import { useId, useState } from "react";
import { UNREACHABLE } from "../../api/failure";
import type { AdminTokenNotice } from "../../stores/tokens";

const FIELD = "adminToken";

// 넣는 자리의 알림은 실패 알림의 제목 표를 따르지 않고 그림대로다(admin-style 명세 "화면 머리와 공통 상태").
const NOTICES = {
  rejected: {
    title: "관리 토큰이 거부됐다",
    body: "서버를 띄울 때 준 값과 같은지 보고 다시 넣는다.",
  },
  unreachable: { title: UNREACHABLE, body: "agent-os serve가 떠 있는지 보고 다시 넣는다." },
} as const satisfies Record<AdminTokenNotice, { title: string; body: string }>;

interface AdminTokenFormProps {
  /** 넣는 자리의 알림. 없으면 null 이다. */
  readonly notice: AdminTokenNotice | null;
  /** 넣은 토큰을 확인한다. 판정은 돌려주지 않고, 받아들인 토큰이나 알림으로 드러난다. */
  readonly onEnter: (token: string) => Promise<void>;
  /** 이 탭에 남은 토큰을 지운다. 있으면 카드 아래에 채널 토큰이 남았다는 줄과 버튼이 선다. 없으면 null 이다. */
  readonly onClearTokens: (() => void) | null;
}

/**
 * 관리 토큰을 넣는 자리. 넣으면 `onEnter` 가 목록 요청 하나로 확인한다. 화면 머리, 알림, 카드, 아래 줄이 위에서
 * 아래로 선다(그림 mk-token, mk-token-m).
 *
 * 토큰은 헤더에만 실린다(스토리 9). 입력칸은 가린 입력이고 값을 React 상태로 들지 않는다. 제어하는 입력은 값을
 * 요소의 속성에도 옮겨 적는다. 넣는 즉시 칸을 비워 거부된 토큰도 문서에 남지 않는다. 폼은 보내지 않고 가로채므로
 * 토큰이 주소의 질의로 가지 않는다.
 */
export function AdminTokenForm({ notice, onEnter, onClearTokens }: AdminTokenFormProps) {
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
      await onEnter(token);
    } finally {
      // 예상하지 못한 예외(판정이 다시 던진 것)에도 버튼은 풀린다. 예외는 삼키지 않고 콘솔에 드러난다.
      setChecking(false);
    }
  }

  return (
    <section aria-labelledby={headingId} className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id={headingId} className="text-title">
          관리 토큰 넣기
        </h1>
        {/* 좁은 폭에서 긴 변수 이름이 칸 밖으로 밀리지 않게 아무 곳에서나 줄을 바꾼다(그림 mk-token-m). */}
        <p className="text-body text-text-muted">
          <code className="font-mono text-mono">agent-os serve</code> 를 띄울 때{" "}
          <code className="font-mono text-mono wrap-anywhere">AGENT_OS_ADMIN_TOKEN</code> 에 준
          값이다. 이 탭에만 남고 탭을 닫으면 사라진다.
        </p>
      </div>
      {notice === null ? null : (
        <Alert tone="danger" title={NOTICES[notice].title}>
          {NOTICES[notice].body}
        </Alert>
      )}
      <Card padding="4">
        <form
          className="flex flex-col gap-4"
          onSubmit={(event) => {
            event.preventDefault();
            void submit(event.currentTarget);
          }}
        >
          <TextField
            label="관리 토큰"
            type="password"
            name={FIELD}
            autoComplete="off"
            required
            help="넣으면 플러그인 목록을 한 번 읽어 맞는 토큰인지 본다."
          />
          {/* 넓은 폭은 오른쪽 끝에, 좁은 폭은 칸의 폭으로 선다(그림 mk-token, mk-token-m). */}
          <div className="flex flex-col wide:items-end">
            <Button type="submit" disabled={checking}>
              넣기
            </Button>
          </div>
        </form>
      </Card>
      {onClearTokens === null ? null : (
        <div className="flex items-center justify-between gap-3 border-t border-border pt-4">
          <p className="min-w-0 text-body text-text-muted">이 탭에 채널 토큰이 남아 있다.</p>
          <Button variant="secondary" onClick={onClearTokens}>
            토큰 지우기
          </Button>
        </div>
      )}
    </section>
  );
}
