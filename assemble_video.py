import json
import subprocess
import os
import shutil


def get_audio_duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True
    )
    return float(result.stdout.strip())


with open("stories/story.json", "r", encoding="utf-8") as f:
    story = json.load(f)

images = sorted([f for f in os.listdir("images/generated") if f.endswith(".png")])
audio_path = "audio/narration.mp3"
subs_src = "audio/subtitles.srt"
os.makedirs("output", exist_ok=True)
os.makedirs("video", exist_ok=True)

duration = get_audio_duration(audio_path)
per_scene = duration / len(images)
print(f"Audio duration: {duration:.1f}s  |  {per_scene:.1f}s per scene", flush=True)

list_file = "video/images.txt"
with open(list_file, "w") as f:
    for img in images:
        f.write(f"file '../images/generated/{img}'\n")
        f.write(f"duration {per_scene:.2f}\n")
    f.write(f"file '../images/generated/{images[-1]}'\n")

# Step 1: video + audio
tmp_video = "output/tmp_notsubs.mp4"
cmd1 = [
    "ffmpeg", "-y",
    "-f", "concat", "-safe", "0", "-i", list_file,
    "-i", audio_path,
    "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
    "-c:v", "libx264", "-preset", "fast", "-crf", "23",
    "-c:a", "aac", "-b:a", "192k",
    "-pix_fmt", "yuv420p",
    "-shortest",
    tmp_video
]
print("Step 1: Rendering video with audio...", flush=True)
subprocess.run(cmd1, check=True, stderr=subprocess.DEVNULL)
print("Step 1 done.", flush=True)

# Step 2: burn subtitles
subs_tmp = "/tmp/mysubs.srt"
shutil.copy(subs_src, subs_tmp)
os.chmod(subs_tmp, 0o644)

if not os.path.exists(subs_tmp):
    print("WARNING: srt copy failed, skipping subtitles")
    shutil.copy(tmp_video, "output/final_short.mp4")
else:
    # Use escaped path for ffmpeg filter
    subs_escaped = subs_tmp.replace(":", "\\:")
    vf = f"subtitles={subs_escaped}"
    cmd2 = [
        "ffmpeg", "-y",
        "-i", tmp_video,
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        "output/final_short.mp4"
    ]
    print("Step 2: Burning subtitles...", flush=True)
    result = subprocess.run(cmd2, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Subtitle burn failed: {result.stderr[-300:]}")
        print("Saving video without subtitles.")
        shutil.copy(tmp_video, "output/final_short.mp4")
    else:
        print("Step 2 done.", flush=True)

if os.path.exists(tmp_video):
    os.remove(tmp_video)

size = os.path.getsize("output/final_short.mp4") // 1024
print(f"\nDone: output/final_short.mp4  ({size} KB)")
