"""
Speech-to-Text service using OpenAI Whisper
"""
import os
import io
import time
import tempfile
from  pathlib import Path
from  typing import Optional, Tuple

class STTService:
    """Speech-to-Text service using Whisper"""
    
    def __init__(self):
        try:
            from  openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            print(f"Error initializing STT service: {e}")
            self.client = None
    
    @staticmethod
    def _guess_filename(audio_data: bytes) -> str:
        if len(audio_data) >= 4 and audio_data[:4] == b"RIFF":
            return "audio.wav"
        if len(audio_data) >= 4 and audio_data[0:1] == b"\x1a":
            return "audio.webm"
        if len(audio_data) >= 8 and audio_data[4:8] == b"ftyp":
            return "audio.mp4"
        return "audio.webm"

    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        save_debug: bool = False,
    ) -> Tuple[str, float, Optional[str]]:
        """
        Transcribe audio to text.
        Returns (transcript, latency_ms, error_message).
        error_message is set when transcription fails (not for empty speech).
        """
        start_time = time.time()

        if not self.client:
            return "", 0, "OPENAI_API_KEY missing — set it in backend/.env and restart the server."

        print(f"[STT] Audio received: {len(audio_data)} bytes")
        if len(audio_data) < 1000:
            return "", 0, f"Audio too short ({len(audio_data)} bytes). Record at least 2 seconds of speech."

        filename = self._guess_filename(audio_data)

        if save_debug:
            suffix = Path(filename).suffix or ".bin"
            debug_dir = Path(tempfile.gettempdir()) / "voice-agent-debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            debug_path = debug_dir / f"debug_audio{suffix}"
            debug_path.write_bytes(audio_data)
            print(f"[STT] Debug audio saved: {debug_path}")

        try:
            audio_file = io.BytesIO(audio_data)
            audio_file.name = filename

            transcription_kwargs = {
                "model": "whisper-1",
                "file": audio_file,
            }

            lang = (language or "auto").lower()
            if lang not in {"en", "auto", "hi", "ta"}:
                lang = None
            if lang and lang != "auto":
                transcription_kwargs["language"] = lang

            print(f"[STT] Whisper request: file={filename}, language={lang or 'auto'}")
            response = await self.client.audio.transcriptions.create(**transcription_kwargs)

            latency_ms = (time.time() - start_time) * 1000
            text = (response.text or "").strip()
            print(f"[STT] Done ({latency_ms:.0f}ms): {text!r}")

            if not text:
                return "", latency_ms, "No speech detected in recording. Speak louder and try again."

            return text, latency_ms, None

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            err = str(e)
            print(f"[STT] Error: {err}")
            import traceback
            traceback.print_exc()

            if "api_key" in err.lower() or "authentication" in err.lower() or "401" in err:
                return "", latency_ms, "Invalid or missing OPENAI_API_KEY in backend/.env"
            if "invalid" in err.lower() and "file" in err.lower():
                return "", latency_ms, f"Unsupported audio format for Whisper ({filename}). Try Chrome/Edge and record again."
            return "", latency_ms, f"Whisper API error: {err}"

class TTSService:
    """Text-to-Speech service using OpenAI or ElevenLabs"""
    
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        
        if provider == "openai":
            try:
                from  openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            except Exception as e:
                print(f"Error initializing TTS service: {e}")
                self.client = None
        elif provider == "elevenlabs":
            try:
                import elevenlabs
                self.client = elevenlabs
            except Exception as e:
                print(f"Error initializing ElevenLabs TTS: {e}")
                self.client = None
    
    async def synthesize(
        self,
        text: str,
        language: str = "en",
        voice: Optional[str] = None
    ) -> tuple[bytes, float]:
        """
        Synthesize text to speech
        Returns (audio_data, latency_ms)
        """
        start_time = time.time()
        
        try:
            if self.provider == "openai":
                return await self._synthesize_openai(text, voice)
            elif self.provider == "elevenlabs":
                return await self._synthesize_elevenlabs(text, language)
            else:
                return b"", 0
        
        except Exception as e:
            print(f"Error synthesizing speech: {e}")
            return b"", 0
    
    async def _synthesize_openai(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> tuple[bytes, float]:
        """OpenAI TTS"""
        start_time = time.time()
        
        if not self.client:
            return b"", 0
        
        try:
            voice = voice or os.getenv("OPENAI_TTS_VOICE", "nova")
            
            response = await self.client.audio.speech.create(
                model=os.getenv("OPENAI_TTS_MODEL", "tts-1"),
                voice=voice,
                input=text,
            )
            
            latency_ms = (time.time() - start_time) * 1000
            return response.content, latency_ms
        
        except Exception as e:
            print(f"Error with OpenAI TTS: {e}")
            return b"", 0
    
    async def _synthesize_elevenlabs(
        self,
        text: str,
        language: str
    ) -> tuple[bytes, float]:
        """ElevenLabs TTS"""
        start_time = time.time()
        
        try:
            # ElevenLabs implementation would go here
            # This is a placeholder
            latency_ms = (time.time() - start_time) * 1000
            return b"", latency_ms
        
        except Exception as e:
            print(f"Error with ElevenLabs TTS: {e}")
            return b"", 0
