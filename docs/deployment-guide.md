# 后端部署指南

## 环境要求

### 硬件要求
- **GPU**: NVIDIA GPU with CUDA 12.6+ (已验证CUDA 12.8)
- **内存**: 16GB+
- **磁盘**: 20GB+ (含模型文件)

### 软件要求
- **操作系统**: Ubuntu 20.04+ / WSL2
- **Python**: 3.10
- **Docker**: 20.10+ with NVIDIA Container Toolkit
- **CUDA**: 12.6+ (宿主机)

---

## 部署架构

```
宿主机 FastAPI (端口 8090)
  ├── PaddleOCR OCRv5 (本地推理)
  ├── PaddleOCR StructureV3 (本地推理)
  └── PaddleOCR paddle-vl (调用docker 创建对象实例)

Docker 容器：
└── Docker paddleocr-vlm-server (端口 8118)
```

---

## 部署步骤

### Step 1: 验证Docker vLLM推理端点状态

vLLM推理服务应已部署在 `paddle-vl_vllm_service/` 目录：

```bash
cd /home/mistcovers/SCUT_25_Fall/SCUT-SoftwareArchiteture-Project/python-infer/paddle-vl_vllm_service

# 检查容器状态
docker compose ps

# 查看vLLM推理服务日志
docker compose logs paddleocr-vllm | tail -30
```

**预期输出**：
```
paddleocr-vllm   Up   network_mode: host (监听8118端口)
```

**健康检查**：
```bash
curl http://localhost:8118/health
# 预期返回: 200 OK
```

**启动命令**（如未启动）：
```bash
cd paddle-vl_vllm_service
./docker_vlm_deploy.sh up -d
# 等待日志显示: "The PaddleOCR GenAI server has been started"
```

---

### Step 2: 安装宿主机Python环境

创建独立conda环境（避免与现有OCR环境冲突）：

```bash
conda create -n ocr-api python=3.10 -y
conda activate ocr-api
```

安装核心依赖：

```bash
# PaddleOCR（本地推理OCRv5和StructureV3）
pip install paddleocr

# FastAPI框架
pip install fastapi uvicorn[standard] python-multipart

# 图像处理
pip install pillow numpy

# HTTP客户端（调用Docker VL服务）
pip install requests
```

**验证安装**：
```bash
python -c "from paddleocr import PaddleOCR; print('PaddleOCR OK')"
python -c "import fastapi; print('FastAPI OK')"
```

---

### Step 3: 首次运行下载模型

PaddleOCR首次使用会自动下载模型文件（~2GB），建议提前触发：

```bash
python << EOF
from paddleocr import PaddleOCR
# 下载OCRv5模型（检测+识别+方向分类器）
ocr = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=True)
print("OCRv5 models downloaded")
EOF
```

**模型存储位置**：
```
~/.paddleocr/
├── det/
│   └── ch_PP-OCRv5_det_infer/
├── rec/
│   └── ch_PP-OCRv5_rec_infer/
└── cls/
    └── ch_ppocr_mobile_v2.0_cls_infer/
```

---

### Step 4: 启动FastAPI服务

```bash
cd /home/mistcovers/SCUT_25_Fall/SCUT-SoftwareArchiteture-Project/python-infer/app

# 开发模式（自动重载）
uvicorn main:app --host 0.0.0.0 --port 8090 --reload

# 生产模式
# uvicorn main:app --host 0.0.0.0 --port 8090 --workers 4
```

**预期输出**：
```
INFO:     Uvicorn running on http://0.0.0.0:8090 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**验证服务**：
```bash
curl http://localhost:8090/
# 预期返回项目信息JSON
```

---

### Step 5: 测试各产线接口

准备测试图片：
```bash
# 使用项目中已有测试图片，或准备自己的
TEST_IMAGE="/path/to/test.jpg"
```

#### 测试OCRv5（本地推理）
```bash
curl -X POST http://localhost:8090/api/v1/ocr/text \
  -F "file=@${TEST_IMAGE}" \
  | jq .

