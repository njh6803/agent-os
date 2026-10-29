import { Button, Progress } from "@agent-os/ui";
import { type ReactNode, useId } from "react";
import { describeFailure } from "../../api/failure";
import { AfterDelay } from "../atoms/AfterDelay";
import { FailureAlert } from "../molecules/FailureAlert";
import { ScreenHeader } from "../molecules/ScreenHeader";

/** 다시 확인하는 동안 머리 아래 진행 표시와 상태 영역이 함께 드는 이름. */
const REFRESHING_LABEL = "다시 확인하는 중";

/**
 * 서버에서 읽은 값과 읽는 상태. 이 골격을 지나는 organisms 는 이것을 pages 에서 props 로 받는다. 읽기 훅을 부르는
 * 것은 pages 다.
 */
export interface ReadState<T> {
  /** 서버에서 읽은 값. 아직 없으면 undefined 다. */
  readonly data: T | undefined;
  /** 마지막 읽기의 실패. 없으면 undefined 다. */
  readonly error: unknown;
  readonly isValidating: boolean;
  readonly onRefresh: () => void;
}

interface ReadSectionProps<T> extends ReadState<T> {
  /** 화면의 제목(`h1`). 화면의 구역도 이 이름을 얻는다. */
  readonly title: ReactNode;
  /** 제목 옆에 서되 제목의 이름에 들지 않는 것. */
  readonly titleBeside?: ReactNode;
  /** 제목 아래 흐린 설명 한 줄. */
  readonly description?: ReactNode;
  /** 처음 불러오는 동안 머리 아래 진행 표시의 이름("…을 불러오는 중"). */
  readonly loadingLabel: string;
  /** 읽다 실패했을 때 알림의 제목("…을 읽지 못했다"). */
  readonly failureTitle: string;
  /** 머리와 값의 갈래 사이에 늘 서는 자리. 실패 중에도 남는다. 거르기나 켜고 끄기의 실패가 선다. */
  readonly above?: ReactNode;
  readonly children: (data: T) => ReactNode;
}

/**
 * 서버 데이터를 읽어 보이는 화면의 골격(admin-style 명세 "화면 머리와 공통 상태"). 화면 머리(제목, 설명, 보조 버튼
 * "새로 고침"), 머리 아래의 진행 표시, 그리고 실패·값의 갈래다. 플러그인 목록, 플러그인 하나, 실행 목록, 실행 하나가
 * 이 골격을 지난다. 읽은 값과 상태는 props 로 받는다(`ReadState`).
 *
 * 처음 불러오는 중은 머리 아래 진행 표시 하나이고 0.3초를 넘길 때만 선다(`AfterDelay`). 이미 보인 것을 다시 확인하는
 * 중은 "새로 고침"이 불러오는 중이 되고 머리 아래 진행 표시 "다시 확인하는 중"이 서며, 보인 것을 지우지 않는다(web-admin
 * 스토리 36). 다시 읽다 실패하면 이미 보인 것을 지우고 실패만 보인다. 운영자가 옛 값을 믿지 않게 한다(`.claude/rules/web-admin.md`).
 * 실패는 위험 알림이고 제목이 실패한 일, 본문이 봉투의 메시지와 추적 식별자다(web-admin 스토리 37).
 *
 * progressbar 는 라이브 영역이 아니라서(WAI-ARIA 1.2) 두 진행 표시의 이름은 화면에서 숨긴 상태 영역(`role="status"`)이
 * 따로 든다. 그 영역은 늘 서 있고 글만 바뀐다. 영역째 새로 들어오면 알리지 않는 화면 읽기 프로그램이 있어서다(위젯의
 * `ComposerBand` 와 같은 판단이고, 화면 읽기 프로그램으로 듣지 않았다). `sr-only` 는 절대 위치라 구역의 사이를 얻지 않는다.
 */
export function ReadSection<T>({
  title,
  titleBeside,
  description,
  data,
  error,
  isValidating,
  onRefresh,
  loadingLabel,
  failureTitle,
  above,
  children,
}: ReadSectionProps<T>) {
  const titleId = useId();
  const shown = data !== undefined || error !== undefined;
  const refreshing = shown && isValidating;

  return (
    <section aria-labelledby={titleId} className="flex flex-col gap-6">
      <ScreenHeader
        titleId={titleId}
        title={title}
        beside={titleBeside}
        description={description}
        action={
          <Button variant="secondary" loading={refreshing} onClick={onRefresh}>
            새로 고침
          </Button>
        }
      />
      <div role="status" className="sr-only">
        {refreshing ? REFRESHING_LABEL : null}
        {shown ? null : <AfterDelay>{loadingLabel}</AfterDelay>}
      </div>
      {refreshing ? <Progress label={REFRESHING_LABEL} /> : null}
      {shown ? null : (
        <AfterDelay>
          <Progress label={loadingLabel} />
        </AfterDelay>
      )}
      {above}
      {error !== undefined ? (
        <FailureAlert title={failureTitle} {...describeFailure(error)} />
      ) : data === undefined ? null : (
        children(data)
      )}
    </section>
  );
}
