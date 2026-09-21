---
name: code-review
description: "Review the changes since a fixed point (commit, branch, tag, or merge-base) along two axes: Standards (does the code follow this repo's documented coding standards?) and Spec (does the code match what the originating issue/spec asked for?). Runs both reviews in parallel sub-agents and reports them side by side. Use when the user wants to review a branch, a PR, work-in-progress changes, or asks to \"review since X\"."
---

<!-- 프로젝트 사본. 원본(mattpocock/skills)에 넷을 더했다. 4단계의 sonnet 규칙(일지 2026-09-20 첫 회고), 1단계의 미커밋·미추적 범위와 5단계의 범위 한 줄, 6단계의 반영(일지 2026-09-21 리뷰 반영 루프). 이 주석이 `tools/check_instructions.py`의 센티널이라 지우면 검사가 빨강이 된다. -->

Two-axis review of the diff between `HEAD` and a fixed point the user supplies:

- **Standards**: does the code conform to this repo's documented coding standards?
- **Spec**: does the code faithfully implement the originating issue / spec?

Both axes run as **parallel sub-agents** so they don't pollute each other's context, then this skill aggregates their findings.

The issue tracker should have been provided to you. If `docs/agents/issue-tracker.md` is missing, tell the user to run `/setup-matt-pocock-skills`.

## Process

### 1. Pin the fixed point

Whatever the user said is the fixed point (a commit SHA, branch name, tag, `main`, `HEAD~5`, etc.). If they didn't specify one, ask for it.

`git merge-base <fixed-point> HEAD`로 base SHA를 한 번 구해 고정하고, 아래 명령과 서브에이전트 둘에 ref가 아니라 그 SHA를 넘긴다. 셸이 다시 확장하지 않고 두 축이 같은 나무를 본다.

주 용도가 커밋 전 셀프 리뷰이므로 범위는 커밋된 것에서 끝나지 않는다. 셋을 잡는다.

- `git diff <BASE>`: base 이후의 커밋과 staged·unstaged 작업. 세 점 diff(`<BASE>...HEAD`)는 아직 커밋하지 않은 작업을 빼므로 쓰지 않는다. `implement`는 리뷰한 뒤 커밋하므로 리뷰 시점의 작업은 대개 미커밋이다.
- `git status --porcelain`의 `??` 항목: 미추적 파일. 어떤 diff에도 안 잡힌다. 새 어댑터나 새 테스트가 통째로 리뷰에서 빠지는 자리다. 경로 목록을 서브에이전트에 넘겨 파일 전체를 새 코드로 읽게 한다.
- `git log <BASE>..HEAD --oneline`: 커밋 목록.

Before going further, confirm the fixed point resolves (`git rev-parse <fixed-point>`). diff와 미추적 목록이 **둘 다** 비면 여기서 실패한다. 빈 diff 하나로는 실패하지 않는다. 미추적 파일만 있는 상태가 이 스킬이 닫으려는 갭이기 때문이다. A bad ref should fail here, not inside two parallel sub-agents.

### 2. Identify the spec source

Look for the originating spec, in this order:

1. Issue references in the commit messages (`#123`, `Closes #45`, GitLab `!67`, etc.), fetched via the workflow in `docs/agents/issue-tracker.md`.
2. A path the user passed as an argument.
3. A spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.
4. If nothing is found, ask the user where the spec is. If they say there isn't one, the **Spec** sub-agent will skip and report "no spec available".

### 3. Identify the standards sources

Anything in the repo that documents how code should be written, such as `CODING_STANDARDS.md` or `CONTRIBUTING.md`.

On top of whatever the repo documents, the Standards axis always carries the **smell baseline** below: a fixed set of Fowler code smells (_Refactoring_, ch.3) that applies even when a repo documents nothing. Two rules bind it:

- **The repo overrides.** A documented repo standard always wins; where it endorses something the baseline would flag, suppress the smell.
- **Always a judgement call.** Each smell is a labelled heuristic ("possible Feature Envy"), never a hard violation. Like any standard here, skip anything tooling already enforces.

Each smell reads *what it is* → *how to fix*; match it against the diff:

- **Mysterious Name**: a function, variable, or type whose name doesn't reveal what it does or holds. → rename it; if no honest name comes, the design's murky.
- **Duplicated Code**: the same logic shape appears in more than one hunk or file in the change. → extract the shared shape, call it from both.
- **Feature Envy**: a method that reaches into another object's data more than its own. → move the method onto the data it envies.
- **Data Clumps**: the same few fields or params keep travelling together (a type wanting to be born). → bundle them into one type, pass that.
- **Primitive Obsession**: a primitive or string standing in for a domain concept that deserves its own type. → give the concept its own small type.
- **Repeated Switches**: the same `switch`/`if`-cascade on the same type recurs across the change. → replace with polymorphism, or one map both sites share.
- **Shotgun Surgery**: one logical change forces scattered edits across many files in the diff. → gather what changes together into one module.
- **Divergent Change**: one file or module is edited for several unrelated reasons. → split so each module changes for one reason.
- **Speculative Generality**: abstraction, parameters, or hooks added for needs the spec doesn't have. → delete it; inline back until a real need shows.
- **Message Chains**: long `a.b().c().d()` navigation the caller shouldn't depend on. → hide the walk behind one method on the first object.
- **Middle Man**: a class or function that mostly just delegates onward. → cut it, call the real target direct.
- **Refused Bequest**: a subclass or implementer that ignores or overrides most of what it inherits. → drop the inheritance, use composition.

