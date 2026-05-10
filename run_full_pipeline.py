import os
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)


def run(label, cmd):
    print(f"\n{'='*50}")
    print(f"  {label}")
    print('='*50)
    subprocess.run(cmd, check=True)


venv_python = os.path.join(BASE, "venv", "bin", "python")

run("1. Generating story JSON", [venv_python, "generate_and_save_story.py"])
run("2. Generating images", [venv_python, "auto_generate_images.py"])
run("3. Generating voice narration", [venv_python, "generate_voice.py"])
run("4. Assembling final video", [venv_python, "assemble_video.py"])

print("\n" + "="*50)
print("  PIPELINE COMPLETE")
print("="*50)
print("Output: output/final_short.mp4")
