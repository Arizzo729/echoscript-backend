import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# relative prefix (no /api or /v1)
router = APIRouter(prefix="/transcribe", tags=["transcription-stream"])

class DummyStreamer:
    async def feed(self, _pcm_bytes: bytes):
        return [{
            "id": str(uuid.uuid4()),
            "text": "(partial…)",
            "start": 0.0,
            "end": None,
            "final": False,
        }]

    async def flush(self):
        return [{
            "id": str(uuid.uuid4()),
            "text": "(final segment)",
            "start": 0.0,
            "end": 1.0,
            "final": True,
        }]

@router.websocket("/stream")
async def ws_stream(ws: WebSocket):
    await ws.accept()
    streamer = DummyStreamer()
    try:
        while True:
            chunk = await ws.receive_bytes()
            for seg in await streamer.feed(chunk):
                await ws.send_json({"type": "partial", **seg})
    except WebSocketDisconnect:
        for seg in await streamer.flush():
            await ws.send_json({"type": "final", **seg})

