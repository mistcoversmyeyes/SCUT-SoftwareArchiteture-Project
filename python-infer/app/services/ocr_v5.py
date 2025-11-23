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

    def __init__(
        self,
        lang: str = 'ch',
        ocr_version: str = 'PP-OCRv5',
        device: str = 'gpu:0',
        use_doc_orientation_classify: bool = False,
        use_doc_unwarping: bool = False,
        use_textline_orientation: bool = False
    ):
        """
        初始化OCRv5模型

        Args:
            lang: 语言代码 (ch/en/ja等)
            ocr_version: OCR版本 (PP-OCRv5/PP-OCRv4)
            device: 推理设备 (gpu:0/cpu)
            use_doc_orientation_classify: 是否启用文档方向分类
            use_doc_unwarping: 是否启用文本图像矫正
            use_textline_orientation: 是否启用文本行方向分类
        """
        logger.info("初始化OCRv5模型...")
        self.ocr = PaddleOCR(
            lang=lang,
            ocr_version=ocr_version,
            device=device,
            use_doc_orientation_classify=use_doc_orientation_classify,
            use_doc_unwarping=use_doc_unwarping,
            use_textline_orientation=use_textline_orientation
        )
        logger.info("OCRv5模型加载完成")

    def predict(self, image: np.ndarray) -> dict:
        """
        执行OCR推理

        Args:
            image: numpy数组格式的图片

        Returns:
            包含识别结果和推理时间的字典
        """
        start_time = time.time()

        try:
            # 执行OCR推理
            result = self.ocr.predict(image)
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

    def _format_result(self, raw_result) -> dict:
        """
        格式化OCR原始结果

        Args:
            raw_result: PaddleOCR返回的原始结果

        Returns:
            格式化后的结果字典
        """
        # 处理空结果
        if not raw_result:
            return {
                "text": "",
                "regions": [],
                "detected_lines": 0
            }

        # 如果是列表，取第一个元素
        if isinstance(raw_result, list):
            if len(raw_result) == 0:
                return {"text": "", "regions": [], "detected_lines": 0}
            raw_result = raw_result[0]

        # 提取结果数据
        rec_texts = raw_result.get("rec_texts", []) if isinstance(raw_result, dict) else []
        rec_scores = raw_result.get("rec_scores", []) if isinstance(raw_result, dict) else []
        dt_polys = raw_result.get("dt_polys", []) if isinstance(raw_result, dict) else []
        rec_boxes = raw_result.get("rec_boxes", []) if isinstance(raw_result, dict) else []

        if not rec_texts:
            return {
                "text": "",
                "regions": [],
                "detected_lines": 0
            }

        regions = []
        for i, text in enumerate(rec_texts):
            region = {
                "text": text,
                "score": float(rec_scores[i]) if i < len(rec_scores) else 0.0
            }

            # 添加边界框信息（转为列表以支持JSON序列化）
            if i < len(dt_polys):
                poly = dt_polys[i]
                region["polygon"] = poly.tolist() if hasattr(poly, 'tolist') else poly
            if i < len(rec_boxes):
                bbox = rec_boxes[i]
                region["bbox"] = bbox.tolist() if hasattr(bbox, 'tolist') else bbox

            regions.append(region)

        return {
            "text": "\n".join(rec_texts),
            "regions": regions,
            "detected_lines": len(regions)
        }

    def health_check(self) -> dict:
        """健康检查"""
        return {
            "status": "ready",
            "model_loaded": self.ocr is not None
        }
