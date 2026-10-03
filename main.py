from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import edge_tts
import io

app = FastAPI(title="Omar Edge TTS API")


class SpeechRequest(BaseModel):
    text: str
    voice: str = "ar-SA-HamedNeural"
    rate: str = "+0%"
    pitch: str = "+0Hz"


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "Omar Edge TTS",
        "message": "خدمة تحويل النص إلى صوت تعمل بنجاح"
    }


@app.get("/voices")
async def voices():
    voices = await edge_tts.list_voices()

    arabic = [
        {
            "name": v["ShortName"],
            "gender": v["Gender"],
            "locale": v["Locale"],
            "friendly_name": v.get("FriendlyName", "")
        }
        for v in voices
        if v["Locale"].startswith("ar-")
    ]

    return arabic


@app.post("/tts")
async def text_to_speech(request: SpeechRequest):

    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="النص فارغ"
        )

    try:
        audio = io.BytesIO()

        communicate = edge_tts.Communicate(
            request.text,
            request.voice,
            rate=request.rate,
            pitch=request.pitch
        )

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.write(chunk["data"])

        audio.seek(0)

        return StreamingResponse(
            audio,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"فشل توليد الصوت: {str(e)}"
        )
