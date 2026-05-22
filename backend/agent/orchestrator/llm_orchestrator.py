import google.generativeai as genai
import os


class LLMOrchestrator:

    def __init__(self):

        genai.configure(
            api_key=os.getenv("GEMINI_API_KEY")
        )

        self.model = genai.GenerativeModel(
            "gemini-1.5-flash"
        )

    async def generate_response(
        self,
        prompt: str
    ):

        try:

            response = self.model.generate_content(
                f"""
                You are a helpful AI healthcare assistant.

                Patient said:
                {prompt}

                Give short helpful response.
                """
            )

            return {
                "success": True,
                "response": response.text
            }

        except Exception as e:

            print(f"[LLM ERROR] {e}")

            return {
                "success": False,
                "response": "Sorry, I could not process your request."
            }