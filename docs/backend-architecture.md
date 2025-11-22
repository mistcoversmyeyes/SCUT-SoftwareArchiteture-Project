# 后端架构设计

## 1. 系统架构概览

### 1.1 三层架构

```
┌─────────────────────────────────────────────────────────┐
│  前端层 (React)                                          │
│  - 图片上传                                              │
│  - 可选压缩（计算分区实验）                               │
│  - 产线选择（OCRv5 / VL / StructureV3）                  │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP POST
                 ↓
┌─────────────────────────────────────────────────────────┐
│  API网关层 (FastAPI on 宿主机:8090)                      │
│  - 统一路由：/api/v1/ocr/{text|document|table}          │
│  - 请求验证、文件处理                                     │
│  - 性能监控（计时、数据收集）                             │
│  - 响应标准化                                            │
└─────┬───────────────┬──────────────────┬────────────────┘
      │               │                  │
      ↓               ↓                  ↓
┌──────────┐   ┌──────────┐    ┌────────────────────────┐
│ OCRv5    │   │Structure │    │ PaddleOCR VL对象       │
│ (本地)   │   │V3 (本地) │    │ (本地实例化)           │
└──────────┘   └──────────┘    └───────┬────────────────┘
                                       │ 依赖vLLM推理端点
                                       ↓
                              ┌─────────────────────────┐
                              │ Docker容器:8118         │
                              │ vLLM推理服务            │
                              └─────────────────────────┘
```

### 1.2 技术栈分层

| 层级 | 组件 | 技术栈 | 部署位置 |
|-----|------|--------|---------|
| 前端 | React应用 | React + Axios | 浏览器 |
| 网关 | FastAPI | FastAPI + Uvicorn | 宿主机:8090 |
| 产线1 | OCRv5 | PaddleOCR | 宿主机（本地推理） |
| 产线2 | StructureV3 | PaddleOCR.PPStructure | 宿主机（本地推理） |
| 产线3 | VL | PaddleOCR (本地实例化VL对象) | 宿主机（依赖Docker vLLM端点） |
| 推理 | vLLM推理端点 | vLLM Server | Docker容器:8118 |

---

## 2. 产线集成方式

### 2.1 OCRv5/StructureV3（本地推理）

**实现方式**：
```python
from paddleocr import PaddleOCR, PPStructure

# 初始化（应用启动时）
ocr_v5 = PaddleOCR(
    use_angle_cls=True,  # 启用方向分类器
    lang='ch',           # 中文模型
    use_gpu=True,        # GPU加速
    show_log=False       # 关闭调试日志
)

structure_v3 = PPStructure(
    layout=True,         # 启用版面分析
    table=True,          # 启用表格识别
    ocr=True,            # 启用OCR
    use_gpu=True
)

# 推理调用
result = ocr_v5.ocr(image_array, cls=True)
```

**特点**：
- ✅ 轻量级，pip install即可
- ✅ 推理速度快（0.95s验证）
- ✅ 资源占用低（~2GB显存）
- ❌ 功能单一（仅文本识别）

---

### 2.2 PaddleOCR-VL（本地实例化+远程vLLM端点）

**实现方式**：
```python
from paddleocr import PaddleOCR

# 初始化VL对象(应用启动时)
# vllm_url指向Docker容器的vLLM推理端点
vl_ocr = PaddleOCR(
    use_vl=True,                        # 启用VL模型
    vllm_url="http://localhost:8118",   # vLLM推理端点
    use_gpu=False,                      # 宿主机不需要GPU(推理在Docker)
    show_log=False
)

# 推理调用(与OCRv5相同的API)
result = vl_ocr.ocr(image_array, use_vl=True)
```

**特点**：
- ✅ SOTA精度（官方benchmark领先）
- ✅ 支持复杂文档（表格、公式、图表）
- ✅ 宿主机无需复杂环境（仅paddleocr库）
- ✅ Docker仅提供vLLM推理加速
- ❌ 推理耗时较长（~1.5-2s）
- ❌ 显存占用大（0.9B模型在Docker）

---

## 3. API端点设计

### 3.1 路由映射

| HTTP端点 | 产线 | 推理位置 | 用途 |
|---------|------|---------|------|
| `POST /api/v1/ocr/text` | OCRv5 | 宿主机 | 基础文本识别 |
| `POST /api/v1/ocr/document` | VL | Docker | 复杂文档解析 |
| `POST /api/v1/ocr/table` | StructureV3 | 宿主机 | 表格识别 |
| `GET /api/v1/health` | - | - | 健康检查 |
| `GET /api/v1/metrics` | - | - | 性能统计 |

### 3.2 请求处理流程

