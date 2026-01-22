import os
import datetime
import json
import random
import time
import requests
import urllib.parse
from io import BytesIO

# 图像处理库
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# OpenAI 客户端
from openai import OpenAI

# ================= 配置区域 (修改了这里) =================
# 逻辑：优先尝试从系统环境变量获取，如果获取不到（比如在本地直接运行），就使用后面的默认字符串
API_KEY = os.getenv("OPENAI_API_KEY", "sk-Fl2MU75boehSkbb671F707D93cF64513A17c09987eB9EcE9")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://free.v36.cm/v1/")

TEXT_MODEL_NAME = "gpt-4o-mini"

# 输出配置
OUTPUT_DIR = "content/posts"
LOCAL_FONT_PATH = "font.ttf"  # ⚠️ 必须提交到 GitHub 仓库根目录
# =======================================================

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

class FreeAIImageGenerator:
    """
    使用 Pollinations 免费绘图接口，带重试和防空图机制
    """
    def __init__(self):
        self.width = 1200
        self.height = 630

        if os.path.exists(LOCAL_FONT_PATH):
            self.font_path = LOCAL_FONT_PATH
        else:
            self.font_path = None
            # 在 GitHub Actions 日志中打印警告
            print("⚠️ [Warning] font.ttf not found! Chinese text will be squares.")

    def _get_font(self, size):
        if not self.font_path: return ImageFont.load_default()
        try:
            return ImageFont.truetype(self.font_path, size)
        except:
            return ImageFont.load_default()

    def _wrap_text(self, text, font, max_width):
        lines = []
        if not text: return []
        for paragraph in text.split('\n'):
            chars = list(paragraph)
            current_line = []
            for char in chars:
                current_line.append(char)
                if font.getbbox("".join(current_line))[2] > max_width:
                    current_line.pop()
                    lines.append("".join(current_line))
                    current_line = [char]
            if current_line: lines.append("".join(current_line))
        return lines

    def _download_free_ai_image(self, prompt, retries=3):
        print(f"🎨 Calling AI Image Gen: {prompt[:30]}...")
        enhanced_prompt = f"{prompt}, highly detailed, 8k resolution, cinematic lighting, photorealistic, no text"
        safe_prompt = urllib.parse.quote(enhanced_prompt)
        seed = random.randint(0, 9999999)
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width={self.width}&height={self.height}&seed={seed}&model=flux&nologo=true"

        for attempt in range(retries):
            try:
                res = requests.get(url, timeout=60)
                if res.status_code == 200:
                    if 'image' not in res.headers.get('content-type', ''):
                        continue
                    img = Image.open(BytesIO(res.content))
                    if img.getbbox() is None: continue
                    return img.convert('RGB')
            except Exception as e:
                print(f"⚠️ Retry {attempt+1}/{retries} error: {e}")
                time.sleep(2)

        print("❌ All retries failed. Using fallback gradient.")
        return self._create_gradient_fallback()

    def _create_gradient_fallback(self):
        base = Image.new('RGB', (self.width, self.height), "#ffffff")
        draw = ImageDraw.Draw(base)
        c1 = (random.randint(0, 50), random.randint(0, 50), random.randint(50, 150))
        c2 = (random.randint(50, 150), random.randint(0, 50), random.randint(50, 100))
        for y in range(self.height):
            r = int(c1[0] + (c2[0] - c1[0]) * y / self.height)
            g = int(c1[1] + (c2[1] - c1[1]) * y / self.height)
            b = int(c1[2] + (c2[2] - c1[2]) * y / self.height)
            draw.line((0, y, self.width, y), fill=(r,g,b))
        return base

    def generate_cover(self, title, save_path):
        bg_img = self._download_free_ai_image(f"Epic conceptual art representing {title}, futuristic, majestic")
        overlay = Image.new('RGBA', bg_img.size, (0, 0, 0, 90))
        bg_img = Image.alpha_composite(bg_img.convert('RGBA'), overlay).convert('RGB')

        draw = ImageDraw.Draw(bg_img)
        font = self._get_font(64)
        lines = self._wrap_text(title, font, self.width - 120)[:3]

        total_h = len(lines) * 85
        start_y = (self.height - total_h) // 2

        for i, line in enumerate(lines):
            bbox = font.getbbox(line)
            x = (self.width - bbox[2]) // 2
            y = start_y + i * 85
            draw.text((x+2, y+2), line, font=font, fill="black")
            draw.text((x, y), line, font=font, fill="white")

        bg_img.save(save_path, quality=90)

    def generate_content_image(self, prompt, save_path):
        img = self._download_free_ai_image(prompt)
        img.save(save_path, quality=90)

