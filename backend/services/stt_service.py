from faster_whisper import WhisperModel
import tempfile
import os


class STTService:

    def __init__(self):

        self.model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8"
        )

        print("[STT] Faster Whisper initialized")

    async def transcribe_audio(
        self,
        audio_bytes: bytes
    ):

        try:

            print(
                f"[STT] Audio received: {len(audio_bytes)} bytes"
            )

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".wav"
            ) as temp_audio:

                temp_audio.write(audio_bytes)

                temp_path = temp_audio.name

            segments, info = self.model.transcribe(
                temp_path,
                beam_size=1
            )

            text = " ".join(
                [segment.text for segment in segments]
            )

            os.remove(temp_path)

            print(
                f"[STT] Transcribed: {text}"
            )

            return {
                "success": True,
                "text": text,
                "language": info.language,
            }

        except Exception as e:

            print(f"[STT] Error: {e}")

            return {
                "success": False,
                "error": str(e),
            }