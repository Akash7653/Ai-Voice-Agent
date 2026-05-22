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

    async def generate_response(
        self,
        prompt: str
    ):

        try:
            response = self.model.generate_content(
                prompt
            )

            return {
                "success": True,
                "response": response.text
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }