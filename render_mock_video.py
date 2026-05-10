import json
import os
import subprocess
from PIL import Image, ImageDraw, ImageFont


WIDTH = 1080
HEIGHT = 1920
SCENE_DURATION = 5
FPS = 30

os.makedirs("video/frames", exist_ok=True)
os.makedirs("output", exist_ok=True)

with open("stories/story.json", "r", encoding="utf-8") as f:
    story = json.load(f)

scenes = story["scenes"]

try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 54)
    font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
except:
    font_title = ImageFont.load_default()
    font_text = ImageFont.load_default()


def wrap_text(text, max_chars=34):
    words = text.split()
    lines = []
    line = ""

    for word in words:
        if len(line + " " + word) <= max_chars:
            line = (line + " " + word).strip()
        else:
            lines.append(line)
            line = word

    if line:
        lines.append(line)

    return lines


for i, scene in enumerate(scenes, start=1):
    img = Image.new("RGB", (WIDTH, HEIGHT), (15, 15, 20))
    draw = ImageDraw.Draw(img)

    title = story["title"]
    desc = scene["description"]

    draw.text((80, 160), title, font=font_title, fill=(240, 240, 240))

    y = 520
    for line in wrap_text(desc):
        draw.text((80, y), line, font=font_text, fill=(220, 220, 220))
        y += 58

    draw.text((80, 1680), f"Scene {i}", font=font_text, fill=(160, 160, 160))

    frame_path = f"video/frames/scene_{i:02d}.png"
    img.save(frame_path)


list_path = "video/frames/frames.txt"

with open(list_path, "w", encoding="utf-8") as f:
    for i in range(1, len(scenes) + 1):
        f.write(f"file 'scene_{i:02d}.png'\n")
        f.write(f"duration {SCENE_DURATION}\n")
    f.write(f"file 'scene_{len(scenes):02d}.png'\n")


output_path = "output/short_mock.mp4"

cmd = [
    "ffmpeg",
    "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", "video/frames/frames.txt",
    "-vf", f"fps={FPS},format=yuv420p",
    output_path
]

subprocess.run(cmd, check=True)

print(f"✅ Vídeo mock creado: {output_path}")
