// 링크 주소 판정의 시험(answer-markdown 명세 "부품의 단위 시험"의 "주소 판정의 시험은 순수 함수로 따로 둔다"). DOM 이 필요
// 없어 node 프로젝트에서 돈다. 링크로 그려도 되는 주소는 URL 파서가 정규화한 주소로, 아니면 null 로 판정한다.
import { describe, expect, it } from "vitest";
import { linkHref } from "./link-url";

/** 링크 17가지(프로브 `shape-cases.mjs` 의 `LINKS`)가 부품에 넘기는 주소와 판정. 마크다운이 풀어 낸 뒤의 글이다(`l12` 는 GFM 이 이메일로 읽어 `mailto:` 를 붙인 꼴). */
const LINK_ADDRESSES: readonly { id: string; address: string; href: string | null }[] = [
  { id: "l01-userinfo-host", address: "https://www.law.go.kr@evil.example/login", href: null },
  { id: "l02-user-password", address: "https://user:pw@host.example/", href: null },
  { id: "l03-user-only", address: "https://user@host.example/", href: null },
  { id: "l04-empty-userinfo", address: "https://@host.example/", href: "https://host.example/" },
  { id: "l05-empty-password", address: "https://www.law.go.kr:@evil.example/", href: null },
  { id: "l06-angle-autolink", address: "https://www.law.go.kr@evil.example/", href: null },
  { id: "l07-bare-autolink", address: "https://shop.example.com@phish.example/refund", href: null },
  { id: "l08-escaped-at", address: "https://www.law.go.kr@evil.example/", href: null },
  { id: "l09-uppercase", address: "HTTPS://USER@EXAMPLE.COM/", href: null },
  { id: "l10-percent-encoded-at", address: "https://www.law.go.kr%40evil.example/", href: null },
  { id: "l11-normal", address: "https://www.law.go.kr/", href: "https://www.law.go.kr/" },
  { id: "l12-www-at", address: "mailto:www.law.go.kr@evil.example", href: null },
  { id: "l13-email", address: "mailto:help@example.com", href: null },
  { id: "l14-title", address: "https://example.com/", href: "https://example.com/" },
  { id: "l15-reference", address: "https://u:p@host.example/", href: null },
  {
    id: "l16-http-query",
    address: "http://example.com/a?b=1&c=2",
    href: "http://example.com/a?b=1&c=2",
  },
  {
    id: "l17-userinfo-in-path",
    address: "https://example.com/@user",
    href: "https://example.com/@user",
  },
];

