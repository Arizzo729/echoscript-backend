import io
import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app

BASE_URL = "http://test"

@pytest.mark.asyncio
async def test_upload_transcribe():
    """
    Mocks the Whisper model to avoid loading dependencies like matplotlib and torchmetrics.
    """

    mock_model = MagicMock()
    mock_model.transcribe.return_value = (
        [MagicMock(text="Hello world")],
        MagicMock(language="en")
    )

    fake_audio = io.BytesIO(b"RIFF....WAVEfmt " + b"\x00" * 4000)
    fake_audio.name = "test.wav"

    transport = ASGITransport(app=app)

    with patch("app.main.load_model", return_value=mock_model):
        with patch("app.main.apply_gpt_cleanup", return_value="Hello world"):
            async with AsyncClient(transport=transport, base_url=BASE_URL) as client:
                response = await client.post(
                    "/api/transcribe",
                    files={"file": ("test.wav", fake_audio, "audio/wav")},
                    data={"language": "en"}
                )

                assert response.status_code == 200
                data = response.json()
                assert data["transcript"] == "Hello world"
                assert data["language"] == "en"


