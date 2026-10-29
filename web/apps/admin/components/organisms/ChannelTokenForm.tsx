import { Button, Card, Icon, TextField } from "@agent-os/ui";

const FIELD = "channelToken";

interface ChannelTokenFormProps {
  /** 이 탭에 채널 토큰이 있는가. 있으면 넣었다는 줄만 선다. */
  readonly entered: boolean;
  readonly onEnter: (token: string) => void;
}

/**
 * 설정 화면의 채널 토큰 구역(admin-style 명세 "설정 화면과 테마", 그림 mk-settings, mk-settings-m). 선택이다. 넣지
 * 않아도 관리 화면의 나머지를 모두 쓰고, 넣으면 멈춘 실행에 결정 자리가 설 수 있다(web-admin 스토리 4, 5. 서는 조건은
 * `RunDecision` 이 든다). 확인할 채널의 읽기 경로가 없어(ADR 0014) 넣을 때 확인하지 않는다. 틀린 채널 토큰은 첫 결정의
 * 401 로 드러나 이 탭에서 지워지고, 그 뒤 설정 화면에 이 입력이 다시 선다.
 *
 * 토큰은 헤더에만 실린다(스토리 9). 관리 토큰을 넣는 자리처럼 가린 입력이고 값을 React 상태로 들지 않으며, 넣는
 * 즉시 칸을 비운다. 폼은 보내지 않고 가로채므로 토큰이 주소의 질의로 가지 않는다.
 */
export function ChannelTokenForm({ entered, onEnter }: ChannelTokenFormProps) {
  return (
    <section className="flex flex-col gap-3">
      <div className="flex flex-col gap-1">
        <h2 className="text-body font-semibold">채널 토큰</h2>
        <p className="text-body text-text-muted">
          일시정지한 실행에 결정을 낼 때 쓴다. <code className="font-mono">agent-os serve</code> 를
          띄울 때 <code className="font-mono wrap-anywhere">AGENT_OS_CHANNEL_TOKEN</code> 에 준
          값이다.
        </p>
      </div>
      {entered ? (
        <Card padding="3">
          <p className="flex items-center gap-2 text-body">
            <Icon name="circle-check" size="16" />
            채널 토큰을 넣었다
          </p>
        </Card>
      ) : (
        <Card padding="4">
          <form
            className="flex flex-col gap-3 wide:flex-row wide:items-end"
            onSubmit={(event) => {
              event.preventDefault();
              const form = event.currentTarget;
              const token = new FormData(form).get(FIELD);
              form.reset();
              if (typeof token === "string" && token.trim() !== "") {
                onEnter(token);
              }
            }}
          >
            <div className="min-w-0 flex-1">
              <TextField
                label="채널 토큰"
                type="password"
                name={FIELD}
                autoComplete="off"
                required
              />
            </div>
            <Button type="submit">채널 토큰 넣기</Button>
          </form>
        </Card>
      )}
    </section>
  );
}
