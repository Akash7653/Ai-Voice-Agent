"""
FastAPI main application
"""
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="backend/.env")

print("OPENAI:", os.getenv("OPENAI_API_KEY"))
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import init_db, close_db, get_db
from websocket.voice_handler import VoiceAgentWebSocketHandler
from models.models import Appointment, AppointmentStatus, PatientMemory, DoctorSchedule
from memory.session_memory import RedisMemoryManager
from sqlalchemy import select



# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
redis_memory = RedisMemoryManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events"""
    # Startup
    logger.info("Starting Voice Agent API")
    await init_db()
    logger.info("Database initialized")
    yield
    # Shutdown
    logger.info("Shutting down Voice Agent API")
    await close_db()

app = FastAPI(
    title="Voice AI Healthcare Agent",
    description="Real-time multilingual voice AI agent for appointment booking",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket endpoint
@app.websocket("/ws/voice/{patient_id}")
async def websocket_voice_endpoint(websocket: WebSocket, patient_id: str, db: AsyncSession = Depends(get_db)):
    """
    WebSocket endpoint for voice interaction
    Path: /ws/voice/{patient_id}
    """
    handler = VoiceAgentWebSocketHandler(db_session=db)
    await handler.handle_connection(websocket, patient_id)

# REST API endpoints

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Voice AI Healthcare Agent",
        "version": "1.0.0"
    }

@app.get("/api/appointments/{patient_id}")
async def get_patient_appointments(
    patient_id: str,
    status: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get all appointments for a patient"""
    try:
        query = select(Appointment).where(Appointment.patient_id == patient_id)
        
        if status:
            query = query.where(Appointment.status == status)
        
        result = await db.execute(query)
        appointments = result.scalars().all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": str(ap.id),
                    "doctor_name": ap.doctor_name,
                    "specialty": ap.specialty,
                    "appointment_date": ap.appointment_date,
                    "appointment_time": ap.appointment_time,
                    "status": ap.status.value,
                    "created_at": ap.created_at.isoformat()
                }
                for ap in appointments
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching appointments: {e}")
        raise HTTPException(status_code=500, detail="Error fetching appointments")

@app.get("/api/doctors")
async def get_doctors(
    specialty: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get list of available doctors"""
    try:
        query = select(DoctorSchedule).where(DoctorSchedule.is_active == True)
        
        if specialty:
            query = query.where(DoctorSchedule.specialty.ilike(f"%{specialty}%"))
        
        result = await db.execute(query)
        doctors = result.scalars().all()
        
        return {
            "success": True,
            "data": [
                {
                    "id": doctor.doctor_id,
                    "name": doctor.doctor_name,
                    "specialty": doctor.specialty,
                    "working_hours": f"{doctor.working_hours_start}-{doctor.working_hours_end}",
                    "available_slots": doctor.available_slots
                }
                for doctor in doctors
            ]
        }
    except Exception as e:
        logger.error(f"Error fetching doctors: {e}")
        raise HTTPException(status_code=500, detail="Error fetching doctors")

@app.get("/api/patient/{patient_id}")
async def get_patient_info(
    patient_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get patient information and preferences"""
    try:
        result = await db.execute(
            select(PatientMemory).where(PatientMemory.patient_id == patient_id)
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
                "preferred_language": patient.preferred_language,
                "preferred_doctor": patient.preferred_doctor,
                "interaction_count": patient.interaction_count,
                "last_interaction": patient.last_interaction.isoformat() if patient.last_interaction else None,
                "conversation_summary": patient.conversation_summary
            }
        }
    except Exception as e:
        logger.error(f"Error fetching patient info: {e}")
        raise HTTPException(status_code=500, detail="Error fetching patient info")

@app.post("/api/patient/{patient_id}/preferences")
async def update_patient_preferences(
    patient_id: str,
    preferences: dict,
    db: AsyncSession = Depends(get_db)
):
    """Update patient preferences"""
    try:
        result = await db.execute(
            select(PatientMemory).where(PatientMemory.patient_id == patient_id)
        )
        patient = result.scalar_one_or_none()
        
        if not patient:
            from models.models import PatientMemory
            patient = PatientMemory(patient_id=patient_id)
            db.add(patient)
        
        if "preferred_language" in preferences:
            patient.preferred_language = preferences["preferred_language"]
        
        if "preferred_doctor" in preferences:
            patient.preferred_doctor = preferences["preferred_doctor"]
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Preferences updated"
        }
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail="Error updating preferences")

@app.get("/api/session/{session_id}")
async def get_session_info(session_id: str):
    """Get session information"""
    try:
        session = await redis_memory.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "success": True,
            "data": session
        }
    except Exception as e:
        logger.error(f"Error fetching session: {e}")
        raise HTTPException(status_code=500, detail="Error fetching session")

@app.get("/api/latency-stats/{patient_id}")
async def get_latency_stats(
    patient_id: str,
    limit: int = Query(100),
    db: AsyncSession = Depends(get_db)
):
    """Get latency statistics for patient"""
    empty_stats = {
        "avg_total_latency": 0,
        "min_latency": 0,
        "max_latency": 0,
        "metrics_count": 0,
    }
    try:
        from models.models import LatencyMetric, ConversationLog

        result = await db.execute(
            select(LatencyMetric)
            .join(
                ConversationLog,
                ConversationLog.session_id == LatencyMetric.session_id,
            )
            .where(ConversationLog.patient_id == patient_id)
            .order_by(LatencyMetric.timestamp.desc())
            .limit(limit)
        )

        metrics = result.scalars().all()
        total_latencies = [m.duration_ms for m in metrics if m.component == "total"]

        return {
            "success": True,
            "data": {
                "avg_total_latency": (
                    sum(total_latencies) / len(total_latencies) if total_latencies else 0
                ),
                "min_latency": min(total_latencies) if total_latencies else 0,
                "max_latency": max(total_latencies) if total_latencies else 0,
                "metrics_count": len(metrics),
            },
        }
    except Exception as e:
        logger.error(f"Error fetching latency stats: {e}")
        return {"success": True, "data": empty_stats}

# Error handlers
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return {
        "success": False,
        "error": "Internal server error"
    }

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=os.getenv("DEBUG", "False").lower() == "true",
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
