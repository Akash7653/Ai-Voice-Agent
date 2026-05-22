import google.generativeai as genai
import os


class LLMService:

    def __init__(self):

        genai.configure(
            api_key=os.getenv("GEMINI_API_KEY")
        )

        self.model = genai.GenerativeModel(
            "gemini-1.5-flash"
        )

    async def reason_and_plan(
        self,
        user_input: str,
        language: str = "en",
        session_context=None,
    ):

        try:

            prompt = f"""
            You are a healthcare voice AI assistant.

            User said:
            {user_input}

            Detect:
            - intent
            - entities
            - response

            Return conversational response.
            """

            response = self.model.generate_content(
                prompt
            )

            return (
                {
                    "intent": "general_query",
                    "confidence": 0.95,
                    "entities": {},
                    "reasoning": "Gemini reasoning completed",
                    "response": response.text,
                },
                None,
            )

        except Exception as e:

            return (
                {
                    "intent": "error",
                    "confidence": 0,
                    "entities": {},
                    "reasoning": str(e),
                    "response":
                        "I could not process your request.",
                },
                None,
            )

    async def execute_tool(
        self,
        tool_name,
        tool_args,
        language="en",
    ):

        return {
            "success": True,
            "message":
                "Tool execution simulated successfully.",
        }