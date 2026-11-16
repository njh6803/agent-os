// 미리보기를 "보기만 하는 그림"으로 가렸을 때, 실제 브라우저에서 Tab 이 위젯 안에 드는지와 접근성 트리에 무엇이 남는지를
// 본다(README "미리보기를 그림으로 가렸을 때").
//
// 왜 따로 있나. 관리 화면의 스토리 시험(play)은 같은 것을 흉내로 본다. `userEvent.tab()` 은 다음 요소를 스스로 고르며
// `inert` 를 보지 않고, 역할로 찾는 testing-library 도 `inert` 를 보지 않는다(스토리 파일의 주석이 읽은 자리를 적는다).
// 그래서 `inert` 갈래에서 "Tab 이 위젯을 건너 다음 단추에 닿는다"와 "위젯의 단추가 접근성 트리에 없다"는 흉내로는 보이지
// 않는다. 이 스크립트는 지은 Storybook(`web/apps/admin/storybook-static`)을 chromium 으로 열어 키보드의 Tab 을 실제로
// 누르고(`page.keyboard.press`), CDP `Accessibility.getFullAXTree` 가 낸 트리에서 무시되지 않은 노드를 센다.
//
// 회차는 스토리 넷과 폭 둘의 곱 여덟이다. 회차마다 위젯이 눈에 그려졌다는 표지(위젯의 `main` 이 `overflow-y: auto` 이고
// 크기가 0 이 아니다, 제목의 글자 크기가 15px 다)를 먼저 본다. 표지가 없는 회차는 측정이 아니라고 세고, 그런 회차가
// 있으면 2 로 끝난다. 기대와 다른 회차가 있으면 1 로 끝난다.
//
// 트리는 회차마다 두 번 읽는다. 처음은 위젯이 포커스를 한 번도 받지 않은 때다. 정적 빌드도 스토리의 play 를 돌리고 그
// play 가 흉내 Tab 으로 `element.focus()` 를 부르므로, 페이지가 뜨기 전에 `HTMLElement.prototype.focus` 를 빈 함수로
// 바꿔 둔다(키보드의 Tab 은 이 메서드를 지나지 않는다). 두 번째는 실제 Tab 이 위젯 안에 처음 든 때이고, 한 번도 들지
// 않았으면 Tab 을 다 누른 뒤다. chromium 은 포커스가 든 요소의 조상에 단 `aria-hidden` 을 무시하므로(첫 실행에서
// `shielded-hidden` 의 트리에 위젯이 통째로 나왔다) 둘을 갈라 읽는다. 그때 콘솔에 뜨는 `aria-hidden` 경고도 센다.
//
// 대조는 스토리 둘이다. 가리지 않은 `in-admin-frame` 에서는 Tab 이 위젯 안에 들고 위젯의 단추가 트리에 있어야 하고,
// `aria-hidden` 만 단 `shielded-hidden` 에서는 Tab 이 위젯 안에 들어야 한다. 그래야 다른 갈래의 "들지 않는다"와 "없다"가
// 이 스크립트가 포커스와 트리를 실제로 본 결과다.
//
// 마우스 회차는 따로다(README 의 같은 절 "휠과 클릭"). 미리보기의 높이를 넘는 내용을 준 스토리 넷(가리지 않은 것과 갈래
// A, 긴 안내와 긴 대화)과 폭 둘의 곱 여덟이다. 긴 안내는 위젯의 `main` 을, 긴 대화는 그 안의 대화 영역을 넘치게 한다.
// 회차마다 실제 마우스로 "새 대화"를 한 번 누르고(`page.mouse.click`) 임시 소비자가 센 처리기의 호출 횟수를 읽은 뒤,
// 페이지를 300px 내려 두고 마우스를 넘친 자리 위에 올려 휠을 200px 굴린다(`page.mouse.wheel`). 방향은 넘친 자리에
// 굴릴 데가 남은 쪽이다(긴 대화는 끝에 내려가 있어 위로, 긴 안내는 처음이라 아래로). 그 자리의 `scrollTop` 과 페이지의
// 스크롤 위치를 앞뒤로 읽는다. 페이지를 미리 내려 두는 것은 위젯이 받지 않은 휠이 어느 방향이든 페이지로 넘어갈 데가
// 있게 하려는 것이다. 표지는 넷이다. 위젯이 그려졌다, 그 자리가 넘쳤다(`scrollHeight` 가 `clientHeight` 보다 크다),
// 페이지가 앞뒤로 200px 넘게 굴릴 데가 있다, 문서가 click 과 wheel 이벤트를 실제로 받았다. 하나라도 없으면 측정이
// 아니라고 센다. 대조는 가리지 않은 두 스토리다. 거기서 처리기가 한 번 불리고 `scrollTop` 이 바뀌어야, 갈래 A 의 "불리지
// 않는다"와 "바뀌지 않는다"가 이 스크립트가 마우스를 실제로 움직인 결과다. 이 회차에서는 `focus()` 를 바꾸지 않는다.
//
// 쓰기: node preview_shield.mjs <web 디렉터리의 절대 경로>
//   먼저 `pnpm -C web/apps/admin run build-storybook` 으로 정적 빌드를 짓는다. 브라우저는 `browser.close()` 로 닫는다.
import { existsSync, statSync } from "node:fs";
import { createRequire } from "node:module";
import { isAbsolute, join, sep } from "node:path";

