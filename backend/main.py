"""
FastAPI main application
"""

from dotenv import load_dotenv
load_dotenv()

import os
import logging

from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    WebSocket,
    Depends,
    HTTPException,
    Query,
)

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.responses import JSONResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from db.database import (
    init_db,
    close_db,
    get_db,
)

from websocket.voice_handler import (
    VoiceAgentWebSocketHandler,
)

from models.models import (
    Appointment,
    AppointmentStatus,
    PatientMemory,
    DoctorSchedule,
    ConversationLog,
    LatencyMetric,
)

from memory.session_memory import (
    RedisMemoryManager,
)

from services.stt_service import STTService
from services.tts_service import TTSService
from agent.orchestrator.llm_orchestrator import (
    LLMOrchestrator
)
import base64
from time import perf_counter


# =========================
# LOGGING
# =========================

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# =========================
# GLOBAL SERVICES
# =========================

stt_service = STTService()
tts_service = TTSService()
llm_service = LLMOrchestrator()

redis_memory = RedisMemoryManager()


# =========================
# LIFESPAN
# =========================

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting Voice Agent API")

    await init_db()

    logger.info("Database initialized")

    yield

    logger.info("Shutting down Voice Agent API")

    await close_db()


# =========================
# FASTAPI APP
# =========================

app = FastAPI(
    title="Voice AI Healthcare Agent",
    description="Real-time multilingual voice AI agent",
    version="1.0.0",
    lifespan=lifespan,
)


# =========================
# CORS
# =========================

cors_origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "https://ai-voice-agent-six-delta.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# ROOT
# =========================

@app.get("/")
async def root():

    return {
        "status": "success",
        "message": "Backend is running successfully 🚀",
        "service": "Voice AI Healthcare Agent"
    }


# =========================
# HEALTH
# =========================

@app.get("/health")
async def health_check():

    return {
        "status": "healthy"
    }


# =========================
# WEBSOCKET
# =========================

@app.websocket("/ws/voice/{patient_id}")
async def websocket_voice_endpoint(
    websocket: WebSocket,
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):

    try:

        logger.info(f"WebSocket connection requested for patient: {patient_id}")

        handler = VoiceAgentWebSocketHandler(db_session=db)

        # handler.handle will call websocket.accept() before entering receive loop
        await handler.handle(websocket, patient_id)

    except Exception as e:

        logger.error(
            f"WebSocket error: {e}"
        )


# =========================
# APPOINTMENTS
# =========================


@app.get("/api/appointments/{patient_id}")
async def get_appointments(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):

    try:

        query = select(Appointment).where(
            Appointment.patient_id == patient_id
        )

        result = await db.execute(query)

        appts = result.scalars().all()

        return {
            "success": True,
            "data": [
                {
                    "id": str(a.id),
                    "patient_id": a.patient_id,
                    "doctor_name": a.doctor_name,
                    "specialty": a.specialty,
                    "appointment_date": a.appointment_date,
                    "appointment_time": a.appointment_time,
                    "status": a.status.value if a.status else None,
                }
                for a in appts
            ]
        }

    except Exception as e:

        logger.error(f"Error fetching appointments: {e}")

        raise HTTPException(
            status_code=500,
            detail="Error fetching appointments"
        )


# =========================
# LATENCY STATS
# =========================


@app.get("/api/latency-stats/{patient_id}")
async def get_latency_stats(
    patient_id: str,
    limit: int = Query(100),
    db: AsyncSession = Depends(get_db)
):

    try:

        # find recent session ids for this patient
        s = select(ConversationLog.session_id).where(
            ConversationLog.patient_id == patient_id
        ).order_by(ConversationLog.created_at.desc()).limit(limit)

        res = await db.execute(s)
        sessions = [r[0] for r in res.fetchall()]

        if not sessions:
            return {"success": True, "data": []}

        q = select(LatencyMetric).where(
            LatencyMetric.session_id.in_(sessions)
        ).order_by(LatencyMetric.timestamp.desc()).limit(limit)

        r2 = await db.execute(q)
        metrics = r2.scalars().all()

        return {
            "success": True,
            "data": [
                {
                    "session_id": m.session_id,
                    "component": m.component,
                    "duration_ms": m.duration_ms,
                    "timestamp": str(m.timestamp),
                }
                for m in metrics
            ]
        }

    except Exception as e:

        logger.error(f"Error fetching latency stats: {e}")

        raise HTTPException(
            status_code=500,
            detail="Error fetching latency stats"
        )


