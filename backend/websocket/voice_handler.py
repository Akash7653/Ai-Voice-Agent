"""
WebSocket handler for real-time voice streaming
"""

import base64
import logging
import time
import uuid

from typing import Dict, Any, Optional

from fastapi import WebSocket, WebSocketDisconnect

from services.stt_service import STTService
from services.tts_service import TTSService

from services.language_detection import (
    LanguageDetectionService,
)

from agent.orchestrator.llm_orchestrator import LLMService

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

    def __init__(self, db_session=None):

        self.db_session = db_session

        # FREE STT
        self.stt_service = STTService()

        # FREE TTS
        self.tts_service = TTSService()

        self.language_detector = (
            LanguageDetectionService()
        )

        self.orchestrator = LLMService()

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

            await websocket.accept()

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
                "message":
                    "Voice agent ready",
            })

            # MAIN LOOP
            while True:

                message = await websocket.receive()

                # AUDIO CHUNK
                if "bytes" in message:

                    audio_chunk = message["bytes"]

                    if audio_chunk:
                        audio_buffer.extend(audio_chunk)

                # CLIENT SENT STOP
                elif "text" in message:

                    text_data = message["text"]

                    if text_data == "STOP":

                        if audio_buffer:

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

            if not stt_result["success"]:

                await websocket.send_json({
                    "type": "error",
                    "message":
                        stt_result["error"],
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
                "language":
                    detected_language,
            })

            # =========================
            # LLM
            # =========================

            latency_tracker.start("llm")

            reasoning_result, _ = (
                await self.orchestrator.reason_and_plan(
                    user_input=transcript,
                    language=detected_language,
                    session_context=session.get(
                        "context",
                        {}
                    ),
                )
            )

            latency_tracker.end("llm")

            # SEND REASONING TRACE
            await websocket.send_json({
                "type": "reasoning_trace",
                "intent":
                    reasoning_result.get(
                        "intent"
                    ),

                "confidence":
                    reasoning_result.get(
                        "confidence",
                        0,
                    ),

                "entities":
                    reasoning_result.get(
                        "entities",
                        {}
                    ),

                "reasoning":
                    reasoning_result.get(
                        "reasoning",
                        ""
                    ),
            })

            # =========================
            # TOOL EXECUTION
            # =========================

            tool_result = None

            if (
                reasoning_result.get(
                    "intent"
                )
                != "small_talk"
            ):

                latency_tracker.start(
                    "tools"
                )

                intent_to_tool = {
                    "book_appointment":
                        "book_appointment",

                    "reschedule_appointment":
                        "reschedule_appointment",

                    "cancel_appointment":
                        "cancel_appointment",

                    "check_availability":
                        "check_availability",
                }

                tool_name = (
                    intent_to_tool.get(
                        reasoning_result.get(
                            "intent"
                        )
                    )
                )

                if tool_name:

                    tool_args = (
                        reasoning_result.get(
                            "entities",
                            {}
                        )
                    )

                    tool_args[
                        "patient_id"
                    ] = patient_id

                    tool_result = (
                        await self.orchestrator.execute_tool(
                            tool_name,
                            tool_args,
                            language=
                                detected_language,
                        )
                    )

                latency_tracker.end(
                    "tools"
                )

            # =========================
            # RESPONSE
            # =========================

            if (
                tool_result
                and tool_result.get(
                    "success"
                )
            ):

                response_text = (
                    tool_result.get(
                        "message",
                        "Done",
                    )
                )

            else:

                response_text = (
                    reasoning_result.get(
                        "response",
                        "I could not process your request.",
                    )
                )

            # SEND TEXT RESPONSE
            await websocket.send_json({
                "type": "response",
                "text": response_text,
                "language":
                    detected_language,
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

            # SEND AUDIO
            if tts_result["success"]:

                audio_base64 = (
                    base64.b64encode(
                        tts_result["audio"]
                    ).decode("utf-8")
                )

                await websocket.send_json({
                    "type": "audio_response",
                    "audio":
                        audio_base64,
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
                    "last_response":
                        response_text,

                    "transcript":
                        transcript,

                    "language":
                        detected_language,
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
                "message":
                    "Failed to process audio",
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