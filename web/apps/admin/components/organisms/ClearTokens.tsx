import { Button } from "@agent-os/ui";

/**
 * 설정 화면의 토큰 지우기 구역(admin-style 명세 "설정 화면과 테마", 그림 mk-settings). 누르면 이 탭의 관리 토큰과
 * 채널 토큰을 모두 지우고 관리 토큰 넣기 화면으로 돌아간다(web-admin 스토리 8).
 */
export function ClearTokens({ onClear }: { readonly onClear: () => void }) {
  return (
    <section className="flex flex-col items-start gap-3">
      <div className="flex flex-col gap-1">
        <h2 className="text-body font-semibold">토큰 지우기</h2>
        <p className="text-body text-text-muted">관리 토큰과 채널 토큰을 이 탭에서 모두 지운다.</p>
      </div>
      <Button variant="secondary" onClick={onClear}>
        토큰 지우기
      </Button>
    </section>
  );
}
