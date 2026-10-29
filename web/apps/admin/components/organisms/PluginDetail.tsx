import { Icon } from "@agent-os/ui";
import { useId } from "react";
import type { Plugin, PluginKind } from "../../api/plugins";
import { CodeBlock, formatJson } from "../atoms/CodeBlock";
import { TextLink } from "../atoms/TextLink";
import { KIND_NAMES } from "./PluginList";
import { ReadSection, type ReadState } from "./ReadSection";

interface PluginDetailProps extends ReadState<Plugin> {
  readonly kind: PluginKind;
  readonly name: string;
}

/**
 * 플러그인 하나(`GET /plugins/{kind}/{name}`, 그림 mk-plugin, mk-plugin-m). 돌아가는 링크 "플러그인 목록", 제목인
 * 플러그인 이름과 그 옆의 켜짐·꺼짐, 그리고 매니페스트를 통째로 보인다. 승인 대상 도구와 쓰는 MCP 서버를 운영자가
 * 여기서 확인한다(스토리 14). 매니페스트는 서버가 준 JSON 을 들여 적은 글자다. HTML 로 그리지 않는다. 켜고 끄기는
 * 목록에서만 한다.
 *
 * 읽을 수 없는 매니페스트는 500 봉투이고 그 메시지가 경로와 이유를 든다(스토리 15). 새로 고침과 실패의 표시는 읽기
 * 골격(`ReadSection`)이다. 켜짐·꺼짐도 읽은 값이 보일 때만 선다.
 */
export function PluginDetail({ kind, name, ...read }: PluginDetailProps) {
  const manifestId = useId();
  const shown = read.error === undefined ? read.data : undefined;

  return (
    <div className="flex max-w-content flex-col gap-6">
      <PluginsLink />
      <ReadSection
        title={<span className="font-mono">{name}</span>}
        titleBeside={shown === undefined ? undefined : <EnabledMark enabled={shown.enabled} />}
        description={`${KIND_NAMES[kind]}. 켜고 끄기는 플러그인 목록에서 한다.`}
        {...read}
        loadingLabel="플러그인을 불러오는 중"
        failureTitle="플러그인을 읽지 못했다"
      >
        {(plugin) => (
          <section aria-labelledby={manifestId} className="flex flex-col gap-2">
            <h2 id={manifestId} className="text-body font-semibold">
              매니페스트
            </h2>
            <CodeBlock>{formatJson(plugin.manifest)}</CodeBlock>
          </section>
        )}
      </ReadSection>
    </div>
  );
}

/** 플러그인 목록으로 돌아가는 링크. 주소로 플러그인을 고르지 못한 화면도 같은 자리에 둔다. */
export function PluginsLink() {
  return (
    <div className="self-start">
      <TextLink href="/">플러그인 목록</TextLink>
    </div>
  );
}

/** 켜짐(`circle-check`)이나 꺼짐(`circle-minus`). 색만으로 가르지 않고 아이콘 모양과 글자로 가른다. */
function EnabledMark({ enabled }: { readonly enabled: boolean }) {
  return (
    <span className="flex items-center gap-1 text-body">
      <Icon name={enabled ? "circle-check" : "circle-minus"} size="16" />
      {enabled ? "켜짐" : "꺼짐"}
    </span>
  );
}
