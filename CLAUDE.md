# Claude Code 会话记录

## 会话上下文

- **项目**: 6人团队OCR系统 - 软件架构课程PA作业
- **截止日期**: 2025-11-30
- **当前分支**: `main`
- **架构**: 单容器vLLM (端口8118) + 宿主机模型实例化

## 本次会话关键事件

### 1. OCRv5 API修正
**问题**: PaddleOCR升级到3.x后API发生变化

**修改内容** (`/python-infer/app/services/ocr_v5.py`):
- ❌ 移除参数: `use_gpu`, `show_log`, `cls`, `det`, `rec`
- ✅ 新增参数: `lang`, `ocr_version`, `device`, `use_doc_orientation_classify`, `use_doc_unwarping`, `use_textline_orientation`
- 方法变更: `self.ocr.ocr()` → `self.ocr.predict()`
- 结果解析: 使用新的JSON结构 (`rec_texts`, `rec_scores`, `dt_polys`, `rec_boxes`)

**遇到的错误及修复**:
1. **AttributeError: set_optimization_level** → 更新requirements.txt使用paddlepaddle-gpu==3.2.0
2. **ValueError: too many values to unpack** → 重写`_format_result()`适配新格式
3. **TypeError: ndarray is not JSON serializable** → 添加`.tolist()`转换numpy数组

**最终返回格式**:
```json
{
  "result": {
    "text": "#\n如果是列表，\n取第一个元素",
    "regions": [
      {
        "text": "#",
        "score": 0.9977329969406128,
        "polygon": [[28, 34], [47, 34], [47, 57], [28, 57]],
        "bbox": [28, 34, 47, 57]
      }
    ],
    "detected_lines": 3
  },
  "inference_time": 0.7665205001831055,
  "source": "local"
}
```

### 2. Requirements.txt更新
```txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
python-multipart==0.0.20
pillow==11.0.0
numpy==2.2.1
paddleocr[all]
# 需要从官方源安装GPU版本:
# pip install paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
opencv-python==4.10.0.84
opencv-contrib-python==4.10.0.84
```

### 3. API端点更新

**OCRv5** (`/ocr/text`):
- ❌ 移除参数: `lang`, `cls`, `det`, `rec`
- 简化为单一端点,所有配置在服务初始化时完成

**StructureV3** (`/ocr/table`):
- ❌ 移除参数: `return_html`
- ✅ 新增参数: `output_format` (可选值: "json" | "markdown")

### 4. StructureV3服务重构

**构造函数参数** (`/python-infer/app/services/structure_v3.py`):
```python
def __init__(
    self,
    device: str = 'gpu:0',                          # 推理设备 (gpu:0/cpu)
    use_doc_orientation_classify: bool = False,     # 文档方向分类
    use_doc_unwarping: bool = False,                # 文本图像矫正
    use_textline_orientation: bool = False,         # 文本行方向分类
    use_table_recognition: bool = True,             # 表格识别
    use_formula_recognition: bool = True,           # 公式识别
    use_region_detection: bool = True,              # 区域检测
):
```

**新增功能**:
- ✅ 支持输出格式选择: JSON (结构化) 或 Markdown (文档格式)
- ✅ `_get_markdown_result()`: 返回markdown_texts
- ✅ `_format_json_result()`: 返回layout/tables/formulas/parsing_res

### 5. 文档更新

**已完成**:
- ✅ `/docs/api-reference.md` - OCRv5部分已更新实际响应格式
- ⏸️ `/docs/api-reference.md` - StructureV3部分待完成(会话中断)

**待完成内容**:
1. 更新StructureV3章节标题 "表格识别" → "文档结构识别"
2. 更新请求参数表 (替换`return_html`为`output_format`)
3. 添加JSON和Markdown两种格式的响应示例

## 测试脚本简化

**用户反馈**: "我不需要那么多打印,只需要必要的阶段分割线,我自己有眼睛会看代码"

**简化后的测试脚本** (`/python-infer/test/test_ocr_v5.py`):
```python
def test_ocr_v5(image_path: str):
    print("=" * 50)
    print("初始化模型")
    print("=" * 50)
    service = OCRv5Service()

    print("=" * 50)
    print("执行推理")
    print("=" * 50)
    image = Image.open(image_path)
    result = service.predict(np.array(image))

    print("=" * 50)
    print("结果")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result
```

## 核心技术要点

### PaddleOCR 3.x API变化
- **旧版**: `ocr.ocr(image, cls=True, det=True, rec=True)` → 返回嵌套列表
- **新版**: `ocr.predict(image)` → 返回带字段的字典
  - `rec_texts`: 识别文本列表
  - `rec_scores`: 置信度列表
  - `dt_polys`: 检测多边形坐标
  - `rec_boxes`: 识别框坐标

### Numpy数组序列化
**问题**: `Object of type ndarray is not JSON serializable`
**解决**: `poly.tolist() if hasattr(poly, 'tolist') else poly`

### 项目哲学
用户明确表示: **"我们是玩具项目"**
- ❌ 不需要向后兼容旧版本格式
- ❌ 不需要过度的错误处理
- ✅ 保持代码简洁
- ✅ 只实现必要功能

## 待办任务

### 立即待办
1. **完成StructureV3 API文档更新** - 会话中断前正在进行
2. **提供可选改进建议** (用户要求: 必须不增加复杂度)
3. **测试StructureV3服务** - 验证实际输出格式

### 项目TODO (来自TodoWrite)
- ⏳ 集成测试多产线性能(对比 OCRv5 vs VL)
- ⏳ 实现 React 前端
- ⏳ 编写性能测试脚本
- ⏳ Day 8-14: Go 微服务架构升级
- ⏳ Day 15-21: 实验数据分析、报告撰写与最终交付

## Git状态 (会话开始时)
```
Current branch: main

Modified:
  M python-infer/app/api/v1/ocr.py
  M python-infer/app/services/structure_v3.py

Untracked:
  ?? .vscode/

Recent commits:
  e1d9f51 feat(ocr): 优化OCRv5服务，简化参数，更新文档和测试用例
  e97f4ba feat(python-infer/api): Initial commit of FastAPI project structure
  5eaa250 feat(python-infer): 实现docker化部署Paddle-VL VLLM服务及添加技术文档
  9989bfa initial commit
```

## 用户关键反馈
1. "删除对旧版格式的兼容,别考虑那么多,我们是玩具项目"
2. "我不需要那么多打印,只需要必要的阶段分割线"
3. "为啥需要自己手动安装,不能够写在里面吗" (关于requirements.txt)
4. 要求提供 "必须是不增加复杂度改进"

---

**最后更新**: 2025-11-23
**会话状态**: 等待完成StructureV3文档更新和改进建议
