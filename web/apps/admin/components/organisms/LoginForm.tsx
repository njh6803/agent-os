// 로그인 화면의 입력 자리(admin-login 명세 "로그인 화면", 그림 mk-login-m, mk-login-notices). 화면 머리, 알림, 카드 안의 두
// 칸과 단추가 위에서 아래로 선다. 알림은 위에서부터 이전 화면이 남긴 알림(로그아웃했다 따위), https 가 아닌 주소의 경고,
// 로그인 실패 순이다.
//
// 입력은 폼이 가로채 보내므로 이름과 비밀번호가 주소의 질의로 가지 않는다. 비밀번호 칸은 거절될 때마다 새로 세운다
// (`rejections` 를 열쇠로). 이름 칸은 그대로 두고 비밀번호 칸만 비워 다시 입력하게 한다. 새로 선 칸이 포커스를 받는다.
import { Alert, Button, Card, TextField } from "@agent-os/ui";
import { useId } from "react";
import { describeFailure, type RequestFailure } from "../../api/failure";
import type { LoginNotice } from "../../api/session";
import { FailureAlert } from "../molecules/FailureAlert";

const NOTICES = {
  "logged-out": { title: "로그아웃했다", body: null },
  expired: {
    title: "로그인이 끝났다",
    body: "오래 쓰지 않았거나 서버가 로그인을 끊었다. 다시 로그인한다.",
  },
  "password-set": { title: "비밀번호를 정했다", body: "정한 비밀번호로 로그인한다." },
} as const satisfies Record<LoginNotice, { title: string; body: string | null }>;

/** 로그인 요청 하나의 상태(훅 `useLogIn` 이 낸다). */
export interface LoginState {
  /** 이름이나 비밀번호가 맞지 않아 거절됐다. */
  readonly rejected: boolean;
  /** 지금까지 거절된 횟수. 비밀번호 칸을 새로 세우는 열쇠다. */
  readonly rejections: number;
  /** 거절이 아닌 실패(서버에 닿지 못함, 서버의 오류). 없으면 null 이다. */
  readonly failure: RequestFailure | null;
  /** 로그인 요청이 가는 동안 참이다. */
  readonly pending: boolean;
}

interface LoginFormProps {
  /** 이전 화면이 남긴 알림. 없으면 null 이다. */
  readonly notice: LoginNotice | null;
  /**
   * https 가 아닌 주소로 열었다. 서버가 쿠키를 받아 주지 않아 로그인할 수 없으므로 로그인 단추만 막고 알린다. 입력 칸은
   * 열어 두어 알림을 읽고 값을 옮겨 적을 수 있다(그림 mk-login-notices 는 주 버튼만 막았다).
   */
  readonly insecure: boolean;
  readonly state: LoginState;
  readonly onSubmit: (name: string, password: string) => Promise<void>;
}

export function LoginForm({ notice, insecure, state, onSubmit }: LoginFormProps) {
  const { rejected, rejections, failure, pending } = state;
  const headingId = useId();

  function submit(form: HTMLFormElement): void {
    const data = new FormData(form);
    const name = data.get("name");
    const password = data.get("password");
    if (typeof name !== "string" || typeof password !== "string") {
      return;
    }
    void onSubmit(name, password);
  }

  const shownNotice = notice === null ? null : NOTICES[notice];
  const failureText = failure === null ? null : describeFailure(failure);
  return (
    <section aria-labelledby={headingId} className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id={headingId} className="text-title">
          로그인
        </h1>
        <p className="text-body text-text-muted">운영자 계정으로 로그인한다.</p>
      </div>
      {shownNotice === null ? null : (
        <Alert tone="info" title={shownNotice.title}>
          {shownNotice.body}
        </Alert>
      )}
      {insecure ? (
        <Alert tone="warning" title="이 주소에서는 로그인할 수 없다">
          이 주소는 https가 아니라 로그인할 수 없다. https 주소로 연다. 로그인은 https 주소나 이
          서버 자신(localhost)에서만 된다.
        </Alert>
      ) : null}
      {rejected ? (
        <Alert tone="danger" title="로그인하지 못했다">
          계정 이름이나 비밀번호가 맞지 않거나 지금은 이 계정으로 로그인할 수 없다. 비밀번호를
          잊었거나 계정이 잠겼으면 시스템 관리자에게 비밀번호 링크를 받는다.
        </Alert>
      ) : null}
      {failureText === null ? null : (
        <FailureAlert
          title="로그인을 보내지 못했다"
          message={failureText.message}
          requestId={failureText.requestId}
        />
      )}
      <Card padding="4">
        <form
          className="flex flex-col gap-4"
          onSubmit={(event) => {
            event.preventDefault();
            submit(event.currentTarget);
          }}
        >
          <TextField label="계정 이름" name="name" autoComplete="username" required />
          <TextField
            key={rejections}
            label="비밀번호"
            type="password"
            name="password"
            autoComplete="current-password"
            required
            autoFocus={rejections > 0}
          />
          {/* 넓은 폭은 오른쪽 끝에, 좁은 폭은 칸의 폭으로 선다(그림 mk-login-m). */}
          <div className="flex flex-col wide:items-end">
            <Button type="submit" loading={pending} disabled={insecure}>
              로그인
            </Button>
          </div>
        </form>
      </Card>
    </section>
  );
}
