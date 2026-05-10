from core.model_router import run_task


prompt = """
Escribe una historia de misterio sobre una radio que recibe mensajes del futuro.
Duración aproximada: 45 segundos.
Final inquietante.
"""

result = run_task("story", prompt)

print("\n=== RESULTADO ===\n")
print(result)
