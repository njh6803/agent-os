# 임시 tokens.json 저장 꼴 재기

design-reverse-sync 티켓 02 가 페이지가 저장한 `tokens.json` 의 꼴과 낡은 판의 거부를 손으로 보려고 만든 임시 디자인 시스템이다. 재기가 끝나면 지운다.


---

## Consuming this system (generated — do not edit)

Every path named below is under `project/` in this design system: read `project/api/tokens.md`, not `api/tokens.md`.

This system ships tokens, no components: take colours, type and fonts from the tokens card below for any page, deck or mock-up; a Slides deck or Design canvas also takes `tokens.json` by file path (that type’s SKILL.md says how). On a Design canvas, also copy `tokens.css` to `project/ds/<folder>/tokens.css` in the call that installs this system, and link it in each artboard that uses this system, right after the `support.js` line and before the system’s other stylesheets: `<link rel="stylesheet" href="ds/<folder>/tokens.css">` (with one `../` in front for each folder the artboard is in).

**Read, per thing:** token values: `api/tokens.md`. After this README, fetch the cards and fonts you need in ONE message as parallel calls — none depends on another.

**Two rules.** Before you use a thing — a component, a token group, an icon, an asset — read its card from the index below; a value you did not read from a card is a guess. `tokens.json`, `manifest.json` and `design-system.json` are sources for tools: hand them over. `SKILL.md` and `artifact-type/` beside them are authoring guidance, not needed to consume the system.

## Index (generated — do not edit)

**Tokens**

- `api/tokens.md` — Every token: text, fill, border, palette, type, spacing, radius. (18.0k)
