"""
IHDS Daily View Fetcher
~~~~~~~~~~~~~~~~~~~~~~~

自动抓取 IHDS Daily View 内容并生成中英文双语 Markdown 文件。

Usage:
    >>> from ihds import DailyViewFetcher
    >>> fetcher = DailyViewFetcher(api_key="your-api-key")
    >>> fetcher.run()

    >>> from ihds import LeonardoImageGenerator
    >>> generator = LeonardoImageGenerator(api_key="your-leonardo-key")
    >>> generator.generate_daily_art(content, output_dir)
"""

from .fetcher import IHDSDailyViewFetcher as DailyViewFetcher
from .image_generator import LeonardoImageGenerator

__version__ = "1.1.0"
__author__ = "IHDS Daily View Project"
__all__ = ["DailyViewFetcher", "LeonardoImageGenerator"]

