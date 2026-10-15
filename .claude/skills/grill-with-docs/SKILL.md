---
name: grill-with-docs
description: "설계 인터뷰. 사용자가 이를 요청할 때('grill', '인터뷰 진행하자'), 또는 새 기능에 `.scratch/<slug>/`가 없는 단계일 때만 부른다. 구현과 리뷰 중에는 하던 일을 이어 간다."
---

<!-- 프로젝트 사본, model-invoked. 원본(mattpocock/skills)은 disable-model-invocation: true. 사용자가 다른 세션에서 설계 인터뷰를 `grilling`만 불러 진행했고, 그 결과 `domain-modeling`이 하는 CONTEXT.md 용어 기록과 ADR 초안이 빠졌다. 이 스킬이 둘을 차례로 부르는 라우터라서, 모델이 이 스킬을 부를 수 있어야 한 번에 둘 다 돈다(일지 2026-10-15-10). 모델이 부르면 설명이 모든 세션에 실리므로 설명은 짧게, 트리거는 좁게 썼고, 부르기 직전 `tools/hook_grill_design_check.py`가 설계 인터뷰가 맞는지 확인하라는 계기를 넣는다(ADR 0028 이력 2026-10-15). `to-spec`·`to-tickets`·`implement`는 단계를 넘어갈지 사람이 정하는 관문이라 사용자 전용으로 둔다. 이 주석이 `tools/check_instructions.py`의 센티널이라 지우면 검사가 빨강이 된다. -->

Call the Skill tool twice, for "grilling" and "domain-modeling".