def get_todays_hot_topics():
    """让AI决定今日话题"""
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"🤖 Brainstorming topics for {today_str}...")

    prompt = f"""
    Today is {today_str}. Please act as a professional Tech & News editor.
    Generate a JSON list of 3 distinct blog post titles.
    Rules:
    1. Include 1 Tech/AI topic, 1 Global News/Economy topic, 1 Lifestyle/Society topic.
    2. Titles should be engaging and deep.
    3. Return ONLY a JSON list of strings. Example: ["Title 1", "Title 2", "Title 3"]
    """

    try:
        res = client.chat.completions.create(
            model=TEXT_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        content = res.choices[0].message.content.strip()
        if content.startswith("```json"): content = content[7:-3]
        elif content.startswith("```"): content = content[3:-3]

        topics = json.loads(content)
        print(f"✅ Generated Topics: {topics}")
        return topics
    except Exception as e:
        print(f"❌ Topic generation failed: {e}. Using defaults.")
        return [
            f"Artificial Intelligence Trends in {today_str}",
            "Global Economic Shifts Analysis",
            "Modern Remote Work Culture"
        ]

def generate_text_content(topic):
    print(f"\n🧠 Writing content for: {topic}...")
    prompt = f"""
    Write a deep blog post about "{topic}".
    Output strict JSON format with keys:
    - summary (string)
    - content (markdown string, detailed, >1200 words)
    - categories (list of strings, e.g. ["Tech", "AI"])
    - tags (list of strings)
    - image_prompts (list of 3 strings, visually descriptive in English)
    """
    try:
        res = client.chat.completions.create(
            model=TEXT_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}]
        )
        content = res.choices[0].message.content.strip()
        if content.startswith("```json"): content = content[7:-3]
        elif content.startswith("```"): content = content[3:-3]
        return json.loads(content)
    except Exception as e:
        print(f"❌ Content generation error: {e}")
        return None

def main(topic):
    clean_title = "".join([c for c in topic if c.isalnum()]).strip()
    folder = f"{clean_title}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    path = os.path.join(OUTPUT_DIR, folder)
    os.makedirs(path, exist_ok=True)

    data = generate_text_content(topic)
    if not data: return

    img_gen = FreeAIImageGenerator()
    print("🎨 Generating Cover...")
    img_gen.generate_cover(topic, os.path.join(path, "cover.jpg"))

    img_map = []
    for i, prompt in enumerate(data.get('image_prompts', [])):
        fname = f"img_{i}.jpg"
        print(f"📊 Generating Figure {i+1}...")
        img_gen.generate_content_image(prompt, os.path.join(path, fname))
        img_map.append((prompt, fname))

    content = data['content']
    paragraphs = content.split('\n\n')
    new_parts = []
    img_idx = 0

    for i, p in enumerate(paragraphs):
        new_parts.append(p)
        if i == 0: new_parts.append("\n<!--more-->\n")
        if i > 1 and i % 3 == 0 and img_idx < len(img_map):
            desc, fname = img_map[img_idx]
            new_parts.append(f"\n\n![AI Image]({fname})\n*Figure: {desc}*\n\n")
            img_idx += 1

    body_content = "\n\n".join(new_parts)
    categories_json = json.dumps(data.get('categories', ['Uncategorized']), ensure_ascii=False)
    tags_json = json.dumps(data.get('tags', []), ensure_ascii=False)
    summary = data.get('summary', '').replace('"', "'")

    full_md = f"""---
title: "{topic}"
date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
draft: false
categories: {categories_json}
tags: {tags_json}
summary: "{summary}"
cover: cover.jpg
---

{body_content}
"""

    with open(os.path.join(path, "index.md"), "w", encoding="utf-8") as f:
        f.write(full_md)
    print(f"✅ Saved to: {path}")

if __name__ == "__main__":
    topics = get_todays_hot_topics()
    print(f"🚀 Starting {len(topics)} tasks...\n")
    for topic in topics:
        try:
            main(topic)
            time.sleep(10)
        except Exception as e:
            print(f"❌ Error on '{topic}': {e}")
