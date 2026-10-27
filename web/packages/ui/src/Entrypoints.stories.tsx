// 진입점 일곱 가운데 브라우저에서 도는 여섯을 소비자처럼 패키지 이름으로 푸는 확인(design-system 명세 스토리 18). 일곱째
// `./visual` 은 `node:fs` 를 들이는 사진 비교 도구라 이 스토리가 불러올 수 없고, 그 이름 풀이는 위젯의 사진
// 비교(`web/apps/widget/visual/`)의 tsc 와 실행이 본다(web-widget 티켓 03). 상대 경로로 import 하는 테스트는
// `exports` 가 틀려도 초록이다. 패키지 안에서 자기 이름을 import 하면 Vite 와 TypeScript 가 앱과 같은 `exports` 맵으로
// 푼다(자기 참조. 루트 `web/package.json` 이 이 패키지를 들여 링크가 서기 전에도 풀렸다). 이름으로 푼 모듈과 상대 경로로
// 푼 모듈이 같은 파일인지 견준다. play 는 여섯 모두 Vite 의 해석을 본다. 이 파일의 타입 검사는 넷(`.`, `./testing`,
// `./storybook`, `./contrast`)만 TypeScript 의 해석을 본다. CSS 둘은 `?inline` 이 붙어 `exports` 키와 맞지 않고
// `.storybook/css-inline.d.ts` 의 와일드카드 선언으로 풀린다. `./contrast` 를 루트 설정(`nodenext`)과 Node 로 푸는 것은
// `web/tools/contrast-module.test.ts` 가 본다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import * as root from "@agent-os/ui";
import * as contrast from "@agent-os/ui/contrast";
import fontsCss from "@agent-os/ui/fonts.css?inline";
import * as storybook from "@agent-os/ui/storybook";
import * as testing from "@agent-os/ui/testing";
import themeCss from "@agent-os/ui/theme.css?inline";
import { expect } from "storybook/test";
import * as rootByPath from "./index";
import * as storybookByPath from "./storybook/preview";
import * as contrastByPath from "./styles/contrast";
import fontsByPath from "./styles/fonts.css?inline";
import themeByPath from "./styles/theme.css?inline";
import * as testingByPath from "./testing";

const meta = {
  title: "디자인 토큰/진입점",
  tags: ["judgment"],
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

function sameModule(byName: object, byPath: object): boolean {
  const names = Object.keys(byName).sort();
  return (
    names.length > 0 &&
    names.join() === Object.keys(byPath).sort().join() &&
    names.every((name) => Reflect.get(byName, name) === Reflect.get(byPath, name))
  );
}

export const ByName: Story = {
  name: "브라우저 진입점 여섯이 패키지 이름으로 풀리고 상대 경로의 그 파일과 같다",
  render: () => <p className="text-body">진입점</p>,
  play: async () => {
    await expect({
      root: sameModule(root, rootByPath),
      testing: sameModule(testing, testingByPath),
      storybook: sameModule(storybook, storybookByPath),
      contrast: sameModule(contrast, contrastByPath),
      theme: themeCss.length > 0 && themeCss === themeByPath,
      fonts: fontsCss.length > 0 && fontsCss === fontsByPath,
    }).toEqual({
      root: true,
      testing: true,
      storybook: true,
      contrast: true,
      theme: true,
      fonts: true,
    });
  },
};
