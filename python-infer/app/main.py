# -*- coding: utf-8 -*-
"""
FastAPI主入口文件
OCR多产线统一网关
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from typing import Optional
from core.config import settings
from api.v1 import ocr, health
from services.ocr_v5 import OCRv5Service
from services.vl_service import VLService
from services.structure_v3 import StructureV3Service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 全局服务实例
ocr_v5_service: Optional[OCRv5Service] = None
vl_service: Optional[VLService] = None
structure_v3_service: Optional[StructureV3Service] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global ocr_v5_service, vl_service, structure_v3_service

    # 启动时初始化服务
    logger.info("=" * 60)
    logger.info("OCR Multi-Pipeline API 启动中...")
    logger.info("=" * 60)

    try:
        # 初始化OCRv5服务
        logger.info("正在初始化 OCRv5 服务...")
        ocr_v5_service = OCRv5Service(
            lang = 'ch',
            device = 'gpu:0',
        )
        logger.info("✓ OCRv5 服务就绪")

        # 初始化StructureV3服务
        logger.info("正在初始化 StructureV3 服务...")
        structure_v3_service = StructureV3Service(
            device='gpu:0',
            use_table_recognition=True,
            use_formula_recognition=True,
            use_region_detection=True,
        )
        logger.info("✓ StructureV3 服务就绪")

        # 初始化VL服务
        logger.info("正在初始化 PaddleOCR-VL 服务...")
        vl_service = VLService()
        logger.info(f"✓ VL 服务就绪 (vLLM端点: {settings.VLLM_ENDPOINT})")

        # 将服务实例注入到路由模块
        ocr.set_services(ocr_v5_service, vl_service, structure_v3_service)
        health.set_services(ocr_v5_service, vl_service, structure_v3_service)

        logger.info("=" * 60)
        logger.info("✓ 所有服务初始化完成，API网关已启动")
        logger.info(f"API文档: http://0.0.0.0:8090{settings.API_V1_PREFIX}/docs")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"✗ 服务初始化失败: {str(e)}", exc_info=True)
        raise

    yield

    # 关闭时清理
    logger.info("正在关闭服务...")
    ocr_v5_service = None
    vl_service = None
    structure_v3_service = None
    logger.info("服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(ocr.router, prefix=settings.API_V1_PREFIX, tags=["OCR"])
app.include_router(health.router, prefix=settings.API_V1_PREFIX, tags=["Health"])


@app.get("/", summary="根路径")
async def root():
    """API根路径信息"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "description": settings.DESCRIPTION,
        "docs_url": f"{settings.API_V1_PREFIX}/docs",
        "health_check": f"{settings.API_V1_PREFIX}/health",
        "pipelines": {
            "ocrv5": f"{settings.API_V1_PREFIX}/text",
            "vl": f"{settings.API_V1_PREFIX}/document",
            "structure": f"{settings.API_V1_PREFIX}/table"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8090,
        reload=False,  # 禁用自动重载，避免模型加载时被中断
        log_level="info"
    )
