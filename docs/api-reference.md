# API 接口文档

## 基础信息

- **Base URL**: `http://localhost:8090/api/v1`
- **协议**: HTTP/1.1
- **认证方式**: 无（内网部署）
- **请求格式**: `multipart/form-data` (文件上传)
- **响应格式**: `application/json`
- **字符编码**: UTF-8

---

## 通用规范

### 请求头

```http
Content-Type: multipart/form-data
```

### 响应状态码

| 状态码 | 含义 | 示例场景 |
|-------|------|---------|
| 200 | 成功 | 推理完成 |
| 400 | 请求错误 | 文件格式不支持、参数缺失 |
| 500 | 服务器错误 | 推理失败、模型未加载 |
| 503 | 服务不可用 | Docker VL容器未启动 |
| 504 | 超时 | VL推理超过10s |

### 统一响应格式

#### 成功响应
```json
{
  "success": true,
  "pipeline": "ocrv5" | "vl" | "structure",
  "result": {
    // 具体结果（各端点不同）
  },
  "metrics": {
    "total_time": 1.234,
    "inference_time": 0.987,
    "upload_time": 0.123,
    "network_time": 0.050,
    "image_size_kb": 450,
    "compressed": false,
    "source": "local" | "docker"
  }
}
```

#### 错误响应
```json
{
  "success": false,
  "error": "错误描述",
  "code": 400,
  "detail": "详细错误信息（可选）"
}
```

---

## 端点列表

### 1. 基础文本识别（OCRv5）

#### `POST /ocr/text`

**功能**：使用PP-OCRv5进行基础文本识别，适用于纯文本场景。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| file | File | 是 | 图片文件（支持jpg/png/bmp） |
| compress | boolean | 否 | 是否前端已压缩（默认false） |

**请求示例**：

```bash
curl -X POST http://localhost:8090/api/v1/ocr/text \
  -F "file=@test_image.jpg"
```
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('http://localhost:8090/api/v1/ocr/text', {
  method: 'POST',
  body: formData
});
const result = await response.json();
```

**响应示例**：

```json
{
  "success": true,
  "pipeline": "ocrv5",
  "result": {
    "text": "#\n如果是列表，\n取第一个元素",
    "regions": [
      {
        "text": "#",
        "score": 0.9977329969406128,
        "polygon": [[28, 34], [47, 34], [47, 57], [28, 57]],
        "bbox": [28, 34, 47, 57]
      },
      {
        "text": "如果是列表，",
        "score": 0.9989599585533142,
        "polygon": [[57, 30], [214, 30], [214, 60], [57, 60]],
        "bbox": [57, 30, 214, 60]
      },
      {
        "text": "取第一个元素",
        "score": 0.9998381733894348,
        "polygon": [[231, 29], [407, 29], [407, 63], [231, 63]],
        "bbox": [231, 29, 407, 63]
      }
    ],
    "detected_lines": 3
  },
  "metrics": {
    "total_time": 0.82,
    "inference_time": 0.77,
    "upload_time": 0.05,
    "image_size_kb": 45.2,
    "compressed": false,
    "source": "local"
  }
}
```

---

### 2. 文档结构解析（PaddleOCR-VL）

#### `POST /ocr/document`

**功能**：使用PaddleOCR-VL进行复杂文档解析，支持表格、公式、图表等结构化内容。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| file | File | 是 | 图片或PDF文件 |
| compress | boolean | 否 | 是否前端已压缩（默认false） |
| parse_table | boolean | 否 | 是否解析表格（默认true） |
| parse_formula | boolean | 否 | 是否解析公式（默认true） |
| parse_chart | boolean | 否 | 是否解析图表（默认true） |

**请求示例**：

```bash
curl -X POST http://localhost:8090/api/v1/ocr/document \
  -F "file=@complex_doc.jpg" \
  -F "parse_table=true"
```

**响应示例**：

```json
{
  "success": true,
  "pipeline": "vl",
  "result": {
    "text": "文档完整文本",
    "layout": [
      {
        "type": "title",
        "bbox": [x1, y1, x2, y2],
        "content": "文档标题"
      },
      {
        "type": "paragraph",
        "bbox": [x1, y1, x2, y2],
        "content": "段落文本..."
      },
      {
        "type": "table",
        "bbox": [x1, y1, x2, y2],
        "content": {
          "html": "<table>...</table>",
          "rows": 5,
          "cols": 3,
          "cells": [
            ["单元格1", "单元格2", "单元格3"],
            ["数据1", "数据2", "数据3"]
          ]
        }
      },
      {
        "type": "formula",
        "bbox": [x1, y1, x2, y2],
        "content": {
          "latex": "E = mc^2",
          "text": "E equals m times c squared"
        }
      }
    ],
    "elements_count": {
      "title": 1,
      "paragraph": 5,
      "table": 2,
      "formula": 3,
      "chart": 1
    }
  },
  "metrics": {
    "total_time": 2.456,
    "inference_time": 1.890,
    "upload_time": 0.150,
    "network_time": 0.080,
    "docker_processing_time": 1.810,
    "image_size_kb": 2500,
    "compressed": false,
    "source": "docker"
  }
}
```

---

### 3. 表格识别（PP-StructureV3）

#### `POST /ocr/table`

**功能**：使用PP-StructureV3进行专业表格识别，适用于财务报表、数据表格等场景。

**请求参数**：

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| file | File | 是 | 图片文件 |
| compress | boolean | 否 | 是否前端已压缩（默认false） |
| layout | boolean | 否 | 是否进行版面分析（默认true） |
| return_html | boolean | 否 | 是否返回HTML格式（默认true） |

**请求示例**：

```bash
curl -X POST http://localhost:8090/api/v1/ocr/table \
  -F "file=@table.jpg" \
  -F "return_html=true"
