// 내 비밀번호 바꾸기 화면의 본문(admin-login 명세 "계정 화면과 내 비밀번호", 그림 mk-my-password). 지금 비밀번호 칸, 새 비밀번호
// 칸, 처음부터 보이는 규칙 목록과 단추 하나다. 규칙은 칸에 적는 대로 미리 대 보인다(`passwordRules`). 규칙을 다 맞추지 않으면
// 보내지 않고 규칙 목록을 위험 색으로 바꾼다.
//
// 서버의 422 는 칸마다 그 칸 아래에 알리고(지금 비밀번호가 맞지 않다, 새 비밀번호가 규칙을 어겼다), 409 는 계정이 잠겼다는
// 알림이다. 성공하면 칸을 비운다. 칸들을 새로 세워 비우므로(`changes` 를 열쇠로) 새 비밀번호가 화면에 남지 않는다.
import { Alert, Button, Card, TextField } from "@agent-os/ui";
import { useId, useState } from "react";
import { describeFailure, type RequestFailure } from "../../api/failure";
import { FailureAlert } from "../molecules/FailureAlert";
import { PasswordRuleList } from "../molecules/PasswordRuleList";
import { PASSWORD_MAX, checkPassword } from "../molecules/passwordRules";
import { ScreenHeader } from "../molecules/ScreenHeader";

/** 바꾸는 요청 하나의 상태(훅 `useChangePassword` 가 낸다). */
export interface ChangePasswordState {
  readonly pending: boolean;
  /** 바뀌었다. 다음 시도를 보내면 걷힌다. */
  readonly changed: boolean;
  /** 계정이 잠겼다(409). */
  readonly locked: boolean;
  /** 서버가 지금 비밀번호 칸에 단 글(422). */
  readonly currentError: string | null;
  /** 서버가 새 비밀번호 칸에 단 글(422). */
  readonly newError: string | null;
  /** 지금까지 바뀐 횟수. 칸들을 새로 세우는 열쇠다. */
  readonly changes: number;
  /** 서버에 닿지 못함, 서버의 오류. 없으면 null 이다. */
  readonly failure: RequestFailure | null;
}

interface ChangePasswordFormProps {
  /** 로그인한 계정의 이름. 화면 머리의 설명에 든다. */
  readonly name: string;
  readonly state: ChangePasswordState;
  /** 로그인이 길어야 몇 분 안에 끊기는지. 보내기 전의 안내와 바꾼 뒤의 알림에 든다. */
  readonly tokenMinutes: number;
  readonly onSubmit: (currentPassword: string, newPassword: string) => Promise<void>;
}

export function ChangePasswordForm({
  name,
  state,
  tokenMinutes,
  onSubmit,
}: ChangePasswordFormProps) {
  const headingId = useId();
  const failureText = state.failure === null ? null : describeFailure(state.failure);
  return (
    <section aria-labelledby={headingId} className="flex max-w-form flex-col gap-6">
      <ScreenHeader
        titleId={headingId}
        title="내 비밀번호 바꾸기"
        description={`${name}의 비밀번호를 바꾼다.`}
      />
      {state.changed ? (
        <Alert tone="info" title="비밀번호를 바꿨다">
          다른 곳의 로그인은 길어야 {tokenMinutes}분 안에 끊긴다.
        </Alert>
      ) : null}
      {state.locked ? <Alert tone="danger" title="계정이 잠겼다. 잠시 뒤에 다시 한다" /> : null}
      {failureText === null ? null : (
        <FailureAlert
          title="비밀번호를 바꾸지 못했다"
          message={failureText.message}
          requestId={failureText.requestId}
        />
      )}
      <Card padding="4">
        <Fields key={state.changes} state={state} tokenMinutes={tokenMinutes} onSubmit={onSubmit} />
      </Card>
    </section>
  );
}

function Fields({
  state,
  tokenMinutes,
  onSubmit,
}: {
  readonly state: ChangePasswordState;
  readonly tokenMinutes: number;
  readonly onSubmit: (currentPassword: string, newPassword: string) => Promise<void>;
}) {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const check = checkPassword(next);

  function submit(): void {
    setSubmitted(true);
    if (!check.ok) {
      return;
    }
    void onSubmit(current, next);
  }

  return (
    <form
      className="flex flex-col gap-4"
      noValidate
      onSubmit={(event) => {
        event.preventDefault();
        submit();
      }}
    >
      <TextField
        label="지금 비밀번호"
        type="password"
        name="current_password"
        autoComplete="current-password"
        value={current}
        error={state.currentError}
        onChange={setCurrent}
      />
      <TextField
        label="새 비밀번호"
        type="password"
        name="new_password"
        autoComplete="new-password"
        value={next}
        error={check.tooLong ? `${String(PASSWORD_MAX)}자 이하로 줄인다` : state.newError}
        onChange={setNext}
      />
      <PasswordRuleList check={check} submitted={submitted} />
      <p className="text-small text-text-muted">
        바꾸면 이 계정의 다른 로그인은 길어야 {tokenMinutes}분 안에 모두 끊긴다. 이 브라우저의
        로그인은 그대로다.
      </p>
      <div className="flex flex-col wide:items-end">
        <Button type="submit" loading={state.pending}>
          비밀번호 바꾸기
        </Button>
      </div>
    </form>
  );
}
