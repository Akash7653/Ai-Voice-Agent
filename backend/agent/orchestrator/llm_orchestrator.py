import google.generativeai as genai
import os
import re
import json


class LLMOrchestrator:

    def __init__(self):

        genai.configure(
            api_key=os.getenv("GEMINI_API_KEY")
        )

        self.model = genai.GenerativeModel(
            "gemini-1.5-flash"
        )

    async def generate_response(self, prompt: str):
        """Generate a response and parse structured JSON intent when possible.

        Returns a dict: { success: bool, response: raw_text, intent: str|None, entities: dict }
        """
        try:

            instruct = f"""
You are an AI healthcare scheduling assistant. Analyze the user's utterance and return a JSON object only (no surrounding text)
with the following structure:
{{
  "intent": "book_appointment|reschedule_appointment|cancel_appointment|check_availability|small_talk",
  "confidence": 0.0,
  "entities": {{
    "patient_id": "string or null",
    "appointment_id": "string or null",
    "doctor_id": "string or null",
    "doctor_name": "string or null",
    "specialty": "string or null",
    "appointment_date": "YYYY-MM-DD or null",
    "appointment_time": "HH:MM or null",
    "new_appointment_date": "YYYY-MM-DD or null",
    "new_appointment_time": "HH:MM or null"
  }}
}}

User utterance:
{prompt}
Return only the JSON object.
"""

            response = self.model.generate_content(instruct)
            raw = getattr(response, "text", str(response))

            # Try to parse JSON directly
            parsed = None
            try:
                parsed = json.loads(raw)
            except Exception:
                # try to extract first JSON object in text
                m = re.search(r"(\{.*\})", raw, re.S)
                if m:
                    try:
                        parsed = json.loads(m.group(1))
                    except Exception:
                        parsed = None

            if parsed and isinstance(parsed, dict):
                intent = parsed.get("intent")
                entities = parsed.get("entities", {})
                return {
                    "success": True,
                    "response": raw,
                    "intent": intent,
                    "entities": entities,
                }

            # fallback: return raw text
            return {"success": True, "response": raw, "intent": None, "entities": {}}

        except Exception as e:
            print(f"[LLM ERROR] {e}")
            return {"success": False, "response": "Sorry, I could not process your request.", "intent": None, "entities": {}}