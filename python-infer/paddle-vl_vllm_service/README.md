# PaddleOCR VLLM Service Deploy

该目录封装了基于 Docker Compose 的 PaddleOCR-VL vLLM 推理服务启动方案，方便在单机 GPU 环境下快速拉起、调整和维护服务。

## 目录结构

- `docker_vlm_deploy.sh`：启动、停止及调试服务的入口脚本（`docker compose` 薄包装）。
- `docker-compose.yaml`：服务编排文件，定义容器镜像、启动命令、挂载和 GPU 相关设置。
- `vllm_config.yaml`：传入 `paddleocr genai_server` 的 vLLM 配置，包含显存利用率和并发控制等核心参数。

## 前置要求

1. 已安装 Docker（推荐 24.0+）并启用 NVIDIA Container Toolkit，使容器可访问宿主机 GPU。
2. 已安装 Docker Compose v2（`docker compose` 子命令）。
3. 宿主机具备至少 8 GB 显存，且可以使用 `--network host`（例如 Linux 环境）。

## 快速启动

```bash
cd python-infer/paddle-vl_vllm_service_deploy
./docker_vlm_deploy.sh up -d
```

脚本默认执行 `docker compose up`，可自行添加 `-d` 背景运行。等待日志出现 `The PaddleOCR GenAI server has been started` 即表示 8118 端口的 vLLM API 就绪。

### 健康检查

```bash
curl http://localhost:8118/health
```

返回 `200 OK` 即代表服务在线。可进一步调用 `/v1/chat/completions` 等 OpenAI 兼容接口联调前端。

## 日志与停止

- 查看日志：`docker compose logs -f`（在本目录下执行）。
- 停止并清理：`./docker_vlm_deploy.sh down`。

## 调参与扩展

- 修改 `vllm_config.yaml` 后重新 `up` 即可生效，可按需调整 `gpu-memory-utilization`、`max-num-seqs`、`max-model-len` 等参数。
- 如需切换模型或端口，编辑 `docker-compose.yaml` 中的 `command` 段或 `--port` 参数。
- 需要自定义镜像或挂载额外模型文件时，可在同一 Compose 服务中添加新的 volume 或环境变量。

## 故障排查

- **显存不足**：降低 `vllm_config.yaml` 中的 `max-model-len`/`max-num-batched-tokens`，或进一步减小 `gpu-memory-utilization`。
- **端口占用**：调整 `docker-compose.yaml` 中的 `--port`，并在调用端同步修改。
- **GPU 识别失败**：确保主机已安装 NVIDIA 驱动与 Container Toolkit，且容器运行时设置 `runtime: nvidia`、`NVIDIA_VISIBLE_DEVICES=all`。

如需将此服务纳入更大的编排体系，可直接引用本目录的 Compose 文件或将相关 service 段落复制到您的主项目 `docker-compose.yaml` 中。