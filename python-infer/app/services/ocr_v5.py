"""
OCRv5服务层
使用PaddleOCR进行基础文本识别
"""
import time
import numpy as np
from paddleocr import PaddleOCR
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class OCRv5Service:
    """PP-OCRv5服务"""

    def __init__(self, use_gpu: bool = True, show_log: bool = False):
        """初始化OCRv5模型"""
        logger.info("初始化OCRv5模型...")
        self.ocr = PaddleOCR(
            use_angle_cls=True,  # 启用方向分类器
            lang='ch',           # 中文模型
            use_gpu=use_gpu,
            show_log=show_log
        )
        logger.info("OCRv5模型加载完成")

    def predict(
        self,
        image: np.ndarray,
        cls: bool = True,
        det: bool = True,
        rec: bool = True
    ) -> dict:
        """
        执行OCR推理

        Args:
            image: numpy数组格式的图片
            cls: 是否启用方向分类
            det: 是否启用文本检测
            rec: 是否启用文本识别

        Returns:
            包含识别结果和推理时间的字典
        """
        start_time = time.time()

        try:
            # 执行OCR推理
            result = self.ocr.ocr(image, cls=cls, det=det, rec=rec)
            inference_time = time.time() - start_time

            # 格式化结果
            formatted_result = self._format_result(result)

            return {
                "result": formatted_result,
                "inference_time": inference_time,
                "source": "local"
            }

        except Exception as e:
            logger.error(f"OCRv5推理失败: {str(e)}")
            raise

    def _format_result(self, raw_result: list) -> dict:
        """
        格式化OCR原始结果

        Args:
            raw_result: PaddleOCR返回的原始结果

        Returns:
            格式化后的结果字典
        """
        if not raw_result or not raw_result[0]:
            return {
                "text": "",
                "regions": [],
                "detected_lines": 0
            }

        regions = []
        full_text = []

        for line in raw_result[0]:
            bbox, (text, score) = line
            regions.append({
                "bbox": bbox,
                "text": text,
                "score": float(score)
            })
            full_text.append(text)

        return {
            "text": "\n".join(full_text),
            "regions": regions,
            "detected_lines": len(regions)
        }

    def health_check(self) -> dict:
        """健康检查"""
        return {
            "status": "ready",
            "model_loaded": self.ocr is not None,
            "gpu_available": self.ocr.use_gpu if hasattr(self.ocr, 'use_gpu') else False
        }
