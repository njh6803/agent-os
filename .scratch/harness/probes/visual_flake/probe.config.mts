// 사진 비교 흔들림 프로브(harness 티켓 016)의 컨테이너 쪽 설정. 패키지의 사진 비교 설정을 그대로 들여(창, 배율, 지역,
// 워커 하나, 이미지 표지 검사, 브라우저 실행 인자) 시험 폴더와 산출물 자리만 바꾼다. run.mjs 가 띄운 컨테이너 안에서만
// 돈다. FLAKE_ARGS 가 `config` 면 패키지 설정의 launchOptions 를 그대로 쓰고(고친 뒤), `none` 이면 인자 없이(고치기 전),
// 그 밖이면 공백으로 갈라 launchOptions.args 로 쓴다.
import base from "/web/packages/ui/visual/playwright.config.ts";

const raw = process.env["FLAKE_ARGS"] ?? "config";
const use =
  raw === "config"
    ? base.use
    : { ...base.use, launchOptions: { args: raw === "none" ? [] : raw.split(" ").filter(Boolean) } };

export default {
  ...base,
  use,
  testDir: "/probe",
  testMatch: "flake.probe.mts",
  outputDir: "/out/test-results",
  reporter: "line",
  // 시험 하나가 스토리를 네 번 열고 사진을 여러 장 찍는다.
  timeout: 120_000,
};
