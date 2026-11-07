# otel-export: 실행의 트레이스를 OpenTelemetry 표준으로 내보내 Langfuse 같은 도구에서 볼 수 있게 한다.
**슬라이스:** 12
**Blocked by:** claude-code-compat

OTel 내보내기(후보 13). main이 트레이스 저장소를 감싸는 어댑터로 쓰기마다 span을 OTel SDK에 넘기고 배치 프로세서가 OTLP로 보낸다. 설정은 표준 환경 변수뿐이다. 실행 = trace, 이벤트 = span, 속성은 GenAI 시맨틱 컨벤션이고 본문은 마스킹을 지난 글을 늘 싣는다. 수락 기준은 로컬 Langfuse에 뜨는 것(ADR 0042 묶음 ③)
