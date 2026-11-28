import { expect, test } from "vitest";
import { lastRevision, PRODUCT_VERSIONS, productRevision, WIDGET_VERSIONS } from "./migrations.ts";

const file = (revision: string, down: string): string =>
  `"""설명."""\n\nrevision: str = "${revision}"\ndown_revision: str | None = ${down}\n`;

test("마이그레이션 파일들의 판 번호 가운데 가장 큰 것을 마지막 판으로 읽는다", () => {
  expect(lastRevision([file("0002", '"0001"'), file("0010", '"0002"'), file("0001", "None")])).toBe(
    "0010",
  );
});

test("down_revision 줄의 번호는 판 번호로 읽지 않는다", () => {
  expect(lastRevision([file("0001", '"0009"')])).toBe("0001");
});

test("마이그레이션 파일이 하나도 없으면 던진다", () => {
  expect(() => lastRevision([])).toThrow(/하나도 없다/u);
});

test("판 번호 줄이 없는 파일이 있으면 던진다", () => {
  expect(() => lastRevision([file("0001", "None"), '"""판이 없다."""\n'])).toThrow(/판 번호/u);
});

test("이 저장소의 제품 마이그레이션 폴더에서 네 자리 판 번호를 읽는다", () => {
  expect(productRevision()).toMatch(/^[0-9]{4}$/u);
});

test("위젯 관리 서버의 마이그레이션 폴더에서도 네 자리 판 번호를 읽는다", () => {
  expect(WIDGET_VERSIONS).not.toBe(PRODUCT_VERSIONS);
  expect(WIDGET_VERSIONS).toMatch(/widget_admin[\\/]migrations[\\/]versions$/u);
  expect(productRevision(WIDGET_VERSIONS)).toMatch(/^[0-9]{4}$/u);
});

test("폴더가 없으면 던져 읽지 못한 채 지나가지 않는다", () => {
  expect(() => productRevision(`${WIDGET_VERSIONS}-없는-폴더`)).toThrow();
});
