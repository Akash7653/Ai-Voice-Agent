from faster_whisper import WhisperModel
import tempfile
import os


class STTService:

    def __init__(self):

        print("[STT] Loading Faster Whisper model...")

        self.model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8"
        )

        print("[STT] Faster Whisper initialized")

    async def transcribe_audio(
        self,
        audio_data: bytes
    ):

        try:

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".wav"
            ) as temp_audio:

                temp_audio.write(audio_data)

                temp_audio_path = temp_audio.name

            segments, info = self.model.transcribe(
                temp_audio_path
            )

            text = " ".join(
                [segment.text for segment in segments]
            )

            os.remove(temp_audio_path)

            return {
                "success": True,
                "text": text,
                "language": info.language,
            }

        except Exception as e:

            return {
                "success": False,
                "error": str(e),
            }