"""
Memory management for sessions and persistent data
Uses Upstash Redis for session memory
Uses PostgreSQL for persistent patient memory
"""

import os
import json

from datetime import datetime
from typing import Dict, Any, Optional

from upstash_redis import Redis
import uuid


class RedisMemoryManager:
    """Session memory using Upstash Redis"""

    def __init__(self):
        self.client = Redis(
            url=os.getenv("UPSTASH_REDIS_REST_URL"),
            token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
        )

        self.ttl = int(
            os.getenv("SESSION_TTL", 3600)
        )

    async def set_session(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> bool:
        """Store session data with TTL"""

        try:
            key = f"session:{session_id}"

            self.client.set(
                key,
                json.dumps(data),
                ex=self.ttl
            )

            return True

        except Exception as e:
            print(f"Error setting session: {e}")
            return False

    async def get_session(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve session data"""

        try:
            key = f"session:{session_id}"

            data = self.client.get(key)

            if not data:
                return None

            return json.loads(data)

        except Exception as e:
            print(f"Error getting session: {e}")
            return None

    async def update_session(
        self,
        session_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update session fields"""

        try:
            session = await self.get_session(session_id)

            if session:
                session.update(updates)

                await self.set_session(
                    session_id,
                    session
                )

                return True

            return False

        except Exception as e:
            print(f"Error updating session: {e}")
            return False

    async def delete_session(
        self,
        session_id: str
    ) -> bool:
        """Delete session"""

        try:
            key = f"session:{session_id}"

            self.client.delete(key)

            return True

        except Exception as e:
            print(f"Error deleting session: {e}")
            return False

    async def set_context(
        self,
        session_id: str,
        key: str,
        value: Any
    ) -> bool:
        """Set session context"""

        try:
            session = await self.get_session(session_id)

            if not session:
                session = {}

            context = session.get("context", {})

            context[key] = value

            session["context"] = context

            await self.set_session(
                session_id,
                session
            )

            return True

        except Exception as e:
            print(f"Error setting context: {e}")
            return False

    async def get_context(
        self,
        session_id: str,
        key: str
    ) -> Optional[Any]:
        """Get session context"""

        try:
            session = await self.get_session(session_id)

            if session:
                return session.get(
                    "context",
                    {}
                ).get(key)

            return None

        except Exception as e:
            print(f"Error getting context: {e}")
            return None

    # -----------------
    # Simple distributed lock helpers
    # -----------------

    async def acquire_lock(self, key: str, ttl: int = 30) -> Optional[str]:
        """Attempt to acquire a lock for `key`. Returns token string if acquired, else None."""

        try:
            lock_key = f"lock:{key}"
            token = str(uuid.uuid4())

            # set NX with expiry
            ok = self.client.set(lock_key, token, ex=ttl, nx=True)

            if ok:
                return token

            return None

        except Exception as e:
            print(f"Error acquiring lock {key}: {e}")
            return None

    async def release_lock(self, key: str, token: str) -> bool:
        """Release lock only if token matches owner."""

        try:
            lock_key = f"lock:{key}"
            val = self.client.get(lock_key)

            if not val:
                return True

            # upstash returns bytes/str depending; ensure str
            if isinstance(val, bytes):
                val = val.decode("utf-8")

            if val == token:
                self.client.delete(lock_key)
                return True

            return False

        except Exception as e:
            print(f"Error releasing lock {key}: {e}")
            return False


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

        from models.models import PatientMemory
        from sqlalchemy import select

        try:
            result = await self.db_session.execute(
                select(PatientMemory).where(
                    PatientMemory.patient_id == patient_id
                )
            )

            memory = result.scalar_one_or_none()

            if memory:
                memory.preferred_language = language

                if doctor:
                    memory.preferred_doctor = doctor

                if conversation_summary:
                    memory.conversation_summary = (
                        conversation_summary
                    )

                memory.interaction_count += 1

                memory.last_interaction = (
                    datetime.utcnow()
                )

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

    async def get_patient_memory(
        self,
        patient_id: str
    ) -> Optional[Dict[str, Any]]:
        """Retrieve patient memory"""

        from models.models import PatientMemory
        from sqlalchemy import select

        try:
            result = await self.db_session.execute(
                select(PatientMemory).where(
                    PatientMemory.patient_id == patient_id
                )
            )

            memory = result.scalar_one_or_none()

            if memory:
                return {
                    "preferred_language":
                        memory.preferred_language,

                    "preferred_doctor":
                        memory.preferred_doctor,

                    "interaction_count":
                        memory.interaction_count,

                    "last_interaction":
                        (
                            memory.last_interaction.isoformat()
                            if memory.last_interaction
                            else None
                        ),

                    "conversation_summary":
                        memory.conversation_summary,
                }

            return None

        except Exception as e:
            print(f"Error getting patient memory: {e}")

            return None