```
1. 接收请求
   ↓
2. 参数验证（文件类型、大小限制）
   ↓
3. 图片预处理
   ├── 如果compress=true → 前端已压缩
   └── 如果compress=false → 原图
   ↓
4. 路由分发
   ├── /text → OCRv5本地推理
   ├── /document → HTTP调用Docker VL
   └── /table → StructureV3本地推理
   ↓
5. 性能监控
   ├── 记录总耗时
   ├── 记录推理耗时
   └── 记录图片大小
   ↓
6. 响应标准化
   {
     "success": true,
     "pipeline": "ocrv5",
     "result": {...},
     "metrics": {...}
   }
```

### 3.3 统一响应格式

```python
# 成功响应
{
  "success": true,
  "pipeline": "ocrv5" | "vl" | "structure",
  "result": {
    # OCRv5/VL: {"text": "..."}
    # StructureV3: {"tables": [...], "layout": [...]}
  },
  "metrics": {
    "total_time": 1.2,        # 总耗时（秒）
    "inference_time": 0.95,   # 推理耗时（秒）
    "network_time": 0.25,     # 网络传输（仅VL）
    "image_size_kb": 450,     # 图片大小
    "compressed": false,      # 是否压缩
    "source": "local" | "docker"  # 推理位置
  }
}

# 错误响应
{
  "success": false,
  "error": "Invalid file format",
  "code": 400
}
```

---

## 4. 计算分区策略

### 4.1 分区维度

基于PA要求"尝试在浏览器/移动设备与远程服务器之间划分模块"，本项目支持：

| 分区方式 | 前端职责 | 后端职责 | 实验对比点 |
|---------|---------|---------|-----------|
| **方案1：前端压缩** | 图片压缩（Canvas API） | OCR推理 | 网络传输↓ vs 精度↓ |
| **方案2：原图上传** | 仅上传 | 图片处理 + OCR推理 | 网络传输↑ vs 精度保持 |

**实现示例**：
```javascript
// 前端压缩选项
async function uploadImage(file, compress) {
  if (compress) {
    // Canvas压缩到800px宽度
    const compressed = await compressImage(file, 800);
    formData.append('file', compressed);
    formData.append('compressed', 'true');
  } else {
    formData.append('file', file);
    formData.append('compressed', 'false');
  }
}
```

### 4.2 性能权衡分析

| 场景 | 图片大小 | 网络环境 | 推荐方案 | 理由 |
|-----|---------|---------|---------|------|
| 高清文档 | 5MB+ | WiFi | 前端压缩 | 减少传输时间 > 轻微精度损失 |
| 简单文本 | <1MB | 5G | 原图上传 | 网络足够快，保持精度 |
| 复杂表格 | 3MB | 4G | 前端压缩 | VL模型对中等分辨率足够 |
| 移动设备 | 2MB | 4G | 前端压缩 | 节省流量 |

### 4.3 实验数据收集

FastAPI自动记录每次请求的分区指标：

```python
# 伪代码
metrics = {
    "upload_time": time_upload,      # 文件上传耗时
    "preprocess_time": time_preprocess,  # 预处理耗时
    "inference_time": time_inference,    # 推理耗时
    "total_time": time_total,
    "image_size_kb": size_kb,
    "compressed": is_compressed,
    "network": request.headers.get("X-Network-Type", "unknown")  # 前端传入
}
```

导出CSV用于PA报告实验章节：
```csv
timestamp,pipeline,compress,image_size_kb,network,upload_time,inference_time,total_time,accuracy
2025-11-22T10:00:00,ocrv5,false,2500,wifi,0.3,0.95,1.25,0.98
2025-11-22T10:01:00,ocrv5,true,800,wifi,0.1,0.95,1.05,0.96
2025-11-22T10:02:00,vl,false,2500,4g,1.2,1.8,3.0,0.99
```

---

## 5. 关键技术决策

### 5.1 为何混合部署多产线？

**决策**：同时部署OCRv5（本地）+ VL（Docker）+ StructureV3（本地）

**理由**：
1. **满足PA Part B-2要求**：多种计算分区方式对比
2. **性能vs精度权衡**：
   - OCRv5：快速响应（<1s），适合简单文本
   - VL：高精度（SOTA），适合复杂文档
3. **风险对冲**：
   - 如果VL部署失败，OCRv5已验证可用
   - StructureV3作为表格识别备选方案
4. **报告素材丰富**：
   - 不同产线性能对比图表
   - 架构演进分析（从单一到混合）

### 5.2 为何VL需要Docker容器？

**决策**：VL使用Docker，OCRv5/StructureV3使用宿主机

**技术原因**：
| 产线 | 模型类型 | 推理框架 | 部署复杂度 |
|-----|---------|---------|-----------|
| OCRv5 | 传统CNN | Paddle Inference | 简单（pip install） |
| StructureV3 | Pipeline组合 | Paddle Inference | 简单 |
| VL | 0.9B多模态大模型 | vLLM | 复杂（需编译、特殊依赖） |

**实际考量**：
- VL官方提供现成Docker镜像（已配置vLLM + safetensors）
- 避免宿主机环境污染（CUDA版本、Python依赖冲突）
- 资源隔离（VL独占GPU 0，防止显存溢出影响其他产线）

