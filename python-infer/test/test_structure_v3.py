"""
测试 StructureV3 服务的 JSON 和 Markdown 输出格式
"""
import sys
import json
sys.path.insert(0, '/home/yuming/SCUT/SCUT_25_Fall/SCUT-SoftwareArchiteture-Project/python-infer/app')

from services.structure_v3 import StructureV3Service

def test_structure_v3_json(image_path: str):
    """测试JSON格式输出"""
    print("\n" + "=" * 50)
    print("测试 JSON 格式输出")
    print("=" * 50)

    print("=" * 50)
    print("初始化模型")
    print("=" * 50)
    service = StructureV3Service(
        device='gpu:0',
        use_table_recognition=True,
        use_formula_recognition=True,
        use_region_detection=True
    )

    print("=" * 50)
    print("执行推理 (output_format='json')")
    print("=" * 50)
    result = service.predict(image_path, output_format="json")

    print("=" * 50)
    print("JSON 结果")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result


def test_structure_v3_markdown(image_path: str):
    """测试Markdown格式输出"""
    print("\n" + "=" * 50)
    print("测试 Markdown 格式输出")
    print("=" * 50)

    print("=" * 50)
    print("初始化模型")
    print("=" * 50)
    service = StructureV3Service(
        device='gpu:0',
        use_table_recognition=True,
        use_formula_recognition=True,
        use_region_detection=True
    )

    print("=" * 50)
    print("执行推理 (output_format='markdown')")
    print("=" * 50)
    result = service.predict(image_path, output_format="markdown")

    print("=" * 50)
    print("Markdown 结果")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_structure_v3.py <图片路径>")
        sys.exit(1)

    image_path = sys.argv[1]

    # 测试两种格式
    json_result = test_structure_v3_json(image_path)
    markdown_result = test_structure_v3_markdown(image_path)