const [web] = process.argv.slice(2);
if (web === undefined || !isAbsolute(web)) {
  console.error("쓰기: node preview_shield.mjs <web 디렉터리의 절대 경로>");
  process.exit(2);
}
const site = join(web, "apps", "admin", "storybook-static");
if (!existsSync(join(site, "iframe.html"))) {
  console.error(`정적 빌드가 없다: ${site}. pnpm -C web/apps/admin run build-storybook 을 먼저 친다`);
  process.exit(2);
}
const { chromium } = createRequire(join(web, "package.json"))("playwright");

const ORIGIN = "http://storybook.invalid";
const LABEL = "미리보기, 저장하지 않은 값으로 그린 위젯";
// 관리 화면의 스토리 시험이 쓰는 창 두 벌(web/apps/admin/.storybook/viewports.ts).
const VIEWPORTS = [
  { name: "wide", width: 1280, height: 900 },
  { name: "narrow", width: 320, height: 640 },
];
// 위젯 밖에서 포커스를 받는 것은 "저장" 단추 하나, 위젯 안에서 받는 것은 가리지 않았을 때 넷이다. 한 바퀴가 여섯 번을
// 넘지 않으므로 열네 번이면 두 바퀴를 돈다.
const PRESSES = 14;

/**
 * 갈래마다의 기대. `inside` 는 Tab 이 위젯 안에 드는지, `images` 는 이름 붙은 그림의 수다. `before` 와 `after` 는 위젯이
 * 트리에 있는지다(처음과, 포커스가 위젯 안에 처음 든 때 또는 Tab 을 다 누른 뒤). 있으면 `main` 이 둘이고 "새 대화" 단추와
 * "주문 도우미" 제목이 있다. 없으면 `main` 이 하나, 단추는 "저장" 하나, 제목은 "사이트 고치기" 하나이고 입력창이 없다.
 * `shielded-hidden` 의 `after` 는 첫 실행의 결과를 본 뒤에 적었다(README 가 바꾼 기준으로 적는다).
 */
const BRANCHES = [
  { id: "in-admin-frame", inside: true, images: 0, before: true, after: true },
  { id: "shielded-both", inside: false, images: 1, before: false, after: false },
  { id: "shielded-inert", inside: false, images: 1, before: false, after: false },
  { id: "shielded-hidden", inside: true, images: 1, before: false, after: true },
];

/**
 * 마우스 회차의 스토리와 기대. `scroller` 는 넘치는 자리(감싼 요소 안에서 찾는다)다. `calls` 는 "새 대화"를 한 번 누른 뒤
 * 처리기가 불린 횟수, `scrolls` 는 휠 뒤에 그 자리의 `scrollTop` 이 바뀌는지, `page` 는 같은 휠에 페이지의 스크롤 위치가
 * 바뀌는지다. 갈래 A 의 기대(처리기가 불리지 않고, 그 자리가 구르지 않고, 휠이 페이지로 넘어간다)는 돌리기 전에 적은
 * 예측이다.
 */
const POINTER = [
  { id: "long-intro-in-admin-frame", scroller: "main", calls: 1, scrolls: true, page: false },
  { id: "long-intro-shielded", scroller: "main", calls: 0, scrolls: false, page: true },
  {
    id: "long-talk-in-admin-frame",
    scroller: '[aria-label="대화"]',
    calls: 1,
    scrolls: true,
    page: false,
  },
  { id: "long-talk-shielded", scroller: '[aria-label="대화"]', calls: 0, scrolls: false, page: true },
];
const PAGE_START = 300;
const WHEEL = 200;

