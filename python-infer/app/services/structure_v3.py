"""
PP-StructureV3服务层
用于表格和文档结构识别
"""
import time
import numpy as np
from paddleocr import PPStructureV3
from typing import Literal
import logging

logger = logging.getLogger(__name__)


class StructureV3Service:
    """PP-StructureV3服务"""

    def __init__(
        self,
        device: str = 'gpu:0',                          # 推理设备 (gpu:0/cpu)
        use_doc_orientation_classify: bool = False,     # 文档方向分类
        use_doc_unwarping: bool = False,                # 文本图像矫正
        use_textline_orientation: bool = False,         # 文本行方向分类
        use_table_recognition: bool = True,             # 表格识别
        use_formula_recognition: bool = True,           # 公式识别
        use_region_detection: bool = True,              # 区域检测
        # use_seal_recognition: bool = False,           # 印章识别
        # use_chart_recognition: bool = False,          # 图表解析
        # layout_threshold: float = 0.5,                # 版面检测阈值
        # layout_nms: bool = True,                      # 版面NMS后处理
        # text_det_limit_side_len: int = 960,           # 文本检测边长限制
    ):
        """初始化StructureV3模型"""
        logger.info("初始化StructureV3模型...")
        self.model = PPStructureV3(
            device=device,
            use_doc_orientation_classify=use_doc_orientation_classify,
            use_doc_unwarping=use_doc_unwarping,
            use_textline_orientation=use_textline_orientation,
            use_table_recognition=use_table_recognition,
            use_formula_recognition=use_formula_recognition,
            use_region_detection=use_region_detection,
        )
        logger.info("StructureV3模型加载完成")

    def predict(
        self,
        image: np.ndarray,
        output_format: Literal["json", "markdown"] = "json"
    ) -> dict:
        """
        执行文档结构识别推理

        Args:
            image: numpy数组格式的图片
            output_format: 输出格式 ("json" 或 "markdown")

        Returns:
            包含识别结果和推理时间的字典
        """
        start_time = time.time()

        try:
            # 执行Structure推理
            result = self.model.predict(image)
            inference_time = time.time() - start_time

            # 根据输出格式处理结果
            if output_format == "markdown":
                formatted_result = self._get_markdown_result(result)
            else:
                formatted_result = self._format_json_result(result)

            return {
                "result": formatted_result,
                "inference_time": inference_time,
                "source": "local"
            }

        except Exception as e:
            logger.error(f"StructureV3推理失败: {str(e)}")
            raise

    def _get_markdown_result(self, raw_result) -> dict:
        """
        获取Markdown格式结果

        Args:
            raw_result: PPStructureV3返回的原始结果

        Returns:
            包含markdown内容的字典
        """
        # 结果是列表，取第一个
        if isinstance(raw_result, list) and len(raw_result) > 0:
            res = raw_result[0]
        else:
            res = raw_result

        # 提取markdown相关字段
        markdown_texts = res.get("markdown_texts", "") if isinstance(res, dict) else ""

        return {
            "markdown": markdown_texts,
            "format": "markdown"
        }

    def _format_json_result(self, raw_result) -> dict:
        """
        格式化JSON结果

        Args:
            raw_result: PPStructureV3返回的原始结果

        Returns:
            格式化后的结果字典
        """
        # 结果是列表，取第一个
        if isinstance(raw_result, list) and len(raw_result) > 0:
            res = raw_result[0]
        else:
            res = raw_result

        if not isinstance(res, dict):
            return {"layout": [], "tables": [], "formulas": [], "format": "json"}

        # 提取版面检测结果
        layout_det_res = res.get("layout_det_res", {})
        boxes = layout_det_res.get("boxes", []) if isinstance(layout_det_res, dict) else []

        # 提取解析结果列表
        parsing_res_list = res.get("parsing_res_list", [])

        # 提取表格结果
        table_res_list = res.get("table_res_list", [])
        tables = []
        for table in table_res_list:
            if isinstance(table, dict):
                tables.append({
                    "html": table.get("pred_html", ""),
                    "cell_ocr_res": table.get("cell_ocr_res", [])
                })

        # 提取公式结果
        formula_res_list = res.get("formula_res_list", [])

        # 转换numpy数组为列表
        def to_serializable(obj):
            if hasattr(obj, 'tolist'):
                return obj.tolist()
            return obj

        layout = []
        for box in boxes:
            if isinstance(box, dict):
                layout.append({
                    "label": box.get("label", ""),
                    "bbox": to_serializable(box.get("coordinate", [])),
                    "score": float(box.get("score", 0.0))
                })

        return {
            "layout": layout,
            "tables": tables,
            "formulas": formula_res_list,
            "parsing_res": parsing_res_list,
            "format": "json"
        }

    def health_check(self) -> dict:
        """健康检查"""
        return {
            "status": "ready",
            "model_loaded": self.model is not None
        }