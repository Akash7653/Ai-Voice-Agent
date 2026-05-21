"""
WebSocket handler for real-time voice streaming
"""
import base64
import logging
import time
from typing import Dict, Any, Optional
import uuid
from fastapi import WebSocket, WebSocketDisconnect

from backend.services.stt_service import STTService, TTSService
from backend.services.language_detection import LanguageDetectionService
from backend.agent.orchestrator.llm_orchestrator import LLMOrchestrator
from backend.memory.session_memory import RedisMemoryManager, PersistentMemoryManager
from backend.services.latency_tracker import LatencyTracker

logger = logging.getLogger(__name__)

class VoiceAgentWebSocketHandler:
    """Handles WebSocket connections for voice agent"""
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.stt_service = STTService()
        self.tts_service = TTSService(provider="openai")
        self.language_detector = LanguageDetectionService()
        self.orchestrator = LLMOrchestrator(db_session=db_session)
        self.redis_memory = RedisMemoryManager()
        self.persistent_memory = PersistentMemoryManager(db_session) if db_session else None
    
    async def handle_connection(self, websocket: WebSocket, patient_id: str):
        """
        Handle WebSocket connection for voice interaction
        """
        session_id = str(uuid.uuid4())
        latency_tracker = LatencyTracker(session_id)
        
        await websocket.accept()
        
        try:
            # Initialize session in Redis
            await self.redis_memory.set_session(
                session_id,
                {
                    "session_id": session_id,
                    "patient_id": patient_id,
                    "language": "auto",
                    "context": {},
                    "transcript": "",
                    "state": "listening",
                    "created_at": time.time()
                }
            )
            
            logger.info(f"WebSocket connection established: {session_id} for patient {patient_id}")
            
            # Send welcome message
            await websocket.send_json({
                "type": "session_start",
                "session_id": session_id,
                "message": "Voice agent ready. Please speak."
            })

            audio_buffer = bytearray()
            
            # Main conversation loop
            while True:
                audio_data = await websocket.receive_bytes()

                if not audio_data:
                    if audio_buffer:
                        await self._handle_end_audio(
                            websocket,
                            session_id,
                            patient_id,
                            bytes(audio_buffer),
                            latency_tracker
                        )
                        audio_buffer.clear()
                    continue

                audio_buffer.extend(audio_data)
        
        except WebSocketDisconnect:
            await self._handle_disconnect(session_id)
        except Exception as e:
            logger.error(f"Error in WebSocket handler: {e}")
            await self._handle_disconnect(session_id)
    
    async def _handle_end_audio(
        self,
        websocket: WebSocket,
        session_id: str,
        patient_id: str,
        audio_data: bytes,
        latency_tracker: LatencyTracker
    ):
        """Handle end of audio and process complete request"""
        try:
            # Get session data
            session = await self.redis_memory.get_session(session_id)
            if not session:
                await websocket.send_json({
                    "type": "error",
                    "message": "Session not found"
                })
                return

            language = session.get("language", "auto") if session else "auto"

            if not audio_data:
                await websocket.send_json({
                    "type": "error",
                    "message": "No audio received"
                })
                return

            await self.redis_memory.update_session(
                session_id,
                {"state": "processing"}
            )

            # Transcribe the full buffered binary audio stream (with debug audio save)
            latency_tracker.start("stt")
            print(f"[WebSocket] Audio buffer size: {len(audio_data)} bytes")
            transcript, stt_latency, stt_error = await self.stt_service.transcribe(
                audio_data,
                language,
                save_debug=True,
            )
            latency_tracker.end("stt")

            if not transcript:
                msg = stt_error or (
                    "Could not transcribe audio. Speak for 2+ seconds, then press Stop."
                )
                await websocket.send_json({
                    "type": "error",
                    "message": msg,
                    "code": "stt_failed",
                    "audio_bytes": len(audio_data),
                })
                await self.redis_memory.update_session(
                    session_id,
                    {"state": "listening"},
                )
                return

            detected_language, lang_confidence = self.language_detector.detect_language(transcript)
            if lang_confidence > 0.5:
                language = detected_language

            await websocket.send_json({
                "type": "transcript",
                "text": transcript,
                "language": language,
                "confidence": 0.9
            })
            
            # LLM reasoning
            latency_tracker.start("llm")
            
            reasoning_result, llm_latency = await self.orchestrator.reason_and_plan(
                user_input=transcript,
                language=language,
                session_context=session.get("context", {})
            )
            latency_tracker.end("llm")
            
            # Send reasoning trace
            await websocket.send_json({
                "type": "reasoning_trace",
                "intent": reasoning_result.get("intent"),
                "confidence": reasoning_result.get("confidence", 0),
                "entities": reasoning_result.get("entities", {}),
                "reasoning": reasoning_result.get("reasoning", "")
            })
            
            # Execute tool if intent requires action
            tool_result = None
            if reasoning_result.get("intent") != "small_talk":
                latency_tracker.start("tools")
                
                # Map intent to tool
                intent_to_tool = {
                    "book_appointment": "book_appointment",
                    "reschedule_appointment": "reschedule_appointment",
                    "cancel_appointment": "cancel_appointment",
                    "check_availability": "check_availability"
                }
                
                tool_name = intent_to_tool.get(reasoning_result.get("intent"))
                if tool_name:
                    tool_args = reasoning_result.get("entities", {})
                    tool_args["patient_id"] = patient_id
                    
                    tool_result = await self.orchestrator.execute_tool(
                        tool_name,
                        tool_args,
                        language=language
                    )
                
                latency_tracker.end("tools")
            
            # Generate response
            if tool_result and tool_result.get("success"):
                response_text = tool_result.get("message", "Tool executed successfully")
            else:
                response_text = reasoning_result.get("response", "I'm unable to process your request.")
            
            # TTS
            latency_tracker.start("tts")
            audio_response, tts_latency = await self.tts_service.synthesize(
                response_text,
                language=language
            )
            latency_tracker.end("tts")
            
            # Send response
            await websocket.send_json({
                "type": "response",
                "text": response_text,
                "language": language,
                "audio": base64.b64encode(audio_response).decode("utf-8") if audio_response else None
            })
            
            # Send latency metrics
            latency_report = latency_tracker.get_report()
            await websocket.send_json({
                "type": "latency_metrics",
                "total_latency_ms": latency_report["total_latency_ms"],
                "breakdown": latency_report["breakdown"]
            })
            
            # Update session
            await self.redis_memory.update_session(
                session_id,
                {
                    "state": "listening",
                    "last_response": response_text,
                    "latency_metrics": latency_report["breakdown"],
                    "tool_result": tool_result,
                    "language": language,
                    "detected_language": detected_language,
                    "transcript": transcript,
                }
            )
            
            # Log conversation
            if self.db_session:
                await self._log_conversation(
                    session_id,
                    patient_id,
                    language,
                    transcript,
                    reasoning_result,
                    tool_result,
                    latency_report
                )
            
            logger.info(f"Request processed: {session_id}, Intent: {reasoning_result.get('intent')}, Latency: {latency_report['total_latency_ms']:.2f}ms")
        
        except Exception as e:
            logger.error(f"Error handling end audio: {e}")
            await websocket.send_json({
                "type": "error",
                "message": "Error processing request"
            })
    
    async def _handle_disconnect(self, session_id: str):
        """Handle WebSocket disconnection"""
        await self.redis_memory.delete_session(session_id)
        logger.info(f"WebSocket disconnected: {session_id}")
    
    async def _log_conversation(
        self,
        session_id: str,
        patient_id: str,
        language: str,
        transcript: str,
        reasoning_result: Dict[str, Any],
        tool_result: Optional[Dict[str, Any]],
        latency_report: Dict[str, Any]
    ):
        """Log conversation to database"""
        try:
            from backend.models.models import ConversationLog
            
            log = ConversationLog(
                session_id=session_id,
                patient_id=patient_id,
                language=language,
                transcript=transcript,
                extracted_intent=reasoning_result.get("intent"),
                tools_used=[reasoning_result.get("intent")] if reasoning_result.get("intent") != "small_talk" else [],
                latency_metrics=latency_report["breakdown"]
            )
            
            self.db_session.add(log)
            await self.db_session.commit()
        
        except Exception as e:
            logger.error(f"Error logging conversation: {e}")
