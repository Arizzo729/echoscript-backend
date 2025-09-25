# === app/ws/socket_transcriber.py ===
from fastapi import WebSocket


async def websocket_endpoint(ws: WebSocket):
    """
    WebSocket endpoint for live transcription.
    Currently a stub that sends a 'Live transcription coming soon.' message.
    """
    await ws.accept()
    await ws.send_text("Live transcription coming soon.")
    # TODO: hook up real-time transcription stream here
