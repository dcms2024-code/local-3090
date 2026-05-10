from core.model_router import run_task
import json
import os


prompt = """
Genera una historia corta de misterio para un Short de YouTube.

Reglas:
- Devuelve SOLO JSON válido.
- No añadas explicaciones.
- No uses markdown.
- Cierra correctamente todos los corchetes y llaves.
- Crea exactamente 5 escenas.
- Cada visual_prompt debe estar en inglés y ser cinematográfico.

Formato exacto:
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

print("\n=== RAW RESULT ===\n")
print(result)

data = json.loads(result)

os.makedirs("stories", exist_ok=True)

with open("stories/story.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("\n✅ Historia guardada en stories/story.json")
