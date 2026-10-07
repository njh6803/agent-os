// 진입점 다섯을 소비자처럼 패키지 이름으로 푸는 확인(design-system 명세 스토리 18). 상대 경로로 import 하는 테스트는
// `exports` 가 틀려도 초록이다. 패키지 안에서 자기 이름을 import 하면 Vite 와 TypeScript 가 앱과 같은 `exports` 맵으로
// 푼다(자기 참조. 워크스페이스 링크가 없는 자리에서 풀렸다). 이름으로 푼 모듈과 상대 경로로 푼 모듈이 같은 파일인지
// 견준다. play 는 다섯 모두 Vite 의 해석을 본다. 이 파일의 타입 검사는 셋(`.`, `./testing`, `./storybook`)만 TypeScript 의
// 해석을 본다. CSS 둘은 `?inline` 이 붙어 `exports` 키와 맞지 않고 `.storybook/css-inline.d.ts` 의 와일드카드 선언으로 풀린다.
import type { Meta, StoryObj } from "@storybook/react-vite";
import * as root from "@agent-os/ui";
import fontsCss from "@agent-os/ui/fonts.css?inline";
import * as storybook from "@agent-os/ui/storybook";
import * as testing from "@agent-os/ui/testing";
import themeCss from "@agent-os/ui/theme.css?inline";
import { expect } from "storybook/test";
import * as rootByPath from "./index";
import * as storybookByPath from "./storybook/preview";
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
  name: "진입점 다섯이 패키지 이름으로 풀리고 상대 경로의 그 파일과 같다",
  render: () => <p className="text-body">진입점</p>,
  play: async () => {
    await expect({
      root: sameModule(root, rootByPath),
      testing: sameModule(testing, testingByPath),
      storybook: sameModule(storybook, storybookByPath),
      theme: themeCss.length > 0 && themeCss === themeByPath,
      fonts: fontsCss.length > 0 && fontsCss === fontsByPath,
    }).toEqual({ root: true, testing: true, storybook: true, theme: true, fonts: true });
  },
};
