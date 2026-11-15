# 로컬 모델 시험의 모델 서버를 Runpod에 띄우는 구성. `tools/llm_local.py`가 부른다(독스트링 참조).
#
# 자원의 속성 이름은 설치한 프로바이더 `runpod/runpod` 2.0.0의 스키마(`terraform providers
# schema -json`, 2026-11-13)로 맞췄다. 첫 실제 실행이 추정한 이름(`image_name`, `gpu_type_ids`,
# `container_disk_in_gb`, `cloud_type`, `volume_in_gb`, `cost_per_hr`)을 모두 거절해 파드를 만들지
# 못했다. `args`가 문자열 하나이고 JSON 객체면 entrypoint와 cmd를 따로 정한다는 것은 Runpod
# 플러그인의 create-pod 도구 설명에서 읽었다. 이 `args`로 공식 이미지가 `vllm serve`를 실행하는 것은
# 2026-11-14에 파드 로그로 봤다(티켓 03의 "띄워 확인하는 것").
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
  description = "shared 배치에서 서버마다 쓰는 GPU 메모리 비율. 시작할 때 남은 메모리가 이 몫보다 작으면 서버가 뜨지 않는다."
}

variable "shared_kv_cache_bytes" {
  type        = number
  default     = 4294967296
  description = "shared 배치에서 서버마다 고정하는 KV 캐시 크기(바이트). 비율만으로는 한 GPU에 서버 둘이 서지 않았다."
}

locals {
  shared = var.layout == "shared"

  # 파드 이름 → 그 파드가 띄울 모델 번호들
  pods = local.shared ? { shared = sort(keys(var.models)) } : { for n in keys(var.models) : n => [n] }

  # shared 배치는 서버마다 포트가 다르다(8000, 8001)
  ports = { for i, n in sort(keys(var.models)) : n => local.shared ? 8000 + i : 8000 }

  # 파드가 시작하면 가장 먼저 건다. 멈추지 않고 지운다(멈춘 파드는 디스크 요금이 계속 나간다).
  # 지우는 명령은 이미지의 runpodctl(1.14.15)이 아는 `remove pod`다. 첫 판은 `pod` 하위 명령을
  # 썼는데 그 판에 없어 타이머가 실패했다(2026-11-14 파드 로그와 `exec-pod`로 봤다). 파드 안에서 친
  # `runpodctl remove pod "$RUNPOD_POD_ID"`는 Runpod가 주입한 키로 파드를 지웠다.
  timer = join(" ", [
    "( sleep ${var.timer_minutes * 60};",
    "runpodctl remove pod \"$RUNPOD_POD_ID\" ) &",
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
      local.shared ? "--kv-cache-memory=${var.shared_kv_cache_bytes}" : "",
    ]))
  }

  # 한 GPU에 서버 둘이면 앞 서버가 응답한 뒤에 다음 서버를 시작한다. 동시에 시작하면 서로의 메모리를
  # 자기 몫에서 빼서 시작이 실패했다. 서버가 하나인 파드는 기다릴 서버가 없어 줄이 늘지 않는다.
  # 앞 서버가 죽으면 이 루프는 끝나지 않는다. 그때는 명령의 준비 상한(30분)이 파드를 지우고, 그 전에
  # 명령이 죽어도 위 타이머가 90분 뒤 지운다. 서버가 연결만 받고 응답을 끝내지 않아도 호출 하나가
  # 멈춰 루프가 돌지 못하는 일이 없게 curl에 요청 전체 시간 제한(`--max-time`)을 둔다.
  start = {
    for n, m in var.models : n => join("\n", compact([
      "${local.serve[n]} &",
      local.shared ? "until curl -fs --max-time 10 localhost:${local.ports[n]}/health > /dev/null; do sleep 3; done" : "",
    ]))
  }

  script = {
    for pod, numbers in local.pods : pod => join("\n", concat(
      [local.timer],
      [for n in numbers : local.start[n]],
      ["wait"],
    ))
  }
}

resource "runpod_pod" "server" {
  for_each = local.pods

  name        = "agent-os-llm-local-${each.key}"
  image       = var.image
  gpu_type_id = var.gpu_type_id
  gpu_count   = 1
  cloud       = "SECURE"
  disk        = 60
  ports       = local.shared ? ["8000/http", "8001/http"] : ["8000/http"]
  # 공식 이미지의 시작 명령(vllm serve)을 bash로 바꿔 타이머와 서버를 함께 띄운다. `args`는 문자열
  # 하나이고, JSON 객체면 entrypoint와 cmd를 따로 정한다(Runpod 플러그인의 create-pod 도구 설명).
  args = jsonencode({ entrypoint = ["/bin/bash", "-c"], cmd = [local.script[each.key]] })
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
      cost_per_hr = runpod_pod.server[pod].cost
    }
  ]
}