describe("링크 주소 판정", () => {
  it("링크 17가지의 주소를 사례 파일의 판정대로 가른다", () => {
    expect(LINK_ADDRESSES).toHaveLength(17);
    for (const { id, address, href } of LINK_ADDRESSES) {
      expect({ id, href: linkHref(address) }).toEqual({ id, href });
    }
  });

  it("http와 https의 절대 주소만 링크로 판정한다", () => {
    expect(linkHref("http://example.com/")).toBe("http://example.com/");
    expect(linkHref("https://example.com/a/b?c=d#e")).toBe("https://example.com/a/b?c=d#e");
    expect(linkHref("https://example.com:8080/a")).toBe("https://example.com:8080/a");
  });

  it("파서가 정규화한 주소를 돌려준다", () => {
    expect(linkHref("HTTPS://EXAMPLE.COM/PATH")).toBe("https://example.com/PATH");
    expect(linkHref("HtTp://Example.COM")).toBe("http://example.com/");
    expect(linkHref("https://example.com/법령/민법")).toBe(
      "https://example.com/%EB%B2%95%EB%A0%B9/%EB%AF%BC%EB%B2%95",
    );
  });

  describe("스킴이 http나 https가 아닌 주소", () => {
    it.each([
      "javascript:alert(1)",
      "data:text/html,<script>alert(1)</script>",
      "vbscript:msgbox(1)",
      "mailto:a@example.com",
      "tel:+82-2-0000-0000",
      "file:///C:/Windows/win.ini",
      "blob:https://evil.example/1",
      "ftp://evil.example/",
    ])("%s 는 링크가 아니다", (address) => {
      expect(linkHref(address)).toBeNull();
    });

    it("대문자 스킴도 같은 규칙으로 가른다", () => {
      expect(linkHref("JAVASCRIPT:alert(1)")).toBeNull();
      expect(linkHref("JaVaScRiPt:alert(1)")).toBeNull();
      expect(linkHref("DATA:text/html,a")).toBeNull();
      expect(linkHref("HTTP://EXAMPLE.COM/")).toBe("http://example.com/");
    });
  });

  describe("공백과 제어 글자가 섞인 스킴", () => {
    it.each([
      ["스킴 가운데 탭", "java\tscript:alert(1)"],
      ["스킴 가운데 줄바꿈", "java\nscript:alert(1)"],
      ["앞에 공백", "  javascript:alert(1)"],
      ["앞에 제어 글자", "\u0001javascript:alert(1)"],
      ["앞에 널 글자 뒤 공백", "\u0000 javascript:alert(1)"],
      ["뒤에 공백이 붙은 data", "data:text/html,a "],
    ])("%s 는 링크가 아니다", (_name, address) => {
      expect(linkHref(address)).toBeNull();
    });

    it("앞뒤 공백과 글자 사이의 탭은 파서가 떼어 낸 주소로 돌려준다", () => {
      expect(linkHref(" https://example.com/ ")).toBe("https://example.com/");
      expect(linkHref("ht\ttps://example.com/")).toBe("https://example.com/");
    });

    it("호스트에 공백이 든 주소는 링크가 아니다", () => {
      expect(linkHref("https://exa mple.com/")).toBeNull();
    });
  });

  describe("사용자 정보가 든 주소", () => {
    it.each([
      ["사용자 이름", "https://user@host.example/"],
      ["사용자 이름과 비밀번호", "https://user:pw@host.example/"],
      ["비밀번호만", "https://:pw@host.example/"],
      ["빈 비밀번호", "https://user:@host.example/"],
      ["믿는 호스트 이름을 사용자 이름으로", "https://www.law.go.kr@evil.example/login"],
      ["퍼센트로 쓴 사용자 이름", "https://%75ser@host.example/"],
      ["골뱅이 둘", "https://@@host.example/"],
      ["http 스킴", "http://user:pw@host.example/"],
      ["대문자", "HTTPS://USER@EXAMPLE.COM/"],
    ])("%s 가 든 주소는 링크가 아니다", (_name, address) => {
      expect(linkHref(address)).toBeNull();
    });

    it("빈 사용자 정보는 파서가 없는 것으로 읽어 골뱅이 없는 주소로 돌려준다", () => {
      expect(linkHref("https://@host.example/")).toBe("https://host.example/");
    });

    it("경로와 질의에 든 골뱅이는 사용자 정보가 아니다", () => {
      expect(linkHref("https://example.com/@user")).toBe("https://example.com/@user");
      expect(linkHref("https://example.com/?u=a@b")).toBe("https://example.com/?u=a@b");
    });

    it("퍼센트로 쓴 골뱅이가 호스트에 든 주소는 링크가 아니다", () => {
      expect(linkHref("https://www.law.go.kr%40evil.example/")).toBeNull();
    });
  });

  describe("기준 주소 없이 풀리지 않는 주소", () => {
    it.each([
      ["프로토콜 상대 주소", "//evil.example/x"],
      ["경로 상대 주소", "/admin"],
      ["현재 폴더 상대 주소", "./a"],
      ["위 폴더 상대 주소", "../a"],
      ["조각", "#top"],
      ["질의", "?q=1"],
      ["스킴 없는 주소", "evil.example"],
      ["스킴 없는 www 주소", "www.law.go.kr"],
      ["스킴만 있는 주소", "https:"],
      ["빈 주소", ""],
      ["공백뿐인 주소", "   "],
    ])("%s 는 링크가 아니다", (_name, address) => {
      expect(linkHref(address)).toBeNull();
    });
  });
});
