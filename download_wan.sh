#!/bin/bash
# Token HF requerido - exportar antes de ejecutar:
#   export HF_TOKEN=hf_xxx
#   o crear /home/andreu/.hf_token con el token

if [ -z "$HF_TOKEN" ] && [ -f "/home/andreu/.hf_token" ]; then
  HF_TOKEN=$(cat /home/andreu/.hf_token)
fi

if [ -z "$HF_TOKEN" ]; then
  echo "ERROR: HF_TOKEN no definido. Exporta HF_TOKEN o crea /home/andreu/.hf_token"
  exit 1
fi

BASE=/home/andreu/ai-tools/ComfyUI/models
HF=https://huggingface.co/Kijai/WanVideo_comfy/resolve/main
HF_FP8=https://huggingface.co/Kijai/WanVideo_comfy_fp8_scaled/resolve/main

download() {
  local url="$1" dest="$2" name="$3"
  local size=$(stat -c%s "$dest" 2>/dev/null || echo 0)
  if [ "$size" -gt "1000000" ]; then
    echo "$name ya existe ($(stat -c%s $dest) bytes), saltando."
    return 0
  fi
  echo "[$(date +%H:%M:%S)] Descargando $name..."
  wget -c --retry-connrefused --tries=5 --waitretry=5 -q --show-progress \
    --header="Authorization: Bearer $HF_TOKEN" \
    -O "$dest" "$url"
  local ret=$?
  if [ $ret -eq 0 ]; then
    echo "$name OK - $(stat -c%s $dest) bytes"
  else
    echo "ERROR: $name fallo (exit $ret)"
  fi
}

download "$HF/Wan2_1_VAE_bf16.safetensors" \
  "$BASE/vae/Wan2_1_VAE_bf16.safetensors" "VAE (243MB)"

download "$HF/open-clip-xlm-roberta-large-vit-huge-14_visual_fp16.safetensors" \
  "$BASE/clip_vision/open-clip-vit-huge_fp16.safetensors" "CLIP vision (~600MB)"

download "$HF/umt5-xxl-enc-bf16.safetensors" \
  "$BASE/text_encoders/umt5-xxl-enc-bf16.safetensors" "T5 encoder (~9.5GB)"

download "$HF_FP8/I2V/Wan2_1-I2V-14B-480p_fp8_e4m3fn_scaled_KJ.safetensors" \
  "$BASE/diffusion_models/Wan2_1-I2V-14B-480p_fp8_e4m3fn_scaled_KJ.safetensors" "WAN I2V 14B fp8 (~14GB)"

echo "=== DESCARGA COMPLETA ==="
