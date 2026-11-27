// 계정이 하나도 없는 서버의 로그인 화면(admin-login 명세 "로그인 화면", 그림 mk-login-empty). 입력 칸 대신 첫 계정을 만드는
// 명령 두 꼴을 보이고, 만든 뒤 화면을 새로 고치게 한다. 남이 먼저 계정을 만들 길이 없다는 것을 믿게 하려고, 계정은 서버에서
// 명령으로만 만든다고 말한다.
//
// 명령은 글자 그대로 고정폭이고, 칸마다 복사 단추가 있다. 복사는 브라우저가 허락한 자리(https 나 localhost)에서만 된다.
// 막히면 아무 일도 일어나지 않고, 명령은 그대로 보여 손으로 고를 수 있다.
import { Button, Card, IconButton } from "@agent-os/ui";
import { useId, useState } from "react";

const COMMANDS = [
  { id: "plain", text: "agent-os operator system-admin <계정 이름>", note: null },
  {
    id: "docker",
    text: "docker compose exec serve agent-os operator system-admin <계정 이름>",
    note: "단독 배포로 띄웠으면 이 명령을 친다.",
  },
] as const satisfies readonly { id: string; text: string; note: string | null }[];

function CommandRow({ text, note }: { readonly text: string; readonly note: string | null }) {
  const [copied, setCopied] = useState(false);
  async function copy(): Promise<void> {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      // 복사가 막힌 자리다. 명령이 화면에 그대로 있어 손으로 고르면 된다.
    }
  }
  return (
    <div className="flex flex-col gap-1">
      {note === null ? null : <p className="text-small text-text-muted">{note}</p>}
      <div className="flex items-start gap-2">
        <code className="min-w-0 flex-1 font-mono text-mono wrap-anywhere">{text}</code>
        <IconButton
          icon={copied ? "check" : "copy"}
          label={copied ? "복사했다" : "명령 복사"}
          variant="ghost"
          size="s"
          onClick={() => {
            void copy();
          }}
        />
      </div>
    </div>
  );
}

export function FirstAccountGuide() {
  const headingId = useId();
  return (
    <section aria-labelledby={headingId} className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 id={headingId} className="text-title">
          첫 계정을 만든다
        </h1>
        <p className="text-body text-text-muted">
          아직 운영자 계정이 없다. 서버에서 아래 명령으로 시스템 관리자를 만든다. 비밀번호는 명령이
          묻는다.
        </p>
      </div>
      <Card padding="4">
        <div className="flex flex-col gap-3">
          {COMMANDS.map(({ id, text, note }) => (
            <CommandRow key={id} text={text} note={note} />
          ))}
          <div className="flex items-center justify-between gap-3 border-t border-border pt-3">
            <span className="text-body text-text-muted">만든 뒤 이 화면을 새로 고친다.</span>
            <Button
              variant="secondary"
              onClick={() => {
                location.reload();
              }}
            >
              새로 고침
            </Button>
          </div>
        </div>
      </Card>
    </section>
  );
}
