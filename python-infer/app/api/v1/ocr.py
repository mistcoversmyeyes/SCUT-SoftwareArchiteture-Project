"""
OCR API路由层
处理OCRv5/VL/StructureV3三个端点
"""
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
import time
import numpy as np
from PIL import Image
from io import BytesIO
import logging

from core.models import OCRResponse, MetricsModel, ErrorResponse
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局服务实例（在main.py中初始化）
ocr_v5_service = None
vl_service = None
structure_v3_service = None


def set_services(ocr_v5, vl, structure_v3):
    """设置服务实例"""
    global ocr_v5_service, vl_service, structure_v3_service
    ocr_v5_service = ocr_v5
    vl_service = vl
    structure_v3_service = structure_v3


async def process_upload_file(file: UploadFile) -> tuple[np.ndarray, float, float]:
    """
    处理上传文件

    Returns:
        (image_array, upload_time, file_size_kb)
    """
    start_time = time.time()

    # 验证文件类型
    file_ext = file.filename.split('.')[-1].lower()
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}。仅支持: {settings.ALLOWED_EXTENSIONS}"
        )

    # 读取文件
    contents = await file.read()
    file_size_kb = len(contents) / 1024

    # 验证文件大小
    if file_size_kb > settings.MAX_FILE_SIZE_MB * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"文件过大: {file_size_kb:.1f}KB。最大支持: {settings.MAX_FILE_SIZE_MB}MB"
        )

    # 转换为numpy数组
    try:
        image = Image.open(BytesIO(contents))
        image_array = np.array(image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"图片解析失败: {str(e)}")

    upload_time = time.time() - start_time

    return image_array, upload_time, file_size_kb


@router.post("/text", response_model=OCRResponse, summary="基础文本识别（OCRv5）")
async def ocr_text(
    file: UploadFile = File(..., description="图片文件"),
    compress: bool = Form(False, description="是否前端已压缩")
):
    """
    使用PP-OCRv5进行基础文本识别

    - 适用场景：纯文本文档、证件照片、简单截图
    - 推理位置：宿主机本地
    - 预期耗时：~0.95s
    """
    if not ocr_v5_service:
        raise HTTPException(status_code=503, detail="OCRv5服务未初始化")

    total_start = time.time()

    try:
        # 处理文件上传
        image_array, upload_time, file_size_kb = await process_upload_file(file)

        # 执行OCR推理
        prediction = ocr_v5_service.predict(image_array)

        # 构造响应
        total_time = time.time() - total_start

        return OCRResponse(
            success=True,
            pipeline="ocrv5",
            result=prediction["result"],
            metrics=MetricsModel(
                total_time=total_time,
                inference_time=prediction["inference_time"],
                upload_time=upload_time,
                preprocess_time=None,
                image_size_kb=file_size_kb,
                compressed=compress,
                source=prediction["source"]
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCRv5推理失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")


@router.post("/document", response_model=OCRResponse, summary="复杂文档解析（PaddleOCR-VL）")
async def ocr_document(
    file: UploadFile = File(..., description="图片或PDF文件"),
    compress: bool = Form(False, description="是否前端已压缩")
):
    """
    使用PaddleOCR-VL进行复杂文档解析

    - 适用场景：学术论文、财务报表、技术文档
    - 推理位置：宿主机对象 → Docker vLLM(8118)
    - 预期耗时：~1.65s
    """
    if not vl_service:
        raise HTTPException(status_code=503, detail="VL服务未初始化")

    total_start = time.time()

    try:
        # 处理文件上传
        image_array, upload_time, file_size_kb = await process_upload_file(file)

        # 执行VL推理
        prediction = vl_service.predict(image_array)

        # 构造响应
        total_time = time.time() - total_start

        return OCRResponse(
            success=True,
            pipeline="vl",
            result=prediction["result"],
            metrics=MetricsModel(
                total_time=total_time,
                inference_time=prediction["inference_time"],
                upload_time=upload_time,
                preprocess_time=None,
                image_size_kb=file_size_kb,
                compressed=compress,
                source=prediction["source"]
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"VL推理失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")


@router.post("/table", response_model=OCRResponse, summary="表格识别（StructureV3）")
async def ocr_table(
    file: UploadFile = File(..., description="图片文件"),
    compress: bool = Form(False, description="是否前端已压缩"),
    return_html: bool = Form(True, description="是否返回HTML格式表格")
):
    """
    使用PP-StructureV3进行专业表格识别

    - 适用场景：Excel截图、数据报表、统计表格
    - 推理位置：宿主机本地
    - 预期耗时：~1.5s
    """
    if not structure_v3_service:
        raise HTTPException(status_code=503, detail="StructureV3服务未初始化")

    total_start = time.time()

    try:
        # 处理文件上传
        image_array, upload_time, file_size_kb = await process_upload_file(file)

        # 执行Structure推理
        prediction = structure_v3_service.predict(image_array, return_html=return_html)

        # 构造响应
        total_time = time.time() - total_start

        return OCRResponse(
            success=True,
            pipeline="structure",
            result=prediction["result"],
            metrics=MetricsModel(
                total_time=total_time,
                inference_time=prediction["inference_time"],
                upload_time=upload_time,
                preprocess_time=None,
                image_size_kb=file_size_kb,
                compressed=compress,
                source=prediction["source"]
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"StructureV3推理失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"推理失败: {str(e)}")
