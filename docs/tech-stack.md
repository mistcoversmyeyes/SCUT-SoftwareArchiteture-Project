# 技术栈说明

## PaddleOCR vs PaddleX

- **PaddleX**: 飞桨训推一体化框架（通用）
- **PaddleOCR**: PaddleX针对OCR领域的**简化版本**

> 参考：[官方文档说明](https://www.paddleocr.ai/latest/version3.x/paddleocr_and_paddlex.html#32)

---

## 本项目使用

| 组件                | 技术栈    | 部署位置   | 原因                                |
| ------------------- | --------- | ---------- | ----------------------------------- |
| **OCRv5产线**       | PaddleOCR | 宿主机     | 轻量级，`pip install paddleocr`即可 |
| **StructureV3产线** | PaddleOCR | 宿主机     | 同上，PaddleOCR内置                 |
| **VL产线**          | PaddleX   | Docker容器 | 官方仅提供PaddleX部署方案           |
| **API网关**         | FastAPI   | 宿主机     | 统一封装三个产线                    |

---

## 环境说明

### 宿主机环境
```bash
# 只需安装PaddleOCR（无需PaddleX）
pip install paddleocr fastapi
```

```python
# 使用PaddleOCR API
from paddleocr import PaddleOCR, PPStructure

ocr_v5 = PaddleOCR(use_angle_cls=True, lang='ch')
structure_v3 = PPStructure(layout=True, table=True)
```

### Docker VL容器
```yaml
# compose.yaml已部署
paddleocr-vl-api:
  # 容器内部使用PaddleX
  command: paddlex --serve --pipeline PaddleOCR-VL
```

```python
# 宿主机通过HTTP调用
import requests
response = requests.post("http://localhost:8080/infer", files={"file": image})
```

---
## 为什么VL用Docker？

| 方面 | OCRv5/StructureV3 | PaddleOCR-VL |
|-----|------------------|--------------|
| **模型类型** | 传统CNN | 0.9B多模态大模型 |
| **推理框架** | Paddle Inference | vLLM（需编译） |
| **部署复杂度** | 简单（pip install） | 复杂（特殊依赖） |
| **官方支持** | PaddleOCR直接支持 | 仅PaddleX服务化部署 |
| **环境隔离** | 无需隔离 | 避免依赖冲突 |

---

## 架构图

```
React前端
   ↓ HTTP
FastAPI网关（宿主机:8090）
   ├── PaddleOCR.OCR() → OCRv5（本地推理）
   ├── PaddleOCR.PPStructure() → StructureV3（本地推理）
   └── requests.post() → VL（HTTP调用）
          ↓
       Docker VL容器（8080）
          └── paddlex --serve
```

---

## 常见误解澄清

### ❌ 错误理解
- "PaddleX是PaddleOCR的升级版"
- "宿主机需要安装PaddleX才能调用VL"
- "所有产线都应该用Docker部署"

### ✅ 正确理解
- **PaddleOCR是PaddleX的OCR简化版**（专注OCR领域）
- **宿主机只需PaddleOCR**，VL通过HTTP调用Docker容器
- **仅VL需要Docker**，因为它依赖复杂的vLLM环境

---

## 技术选型决策

### 为何宿主机用PaddleOCR而非PaddleX？

1. **轻量级**：`pip install paddleocr`一行命令完成
2. **专注性**：PaddleOCR专为OCR优化，API更简洁
3. **稳定性**：PaddleOCR成熟度高（v2.x→v3.0多年迭代）
4. **文档丰富**：OCRv5/StructureV3的PaddleOCR示例更多

### 为何VL必须用PaddleX？

1. **官方限制**：PaddleOCR-VL仅在PaddleX中提供
2. **服务化支持**：`paddlex --serve`开箱即用
3. **vLLM集成**：PaddleX已集成vLLM加速框架

---

## 依赖安装清单

### 宿主机
```bash
conda create -n ocr-api python=3.10
conda activate ocr-api

# 核心依赖
pip install paddleocr      # OCRv5 + StructureV3
pip install fastapi        # API框架
pip install uvicorn        # ASGI服务器
pip install python-multipart  # 文件上传
pip install pillow numpy   # 图像处理
pip install requests       # HTTP客户端（调用VL）
```

### Docker容器
```bash
# 无需手动安装，docker-compose已配置
docker-compose up -d paddleocr-vl-api paddleocr-vlm-server
```

---

## 版本信息

| 组件      | 版本   | 说明                   |
| --------- | ------ | ---------------------- |
| PaddleOCR | 3.0+   | 包含OCRv5和StructureV3 |
| PaddleX   | 3.0+   | 仅Docker容器内使用     |
| FastAPI   | 0.100+ | API框架                |
| Python    | 3.10   | 宿主机环境             |
| CUDA      | 12.6+  | GPU推理                |
| Docker    | 20.10+ | 容器运行时             |
