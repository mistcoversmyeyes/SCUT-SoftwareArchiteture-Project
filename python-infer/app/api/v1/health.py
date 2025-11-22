"""
健康检查路由
"""
from fastapi import APIRouter
from datetime import datetime
from core.models import HealthResponse

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


@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def health_check():
    """
    检查所有产线服务状态

    返回各产线的运行状态、模型加载情况、GPU可用性等信息
    """
    pipelines = {}

    # 检查OCRv5
    if ocr_v5_service:
        pipelines["ocrv5"] = ocr_v5_service.health_check()
    else:
        pipelines["ocrv5"] = {"status": "unavailable", "error": "Service not initialized"}

    # 检查VL
    if vl_service:
        pipelines["vl"] = vl_service.health_check()
    else:
        pipelines["vl"] = {"status": "unavailable", "error": "Service not initialized"}

    # 检查StructureV3
    if structure_v3_service:
        pipelines["structure"] = structure_v3_service.health_check()
    else:
        pipelines["structure"] = {"status": "unavailable", "error": "Service not initialized"}

    # 判断整体状态
    all_ready = all(
        p.get("status") == "ready" for p in pipelines.values()
    )
    any_ready = any(
        p.get("status") == "ready" for p in pipelines.values()
    )

    if all_ready:
        overall_status = "healthy"
    elif any_ready:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now().isoformat(),
        pipelines=pipelines
    )
