# OCR Multi-Pipeline API

统一OCR服务网关，支持OCRv5/VL/StructureV3多产线

## 项目结构

```
app/
├── main.py                 # FastAPI主入口
├── requirements.txt        # Python依赖
├── .env.example           # 环境变量示例
├── core/                  # 核心模块
│   ├── config.py         # 配置管理
│   └── models.py         # 响应模型
├── services/             # 服务层
│   ├── ocr_v5.py        # OCRv5服务
│   ├── vl_service.py    # VL服务（宿主机实例化VL对象）
│   └── structure_v3.py  # StructureV3服务
└── api/v1/              # API路由
    ├── ocr.py          # OCR端点
    └── health.py       # 健康检查
```

## 快速开始

### 1. 安装依赖

```bash
conda create -n ocr-api python=3.10
conda activate ocr-api
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 根据实际情况编辑 .env
```

### 3. 启动vLLM Docker容器

```bash
cd ../paddle-vl_vllm_service
./docker_vlm_deploy.sh up -d
# 等待服务ready: curl http://localhost:8118/health
```

### 4. 启动FastAPI服务

```bash
# 开发模式（自动重载）
uvicorn main:app --host 0.0.0.0 --port 8090 --reload

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8090 --workers 4
```

## API端点

### 根路径
- `GET /` - 项目信息

### OCR服务
- `POST /api/v1/text` - 基础文本识别（OCRv5）
- `POST /api/v1/document` - 复杂文档解析（VL）
- `POST /api/v1/table` - 表格识别（StructureV3）

### 监控
- `GET /api/v1/health` - 健康检查

### 文档
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc文档

## 使用示例

### curl测试

```bash
# OCRv5文本识别
curl -X POST http://localhost:8090/api/v1/text \
  -F "file=@test.jpg" \
  -F "compress=false" \
  | jq .

# VL文档解析
curl -X POST http://localhost:8090/api/v1/document \
  -F "file=@document.jpg" \
  | jq .

# 表格识别
curl -X POST http://localhost:8090/api/v1/table \
  -F "file=@table.jpg" \
  -F "return_html=true" \
  | jq .

# 健康检查
curl http://localhost:8090/api/v1/health | jq .
```

### Python测试

```python
import requests

# OCRv5
with open('test.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8090/api/v1/text',
        files={'file': f},
        data={'compress': 'false'}
    )
    print(response.json())
```

## 架构说明

### 单容器架构（核心）

```
宿主机 FastAPI (端口 8090)
  ├── PaddleOCR OCRv5 (本地推理)
  ├── PaddleOCR StructureV3 (本地推理)
  └── PaddleOCR VL对象 (本地实例化)
       ↓ 依赖vLLM推理端点
Docker容器 (端口 8118)
  └── vLLM推理服务
```

### 关键技术要点

**VL服务初始化**：
```python
# services/vl_service.py
vl_ocr = PaddleOCR(
    use_vl=True,                        # 启用VL模型
    vllm_url="http://localhost:8118",   # vLLM推理端点
    use_gpu=False,                      # 宿主机不需要GPU
    show_log=False
)
```

- 宿主机只需 `pip install paddleocr`（无需PaddleX）
- Docker仅负责vLLM推理加速
- 统一PaddleOCR API（OCRv5和VL相同调用方式）

## 故障排查

### vLLM端点不可用
```bash
# 检查Docker容器状态
cd ../paddle-vl_vllm_service
docker compose ps

# 查看日志
docker compose logs paddleocr-vllm | tail -50

# 重启容器
./docker_vlm_deploy.sh down
./docker_vlm_deploy.sh up -d
```

### 显存不足
编辑 `../paddle-vl_vllm_service/vllm_config.yaml`：
```yaml
gpu-memory-utilization: 0.7  # 降至0.5
max-model-len: 2048          # 降至1024
```

## 性能参考

| 产线 | 典型耗时 | 推理位置 | 用途 |
|-----|---------|---------|------|
| OCRv5 | ~0.95s | 宿主机 | 简单文本 |
| VL | ~1.65s | Docker vLLM | 复杂文档 |
| StructureV3 | ~1.5s | 宿主机 | 表格识别 |

*测试环境：NVIDIA RTX 3090, CUDA 12.8*
