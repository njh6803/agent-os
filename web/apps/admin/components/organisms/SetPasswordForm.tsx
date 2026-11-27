// 링크로 비밀번호를 정하는 화면의 본문(admin-login 명세 "비밀번호 링크"와 "계정 화면과 내 비밀번호", 그림
// mk-set-password-states). 로그인 없이 열리는 화면이라 `EntryFrame` 안에 선다. 새 비밀번호 칸 둘과 처음부터 보이는 규칙 목록이다.
// 두 칸이 다르면 보내지 않고 둘째 칸 아래에 알린다. 규칙을 다 맞추지 않으면 보내지 않고 규칙 목록을 위험 색으로 바꾼다. 128자를
// 넘으면 규칙 목록 위(첫째 칸 아래)에 알린다.
//
// 링크가 더 쓸 수 없는 것(404)이면 입력 칸을 모두 걷고 안내와 로그인 화면으로 가는 링크만 보인다. 화면은 토큰으로 무엇을 읽어
// 오지 않아 계정 이름을 모른다.
import { Alert, Button, Card, TextField } from "@agent-os/ui";
import { useId, useState } from "react";
import { describeFailure, type RequestFailure } from "../../api/failure";
import { TextLink } from "../atoms/TextLink";
import { FailureAlert } from "../molecules/FailureAlert";
import { PasswordRuleList } from "../molecules/PasswordRuleList";
import { PASSWORD_MAX, checkPassword } from "../molecules/passwordRules";

/** 정하는 요청 하나의 상태(훅 `useSetPassword` 가 낸다). */
export interface SetPasswordState {
  readonly pending: boolean;
  /** 링크를 더 쓸 수 없다(404). */
  readonly unusable: boolean;
  /** 서버가 비밀번호 칸에 단 글(422). */
  readonly passwordError: string | null;
  /** 서버에 닿지 못함, 서버의 오류. 없으면 null 이다. */
  readonly failure: RequestFailure | null;
}

interface SetPasswordFormProps {
  readonly state: SetPasswordState;
  readonly onSubmit: (password: string) => Promise<void>;
}

export function SetPasswordForm({ state, onSubmit }: SetPasswordFormProps) {
  const headingId = useId();
  const failureText = state.failure === null ? null : describeFailure(state.failure);
  return (
    <section aria-labelledby={headingId} className="flex flex-col gap-6">
      <h1 id={headingId} className="text-title">
        비밀번호 정하기
      </h1>
      {failureText === null ? null : (
        <FailureAlert
          title="비밀번호를 정하지 못했다"
          message={failureText.message}
          requestId={failureText.requestId}
        />
      )}
      {state.unusable ? (
        <>
          <Alert tone="danger" title="이 링크는 더 쓸 수 없다">
            링크는 한 번만 쓰이고 만든 뒤 24시간이 지나면 끝난다. 다시 만든 링크가 있으면 앞 링크는
            쓸 수 없다. 관리하는 사람에게 새 링크를 받는다.
          </Alert>
          <TextLink href="/login">로그인 화면으로</TextLink>
        </>
      ) : (
        <Card padding="4">
          <Fields state={state} onSubmit={onSubmit} />
        </Card>
      )}
    </section>
  );
}

function Fields({
  state,
  onSubmit,
}: {
  readonly state: SetPasswordState;
  readonly onSubmit: (password: string) => Promise<void>;
}) {
  const [password, setPassword] = useState("");
  const [again, setAgain] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const check = checkPassword(password);
  const differs = submitted && password !== again;

  function submit(): void {
    setSubmitted(true);
    if (!check.ok || password !== again) {
      return;
    }
    void onSubmit(password);
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
        label="새 비밀번호"
        type="password"
        name="new_password"
        autoComplete="new-password"
        value={password}
        error={check.tooLong ? `${String(PASSWORD_MAX)}자 이하로 줄인다` : state.passwordError}
        onChange={setPassword}
      />
      <PasswordRuleList check={check} submitted={submitted} />
      <TextField
        label="새 비밀번호 다시"
        type="password"
        name="new_password_again"
        autoComplete="new-password"
        value={again}
        error={differs ? "위 칸과 같지 않다" : null}
        onChange={setAgain}
      />
      <div className="flex flex-col wide:items-end">
        <Button type="submit" loading={state.pending}>
          비밀번호 정하기
        </Button>
      </div>
    </form>
  );
}
