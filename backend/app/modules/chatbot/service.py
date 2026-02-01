from google import genai
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine
from .schemas import ChatRouting
from .prompts import get_routing_system_prompt, get_summary_prompt
from .helper import check_and_raise_api_error


class ChatbotService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_id = "gemini-2.5-flash"

    def send_and_trim(self, user_text: str, history: list = None) -> tuple[str, list]:
        """
        Send message to chat and trim history if needed.
        Returns (response_text, updated_history)
        """
        if not user_text.strip():
            raise ValueError("Prompt cannot be empty")

        # Create a new chat session with history
        chat = self.client.chats.create(model=self.model_id, history=history or [])
        response = chat.send_message(user_text)
        response_text = response.text.strip()

        # Get updated history and trim if needed
        current_history = chat.get_history()
        if len(current_history) > 10:
            trimmed_history = current_history[-10:]
        else:
            trimmed_history = current_history

        return response_text, trimmed_history

    def generate_text(self, prompt: str, history: list = None) -> tuple[str, list]:
        """Generate text response"""
        return self.send_and_trim(prompt, history)

    def generate_financial_answer(
        self, user_question: str, current_user_id: str, history: list = None
    ) -> str:
        """Generate financial answer with routing logic"""
        system_prompt = get_routing_system_prompt(current_user_id)

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=user_question,
                config={
                    "system_instruction": system_prompt,
                    "response_mime_type": "application/json",
                    "response_json_schema": ChatRouting.model_json_schema(),
                },
            )

            routing = ChatRouting.model_validate_json(response.text)

        except Exception as e:
            error_str = str(e)
            print(f"Error in structured output parsing: {e}")
            check_and_raise_api_error(error_str)

            try:
                response_text, _ = self.send_and_trim(user_question, history)
                return response_text
            except Exception as fallback_error:
                check_and_raise_api_error(str(fallback_error))
                return "I'm having trouble understanding your request. As your PaisaTrack Financial Assistant, I'm here to help you track expenses and manage your finances. Could you try rephrasing?"

        if routing.intent == "chat":
            if routing.chat_response:
                return routing.chat_response
            try:
                response_text, _ = self.send_and_trim(user_question, history)
                return response_text
            except Exception as e:
                check_and_raise_api_error(str(e))
                return "Hello! I'm your PaisaTrack Financial Assistant AI. I'm here to help you track expenses, analyze spending patterns, and manage your finances. How can I assist you today?"

        if routing.intent == "query":
            if not routing.sql:
                return "I understand you're asking about your finances, but I couldn't generate a query for that. Could you try rephrasing your question?"

            forbidden = ["DELETE", "UPDATE", "DROP", "ALTER", "INSERT", "TRUNCATE"]
            if any(word in routing.sql.upper() for word in forbidden):
                return "I'm sorry, I can't perform that action on your data."

            try:
                print(f"DEBUG SQL: {routing.sql}")

                with engine.connect() as conn:
                    result = conn.execute(text(routing.sql))
                    data = [dict(row._mapping) for row in result]

                summary_prompt = get_summary_prompt(user_question, data)

                try:
                    summary_response = self.client.models.generate_content(
                        model=self.model_id, contents=summary_prompt
                    )
                    return summary_response.text.strip()
                except Exception as summary_error:
                    check_and_raise_api_error(str(summary_error))
                    try:
                        response_text, _ = self.send_and_trim(summary_prompt, history)
                        return response_text
                    except Exception as fallback_error:
                        check_and_raise_api_error(str(fallback_error))
                        raise summary_error

            except Exception as e:
                error_msg = str(e)
                print(f"SQL ERROR: {error_msg}")
                print(f"SQL that failed: {routing.sql}")
                raise Exception(f"SQL Error: {error_msg} | SQL: {routing.sql}")

        return "I'm your PaisaTrack Financial Assistant AI! I can help you track expenses, analyze spending patterns, and answer questions about your finances. What would you like to know?"
