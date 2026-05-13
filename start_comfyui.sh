#!/bin/bash
PYTHON=/home/andreu/miniconda3/envs/comfyui/bin/python
cd /home/andreu/ai-tools/ComfyUI
nohup  main.py --listen 0.0.0.0 --port 8188 > /home/andreu/comfyui.log 2>&1 &
echo "ComfyUI PID: $!"
echo "Log: /home/andreu/comfyui.log"
echo "URL: http://192.168.1.107:8188"