/** 정적 빌드를 가짜 출처로 연다. 그 밖의 요청은 404 다(web/packages/ui/visual/index.ts 의 방식). */
async function serve(page) {
  await page.route("**/*", async (route) => {
    const url = new URL(route.request().url());
    const path = join(site, decodeURIComponent(url.pathname));
    if (
      url.origin !== ORIGIN ||
      !path.startsWith(site + sep) ||
      !existsSync(path) ||
      statSync(path).isDirectory()
    ) {
      await route.fulfill({ status: 404 });
      return;
    }
    await route.fulfill({ path });
  });
}

/** 렌더가 play 와 afterEach 까지 끝났는지(Storybook 10.6.1 의 마지막 단계 `finished`). */
function renderFinished() {
  return window.__STORYBOOK_PREVIEW__?.currentRender?.phase === "finished";
}

/** 위젯이 눈에 그려졌다는 표지. */
function drawn() {
  const wrapper = document.querySelector("[data-density]");
  const main = wrapper?.querySelector("main");
  const heading = wrapper?.querySelector("h1");
  if (!wrapper || !main || !heading) {
    return { ok: false, why: "감싼 요소나 main 이나 제목이 없다" };
  }
  const box = main.getBoundingClientRect();
  const overflowY = getComputedStyle(main).overflowY;
  const fontSize = getComputedStyle(heading).fontSize;
  const ok =
    document.querySelector("body.sb-show-errordisplay") === null &&
    overflowY === "auto" &&
    box.width > 0 &&
    box.height > 0 &&
    heading.textContent === "주문 도우미" &&
    fontSize === "15px";
  return { ok, why: `overflow-y ${overflowY}, ${box.width}x${box.height}, 제목 ${fontSize}` };
}

/** 지금 포커스를 받은 요소. */
function focused() {
  const wrapper = document.querySelector("[data-density]");
  const active = document.activeElement;
  if (active === null || active === document.body) {
    return { where: "body", label: "body" };
  }
  const text = (active.textContent ?? "").trim().slice(0, 10);
  return {
    where: wrapper !== null && wrapper.contains(active) ? "in" : "out",
    label: `${active.tagName.toLowerCase()}:${text}`,
  };
}

/** 접근성 트리에서 무시되지 않은 노드를 역할마다 이름으로 모은다. */
async function accessibilityTree(page) {
  const session = await page.context().newCDPSession(page);
  try {
    await session.send("Accessibility.enable");
    const { nodes } = await session.send("Accessibility.getFullAXTree");
    const named = (roles) =>
      nodes
        .filter((node) => !node.ignored && roles.includes(node.role?.value))
        .map((node) => node.name?.value ?? "");
    return {
      total: nodes.filter((node) => !node.ignored).length,
      images: named(["image", "img"]),
      mains: named(["main"]),
      buttons: named(["button"]),
      headings: named(["heading"]),
      textboxes: named(["textbox"]),
    };
  } finally {
    await session.detach();
  }
}

const same = (a, b) => JSON.stringify([...a].sort()) === JSON.stringify([...b].sort());

/** 위젯이 트리에 통째로 있는지, 통째로 없는지. 어느 쪽도 아니면 null 이다. */
function widgetInTree(tree) {
  const present =
    tree.mains.length === 2 &&
    tree.buttons.includes("새 대화") &&
    tree.headings.includes("주문 도우미");
  const absent =
    tree.mains.length === 1 &&
    same(tree.buttons, ["저장"]) &&
    same(tree.headings, ["사이트 고치기"]) &&
    tree.textboxes.length === 0;
  return present ? true : absent ? false : null;
}

const describe = (tree) =>
  `${tree.total}노드, 그림 ${JSON.stringify(tree.images)}, main ${tree.mains.length}, 단추 ${JSON.stringify(tree.buttons)}, 제목 ${JSON.stringify(tree.headings)}, 입력창 ${tree.textboxes.length}`;

/**
 * 마우스 회차: 문서가 받은 click 과 wheel 을 적어 둔다. 받은 요소가 위젯의 어디인지와 함께다. 같은 가름을 `__where` 로 내어
 * 한 점에서 브라우저가 맞히는 요소(`elementFromPoint`)에도 쓴다.
 */
