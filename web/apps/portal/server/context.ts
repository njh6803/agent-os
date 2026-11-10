// 요청 처리기가 쓰는 값. 시작 검사를 지난 결과(`load.ts`)에서 요청마다 필요한 것만 뽑아 두고, 시계와 식별자 만들기는 인자로
// 받아 시험이 고정한다(pilot-portal 명세 "HTTP 요청 처리기와 서버").

import type { KeyObject } from "node:crypto";
import type { Assets } from "./assets.ts";
import type { Assurance } from "./config.ts";
import type { LoadedPortal } from "./load.ts";

export interface SiteContext {
  readonly name: string;
  readonly issuer: string;
  /** 사이트 파일의 그 사이트 `audience`. 토큰의 `aud` 가 된다. */
  readonly audience: string;
  readonly assurance: Assurance;
}

/** 요청 처리가 바깥에서 받는 둘. 서버는 실제 시계와 `randomUUID` 를, 시험은 고정한 값을 준다. */
export interface PortalSources {
  /** 지금. 에포크 밀리초다(`Date.now` 와 같다). */
  readonly now: () => number;
  /** 새 익명 식별자. 소문자 UUID v4 여야 한다. */
  readonly newAnonymousId: () => string;
}

export interface PortalContext extends PortalSources {
  readonly publicOrigin: string;
  readonly kid: string;
  /** 시작 때 읽어 둔 개인 키. 모든 사이트의 토큰에 서명한다. */
  readonly privateKey: KeyObject;
  readonly sites: readonly SiteContext[];
  /** 시작 때 지어 둔 페이지와 정적 파일과 글꼴 표. 요청 처리 중에는 파일을 읽지 않는다. */
  readonly assets: Assets;
}

/**
 * 시작 검사를 지난 결과의 사이트마다 사이트 파일에서 발급자로 `audience` 를 찾아 붙인다. 시작 검사가 발급자가 사이트 파일에
 * 있음을 이미 보았으므로 못 찾으면 시작 검사가 어긋난 것이라, 서버가 뜨기 전에 오류로 멈춘다.
 */
export function portalContext(
  loaded: LoadedPortal,
  assets: Assets,
  sources: PortalSources,
): PortalContext {
  const { config, privateKey, siteFile } = loaded;
  const sites = config.sites.map((site): SiteContext => {
    const entry = siteFile.sites.find((candidate) => candidate.issuer === site.issuer);
    if (entry === undefined) {
      throw new Error(`사이트 ${site.name} 의 발급자가 사이트 파일에 없다. 시작 검사가 어긋났다.`);
    }
    return {
      name: site.name,
      issuer: site.issuer,
      audience: entry.audience,
      assurance: site.assurance,
    };
  });
  return {
    publicOrigin: config.publicOrigin,
    kid: config.kid,
    privateKey,
    sites,
    assets,
    now: sources.now,
    newAnonymousId: sources.newAnonymousId,
  };
}
