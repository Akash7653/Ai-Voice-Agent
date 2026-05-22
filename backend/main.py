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
    PatientMemory,
    DoctorSchedule,
)

from memory.session_memory import (
    RedisMemoryManager,
)

from services.stt_service import STTService
from services.tts_service import TTSService
from agent.orchestrator.llm_orchestrator import (
    LLMService
)


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
llm_service = LLMService()

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

        await websocket.accept()

        logger.info(
            f"WebSocket connected for patient: {patient_id}"
        )

        handler = VoiceAgentWebSocketHandler(
            db_session=db,
            stt_service=stt_service,
            tts_service=tts_service,
            llm_service=llm_service,
        )

        await handler.handle_connection(
            websocket,
            patient_id
        )

    except Exception as e:

        logger.error(
            f"WebSocket error: {e}"
        )


# =========================
# DOCTORS
# =========================

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