function recordPointerEvents(selector) {
  const where = (target) => {
    const wrapper = document.querySelector("[data-density]");
    const scroller = wrapper?.querySelector(selector);
    if (!(target instanceof Element)) {
      return "요소 아님";
    }
    const tag = target.tagName.toLowerCase();
    if (scroller?.contains(target)) {
      return `넘친 자리 안의 ${tag}`;
    }
    if (target === wrapper) {
      return "감싼 바깥 요소";
    }
    return wrapper?.contains(target) ? `위젯 안의 ${tag}` : `위젯 밖의 ${tag}`;
  };
  window.__where = where;
  window.__pointerEvents = [];
  for (const type of ["click", "wheel"]) {
    window.addEventListener(
      type,
      (event) => {
        window.__pointerEvents.push(`${type}→${where(event.target)}`);
      },
      { capture: true, passive: true },
    );
  }
}

/** "새 대화" 단추의 가운데(뷰포트 좌표)와, 그 점에서 브라우저가 맞히는 요소. */
function newConversationPoint() {
  const wrapper = document.querySelector("[data-density]");
  const button = [...(wrapper?.querySelectorAll("button") ?? [])].find(
    (element) => element.textContent === "새 대화",
  );
  if (!button) {
    return null;
  }
  const box = button.getBoundingClientRect();
  const x = box.left + box.width / 2;
  const y = box.top + box.height / 2;
  return {
    x,
    y,
    visible: box.width > 0 && box.height > 0 && x >= 0 && y >= 0 && x <= innerWidth && y <= innerHeight,
    hit: window.__where(document.elementFromPoint(x, y)),
  };
}

/** 넘친 자리와 페이지의 스크롤, 처리기의 호출 횟수, 넘친 자리의 보이는 부분의 가운데와 거기서 맞히는 요소. */
function pointerState(selector) {
  const wrapper = document.querySelector("[data-density]");
  const scroller = wrapper?.querySelector(selector);
  const main = wrapper?.querySelector("main");
  const page = document.scrollingElement;
  if (!wrapper || !scroller || !main || !page) {
    return null;
  }
  const box = scroller.getBoundingClientRect();
  const top = Math.max(box.top, 0);
  const bottom = Math.min(box.bottom, innerHeight);
  const x = box.left + box.width / 2;
  const y = (top + bottom) / 2;
  return {
    calls: wrapper.dataset.newConversationCalls ?? "없음",
    scrollTop: scroller.scrollTop,
    scrollHeight: scroller.scrollHeight,
    clientHeight: scroller.clientHeight,
    mainScrollHeight: main.scrollHeight,
    mainClientHeight: main.clientHeight,
    pageTop: page.scrollTop,
    pageRoom: page.scrollHeight - page.clientHeight,
    x,
    y,
    shown: bottom - top,
    hit: window.__where(document.elementFromPoint(x, y)),
    events: [...window.__pointerEvents],
  };
}

/**
 * 스크롤이 멎을 때까지(두 번 이어 같은 값) 기다려 상태를 읽는다. 휠은 부드럽게 굴러 바로 읽으면 중간 값이다. 읽는 사이에
 * 넘친 자리가 사라져 `pointerState` 가 null 을 내면 null 을 돌려주고, 부르는 쪽이 그 회차를 측정이 아니라고 센다.
 */
async function settledState(page, selector) {
  await page.waitForTimeout(400);
  let last = await page.evaluate(pointerState, selector);
  for (let read = 0; read < 12 && last !== null; read += 1) {
    await page.waitForTimeout(250);
    const next = await page.evaluate(pointerState, selector);
    if (next === null) {
      return null;
    }
    if (next.scrollTop === last.scrollTop && next.pageTop === last.pageTop) {
      return next;
    }
    last = next;
  }
  return last;
}

