"""
IHDS Daily View Fetcher
~~~~~~~~~~~~~~~~~~~~~~~

自动抓取 IHDS Daily View 内容并生成中英文双语 Markdown 文件。

Usage:
    >>> from ihds import DailyViewFetcher
    >>> fetcher = DailyViewFetcher(api_key="your-api-key")
    >>> fetcher.run()
"""

from .fetcher import IHDSDailyViewFetcher as DailyViewFetcher

__version__ = "1.0.0"
__author__ = "IHDS Daily View Project"
__all__ = ["DailyViewFetcher"]

