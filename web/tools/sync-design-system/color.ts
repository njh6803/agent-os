/**
 * 색 변환. 들이기가 웹의 색 값을 hex 로 바꾸고, 명암비에 걸린 원색의 가장 가까운 통과 값을 OKLCH 밝기나 투명도로 찾을 때
 * 쓴다(design-reverse-sync 명세 "hex 가 아닌 값"과 "가장 가까운 값"의 2026-10-22 주석). 의존성을 더하지 않고 여기서
 * 계산한다. sRGB 의 전달 함수와 색 함수의 문법은 CSS Color 4(https://www.w3.org/TR/css-color-4/)다. OKLab 과 선형 sRGB
 * 사이의 행렬은 Björn Ottosson 의 글(https://bottosson.github.io/posts/oklab/)이 낸 선형 sRGB 직행 행렬이다. CSS Color 4 의
 * 표본 코드는 XYZ 를 거치는 행렬을 쓰고 그 글을 참고 문헌으로 든다.
 *
 * - 읽는 것: hex(3·4·6·8 자리), `rgb()`·`rgba()`·`hsl()`·`hsla()`·`oklab()`·`oklch()` 의 공백 꼴(값 셋과 `/` 뒤의 투명도),
 *   `rgb()`·`rgba()`·`hsl()`·`hsla()` 의 쉼표 꼴(값 셋이나 넷, `none` 없이), `none`, 백분율, 각도 단위
 *   (`deg`·`rad`·`grad`·`turn`). `lab()`·`lch()`·`color()`, 색 이름, 다른 토큰을 가리키는 값은 읽지 않는다.
 * - sRGB 밖: 읽은 값의 채널이 0~1 밖이어도 그대로 둔다. hex 는 채널마다 0~255 의 정수로 반올림하므로, 반올림해 0~255 에
 *   드는 값(반 단계 안쪽)을 sRGB 안으로 본다. 그보다 밖이면 hex 가 없다. `rgb(300 0 0)` 처럼 CSS 가 읽을 때 자르는 값도
 *   자르지 않고 밖으로 본다. CSS 가 자르는 값 가운데 투명도(0~1), `hsl()` 의 음수 채도(0), OKLab·OKLCH 의 밝기(0~1)와
 *   OKLCH 의 음수 채도(0)는 CSS 처럼 자른다.
 *
 * 못 보는 것: 쉼표 꼴에서 CSS 가 받지 않는 값의 꼴(`rgb(100%, 0, 0)` 처럼 백분율과 수를 섞은 것, `hsl(120, 100, 50)` 처럼
 * 채도·밝기가 백분율이 아닌 것)도 여기서는 읽는다.
 */

/** 감마로 부호화한 sRGB 의 채널(0~1 이 sRGB 안)과 투명도(0~1). */
export interface Srgb {
  readonly red: number;
  readonly green: number;
  readonly blue: number;
  readonly alpha: number;
}

/** OKLCH. 색상은 도다. `toOklch` 는 0 이상 360 미만으로 내고, `readOklch` 는 `oklch()` 에 적힌 값 그대로다. */
export interface Oklch {
  readonly lightness: number;
  readonly chroma: number;
  readonly hue: number;
  readonly alpha: number;
}

/** 가장 가까운 통과 값. `steps` 는 옮긴 단계(밝거나 불투명한 쪽이 양수)다. */
export interface Nearest {
  readonly steps: number;
  readonly value: string;
}

type Triple = readonly [number, number, number];

/** 색 함수를 이름과 인자로 푼 것. */
interface ColorFunction {
  readonly name: string;
  readonly parts: readonly [string, string, string];
  readonly alpha: number;
}

