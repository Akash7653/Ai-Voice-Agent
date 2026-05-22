import json
import uuid
import logging
import tempfile
import os
import base64
from fastapi import WebSocket, WebSocketDisconnect

from services.stt_service import STTService
from services.tts_service import TTSService
from agent.orchestrator.llm_orchestrator import LLMOrchestrator

from sqlalchemy import select
from models.models import Appointment, DoctorSchedule, AppointmentStatus, LatencyMetric, ConversationLog
from datetime import datetime
import time
from memory.session_memory import RedisMemoryManager

logger = logging.getLogger(__name__)


class VoiceAgentWebSocketHandler:

    _stt_service = None
    _tts_service = None
    _llm_service = None

    def __init__(self, db_session=None):

        self.db_session = db_session
        self.redis = RedisMemoryManager()

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

        # notify client of session start so frontend can resolve connect promise
        try:
            await websocket.send_json({
                "type": "session_start",
                "session_id": session_id,
            })
        except Exception:
            logger.debug("Failed to send session_start message")

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

                            # read temp audio bytes and call STT
                            with open(temp_audio_path, "rb") as f:
                                audio_bytes = f.read()

                            stt_start = time.perf_counter()
                            stt_result = await self.stt_service.transcribe_audio(audio_bytes)
                            stt_end = time.perf_counter()

                            stt_ms = (stt_end - stt_start) * 1000.0

                            if not stt_result.get("success"):
                                raise Exception(stt_result.get("error", "STT failed"))

                            transcript = stt_result.get("text", "")

                            logger.info(f"[TRANSCRIPT] {transcript}")

                            await websocket.send_json({"type": "transcript", "text": transcript})

                            #
                            # LLM
                            #
                            logger.info("[PIPELINE] LLM started")

                            llm_start = time.perf_counter()
                            llm_response = await self.llm_service.generate_response(transcript)
                            llm_end = time.perf_counter()

                            llm_ms = (llm_end - llm_start) * 1000.0

                            response_text = (llm_response.get("response") if isinstance(llm_response, dict) else str(llm_response))

                            logger.info(f"[LLM] {response_text}")

                            # If LLM returned structured intent, run tool orchestration
                            intent = None
                            entities = {}

                            if isinstance(llm_response, dict):
                                intent = llm_response.get("intent")
                                entities = llm_response.get("entities") or {}

                            await websocket.send_json({"type": "response", "text": response_text})

                            if intent:
                                try:
                                    action_result, action_text = await self.handle_intent(
                                        intent, entities, patient_id, websocket
                                    )

                                    # send back action result and textual confirmation
                                    await websocket.send_json({
                                        "type": "action_result",
                                        "action": intent,
                                        "success": action_result.get("success", False),
                                        "data": action_result.get("data", {}),
                                    })

                                    if action_text:
                                        await websocket.send_json({"type": "response", "text": action_text})

                                except Exception as e:
                                    logger.exception("Error handling intent")
                                    await websocket.send_json({"type": "error", "message": str(e)})

                            #
                            # TTS
                            #
                            logger.info("[PIPELINE] TTS started")

                            tts_start = time.perf_counter()
                            tts_result = await self.tts_service.generate_speech(response_text)
                            tts_end = time.perf_counter()

                            tts_ms = (tts_end - tts_start) * 1000.0

                            if not tts_result.get("success"):
                                raise Exception(tts_result.get("error", "TTS failed"))

                            audio_bytes_out = tts_result.get("audio")

                            # encode to base64 for websocket transport
                            audio_base64 = base64.b64encode(audio_bytes_out).decode("utf-8")

                            await websocket.send_json({"type": "audio_response", "audio": audio_base64})

                            total_ms = (time.perf_counter() - stt_start) * 1000.0 if 'stt_start' in locals() else None

                            logger.info("[PIPELINE] Completed")

                            # persist latency metrics
                            try:
                                metrics = []
                                if 'stt_ms' in locals():
                                    metrics.append(LatencyMetric(session_id=session_id, component='stt', duration_ms=stt_ms))
                                if 'llm_ms' in locals():
                                    metrics.append(LatencyMetric(session_id=session_id, component='llm', duration_ms=llm_ms))
                                if 'tts_ms' in locals():
                                    metrics.append(LatencyMetric(session_id=session_id, component='tts', duration_ms=tts_ms))
                                if total_ms is not None:
                                    metrics.append(LatencyMetric(session_id=session_id, component='total', duration_ms=total_ms))

                                for m in metrics:
                                    self.db_session.add(m)

                                # update conversation log latency_metrics JSON
                                try:
                                    q = select(ConversationLog).where(ConversationLog.session_id == session_id)
                                    res = await self.db_session.execute(q)
                                    conv = res.scalar_one_or_none()
                                    if conv:
                                        lm = {m.component: m.duration_ms for m in metrics}
                                        conv.latency_metrics = lm
                                        self.db_session.add(conv)

                                except Exception:
                                    logger.debug("Failed to update conversation log latency_metrics")

                                await self.db_session.commit()
                            except Exception as e:
                                logger.debug(f"Failed to persist latency metrics: {e}")

                        except Exception as e:

                            logger.exception("[PIPELINE ERROR]")

                            await websocket.send_json({"type": "error", "message": str(e)})

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

    async def handle_intent(self, intent: str, entities: dict, patient_id: str, websocket: WebSocket):
        """Simple orchestration to call appointment actions based on LLM intent."""

        intent = (intent or "").lower()

        if intent == "book_appointment":
            # Expect doctor_id or doctor_name, specialty, appointment_date, appointment_time
            doctor_id = entities.get("doctor_id")
            doctor_name = entities.get("doctor_name")
            specialty = entities.get("specialty")
            appointment_date = entities.get("appointment_date")
            appointment_time = entities.get("appointment_time")

            # find doctor if id not provided
            if not doctor_id and doctor_name:
                q = select(DoctorSchedule).where(DoctorSchedule.doctor_name.ilike(f"%{doctor_name}%"))
                res = await self.db_session.execute(q)
                ds = res.scalar_one_or_none()
                if ds:
                    doctor_id = ds.doctor_id
                    doctor_name = ds.doctor_name

            if not doctor_id:
                return ({"success": False, "error": "Doctor not found"}, "I couldn't find that doctor.")

            # check schedule
            r = await self.db_session.execute(select(DoctorSchedule).where(DoctorSchedule.doctor_id == doctor_id))
            schedule = r.scalar_one_or_none()
            if not schedule:
                return ({"success": False, "error": "Doctor schedule not found"}, "Doctor schedule not found.")

            slots = schedule.available_slots or {}
            day_slots = slots.get(appointment_date, [])
            if appointment_time not in day_slots:
                return ({"success": False, "available_slots": day_slots}, "That time isn't available. Here are available slots." )

            # acquire distributed lock for this slot
            lock_key = f"{doctor_id}:{appointment_date}:{appointment_time}"
            token = await self.redis.acquire_lock(lock_key, ttl=30)
            if not token:
                return ({"success": False, "error": "lock_failed"}, "Another booking is in progress for that slot. Please try again.")

            try:
                # conflict check
                q2 = select(Appointment).where(
                    Appointment.doctor_id == doctor_id,
                    Appointment.appointment_date == appointment_date,
                    Appointment.appointment_time == appointment_time,
                    Appointment.status == AppointmentStatus.SCHEDULED,
                )
                r2 = await self.db_session.execute(q2)
                conflict = r2.scalar_one_or_none()
                if conflict:
                    return ({"success": False, "error": "Slot already booked"}, "Sorry, that slot is already taken.")

                appt = Appointment(
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    doctor_name=doctor_name or schedule.doctor_name,
                    specialty=specialty or schedule.specialty,
                    appointment_date=appointment_date,
                    appointment_time=appointment_time,
                )

                self.db_session.add(appt)
                await self.db_session.commit()
                await self.db_session.refresh(appt)

                text = f"Booked appointment with {appt.doctor_name} on {appt.appointment_date} at {appt.appointment_time}."
                return ({"success": True, "data": {"id": str(appt.id)}}, text)
            finally:
                await self.redis.release_lock(lock_key, token)

        if intent == "cancel_appointment":
            appointment_id = entities.get("appointment_id")
            if not appointment_id:
                return ({"success": False, "error": "missing appointment_id"}, "I need the appointment id to cancel.")

            r = await self.db_session.execute(select(Appointment).where(Appointment.id == appointment_id))
            appt = r.scalar_one_or_none()
            if not appt:
                return ({"success": False, "error": "not_found"}, "Appointment not found.")

            appt.status = AppointmentStatus.CANCELLED
            self.db_session.add(appt)
            await self.db_session.commit()
            await self.db_session.refresh(appt)

            text = f"Cancelled appointment {appointment_id}."
            return ({"success": True, "data": {"id": str(appt.id)}}, text)

        if intent == "reschedule_appointment":
            appointment_id = entities.get("appointment_id")
            new_date = entities.get("new_appointment_date")
            new_time = entities.get("new_appointment_time")
            if not appointment_id or not new_date or not new_time:
                return ({"success": False, "error": "missing_fields"}, "I need appointment id and new date/time to reschedule.")

            r = await self.db_session.execute(select(Appointment).where(Appointment.id == appointment_id))
            appt = r.scalar_one_or_none()
            if not appt:
                return ({"success": False, "error": "not_found"}, "Appointment not found.")

            # check conflicts
            # lock new slot before checking conflicts
            lock_key_new = f"{appt.doctor_id}:{new_date}:{new_time}"
            token_new = await self.redis.acquire_lock(lock_key_new, ttl=30)
            if not token_new:
                return ({"success": False, "error": "lock_failed"}, "Another booking is in progress for the requested new slot. Please try again.")

            try:
                q3 = select(Appointment).where(
                    Appointment.doctor_id == appt.doctor_id,
                    Appointment.appointment_date == new_date,
                    Appointment.appointment_time == new_time,
                    Appointment.status == AppointmentStatus.SCHEDULED,
                )
                r3 = await self.db_session.execute(q3)
                conflict = r3.scalar_one_or_none()
                if conflict:
                    return ({"success": False, "error": "conflict"}, "That new slot is already booked.")

                appt.appointment_date = new_date
                appt.appointment_time = new_time
                appt.status = AppointmentStatus.RESCHEDULED
                self.db_session.add(appt)
                await self.db_session.commit()
                await self.db_session.refresh(appt)

                text = f"Rescheduled appointment to {new_date} at {new_time}."
                return ({"success": True, "data": {"id": str(appt.id)}}, text)
            finally:
                await self.redis.release_lock(lock_key_new, token_new)

        # default: no action
        return ({"success": False, "error": "no_action", "intent": intent}, None)