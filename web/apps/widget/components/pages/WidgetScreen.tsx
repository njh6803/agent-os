// 위젯 화면. 읽은 임베드 설정과 대화의 상태를 받아 그린다. 질의를 읽고 문서에 테마를 달고 대화를 돌리는 것은
// WidgetPage 다. 스토리가 이 화면을 폭 320px 과 400px 에서 그린다.
//
// - 설정이 잘못됐으면(에이전트가 없거나 패턴 밖) 대화 자리에 위험 알림을 보이고 입력 자리를 막는다(web-widget 명세
//   "임베드"의 잘못 준 속성).
// - 교환이 없으면 첫 화면이고, 있으면 대화 목록이다.
// - 숨긴 role="status" 영역 하나가 새 도구 줄과 끝난 출력을 생긴 차례로 한 번씩 읽는다. 글마다 문단 하나를 덧붙여,
//   화면 읽기 프로그램은 더해진 문단만 읽는다. 영역은 처음부터 서 있어야 더해진 것을 읽으므로 늘 그린다.
// - 포커스 차례는 문서의 차례 그대로다. 위쪽 띠의 "새 대화" → 대화 영역 → 대화 안의 버튼 → 입력창 → 보내기.
//   대화 영역이 포커스를 받는 까닭은 organisms/Conversation 의 머리 주석이다.
import { Alert } from "@agent-os/ui";
import type { Exchange } from "../../lib/conversation";
import { Welcome } from "../molecules/Welcome";
import { Composer } from "../organisms/Composer";
import { Conversation } from "../organisms/Conversation";
import { TopBar } from "../organisms/TopBar";
import { WidgetFrame } from "../templates/WidgetFrame";

export interface WidgetScreenProps {
  readonly heading: string;
  readonly intro: string | null;
  /** 요청을 보낼 수 없는 설정이다. */
  readonly misconfigured: boolean;
  readonly exchanges: readonly Exchange[];
  /** 숨긴 읽기 영역이 읽을 글. 생긴 차례다. */
  readonly announcements: readonly string[];
  /** 실행이 돌거나 멈춰 있어 보내지 못한다. 보내기와 "다시 보내기"를 막는다. */
  readonly sendBlocked: boolean;
  /** 승인을 기다리며 멈춰 있다. 입력창도 막는다(승인 묻기는 티켓 08). */
  readonly paused: boolean;
  /** 응답이 결말 전이라 새 대화를 막는다. */
  readonly newConversationDisabled: boolean;
  readonly draft: string;
  readonly onDraftChange: (value: string) => void;
  readonly onSend: (request: string) => void;
  readonly onRetry: (request: string) => void;
  readonly onNewConversation: () => void;
  /** 요청 글자 수 상한(코드 포인트). */
  readonly requestChars: number;
}

export function WidgetScreen({
  heading,
  intro,
  misconfigured,
  exchanges,
  announcements,
  sendBlocked,
  paused,
  newConversationDisabled,
  draft,
  onDraftChange,
  onSend,
  onRetry,
  onNewConversation,
  requestChars,
}: WidgetScreenProps) {
  let conversation;
  if (misconfigured) {
    conversation = (
      <div className="p-4">
        <Alert tone="danger" title="위젯 설정이 올바르지 않습니다.">
          사이트 관리자에게 알려 주세요.
        </Alert>
      </div>
    );
  } else if (exchanges.length === 0) {
    conversation = <Welcome intro={intro} />;
  } else {
    conversation = (
      <Conversation exchanges={exchanges} onRetry={onRetry} retryBlocked={sendBlocked} />
    );
  }
  return (
    <WidgetFrame
      topBar={
        <TopBar
          heading={heading}
          onNewConversation={onNewConversation}
          newConversationDisabled={newConversationDisabled}
        />
      }
      conversation={
        <>
          {/* role="status" 의 aria-atomic 은 기본이 true 라 끄지 않으면 영역 전체를 다시 읽는다. */}
          <div role="status" aria-atomic="false" className="sr-only">
            {announcements.map((text, index) => (
              // 글은 뒤에만 붙고 새 대화가 통째로 비운다. 자리가 곧 글의 이름이다.
              <p key={index}>{text}</p>
            ))}
          </div>
          {conversation}
        </>
      }
      composer={
        <Composer
          value={draft}
          onChange={onDraftChange}
          onSend={onSend}
          limit={requestChars}
          disabled={misconfigured || paused}
          blocked={sendBlocked}
        />
      }
    />
  );
}
