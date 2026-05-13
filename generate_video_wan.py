"""
WAN 2.1 Image-to-Video via ComfyUI API.
Genera clips animados desde imágenes estáticas.
Uso: python generate_video_wan.py [directorio_imagenes] [story_json]
"""
import json, time, uuid, sys, os
import urllib.request, urllib.parse
import websocket

COMFY_URL = "http://127.0.0.1:8188"
WS_URL    = "ws://127.0.0.1:8188/ws"

DIFFUSION_MODEL = "Wan2_1-I2V-14B-480p_fp8_e4m3fn_scaled_KJ.safetensors"
VAE_MODEL       = "Wan2_1_VAE_bf16.safetensors"
CLIP_VISION     = "open-clip-vit-huge_fp16.safetensors"
T5_ENCODER      = "umt5-xxl-enc-bf16.safetensors"

FRAMES  = 49    # ~2s a 24fps (480p, más rápido)
STEPS   = 20
CFG     = 5.0
WIDTH   = 480
HEIGHT  = 832   # vertical 9:16 aproximado


def queue_prompt(workflow, client_id):
    data = json.dumps({"prompt": workflow, "client_id": client_id}).encode()
    req  = urllib.request.Request(
        f"{COMFY_URL}/prompt", data=data,
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req).read()
    return json.loads(resp)


def wait_done(prompt_id, client_id):
    ws = websocket.WebSocket()
    ws.connect(f"{WS_URL}?clientId={client_id}")
    while True:
        msg = json.loads(ws.recv())
        if msg.get("type") == "executing":
            d = msg.get("data", {})
            if d.get("node") is None and d.get("prompt_id") == prompt_id:
                break
    ws.close()


def get_output_videos(prompt_id):
    with urllib.request.urlopen(f"{COMFY_URL}/history/{prompt_id}") as r:
        history = json.loads(r.read())
    videos = []
    for node_output in history[prompt_id]["outputs"].values():
        for v in node_output.get("videos", []):
            videos.append(v)
    return videos


def download_video(filename, subfolder, folder_type, out_path):
    params = urllib.parse.urlencode(
        {"filename": filename, "subfolder": subfolder, "type": folder_type}
    )
    with urllib.request.urlopen(f"{COMFY_URL}/view?{params}") as r:
        with open(out_path, "wb") as f:
            f.write(r.read())


def upload_image(img_path):
    """Sube una imagen a ComfyUI y devuelve el nombre asignado."""
    with open(img_path, "rb") as f:
        data = f.read()
    boundary = "----FormBoundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{os.path.basename(img_path)}"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{COMFY_URL}/upload/image",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    return resp["name"]


