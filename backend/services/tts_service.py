import edge_tts
import tempfile
import os


class TTSService:

    async def generate_speech(
        self,
        text: str,
        language: str = "en"
    ):

        try:

            voice_map = {
                "en": "en-US-AriaNeural",
                "hi": "hi-IN-SwaraNeural",
                "ta": "ta-IN-PallaviNeural",
            }

            voice = voice_map.get(
                language,
                "en-US-AriaNeural"
            )

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".mp3"
            ) as temp_audio:

                temp_path = temp_audio.name

            communicate = edge_tts.Communicate(
                text=text,
                voice=voice
            )

            await communicate.save(temp_path)

            with open(temp_path, "rb") as audio_file:
                audio_bytes = audio_file.read()

            os.remove(temp_path)

            return {
                "success": True,
                "audio": audio_bytes,
            }

        except Exception as e:
            print(f"TTS Error: {e}")

            return {
                "success": False,
                "error": str(e),
            }