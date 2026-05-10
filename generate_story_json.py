from core.model_router import run_task
import json


prompt = """
Genera una historia corta de misterio para un Short de YouTube.

Devuelve SOLO JSON válido.

Formato:

{
  "title": "...",
  "hook": "...",
  "story": "...",
  "ending": "...",
  "scenes": [
    {
      "scene": 1,
      "description": "...",
      "visual_prompt": "..."
    }
  ]
}
"""

result = run_task("story", prompt)

print("\n=== RESULTADO JSON ===\n")
print(result)
