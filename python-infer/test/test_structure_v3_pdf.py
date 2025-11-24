"""
测试 StructureV3 的 PDF 支持
"""
import sys
import json
sys.path.insert(0, '/home/yuming/SCUT/SCUT_25_Fall/SCUT-SoftwareArchiteture-Project/python-infer/app')

from services.structure_v3 import StructureV3Service

def test_pdf_json(pdf_path: str):
    """测试PDF的JSON格式输出"""
    print("=" * 50)
    print("测试 PDF - JSON 格式")
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
    result = service.predict(pdf_path, output_format="json")

    print("=" * 50)
    print("JSON 结果")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 统计信息
    layout_count = len(result['result'].get('layout', []))
    tables_count = len(result['result'].get('tables', []))
    formulas_count = len(result['result'].get('formulas', []))
    parsing_count = len(result['result'].get('parsing_res', []))

    print("\n" + "=" * 50)
    print("统计信息")
    print("=" * 50)
    print(f"版面元素数: {layout_count}")
    print(f"表格数: {tables_count}")
    print(f"公式数: {formulas_count}")
    print(f"解析块数: {parsing_count}")
    print(f"推理时间: {result['inference_time']:.2f}s")

    return result


def test_pdf_markdown(pdf_path: str):
    """测试PDF的Markdown格式输出"""
    print("\n" + "=" * 50)
    print("测试 PDF - Markdown 格式")
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
    result = service.predict(pdf_path, output_format="markdown")

    print("=" * 50)
    print("Markdown 结果")
    print("=" * 50)
    markdown_content = result['result']['markdown']
    print(markdown_content)

    print("\n" + "=" * 50)
    print("统计信息")
    print("=" * 50)
    print(f"Markdown长度: {len(markdown_content)} 字符")
    print(f"推理时间: {result['inference_time']:.2f}s")

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python test_structure_v3_pdf.py <PDF路径>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # 测试两种格式
    json_result = test_pdf_json(pdf_path)
    markdown_result = test_pdf_markdown(pdf_path)
