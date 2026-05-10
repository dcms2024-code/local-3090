import json
import time
import uuid
import urllib.request
import urllib.parse
import os

COMFY_URL = "http://127.0.0.1:8188"
CHECKPOINT = "juggernaut.safetensors"

os.makedirs("images/generated", exist_ok=True)

with open("stories/story.json", "r", encoding="utf-8") as f:
    story = json.load(f)

client_id = str(uuid.uuid4())


def queue_prompt(prompt):
    data = json.dumps({
        "prompt": prompt,
        "client_id": client_id
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{COMFY_URL}/prompt",
        data=data,
        headers={"Content-Type": "application/json"}
    )

    return json.loads(urllib.request.urlopen(req).read())


def get_history(prompt_id):
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as r:
        return json.loads(r.read())


def download_image(filename, subfolder, folder_type, out_path):
    params = urllib.parse.urlencode({
        "filename": filename,
        "subfolder": subfolder,
        "type": folder_type
    })

    url = f"{COMFY_URL}/view?{params}"

    with urllib.request.urlopen(url) as r:
        with open(out_path, "wb") as f:
            f.write(r.read())


def build_workflow(positive_prompt, scene_number):
    negative_prompt = (
        "people, woman, girl, child, face, portrait, blurry, low quality, "
        "watermark, text, logo, distorted, bad anatomy"
    )

    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": CHECKPOINT
            }
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": positive_prompt,
                "clip": ["1", 1]
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": negative_prompt,
                "clip": ["1", 1]
            }
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 768,
                "height": 1344,
                "batch_size": 1
            }
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": scene_number * 1234567,
                "steps": 25,
                "cfg": 7,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0]
            }
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["1", 2]
            }
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": f"scene_{scene_number:02d}",
                "images": ["6", 0]
            }
        }
    }


for scene in story["scenes"]:
    scene_number = int(scene["scene"])

    visual_prompt = scene["visual_prompt"]
    positive_prompt = (
        visual_prompt
        + ", cinematic lighting, mysterious atmosphere, ultra realistic, "
        + "movie still, vertical composition, highly detailed, no people"
    )

    print(f"\nGenerating scene {scene_number}...")
    print(positive_prompt)

    workflow = build_workflow(positive_prompt, scene_number)
    result = queue_prompt(workflow)
    prompt_id = result["prompt_id"]

    while True:
        history = get_history(prompt_id)
        if prompt_id in history:
            break
        time.sleep(2)

    outputs = history[prompt_id]["outputs"]

    for node_id, node_output in outputs.items():
        if "images" in node_output:
            image = node_output["images"][0]
            out_path = f"images/generated/scene_{scene_number:02d}.png"

            download_image(
                image["filename"],
                image.get("subfolder", ""),
                image.get("type", "output"),
                out_path
            )

            print(f"Saved {out_path}")

print("\nDONE. Images generated in images/generated/")
