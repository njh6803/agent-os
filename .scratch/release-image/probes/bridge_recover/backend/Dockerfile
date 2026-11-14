# 뒷단 흉내 이미지. 프로브가 dind 안쪽 엔진에서 v1 과 v2 두 태그로 짓는다(판 올림의 모양).
# BASE 는 프로브가 digest 로 고정한 python 이미지다. 안쪽 엔진에 미리 실어 두어 받지 않는다.
ARG BASE
FROM ${BASE}
ARG VERSION
ENV IMAGE_VERSION=${VERSION} PYTHONUNBUFFERED=1
COPY server.py dns_ttl.py /srv/
USER 65534:65534
CMD ["python", "/srv/server.py"]
