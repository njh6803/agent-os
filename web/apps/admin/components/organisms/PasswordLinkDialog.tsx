// 비밀번호 링크 창(admin-login 명세 "계정 화면과 내 비밀번호", 그림 mk-accounts-link). 링크와 "복사" 단추, 그리고 네 줄이다.
// 링크는 서버가 준 토큰으로 화면이 짓는다(`address`). 서버는 토큰의 해시만 두어 링크를 다시 보여 주지 못하므로, 이 창을
// 닫으면 링크는 화면에서도 사라진다. 그래서 어두운 막을 눌러서는 닫히지 않고 "닫기" 단추와 Esc 로만 닫는다(Esc 는 확인
// 없이 바로 닫는다. 명세가 정한 것은 막을 눌러 닫지 않는 것까지다).
import { Alert, Button } from "@agent-os/ui";
import { useState } from "react";
import type { IssuedLink } from "../../api/accounts";
import { formatMinute, localClock } from "../atoms/clock";
import { Dialog } from "../molecules/Dialog";

type Copying = "idle" | "copied" | "failed";

interface PasswordLinkDialogProps {
  readonly link: IssuedLink;
  /** 토큰으로 링크의 주소를 짓는다. 이 관리 화면의 출처가 들어간다. */
  readonly addressOf: (token: string) => string;
  readonly onClose: () => void;
}

export function PasswordLinkDialog({ link, addressOf, onClose }: PasswordLinkDialogProps) {
  const [copying, setCopying] = useState<Copying>("idle");
  const address = addressOf(link.token);
  const expires = formatMinute(localClock(), link.expiresAt);

  async function copy(): Promise<void> {
    try {
      await navigator.clipboard.writeText(address);
      setCopying("copied");
    } catch {
      setCopying("failed");
    }
  }

  return (
    <Dialog
      title={
        <>
          <span className="font-mono">{link.name}</span>의 비밀번호 링크
        </>
      }
      onClose={onClose}
    >
      <p className="text-body text-text-muted">
        이 링크를 {link.name}에게 직접 전한다. 메일은 보내지 않는다.
      </p>
      <div className="flex items-start gap-2 rounded-m border border-border bg-bg py-2 pr-2 pl-3">
        <code className="min-w-0 flex-1 py-1 font-mono text-mono wrap-anywhere">{address}</code>
        <Button
          variant="secondary"
          icon="copy"
          onClick={() => {
            void copy();
          }}
        >
          {copying === "copied" ? "복사했다" : "복사"}
        </Button>
      </div>
      {copying === "failed" ? (
        <p role="status" className="text-small text-danger">
          복사하지 못했다. 링크를 직접 골라 복사한다.
        </p>
      ) : null}
      <ul className="m-0 flex list-none flex-col gap-1 p-0 text-body text-text-muted">
        <li>한 번만 쓰인다. {expires}에 끝난다(만든 뒤 24시간).</li>
        <li>다시 만들면 이 링크는 쓸 수 없다.</li>
      </ul>
      <Alert tone="info" title="이 창을 닫으면 링크를 다시 볼 수 없다">
        서버는 링크를 다시 보여 주지 못한다. 잃으면 새로 만든다.
      </Alert>
      <div className="flex justify-end">
        <Button variant="secondary" onClick={onClose}>
          닫기
        </Button>
      </div>
    </Dialog>
  );
}
