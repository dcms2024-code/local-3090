#!/bin/bash
# Setup script para nuevo worker con RTX 3090 (Ubuntu 20.04)
# Uso: bash setup_worker.sh
# Requiere: sudo NOPASSWD configurado

set -e
LOG=~/setup_worker.log
exec > >(tee -a ) 2>&1

ENPC_IP=192.168.1.107
PYTHON=/home/andreu/miniconda3/bin/python

echo "=== SETUP WORKER mié 13 may 2026 11:58:08 CEST ==="

# 1. Dependencias sistema
echo "[1/6] System deps..."
sudo apt-get update -q
sudo apt-get install -y zstd git curl wget rsync -q

# 2. Miniconda3
echo "[2/6] Miniconda3..."
if [ ! -f ~/miniconda3/bin/python ]; then
  wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh
  bash /tmp/miniconda.sh -b -p ~/miniconda3
fi
export PATH=~/miniconda3/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin

# 3. Ollama
echo "[3/6] Ollama..."
if ! command -v ollama &>/dev/null; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
sudo systemctl enable ollama --now 2>/dev/null || true

# 4. ComfyUI
echo "[4/6] ComfyUI + WAN nodes..."
mkdir -p ~/ai-tools
if [ ! -d ~/ai-tools/ComfyUI ]; then
  git clone https://github.com/comfyanonymous/ComfyUI ~/ai-tools/ComfyUI
  cd ~/ai-tools/ComfyUI
  ~/miniconda3/bin/pip install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu121 -q
  ~/miniconda3/bin/pip install -r requirements.txt -q
fi
cd ~/ai-tools/ComfyUI/custom_nodes
for REPO in ComfyUI-KJNodes ComfyUI-VideoHelperSuite ComfyUI-WanVideoWrapper; do
  [ ! -d  ] && git clone https://github.com/kijai/ 2>/dev/null || git clone https://github.com/Kosinkadink/ 2>/dev/null || true
  [ -f /requirements.txt ] && ~/miniconda3/bin/pip install -r /requirements.txt -q || true
done

# 5. Pipeline repos
echo "[5/6] Repos..."
mkdir -p ~/ai-projects
[ ! -d ~/ai-projects/local-3090 ] && git clone https://github.com/dcms2024-code/local-3090 ~/ai-projects/local-3090
mkdir -p ~/inspiring-factory

# 6. Python deps
echo "[6/6] Python deps..."
~/miniconda3/bin/pip install edge-tts ollama websocket-client Pillow ffmpeg-python requests -q

# Start script ComfyUI
printf '#!/bin/bash
source ~/miniconda3/bin/activate
cd ~/ai-tools/ComfyUI
nohup python main.py --listen 0.0.0.0 --port 8188 > ~/comfyui.log 2>&1 &
echo ComfyUI PID: 
' > ~/start_comfyui.sh
chmod +x ~/start_comfyui.sh

echo "=== SETUP COMPLETO mié 13 may 2026 11:58:08 CEST ==="
echo "Siguiente: rsync modelos WAN desde "
echo "  rsync -avP andreu@:~/ai-tools/ComfyUI/models/ ~/ai-tools/ComfyUI/models/"
echo "  rsync -avP andreu@:~/inspiring-factory/ ~/inspiring-factory/"
