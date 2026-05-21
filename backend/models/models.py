"""
SQLAlchemy ORM models for database schema
"""
from  datetime import datetime
from  sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, Enum, ForeignKey, JSON
from  sqlalchemy.orm import relationship
from  sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
import uuid
import enum

from db.database import Base

class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"

class ConversationStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class CampaignStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class Appointment(Base):
    """Appointment model"""
    __tablename__ = "appointments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(String, nullable=False, index=True)
    doctor_name = Column(String, nullable=False)
    doctor_id = Column(String, nullable=True)
    specialty = Column(String, nullable=False)
    appointment_date = Column(String, nullable=False)  # ISO format date
    appointment_time = Column(String, nullable=False)  # HH:MM format
    duration_minutes = Column(Integer, default=30)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    notes = Column(Text, nullable=True)
    confirmed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, patient={self.patient_id}, doctor={self.doctor_name})>"

class DoctorSchedule(Base):
    """Doctor availability schedule"""
    __tablename__ = "doctor_schedule"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(String, nullable=False, unique=True, index=True)
    doctor_name = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    available_slots = Column(JSON, nullable=False)  # {date: [time1, time2, ...]}
    working_hours_start = Column(String, default="09:00")
    working_hours_end = Column(String, default="17:00")
    is_active = Column(Boolean, default=True)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<DoctorSchedule(doctor={self.doctor_name}, specialty={self.specialty})>"

class PatientMemory(Base):
    """Persistent patient memory and preferences"""
    __tablename__ = "patient_memory"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(String, nullable=False, unique=True, index=True)
    preferred_language = Column(String, default="en")
    preferred_doctor = Column(String, nullable=True)
    preferred_specialties = Column(JSON, default={})  # {specialty: preference_score}
    past_appointments = Column(JSON, default=[])
    interaction_count = Column(Integer, default=0)
    last_interaction = Column(TIMESTAMP(timezone=True), nullable=True)
    conversation_summary = Column(Text, nullable=True)
    patient_metadata = Column(JSON, default={})  # email, phone, age, etc.
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<PatientMemory(patient={self.patient_id}, language={self.preferred_language})>"

class ConversationLog(Base):
    """Log of all conversations"""
    __tablename__ = "conversation_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=False, index=True)
    patient_id = Column(String, nullable=False, index=True)
    language = Column(String, default="en")  # Supported: en, hi, ta, te
    status = Column(Enum(ConversationStatus), default=ConversationStatus.ACTIVE)
    transcript = Column(Text, nullable=True)
    extracted_intent = Column(String, nullable=True)
    tools_used = Column(JSON, default=[])
    latency_metrics = Column(JSON, default={})
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ConversationLog(session={self.session_id}, patient={self.patient_id})>"

class CampaignTask(Base):
    """Outbound campaign tasks (reminders, follow-ups)"""
    __tablename__ = "campaign_task"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(String, nullable=False, index=True)
    campaign_type = Column(String, nullable=False)  # reminder, follow_up, vaccination
    appointment_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.SCHEDULED)
    scheduled_time = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    completed_time = Column(TIMESTAMP(timezone=True), nullable=True)
    result = Column(String, nullable=True)  # confirmed, rescheduled, rejected
    transcript = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    updated_at = Column(TIMESTAMP(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CampaignTask(patient={self.patient_id}, type={self.campaign_type})>"

class LatencyMetric(Base):
    """Latency tracking for performance monitoring"""
    __tablename__ = "latency_metric"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, nullable=False, index=True)
    component = Column(String, nullable=False)  # stt, llm, tools, tts, total
    duration_ms = Column(Float, nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), default=datetime.utcnow)
    
    def __repr__(self):
        return f"<LatencyMetric(component={self.component}, duration={self.duration_ms}ms)>"