# 预期: metrics.source = "local"
```

#### 测试PaddleOCR-VL（Docker推理）
```bash
curl -X POST http://localhost:8090/api/v1/ocr/document \
  -F "file=@${TEST_IMAGE}" \
  | jq .

# 预期: metrics.source = "docker"
```

#### 测试StructureV3（本地推理）
```bash
curl -X POST http://localhost:8090/api/v1/ocr/table \
  -F "file=@${TEST_IMAGE}" \
  | jq .

# 预期: result包含tables和layout字段
```

---

## 常见问题排查

### Q1: 宿主机需要安装PaddleX吗？
**A**: 不需要。宿主机只需`paddleocr`即可，PaddleX仅在Docker VL容器中使用。

### Q2: 如何判断vLLM推理端点是否ready？
**A**: 执行以下检查：
```bash
# 健康检查
curl http://localhost:8118/health

# 查看启动日志（模型加载完成标志）
cd paddle-vl_vllm_service
docker compose logs paddleocr-vllm | grep -i "PaddleOCR GenAI server has been started"
```

### Q3: OCRv5首次推理为什么慢？
**A**: 首次运行需下载模型（~2GB），后续推理会使用缓存模型。

### Q4: 显存不足怎么办？
**A**: 调整vLLM配置参数：
```bash
# 编辑 paddle-vl_vllm_service/vllm_config.yaml
# 降低以下参数：
gpu-memory-utilization: 0.7  
max-model-len: 2048          
max-num-batched-tokens: 2048 

# 重启容器生效
cd paddle-vl_vllm_service
./docker_vlm_deploy.sh down
./docker_vlm_deploy.sh up -d
```

### Q5: FastAPI端口8090被占用？
**A**: 修改启动命令中的端口号：
```bash
uvicorn main:app --host 0.0.0.0 --port 8091
```

### Q6: curl测试返回404？
**A**: 检查路由是否正确，访问API文档：
```bash
# 打开浏览器访问
http://localhost:8090/docs
```

---

## 多环境部署

### 局域网部署（默认）
- FastAPI监听 `0.0.0.0:8090`
- 局域网内其他设备通过 `http://<宿主机IP>:8090` 访问
- 适用于WiFi性能测试

### 外网部署（云服务器）
1. 修改CORS配置（`app/main.py`）：
   ```python
   allow_origins=["https://your-frontend-domain.com"]
   ```

2. 配置防火墙：
   ```bash
   sudo ufw allow 8090/tcp
   ```

3. 建议使用Nginx反向代理：
   ```nginx
   location /api {
       proxy_pass http://127.0.0.1:8090;
   }
   ```

### 多GPU环境
1. 修改 `compose.yaml` 中的GPU分配：
   ```yaml
   device_ids: ["1"]  # 使用第二块GPU
   ```

2. 宿主机指定GPU（如果有多块）：
   ```bash
   CUDA_VISIBLE_DEVICES=0 uvicorn main:app --port 8090
   ```

---

## 性能优化建议

### 预加载模型
在FastAPI启动时预加载模型，避免首次请求等待：
```python
# app/main.py
@app.on_event("startup")
async def startup_event():
    # 预加载OCRv5模型
    global ocr_v5
    ocr_v5 = PaddleOCR(use_angle_cls=True, lang='ch')
```

### 批量推理
如果需要处理大量图片，考虑批量API：
```python
@app.post("/api/v1/ocr/batch")
async def batch_ocr(files: List[UploadFile]):
    # 批量处理逻辑
```

### 异步调用
对于Docker VL服务的HTTP调用，使用异步客户端：
```bash
pip install httpx
```
```python
import httpx
async with httpx.AsyncClient() as client:
    response = await client.post(...)
```

---

## 下一步

部署完成后：
1. 查看 `api-reference.md` 了解完整API文档
2. 查看 `backend-architecture.md` 理解架构设计
3. 运行性能测试脚本收集实验数据
