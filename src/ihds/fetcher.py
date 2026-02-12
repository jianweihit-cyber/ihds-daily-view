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
        
        # 统一的图片收藏目录
        self.images_collection_dir = self.base_output_dir.parent / "Gate_Rave_Mandala_Collection"
        self.images_collection_dir.mkdir(parents=True, exist_ok=True)
        
        # 日期字符串，目录会在解析内容后创建
        self.date_str = datetime.now().strftime("%Y-%m-%d")
        self.output_dir = None
        self.gate_num = None  # 当前 Gate 号
    
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
        self.gate_num = gate_num  # 保存 Gate 号供图片命名使用
        
        # 构建目录名: 日期-Gate号.Line号
        if gate_num and line_num:
            dir_name = f"{self.date_str}-{gate_num}.{line_num}"
        elif gate_num:
            dir_name = f"{self.date_str}-{gate_num}"
        else:
            dir_name = self.date_str
        
        self.output_dir = self.base_output_dir / dir_name
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 不再创建 images 子目录，图片统一存放在 Gate_Rave_Mandala_Collection
        
        return dir_name
        
    def fetch_page(self) -> str:
        """获取网页 HTML 内容"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(self.DAILY_VIEW_URL, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    
    def download_images(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """下载图片到统一目录 Gate_Rave_Mandala_Collection"""
        gate_num = self.gate_num or ""
        
        # Gate 图片：检查是否已存在，不存在则下载
        if content.get('gate_image_url') and gate_num:
            gate_image_path = self.images_collection_dir / f"Gate-{gate_num}.jpg"
            
            if not gate_image_path.exists():
                try:
                    response = requests.get(content['gate_image_url'], timeout=30)
                    response.raise_for_status()
                    with open(gate_image_path, 'wb') as f:
                        f.write(response.content)
                    print(f"   ✅ Gate-{gate_num}.jpg 已下載")
                except Exception as e:
                    print(f"   ⚠️ Gate 圖片下載失敗: {e}")
            else:
                print(f"   ⏭️  Gate-{gate_num}.jpg 已存在")
            
            content['gate_image_local'] = f"Gate-{gate_num}.jpg"
        
        # Rave Mandala：每天動態生成，保存為 Gate-{num}-Rave-Mandala.png
        if content.get('rave_mandala_b64') and gate_num:
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
                rave_mandala_path = self.images_collection_dir / f"Gate-{gate_num}-Rave-Mandala.png"
                
                # Rave Mandala 每天都更新（因为行星位置每天变化）
                with open(rave_mandala_path, 'wb') as f:
                    f.write(img_data)
                content['rave_mandala_local'] = f"Gate-{gate_num}-Rave-Mandala.png"
                print(f"   ✅ Gate-{gate_num}-Rave-Mandala.png 已保存 ({len(img_data)} 字節)")
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
        
        # 图片路径：相对于日期目录，指向 Gate_Rave_Mandala_Collection
        gate_image_file = content.get('gate_image_local', '')
        rave_mandala_file = content.get('rave_mandala_local', '')
        gate_image = f"../../Gate_Rave_Mandala_Collection/{gate_image_file}" if gate_image_file else ''
        rave_mandala = f"../../Gate_Rave_Mandala_Collection/{rave_mandala_file}" if rave_mandala_file else ''
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
        
        # 图片路径：相对于日期目录，指向 Gate_Rave_Mandala_Collection
        gate_image_file = content.get('gate_image_local', '')
        rave_mandala_file = content.get('rave_mandala_local', '')
        gate_image = f"../../Gate_Rave_Mandala_Collection/{gate_image_file}" if gate_image_file else ''
        rave_mandala = f"../../Gate_Rave_Mandala_Collection/{rave_mandala_file}" if rave_mandala_file else ''
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
    
    def _check_duplicate(self) -> bool:
        """
        检查当前内容是否已存在（防止重复抓取）
        
        Returns:
            True 表示内容已存在，应跳过；False 表示是新内容
        """
        if self.output_dir is None:
            return False
        
        en_file = self.output_dir / f"daily_view_{self.date_str}_en.md"
        zh_file = self.output_dir / f"daily_view_{self.date_str}_zh.md"
        
        if en_file.exists() and zh_file.exists():
            return True
        
        return False
    
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
        
        # 3.5 重复检测：如果同一个 Gate.Line 的内容已存在，跳过
        if self._check_duplicate():
            print(f"\n   ⏭️  {dir_name} 已存在完整內容，跳過本次抓取")
            print("\n" + "=" * 60)
            print("✨ 內容已是最新，無需重複抓取!")
            print("=" * 60)
            # 返回已有文件的路径
            return str(self.output_dir / f"daily_view_{self.date_str}_en.md")
        
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
        
        # 同时保存 latest 版本到根目录（调整图片路径：从 ../../ 改为 ../）
        latest_markdown_en = markdown_en.replace('../../Gate_Rave_Mandala_Collection/', '../Gate_Rave_Mandala_Collection/')
        latest_markdown_zh = markdown_zh.replace('../../Gate_Rave_Mandala_Collection/', '../Gate_Rave_Mandala_Collection/')
        
        latest_en_path = self.base_output_dir / "latest_en.md"
        with open(latest_en_path, 'w', encoding='utf-8') as f:
            f.write(latest_markdown_en)
        
        latest_zh_path = self.base_output_dir / "latest_zh.md"
        with open(latest_zh_path, 'w', encoding='utf-8') as f:
            f.write(latest_markdown_zh)
        print(f"   ✅ 最新英文版: {latest_en_path}")
        print(f"   ✅ 最新中文版: {latest_zh_path}")
        
        # 7. 生成 AI 绘图提示词文件
        print("\n🎨 正在生成 AI 繪圖提示詞...")
        prompt_path = self.generate_ai_prompt(en_content)
        print(f"   ✅ 提示詞文件: {prompt_path}")
        
        print("\n" + "=" * 60)
        print("✨ 完成!")
        print("=" * 60)
        
        return str(filepath_en)
    
    def generate_ai_prompt(self, content: Dict[str, Any]) -> str:
        """
        生成适用于 Leonardo.AI / Midjourney 等 AI 绘图工具的提示词文件
        
        Args:
            content: Daily View 英文内容字典
            
        Returns:
            提示词文件路径
        """
        gate_num = self.gate_num or "unknown"
        gate_title = content.get('gate_title', '')
        gate_subtitle = content.get('gate_subtitle', '')
        lead = content.get('lead_description', '')
        line_title = content.get('line_title', '')
        exaltation = content.get('exaltation', '')
        
        # 英文提示词（用于 AI 生图）
        en_prompt = f"""Mystical spiritual artwork for Human Design {gate_title}.

