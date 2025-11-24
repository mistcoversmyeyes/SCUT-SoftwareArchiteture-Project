"""
测试 OCRv5 服务的 JSON 输出格式
"""
import sys
import json
sys.path.insert(0, '/home/yuming/SCUT/SCUT_25_Fall/SCUT-SoftwareArchiteture-Project/python-infer/app')

from services.ocr_v5 import OCRv5Service

def test_ocr_v5(image_path: str):
    print("=" * 50)
    print("初始化模型")
    print("=" * 50)
    service = OCRv5Service(
        # 可选以下参数
        # lang = 'ch',
        # ocr_version ='PP-OCRv5',
        # device ='gpu:0',
        # use_doc_orientation_classify = True,
        # use_doc_unwarping = True,
        # use_textline_orientation = True
    )

    print("=" * 50)
    print("执行推理")
    print("=" * 50)
    result = service.predict(image_path)

    print("=" * 50)
    print("结果")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_ocr_v5.py <图片路径>")
        sys.exit(1)
    test_ocr_v5(sys.argv[1])