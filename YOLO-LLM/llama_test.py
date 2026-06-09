from ollama import chat

MODEL = "llama3.2:3b"

response = chat(
    model=MODEL,
    messages=[
        {
            "role": "system",
            "content": "Responde en español, de forma breve y técnica.",
        },
        {
            "role": "user",
            "content": "Explica en una frase para qué sirve YOLO en visión por computador.",
        },
    ],
)

print(response["message"]["content"])