const browser = await chromium.launch();
let unmeasured = 0;
let mismatched = 0;
try {
  console.log(`chromium ${browser.version()}`);
  for (const branch of BRANCHES) {
    for (const viewport of VIEWPORTS) {
      const round = `${branch.id} ${viewport.name}`;
      const page = await browser.newPage({
        viewport: { width: viewport.width, height: viewport.height },
      });
      try {
        const warnings = [];
        page.on("console", (message) => {
          if (message.text().includes("aria-hidden")) {
            warnings.push(message.text());
          }
        });
        // play 의 흉내 Tab 이 위젯에 포커스를 넣지 못하게 한다(머리 주석).
        await page.addInitScript(() => {
          HTMLElement.prototype.focus = function focus() {};
        });
        await serve(page);
        await page.goto(
          `${ORIGIN}/iframe.html?id=pages-widgetpreviewprobe--${branch.id}&viewMode=story`,
        );
        await page.waitForFunction(renderFinished);
        await page.evaluate(async () => {
          await document.fonts.ready;
        });
        const marker = await page.evaluate(drawn);
        const start = await page.evaluate(focused);
        if (!marker.ok || start.where !== "body") {
          unmeasured += 1;
          console.log(`${round}: 측정이 아니다(${marker.why}, 처음 포커스 ${start.label})`);
          continue;
        }

        const before = await accessibilityTree(page);
        const trail = [];
        let after = null;
        for (let press = 0; press < PRESSES; press += 1) {
          await page.keyboard.press("Tab");
          const step = await page.evaluate(focused);
          trail.push(step);
          if (after === null && step.where === "in") {
            after = await accessibilityTree(page);
          }
        }
        after ??= await accessibilityTree(page);
        const inside = trail.filter((step) => step.where === "in").length;
        const reachedSave = trail.some((step) => step.label === "button:저장");

        const problems = [];
        // 표지: Tab 이 실제로 포커스를 옮겼다. 어느 갈래든 위젯 밖의 "저장" 단추에는 닿아야 한다.
        if (!reachedSave) {
          problems.push("Tab 이 저장 단추에 닿지 않았다");
        }
        if (inside > 0 !== branch.inside) {
          problems.push(`위젯 안에 든 횟수 ${inside}`);
        }
        for (const [when, tree, expected] of [
          ["처음", before, branch.before],
          ["뒤", after, branch.after],
        ]) {
          if (tree.images.filter((name) => name === LABEL).length !== branch.images) {
            problems.push(`${when} 트리의 이름 붙은 그림 ${JSON.stringify(tree.images)}`);
          }
          if (widgetInTree(tree) !== expected) {
            problems.push(`${when} 트리에 위젯이 ${expected ? "있어야" : "없어야"} 한다`);
          }
        }
        if (problems.length > 0) {
          mismatched += 1;
        }
        console.log(
          `${round}: ${problems.length === 0 ? "기대와 같다" : `기대와 다르다: ${problems.join("; ")}`}`,
        );
        console.log(`  그려짐: ${marker.why}`);
        console.log(
          `  Tab ${PRESSES}번 가운데 위젯 안 ${inside}번, 저장 단추 ${reachedSave ? "닿음" : "닿지 않음"}: ${trail.map((step) => `${step.where}/${step.label}`).join(" → ")}`,
        );
        console.log(`  처음 트리(포커스 받기 전): ${describe(before)}`);
        console.log(
          `  뒤 트리(${inside > 0 ? "포커스가 위젯 안에 처음 든 때" : "Tab 을 다 누른 뒤"}): ${describe(after)}`,
        );
        console.log(`  aria-hidden 콘솔 경고 ${warnings.length}건${warnings[0] ? `: ${warnings[0]}` : ""}`);
      } finally {
        await page.close();
      }
    }
  }

  for (const target of POINTER) {
    for (const viewport of VIEWPORTS) {
      const round = `${target.id} ${viewport.name}`;
      const page = await browser.newPage({
        viewport: { width: viewport.width, height: viewport.height },
      });
      try {
        await serve(page);
        await page.goto(
          `${ORIGIN}/iframe.html?id=pages-widgetpreviewprobe--${target.id}&viewMode=story`,
        );
        await page.waitForFunction(renderFinished);
        await page.evaluate(async () => {
          await document.fonts.ready;
        });
        const marker = await page.evaluate(drawn);
        await page.evaluate(recordPointerEvents, target.scroller);
        const start = await page.evaluate(pointerState, target.scroller);
        const point = await page.evaluate(newConversationPoint);
        const missing = [];
        if (!marker.ok) {
          missing.push(`그려지지 않았다(${marker.why})`);
        }
        if (start === null) {
          missing.push("넘치는 자리를 찾지 못했다");
        } else {
          if (start.scrollHeight <= start.clientHeight) {
            missing.push(`넘치지 않았다(${start.scrollHeight}/${start.clientHeight})`);
          }
          if (start.pageRoom < PAGE_START + WHEEL) {
            missing.push(`페이지에 굴릴 데가 모자란다(${start.pageRoom})`);
          }
        }
        if (point === null || !point.visible) {
          missing.push("새 대화 단추가 화면에 없다");
        }
        if (missing.length > 0) {
          unmeasured += 1;
          console.log(`${round}: 측정이 아니다(${missing.join("; ")})`);
          continue;
        }

        // 클릭. 처리기가 불린 횟수는 임시 소비자가 감싼 바깥 요소의 data 속성으로 낸다.
        await page.mouse.click(point.x, point.y);
        const clicked = await settledState(page, target.scroller);

        // 휠. 페이지를 미리 내려 두고, 넘친 자리의 보이는 부분 가운데에 마우스를 올린다.
        await page.evaluate((top) => {
          window.scrollTo(0, top);
        }, PAGE_START);
        const before = await settledState(page, target.scroller);
        if (clicked === null || before === null) {
          unmeasured += 1;
          console.log(`${round}: 측정이 아니다(누른 뒤 넘치는 자리를 읽지 못했다)`);
          continue;
        }
        const roomDown = before.scrollHeight - before.clientHeight - before.scrollTop;
        const delta = roomDown >= WHEEL / 2 ? WHEEL : -WHEEL;
        await page.mouse.move(before.x, before.y);
        await page.mouse.wheel(0, delta);
        const after = await settledState(page, target.scroller);
        if (after === null) {
          unmeasured += 1;
          console.log(`${round}: 측정이 아니다(휠 뒤 넘치는 자리를 읽지 못했다)`);
          continue;
        }

        const gotClick = after.events.some((event) => event.startsWith("click→"));
        const gotWheel = after.events.some((event) => event.startsWith("wheel→"));
        if (before.pageTop !== PAGE_START || before.shown < 40 || !gotClick || !gotWheel) {
          unmeasured += 1;
          console.log(
            `${round}: 측정이 아니다(페이지 위치 ${before.pageTop}, 넘친 자리의 보이는 높이 ${before.shown}, 받은 이벤트 ${JSON.stringify(after.events)})`,
          );
          continue;
        }

        const scrolled = after.scrollTop !== before.scrollTop;
        const pageMoved = after.pageTop !== before.pageTop;
        const problems = [];
        if (clicked.calls !== String(target.calls)) {
          problems.push(`처리기 호출 ${clicked.calls}`);
        }
        if (scrolled !== target.scrolls) {
          problems.push(`넘친 자리의 scrollTop ${before.scrollTop} → ${after.scrollTop}`);
        }
        if (pageMoved !== target.page) {
          problems.push(`페이지의 scrollTop ${before.pageTop} → ${after.pageTop}`);
        }
        if (problems.length > 0) {
          mismatched += 1;
        }
        console.log(
          `${round}: ${problems.length === 0 ? "기대와 같다" : `기대와 다르다: ${problems.join("; ")}`}`,
        );
        console.log(
          `  그려짐: ${marker.why}. 넘침: ${target.scroller} ${start.scrollHeight}/${start.clientHeight}(scrollHeight/clientHeight), main ${start.mainScrollHeight}/${start.mainClientHeight}, 처음 scrollTop ${start.scrollTop}`,
        );
        console.log(
          `  클릭: 새 대화의 가운데에서 맞히는 요소 "${point.hit}", 처리기 호출 ${start.calls} → ${clicked.calls}`,
        );
        console.log(
          `  휠 ${delta}px: 마우스 아래에서 맞히는 요소 "${before.hit}", 넘친 자리의 scrollTop ${before.scrollTop} → ${after.scrollTop}, 페이지의 scrollTop ${before.pageTop} → ${after.pageTop}`,
        );
        console.log(`  문서가 받은 이벤트: ${after.events.join(", ")}`);
      } finally {
        await page.close();
      }
    }
  }
} finally {
  await browser.close();
}

const rounds = (BRANCHES.length + POINTER.length) * VIEWPORTS.length;
console.log(`회차 ${rounds}, 측정이 아닌 회차 ${unmeasured}, 기대와 다른 회차 ${mismatched}`);
process.exit(unmeasured > 0 ? 2 : mismatched > 0 ? 1 : 0);
