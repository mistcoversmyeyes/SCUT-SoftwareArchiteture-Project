"""
PaddleOCR-VL服务层
宿主机实例化VL对象，依赖Docker vLLM推理端点
"""
import time
import numpy as np
from paddleocr import PaddleOCR
import logging
import requests

logger = logging.getLogger(__name__)


class VLService:
    """PaddleOCR-VL服务"""

    def __init__(self, vllm_url: str = "http://localhost:8118", show_log: bool = False):
        """
        初始化VL模型

        Args:
            vllm_url: Docker vLLM推理端点URL
            show_log: 是否显示日志
        """
        logger.info(f"初始化VL模型，vLLM端点: {vllm_url}")
        self.vllm_url = vllm_url

        try:
            # 关键：宿主机实例化VL对象，指向Docker vLLM端点
            self.vl_ocr = PaddleOCR(
                use_vl=True,                    # 启用VL模型
                vllm_url=vllm_url,              # vLLM推理端点
                use_gpu=False,                  # 宿主机不需要GPU（推理在Docker）
                show_log=show_log
            )
            logger.info("VL模型初始化完成")
        except Exception as e:
            logger.error(f"VL模型初始化失败: {str(e)}")
            self.vl_ocr = None
            raise

    def predict(self, image: np.ndarray) -> dict:
        """
        执行VL推理

        Args:
            image: numpy数组格式的图片

        Returns:
            包含识别结果和推理时间的字典
        """
        if self.vl_ocr is None:
            raise RuntimeError("VL模型未初始化")

        start_time = time.time()

        try:
            # 调用VL对象推理（内部会调用vLLM端点）
            result = self.vl_ocr.ocr(image, use_vl=True)
            inference_time = time.time() - start_time

            # 格式化结果
            formatted_result = self._format_result(result)

            return {
                "result": formatted_result,
                "inference_time": inference_time,
                "source": "docker"  # 实际推理在Docker vLLM
            }

        except Exception as e:
            logger.error(f"VL推理失败: {str(e)}")
            raise

    def _format_result(self, raw_result: list) -> dict:
        """
        格式化VL原始结果

        Args:
            raw_result: PaddleOCR-VL返回的原始结果

        Returns:
            格式化后的结果字典
        """
        if not raw_result or not raw_result[0]:
            return {
                "text": "",
                "layout": [],
                "elements_count": {}
            }

        # VL结果包含layout信息
        layout_elements = []
        element_counts = {}
        full_text = []

        for element in raw_result[0]:
            # 假设VL返回格式: [bbox, (type, content, score)]
            # 实际格式需要根据PaddleOCR-VL官方文档调整
            if len(element) >= 2:
                bbox, info = element[0], element[1]
                element_type = info.get('type', 'text') if isinstance(info, dict) else 'text'
                content = info.get('content', '') if isinstance(info, dict) else str(info)

                layout_elements.append({
                    "type": element_type,
                    "bbox": bbox,
                    "content": content
                })

                element_counts[element_type] = element_counts.get(element_type, 0) + 1
                full_text.append(content)

        return {
            "text": "\n".join(full_text),
            "layout": layout_elements,
            "elements_count": element_counts
        }

    def health_check(self) -> dict:
        """健康检查"""
        vllm_status = self._check_vllm_endpoint()

        return {
            "status": "ready" if self.vl_ocr and vllm_status else "unavailable",
            "model_loaded": self.vl_ocr is not None,
            "vllm_endpoint": self.vllm_url,
            "vllm_health": vllm_status
        }

    def _check_vllm_endpoint(self) -> bool:
        """检查vLLM端点是否可用"""
        try:
            response = requests.get(f"{self.vllm_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"vLLM端点检查失败: {str(e)}")
            return False
