# plugin-toggle: 운영자가 플러그인을 켜고 끌 수 있고, 꺼진 플러그인을 부른 실행은 시작 전에 막힌다.
**슬라이스:** 2
**Blocked by:** admin-api
**끝:** 2026-09-28

플러그인을 켜고 끈다. PRD의 운영자가 "켜고 끄고" 싶다는 그것이다. 켜짐은 매니페스트가 아니라 플러그인 루트의 `disabled.toml`이 들고, 매니페스트와 sdk는 바뀌지 않는다(ADR 0017). 관리의 첫 쓰기 경로 `PUT /plugins/{kind}/{name}/enabled`(204)와, `/plugins`의 감싼 행 `{kind, name, enabled}` + `manifest`·`reason`(ADR 0010 이력). `PluginSource`에 메서드 둘(ADR 0012 이력). 꺼진 것을 부른 새 실행과 재개는 core의 `Disabled`이고 409다(ADR 0017). 재개 쪽과 하위 타입 기준의 개정은 ADR 0014 이력에 있다. 첫 티켓은 계약: `openapi.json`의 `/plugins` 응답과 새 경로, `POST /runs`의 409, 포트, `Disabled`. 설계는 일지 2026-09-26-06
