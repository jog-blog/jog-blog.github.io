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

# ================= 配置区域 =================
# 优先从环境变量读取 (用于GitHub Actions)，如果本地没有环境变量则使用默认值
API_KEY = os.getenv("OPENAI_API_KEY", "sk-Fl2MU75boehSkbb671F707D93cF64513A17c09987eB9EcE9")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://free.v36.cm/v1/")
TEXT_MODEL_NAME = "gpt-4o-mini"

# 输出配置
OUTPUT_DIR = "content/posts"
# ⚠️ 注意：在 GitHub 上运行时，必须将 font.ttf 提交到仓库中
LOCAL_FONT_PATH = "font.ttf"
# ===========================================

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

class FreeAIImageGenerator:
    def __init__(self):
        self.width = 1200
        self.height = 630
        if os.path.exists(LOCAL_FONT_PATH):
            self.font_path = LOCAL_FONT_PATH
        else:
            self.font_path = None
            print("⚠️ 警告：未找到 font.ttf，图片中文将显示为方块！请确保仓库中包含字体文件。")

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
        """
        带重试机制的图片下载，防止只生成背景图
        """
        print(f"🎨 调用免费AI绘图: {prompt[:30]}...")

        # 优化提示词：强制写实风格，避免抽象
        enhanced_prompt = f"{prompt}, highly detailed, 8k resolution, cinematic lighting, photorealistic, wide angle, no text"
        safe_prompt = urllib.parse.quote(enhanced_prompt)

        # 使用随机种子
        seed = random.randint(0, 9999999)
        url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width={self.width}&height={self.height}&seed={seed}&model=flux&nologo=true"

        for attempt in range(retries):
            try:
                # 设置较长的超时时间
                res = requests.get(url, timeout=60)
                if res.status_code == 200:
                    content_type = res.headers.get('content-type', '')
                    if 'image' not in content_type:
                        print(f"⚠️ 第 {attempt+1} 次尝试返回非图片数据，重试...")
                        continue

                    img = Image.open(BytesIO(res.content))
                    # 简单校验：如果图片全是纯色（极少情况），视为失败
                    if img.getbbox() is None:
                        continue

                    return img.convert('RGB')
            except Exception as e:
                print(f"⚠️ 第 {attempt+1} 次绘图网络错误: {e}")
                time.sleep(2) # 失败后等待2秒

        print("❌ 多次尝试失败，使用兜底背景。")
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
        # 封面提示词更宏大
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
    """
    【新功能】让 AI 自动生成当天的热门选题
    """
    today_str = datetime.datetime.now().strftime("%Y年%m月%d日")
    print(f"🤖 正在分析 {today_str} 的全球趋势并生成选题...")

    prompt = f"""
    今天是 {today_str}。请作为一名资深主编，构思 3 个截然不同的热门博客选题。
    
    【要求】：
    1. 选题必须有时效性、争议性或深度。
    2. 覆盖三个领域：
       - 话题1：前沿科技/AI/互联网 (如 AI, Apple, crypto)
       - 话题2：国际大事件/经济/社会趋势
       - 话题3：生活方式/心理学/职场
    3. 直接返回一个 JSON 列表，不要有其他废话。格式：["标题1", "标题2", "标题3"]
    """

    try:
        res = client.chat.completions.create(
            model=TEXT_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8 # 提高创造性
        )
        content = res.choices[0].message.content.strip()
        if content.startswith("```json"): content = content[7:-3]
        elif content.startswith("```"): content = content[3:-3]

        topics = json.loads(content)
        print(f"✅ 今日选题已生成: {topics}")
        return topics
    except Exception as e:
        print(f"❌ 自动选题失败 ({e})，使用默认备选列表。")
        return [
            f"AI时代下的个人生存指南 ({today_str})",
            "全球经济放缓对普通人的影响",
            "如何建立深度工作的习惯"
        ]

def generate_text_content(topic):
    print(f"\n🧠 正在撰写文章: {topic}...")
    prompt = f"""
    请为主题“{topic}”写一篇深度博客。
    要求：
    1. 返回纯 JSON。包含 keys: 
       - summary (一句话摘要)
       - content (markdown正文，必须详细，分章节)
       - categories (list of strings, 自动归类，如 ["Tech", "News"])
       - tags (list of strings)
       - image_prompts (3个纯英文场景描述，用于生成插图)
    2. image_prompts 必须具体、写实，例如 "A busy street in Tokyo at night with neon lights"。
    3. 正文 > 1200 字。
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
        print(f"❌ 文本生成出错: {e}")
        return None

def main(topic):
    # 1. 准备目录
    clean_title = "".join([c for c in topic if c.isalnum()]).strip()
    # 使用日期+时间作为文件夹，防止重复
    folder = f"{clean_title}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    path = os.path.join(OUTPUT_DIR, folder)
    os.makedirs(path, exist_ok=True)

    # 2. 生成内容
    data = generate_text_content(topic)
    if not data: return

    # 3. 生成图片
    img_gen = FreeAIImageGenerator()
    print("🎨 生成封面中...")
    img_gen.generate_cover(topic, os.path.join(path, "cover.jpg"))

    img_map = []
    for i, prompt in enumerate(data.get('image_prompts', [])):
        fname = f"img_{i}.jpg"
        print(f"📊 生成插图 {i+1}/3...")
        img_gen.generate_content_image(prompt, os.path.join(path, fname))
        img_map.append((prompt, fname))

    # 4. 组装 Markdown
    content = data['content']
    paragraphs = content.split('\n\n')
    new_parts = []
    img_idx = 0

    for i, p in enumerate(paragraphs):
        new_parts.append(p)

        # 插入摘要分隔符
        if i == 0:
            new_parts.append("\n<!--more-->\n")

        # 智能插图
        if i > 1 and i % 3 == 0 and img_idx < len(img_map):
            desc, fname = img_map[img_idx]
            new_parts.append(f"\n\n![AI插图]({fname})\n*图示: {desc}*\n\n")
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
    print(f"✅ 文章生成完毕: {path}")

if __name__ == "__main__":
    # 1. 自动获取今日选题
    topics = get_todays_hot_topics()

    print(f"🚀 开始执行 {len(topics)} 个生成任务...\n")

    for topic in topics:
        try:
            main(topic)
            print("\n⏳ 休息 10 秒，准备下一篇 (防止接口限流)...\n")
            time.sleep(10)
        except Exception as e:
            print(f"❌ 任务 '{topic}' 异常终止: {e}")

    print("🎉 今日自动发文任务全部完成！")
