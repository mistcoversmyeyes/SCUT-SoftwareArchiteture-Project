"""
PP-StructureV3服务层
用于表格和文档结构识别
"""
import time
import numpy as np
from paddleocr import PPStructure
import logging

logger = logging.getLogger(__name__)


class StructureV3Service:
    """PP-StructureV3服务"""

    def __init__(self, use_gpu: bool = True, show_log: bool = False):
        """初始化StructureV3模型"""
        logger.info("初始化StructureV3模型...")
        self.structure = PPStructure(
            layout=True,         # 启用版面分析
            table=True,          # 启用表格识别
            ocr=True,            # 启用OCR
            use_gpu=use_gpu,
            show_log=show_log
        )
        logger.info("StructureV3模型加载完成")

    def predict(self, image: np.ndarray, return_html: bool = True) -> dict:
        """
        执行表格识别推理

        Args:
            image: numpy数组格式的图片
            return_html: 是否返回HTML格式表格

        Returns:
            包含识别结果和推理时间的字典
        """
        start_time = time.time()

        try:
            # 执行Structure推理
            result = self.structure(image)
            inference_time = time.time() - start_time

            # 格式化结果
            formatted_result = self._format_result(result, return_html)

            return {
                "result": formatted_result,
                "inference_time": inference_time,
                "source": "local"
            }

        except Exception as e:
            logger.error(f"StructureV3推理失败: {str(e)}")
            raise

    def _format_result(self, raw_result: list, return_html: bool) -> dict:
        """
        格式化Structure原始结果

        Args:
            raw_result: PPStructure返回的原始结果
            return_html: 是否返回HTML格式

        Returns:
            格式化后的结果字典
        """
        tables = []
        layout = []

        for item in raw_result:
            item_type = item.get('type', 'unknown')
            bbox = item.get('bbox', [])

            if item_type == 'table':
                table_info = {
                    "bbox": bbox,
                    "rows": 0,
                    "cols": 0,
                    "confidence": item.get('score', 0.0)
                }

                # 提取表格HTML和单元格信息
                if 'res' in item:
                    table_html = item['res'].get('html', '')
                    if return_html:
                        table_info["html"] = table_html

                    # 解析单元格
                    cells_data = item['res'].get('cell_bbox', [])
                    if cells_data:
                        table_info["cells"] = cells_data
                        # 估算行列数
                        table_info["rows"] = len(set(cell[1] for cell in cells_data))
                        table_info["cols"] = len(set(cell[0] for cell in cells_data))

                tables.append(table_info)

            # 记录所有布局元素
            layout.append({
                "type": item_type,
                "bbox": bbox,
                "content": item.get('res', {}).get('text', '') if item_type == 'text' else None,
                "table_id": len(tables) - 1 if item_type == 'table' else None
            })

        return {
            "tables": tables,
            "layout": layout,
            "tables_count": len(tables)
        }

    def health_check(self) -> dict:
        """健康检查"""
        return {
            "status": "ready",
            "model_loaded": self.structure is not None,
            "gpu_available": self.structure.use_gpu if hasattr(self.structure, 'use_gpu') else False
        }
