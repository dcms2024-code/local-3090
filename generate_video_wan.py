"""
Image-to-video via ComfyUI WanVideoWrapper API.
Toma cada imagen de images/generated/ y genera un clip animado.
Requiere ComfyUI corriendo en localhost:8188.
"""
import json
import time
import uuid
import urllib.request
import urllib.parse
import os
import websocket

COMFY_URL = "http://127.0.0.1:8188"
WS_URL = "ws://127.0.0.1:8188/ws"

DIFFUSION_MODEL = "Wan2_1-I2V-14B-480P_fp8_e4m3fn.safetensors"
TEXT_ENCODER = "umt5-xxl-enc-bf16.safetensors"
CLIP_VISION = "clip_vision_h.safetensors"
VAE_MODEL = "Wan2_1_VAE_bf16.safetensors"

FRAMES = 81       # ~3.3s a 24fps
STEPS = 20
CFG = 6.0
WIDTH = 832
HEIGHT = 480


def queue_prompt(workflow, client_id):
    data = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req = urllib.request.Request(
        f"{COMFY_URL}/prompt", data=data,
        headers={"Content-Type": "application/json"}
    )
    return json.loads(urllib.request.urlopen(req).read())


def wait_for_completion(prompt_id, client_id):
    ws = websocket.WebSocket()
    ws.connect(f"{WS_URL}?clientId={client_id}")
    while True:
        msg = json.loads(ws.recv())
        if msg.get("type") == "executing":
            data = msg.get("data", {})
            if data.get("node") is None and data.get("prompt_id") == prompt_id:
                break
    ws.close()


def get_output_videos(prompt_id):
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as r:
        history = json.loads(r.read())
    outputs = history[prompt_id]["outputs"]
    videos = []
    for node_output in outputs.values():
        for v in node_output.get("videos", []):
            videos.append(v)
    return videos


def download_video(filename, subfolder, folder_type, out_path):
    params = urllib.parse.urlencode({
        "filename": filename, "subfolder": subfolder, "type": folder_type
    })
    with urllib.request.urlopen(f"{COMFY_URL}/view?{params}") as r:
        with open(out_path, "wb") as f:
            f.write(r.read())


def build_i2v_workflow(image_path, positive_prompt):
    abs_path = os.path.abspath(image_path)
    return {
        "1": {
            "class_type": "WanVideoModelLoader",
            "inputs": {
                "model": DIFFUSION_MODEL,
                "base_precision": "fp8_e4m3fn",
                "quantization": "disabled",
                "load_device": "main_device",
                "attention_mode": "sdpa"
            }
        },
        "2": {
            "class_type": "WanVideoVAELoader",
            "inputs": {"model_name": VAE_MODEL, "precision": "bf16"}
        },
        "3": {
            "class_type": "CLIPLoader",
            "inputs": {"clip_name": TEXT_ENCODER, "type": "wan"}
        },
        "4": {
            "class_type": "CLIPVisionLoader",
            "inputs": {"clip_name": CLIP_VISION}
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": abs_path}
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": positive_prompt,
                "clip": ["3", 0]
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "blurry, low quality, static, watermark",
                "clip": ["3", 0]
            }
        },
        "8": {
            "class_type": "WanVideoTextEmbedBridge",
            "inputs": {
                "positive": ["6", 0],
                "negative": ["7", 0]
            }
        },
        "9": {
            "class_type": "WanVideoI2VConditioningPipeline",
            "inputs": {
                "pipeline": ["1", 0],
                "vae": ["2", 0],
                "clip_vision": ["4", 0],
                "image": ["5", 0],
                "width": WIDTH,
                "height": HEIGHT,
                "num_frames": FRAMES,
                "text_embeds": ["8", 0]
            }
        },
        "10": {
            "class_type": "KSamplerSelect",
            "inputs": {"sampler_name": "euler"}
        },
        "11": {
            "class_type": "BasicScheduler",
            "inputs": {
                "model": ["1", 0],
                "scheduler": "simple_linear",
                "steps": STEPS,
                "denoise": 1.0
            }
        },
        "12": {
            "class_type": "SamplerCustomAdvanced",
            "inputs": {
                "noise": ["9", 1],
                "guider": ["9", 0],
                "sampler": ["10", 0],
                "sigmas": ["11", 0],
                "latent_image": ["9", 2]
            }
        },
        "13": {
            "class_type": "WanVideoVAEDecode",
            "inputs": {
                "vae": ["2", 0],
                "samples": ["12", 0],
                "enable_vae_tiling": True,
                "tile_sample_min_height": 272,
                "tile_sample_min_width": 272
            }
        },
        "14": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["13", 0],
                "frame_rate": 24,
                "loop_count": 0,
                "filename_prefix": "wan_clip",
                "format": "video/h264-mp4",
                "save_output": True
            }
        }
    }


os.makedirs("video/clips", exist_ok=True)

images = sorted([f for f in os.listdir("images/generated") if f.endswith(".png")])
print(f"Generando {len(images)} clips con WAN I2V...")

import json as _json
with open("stories/story.json") as f:
    story = _json.load(f)

scene_prompts = {s["scene"]: s["visual_prompt"] for s in story["scenes"]}

for img_file in images:
    scene_num = int(img_file.replace("scene_", "").replace(".png", ""))
    img_path = f"images/generated/{img_file}"
    prompt = scene_prompts.get(scene_num, "cinematic motion, smooth animation")
    out_path = f"video/clips/clip_{scene_num:02d}.mp4"

    if os.path.exists(out_path):
        print(f"  Scene {scene_num}: ya existe, saltando")
        continue

    print(f"  Scene {scene_num}: {prompt[:60]}...")
    client_id = str(uuid.uuid4())
    workflow = build_i2v_workflow(img_path, prompt)

    result = queue_prompt(workflow, client_id)
    prompt_id = result["prompt_id"]
    wait_for_completion(prompt_id, client_id)

    videos = get_output_videos(prompt_id)
    if videos:
        v = videos[0]
        download_video(v["filename"], v.get("subfolder", ""), v.get("type", "output"), out_path)
        print(f"  Guardado: {out_path}")
    else:
        print(f"  ERROR: no se generó vídeo para scene {scene_num}")

print("\nDone. Clips en video/clips/")
