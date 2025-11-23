"""
统一响应模型
"""
from pydantic import BaseModel, Field
from typing import Any, Optional, Literal


class MetricsModel(BaseModel):
    """性能指标模型"""

    total_time: float = Field(..., description="总耗时(秒)")
    inference_time: float = Field(..., description="推理耗时(秒)")
    upload_time: Optional[float] = Field(None, description="上传耗时(秒)")
    preprocess_time: Optional[float] = Field(None, description="预处理耗时(秒)")
    image_size_kb: float = Field(..., description="图片大小(KB)")
    compressed: bool = Field(..., description="是否压缩")
    source: Literal["local", "docker"] = Field(..., description="推理位置")


class OCRResponse(BaseModel):
    """OCR统一响应模型"""

    success: bool = Field(..., description="是否成功")
    pipeline: Literal["ocrv5", "vl", "structure"] = Field(..., description="使用的产线")
    result: Any = Field(..., description="识别结果")
    metrics: MetricsModel = Field(..., description="性能指标")


class ErrorResponse(BaseModel):
    """错误响应模型"""

    success: bool = Field(False, description="是否成功")
    error: str = Field(..., description="错误描述")
    code: int = Field(..., description="错误码")
    detail: Optional[str] = Field(None, description="详细信息")


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: Literal["healthy", "degraded", "unhealthy"] = Field(..., description="服务状态")
    timestamp: str = Field(..., description="检查时间")
    pipelines: dict = Field(..., description="各产线状态")
