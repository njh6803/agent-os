/// <reference path="./lucide-icons.d.ts" />
// 아이콘(재탐색 디자인 파일 2.9). Lucide 의 모양을 크기와 상관없이 화면의 1.5px 선으로 그리고 색은 놓인 곳의 글자
// 색이다. `nonScalingStroke` 가 그린 요소마다 `vector-effect: non-scaling-stroke` 를 달아 `strokeWidth` 가 화면의 px
// 가 된다. `absoluteStrokeWidth` 는 `size` prop 으로 나누는데 여기는 크기를 클래스로 주어 맞지 않는다(lucide-react
// 1.51.0 의 `dist/esm/shared/src/build/buildLucideIconNode.mjs`).
// import 는 아이콘 하나짜리 서브패스다(ADR 0024. 세트를 통째로 import 하는 것은 ESLint 가 막는다).
import Check from "lucide-react/dist/esm/icons/check";
import CircleCheck from "lucide-react/dist/esm/icons/circle-check";
import CircleMinus from "lucide-react/dist/esm/icons/circle-minus";
import CirclePause from "lucide-react/dist/esm/icons/circle-pause";
import CircleX from "lucide-react/dist/esm/icons/circle-x";
import Ellipsis from "lucide-react/dist/esm/icons/ellipsis";
import Info from "lucide-react/dist/esm/icons/info";
import List from "lucide-react/dist/esm/icons/list";
import LoaderCircle from "lucide-react/dist/esm/icons/loader-circle";
import Menu from "lucide-react/dist/esm/icons/menu";
import Plug from "lucide-react/dist/esm/icons/plug";
import Search from "lucide-react/dist/esm/icons/search";
import Send from "lucide-react/dist/esm/icons/send";
import ShieldCheck from "lucide-react/dist/esm/icons/shield-check";
import TriangleAlert from "lucide-react/dist/esm/icons/triangle-alert";
import Wrench from "lucide-react/dist/esm/icons/wrench";
import X from "lucide-react/dist/esm/icons/x";
import type { NativeProps } from "../../props";

const GLYPHS = {
  send: Send,
  x: X,
  check: Check,
  "shield-check": ShieldCheck,
  "circle-pause": CirclePause,
  "circle-check": CircleCheck,
  "circle-x": CircleX,
  "circle-minus": CircleMinus,
  "triangle-alert": TriangleAlert,
  info: Info,
  wrench: Wrench,
  plug: Plug,
  list: List,
  search: Search,
  menu: Menu,
  ellipsis: Ellipsis,
};

/** 디자인 파일의 아이콘 열여섯. 불러오는 중의 `loader-circle` 은 컴포넌트 안에서만 쓰고 여기 들지 않는다. */
export type IconName = keyof typeof GLYPHS;
export const ICON_NAMES = Object.keys(GLYPHS).filter((name): name is IconName => name in GLYPHS);

export const ICON_SIZES = ["14", "16", "20"] as const;
export type IconSize = (typeof ICON_SIZES)[number];

const SIZE_CLASS = {
  "14": "size-icon-xs",
  "16": "size-icon-s",
  "20": "size-icon-m",
} satisfies Record<IconSize, string>;

// 화면의 px(디자인 파일의 `icon-stroke`). 그린 요소에 `nonScalingStroke` 와 함께 둔다.
const STROKE_WIDTH = 1.5;

interface IconOwnProps {
  name: IconName;
  /** px. 기본 20. */
  size?: IconSize;
  /** null 이면 화면 읽기 프로그램에서 숨는다(글자 옆의 아이콘). 있으면 그 이름의 그림이다. */
  label?: string | null;
}

export type IconProps = IconOwnProps &
  NativeProps<"svg", keyof IconOwnProps | "children" | "role" | "aria-label" | "aria-hidden">;

export function Icon({ name, size = "20", label = null, ...rest }: IconProps) {
  const Glyph = GLYPHS[name];
  const naming = label === null ? { "aria-hidden": true } : { role: "img", "aria-label": label };
  return (
    <Glyph
      {...rest}
      {...naming}
      className={`${SIZE_CLASS[size]} shrink-0`}
      strokeWidth={STROKE_WIDTH}
      nonScalingStroke
    />
  );
}

/**
 * 불러오는 중의 도는 표시. 아이콘과 같은 선이고 놓인 곳의 글자 색이며 움직임 줄이기 설정이면 멈춘다. 컴포넌트 안에서만
 * 쓴다.
 */
export function Spinner({ size }: { size: IconSize }) {
  return (
    <LoaderCircle
      aria-hidden
      className={`${SIZE_CLASS[size]} shrink-0 animate-spin motion-reduce:animate-none`}
      strokeWidth={STROKE_WIDTH}
      nonScalingStroke
    />
  );
}
