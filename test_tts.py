import asyncio
import edge_tts

async def test():
    communicate = edge_tts.Communicate("Hello world. This is a test.", "en-GB-RyanNeural")
    chunks = []
    async for chunk in communicate.stream():
        chunks.append(chunk["type"])
        if chunk["type"] != "audio":
            print(chunk)
    print("\nChunk types:", set(chunks))

asyncio.run(test())