### 4. Spawn both sub-agents in parallel

If the diff touches no source file (no `*.py` under `src/`, `tests/`, `tools/`; only docs, config, harness), spawn the Standards sub-agent with `model: sonnet`. 미추적 파일도 같이 센다. 문서만 바뀐 변경도 리뷰는 한다. 지침과 하네스는 다음 실행에 바로 영향을 주므로 면제 대상이 아니고, 내리는 것은 모델이지 축이 아니다. The Spec sub-agent is usually skipped then (no spec, step 2).

**Standards sub-agent prompt** should include:

- The full diff command, the untracked file list, and the commit list.
- The list of standards-source files you found in step 3, **plus the smell baseline from step 3** pasted in full (the sub-agent has no other access to it).
- The brief: "Report, per file/hunk where relevant, (a) every place the diff violates a documented standard: cite the standard (file + the rule); and (b) any baseline smell you spot: name it and quote the hunk. Distinguish hard violations from judgement calls: documented-standard breaches can be hard, but baseline smells are always judgement calls, and a documented repo standard overrides the baseline. Skip anything tooling enforces. Under 400 words."

**Spec sub-agent prompt** should include:

- The diff command, the untracked file list, and the commit list.
- The path or fetched contents of the spec.
- The brief: "Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. Under 400 words."

If the spec is missing, skip the Spec sub-agent and note this in the final report.

### 5. Aggregate

Present the two reports under `## Standards` and `## Spec` headings, verbatim or lightly cleaned. Do **not** merge or rerank findings, because the two axes are deliberately separate (see _Why two axes_).

End with a one-line summary: total findings per axis, and the worst issue _within each axis_ (if any). Don't pick a single winner across axes: that's the reranking the separation exists to prevent.

그 앞에 본 범위를 한 줄 적는다. base SHA, 파일 몇 개, 커밋 몇 개, 미추적 몇 개. 범위가 어긋난 리뷰는 실패하지 않고 초록으로 끝나므로, 보고만 보고도 무엇을 봤는지 알 수 있어야 한다.

### 6. 반영

보고로 끝내지 않는다. 주 용도가 커밋 전 셀프 리뷰이고 다음 단계가 커밋이므로, 그 사이가 여기다. 심각도의 원천은 `CODING_STANDARDS.md`다.

1. **고친다.** 문서화된 표준 위반, 명세의 누락·부분 구현, 요청하지 않은 범위 추가는 고친다. Critical·Major는 커밋 전에 고친다. 건너뛰지 않는다.
2. **근거를 먼저 본다.** 지적이 불분명하거나 기술적으로 맞지 않아 보이면 그대로 구현하지 않는다. 코드와 명세에서 근거를 확인한 뒤 수정 여부를 정한다. 서브에이전트 둘은 격리된 컨텍스트에서 diff와 표준 문서만 봤고 ADR도 주변 코드도 모른다. 특히 smell baseline은 스스로 judgement call이라고 말하는 휴리스틱이라, 포트와 어댑터의 간접층이 Middle Man으로, 원칙 IV가 요구하는 경계가 Speculative Generality로 보인다. 오탐을 그대로 고치면 수정이 원칙을 깬다. 봇의 초록을 믿지 않는 것과 같은 이유로 봇의 빨강도 그대로 믿지 않는다(`docs/constitution/operations.md` 리뷰 파이프라인). PR 직전 축의 트리아지에 대응하는 것이 이 단계다.
3. **먼저 묻는다.** 수정 방법이 아키텍처 결정이거나 계약(`sdk/`, `openapi.json`, 헌법)에 닿으면 고치기 전에 사용자 판단을 받고, ADR이 필요한지 같이 묻는다(`CLAUDE.md` 작업 규약 5).
4. **남긴다.** Minor·Nit과 근거를 보고 보류한 지적은 별도 티켓으로 빼고 이유를 한 줄 남긴다. 판단 항목만으로 커밋을 막지 않는다.
5. **다시 돌린다.** 고쳤으면 `CLAUDE.md`의 검증 명령 넷을 다시 돌린다. 전체 리뷰는 다시 돌리지 않는다.

보고 끝에 세 줄을 더한다. 고친 것, 남긴 것과 이유, 다시 돌린 명령과 결과.

## Why two axes

A change can pass one axis and fail the other:

- Code that follows every standard but implements the wrong thing → **Standards pass, Spec fail.**
- Code that does exactly what the issue asked but breaks the project's conventions → **Spec pass, Standards fail.**

Reporting them separately stops one axis from masking the other.
