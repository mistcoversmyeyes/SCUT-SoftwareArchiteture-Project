"""
PaddleOCR-VL服务层
宿主机实例化VL对象，依赖Docker vLLM推理端点
"""
import time
from typing import Literal
from paddleocr import PaddleOCRVL
from core.config import Settings
import logging
import requests

logger = logging.getLogger(__name__)


class VLService:
    """PaddleOCR-VL服务"""

    def __init__(
            self,
            vl_rec_backend: str = "vllm-server",
            vl_rec_server_url: str = "http://localhost:8118/v1",
            ):
        """
        初始化VL模型

        Args:
            vl_rec_backend: 推理后端类型
            vl_rec_server_url: Docker vLLM推理端点URL
        """
        logger.info(f"初始化VL模型，vLLM端点: {vl_rec_server_url}")
        self.vl_rec_server_url = vl_rec_server_url

        try:
            # 关键：宿主机实例化VL对象，指向Docker vLLM端点
            self.vl_ocr = PaddleOCRVL(
                vl_rec_backend=vl_rec_backend,           # 使用vLLM服务端
                vl_rec_server_url=vl_rec_server_url,     # vLLM推理端点
            )
            logger.info("VL模型初始化完成")
        except Exception as e:
            logger.error(f"VL模型初始化失败: {str(e)}")
            self.vl_ocr = None
            raise

    def predict(
        self,
        image_path: str,
        format: Literal["json", "markdown"] = "json") -> dict:
        """
        执行VL推理

        Args:
            image_path: 图片或PDF文件路径
            format: 返回格式，支持json或markdown

        Returns:
            包含识别结果和推理时间的字典
        """
        if self.vl_ocr is None:
            raise RuntimeError("VL模型未初始化")

        start_time = time.time()

        try:
            # 调用VL对象推理（内部会调用vLLM端点）
            result = self.vl_ocr.predict(image_path)
            inference_time = time.time() - start_time

            # 格式化结果
            if format == "markdown":
                formatted_result = self._format_markdown_result(result)
            else:
                # print(result)
                formatted_result = self._format_json_result(result)

            return {
                "result": formatted_result,
                "inference_time": inference_time,
                "source": "docker"  # 实际推理在Docker vLLM
            }

        except Exception as e:
            logger.error(f"VL推理失败: {str(e)}")
            raise

    def _format_json_result(self, raw_result: list) -> dict:
        """
        格式化VL原始结果为JSON格式

        Args:
            raw_result: PaddleOCR-VL返回的Result列表（实际是list[dict]）

        Returns:
            格式化后的结果字典
        """
        if not raw_result:
            return {
                "text": "",
                "layout": [],
                "elements_count": {},
                "pages": 0
            }

        # VL结果包含layout信息
        layout_elements = []
        element_counts = {}
        full_text = []

        # 处理所有页面的结果
        for result_dict in raw_result:
            # result_dict 本身就是字典，直接按键访问
            parsing_res_list = result_dict.get('parsing_res_list', [])
            page_index = result_dict.get('page_index', None)
            layout_det_res = result_dict.get('layout_det_res', {})

            # 从layout_det_res中获取boxes（版面检测结果）
            boxes = layout_det_res.get('boxes', []) if layout_det_res else []

            # 处理parsing_res_list中的每个块
            for item in parsing_res_list:
                # item是LayoutBlock对象，有自定义的__str__方法
                # 需要访问其属性
                if hasattr(item, 'label'):
                    label = getattr(item, 'label', '')
                    content = getattr(item, 'content', '')
                    bbox = getattr(item, 'bbox', None)

                    # 序列化bbox（可能是numpy数组）
                    if bbox is not None and hasattr(bbox, 'tolist'):
                        bbox = bbox.tolist()

                    element_data = {
                        "type": label,
                        "content": content,
                        "bbox": bbox
                    }

                    # 添加页码信息（如果是PDF）
                    if page_index is not None:
                        element_data["page"] = page_index

                    layout_elements.append(element_data)

                    # 统计元素类型
                    element_counts[label] = element_counts.get(label, 0) + 1

                    # 收集文本内容
                    if content:
                        full_text.append(content)

            # 如果parsing_res_list为空，尝试从boxes中提取
            if not parsing_res_list and boxes:
                for box in boxes:
                    label = box.get('label', '')
                    # boxes中没有content，只有位置信息
                    bbox = box.get('coordinate', None)

                    if bbox and hasattr(bbox, 'tolist'):
                        bbox = bbox.tolist()

                    element_data = {
                        "type": label,
                        "content": "",  # boxes中没有识别内容
                        "bbox": bbox,
                        "score": box.get('score', 0.0)
                    }

                    if page_index is not None:
                        element_data["page"] = page_index

                    layout_elements.append(element_data)
                    element_counts[label] = element_counts.get(label, 0) + 1

        return {
            "text": "\n".join(full_text),
            "layout": layout_elements,
            "elements_count": element_counts,
            "pages": len(raw_result)
        }

    def _format_markdown_result(self, raw_result: list) -> dict:
        """
        格式化VL原始结果为Markdown格式

        Args:
            raw_result: PaddleOCR-VL返回的Result对象列表

        Returns:
            包含markdown文本和元数据的字典
        """
        if not raw_result:
            return {
                "markdown": "",
                "elements_count": {},
                "pages": 0
            }

        markdown_texts = []
        element_counts = {}

        # 处理所有页面的结果
        for idx, result_dict in enumerate(raw_result):
            page_index = result_dict.get('page_index', idx)
            parsing_res_list = result_dict.get('parsing_res_list', [])

            # 收集本页的markdown内容
            page_content = []
            for item in parsing_res_list:
                if hasattr(item, 'label'):
                    label = getattr(item, 'label', '')
                    content = getattr(item, 'content', '')

                    # 统计元素类型
                    element_counts[label] = element_counts.get(label, 0) + 1

                    # 根据label类型格式化markdown
                    if content:
                        if 'title' in label.lower():
                            page_content.append(f"# {content}")
                        elif 'heading' in label.lower():
                            page_content.append(f"## {content}")
                        else:
                            page_content.append(content)

            # 如果是多页PDF，添加页面分隔符
            if len(raw_result) > 1 and page_content:
                markdown_texts.append(f"\n---\n## 第 {page_index + 1} 页\n\n" + "\n\n".join(page_content))
            elif page_content:
                markdown_texts.append("\n\n".join(page_content))

        return {
            "markdown": "\n".join(markdown_texts),
            "elements_count": element_counts,
            "pages": len(raw_result)
        }

    def health_check(self) -> dict:
        """健康检查"""
        vllm_status = self._check_vllm_endpoint()

        return {
            "status": "ready" if self.vl_ocr and vllm_status else "unavailable",
            "model_loaded": self.vl_ocr is not None,
            "vllm_endpoint": self.vl_rec_server_url,
            "vllm_health": vllm_status
        }

    def _check_vllm_endpoint(self) -> bool:
        """检查vLLM端点是否可用"""
        try:
            # 移除 /v1 后缀，健康检查端点不需要
            base_url = self.vl_rec_server_url.rstrip('/v1')
            response = requests.get(f"{base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"vLLM端点检查失败: {str(e)}")
            return False
