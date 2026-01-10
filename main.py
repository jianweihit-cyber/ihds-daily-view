#!/usr/bin/env python3
"""
IHDS Daily View Fetcher - 入口脚本
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

每天自动抓取 IHDS Daily View 内容并生成中英文双语 Markdown 文件。
可选：使用 Leonardo.AI 生成艺术海报。

Usage:
    python main.py
    python main.py --api-key YOUR_API_KEY
    python main.py --output-dir /path/to/output
    python main.py --generate-image --leonardo-key YOUR_LEONARDO_KEY
"""

import os
import sys
import argparse
from pathlib import Path

# 将 src 目录添加到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ihds import DailyViewFetcher


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='IHDS Daily View Fetcher - 每日人类图视图抓取器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # 基础使用
    python main.py
    python main.py --api-key sk-xxxxx
    python main.py --output-dir ./my_output
    
    # 生成 AI 艺术海报
    python main.py --generate-image
    python main.py --generate-image --leonardo-key YOUR_KEY
        """
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='DeepSeek API Key (默认使用环境变量 DEEPSEEK_API_KEY)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='输出目录 (默认: output/daily_views/)'
    )
    
    # Leonardo.AI 图片生成参数
    parser.add_argument(
        '--generate-image',
        action='store_true',
        help='使用 Leonardo.AI 生成艺术海报'
    )
    
    parser.add_argument(
        '--leonardo-key',
        type=str,
        default=os.environ.get('LEONARDO_API_KEY'),
        help='Leonardo.AI API Key (默认使用环境变量 LEONARDO_API_KEY)'
    )
    
    parser.add_argument(
        '--use-gate-ref',
        action='store_true',
        default=True,
        help='使用 Gate 图片作为参考进行 Image-to-Image 生成 (默认: True)'
    )
    
    args = parser.parse_args()
    
    # 确定 API Key（优先级：命令行参数 > 环境变量 > 默认值）
    api_key = args.api_key
    if not api_key:
        api_key = os.environ.get('DEEPSEEK_API_KEY', '').strip()
    if not api_key:
        # 使用默认 key（仅用于测试）
        api_key = 'sk-b006820f1cfd4c54ae530ccc0ed6dd5a'
        print("⚠️  未设置 DEEPSEEK_API_KEY，使用默认密钥")
    
    # 运行 Daily View 抓取
    fetcher = DailyViewFetcher(
        deepseek_api_key=api_key,
        output_dir=args.output_dir
    )
    
    result = fetcher.run()
    
    # 可选：生成 AI 艺术海报
    if args.generate_image:
        generate_art_poster(fetcher, args)


def generate_art_poster(fetcher, args):
    """生成 AI 艺术海报"""
    from ihds import LeonardoImageGenerator
    
    if not args.leonardo_key:
        print("\n⚠️  未设置 Leonardo.AI API Key")
        print("   请通过 --leonardo-key 参数或环境变量 LEONARDO_API_KEY 设置")
        return
    
    try:
        generator = LeonardoImageGenerator(api_key=args.leonardo_key)
        
        # 获取当前内容（需要从 fetcher 获取）
        # 这里我们需要读取最新生成的英文 Markdown 并解析
        latest_en_path = fetcher.base_output_dir / "latest_en.md"
        
        if not latest_en_path.exists():
            print("\n⚠️  未找到最新的 Daily View 内容")
            return
        
        # 简单解析内容
        content = parse_markdown_content(latest_en_path)
        
        # 获取 Gate 图片路径（如果使用参考图）
        gate_image_path = None
        if args.use_gate_ref and fetcher.gate_num:
            gate_image_path = fetcher.images_collection_dir / f"Gate-{fetcher.gate_num}.jpg"
            if not gate_image_path.exists():
                gate_image_path = None
        
        # 生成海报
        output_path = generator.generate_daily_art(
            content=content,
            output_dir=str(fetcher.output_dir) if fetcher.output_dir else str(fetcher.base_output_dir),
            gate_image_path=str(gate_image_path) if gate_image_path else None,
            date_str=fetcher.date_str
        )
        
        if output_path:
            print(f"\n🎨 艺术海报生成完成!")
        
    except Exception as e:
        print(f"\n⚠️  图片生成失败: {e}")


def parse_markdown_content(md_path: Path) -> dict:
    """从 Markdown 文件解析内容"""
    content = {}
    
    with open(md_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # 解析标题
    title_match = text.split('\n')[0]
    if title_match.startswith('# '):
        content['gate_title'] = title_match[2:].strip()
    
    # 解析副标题
    import re
    subtitle_match = re.search(r'## \*(.+?)\*', text)
    if subtitle_match:
        content['gate_subtitle'] = subtitle_match.group(1)
    
    # 解析引用描述
    lead_match = re.search(r'> (.+?)(?=\n\n|\n###)', text, re.DOTALL)
    if lead_match:
        content['lead_description'] = lead_match.group(1).strip()
    
    # 解析 Line 标题
    line_match = re.search(r'### (Line \d+ - .+?)(?=\n)', text)
    if line_match:
        content['line_title'] = line_match.group(1)
    
    # 解析高阶表达
    exalt_match = re.search(r'Exaltation:\*\* (.+?)(?=\n\n|\n\*\*)', text, re.DOTALL)
    if exalt_match:
        content['exaltation'] = exalt_match.group(1).strip()
    
    return content


def generate_test_poster():
    """
    测试函数：使用 Gate 58 内容生成海报
    
    Usage:
        python main.py --test-poster
    """
    from ihds import LeonardoImageGenerator
    
    api_key = os.environ.get('LEONARDO_API_KEY')
    if not api_key:
        print("请设置环境变量 LEONARDO_API_KEY")
        print("export LEONARDO_API_KEY=your-api-key")
        return
    
    # Gate 58 测试内容
    test_content = {
        "gate_title": "Gate 58 - The Joyous",
        "gate_subtitle": "Gate of Vitality - The Vitality to Challenge",
        "lead_description": "Stimulation is the key to joy. The zest for life and the energy for a 'better-life'. Criticism is a natural by-product of this improvement energy.",
        "line_title": "Line 3 - Electricity",
        "exaltation": "The individual whose electric vitality creates its own stimulation and is not dependent on others. The energy to fuel independent stimulation."
    }
    
    generator = LeonardoImageGenerator(api_key=api_key)
    
    # 使用 Gate 58 图片作为参考
    project_root = Path(__file__).parent
    gate_image = project_root / "output" / "Gate_Rave_Mandala_Collection" / "Gate-58.jpg"
    output_dir = project_root / "output" / "test_posters"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("🧪 Gate 58 海报生成测试")
    print("=" * 60)
    
    result = generator.generate_daily_art(
        content=test_content,
        output_dir=str(output_dir),
        gate_image_path=str(gate_image) if gate_image.exists() else None,
        date_str="test"
    )
    
    if result:
        print(f"\n✨ 测试海报已保存: {result}")
    else:
        print("\n❌ 海报生成失败")


if __name__ == "__main__":
    # 检查是否是测试模式
    if len(sys.argv) > 1 and sys.argv[1] == '--test-poster':
        generate_test_poster()
    else:
        main()
