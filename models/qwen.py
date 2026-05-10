import ollama


def ask_qwen(prompt: str):
    response = ollama.chat(
        model="qwen2.5:14b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]