```

**响应示例**：

```json
{
  "success": true,
  "pipeline": "structure",
  "result": {
    "tables": [
      {
        "bbox": [x1, y1, x2, y2],
        "html": "<table><tr><td>...</td></tr></table>",
        "cells": [
          ["表头1", "表头2", "表头3"],
          ["数据1", "数据2", "数据3"]
        ],
        "rows": 5,
        "cols": 3,
        "confidence": 0.95
      }
    ],
    "layout": [
      {
        "type": "text",
        "bbox": [x1, y1, x2, y2],
        "content": "表格标题"
      },
      {
        "type": "table",
        "bbox": [x1, y1, x2, y2],
        "table_id": 0
      }
    ],
    "tables_count": 1
  },
  "metrics": {
    "total_time": 1.567,
    "inference_time": 1.234,
    "upload_time": 0.100,
    "layout_time": 0.456,
    "table_time": 0.778,
    "image_size_kb": 1200,
    "compressed": false,
    "source": "local"
  }
}
```

---

### 4. 健康检查

#### `GET /health`

**功能**：检查服务及各产线状态。

**请求示例**：

```bash
curl http://localhost:8090/api/v1/health
```

**响应示例**：

```json
{
  "status": "healthy",
  "timestamp": "2025-11-22T10:30:00Z",
  "pipelines": {
    "ocrv5": {
      "status": "ready",
      "model_loaded": true,
      "gpu_available": true,
      "last_inference": "2025-11-22T10:29:45Z"
    },
    "vl": {
      "status": "ready",
      "docker_status": "running",
      "api_url": "http://localhost:8080",
      "health_check": "passed",
      "last_inference": "2025-11-22T10:28:30Z"
    },
    "structure": {
      "status": "ready",
      "model_loaded": true,
      "gpu_available": true,
      "last_inference": null
    }
  },
  "system": {
    "gpu_memory_used": "6.5GB",
    "gpu_memory_total": "24GB",
    "cpu_usage": "15%",
    "uptime": "2h30m"
  }
}
```

**错误状态示例**：

```json
{
  "status": "degraded",
  "pipelines": {
    "ocrv5": {"status": "ready"},
    "vl": {
      "status": "unavailable",
      "error": "Docker container not running",
      "docker_status": "exited"
    },
    "structure": {"status": "ready"}
  }
}
```

---

### 5. 性能统计

#### `GET /metrics`

**功能**：获取服务运行统计数据（用于PA实验报告）。

**请求示例**：

```bash
curl http://localhost:8090/api/v1/metrics
```

**响应示例**：

```json
{
  "total_requests": 1234,
  "requests_by_pipeline": {
    "ocrv5": 800,
    "vl": 300,
    "structure": 134
  },
  "average_times": {
    "ocrv5": {
      "total_time": 1.234,
      "inference_time": 0.987
    },
    "vl": {
      "total_time": 2.456,
      "inference_time": 1.890
    },
    "structure": {
      "total_time": 1.567,
      "inference_time": 1.234
    }
  },
  "compression_stats": {
    "total_compressed": 500,
    "total_uncompressed": 734,
    "avg_size_compressed_kb": 120,
    "avg_size_uncompressed_kb": 1500,
    "avg_time_compressed": 0.95,
    "avg_time_uncompressed": 1.45
  },
  "errors": {
    "total": 12,
    "by_type": {
      "timeout": 5,
      "invalid_file": 4,
      "inference_failed": 3
    }
  }
}
```

---

## 错误码说明

### 客户端错误（4xx）

| 错误码 | 错误信息 | 说明 | 解决方案 |
|-------|---------|------|---------|
| 400 | `File is required` | 未上传文件 | 检查请求中是否包含file字段 |
| 400 | `Invalid file format` | 文件格式不支持 | 仅支持jpg/png/bmp/pdf |
| 400 | `File size exceeds limit` | 文件过大 | 限制10MB以内 |
| 400 | `Invalid parameter` | 参数错误 | 检查参数类型和取值范围 |

### 服务器错误（5xx）

| 错误码 | 错误信息 | 说明 | 解决方案 |
|-------|---------|------|---------|
| 500 | `Model not loaded` | 模型未加载 | 重启服务，检查模型文件 |
| 500 | `Inference failed` | 推理失败 | 查看日志，可能是图片损坏 |
| 503 | `VL service unavailable` | VL容器未运行 | 启动Docker容器 |
| 504 | `Request timeout` | 请求超时 | 减小图片尺寸或增加超时时间 |

---

## 使用建议

### 1. 产线选择策略

```
简单文本识别 → /ocr/text (OCRv5)
  - 扫描文档
  - 证件照片
  - 简单截图