# =========================
# DOCTORS
# =========================


    @app.post("/api/appointments")
    async def create_appointment(payload: dict, db: AsyncSession = Depends(get_db)):

        try:
            required = ["patient_id", "doctor_id", "doctor_name", "specialty", "appointment_date", "appointment_time"]
            for r in required:
                if r not in payload:
                    raise HTTPException(status_code=400, detail=f"Missing field: {r}")

            patient_id = payload["patient_id"]
            doctor_id = payload["doctor_id"]
            doctor_name = payload["doctor_name"]
            specialty = payload["specialty"]
            appointment_date = payload["appointment_date"]
            appointment_time = payload["appointment_time"]
            duration = payload.get("duration_minutes", 30)

            # Verify doctor schedule
            result = await db.execute(select(DoctorSchedule).where(DoctorSchedule.doctor_id == doctor_id))
            schedule = result.scalar_one_or_none()

            if not schedule:
                raise HTTPException(status_code=404, detail="Doctor not found")

            slots = schedule.available_slots or {}
            day_slots = slots.get(appointment_date, [])

            if appointment_time not in day_slots:
                return {
                    "success": False,
                    "error": "Requested time not available",
                    "available_slots": day_slots
                }

            # Check for conflicts
            q = select(Appointment).where(
                Appointment.doctor_id == doctor_id,
                Appointment.appointment_date == appointment_date,
                Appointment.appointment_time == appointment_time,
                Appointment.status == AppointmentStatus.SCHEDULED
            )

            res = await db.execute(q)
            conflict = res.scalar_one_or_none()

            if conflict:
                return {"success": False, "error": "Slot already booked", "conflict": True}

            # create appointment
            appt = Appointment(
                patient_id=patient_id,
                doctor_id=doctor_id,
                doctor_name=doctor_name,
                specialty=specialty,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                duration_minutes=duration,
            )

            db.add(appt)
            await db.commit()
            await db.refresh(appt)

            return {"success": True, "data": {"id": str(appt.id)}}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            raise HTTPException(status_code=500, detail="Error creating appointment")


    @app.patch("/api/appointments/{appointment_id}")
    async def reschedule_appointment(appointment_id: str, payload: dict, db: AsyncSession = Depends(get_db)):

        try:
            new_date = payload.get("appointment_date")
            new_time = payload.get("appointment_time")

            if not new_date or not new_time:
                raise HTTPException(status_code=400, detail="Missing new date/time")

            result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
            appt = result.scalar_one_or_none()

            if not appt:
                raise HTTPException(status_code=404, detail="Appointment not found")

            # check doctor schedule and conflicts
            result = await db.execute(select(DoctorSchedule).where(DoctorSchedule.doctor_id == appt.doctor_id))
            schedule = result.scalar_one_or_none()

            if not schedule:
                raise HTTPException(status_code=404, detail="Doctor not found")

            day_slots = (schedule.available_slots or {}).get(new_date, [])
            if new_time not in day_slots:
                return {"success": False, "error": "Requested time not available", "available_slots": day_slots}

            q = select(Appointment).where(
                Appointment.doctor_id == appt.doctor_id,
                Appointment.appointment_date == new_date,
                Appointment.appointment_time == new_time,
                Appointment.status == AppointmentStatus.SCHEDULED
            )

            res = await db.execute(q)
            conflict = res.scalar_one_or_none()
            if conflict:
                return {"success": False, "error": "Slot already booked"}

            appt.appointment_date = new_date
            appt.appointment_time = new_time
            appt.status = AppointmentStatus.RESCHEDULED

            db.add(appt)
            await db.commit()
            await db.refresh(appt)

            return {"success": True, "data": {"id": str(appt.id), "status": appt.status.value}}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error rescheduling appointment: {e}")
            raise HTTPException(status_code=500, detail="Error rescheduling appointment")


    @app.delete("/api/appointments/{appointment_id}")
    async def cancel_appointment(appointment_id: str, db: AsyncSession = Depends(get_db)):

        try:
            result = await db.execute(select(Appointment).where(Appointment.id == appointment_id))
            appt = result.scalar_one_or_none()

            if not appt:
                raise HTTPException(status_code=404, detail="Appointment not found")

            appt.status = AppointmentStatus.CANCELLED

            db.add(appt)
            await db.commit()
            await db.refresh(appt)

            return {"success": True, "data": {"id": str(appt.id), "status": appt.status.value}}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error cancelling appointment: {e}")
            raise HTTPException(status_code=500, detail="Error cancelling appointment")

