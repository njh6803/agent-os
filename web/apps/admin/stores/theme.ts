// 관리 화면의 테마(admin-style 명세 "설정 화면과 테마", ADR 0026 의 첫째 2026-10-12 이력). 운영자가 고른 테마는 문서
// 뿌리 `html` 의 `data-theme` 이고, 이 브라우저의 localStorage 에 테마 키의 글자 그대로 남는다. 속성이 없는 문서는 기본
// 테마(녹청)로 그려진다. 테마는 비밀이 아니어서 탭 사이에 나눠 가진다. 토큰과 다르다(stores/tokens.ts).
//
// 지금 테마의 원천은 `html` 의 속성 하나다. 화면은 그것을 읽고(`useTheme`), 고르기와 다른 탭과 되살리기는 그것을 쓴다.
// 쓰는 길은 모두 `apply` 를 지나 읽는 화면에 알린다. 첫 그림의 속성은 그리기 전 스크립트(public/theme.js)가 단다. 그
// 파일은 이 모듈을 import 하지 못해 키 목록과 저장 키를 따로 적는다. 그 스크립트의 단위 시험
// (stores/theme.prepaint.test.ts)이 이 모듈의 상수와 맞대어, `THEMES` 에 테마를 더하거나 저장 키를 바꾸고 스크립트를
// 고치지 않은 어긋남을 잡는다.

import { DEFAULT_THEME, THEMES, type ThemeKey } from "@agent-os/ui";
import { useLayoutEffect, useSyncExternalStore } from "react";

/** 고른 테마를 남기는 localStorage 키. 그리기 전 스크립트도 같은 키를 읽는다. */
export const THEME_STORAGE_KEY = "agent-os-admin-theme";

const listeners = new Set<() => void>();

function themeKeyOf(value: string | null): ThemeKey | null {
  return THEMES.find(({ key }) => key === value)?.key ?? null;
}

/** 문서 뿌리에 단 테마. 없거나 목록에 없으면 null 이다. */
function rootTheme(): ThemeKey | null {
  return themeKeyOf(document.documentElement.getAttribute("data-theme"));
}

/** 문서 뿌리의 테마를 바꾸고 읽는 화면에 알린다. null 이면 속성을 걷어 기본 테마로 그린다. */
function apply(theme: ThemeKey | null): void {
  const html = document.documentElement;
  if (theme === null) {
    html.removeAttribute("data-theme");
  } else {
    html.setAttribute("data-theme", theme);
  }
  for (const listener of listeners) {
    listener();
  }
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

/** 지금 그려지는 테마. 문서 뿌리에 속성이 없으면 기본 테마다. 서버가 그릴 때도 기본 테마다. */
export function useTheme(): ThemeKey {
  return useSyncExternalStore(
    subscribe,
    () => rootTheme() ?? DEFAULT_THEME,
    () => DEFAULT_THEME,
  );
}

/** 운영자가 고른 테마를 바로 그리고 이 브라우저에 남긴다. 기본 테마를 골라도 남긴다. */
export function chooseTheme(theme: ThemeKey): void {
  apply(theme);
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch {
    // 저장소를 막은 브라우저. 이 문서에서만 그 테마로 그린다. 쓰기만 실패하고 옛 저장 값이 읽히면(저장소가 가득 찼다)
    // 다음 화면이 마운트될 때 restoreStoredTheme 이 그 옛 값으로 되돌린다. 이 앱이 이 출처의 localStorage 에 적는 것은
    // 이 키 하나라 그 상태는 드물다고 본다(어림).
  }
}

/**
 * 같은 브라우저의 다른 탭이 저장 값을 바꾸면 따른다. 테마 키의 이벤트와 저장소 전체를 비운 이벤트(키가 없다)만 받는다.
 * 목록에 없는 값이 오거나 키가 지워졌으면 속성을 걷어 기본 테마로 그린다.
 */
function followOtherTab(event: StorageEvent): void {
  if (event.key !== null && event.key !== THEME_STORAGE_KEY) {
    return;
  }
  apply(event.key === null ? null : themeKeyOf(event.newValue));
}

/**
 * 하이드레이션이 실패해 React 가 문서 뿌리의 속성을 지웠으면 저장 값으로 다시 단다(명세 "하이드레이션이 실패하면
 * 되살린다"). dev 의 Strict Mode 가 다시 마운트하며 지운 것도 같은 길로 되살린다고 본다(설치본 Next 가이드를 읽었다.
 * dev 에서는 재지 않았다). 저장 값이 목록에 없거나 저장소를 읽지 못하면
 * 그리기 전 스크립트처럼 아무것도 바꾸지 않는다. 평소에는 저장 값과 속성이 같아 아무것도 하지 않는다.
 */
function restoreStoredTheme(): void {
  let stored: ThemeKey | null;
  try {
    stored = themeKeyOf(localStorage.getItem(THEME_STORAGE_KEY));
  } catch {
    return;
  }
  if (stored !== null && stored !== rootTheme()) {
    apply(stored);
  }
}

/**
 * 모든 화면이 지나는 공통 컴포넌트(pages/AdminScreen)가 부른다. 마운트될 때 저장 값으로 되살리고, 마운트된 동안 다른 탭의
 * 테마를 따른다. 그리기 전에 되살리도록 `useLayoutEffect` 다(설치본 Next 가이드 "Preventing Flash"의 "Re-applying
 * attributes in development").
 */
export function useStoredTheme(): void {
  useLayoutEffect(() => {
    restoreStoredTheme();
    window.addEventListener("storage", followOtherTab);
    return () => {
      window.removeEventListener("storage", followOtherTab);
    };
  }, []);
}
