#!/usr/bin/env python3
"""
IHDS Daily View Fetcher
每天自动下载 Human Design 每日视图，并生成中英文双语 Markdown 文件
"""

import os
import re
import json
import base64
import html
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any


class IHDSDailyViewFetcher:
    """IHDS Daily View 内容抓取器"""
    
    DAILY_VIEW_URL = "https://ihdschool.com/the-daily-view"
    DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
    
    def __init__(self, deepseek_api_key: str, output_dir: str = None):
        self.api_key = deepseek_api_key
        # 默认输出到项目根目录的 output/daily_views
        if output_dir:
            self.base_output_dir = Path(output_dir)
        else:
            # 从 src/ihds/fetcher.py 向上两级到项目根目录
            project_root = Path(__file__).parent.parent.parent
            self.base_output_dir = project_root / "output" / "daily_views"
        self.base_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 日期字符串，目录会在解析内容后创建
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.output_dir = None
        self.images_dir = None
    
    def _extract_gate_line_numbers(self, content: Dict[str, Any]) -> tuple:
        """从内容中提取 Gate 号和 Line 号"""
        gate_num = ""
        line_num = ""
        
        # 从 gate_title 提取 Gate 号 (例如: "Gate 54 - The Marrying Maiden" -> "54")
        gate_title = content.get('gate_title', '')
        gate_match = re.search(r'Gate\s+(\d+)', gate_title)
        if gate_match:
            gate_num = gate_match.group(1)
        
        # 从 line_title 提取 Line 号 (例如: "Line 1 - Influence" -> "1")
        line_title = content.get('line_title', '')
        line_match = re.search(r'Line\s+(\d+)', line_title)
        if line_match:
            line_num = line_match.group(1)
        
        return gate_num, line_num
    
    def _setup_daily_directory(self, content: Dict[str, Any]):
        """根据内容创建今天的目录，格式: 2026-01-06-54.1"""
        gate_num, line_num = self._extract_gate_line_numbers(content)
        
        # 构建目录名: 日期-Gate号.Line号
        if gate_num and line_num:
            dir_name = f"{self.date_str}-{gate_num}.{line_num}"
        elif gate_num:
            dir_name = f"{self.date_str}-{gate_num}"
        else:
            dir_name = self.date_str
        
        self.output_dir = self.base_output_dir / dir_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        
        return dir_name
        
    def fetch_page(self) -> str:
        """获取网页 HTML 内容"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(self.DAILY_VIEW_URL, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    
    def download_image(self, url: str, filename: str) -> str:
        """下载图片并返回本地路径"""
        local_path = self.images_dir / filename
        
        # 如果图片已存在，直接返回
        if local_path.exists():
            return str(local_path.relative_to(self.output_dir))
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            with open(local_path, 'wb') as f:
                f.write(response.content)
            return str(local_path.relative_to(self.output_dir))
        except Exception as e:
            print(f"下载图片失败 {url}: {e}")
            return url  # 返回原始 URL
    
    def download_images(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """下载所有图片并更新内容中的路径"""
        # 下载 Gate 图片
        if content.get('gate_image_url') and content.get('gate_image_filename'):
            content['gate_image_local'] = self.download_image(
                content['gate_image_url'], 
                content['gate_image_filename']
            )
        
        # 处理 Rave Mandala base64 图片
        if content.get('rave_mandala_b64'):
            try:
                b64_data = content['rave_mandala_b64']
                
                # 解码 HTML 实体（如 &amp; → &）
                b64_data = html.unescape(b64_data)
                
                # 清理空白字符
                b64_data = b64_data.strip().replace('\n', '').replace('\r', '').replace(' ', '')
                
                # 修复可能的 padding 问题
                missing_padding = len(b64_data) % 4
                if missing_padding:
                    b64_data += '=' * (4 - missing_padding)
                
                img_data = base64.b64decode(b64_data)
                rave_mandala_path = self.images_dir / 'rave_mandala.png'
                with open(rave_mandala_path, 'wb') as f:
                    f.write(img_data)
                content['rave_mandala_local'] = str(rave_mandala_path.relative_to(self.output_dir))
                print(f"   ✅ Rave Mandala 圖片已保存 ({len(img_data)} 字節)")
            except Exception as e:
                print(f"   ⚠️ Rave Mandala 解碼失敗: {e}")
        
        return content
    
    def parse_content(self, page_html: str) -> Dict[str, Any]:
        """解析网页内容，提取每日视图信息（不下载图片）"""
        soup = BeautifulSoup(page_html, 'html.parser')
        content = {}
        
        # 提取 Gate 图片 URL（稍后下载）
        gate_img = soup.find('img', class_='gate')
        if gate_img and gate_img.get('src'):
            img_url = gate_img['src']
            img_filename = img_url.split('/')[-1]
            content['gate_image_url'] = img_url
            content['gate_image_filename'] = img_filename
        
        # 保存 base64 数据用于稍后处理
        b64_match = re.search(r'data:image/png;base64,([^"]+)', page_html)
        if b64_match:
            content['rave_mandala_b64'] = b64_match.group(1)
        
        # 提取 Gate 标题 (例如: "Gate 58 - The Joyous")
        gate_title_tag = soup.find('h2')
        if gate_title_tag:
            content['gate_title'] = gate_title_tag.get_text(strip=True)
        
        # 提取 Gate 副标题 (例如: "Gate of Vitality - The Vitality to Challenge")
        gate_subtitle_tag = soup.find('h4', string=lambda x: x and 'Gate of' in x) or soup.find('h4')
        if gate_subtitle_tag:
            em_tag = gate_subtitle_tag.find('em')
            if em_tag:
                content['gate_subtitle'] = em_tag.get_text(strip=True)
            else:
                content['gate_subtitle'] = gate_subtitle_tag.get_text(strip=True)
        
        # 提取 Lead 描述 (主要描述文字)
        lead_p = soup.find('p', class_='lead')
        if lead_p:
            content['lead_description'] = lead_p.get_text(strip=True)
        
        # 提取 Gate 范围 (例如: "Gate 10 < Gate 58 > Gate 38")
        gate_range_p = soup.find('p', class_='text-lg')
        if gate_range_p:
            content['gate_range'] = gate_range_p.get_text(strip=True)
        
        # 提取 Cross 信息 (例如: "Right Angle Cross of Service 4 | Godhead - Vishnu")
        cross_h4 = soup.find('h4', string=lambda x: x and 'Cross' in x if x else False)
        if cross_h4:
            content['cross_info'] = cross_h4.get_text(strip=True)
        
        # 提取 Quarter 和 Theme 信息
        quarter_p_list = soup.find_all('p', class_='text-lg')
        for p in quarter_p_list:
            text = p.get_text(strip=True)
            if 'Quarter' in text:
                content['quarter_theme'] = text
                break
        
        # 提取 Channel 描述 (主要内容段落)
        # 寻找包含 "This Gate is part of" 的段落
        all_paragraphs = soup.find_all('p')
        main_paragraphs = []
        found_main = False
        for p in all_paragraphs:
            text = p.get_text(strip=True)
            if text and 'This Gate is part of' in text:
                main_paragraphs.append(text)
                found_main = True
            elif found_main and len(text) > 100:
                # 检查是否是无关内容
                if any(skip in text for skip in [
                    'Daily View reflects', 'Exaltation', 'Detriment',
                    'Copyright', 'Projectors are designed', 'Unlike energy Types',
                    'young people', 'register for an IHDS'
                ]):
                    break  # 停止收集
                main_paragraphs.append(text)
        if main_paragraphs:
            content['main_description'] = '\n\n'.join(main_paragraphs)
        
        # 提取 Line 信息 (例如: "Line 3 - Electricity")
        line_h6 = soup.find('h6', string=lambda x: x and 'Line' in x if x else False)
        if line_h6:
            content['line_title'] = line_h6.get_text(strip=True)
        
        # 提取 Exaltation 和 Detriment
        col_md_6_divs = soup.find_all('div', class_='col-md-6')
        for div in col_md_6_divs:
            paragraphs = div.find_all('p')
            for p in paragraphs:
                text = p.get_text(strip=True)
                if 'Exaltation' in text:
                    # 提取 Exaltation 内容
                    content['exaltation'] = text.replace('Exaltation:', '').strip()
                elif 'Detriment' in text:
                    # 提取 Detriment 内容
                    content['detriment'] = text.replace('Detriment:', '').strip()
        
        # 提取页脚说明
        footer_text = soup.find('p', string=lambda x: x and 'The Daily View reflects' in x if x else False)
        if footer_text:
            content['footer_note'] = footer_text.get_text(strip=True)
        else:
            content['footer_note'] = (
                "The Daily View reflects the impact the Sun (70% of the neutrino influence) "
                "is having on humanity as it moves through the Gates and Lines of the Mandala. "
                "Transits are potentials that you can witness in others and the world around you, "
                "and, if correct for you, as you follow your individual Strategy and Authority, "
                "may become a part of your experience as well."
            )
        
        return content
    
    def translate_to_chinese(self, text: str) -> str:
        """使用 DeepSeek API 将文本翻译成中文"""
        if not text:
            return ""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是一位專業的 Human Design（人類圖）翻譯專家。"
                        "請將以下英文內容翻譯成流暢、準確的繁體中文。"
                        "保留專有名詞如 Gate、Channel、Center 等的英文原文，可以在括號中加中文說明。"
                        "注意保持原文的專業性和深度。必須使用繁體中文。"
                    )
                },
                {
                    "role": "user",
                    "content": f"請將以下內容翻譯成繁體中文（台灣用語）：\n\n{text}"
                }
            ],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(
                self.DEEPSEEK_API_URL,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"翻译失败: {e}")
            return f"[翻译失败] {text}"
    
    def translate_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """翻译所有内容到中文"""
        chinese_content = {}
        
        # 需要翻译的字段
        fields_to_translate = [
            'gate_title', 'gate_subtitle', 'lead_description',
            'cross_info', 'quarter_theme', 'main_description',
            'line_title', 'exaltation', 'detriment', 'footer_note'
        ]
        
        print("正在翻譯內容為繁體中文...")
        for field in fields_to_translate:
            if field in content and content[field]:
                print(f"  翻譯 {field}...")
                chinese_content[field] = self.translate_to_chinese(content[field])
        
        # 复制不需要翻译的字段
        for key in content:
            if key not in chinese_content:
                chinese_content[key] = content[key]
        
        return chinese_content
    
    def generate_markdown_en(self, content: Dict[str, Any]) -> str:
        """生成英文 Markdown 文件"""
        date_display = datetime.now().strftime("%B %d, %Y")
        
        gate_image = content.get('gate_image_local', content.get('gate_image_url', ''))
        rave_mandala = content.get('rave_mandala_local', '')
        gate_title = content.get('gate_title', '')
        gate_subtitle = content.get('gate_subtitle', '')
        lead = content.get('lead_description', '')
        cross = content.get('cross_info', '')
        quarter = content.get('quarter_theme', '')
        main_desc = content.get('main_description', '')
        line_title = content.get('line_title', '')
        exaltation = content.get('exaltation', '')
        detriment = content.get('detriment', '')
        
        md = f"""# {gate_title}

