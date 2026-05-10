import json
import asyncio
import edge_tts
import os

VOICE = "en-GB-RyanNeural"


async def generate_voice():
    with open("stories/story.json", "r", encoding="utf-8") as f:
        story = json.load(f)

    parts = [story["hook"]]
    for scene in story["scenes"]:
        parts.append(scene["description"])
    parts.append(story["ending"])
    narration = " ... ".join(parts)

    os.makedirs("audio", exist_ok=True)

    communicate = edge_tts.Communicate(narration, VOICE)
    submaker = edge_tts.SubMaker()

    with open("audio/narration.mp3", "wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                submaker.feed(chunk)

    srt = submaker.get_srt()
    with open("audio/subtitles.srt", "w", encoding="utf-8") as srt_file:
        srt_file.write(srt)

    lines = srt.strip().splitlines()
    print(f"Voice saved: audio/narration.mp3")
    print(f"Subtitles saved: audio/subtitles.srt  ({len(lines)} lines)")


asyncio.run(generate_voice())
