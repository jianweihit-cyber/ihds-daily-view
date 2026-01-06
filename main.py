#!/usr/bin/env python3
"""
IHDS Daily View Fetcher - 入口脚本
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

每天自动抓取 IHDS Daily View 内容并生成中英文双语 Markdown 文件。

Usage:
    python main.py
    python main.py --api-key YOUR_API_KEY
    python main.py --output-dir /path/to/output
"""

import os
import sys
import argparse

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
    python main.py
    python main.py --api-key sk-xxxxx
    python main.py --output-dir ./my_output
        """
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        default=os.environ.get('DEEPSEEK_API_KEY', 'sk-b006820f1cfd4c54ae530ccc0ed6dd5a'),
        help='DeepSeek API Key (默认使用环境变量 DEEPSEEK_API_KEY)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='输出目录 (默认: output/daily_views/)'
    )
    
    args = parser.parse_args()
    
    fetcher = DailyViewFetcher(
        deepseek_api_key=args.api_key,
        output_dir=args.output_dir
    )
    
    fetcher.run()


if __name__ == "__main__":
    main()

