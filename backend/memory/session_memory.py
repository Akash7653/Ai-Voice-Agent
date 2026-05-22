from upstash_redis import Redis
import os
import json
from typing import Dict, Any, Optional


class RedisMemoryManager:
    """Session memory using Upstash Redis"""

    def __init__(self):
        self.client = Redis(
            url=os.getenv("UPSTASH_REDIS_REST_URL"),
            token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
        )

        self.ttl = int(os.getenv("SESSION_TTL", 3600))

    async def set_session(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> bool:
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

        try:
            session = await self.get_session(session_id) or {}

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