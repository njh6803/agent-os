// 위젯의 첫 화면. 읽은 임베드 설정만 받아 그린다. 질의를 읽고 문서에 테마를 다는 것은 WidgetPage 다. 스토리가 이
// 화면을 폭 320px 과 400px 에서 그린다.
//
// 설정이 잘못됐으면(에이전트가 없거나 패턴 밖) 대화 자리에 위험 알림을 보이고 입력 자리를 막는다(web-widget 명세
// "임베드"의 잘못 준 속성).
import { Alert } from "@agent-os/ui";
import { Welcome } from "../molecules/Welcome";
import { Composer } from "../organisms/Composer";
import { TopBar } from "../organisms/TopBar";
import { WidgetFrame } from "../templates/WidgetFrame";

export interface WidgetScreenProps {
  readonly heading: string;
  readonly intro: string | null;
  /** 요청을 보낼 수 없는 설정이다. */
  readonly misconfigured: boolean;
}

export function WidgetScreen({ heading, intro, misconfigured }: WidgetScreenProps) {
  return (
    <WidgetFrame
      topBar={<TopBar heading={heading} />}
      conversation={
        misconfigured ? (
          <div className="p-4">
            <Alert tone="danger" title="위젯 설정이 올바르지 않습니다.">
              사이트 관리자에게 알려 주세요.
            </Alert>
          </div>
        ) : (
          <Welcome intro={intro} />
        )
      }
      composer={<Composer disabled={misconfigured} />}
    />
  );
}