### 5.3 为何不全部Docker化？

**决策**：仅VL使用Docker，其他产线宿主机

**理由**：
1. **开发效率**：宿主机代码修改即生效，Docker需重新构建镜像
2. **调试便利**：本地推理可直接打印日志、断点调试
3. **资源优化**：OCRv5/StructureV3轻量，无需容器隔离
4. **符合PA实验需求**：
   - 宿主机 = "浏览器/移动设备侧计算"的服务器模拟
   - Docker = "云端/远程服务器"
   - 混合部署 = 展示不同分区策略

---

## 6. 数据流详解

### 6.1 OCRv5数据流（本地推理）

```
前端React
  ↓ multipart/form-data (POST /api/v1/ocr/text)
FastAPI接收文件
  ↓
读取为字节流 → PIL.Image → numpy.ndarray
  ↓
ocr_v5.ocr(image_array, cls=True)
  ├── 文本检测（PP-OCRv5_det）
  ├── 方向分类（ppocr_mobile_cls）
  └── 文本识别（PP-OCRv5_rec）
  ↓
返回: [[[bbox1, text1, score1]], [[bbox2, text2, score2]], ...]
  ↓
格式化为统一JSON
  ↓
返回前端
```

**耗时分布**（典型2MB图片）：
- 文件上传：0.1s
- 图片解码：0.05s
- 文本检测：0.4s
- 方向分类：0.1s
- 文本识别：0.35s
- **总计**：~0.95s

### 6.2 VL数据流（本地对象+远程vLLM）

```
前端React
  ↓ multipart/form-data (POST /api/v1/ocr/document)
FastAPI接收文件
  ↓
读取为字节流 → PIL.Image → numpy.ndarray
  ↓
vl_ocr.ocr(image_array, use_vl=True)  # 宿主机PaddleOCR VL对象
  ├── 图像预处理（宿主机）
  ├── HTTP请求 → Docker vLLM端点(8118)
  └── vLLM推理
       ├── 视觉编码器（提取图像特征）
       ├── 多模态融合（图像+文本prompt）
       └── 文本解码器（生成结构化结果）
  ↓
返回JSON → 格式化 → 返回前端
```

**耗时分布**（典型2MB图片）：
- 文件上传：0.1s
- 图像预处理：0.05s（宿主机）
- vLLM推理：1.5s（Docker）
  - HTTP往返：0.02s
  - 图像编码：0.3s
  - 多模态推理：1.0s
  - 结果解析：0.18s
- **总计**：~1.65s

---

## 7. 架构优势分析

### 7.1 满足PA要求对照表

| PA要求 | 本架构实现 | 对应文件/模块 |
|-------|----------|--------------|
| Part A: 计算密集型应用 | OCR推理（CNN+Transformer） | 所有产线 |
| Part A: 延迟敏感型 | 性能监控、多产线选择 | FastAPI metrics |
| Part B-1: 模块结构分析 | 清晰三层架构图 | 本文档第1节 |
| Part B-2: 计算分区 | 前端压缩 vs 原图上传 | 本文档第4节 |
| Part B-3: 性能实验 | metrics自动收集 → CSV | deployment-guide.md |

### 7.2 可扩展性

**水平扩展**：
```yaml
# docker-compose.yaml
paddleocr-vl-api:
  deploy:
    replicas: 3  # 启动3个VL容器
  # FastAPI使用负载均衡调用
```

**垂直扩展**：
```python
# 多GPU并行（如果有4块GPU）
ocr_v5_gpu0 = PaddleOCR(use_gpu=True, gpu_id=0)
ocr_v5_gpu1 = PaddleOCR(use_gpu=True, gpu_id=1)
# 请求轮询分发
```

### 7.3 容错设计

```python
# VL服务降级
try:
    result = call_vl_service(image)
except requests.Timeout:
    # 超时降级到StructureV3
    result = structure_v3(image)
    result["fallback"] = "vl_timeout"
```

---

## 8. 后续优化方向

1. **缓存机制**：相同图片MD5哈希缓存结果
2. **异步处理**：FastAPI异步端点 + 任务队列
3. **批量推理**：合并小图批量调用（提升GPU利用率）
4. **模型量化**：INT8量化减少显存占用
5. **边缘部署**：WASM编译OCRv5到浏览器（Go阶段探索）

---

## 附录：架构演进路径

### Phase 1: Python MVP（当前）
- 宿主机FastAPI + Docker VL
- 适用于快速验证、性能测试

### Phase 2: Go微服务（Day 8-14）
```
Go API Gateway (8090)
  ├── gRPC → Python OCR服务（8091）
  ├── gRPC → Docker VL服务（8080）
  └── WASM OCR模块（浏览器端）
```

### Phase 3: 生产优化（可选）
- Kubernetes编排
- Prometheus监控
- Redis缓存
- Nginx负载均衡
