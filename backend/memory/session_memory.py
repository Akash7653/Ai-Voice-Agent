from upstash_redis import Redis
import os
import json
from typing import Dict, Any, Optional


class RedisMemoryManager:
    """Session memory using Upstash Redis"""

    def __init__(self, db_session):
        self.db_session = db_session

    async def save_patient_memory(
        self,
        patient_id: str,
        language: str = "en",
        doctor: Optional[str] = None,
        conversation_summary: Optional[str] = None
    ) -> bool:

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

    async def get_patient_memory(
        self,
        patient_id: str
    ) -> Optional[Dict[str, Any]]:

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
                    "preferred_language": memory.preferred_language,
                    "preferred_doctor": memory.preferred_doctor,
                    "interaction_count": memory.interaction_count,
                    "last_interaction": (
                        memory.last_interaction.isoformat()
                        if memory.last_interaction
                        else None
                    ),
                    "conversation_summary": memory.conversation_summary,
                }

            return None

        except Exception as e:
            print(f"Error getting patient memory: {e}")

            return None