复杂文档解析 → /ocr/document (VL)
  - 学术论文（含公式）
  - 财务报表（含表格）
  - 技术文档（含图表）

纯表格识别 → /ocr/table (StructureV3)
  - Excel截图
  - 数据报表
  - 统计表格
```

### 2. 压缩参数使用建议

```
图片大小 > 2MB 且 网络环境 = 移动网络 → compress=true
图片大小 < 500KB → compress=false（避免无意义压缩）
需要高精度识别 → compress=false
```

### 3. 性能优化技巧

**批量处理**：
```python
# 不推荐：逐个请求
for img in images:
    result = call_api(img)

# 推荐：使用线程池并发
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=4) as executor:
    results = executor.map(call_api, images)
```

**超时设置**：
```python
# OCRv5：设置较短超时
requests.post(url, files=files, timeout=5)

# VL：设置较长超时
requests.post(url, files=files, timeout=15)
```

---

## 集成示例

### React前端完整示例

```javascript
import React, { useState } from 'react';
import axios from 'axios';

function OCRApp() {
  const [file, setFile] = useState(null);
  const [pipeline, setPipeline] = useState('text');
  const [compress, setCompress] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('compress', compress);

    try {
      const response = await axios.post(
        `http://localhost:8090/api/v1/ocr/${pipeline}`,
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );
      setResult(response.data);
    } catch (error) {
      console.error('OCR failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="file"
        onChange={(e) => setFile(e.target.files[0])}
      />
      <select onChange={(e) => setPipeline(e.target.value)}>
        <option value="text">基础文本（OCRv5）</option>
        <option value="document">文档解析（VL）</option>
        <option value="table">表格识别（StructureV3）</option>
      </select>
      <label>
        <input
          type="checkbox"
          checked={compress}
          onChange={(e) => setCompress(e.target.checked)}
        />
        前端压缩
      </label>
      <button type="submit" disabled={loading}>
        {loading ? '识别中...' : '开始识别'}
      </button>

      {result && (
        <div>
          <h3>识别结果</h3>
          <pre>{JSON.stringify(result, null, 2)}</pre>
          <p>耗时: {result.metrics.total_time}s</p>
        </div>
      )}
    </form>
  );
}
```

### Python性能测试脚本

```python
import requests
import time
import csv
from pathlib import Path

def benchmark_ocr(image_path, pipeline, compress=False):
    """性能测试单次调用"""
    url = f"http://localhost:8090/api/v1/ocr/{pipeline}"

    with open(image_path, 'rb') as f:
        files = {'file': f}
        data = {'compress': str(compress).lower()}

        start = time.time()
        response = requests.post(url, files=files, data=data)
        elapsed = time.time() - start

        result = response.json()
        return {
            'pipeline': pipeline,
            'compress': compress,
            'total_time': elapsed,
            'inference_time': result['metrics']['inference_time'],
            'image_size_kb': result['metrics']['image_size_kb'],
            'success': result['success']
        }

# 批量测试
test_images = list(Path('test_data').glob('*.jpg'))
results = []

for img in test_images:
    for pipeline in ['text', 'document', 'table']:
        for compress in [False, True]:
            result = benchmark_ocr(img, pipeline, compress)
            results.append(result)
            print(f"Tested {img.name} - {pipeline} - compress={compress}: {result['total_time']:.2f}s")

# 导出CSV
with open('benchmark_results.csv', 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=results[0].keys())
    writer.writeheader()
    writer.writerows(results)
```

---

## 附录

### 支持的图片格式

| 格式 | 扩展名 | 最大尺寸 | 说明 |
|-----|--------|---------|------|
| JPEG | .jpg, .jpeg | 10000x10000 | 推荐，压缩率高 |
| PNG | .png | 10000x10000 | 支持透明背景 |
| BMP | .bmp | 8000x8000 | 无损，文件较大 |
| PDF | .pdf | 单页 | 仅VL产线支持 |

### 性能参考值

| 场景 | 图片大小 | OCRv5 | VL | StructureV3 |
|-----|---------|-------|----|-----------  |
| 简单文本 | 500KB | 0.8s | 1.5s | 1.2s |
| 复杂文档 | 2MB | 1.2s | 2.5s | 2.0s |
| 表格文档 | 1.5MB | 1.0s | 2.2s | 1.8s |

*测试环境：NVIDIA RTX 3090, CUDA 12.8, WiFi网络*
