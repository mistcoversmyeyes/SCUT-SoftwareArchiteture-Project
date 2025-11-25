"""
测试 PaddleOCR-VL 模型的图片和PDF识别能力
"""
import sys
import json
sys.path.insert(0, '/home/yuming/SCUT/SCUT_25_Fall/SCUT-SoftwareArchiteture-Project/python-infer/app')

from services.vl_service import VLService


def test_image_json(image_path: str):
    """测试图片的JSON格式输出"""
    print("=" * 50)
    print("测试 图片 - JSON 格式")
    print("=" * 50)

    print("=" * 50)
    print("初始化VL模型")
    print("=" * 50)
    service = VLService()

    print("=" * 50)
    print("执行推理 (format='json')")
    print("=" * 50)
    result = service.predict(image_path, format="json")

    print("=" * 50)
    print("JSON 结果")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 统计信息
    result_data = result['result']
    layout_count = len(result_data.get('layout', []))
    elements_count = result_data.get('elements_count', {})
    pages = result_data.get('pages', 1)
    text_length = len(result_data.get('text', ''))

    print("\n" + "=" * 50)
    print("统计信息")
    print("=" * 50)
    print(f"页数: {pages}")
    print(f"版面元素数: {layout_count}")
    print(f"元素类型统计: {json.dumps(elements_count, ensure_ascii=False)}")
    print(f"提取文本长度: {text_length} 字符")
    print(f"推理时间: {result['inference_time']:.2f}s")

    return result


def test_image_markdown(image_path: str):
    """测试图片的Markdown格式输出"""
    print("\n" + "=" * 50)
    print("测试 图片 - Markdown 格式")
    print("=" * 50)

    print("=" * 50)
    print("初始化VL模型")
    print("=" * 50)
    service = VLService()

    print("=" * 50)
    print("执行推理 (format='markdown')")
    print("=" * 50)
    result = service.predict(image_path, format="markdown")

    print("=" * 50)
    print("Markdown 结果")
    print("=" * 50)
    result_data = result['result']
    markdown_content = result_data.get('markdown', '')
    print(markdown_content)

    print("\n" + "=" * 50)
    print("统计信息")
    print("=" * 50)
    elements_count = result_data.get('elements_count', {})
    pages = result_data.get('pages', 1)
    print(f"页数: {pages}")
    print(f"元素类型统计: {json.dumps(elements_count, ensure_ascii=False)}")
    print(f"Markdown长度: {len(markdown_content)} 字符")
    print(f"推理时间: {result['inference_time']:.2f}s")

    return result


def test_pdf_json(pdf_path: str):
    """测试PDF的JSON格式输出"""
    print("\n" + "=" * 50)
    print("测试 PDF - JSON 格式")
    print("=" * 50)

    print("=" * 50)
    print("初始化VL模型")
    print("=" * 50)
    service = VLService()

    print("=" * 50)
    print("执行推理 (format='json')")
    print("=" * 50)
    result = service.predict(pdf_path, format="json")

    print("=" * 50)
    print("JSON 结果")
    print("=" * 50)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 统计信息
    result_data = result['result']
    layout_count = len(result_data.get('layout', []))
    elements_count = result_data.get('elements_count', {})
    pages = result_data.get('pages', 1)
    text_length = len(result_data.get('text', ''))

    print("\n" + "=" * 50)
    print("统计信息")
    print("=" * 50)
    print(f"页数: {pages}")
    print(f"版面元素数: {layout_count}")
    print(f"元素类型统计: {json.dumps(elements_count, ensure_ascii=False)}")
    print(f"提取文本长度: {text_length} 字符")
    print(f"推理时间: {result['inference_time']:.2f}s")

    return result


def test_pdf_markdown(pdf_path: str):
    """测试PDF的Markdown格式输出"""
    print("\n" + "=" * 50)
    print("测试 PDF - Markdown 格式")
    print("=" * 50)

    print("=" * 50)
    print("初始化VL模型")
    print("=" * 50)
    service = VLService()

    print("=" * 50)
    print("执行推理 (format='markdown')")
    print("=" * 50)
    result = service.predict(pdf_path, format="markdown")

    print("=" * 50)
    print("Markdown 结果")
    print("=" * 50)
    result_data = result['result']
    markdown_content = result_data.get('markdown', '')
    print(markdown_content)

    print("\n" + "=" * 50)
    print("统计信息")
    print("=" * 50)
    elements_count = result_data.get('elements_count', {})
    pages = result_data.get('pages', 1)
    print(f"页数: {pages}")
    print(f"元素类型统计: {json.dumps(elements_count, ensure_ascii=False)}")
    print(f"Markdown长度: {len(markdown_content)} 字符")
    print(f"推理时间: {result['inference_time']:.2f}s")

    return result


def test_health_check():
    """测试健康检查"""
    print("\n" + "=" * 50)
    print("测试 健康检查")
    print("=" * 50)

    service = VLService()
    health = service.health_check()

    print(json.dumps(health, ensure_ascii=False, indent=2))

    return health


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="测试PaddleOCR-VL模型")
    parser.add_argument('file_path', nargs='?', help='图片或PDF文件路径')
    parser.add_argument('--type', choices=['image', 'pdf'], default='image', help='文件类型 (默认: image)')
    parser.add_argument('--format', choices=['json', 'markdown', 'both'], default='both', help='输出格式 (默认: both)')
    parser.add_argument('--health', action='store_true', help='只执行健康检查')

    args = parser.parse_args()

    # 健康检查
    if args.health:
        test_health_check()
        sys.exit(0)

    # 需要提供文件路径
    if not args.file_path:
        parser.print_help()
        print("\n错误: 请提供文件路径或使用 --health 进行健康检查")
        sys.exit(1)

    file_path = args.file_path

    # 根据文件类型和格式选择测试
    if args.type == 'image':
        if args.format in ['json', 'both']:
            test_image_json(file_path)
        if args.format in ['markdown', 'both']:
            test_image_markdown(file_path)
    elif args.type == 'pdf':
        if args.format in ['json', 'both']:
            test_pdf_json(file_path)
        if args.format in ['markdown', 'both']:
            test_pdf_markdown(file_path)
