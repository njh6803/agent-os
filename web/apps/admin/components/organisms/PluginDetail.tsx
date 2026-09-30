import { useId } from "react";
import type { PluginKind } from "../../api/plugins";
import { usePlugin } from "../../hooks/queries/plugins";
import { ReadSection } from "./ReadSection";

interface PluginDetailProps {
  readonly kind: PluginKind;
  readonly name: string;
}

/**
 * 플러그인 하나(`GET /plugins/{kind}/{name}`). 켜짐과 매니페스트를 통째로 보인다. 승인 대상 도구와 쓰는 MCP 서버를
 * 운영자가 여기서 확인한다(스토리 14). 매니페스트는 서버가 준 JSON 을 들여 적은 글자다. HTML 로 그리지 않는다.
 *
 * 읽을 수 없는 매니페스트는 500 봉투이고 그 메시지가 경로와 이유를 든다(스토리 15). 새로 고침과 실패의 표시는 읽기
 * 골격(`ReadSection`)이다.
 */
export function PluginDetail({ kind, name }: PluginDetailProps) {
  const { data, error, isValidating, mutate } = usePlugin(kind, name);
  const manifestId = useId();

  return (
    <ReadSection
      heading={name}
      data={data}
      error={error}
      isValidating={isValidating}
      onRefresh={() => {
        void mutate();
      }}
      placeholder="플러그인을 불러오는 중이다"
    >
      {(plugin) => (
        <>
          <p>{plugin.enabled ? "켜짐" : "꺼짐"}</p>
          <section aria-labelledby={manifestId}>
            <h3 id={manifestId}>매니페스트</h3>
            <pre>{JSON.stringify(plugin.manifest, null, 2)}</pre>
          </section>
        </>
      )}
    </ReadSection>
  );
}