**{date_display}**

"""
        
        # Gate 图片
        if gate_image:
            md += f"""![Gate]({gate_image})

"""
        
        md += f"""## *{gate_subtitle}*

> {lead}

"""
        
        if cross:
            md += f"""### {cross}

"""
        
        if quarter:
            md += f"""*{quarter}*

"""
        
        md += """---

"""
        
        if main_desc:
            md += f"""{main_desc}

"""
        
        # Rave Mandala 大图
        if rave_mandala:
            md += f"""![Rave Mandala]({rave_mandala})

"""
        
        md += """---

"""
        
        if line_title:
            md += f"""### {line_title}

"""
        
        if exaltation:
            md += f"""**☀️ Exaltation:** {exaltation}

"""
        
        if detriment:
            md += f"""**🌑 Detriment:** {detriment}
"""
        
        return md
    
    def generate_markdown_zh(self, content: Dict[str, Any]) -> str:
        """生成繁體中文 Markdown 文件"""
        date_display = datetime.now().strftime("%Y年%m月%d日")
        
        gate_image = content.get('gate_image_local', content.get('gate_image_url', ''))
        rave_mandala = content.get('rave_mandala_local', '')
        gate_title = content.get('gate_title', '')
        gate_subtitle = content.get('gate_subtitle', '')
        lead = content.get('lead_description', '')
        cross = content.get('cross_info', '')
        quarter = content.get('quarter_theme', '')
        main_desc = content.get('main_description', '')
        line_title = content.get('line_title', '')
        exaltation = content.get('exaltation', '')
        detriment = content.get('detriment', '')
        
        md = f"""# {gate_title}