@app.get("/api/doctors")
async def get_doctors(
    specialty: str = Query(None),
    db: AsyncSession = Depends(get_db)
):

    try:

        query = select(DoctorSchedule).where(
            DoctorSchedule.is_active == True
        )

        if specialty:

            query = query.where(
                DoctorSchedule.specialty.ilike(
                    f"%{specialty}%"
                )
            )

        result = await db.execute(query)

        doctors = result.scalars().all()

        return {
            "success": True,
            "data": [
                {
                    "id": doctor.doctor_id,
                    "name": doctor.doctor_name,
                    "specialty": doctor.specialty,
                }
                for doctor in doctors
            ]
        }

    except Exception as e:

        logger.error(f"Error fetching doctors: {e}")

        raise HTTPException(
            status_code=500,
            detail="Error fetching doctors"
        )


# =========================
# PATIENT INFO
# =========================

@app.get("/api/patient/{patient_id}")
async def get_patient_info(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):

    try:

        result = await db.execute(
            select(PatientMemory).where(
                PatientMemory.patient_id == patient_id
            )
        )

        patient = result.scalar_one_or_none()

        if not patient:

            return {
                "success": False,
                "message": "Patient not found"
            }

        return {
            "success": True,
            "data": {
                "patient_id": patient.patient_id,
                "preferred_language":
                    patient.preferred_language,
            }
        }

    except Exception as e:

        logger.error(f"Error fetching patient info: {e}")

        raise HTTPException(
            status_code=500,
            detail="Error fetching patient info"
        )


@app.post("/api/tts")
async def synthesize_tts(payload: dict, db: AsyncSession = Depends(get_db)):
    try:
        text = payload.get("text")
        language = payload.get("language", "en")
        session_id = payload.get("session_id")

        if not text:
            raise HTTPException(status_code=400, detail="Missing text for TTS")

        t0 = perf_counter()
        res = await tts_service.generate_speech(text=text, language=language)
        duration_ms = (perf_counter() - t0) * 1000.0

        if not res.get("success"):
            raise HTTPException(status_code=500, detail=res.get("error", "TTS failed"))

        audio_bytes = res.get("audio")
        encoded = base64.b64encode(audio_bytes).decode('ascii')

        # persist latency metric if session_id available
        try:
            if session_id:
                lm = LatencyMetric(session_id=session_id, component='tts', duration_ms=duration_ms)
                db.add(lm)
                await db.commit()
        except Exception:
            logger.exception('Failed to persist TTS latency metric')

        return {"success": True, "audio": encoded, "duration_ms": duration_ms}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS endpoint error: {e}")
        raise HTTPException(status_code=500, detail="TTS synthesis failed")


# =========================
# ERROR HANDLER
# =========================

@app.exception_handler(Exception)
async def general_exception_handler(
    request,
    exc
):

    logger.error(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": str(exc),
        },
    )