def build_i2v_workflow(image_name, positive_prompt, seed):
    return {
        "1": {
            "class_type": "WanVideoModelLoader",
            "inputs": {
                "model": DIFFUSION_MODEL,
                "base_precision": "fp16",
                "quantization": "fp8_e4m3fn_scaled",
                "load_device": "main_device",
                "attention_mode": "sdpa"
            }
        },
        "2": {
            "class_type": "WanVideoVAELoader",
            "inputs": {"model_name": VAE_MODEL, "precision": "bf16"}
        },
        "3": {
            "class_type": "LoadWanVideoClipTextEncoder",
            "inputs": {
                "model_name": CLIP_VISION,
                "precision": "fp16",
                "load_device": "offload_device"
            }
        },
        "4": {
            "class_type": "LoadWanVideoT5TextEncoder",
            "inputs": {
                "model_name": T5_ENCODER,
                "precision": "bf16",
                "load_device": "offload_device"
            }
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": image_name}
        },
        "6": {
            "class_type": "WanVideoClipVisionEncode",
            "inputs": {
                "clip_vision": ["3", 0],
                "image_1": ["5", 0],
                "strength_1": 1.0,
                "strength_2": 1.0,
                "crop": "center",
                "combine_embeds": "average",
                "force_offload": True
            }
        },
        "7": {
            "class_type": "WanVideoImageToVideoEncode",
            "inputs": {
                "width": WIDTH,
                "height": HEIGHT,
                "num_frames": FRAMES,
                "noise_aug_strength": 0.0,
                "start_latent_strength": 1.0,
                "end_latent_strength": 0.0,
                "force_offload": False,
                "vae": ["2", 0],
                "clip_embeds": ["6", 0],
                "start_image": ["5", 0]
            }
        },
        "8": {
            "class_type": "WanVideoTextEncodeSingle",
            "inputs": {
                "prompt": positive_prompt,
                "t5": ["4", 0],
                "force_offload": True
            }
        },
        "9": {
            "class_type": "WanVideoSampler",
            "inputs": {
                "model": ["1", 0],
                "image_embeds": ["7", 0],
                "steps": STEPS,
                "cfg": CFG,
                "shift": 8.0,
                "seed": seed,
                "force_offload": True,
                "scheduler": "unipc",
                "riflex_freq_index": 0,
                "text_embeds": ["8", 0]
            }
        },
        "10": {
            "class_type": "WanVideoDecode",
            "inputs": {
                "vae": ["2", 0],
                "samples": ["9", 0],
                "enable_vae_tiling": True,
                "tile_x": 272,
                "tile_y": 272,
                "tile_stride_x": 144,
                "tile_stride_y": 144
            }
        },
        "11": {
            "class_type": "VHS_VideoCombine",
            "inputs": {
                "images": ["10", 0],
                "frame_rate": 24,
                "loop_count": 0,
                "filename_prefix": "wan_clip",
                "format": "video/h264-mp4",
                "pingpong": False,
                "save_output": True
            }
        }
    }


# ── Main ──────────────────────────────────────────────────────────────────────

img_dir   = sys.argv[1] if len(sys.argv) > 1 else "images/generated"
json_path = sys.argv[2] if len(sys.argv) > 2 else "stories/story.json"
out_dir   = "video/clips"
os.makedirs(out_dir, exist_ok=True)

with open(json_path, encoding="utf-8") as f:
    story = json.load(f)

scenes = story.get("scenes", [])
# soporta formato archivos_ocultos (prompt) y mystery (visual_prompt)
scene_prompts = {}
for s in scenes:
    idx = s.get("scene", len(scene_prompts) + 1)
    scene_prompts[int(idx)] = s.get("prompt") or s.get("visual_prompt", "cinematic motion")

images = sorted([f for f in os.listdir(img_dir) if f.endswith(".png")])
print(f"Generando {len(images)} clips WAN I2V desde {img_dir}...")

for img_file in images:
    # detectar número de escena del nombre de archivo
    name = img_file.replace("scene_", "").replace("archivos_", "").replace(".png", "")
    try:
        scene_num = int(name.split("_")[0] if "_" in name else name)
    except ValueError:
        scene_num = images.index(img_file) + 1

    out_path = f"{out_dir}/clip_{scene_num:02d}.mp4"
    if os.path.exists(out_path):
        print(f"  Escena {scene_num}: ya existe, saltando")
        continue

    prompt = scene_prompts.get(scene_num, "cinematic motion, smooth camera movement")
    print(f"  Escena {scene_num}/{len(images)}: {prompt[:55]}...")

    img_path = os.path.join(img_dir, img_file)
    image_name = upload_image(img_path)

    client_id = str(uuid.uuid4())
    workflow  = build_i2v_workflow(image_name, prompt, seed=scene_num * 42)

    try:
        result    = queue_prompt(workflow, client_id)
        prompt_id = result["prompt_id"]
        print(f"    En cola: {prompt_id[:8]}... generando (~2 min)")
        wait_done(prompt_id, client_id)

        videos = get_output_videos(prompt_id)
        if videos:
            v = videos[0]
            download_video(v["filename"], v.get("subfolder", ""), v.get("type", "output"), out_path)
            size = os.path.getsize(out_path) // 1024
            print(f"    Guardado: {out_path} ({size} KB)")
        else:
            print(f"    ERROR: no se generó vídeo para escena {scene_num}")
    except Exception as e:
        print(f"    ERROR escena {scene_num}: {e}")

print(f"\nClips en {out_dir}/")
