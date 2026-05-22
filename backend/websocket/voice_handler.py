import json
import uuid
import logging
import tempfile
import os
from fastapi import WebSocket, WebSocketDisconnect

from services.stt_service import STTService
from services.tts_service import TTSService
from agent.orchestrator.llm_orchestrator import LLMOrchestrator

logger = logging.getLogger(__name__)


class VoiceAgentWebSocketHandler:

    _stt_service = None
    _tts_service = None
    _llm_service = None

    def __init__(self, db_session=None):

        self.db_session = db_session

        # LOAD ONLY ONCE
        if VoiceAgentWebSocketHandler._stt_service is None:
            print("[INIT] Loading STT...")
            VoiceAgentWebSocketHandler._stt_service = STTService()

        if VoiceAgentWebSocketHandler._tts_service is None:
            print("[INIT] Loading TTS...")
            VoiceAgentWebSocketHandler._tts_service = TTSService()

        if VoiceAgentWebSocketHandler._llm_service is None:
            print("[INIT] Loading LLM...")
            VoiceAgentWebSocketHandler._llm_service = (
                LLMOrchestrator()
            )

        self.stt_service = VoiceAgentWebSocketHandler._stt_service
        self.tts_service = VoiceAgentWebSocketHandler._tts_service
        self.llm_service = VoiceAgentWebSocketHandler._llm_service

    async def handle(self, websocket: WebSocket, patient_id: str):

        await websocket.accept()

        session_id = str(uuid.uuid4())

        logger.info(f"[WebSocket] Connected: {session_id}")

        audio_chunks = bytearray()

        try:

            while True:

                data = await websocket.receive()

                # DISCONNECT
                if data["type"] == "websocket.disconnect":
                    logger.info("[WebSocket] Client disconnected")
                    break

                # BINARY AUDIO
                if "bytes" in data and data["bytes"]:

                    chunk = data["bytes"]

                    audio_chunks.extend(chunk)

                    logger.info(
                        f"[Audio] Chunk received: {len(chunk)} bytes"
                    )

                # TEXT MESSAGE
                elif "text" in data and data["text"]:

                    text = data["text"]

                    logger.info(f"[Message] {text}")

                    # END AUDIO SIGNAL
                    if text == "END_AUDIO":

                        logger.info(
                            f"[Audio] Total size: {len(audio_chunks)} bytes"
                        )

                        if len(audio_chunks) < 1000:

                            await websocket.send_json({
                                "type": "error",
                                "message": "Audio too short"
                            })

                            audio_chunks = bytearray()
                            continue

                        # SAVE TEMP AUDIO
                        with tempfile.NamedTemporaryFile(
                            suffix=".wav",
                            delete=False
                        ) as tmp:

                            tmp.write(audio_chunks)

                            temp_audio_path = tmp.name

                        try:

                            #
                            # STT
                            #
                            logger.info("[PIPELINE] STT started")

                            transcript = await self.stt_service.transcribe(
                                temp_audio_path
                            )

                            logger.info(
                                f"[TRANSCRIPT] {transcript}"
                            )

                            await websocket.send_json({
                                "type": "transcript",
                                "text": transcript
                            })

                            #
                            # LLM
                            #
                            logger.info("[PIPELINE] LLM started")

                            llm_response = (
                                await self.llm_service.generate_response(
                                    transcript
                                )
                            )

                            response_text = (
                                llm_response.get("response")
                                if isinstance(llm_response, dict)
                                else str(llm_response)
                            )

                            logger.info(
                                f"[LLM] {response_text}"
                            )

                            await websocket.send_json({
                                "type": "response",
                                "text": response_text
                            })

                            #
                            # TTS
                            #
                            logger.info("[PIPELINE] TTS started")

                            audio_base64 = (
                                await self.tts_service.text_to_speech(
                                    response_text
                                )
                            )

                            await websocket.send_json({
                                "type": "audio_response",
                                "audio": audio_base64
                            })

                            logger.info(
                                "[PIPELINE] Completed"
                            )

                        except Exception as e:

                            logger.exception(
                                "[PIPELINE ERROR]"
                            )

                            await websocket.send_json({
                                "type": "error",
                                "message": str(e)
                            })

                        finally:

                            if os.path.exists(temp_audio_path):
                                os.remove(temp_audio_path)

                            audio_chunks = bytearray()

        except WebSocketDisconnect:

            logger.info("[WebSocket] Disconnected")

        except Exception as e:

            logger.exception("[WebSocket ERROR]")

            try:
                await websocket.close()
            except:
                pass