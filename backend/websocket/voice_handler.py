"""
WebSocket handler for real-time voice streaming
"""

import base64
import logging
import time
import uuid

from fastapi import WebSocket, WebSocketDisconnect

from services.language_detection import (
    LanguageDetectionService,
)

from memory.session_memory import (
    RedisMemoryManager,
    PersistentMemoryManager,
)

from services.latency_tracker import (
    LatencyTracker,
)

logger = logging.getLogger(__name__)


class VoiceAgentWebSocketHandler:
    """Handles WebSocket voice conversations"""

    def __init__(
        self,
        db_session=None,
        stt_service=None,
        tts_service=None,
        llm_service=None,
    ):

        self.db_session = db_session

        # USE GLOBAL SINGLETON SERVICES
        self.stt_service = stt_service
        self.tts_service = tts_service
        self.orchestrator = llm_service

        self.language_detector = (
            LanguageDetectionService()
        )

        self.redis_memory = (
            RedisMemoryManager()
        )

        self.persistent_memory = (
            PersistentMemoryManager(db_session)
            if db_session
            else None
        )

    async def handle_connection(
        self,
        websocket: WebSocket,
        patient_id: str
    ):

        session_id = str(uuid.uuid4())

        latency_tracker = (
            LatencyTracker(session_id)
        )

        audio_buffer = bytearray()

        try:

            # CREATE SESSION
            await self.redis_memory.set_session(
                session_id,
                {
                    "session_id": session_id,
                    "patient_id": patient_id,
                    "language": "auto",
                    "context": {},
                    "state": "listening",
                    "created_at": time.time(),
                },
            )

            logger.info(
                f"WebSocket connected: {session_id}"
            )

            # SEND SESSION START
            await websocket.send_json({
                "type": "session_start",
                "session_id": session_id,
                "message": "Voice agent ready",
            })

            while True:

                message = await websocket.receive()

                # AUDIO DATA
                if "bytes" in message:

                    audio_chunk = message["bytes"]

                    if audio_chunk:
                        audio_buffer.extend(audio_chunk)

                # TEXT DATA
                elif "text" in message:

                    text_data = message["text"]

                    # HEARTBEAT
                    if text_data == "ping":

                        await websocket.send_json({
                            "type": "pong"
                        })

                        continue

                    # STOP RECORDING
                    if text_data == "STOP":

                        if audio_buffer:

                            logger.info(
                                f"[WebSocket] Audio buffer size: {len(audio_buffer)} bytes"
                            )

                            await self._process_audio(
                                websocket,
                                session_id,
                                patient_id,
                                bytes(audio_buffer),
                                latency_tracker,
                            )

                            audio_buffer.clear()

        except WebSocketDisconnect:

            logger.info(
                f"WebSocket disconnected: {session_id}"
            )

            await self._handle_disconnect(
                session_id
            )

        except Exception as e:

            logger.error(
                f"WebSocket error: {e}"
            )

            try:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                })
            except:
                pass

            await self._handle_disconnect(
                session_id
            )

    async def _process_audio(
        self,
        websocket: WebSocket,
        session_id: str,
        patient_id: str,
        audio_data: bytes,
        latency_tracker: LatencyTracker,
    ):

        try:

            session = await self.redis_memory.get_session(
                session_id
            )

            if not session:

                await websocket.send_json({
                    "type": "error",
                    "message": "Session not found",
                })

                return

            # =========================
            # STT
            # =========================

            latency_tracker.start("stt")

            stt_result = (
                await self.stt_service.transcribe_audio(
                    audio_data
                )
            )

            latency_tracker.end("stt")

            logger.info(f"[STT] Result: {stt_result}")

            if not stt_result["success"]:

                await websocket.send_json({
                    "type": "error",
                    "message": stt_result["error"],
                })

                return

            transcript = stt_result["text"]

            detected_language = (
                stt_result.get(
                    "language",
                    "en"
                )
            )

            # SEND TRANSCRIPT
            await websocket.send_json({
                "type": "transcript",
                "text": transcript,
                "language": detected_language,
            })

            # =========================
            # LLM
            # =========================

            latency_tracker.start("llm")

            llm_result = await self.orchestrator.generate_response(
                transcript
            )

            latency_tracker.end("llm")

            logger.info(f"[LLM] Result: {llm_result}")

            if not llm_result["success"]:

                await websocket.send_json({
                    "type": "error",
                    "message": llm_result["error"],
                })

                return

            response_text = llm_result["response"]

            # SEND RESPONSE
            await websocket.send_json({
                "type": "response",
                "text": response_text,
                "language": detected_language,
            })

            # =========================
            # TTS
            # =========================

            latency_tracker.start("tts")

            tts_result = (
                await self.tts_service.generate_speech(
                    response_text,
                    detected_language,
                )
            )

            latency_tracker.end("tts")

            logger.info(f"[TTS] Success: {tts_result['success']}")

            if tts_result["success"]:

                audio_base64 = (
                    base64.b64encode(
                        tts_result["audio"]
                    ).decode("utf-8")
                )

                await websocket.send_json({
                    "type": "audio_response",
                    "audio": audio_base64,
                })

            # =========================
            # LATENCY
            # =========================

            latency_report = (
                latency_tracker.get_report()
            )

            await websocket.send_json({
                "type": "latency_metrics",
                "total_latency_ms":
                    latency_report[
                        "total_latency_ms"
                    ],
                "breakdown":
                    latency_report[
                        "breakdown"
                    ],
            })

            # UPDATE SESSION
            await self.redis_memory.update_session(
                session_id,
                {
                    "state": "listening",
                    "last_response": response_text,
                    "transcript": transcript,
                    "language": detected_language,
                },
            )

            logger.info(
                f"Processed request: {session_id}"
            )

        except Exception as e:

            logger.error(
                f"Audio processing error: {e}"
            )

            await websocket.send_json({
                "type": "error",
                "message": "Failed to process audio",
            })

    async def _handle_disconnect(
        self,
        session_id: str
    ):

        try:

            await self.redis_memory.delete_session(
                session_id
            )

        except Exception as e:

            logger.error(
                f"Disconnect cleanup error: {e}"
            )