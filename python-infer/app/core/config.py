"""
FastAPI配置文件
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""

    # API基础配置
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "OCR Multi-Pipeline API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "统一OCR服务网关，支持OCRv5/VL/StructureV3多产线"

    # CORS配置
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # 文件上传限制
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set[str] = {"jpg", "jpeg", "png", "bmp", "pdf"}

    # Docker vLLM配置
    VLLM_ENDPOINT: str = "http://localhost:8118"
    VLLM_TIMEOUT: int = 30

    # OCR模型配置
    USE_GPU: bool = True
    SHOW_LOG: bool = False

    # 性能监控
    ENABLE_METRICS: bool = True
    METRICS_EXPORT_DIR: str = "./metrics"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
