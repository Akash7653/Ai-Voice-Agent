"""
LLM Orchestrator for agent reasoning and tool calling
"""
import json
import re
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
import os
from datetime import datetime


@dataclass
class ReasoningTrace:
    """Reasoning trace for debugging and analysis"""
    timestamp: datetime
    input_text: str
    detected_intent: str
    extracted_entities: Dict[str, Any]
    selected_tool: str
    tool_arguments: Dict[str, Any]
    tool_result: Dict[str, Any]
    llm_response: str
    latency_ms: float


class PromptManager:
    """Manages system prompts for different languages by loading them from JSON."""

    _prompts = None

    @classmethod
    def _load_prompts(cls):
        if cls._prompts is not None:
            return cls._prompts

        from pathlib import Path
        prompts_path = Path(__file__).resolve().parent / "prompts.json"
        try:
            with prompts_path.open("r", encoding="utf-8") as fh:
                cls._prompts = json.load(fh)
        except Exception:
            cls._prompts = {
                "en": "You are a professional healthcare scheduling assistant. Keep responses short and in JSON format.",
            }

        return cls._prompts

    @staticmethod
    def get_system_prompt(language: str = "en") -> str:
        prompts = PromptManager._load_prompts()
        return prompts.get(language, prompts.get("en", ""))


class LLMOrchestrator:
    """Orchestrates LLM reasoning and tool calling"""

    def __init__(self, db_session=None):
        self.db_session = db_session
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        except Exception as e:
            print(f"Error initializing LLM orchestrator: {e}")
            self.client = None

        self.prompt_manager = PromptManager()

    async def reason_and_plan(
        self,
        user_input: str,
        language: str = "en",
        session_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], float]:
        """
        Use LLM to reason about user intent and plan tool calls
        Returns (reasoning_result, latency_ms)
        """
        start_time = time.time()

        try:
            if not self.client:
                return self._fallback_reasoning(user_input, language), 0

            system_prompt = self.prompt_manager.get_system_prompt(language)

            # Add context if available
            context_text = ""
            if session_context:
                context_text = f"\nCurrent context: {json.dumps(session_context)}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input + context_text}
            ]

            response = await self.client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )

            response_text = response.choices[0].message.content
            latency_ms = (time.time() - start_time) * 1000

            # Parse JSON response
            try:
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    result = self._fallback_reasoning(user_input, language)
            except json.JSONDecodeError:
                result = self._fallback_reasoning(user_input, language)

            return result, latency_ms

        except Exception as e:
            print(f"Error in LLM reasoning: {e}")
            return self._fallback_reasoning(user_input, language), 0

    def _fallback_reasoning(self, user_input: str, language: str = "en") -> Dict[str, Any]:
        """Fallback reasoning when LLM is unavailable"""

        user_lower = user_input.lower()

        intent = "small_talk"
        if any(word in user_lower for word in ["book", "schedule", "appointment", "मिलना", "मिलवाना", "சந்திப்பு"]):
            intent = "book_appointment"
        elif any(word in user_lower for word in ["reschedule", "change", "postpone", "बदल", "स्थानांतर", "மாற்று"]):
            intent = "reschedule_appointment"
        elif any(word in user_lower for word in ["cancel", "remove", "delete", "रद्द", "ரத்து", "தொலைக"]):
            intent = "cancel_appointment"
        elif any(word in user_lower for word in ["available", "slot", "when", "कब", "எப்போது", "समय"]):
            intent = "check_availability"

        return {
            "intent": intent,
            "confidence": 0.5,
            "entities": {},
            "reasoning": "Fallback reasoning using keyword matching",
            "response": user_input
        }

    async def execute_tool(
        self,
        tool_name: str,
        tool_arguments: Dict[str, Any],
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Execute appropriate tool based on reasoning
        """
        from backend.tools.appointment_tools import AppointmentTools

        try:
            if not self.db_session:
                return {
                    "success": False,
                    "error": "Database session not available"
                }

            tools = AppointmentTools(self.db_session)

            if tool_name == "book_appointment":
                result = await tools.book_appointment(**tool_arguments, language=language)
            elif tool_name == "reschedule_appointment":
                result = await tools.reschedule_appointment(**tool_arguments, language=language)
            elif tool_name == "cancel_appointment":
                result = await tools.cancel_appointment(**tool_arguments, language=language)
            elif tool_name == "check_availability":
                result = await tools.check_availability(**tool_arguments, language=language)
            else:
                return {
                    "success": False,
                    "error": f"Unknown tool: {tool_name}"
                }

            return {
                "success": result.success,
                "message": result.message,
                "data": result.data,
                "error": result.error
            }

        except Exception as e:
            print(f"Error executing tool {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
