# 로컬 모델 시험의 모델 서버를 Runpod에 띄우는 구성. `tools/llm_local.py`가 부른다(독스트링 참조).
#
# 이 구성은 클라우드에서 돌려 보지 않았다. 자원의 속성 이름(`image_name`, `gpu_type_ids`,
# `container_disk_in_gb`, `cloud_type`, `cost_per_hr` 등)은 프로바이더 `runpod/runpod` 2.0.0의
# 문서와 대조하지 않은 추정이다(명세는 `args`와 `/v2/pods` 경로만 적었다). 공식 이미지의 시작
# 명령이 `args`를 삼키는지도 확인하지 않았다. 확인은 티켓 03의 "띄워 확인하는 것"이다.
# `terraform fmt`로 문법만 봤다.
#
# 계정 키는 이 구성이 받지 않는다. 프로바이더는 호출한 프로세스의 환경에서 스스로 읽고, 파드의
# 타이머는 Runpod가 파드에 주입한 키로 그 파드를 지운다. 서버 키만 받는 변수가 있고 그 값은 자원의
# 칸(시작 명령)에 실려 상태 파일에 평문으로 남는다. 그래서 상태 폴더는 저장소 밖에 있다.

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    runpod = {
      source  = "runpod/runpod"
      version = "= 2.0.0"
    }
  }
}

provider "runpod" {}

variable "server_key" {
  type        = string
  sensitive   = true
  description = "vLLM 서버가 요구하는 키. 명령이 무작위로 만든다."
}

variable "gpu_type_id" {
  type        = string
  description = "Runpod의 GPU 종류 ID."
}

variable "layout" {
  type        = string
  description = "pods는 모델마다 파드 하나, shared는 파드 하나에 서버 둘."

  validation {
    condition     = contains(["pods", "shared"], var.layout)
    error_message = "layout은 pods나 shared다."
  }
}

variable "models" {
  type = map(object({
    model_id = string
    parser   = string
  }))
  description = "키는 모델 번호(1, 2). 서버가 띄울 모델과 도구 호출 파서."
}

variable "timer_minutes" {
  type        = number
  default     = 90
  description = "이 시간이 지나면 파드가 스스로 지워진다."
}

variable "image" {
  type        = string
  default     = "vllm/vllm-openai:v0.33.0"
  description = "vLLM 공식 이미지."
}

variable "shared_memory_utilization" {
  type        = number
  default     = 0.45
  description = "shared 배치에서 서버마다 쓰는 GPU 메모리 비율."
}

locals {
  shared = var.layout == "shared"

  # 파드 이름 → 그 파드가 띄울 모델 번호들
  pods = local.shared ? { shared = sort(keys(var.models)) } : { for n in keys(var.models) : n => [n] }

  # shared 배치는 서버마다 포트가 다르다(8000, 8001)
  ports = { for i, n in sort(keys(var.models)) : n => local.shared ? 8000 + i : 8000 }

  # 파드가 시작하면 가장 먼저 건다. 멈추지 않고 지운다(멈춘 파드는 디스크 요금이 계속 나간다).
  timer = join(" ", [
    "( sleep ${var.timer_minutes * 60};",
    "if command -v runpodctl >/dev/null 2>&1; then runpodctl pod delete \"$RUNPOD_POD_ID\";",
    "else curl -fsS -X DELETE -H \"Authorization: Bearer $RUNPOD_API_KEY\" \"https://rest.runpod.io/v2/pods/$RUNPOD_POD_ID\"; fi ) &",
  ])

  serve = {
    for n, m in var.models : n => join(" ", compact([
      "vllm serve ${m.model_id}",
      "--host 0.0.0.0",
      "--port ${local.ports[n]}",
      "--api-key=${var.server_key}",
      "--enable-auto-tool-choice",
      "--tool-call-parser ${m.parser}",
      local.shared ? "--gpu-memory-utilization ${var.shared_memory_utilization}" : "",
    ]))
  }

  script = {
    for pod, numbers in local.pods : pod => join("\n", concat(
      [local.timer],
      [for n in numbers : "${local.serve[n]} &"],
      ["wait"],
    ))
  }
}

resource "runpod_pod" "server" {
  for_each = local.pods

  name                 = "agent-os-llm-local-${each.key}"
  image_name           = var.image
  gpu_type_ids         = [var.gpu_type_id]
  gpu_count            = 1
  cloud_type           = "SECURE"
  container_disk_in_gb = 60
  volume_in_gb         = 0
  ports                = local.shared ? ["8000/http", "8001/http"] : ["8000/http"]
  args                 = ["bash", "-c", local.script[each.key]]
}

output "servers" {
  description = "모델마다 주소(Runpod 프록시). 서버 키는 싣지 않는다."
  value = [
    for n in sort(keys(var.models)) : {
      n        = n
      model_id = var.models[n].model_id
      base_url = "https://${runpod_pod.server[local.shared ? "shared" : n].id}-${local.ports[n]}.proxy.runpod.net/v1"
    }
  ]
}

output "pods" {
  description = "파드마다 Terraform이 돌려준 시간당 값."
  value = [
    for pod, numbers in local.pods : {
      id          = runpod_pod.server[pod].id
      cost_per_hr = runpod_pod.server[pod].cost_per_hr
    }
  ]
}