const LIGHTNESS_STEP = 0.001;
const LIGHTNESS_STEPS = 1000;
const ALPHA_STEPS = 255;
const LEGACY = new Set(["rgb", "rgba", "hsl", "hsla"]);
const HEX = /^#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/i;
const FUNCTION = /^(rgba?|hsla?|oklab|oklch)\((.*)\)$/i;
const NUMBER = /^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i;
const PERCENT = /^([+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?)%$/i;
const ANGLE = /^([+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?)(deg|rad|grad|turn)?$/i;

const ANGLE_DEGREES: Readonly<Record<string, number>> = {
  deg: 1,
  rad: 180 / Math.PI,
  grad: 0.9,
  turn: 360,
};

/** 3·4 자리 hex 를 6·8 자리로 펴고 소문자로 낸다. hex 가 아니면 undefined. 8 자리는 투명도가 ff 여도 그대로다. */
export function expandHex(text: string): string | undefined {
  const found = HEX.exec(text.trim());
  if (found === null) {
    return undefined;
  }
  const digits = (found[1] ?? "").toLowerCase();
  return digits.length <= 4 ? `#${digits.replace(/./g, (digit) => digit + digit)}` : `#${digits}`;
}

function clamp(value: number, low: number, high: number): number {
  return Math.min(high, Math.max(low, value));
}

/** 성분 하나. 백분율은 `percent` 를 곱하고, 수는 `number` 를 곱한다. `none` 은 0 이다. */
function component(text: string, percent: number, number: number): number | undefined {
  if (text.toLowerCase() === "none") {
    return 0;
  }
  const ratio = PERCENT.exec(text);
  if (ratio !== null) {
    return (Number(ratio[1]) / 100) * percent;
  }
  return NUMBER.test(text) ? Number(text) * number : undefined;
}

/** 색상. 단위가 없으면 도다. */
function hueOf(text: string): number | undefined {
  if (text.toLowerCase() === "none") {
    return 0;
  }
  const found = ANGLE.exec(text);
  if (found === null) {
    return undefined;
  }
  return Number(found[1]) * (ANGLE_DEGREES[(found[2] ?? "deg").toLowerCase()] ?? 1);
}

function alphaOf(text: string | undefined): number | undefined {
  if (text === undefined) {
    return 1;
  }
  const value = component(text, 1, 1);
  return value === undefined ? undefined : clamp(value, 0, 1);
}

/** 쉼표 꼴의 인자. CSS 가 이 꼴을 받는 `rgb`·`rgba`·`hsl`·`hsla` 만이고 `none` 을 받지 않는다. */
function commaParts(name: string, text: string): string[] | undefined {
  const parts = text.split(",").map((part) => part.trim());
  return LEGACY.has(name) && !parts.some((part) => part.toLowerCase() === "none")
    ? parts
    : undefined;
}

/** 공백 꼴의 인자. 값 셋과 `/` 뒤의 투명도다. */
function spaceParts(text: string): string[] | undefined {
  const [main = "", alpha, extra] = text.split("/").map((part) => part.trim());
  const parts = main.split(/\s+/).filter((part) => part !== "");
  if (extra !== undefined || alpha === "" || parts.length !== 3) {
    return undefined;
  }
  return alpha === undefined ? parts : [...parts, alpha];
}

/** 함수의 인자. 쉼표 꼴은 셋이나 넷, 공백 꼴은 셋과 `/` 뒤의 투명도다. 꼴이 어긋나면 undefined. */
function argumentsOf(
  name: string,
  body: string,
): { readonly parts: readonly [string, string, string]; readonly alpha?: string } | undefined {
  const text = body.trim();
  const listed = text.includes(",") ? commaParts(name, text) : spaceParts(text);
  if (listed === undefined || listed.some((part) => part === "" || /\s/.test(part))) {
    return undefined;
  }
  const [first, second, third, alpha, extra] = listed;
  if (first === undefined || second === undefined || third === undefined || extra !== undefined) {
    return undefined;
  }
  return alpha === undefined
    ? { parts: [first, second, third] }
    : { parts: [first, second, third], alpha };
}

function hslToSrgb(hue: number, saturation: number, light: number): Triple {
  const turned = ((hue % 360) + 360) % 360;
  const amount = saturation * Math.min(light, 1 - light);
  const channel = (offset: number): number => {
    const k = (offset + turned / 30) % 12;
    return light - amount * Math.max(-1, Math.min(k - 3, 9 - k, 1));
  };
  return [channel(0), channel(8), channel(4)];
}

function toLinear(channel: number): number {
  const size = Math.abs(channel);
  const linear = size <= 0.04045 ? size / 12.92 : ((size + 0.055) / 1.055) ** 2.4;
  return Math.sign(channel) * linear;
}

function toGamma(channel: number): number {
  const size = Math.abs(channel);
  const gamma = size <= 0.0031308 ? 12.92 * size : 1.055 * size ** (1 / 2.4) - 0.055;
  return Math.sign(channel) * gamma;
}

function oklabToSrgb([lightness, a, b]: Triple): Triple {
  const l = (lightness + 0.3963377774 * a + 0.2158037573 * b) ** 3;
  const m = (lightness - 0.1055613458 * a - 0.0638541728 * b) ** 3;
  const s = (lightness - 0.0894841775 * a - 1.291485548 * b) ** 3;
  return [
    toGamma(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
    toGamma(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
    toGamma(-0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s),
  ];
}

function srgbToOklab(color: Srgb): Triple {
  const red = toLinear(color.red);
  const green = toLinear(color.green);
  const blue = toLinear(color.blue);
  const l = Math.cbrt(0.4122214708 * red + 0.5363325363 * green + 0.0514459929 * blue);
  const m = Math.cbrt(0.2119034982 * red + 0.6806995451 * green + 0.1073969566 * blue);
  const s = Math.cbrt(0.0883024619 * red + 0.2817188376 * green + 0.6299787005 * blue);
  return [
    0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s,
    1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s,
    0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s,
  ];
}

function srgb([red, green, blue]: Triple, alpha: number): Srgb {
  return { red, green, blue, alpha };
}

/** `oklch()` 의 인자. 밝기는 0~1 로, 채도는 0 이상으로 자른다. */
function oklchOf(parts: readonly [string, string, string], alpha: number): Oklch | undefined {
  const lightness = component(parts[0], 1, 1);
  const chroma = component(parts[1], 0.4, 1);
  const hue = hueOf(parts[2]);
  return lightness === undefined || chroma === undefined || hue === undefined
    ? undefined
    : { lightness: clamp(lightness, 0, 1), chroma: Math.max(0, chroma), hue, alpha };
}

/** 색 함수를 이름(소문자)과 인자로 푼다. 색 함수가 아니거나 인자의 꼴이 어긋나면 undefined. */
function colorFunction(text: string): ColorFunction | undefined {
  const found = FUNCTION.exec(text.trim());
  if (found === null) {
    return undefined;
  }
  const name = (found[1] ?? "").toLowerCase();
  const parsed = argumentsOf(name, found[2] ?? "");
  const alpha = alphaOf(parsed?.alpha);
  return parsed === undefined || alpha === undefined
    ? undefined
    : { name, parts: parsed.parts, alpha };
}

function readFunction({ name, parts, alpha }: ColorFunction): Srgb | undefined {
  const [first, second, third] = parts;
  if (name === "rgb" || name === "rgba") {
    const channels = [first, second, third].map((part) => component(part, 1, 1 / 255));
    const [red, green, blue] = channels;
    return red === undefined || green === undefined || blue === undefined
      ? undefined
      : srgb([red, green, blue], alpha);
  }
  if (name === "hsl" || name === "hsla") {
    const hue = hueOf(first);
    const saturation = component(second, 1, 1 / 100);
    const light = component(third, 1, 1 / 100);
    return hue === undefined || saturation === undefined || light === undefined
      ? undefined
      : srgb(hslToSrgb(hue, Math.max(0, saturation), light), alpha);
  }
  if (name === "oklab") {
    const lightness = component(first, 1, 1);
    const a = component(second, 0.4, 1);
    const b = component(third, 0.4, 1);
    return lightness === undefined || a === undefined || b === undefined
      ? undefined
      : srgb(oklabToSrgb([clamp(lightness, 0, 1), a, b]), alpha);
  }
  const exact = oklchOf(parts, alpha);
  return exact === undefined ? undefined : fromOklch(exact);
}

/** 색 값을 sRGB 로 읽는다. 읽지 못하거나 읽지 않는 꼴(다른 색 공간, 색 이름, 가리키는 값)이면 undefined. */
export function readColor(text: string): Srgb | undefined {
  const trimmed = text.trim();
  const hex = expandHex(trimmed);
  if (hex !== undefined) {
    const byte = (at: number): number => Number.parseInt(hex.slice(at, at + 2), 16) / 255;
    return srgb([byte(1), byte(3), byte(5)], hex.length === 9 ? byte(7) : 1);
  }
  const parsed = colorFunction(trimmed);
  return parsed === undefined ? undefined : readFunction(parsed);
}

/**
 * sRGB 안의 색이면 소문자 hex 를 낸다. 투명도를 반올림한 바이트가 ff 면 6 자리, 아니면 8 자리다. 채널을 반올림해
 * 0~255 에 들지 않으면 sRGB 밖이라 undefined 다.
 */
export function toHex(color: Srgb): string | undefined {
  const bytes = [color.red, color.green, color.blue].map((channel) => channel * 255);
  if (bytes.some((byte) => !Number.isFinite(byte) || byte < -0.5 || byte >= 255.5)) {
    return undefined;
  }
  const alpha = Math.round(clamp(color.alpha, 0, 1) * 255);
  const digits = [
    ...bytes.map((byte) => Math.max(0, Math.round(byte))),
    ...(alpha === 255 ? [] : [alpha]),
  ];
  return `#${digits.map((byte) => byte.toString(16).padStart(2, "0")).join("")}`;
}

/**
 * 색 값을 OKLCH 로 읽는다. `oklch()` 는 적힌 값 그대로이고(sRGB 를 거치지 않는다), 다른 꼴은 sRGB 로 읽어 바꾼다.
 * 읽지 못하면 undefined.
 */
export function readOklch(text: string): Oklch | undefined {
  const parsed = colorFunction(text);
  if (parsed?.name === "oklch") {
    return oklchOf(parsed.parts, parsed.alpha);
  }
  const color = readColor(text);
  return color === undefined ? undefined : toOklch(color);
}

export function toOklch(color: Srgb): Oklch {
  const [lightness, a, b] = srgbToOklab(color);
  const degrees = (Math.atan2(b, a) * 180) / Math.PI;
  return {
    lightness,
    chroma: Math.hypot(a, b),
    hue: degrees < 0 ? degrees + 360 : degrees,
    alpha: color.alpha,
  };
}

export function fromOklch(color: Oklch): Srgb {
  const radians = (color.hue * Math.PI) / 180;
  return srgb(
    oklabToSrgb([
      color.lightness,
      color.chroma * Math.cos(radians),
      color.chroma * Math.sin(radians),
    ]),
    color.alpha,
  );
}

/**
 * OKLCH 밝기를 0.001 씩 양쪽으로 옮겨 sRGB 안의 hex 가운데 처음 `passes` 를 지나는 것. 밝기 차이가 같으면 밝은 쪽이
 * 먼저다. 밝기는 0~1 안에서만 옮긴다. 없으면 undefined.
 */
export function nearestByLightness(
  origin: Oklch,
  passes: (hex: string) => boolean,
): Nearest | undefined {
  for (let step = 1; step <= LIGHTNESS_STEPS; step += 1) {
    for (const direction of [1, -1]) {
      const lightness = origin.lightness + direction * step * LIGHTNESS_STEP;
      if (lightness < 0 || lightness > 1) {
        continue;
      }
      const hex = toHex(fromOklch({ ...origin, lightness }));
      if (hex !== undefined && passes(hex)) {
        return { steps: direction * step, value: hex };
      }
    }
  }
  return undefined;
}

/**
 * `#rrggbbaa` 의 색을 두고 투명도를 1/255 씩 양쪽으로 옮겨 처음 `passes` 를 지나는 hex. 차이가 같으면 투명한 쪽이
 * 먼저다. 불투명(ff)에 닿으면 6 자리로 낸다. 없으면 undefined.
 */
export function nearestByAlpha(hex: string, passes: (hex: string) => boolean): Nearest | undefined {
  const color = hex.slice(0, 7);
  const start = Number.parseInt(hex.slice(7, 9), 16);
  for (let step = 1; step <= ALPHA_STEPS; step += 1) {
    for (const direction of [-1, 1]) {
      const alpha = start + direction * step;
      if (alpha < 0 || alpha > 255) {
        continue;
      }
      const candidate = alpha === 255 ? color : `${color}${alpha.toString(16).padStart(2, "0")}`;
      if (passes(candidate)) {
        return { steps: direction * step, value: candidate };
      }
    }
  }
  return undefined;
}