**{date_display}**

"""
        
        # Gate 图片
        if gate_image:
            md += f"""![閘門]({gate_image})

"""
        
        md += f"""## *{gate_subtitle}*

> {lead}

"""
        
        if cross:
            md += f"""### {cross}

"""
        
        if quarter:
            md += f"""*{quarter}*

"""
        
        md += """---

"""
        
        if main_desc:
            md += f"""{main_desc}

"""
        
        # Rave Mandala 大图
        if rave_mandala:
            md += f"""![人類圖曼陀羅]({rave_mandala})

"""
        
        md += """---

"""
        
        if line_title:
            md += f"""### {line_title}

"""
        
        if exaltation:
            md += f"""**☀️ 高階表達:** {exaltation}

"""
        
        if detriment:
            md += f"""**🌑 低階表達:** {detriment}
"""
        
        return md
    
    def run(self) -> str:
        """执行完整的抓取、翻译和生成流程"""
        print("=" * 60)
        print("IHDS Daily View Fetcher")
        print("=" * 60)
        
        # 1. 获取网页内容
        print("\n📥 正在獲取網頁內容...")
        html = self.fetch_page()
        print("   ✅ 網頁獲取成功")
        
        # 2. 解析内容（不下载图片）
        print("\n🔍 正在解析內容...")
        en_content = self.parse_content(html)
        print(f"   ✅ 解析成功，Gate: {en_content.get('gate_title', 'Unknown')}")
        
        # 3. 根据内容创建目录（格式: 2026-01-06-54.1）
        dir_name = self._setup_daily_directory(en_content)
        print(f"   📁 目錄: {dir_name}")
        
        # 4. 下载图片
        print("\n📷 正在下載圖片...")
        en_content = self.download_images(en_content)
        
        # 5. 翻译内容
        print("\n🌐 正在翻譯為繁體中文...")
        zh_content = self.translate_content(en_content)
        print("   ✅ 翻譯完成")
        
        # 6. 生成 Markdown 文件
        print("\n📝 正在生成 Markdown 文件...")
        print(f"   📁 保存目錄: {self.output_dir}")
        
        # 生成英文版 (保存到日期目录，文件名包含日期)
        markdown_en = self.generate_markdown_en(en_content)
        filename_en = f"daily_view_{self.date_str}_en.md"
        filepath_en = self.output_dir / filename_en
        with open(filepath_en, 'w', encoding='utf-8') as f:
            f.write(markdown_en)
        print(f"   ✅ 英文版: {filepath_en}")
        
        # 生成繁體中文版
        markdown_zh = self.generate_markdown_zh(zh_content)
        filename_zh = f"daily_view_{self.date_str}_zh.md"
        filepath_zh = self.output_dir / filename_zh
        with open(filepath_zh, 'w', encoding='utf-8') as f:
            f.write(markdown_zh)
        print(f"   ✅ 繁體中文版: {filepath_zh}")
        
        # 同时保存 latest 版本到根目录（图片路径指向当前日期目录）
        dir_name = self.output_dir.name  # 例如: 2026-01-06-54.1
        latest_markdown_en = markdown_en.replace('images/', f'{dir_name}/images/')
        latest_markdown_zh = markdown_zh.replace('images/', f'{dir_name}/images/')
        
        latest_en_path = self.base_output_dir / "latest_en.md"
        with open(latest_en_path, 'w', encoding='utf-8') as f:
            f.write(latest_markdown_en)
        
        latest_zh_path = self.base_output_dir / "latest_zh.md"
        with open(latest_zh_path, 'w', encoding='utf-8') as f:
            f.write(latest_markdown_zh)
        print(f"   ✅ 最新英文版: {latest_en_path}")
        print(f"   ✅ 最新中文版: {latest_zh_path}")
        
        print("\n" + "=" * 60)
        print("✨ 完成!")
        print("=" * 60)
        
        return str(filepath_en)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='IHDS Daily View Fetcher')
    parser.add_argument(
        '--api-key',
        type=str,
        default=os.environ.get('DEEPSEEK_API_KEY', 'sk-b006820f1cfd4c54ae530ccc0ed6dd5a'),
        help='DeepSeek API Key'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for generated files'
    )
    
    args = parser.parse_args()
    
    fetcher = IHDSDailyViewFetcher(
        deepseek_api_key=args.api_key,
        output_dir=args.output_dir
    )
    
    fetcher.run()


if __name__ == "__main__":
    main()

