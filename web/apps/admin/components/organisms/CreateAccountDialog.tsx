// 계정 만들기 창(admin-login 명세 "계정 화면과 내 비밀번호", 그림 mk-accounts-create). 계정 이름 칸 하나와 "단계: 관리자" 글이다.
// 이름은 칸을 떠날 때 규칙에 대 보고(서버가 다시 본다), 보낼 때도 한 번 더 본다. 규칙을 어기면 보내지 않는다. 409 면 칸 아래에
// "이 이름의 계정이 있다(비활성 계정 포함)"를 보이고, 서버가 422 로 이름이 규칙을 어겼다고 하면 그 문구를 보인다. 만들면
// 곧바로 비밀번호 링크 창으로 이어진다(`onCreated`).
import { Button, TextField } from "@agent-os/ui";
import { useState } from "react";
import { describeFailure } from "../../api/failure";
import type { AccountCreation, IssuedLink } from "../../api/accounts";
import { Dialog } from "../molecules/Dialog";
import { FailureAlert } from "../molecules/FailureAlert";

/** 계정 이름의 규칙. 서버는 영문 대문자만 소문자로 바꾼 뒤 이 규칙에 댄다. */
const NAME_RULE = /^[a-z0-9][a-z0-9._-]{2,31}$/;
const NAME_HELP =
  "영문 소문자, 숫자, . _ - 로 3~32자. 영문자나 숫자로 시작한다. 한 번 쓴 이름은 다시 쓰지 못한다.";
const NAME_INVALID =
  "규칙에 맞지 않는 이름이다. 영문 소문자, 숫자, . _ - 로 3~32자이고 영문자나 숫자로 시작한다.";
const NAME_TAKEN = "이 이름의 계정이 있다(비활성 계정 포함)";

function followsRule(name: string): boolean {
  return NAME_RULE.test(name.replace(/[A-Z]/g, (letter) => letter.toLowerCase()));
}

interface CreateAccountDialogProps {
  readonly onCreate: (name: string) => Promise<AccountCreation>;
  /** 계정을 만들었다. 이 창은 닫고 링크 창으로 이어 간다. */
  readonly onCreated: (link: IssuedLink) => void;
  readonly onClose: () => void;
}

export function CreateAccountDialog({ onCreate, onCreated, onClose }: CreateAccountDialogProps) {
  const [name, setName] = useState("");
  const [problem, setProblem] = useState<string | null>(null);
  const [failure, setFailure] = useState<unknown>(null);
  const [pending, setPending] = useState(false);

  /** 칸을 떠날 때 규칙에 대 본다. 비어 있으면 아직 적지 않은 것이라 탓하지 않는다. */
  function checkName(): void {
    if (name !== "" && !followsRule(name)) {
      setProblem(NAME_INVALID);
    }
  }

  async function submit(): Promise<void> {
    if (pending) {
      return;
    }
    if (!followsRule(name)) {
      setProblem(NAME_INVALID);
      return;
    }
    setPending(true);
    setFailure(null);
    try {
      const result = await onCreate(name);
      if (result.kind === "created") {
        onCreated(result.link);
      } else if (result.kind === "taken") {
        setProblem(NAME_TAKEN);
      } else {
        setProblem(result.message);
      }
    } catch (cause) {
      setFailure(cause);
    } finally {
      setPending(false);
    }
  }

  const failureText = failure === null ? null : describeFailure(failure);
  return (
    <Dialog title="계정 만들기" onClose={onClose} busy={pending}>
      <form
        className="flex flex-col gap-4"
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
      >
        {failureText === null ? null : (
          <FailureAlert
            title="계정을 만들지 못했다"
            message={failureText.message}
            requestId={failureText.requestId}
          />
        )}
        <TextField
          label="계정 이름"
          name="name"
          autoComplete="off"
          value={name}
          help={NAME_HELP}
          error={problem}
          onChange={(value) => {
            setName(value);
            setProblem(null);
          }}
          onBlur={() => {
            checkName();
          }}
        />
        <p className="text-body text-text-muted">단계: 관리자</p>
        <div className="flex justify-end gap-2">
          <Button variant="secondary" disabled={pending} onClick={onClose}>
            취소
          </Button>
          <Button type="submit" loading={pending}>
            만들기
          </Button>
        </div>
      </form>
    </Dialog>
  );
}
