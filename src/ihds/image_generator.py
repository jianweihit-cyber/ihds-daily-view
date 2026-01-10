#!/usr/bin/env python3
"""
Leonardo.AI Image Generator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

基于 Daily View 内容生成艺术海报图片。

Usage:
    from ihds.image_generator import LeonardoImageGenerator
    
    generator = LeonardoImageGenerator(api_key="your-key")
    image_path = generator.generate_daily_art(content, output_dir)
"""

import os
import re
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional


class LeonardoImageGenerator:
    """Leonardo.AI 图片生成器"""
    
    API_BASE = "https://cloud.leonardo.ai/api/rest/v1"
    
    # 推荐的模型 ID
    MODELS = {
        "leonardo_creative": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",
        "leonardo_diffusion_xl": "1e60896f-3c26-4296-8ecc-53e2afecc132",
        "leonardo_vision_xl": "5c232a9e-9061-4777-980a-ddc8e65647c6",
        "dreamshaper_v7": "ac614f96-1082-45bf-be9d-757f2d31c174",
    }
    
    def __init__(self, api_key: str = None):
        """
        初始化 Leonardo.AI 生成器
        
        Args:
            api_key: Leonardo.AI API Key，如未提供则从环境变量 LEONARDO_API_KEY 读取
        """
        self.api_key = api_key or os.environ.get("LEONARDO_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Leonardo API Key 未设置。请通过参数传入或设置环境变量 LEONARDO_API_KEY"
            )
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def generate_prompt(self, content: Dict[str, Any]) -> str:
        """
        根据 Daily View 内容生成艺术提示词
        
        Args:
            content: Daily View 内容字典
            
        Returns:
            适合 Leonardo.AI 的英文提示词
        """
        gate_title = content.get('gate_title', 'Human Design Gate')
        gate_subtitle = content.get('gate_subtitle', '')
        lead = content.get('lead_description', '')
        line_title = content.get('line_title', '')
        exaltation = content.get('exaltation', '')
        
        # 提取 Gate 号
        gate_match = re.search(r'Gate\s+(\d+)', gate_title)
        gate_num = gate_match.group(1) if gate_match else ""
        
        prompt = f"""Mystical spiritual artwork for Human Design {gate_title}.

Theme: {gate_subtitle}
Energy essence: {lead}
Line expression: {line_title}

Art style requirements:
- Sacred geometry patterns and cosmic mandala elements
- Deep purple, golden light, celestial blue color palette
- I Ching hexagram subtle integration
- Ethereal flowing energy lines and particles
- Mystical transformation and enlightenment mood
- Professional poster composition with mystical border
- High detail, cinematic lighting, 4K quality

Additional elements: stars, nebula, sacred symbols, golden ratio spirals"""

        return prompt
    
    def generate_negative_prompt(self) -> str:
        """生成负面提示词"""
        return "text, watermark, signature, blurry, low quality, distorted, ugly, amateur, cartoon, anime"
    
    def upload_init_image(self, image_path: str) -> Optional[str]:
        """
        上传参考图片用于 Image-to-Image 生成
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            上传后的图片 ID，失败返回 None
        """
        # 获取预签名上传 URL
        extension = Path(image_path).suffix.lower().replace('.', '')
        if extension == 'jpg':
            extension = 'jpeg'
        
        init_response = requests.post(
            f"{self.API_BASE}/init-image",
            headers=self.headers,
            json={"extension": extension}
        )
        
        if init_response.status_code != 200:
            print(f"   ⚠️ 获取上传 URL 失败: {init_response.text}")
            return None
        
        init_data = init_response.json()
        upload_url = init_data['uploadInitImage']['url']
        image_id = init_data['uploadInitImage']['id']
        fields = init_data['uploadInitImage']['fields']
        
        # 上传图片
        with open(image_path, 'rb') as f:
            files = {'file': f}
            data = {k: v for k, v in fields.items()}
            upload_response = requests.post(upload_url, data=data, files=files)
        
        if upload_response.status_code not in [200, 204]:
            print(f"   ⚠️ 图片上传失败: {upload_response.status_code}")
            return None
        
        return image_id
    
    def create_generation(
        self,
        prompt: str,
        negative_prompt: str = "",
        model_id: str = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        init_image_id: str = None,
        init_strength: float = 0.3,
        guidance_scale: float = 7,
        preset_style: str = "CINEMATIC"
    ) -> Optional[str]:
        """
        创建图片生成任务
        
        Args:
            prompt: 提示词
            negative_prompt: 负面提示词
            model_id: 模型 ID
            width: 图片宽度
            height: 图片高度
            num_images: 生成数量
            init_image_id: 参考图片 ID（用于 Image-to-Image）
            init_strength: 参考图片影响强度 (0-1)
            guidance_scale: 提示词引导强度
            preset_style: 预设风格
            
        Returns:
            生成任务 ID
        """
        if model_id is None:
            model_id = self.MODELS["leonardo_vision_xl"]
        
        payload = {
            "prompt": prompt,
            "modelId": model_id,
            "width": width,
            "height": height,
            "num_images": num_images,
            "guidance_scale": guidance_scale,
            "presetStyle": preset_style,
            "public": False,
            "promptMagic": True,
        }
        
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        
        if init_image_id:
            payload["init_image_id"] = init_image_id
            payload["init_strength"] = init_strength
        
        response = requests.post(
            f"{self.API_BASE}/generations",
            headers=self.headers,
            json=payload
        )
        
        if response.status_code != 200:
            print(f"   ⚠️ 创建生成任务失败: {response.text}")
            return None
        
        data = response.json()
        generation_id = data.get('sdGenerationJob', {}).get('generationId')
        return generation_id
    
    def wait_for_generation(
        self,
        generation_id: str,
        timeout: int = 120,
        poll_interval: int = 3
    ) -> Optional[list]:
        """
        等待生成完成并返回结果
        
        Args:
            generation_id: 生成任务 ID
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）
            
        Returns:
            生成的图片信息列表
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = requests.get(
                f"{self.API_BASE}/generations/{generation_id}",
                headers=self.headers
            )
            
            if response.status_code != 200:
                time.sleep(poll_interval)
                continue
            
            data = response.json()
            generation = data.get('generations_by_pk', {})
            status = generation.get('status')
            
            if status == 'COMPLETE':
                return generation.get('generated_images', [])
            elif status == 'FAILED':
                print(f"   ⚠️ 生成失败")
                return None
            
            # 显示进度
            print(f"   ⏳ 生成中... ({int(time.time() - start_time)}s)")
            time.sleep(poll_interval)
        
        print(f"   ⚠️ 生成超时 ({timeout}s)")
        return None
    
    def download_image(self, image_url: str, output_path: str) -> bool:
        """
        下载生成的图片
        
        Args:
            image_url: 图片 URL
            output_path: 保存路径
            
        Returns:
            是否成功
        """
        try:
            response = requests.get(image_url, timeout=60)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            print(f"   ⚠️ 下载图片失败: {e}")
            return False
    
    def generate_daily_art(
        self,
        content: Dict[str, Any],
        output_dir: str,
        gate_image_path: str = None,
        date_str: str = None
    ) -> Optional[str]:
        """
        生成 Daily View 艺术海报
        
        Args:
            content: Daily View 内容字典
            output_dir: 输出目录
            gate_image_path: Gate 图片路径（可选，用于 Image-to-Image）
            date_str: 日期字符串
            
        Returns:
            生成的图片路径，失败返回 None
        """
        print("\n🎨 Leonardo.AI 图片生成")
        print("=" * 40)
        
        # 1. 生成提示词
        prompt = self.generate_prompt(content)
        negative_prompt = self.generate_negative_prompt()
        print(f"   📝 提示词已生成 ({len(prompt)} 字符)")
        
        # 2. 可选：上传参考图片
        init_image_id = None
        if gate_image_path and Path(gate_image_path).exists():
            print(f"   📤 上传参考图片: {Path(gate_image_path).name}")
            init_image_id = self.upload_init_image(gate_image_path)
            if init_image_id:
                print(f"   ✅ 图片上传成功")
        
        # 3. 创建生成任务
        print(f"   🚀 开始生成...")
        generation_id = self.create_generation(
            prompt=prompt,
            negative_prompt=negative_prompt,
            init_image_id=init_image_id,
            init_strength=0.25,  # 轻度参考，保留创意空间
            width=1024,
            height=1024,
            num_images=1
        )
        
        if not generation_id:
            return None
        
        # 4. 等待完成
        images = self.wait_for_generation(generation_id)
        if not images:
            return None
        
        # 5. 下载图片
        image_url = images[0].get('url')
        if not image_url:
            print("   ⚠️ 未获取到图片 URL")
            return None
        
        # 提取 Gate 号用于命名
        gate_match = re.search(r'Gate\s+(\d+)', content.get('gate_title', ''))
        gate_num = gate_match.group(1) if gate_match else "unknown"
        
        output_path = Path(output_dir) / f"daily_art_gate{gate_num}_{date_str or 'poster'}.png"
        
        print(f"   📥 下载图片...")
        if self.download_image(image_url, str(output_path)):
            print(f"   ✅ 海报已保存: {output_path}")
            return str(output_path)
        
        return None


def test_generator():
    """测试函数"""
    api_key = os.environ.get("LEONARDO_API_KEY")
    if not api_key:
        print("请设置环境变量 LEONARDO_API_KEY")
        return
    
    generator = LeonardoImageGenerator(api_key)
    
    # 测试内容
    test_content = {
        "gate_title": "Gate 58 - The Joyous",
        "gate_subtitle": "Gate of Vitality - The Vitality to Challenge",
        "lead_description": "Stimulation is the key to joy. The zest for life and the energy for a 'better-life'. Criticism is a natural by-product of this improvement energy.",
        "line_title": "Line 3 - Electricity",
        "exaltation": "The individual whose electric vitality creates its own stimulation and is not dependent on others."
    }
    
    print("生成的提示词:")
    print(generator.generate_prompt(test_content))


if __name__ == "__main__":
    test_generator()
