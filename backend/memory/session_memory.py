"""
Memory management for sessions and persistent data
Uses Redis for session memory and PostgreSQL for persistent memory
"""
import json
import redis
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os

class RedisMemoryManager:
    """Session memory using Redis with TTL"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self.client = redis.from_url(self.redis_url, decode_responses=True)
        self.ttl = int(os.getenv("SESSION_TTL", 3600))
    
    async def set_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Store session data with TTL"""
        try:
            key = f"session:{session_id}"
            self.client.setex(
                key,
                self.ttl,
                json.dumps(data)
            )
            return True
        except Exception as e:
            print(f"Error setting session: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""
        try:
            key = f"session:{session_id}"
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception as e:
            print(f"Error getting session: {e}")
            return None
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields in session"""
        try:
            session = await self.get_session(session_id)
            if session:
                session.update(updates)
                await self.set_session(session_id, session)
                return True
            return False
        except Exception as e:
            print(f"Error updating session: {e}")
            return False
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        try:
            key = f"session:{session_id}"
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Error deleting session: {e}")
            return False
    
    async def set_context(self, session_id: str, key: str, value: Any) -> bool:
        """Set specific context value"""
        try:
            session = await self.get_session(session_id) or {}
            context = session.get("context", {})
            context[key] = value
            session["context"] = context
            await self.set_session(session_id, session)
            return True
        except Exception as e:
            print(f"Error setting context: {e}")
            return False
    
    async def get_context(self, session_id: str, key: str) -> Optional[Any]:
        """Get specific context value"""
        try:
            session = await self.get_session(session_id)
            if session:
                return session.get("context", {}).get(key)
            return None
        except Exception as e:
            print(f"Error getting context: {e}")
            return None

class PersistentMemoryManager:
    """Persistent memory using PostgreSQL"""
    
    def __init__(self, db_session):
        self.db_session = db_session
    
    async def save_patient_memory(
        self,
        patient_id: str,
        language: str = "en",
        doctor: Optional[str] = None,
        conversation_summary: Optional[str] = None
    ) -> bool:
        """Save or update patient memory"""
        from backend.models.models import PatientMemory
        from sqlalchemy import select
        
        try:
            # Check if patient memory exists
            result = await self.db_session.execute(
                select(PatientMemory).where(PatientMemory.patient_id == patient_id)
            )
            memory = result.scalar_one_or_none()
            
            if memory:
                memory.preferred_language = language
                if doctor:
                    memory.preferred_doctor = doctor
                if conversation_summary:
                    memory.conversation_summary = conversation_summary
                memory.interaction_count += 1
                memory.last_interaction = datetime.utcnow()
            else:
                memory = PatientMemory(
                    patient_id=patient_id,
                    preferred_language=language,
                    preferred_doctor=doctor,
                    conversation_summary=conversation_summary,
                    interaction_count=1
                )
                self.db_session.add(memory)
            
            await self.db_session.commit()
            return True
        except Exception as e:
            print(f"Error saving patient memory: {e}")
            await self.db_session.rollback()
            return False
    
    async def get_patient_memory(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve patient memory"""
        from backend.models.models import PatientMemory
        from sqlalchemy import select
        
        try:
            result = await self.db_session.execute(
                select(PatientMemory).where(PatientMemory.patient_id == patient_id)
            )
            memory = result.scalar_one_or_none()
            
            if memory:
                return {
                    "preferred_language": memory.preferred_language,
                    "preferred_doctor": memory.preferred_doctor,
                    "interaction_count": memory.interaction_count,
                    "last_interaction": memory.last_interaction.isoformat() if memory.last_interaction else None,
                    "conversation_summary": memory.conversation_summary,
                }
            return None
        except Exception as e:
            print(f"Error getting patient memory: {e}")
            return None