Theme: {gate_subtitle}
Energy essence: {lead}
Line expression: {line_title}

Art style requirements:
- Sacred geometry patterns and cosmic mandala elements
- Deep purple, golden light, celestial blue color palette
- I Ching hexagram subtle integration
- Ethereal flowing energy lines and luminous particles
- Mystical transformation and enlightenment mood
- Professional poster composition with elegant mystical border
- High detail, cinematic lighting, 4K ultra quality

Additional elements: starfield background, nebula wisps, sacred symbols, golden ratio spirals, soft glowing aura"""

        # 负面提示词
        negative_prompt = "text, watermark, signature, words, letters, blurry, low quality, distorted, ugly, amateur, cartoon, anime, childish, oversaturated"
        
        # 完整的提示词文件内容
        prompt_content = f"""# AI 绘图提示词 - {gate_title}
# 日期: {self.date_str}
# Gate: {gate_num} | Line: {line_title}

================================================================================
🎨 LEONARDO.AI / MIDJOURNEY 提示词
================================================================================

【英文提示词 - 直接复制使用】

{en_prompt}

--------------------------------------------------------------------------------

【负面提示词 Negative Prompt】

{negative_prompt}

================================================================================
📷 参考图片（可选上传）
================================================================================

请从以下路径上传参考图片以获得更好的效果：

1. Gate 图片（I Ching 卦象图）:
   📁 output/Gate_Rave_Mandala_Collection/Gate-{gate_num}.jpg

2. Rave Mandala（人类图曼陀罗）:
   📁 output/Gate_Rave_Mandala_Collection/Gate-{gate_num}-Rave-Mandala.png

================================================================================
⚙️ 推荐设置 (Leonardo.AI)
================================================================================

- Model: Leonardo Vision XL 或 Leonardo Creative
- 图片尺寸: 1024 x 1024 (1:1 正方形)
- Guidance Scale: 7-9
- 如使用参考图片:
  - Init Strength: 0.2-0.3 (保留创意空间)
  - 勾选 "Use as reference" 而非 "Image to Image"

================================================================================
📋 使用步骤
================================================================================

1. 打开 Leonardo.AI (https://leonardo.ai/)
2. 点击 "AI Image Generation"
3. 复制上方【英文提示词】粘贴到 Prompt 框
4. 复制【负面提示词】粘贴到 Negative Prompt 框
5. (可选) 点击 "Image Input" 上传参考图片
6. 选择模型和尺寸
7. 点击 "Generate" 生成
8. 下载喜欢的图片

================================================================================
"""
        
        # 保存到日期目录
        prompt_filename = f"ai_prompt_{self.date_str}.txt"
        prompt_path = self.output_dir / prompt_filename
        
        with open(prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        
        # 同时保存一份到 base_output_dir 作为 latest
        latest_prompt_path = self.base_output_dir / "latest_ai_prompt.txt"
        with open(latest_prompt_path, 'w', encoding='utf-8') as f:
            f.write(prompt_content)
        
        return str(prompt_path)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='IHDS Daily View Fetcher')
    # 确定 API Key
    env_key = os.environ.get('DEEPSEEK_API_KEY', '').strip()
    default_key = env_key if env_key else 'sk-b006820f1cfd4c54ae530ccc0ed6dd5a'
    
    parser.add_argument(
        '--api-key',
        type=str,
        default=default_key,
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

