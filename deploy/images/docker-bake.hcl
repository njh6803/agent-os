# 이미지 넷을 한 번에 짓는 목록(release-image 티켓 11, .scratch/release-image/spec.md "판 내기 워크플로").
# 판 내기 워크플로(.github/workflows/release.yml)가 `docker/bake-action`으로 두 번 부른다. 첫 번째는 증명 없이
# 러너의 Docker 에 실어 단독 배포 시험과 점검을 돌리는 짓기이고, 두 번째는 같은 빌더가 캐시로 다시 지어 증명과
# 함께 커밋 해시 태그로만 올리는 짓기다. 두 번 다 같은 이 파일을 쓰고 달라지는 것은 아래 변수 값뿐이다.
#
# 저장소 루트에서 부른다. context 와 dockerfile 은 부르는 자리(저장소 루트) 기준이다. 이미지마다의 빌드 인자와
# 같은 폴더의 `<이름>.Dockerfile.dockerignore` 는 각 Dockerfile 머리 주석이 원천이다. 로컬에서 같은 이미지를
# 짓는 길은 web/packages/e2e-standalone/e2e/stack.ts 의 `imagesToRun` 이다(같은 인자를 준다).
#
# 이름은 둘이다. 짓기 대상 이름(`serve`, `admin`, `widget`, `portal`)은 코드의 이름이고 Dockerfile 과 compose 서비스와
# 점검 결과 파일이 따른다. Docker Hub 저장소 이름(`agent-os-runtime`, `agent-os-admin`, `agent-os-widget`,
# `agent-os-widget-test-page`)은 아래 `tags` 의 `${NAMESPACE}/<저장소>:${TAG}` 가 정한다. 둘의 대응은 이 파일이 유일하게 정하고,
# 워크플로와 e2e 는 `python3 tools/release_ci.py repository <대상>` 으로 읽는다. compose 의 `image:` 줄과 배포 안내의 대응표는
# 사람이 쓴 사본이라 tests/tools/test_release_ci.py 가 이 파일과 같은지 본다.
#
# 빌드 캐시는 GitHub Actions 캐시에 이미지마다 다른 범위(scope)로 둔다. 범위를 같게 두면 마지막 이미지의 캐시만
# 남는다(.scratch/release-image/probes/release_mechanics/README.md 5번).

# 이미지 이름공간. 첫 짓기는 시험용 이름, 올리는 짓기는 Docker Hub 계정 이름이다.
variable "NAMESPACE" {
  default = "agent-os-release-test"
}

# 태그. 첫 짓기는 판 번호, 올리는 짓기는 `sha-<커밋 해시 40자>`다.
variable "TAG" {
  default = "unknown"
}

# 판 번호(`v` 없음). 이미지 안의 판과 OCI 라벨에 들어간다.
variable "VERSION" {
  default = ""
}

variable "REVISION" {
  default = "unknown"
}

variable "SOURCE" {
  default = "unknown"
}

group "default" {
  targets = ["serve", "admin", "widget", "portal"]
}

target "serve" {
  context    = "."
  dockerfile = "deploy/images/serve.Dockerfile"
  args = {
    APP_VERSION = VERSION
    REVISION    = REVISION
    SOURCE      = SOURCE
  }
  tags       = ["${NAMESPACE}/agent-os-runtime:${TAG}"]
  cache-from = ["type=gha,scope=serve"]
  cache-to   = ["type=gha,scope=serve,mode=max"]
}

target "_web" {
  context = "web"
  args = {
    IMAGE_VERSION  = VERSION
    IMAGE_REVISION = REVISION
    IMAGE_SOURCE   = SOURCE
  }
}

target "admin" {
  inherits   = ["_web"]
  dockerfile = "../deploy/images/admin.Dockerfile"
  tags       = ["${NAMESPACE}/agent-os-admin:${TAG}"]
  cache-from = ["type=gha,scope=admin"]
  cache-to   = ["type=gha,scope=admin,mode=max"]
}

target "widget" {
  inherits   = ["_web"]
  dockerfile = "../deploy/images/widget.Dockerfile"
  tags       = ["${NAMESPACE}/agent-os-widget:${TAG}"]
  cache-from = ["type=gha,scope=widget"]
  cache-to   = ["type=gha,scope=widget,mode=max"]
}

target "portal" {
  inherits   = ["_web"]
  dockerfile = "../deploy/images/portal.Dockerfile"
  tags       = ["${NAMESPACE}/agent-os-widget-test-page:${TAG}"]
  cache-from = ["type=gha,scope=portal"]
  cache-to   = ["type=gha,scope=portal,mode=max"]
}
